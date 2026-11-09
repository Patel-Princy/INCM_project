"""Unit tests for the Phase 2G-A static readiness audit.

The audit's value depends on it refusing to guess, so almost everything worth
testing is a pure function of a file or of the report ledger. The tests below
build synthetic SWC morphologies whose axon geometry is known by construction,
and check the properties the report leans on:

* the two axon branches are reproduced from geometry alone, so the divergence
  between them is a measurement rather than an assertion;
* a morphology with no axon is reported as unusable, never defaulted to a stub;
* the verdict is computed from findings, so prose cannot drift away from them;
* the audit imports nothing that could start NEURON.

Run with ``python -m pytest tests -q``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
# ``tests/conftest.py`` puts ``src/data_audit`` on the path but not ``scripts``,
# and the Phase 2G-A module lives there.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_all_active_readiness as p2g  # noqa: E402

CACHE_PRESENT = p2g.CACHE.exists()
requires_cache = pytest.mark.skipif(
    not CACHE_PRESENT,
    reason="the Allen model cache is gitignored and not present in this checkout",
)

PI = 3.141592653589793


@pytest.fixture(autouse=True)
def reset_findings():
    """``FINDINGS`` is module state; no test may inherit another's decisions."""
    p2g.FINDINGS.update({key: None for key in p2g.FINDINGS})
    yield
    p2g.FINDINGS.update({key: None for key in p2g.FINDINGS})


def write_swc(path, rows):
    """Write a minimal SWC file from (id, type, x, y, z, radius, parent) rows."""
    lines = ["# synthetic morphology written by the Phase 2G-A tests"]
    for row in rows:
        lines.append("%d %d %.6f %.6f %.6f %.9f %d" % row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def straight_axon(path, length_um=80.0, step_um=5.0):
    """A soma with one straight axon, plus one dendrite and one apical point.

    The proximal radii are deliberately uneven and the distal ones deliberately
    constant, so that the truncated branch's two samples are distinguishable:
    a range near the soma and a plateau beyond 60 um.
    """
    rows = [
        (1, 1, 0.0, 0.0, 0.0, 5.0, -1),
        (2, 2, 0.0, 0.0, 0.0, 0.1196, 1),
        (3, 2, 5.0, 0.0, 0.0, 0.1500, 2),
        (4, 2, 10.0, 0.0, 0.0, 0.1100, 3),
    ]
    next_id = 5
    parent = 4
    position = 15.0
    while position <= length_um + 1e-9:
        rows.append((next_id, 2, position, 0.0, 0.0, 0.1144, parent))
        parent = next_id
        next_id += 1
        position += step_um
    rows.append((next_id, 3, -20.0, 0.0, 0.0, 0.9, 1))
    rows.append((next_id + 1, 4, -40.0, 0.0, 0.0, 0.8, 1))
    return write_swc(path, rows)


# ---------------------------------------------------------------------------
# SWC parsing
# ---------------------------------------------------------------------------


def test_read_swc_parses_the_seven_columns(tmp_path):
    path = write_swc(tmp_path / "m.swc", [(1, 1, 1.0, 2.0, 3.0, 4.0, -1)])

    rows = p2g.read_swc(path)

    assert len(rows) == 1
    assert rows[0] == {"id": 1, "type": 1, "x": 1.0, "y": 2.0, "z": 3.0,
                       "r": 4.0, "parent": -1}


def test_read_swc_ignores_comments_blanks_and_short_rows(tmp_path):
    path = tmp_path / "m.swc"
    path.write_text(
        "# a comment\n"
        "\n"
        "1 1 0 0 0 5 -1\n"
        "1 2 0 0\n"
        "not a number 1 0 0 0 5 -1\n"
        "2 2 1 0 0 0.1 1\n",
        encoding="utf-8",
    )

    rows = p2g.read_swc(path)

    assert [row["id"] for row in rows] == [1, 2]


# ---------------------------------------------------------------------------
# Axon chain
# ---------------------------------------------------------------------------


def test_axon_chain_reports_no_axon_rather_than_inventing_one(tmp_path):
    path = write_swc(tmp_path / "m.swc", [
        (1, 1, 0.0, 0.0, 0.0, 5.0, -1),
        (2, 3, -20.0, 0.0, 0.0, 0.9, 1),
    ])

    info = p2g.axon_chain(p2g.read_swc(path))

    assert info["available"] is False
    assert info["n_axon_points"] == 0
    assert info["n_roots"] == 0
    assert info["chain"] == []


def test_axon_chain_accumulates_arc_length_from_the_soma_attached_root(tmp_path):
    path = write_swc(tmp_path / "m.swc", [
        (1, 1, 0.0, 0.0, 0.0, 5.0, -1),
        (2, 2, 0.0, 0.0, 0.0, 0.1, 1),
        (3, 2, 10.0, 0.0, 0.0, 0.1, 2),
        (4, 2, 25.0, 0.0, 0.0, 0.1, 3),
    ])

    info = p2g.axon_chain(p2g.read_swc(path))

    assert info["available"] is True
    assert info["n_roots"] == 1
    assert info["path_um"][2] == pytest.approx(0.0)
    assert info["path_um"][3] == pytest.approx(10.0)
    assert info["path_um"][4] == pytest.approx(25.0)
    assert info["total_path_um"] == pytest.approx(25.0)


def test_axon_chain_ignores_dendrites_when_measuring_arc(tmp_path):
    path = straight_axon(tmp_path / "m.swc", length_um=20.0, step_um=5.0)

    info = p2g.axon_chain(p2g.read_swc(path))

    assert info["total_path_um"] == pytest.approx(20.0)
    assert all(row["type"] == 2 for row in info["chain"])


# ---------------------------------------------------------------------------
# The two axon branches
# ---------------------------------------------------------------------------


def test_stub_area_is_a_uniform_one_micron_cylinder(tmp_path):
    geometry = p2g.axon_branch_geometry(p2g.read_swc(straight_axon(tmp_path / "m.swc")))

    expected = PI * 30.0 * 1.0 * 2.0
    assert geometry["stub_total_area_um2"] == pytest.approx(expected)
    assert geometry["stub_total_area_um2"] == pytest.approx(188.4956, abs=1e-4)


def test_truncated_proximal_sample_spans_the_uneven_stretch(tmp_path):
    geometry = p2g.axon_branch_geometry(p2g.read_swc(straight_axon(tmp_path / "m.swc")))

    # radii 0.2392, 0.3000 and 0.2200 um lie at arcs 0, 5 and 10 um
    assert geometry["truncated_proximal_diam_um_min"] == pytest.approx(0.22)
    assert geometry["truncated_proximal_diam_um_max"] == pytest.approx(0.30)


def test_truncated_distal_sample_is_the_plateau_beyond_sixty_microns(tmp_path):
    geometry = p2g.axon_branch_geometry(p2g.read_swc(straight_axon(tmp_path / "m.swc")))

    assert geometry["truncated_distal_diam_um"] == pytest.approx(0.2288)
    assert geometry["distal_window_all_equal"] is True
    assert geometry["distal_window_n"] >= 3


def test_truncated_area_follows_the_two_sampled_diameters(tmp_path):
    geometry = p2g.axon_branch_geometry(p2g.read_swc(straight_axon(tmp_path / "m.swc")))

    thin = PI * 30.0 * (0.22 + 0.2288)
    thick = PI * 30.0 * (0.30 + 0.2288)
    assert geometry["truncated_total_area_um2_min"] == pytest.approx(thin)
    assert geometry["truncated_total_area_um2_max"] == pytest.approx(thick)
    assert geometry["area_ratio_min"] == pytest.approx(
        geometry["stub_total_area_um2"] / thick)
    assert geometry["area_ratio_max"] == pytest.approx(
        geometry["stub_total_area_um2"] / thin)


def test_the_branches_attach_at_different_points_on_the_soma(tmp_path):
    geometry = p2g.axon_branch_geometry(p2g.read_swc(straight_axon(tmp_path / "m.swc")))

    assert geometry["stub_attachment"] == "soma[0](0.5)"
    assert geometry["truncated_attachment"] == "soma[0](1.0)"


def test_an_axon_too_short_to_sample_twice_is_refused(tmp_path):
    path = straight_axon(tmp_path / "m.swc", length_um=20.0, step_um=5.0)

    geometry = p2g.axon_branch_geometry(p2g.read_swc(path))

    assert geometry["available"] is False
    assert "too short" in geometry["reason"]


def test_a_thin_axon_inflates_the_stub_by_more_than_threefold(tmp_path):
    geometry = p2g.axon_branch_geometry(p2g.read_swc(straight_axon(tmp_path / "m.swc")))

    assert geometry["area_ratio_min"] > 3.0
    assert geometry["area_ratio_max"] < 5.0


# ---------------------------------------------------------------------------
# Bookkeeping helpers
# ---------------------------------------------------------------------------


def test_occurrences_returns_minus_one_for_a_missing_file(tmp_path):
    assert p2g._occurrences(tmp_path / "absent.py", "anything") == -1


def test_occurrences_counts_every_occurrence(tmp_path):
    path = tmp_path / "a.py"
    path.write_text("x = 1\nx = 1\n", encoding="utf-8")

    assert p2g._occurrences(path, "x = 1") == 2


def test_short_digest_handles_none():
    assert p2g._short(None) == "none"
    assert p2g._short("abcdef123456789") == "abcdef123456"


def test_recorded_digests_keys_on_the_basename(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "assets_2a.json").write_text(json.dumps({
        "assets": [
            {"path": "models/all_active_497233292/497233292_fit.json",
             "sha256": "aaa"},
            {"path": "morphology/674389901_382982932_m.swc", "sha256": "bbb"},
            {"path": "no-digest.txt"},
        ]
    }), encoding="utf-8")
    monkeypatch.setattr(p2g, "CACHE", cache)

    recorded = p2g._recorded_digests()

    assert recorded == {"497233292_fit.json": "aaa",
                        "674389901_382982932_m.swc": "bbb"}


# ---------------------------------------------------------------------------
# The report ledger
# ---------------------------------------------------------------------------


def test_a_failing_check_is_retained_as_a_failure():
    report = p2g.Report()

    report.check(True, "a|passes")
    report.check(False, "a|fails", "why")

    assert report.failures == [("a|fails", "why")]


def test_summary_groups_checks_by_their_prefix():
    report = p2g.Report()

    report.check(True, "one|a")
    report.check(False, "one|b")
    report.check(True, "two|c")
    report.observe("note", "value")

    summary = report.summary()

    assert summary["checks"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["observations"] == 1
    assert summary["by_section"]["one"] == {"checks": 2, "failed": 1}
    assert summary["by_section"]["two"] == {"checks": 1, "failed": 0}


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def test_any_failing_check_blocks_the_verdict():
    report = p2g.Report()
    report.check(False, "provenance|something changed")

    verdict, rationale = p2g.decide(report)

    assert verdict == p2g.BLOCKED
    assert "1 check" in rationale


def test_an_unspecified_descriptor_blocks_the_verdict():
    report = p2g.Report()
    p2g.FINDINGS.update({
        "descriptor_compatible": None,
        "mechanisms_complete": True,
        "morphology_mappable": True,
        "axon_type_resolved": True,
    })

    verdict, rationale = p2g.decide(report)

    assert verdict == p2g.BLOCKED
    assert "descriptor_compatible" in rationale


def test_an_unresolved_axon_makes_the_verdict_conditional():
    report = p2g.Report()
    p2g.FINDINGS.update({
        "descriptor_compatible": True,
        "mechanisms_complete": True,
        "morphology_mappable": True,
        "axon_type_resolved": False,
    })

    verdict, rationale = p2g.decide(report)

    assert verdict == p2g.CONDITIONAL
    assert "axon branch" in rationale


def test_a_fully_specified_model_is_ready():
    report = p2g.Report()
    p2g.FINDINGS.update({
        "descriptor_compatible": True,
        "mechanisms_complete": True,
        "morphology_mappable": True,
        "axon_type_resolved": True,
    })

    verdict, _ = p2g.decide(report)

    assert verdict == p2g.READY


# ---------------------------------------------------------------------------
# Against the cached model
# ---------------------------------------------------------------------------


@requires_cache
def test_the_cached_descriptor_still_matches_its_expected_digest():
    spec = p2g.EXPECTED["descriptor"]
    identity = p2g.file_identity(p2g.CACHE / spec["rel"])

    assert identity["exists"] is True
    assert identity["bytes"] == spec["bytes"]
    assert identity["sha256"] == spec["sha256"]


@requires_cache
def test_the_descriptor_splits_its_genome_the_way_the_report_states():
    report = p2g.Report()

    parsed = p2g.section_descriptor(report)

    assert parsed["genome_entries"] == 42
    assert parsed["genome_by_section"] == {"soma": 12, "axon": 14,
                                           "apic": 8, "dend": 8}
    assert parsed["passive_keys"] == ["ra"]
    assert p2g.FINDINGS["descriptor_compatible"] is True


@requires_cache
def test_every_mechanism_the_genome_inserts_is_available():
    report = p2g.Report()
    descriptor = p2g.section_descriptor(report)

    mechanisms = p2g.section_mechanisms(report, descriptor)

    assert mechanisms["missing"] == []
    assert p2g.FINDINGS["mechanisms_complete"] is True


@requires_cache
def test_the_loader_contract_is_pinned_without_a_single_failed_claim():
    report = p2g.Report()
    descriptor = p2g.section_descriptor(report)

    contract = p2g.section_loader_contract(report, descriptor)

    assert contract["claims_failed"] == []
    assert contract["claims"] >= 30


@requires_cache
def test_the_wrong_loader_is_rejected_by_the_descriptor_alone():
    report = p2g.Report()
    descriptor = p2g.section_descriptor(report)

    p2g.section_loader_contract(report, descriptor)

    assert descriptor["passive_keys"] == ["ra"]
    assert all("KeyError" in label for label, ok, _ in report.checks
               if label.startswith("loader|the perisomatic loader"))


@requires_cache
def test_the_axon_branch_is_reported_as_unresolved_with_a_measured_divergence():
    report = p2g.Report()
    descriptor = p2g.section_descriptor(report)

    axon = p2g.section_axon(report, descriptor)

    assert axon["resolved"] is False
    assert p2g.FINDINGS["axon_type_resolved"] is False
    assert axon["geometry"]["available"] is True
    assert axon["geometry"]["n_roots"] == 1
    assert axon["geometry"]["area_ratio_min"] > 1.5
    assert [row[0] for row in axon["comparison"]] == [
        "Exact Allen implementation",
        "Reconstructed axon retained?",
        "Synthetic axon sections created?",
        "Biological assumptions",
        "Reproducibility implications",
        "Supported by published descriptor?",
    ]


@requires_cache
def test_the_substitute_morphology_carries_all_four_section_classes():
    report = p2g.Report()
    descriptor = p2g.section_descriptor(report)

    morphology = p2g.section_morphology(report, descriptor)

    assert morphology["census"]["soma"] == 1
    assert morphology["census"]["axon"] > 0
    assert morphology["census"]["apic"] > 0
    assert morphology["census"]["dend"] > 0
    assert morphology["addressable"] == 42
    assert morphology["fitted_reconstruction_present"] is False
    assert p2g.FINDINGS["morphology_mappable"] is True


@requires_cache
def test_the_draft_manifest_leaves_exactly_one_field_unresolved():
    report = p2g.Report()

    manifest = p2g.section_manifest(report)

    assert manifest["unresolved"] == ["biophys[1].axon_type"]
    assert "axon_type" not in manifest["grounded"]


@requires_cache
def test_sweep_41_is_in_sample_and_never_held_out():
    report = p2g.Report()
    observed = p2g.section_provenance(report)

    fitting = p2g.section_fitting(report, observed)

    assert fitting["fitting_sweeps"] == [41]
    assert fitting["perisomatic_fitting_sweeps"] == [38]
    assert 41 in p2g.COARSE_SWEEPS
    assert 41 not in p2g.HELD_OUT_SWEEPS


@requires_cache
def test_the_audit_runs_clean_and_concludes_conditionally_ready(tmp_path, capsys):
    destination = tmp_path / "summary.json"

    exit_code = p2g.main(["--json", str(destination)])
    capsys.readouterr()

    assert exit_code == 0
    summary = json.loads(destination.read_text(encoding="utf-8"))
    assert summary["verdict"] == p2g.CONDITIONAL
    assert summary["failed"] == 0
    assert summary["descriptor_matches_expected"] is True
    assert summary["axon_type_resolved"] is False
    assert summary["guard"]["leaked"] == []


def test_the_audit_module_never_imports_a_simulation_stack():
    assert "neuron" not in sys.modules
    assert "nrn" not in sys.modules
    assert "allensdk" not in sys.modules

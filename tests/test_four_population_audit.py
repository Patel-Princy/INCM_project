"""Tests for the Phase 0B four-population feasibility audit.

Two layers of checking:

* pure-function unit tests with hand-built records, so the filtering rules are
  pinned independently of the committed data;
* reproducibility tests that re-derive the published counts from
  ``cell_inventory.csv`` / ``sweep_inventory.csv`` and compare them with the
  four committed CSVs and the summary JSON.

No network access is used.  The CLI test writes only into ``tmp_path``.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import pytest

import four_population_audit as audit

RESULTS = audit.RESULTS_DIR
SUMMARY = RESULTS / "four_population_audit_summary.json"
REPORT = RESULTS / "FOUR_V1_POPULATION_FEASIBILITY_AUDIT.md"

FINAL_COUNTS = {"A": 63, "B": 30, "C": 79, "D": 20}
BOTH_COUNTS = {"A": 27, "B": 23, "C": 32, "D": 6}
SPINY_COUNTS = {"A": 54, "B": 7, "C": 41, "D": 8}
IDENTITY_COUNTS = {"A": 47, "B": 2, "C": 15, "D": 5}
IDENTITY_BOTH = {"A": 18, "B": 0, "C": 2, "D": 1}
POP_CONFIDENCE = {"A": "PROBABLE", "B": "LAYER-ONLY",
                  "C": "PROBABLE", "D": "PROBABLE"}
TOTALS = {"A": 458, "B": 311, "C": 505, "D": 272}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def make_cell(**overrides):
    cell = {
        "specimen_id": 485931158,
        "region_acronym": "VISp",
        "layer": "4",
        "structure_id": 721,
        "structure_acronym": "VISp4",
        "species": "Mus musculus",
        "driver_line": "Rorb-IRES2-Cre",
        "reporter_line": "Ai14",
        "genotype": "",
        "dendrite_type": "spiny",
        "apical_status": "not specified",
        "ephys_result_id": 485931155,
        "ephys_available": True,
        "ephys_failed": False,
        "sampling_rate_hz": 200_000,
        "nwb_file_id": 491316384,
        "nwb_download_url": "http://example.invalid/nwb/491316384",
        "has_morphology": True,
        "reconstruction_id": 485931801,
        "reconstruction_type": "dendrite-only",
        "reconstruction_superseded": False,
        "morphology_download_url": "http://example.invalid/swc/485931801",
        "phase0_eligibility": "PASS",
        "phase0_n_long_square_cc": 12,
        "phase0_n_biophysical": 1,
        "phase0_n_perisomatic": 1,
        "phase0_n_all_active": 0,
        "phase0_n_glif": 0,
    }
    cell.update(overrides)
    return cell


def make_model_row(model_id=486509958, specimen_id=485931158,
                   model_class="biophysical_perisomatic",
                   template_id=329230710, reconstruction_id=485931801):
    return {
        "model_id": model_id,
        "model_name": "m",
        "template_id": template_id,
        "template_name": "t",
        "model_class": model_class,
        "reconstruction_id": reconstruction_id,
        "availability_status": "metadata_present_download_reference_resolved",
        "well_known_file_id": 539256354,
        "file_path": "",
        "download_url": "",
    }


def sweep_rows(amplitudes, clamp_mode="current_clamp", units="Amps"):
    return [
        {
            "sweep_id": index,
            "sweep_number": index + 1,
            "stimulus_name": "Long Square",
            "stimulus_description": "C1LSCOARSE150216[0]",
            "stimulus_units": units,
            "clamp_mode": clamp_mode,
            "amplitude": amplitude,
            "duration": 1.0,
            "num_spikes": 3,
        }
        for index, amplitude in enumerate(amplitudes)
    ]


# ---------------------------------------------------------------------------
# Unit rule
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("clamp_mode,units,expected", [
    ("current_clamp", "Amps", True),
    ("current_clamp", "pA", True),
    ("", "pA", True),
    ("", "Amps", False),
    ("voltage_clamp", "pA", False),
    ("voltage_clamp", "Amps", False),
])
def test_units_aware_current_clamp_rule(clamp_mode, units, expected):
    assert audit.units_aware_current_clamp(clamp_mode, units) is expected


def test_voltage_clamp_rows_never_count_as_current_clamp():
    rows = sweep_rows([100.0, 200.0], clamp_mode="voltage_clamp")
    summary = audit.summarise_sweeps(rows)
    assert summary["n_long_square_rows"] == 2
    assert summary["n_long_square_cc"] == 0
    assert summary["n_depolarizing"] == 0


def test_implicit_current_clamp_rows_are_counted_separately():
    rows = sweep_rows([100.0, 200.0], clamp_mode="", units="pA")
    summary = audit.summarise_sweeps(rows)
    assert summary["n_long_square_cc"] == 2
    assert summary["n_implicit_cc"] == 2
    assert summary["n_explicit_cc"] == 0


# ---------------------------------------------------------------------------
# Sweep summaries
# ---------------------------------------------------------------------------
def test_float_noise_does_not_create_extra_amplitudes():
    rows = sweep_rows([170.000000188, 170.0000002, 190.0])
    summary = audit.summarise_sweeps(rows)
    assert summary["n_distinct_depolarizing"] == 2
    assert summary["n_repeated_depolarizing"] == 1


def test_depolarising_and_hyperpolarising_are_separated():
    rows = sweep_rows([-100.0, 0.0, 100.0, 200.0])
    summary = audit.summarise_sweeps(rows)
    assert summary["n_depolarizing"] == 2
    assert summary["n_hyperpolarizing"] == 1
    assert summary["depolarizing_min_pa"] == 100.0
    assert summary["depolarizing_max_pa"] == 200.0


def test_missing_amplitude_is_not_silently_treated_as_zero():
    rows = sweep_rows([100.0, None])
    summary = audit.summarise_sweeps(rows)
    assert summary["n_long_square_cc"] == 2
    assert summary["n_missing_amplitude"] == 1
    assert summary["n_depolarizing"] == 1


# ---------------------------------------------------------------------------
# Identity evidence
# ---------------------------------------------------------------------------
def test_identity_is_never_confirmed_for_any_plausible_input():
    lines = ["", "wt", "Cux2-CreERT2", "Rbp4-Cre_KL100", "Ntsr1-Cre_GN220",
             "Pvalb-IRES-Cre", "Scnn1a-Tg3-Cre", "Rorb-IRES2-Cre"]
    dendrites = ["", "spiny", "aspiny", "sparsely spiny", "unknown"]
    layers = ["1", "2/3", "4", "5", "6a", "6b"]
    for layer in layers:
        for line in lines:
            for dendrite in dendrites:
                result = audit.classify_identity(layer, line, dendrite, "")
                assert result["confidence"] != "CONFIRMED"
                assert result["confidence"] in {
                    "PROBABLE", "LAYER-ONLY", "UNRESOLVED", "NOT-CANDIDATE"}


@pytest.mark.parametrize("population,line,layer", [
    ("A", "Rorb-IRES2-Cre", "4"),
    ("A", "Scnn1a-Tg3-Cre", "4"),
    ("B", "Cux2-CreERT2", "2/3"),
    ("C", "Rbp4-Cre_KL100", "5"),
    ("D", "Ntsr1-Cre_GN220", "6a"),
])
def test_probable_identity_requires_layer_line_and_spiny_morphology(
        population, line, layer):
    result = audit.classify_identity(layer, line, "spiny", "none")
    assert result["confidence"] == "PROBABLE"
    assert result["class"] == population


def test_spiny_cell_with_uninformative_line_is_layer_only():
    result = audit.classify_identity("4", "Slc17a6-IRES-Cre", "spiny", "")
    assert result["confidence"] == "LAYER-ONLY"
    assert result["class"] is None


def test_class_line_in_the_wrong_layer_is_unresolved():
    result = audit.classify_identity("5", "Cux2-CreERT2", "spiny", "")
    assert result["confidence"] == "UNRESOLVED"
    assert result["class"] is None


def test_class_line_with_non_spiny_morphology_is_unresolved():
    result = audit.classify_identity("5", "Rbp4-Cre_KL100", "aspiny", "")
    assert result["confidence"] == "UNRESOLVED"


def test_gabaergic_line_with_non_spiny_morphology_is_not_a_candidate():
    result = audit.classify_identity("2/3", "Pvalb-IRES-Cre", "aspiny", "")
    assert result["confidence"] == "NOT-CANDIDATE"
    assert result["class"] is None


def test_gabaergic_line_with_spiny_morphology_is_unresolved_not_probable():
    result = audit.classify_identity("5", "Sst-IRES-Cre", "spiny", "")
    assert result["confidence"] == "UNRESOLVED"


def test_identity_evidence_always_states_that_projection_is_unmeasured():
    result = audit.classify_identity("4", "Rorb-IRES2-Cre", "spiny", "")
    assert "projection identity is not measured" in result["reason"]


def test_base_driver_line_strips_wt_suffix():
    assert audit.base_driver_line("Htr3a-Cre_NO152;wt") == "Htr3a-Cre_NO152"
    assert audit.base_driver_line("wt") == ""
    assert audit.base_driver_line("") == ""


def test_population_confidence_thresholds():
    def record(confidence):
        return {"identity": {"confidence": confidence}, "flags": {"stage_12": True}}

    assert audit.population_confidence([record("PROBABLE")] * 3) == "PROBABLE"
    # Two PROBABLE final cells without any LAYER-ONLY cell are not enough for a
    # population-level claim; the label falls back to UNRESOLVED.
    assert audit.population_confidence([record("PROBABLE")] * 2) == "UNRESOLVED"
    assert audit.population_confidence(
        [record("PROBABLE"), record("PROBABLE"), record("LAYER-ONLY")]
    ) == "LAYER-ONLY"
    assert audit.population_confidence([record("UNRESOLVED")] * 4) == "UNRESOLVED"
    assert audit.population_confidence([]) == "UNRESOLVED"


# ---------------------------------------------------------------------------
# Stage flags
# ---------------------------------------------------------------------------
def test_stage_flags_are_monotonic():
    cell = make_cell()
    sweep = audit.summarise_sweeps(sweep_rows([100.0, 200.0] * 4))
    model = audit.summarise_models([make_model_row()])
    flags = audit.build_stage_flags(cell, sweep, model, True)
    for stage in range(8, 13):
        if flags[f"stage_{stage:02d}"]:
            assert flags["stage_06"]
    assert flags["stage_12b"] == (flags["stage_12"] and flags["stage_09"])
    assert flags["stage_12e"] == flags["stage_12"]


def test_stage_twelve_requires_morphology():
    cell = make_cell()
    sweep = audit.summarise_sweeps(sweep_rows([100.0, 200.0] * 4))
    model = audit.summarise_models([make_model_row()])
    assert audit.build_stage_flags(cell, sweep, model, True)["stage_12"] is True
    assert audit.build_stage_flags(cell, sweep, model, False)["stage_12"] is False


def test_first_failing_requirement_follows_declared_order():
    status = {key: True for key, _label in audit.REQUIREMENTS}
    status["morphology_asset"] = False
    assert audit.first_failing_requirement(status) == "morphology_asset"
    status["biophysical_model"] = False
    assert audit.first_failing_requirement(status) == "biophysical_model"
    assert audit.failed_requirements(status) == "biophysical_model;morphology_asset"


def test_morphology_usable_requires_reference_and_not_superseded():
    assert audit.morphology_usable(make_cell())[0] is True
    assert audit.morphology_usable(make_cell(has_morphology=False))[0] is False
    assert audit.morphology_usable(make_cell(reconstruction_id=None))[0] is False
    assert audit.morphology_usable(make_cell(morphology_download_url=""))[0] is False
    assert audit.morphology_usable(make_cell(reconstruction_superseded=True))[0] is False


def test_build_records_detects_model_count_mismatch():
    cell = make_cell(phase0_n_perisomatic=1)
    with pytest.raises(RuntimeError, match="model_inventory gives n_perisomatic=0"):
        audit.build_records([cell], {}, {})


# ---------------------------------------------------------------------------
# Published outputs
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def counts():
    return read_csv(RESULTS / "four_population_counts.csv")


@pytest.fixture(scope="module")
def candidates():
    return read_csv(RESULTS / "four_population_candidates.csv")


@pytest.fixture(scope="module")
def exclusions():
    return read_csv(RESULTS / "four_population_exclusions.csv")


@pytest.fixture(scope="module")
def model_rows():
    return read_csv(RESULTS / "four_population_model_availability.csv")


@pytest.fixture(scope="module")
def summary():
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def raw_cells():
    return [row for row in read_csv(audit.CELL_CSV)
            if row["region_acronym"] == "VISp"
            and row["species"] == "Mus musculus"]


def test_summary_quality_checks_all_pass(summary):
    failed = [check for check in summary["quality_checks"] if not check["ok"]]
    assert not failed, failed


def test_source_hashes_match_the_phase0_manifest():
    report = audit.verify_sources(
        [audit.CELL_CSV, audit.SWEEP_CSV, audit.MODEL_CSV])
    assert all(item["ok"] for item in report)


def test_counts_schema_and_stage_coverage(counts):
    assert list(counts[0].keys()) == audit.COUNT_COLUMNS
    assert len(counts) == len(audit.STAGES) * len(audit.POPULATIONS)
    for pop in audit.POPULATIONS:
        stages = [int(row["stage"]) for row in counts if row["population"] == pop["key"]]
        assert stages == list(range(1, 13))


def test_stage_one_reproduces_the_cell_inventory(raw_cells, counts):
    per_layer = Counter(row["cortical_layer"] for row in raw_cells)
    assert per_layer["4"] == TOTALS["A"]
    assert per_layer["2/3"] == TOTALS["B"]
    assert per_layer["5"] == TOTALS["C"]
    assert per_layer["6a"] + per_layer["6b"] == TOTALS["D"]
    stage_one = {row["population"]: int(row["n"])
                 for row in counts if row["stage"] == "1"}
    assert stage_one == TOTALS
    assert sum(stage_one.values()) == 1546
    assert len(raw_cells) == 1588


def test_recording_stages_exclude_only_failed_ephys(raw_cells, counts):
    for row in counts:
        if row["stage"] not in {"2", "3", "4", "5", "6"}:
            continue
        key = row["population"]
        layers = audit.POPULATIONS[[pop["key"] for pop in audit.POPULATIONS].index(key)]["layers"]
        subset = [cell for cell in raw_cells if cell["cortical_layer"] in layers]
        usable = [cell for cell in subset
                  if cell["ephys_available"].lower() == "true"
                  and cell["ephys_failed"].lower() != "true"]
        assert int(row["n"]) == len(usable), (key, row["stage"])


def test_stage_six_recomputed_independently_from_sweeps(counts):
    """Re-derive the units-aware recording funnel without calling the module."""
    family = {pop["key"]: set(pop["layers"]) for pop in audit.POPULATIONS}
    usable_cell = {}
    for row in read_csv(audit.CELL_CSV):
        if row["region_acronym"] != "VISp" or row["species"] != "Mus musculus":
            continue
        usable_cell[row["specimen_id"]] = (
            row["cortical_layer"],
            row["ephys_available"].lower() == "true"
            and row["ephys_failed"].lower() != "true"
            and bool(row["nwb_download_url"]),
        )
    sweeps = {key: [] for key in family}
    for row in read_csv(audit.SWEEP_CSV):
        if row["region_acronym"] != "VISp" or row["stimulus_category"] != "long_square":
            continue
        cell = usable_cell.get(row["specimen_id"])
        if not cell:
            continue
        mode = row["clamp_mode"].strip().lower()
        cc = mode == "current_clamp" or (not mode and row["stimulus_units"] == "pA")
        if not cc:
            continue
        try:
            amplitude = float(row["stimulus_absolute_amplitude"])
        except (TypeError, ValueError):
            continue
        for key, layers in family.items():
            if cell[0] in layers:
                sweeps[key].append((row["specimen_id"], round(amplitude, 3),
                                    cell[1]))
    stage_six = {row["population"]: int(row["n"])
                 for row in counts if row["stage"] == "6"}
    for key, rows in sweeps.items():
        by_cell = {}
        for specimen_id, amplitude, ephys_ok in rows:
            bucket = by_cell.setdefault(
                specimen_id, {"n": 0, "dep_sweeps": 0, "dep": set(), "ok": ephys_ok})
            bucket["n"] += 1
            if amplitude > 0:
                bucket["dep_sweeps"] += 1
                bucket["dep"].add(amplitude)
        eligible = sum(1 for bucket in by_cell.values()
                       if bucket["ok"] and bucket["n"] >= 6
                       and bucket["dep_sweeps"] >= 3
                       and len(bucket["dep"]) >= 2)
        assert eligible == stage_six[key], key


def test_final_counts_and_totals(counts, summary):
    final = {row["population"]: int(row["n"])
             for row in counts if row["stage"] == "12"}
    assert final == FINAL_COUNTS
    assert summary["totals"]["four_population_final_any"] == sum(FINAL_COUNTS.values())
    assert summary["totals"]["visp_mouse_specimens"] == 1588
    assert summary["totals"]["four_population_specimens"] == 1546
    assert summary["totals"]["outside_populations"] == 42


def test_candidates_match_the_final_counts(candidates):
    per_pop = Counter(row["population"] for row in candidates)
    assert dict(per_pop) == FINAL_COUNTS
    ids = [row["specimen_id"] for row in candidates]
    assert len(ids) == len(set(ids))


def test_candidates_belong_to_the_population_layer(candidates):
    for row in candidates:
        population = next(pop for pop in audit.POPULATIONS
                          if pop["key"] == row["population"])
        assert row["layer"] in population["layers"], row


def test_model_ids_are_model_ids_not_specimen_ids(candidates):
    for row in candidates:
        for column in ("perisomatic_model_id", "all_active_model_id"):
            if row[column]:
                assert row[column] != row["specimen_id"]
                assert row[column].isdigit()


def test_model_templates_match_the_declared_classes(candidates):
    for row in candidates:
        if row["perisomatic_model_id"]:
            assert row["perisomatic_template_id"] == str(audit.PERISOMATIC_TEMPLATE_ID)
        if row["all_active_model_id"]:
            assert row["all_active_template_id"] == str(audit.ALL_ACTIVE_TEMPLATE_ID)


def test_exclusions_cover_every_nonfinal_specimen(exclusions):
    assert len(exclusions) == 1546 - sum(FINAL_COUNTS.values())
    assert all(row["first_failing_requirement"] for row in exclusions)
    assert all(row["failed_requirements"] for row in exclusions)


def test_exclusions_record_the_three_failed_recordings(exclusions):
    failed = [row for row in exclusions if row["ephys_failed"] == "true"]
    assert len(failed) == 3
    assert all(row["first_failing_requirement"] == "ephys_available_and_not_failed"
               for row in failed)


def test_exclusion_reasons_sum_to_the_shortfall(exclusions):
    reasons = Counter(row["first_failing_requirement"] for row in exclusions)
    assert sum(reasons.values()) == len(exclusions)
    assert set(reasons) <= {key for key, _label in audit.REQUIREMENTS}


def test_model_availability_agrees_with_the_candidates(candidates, model_rows):
    assert len(model_rows) == 4
    assert list(model_rows[0].keys()) == audit.MODEL_COLUMNS
    by_pop = {row["population"]: row for row in model_rows}
    for key in FINAL_COUNTS:
        final = [row for row in candidates if row["population"] == key]
        row = by_pop[key]
        assert int(row["n_final_any_model"]) == FINAL_COUNTS[key]
        assert int(row["n_final_both_models"]) == BOTH_COUNTS[key]
        assert int(row["n_final_spiny"]) == SPINY_COUNTS[key]
        assert int(row["n_final_identity_compatible"]) == IDENTITY_COUNTS[key]
        assert int(row["n_final_identity_both"]) == IDENTITY_BOTH[key]
        assert int(row["n_final_both_models"]) == sum(
            1 for item in final if item["has_both"] == "true")


def test_model_evidence_levels_are_not_conflated(model_rows):
    for row in model_rows:
        assert int(row["n_listed_any"]) == int(row["n_any_biophysical"])
        assert int(row["n_validated_against_recording"]) == 0
        assert int(row["n_descriptor_resolved"]) <= int(row["n_any_biophysical"])
        assert int(row["n_executable_in_repo"]) <= int(row["n_assets_in_repo"])


def test_only_the_reference_specimen_has_model_assets_in_the_repo(model_rows):
    by_pop = {row["population"]: row for row in model_rows}
    assert int(by_pop["B"]["n_assets_in_repo"]) == 1
    for key in ("A", "C", "D"):
        assert int(by_pop[key]["n_assets_in_repo"]) == 0


def test_no_output_claims_a_confirmed_identity(candidates, summary):
    assert all(row["identity_confidence"] != "CONFIRMED" for row in candidates)
    for pop in summary["populations"]:
        assert pop["identity"]["population_confidence"] != "CONFIRMED"


def test_population_identity_confidence(summary):
    assert {pop["key"]: pop["identity"]["population_confidence"]
            for pop in summary["populations"]} == POP_CONFIDENCE


def test_identity_compatible_cells_always_have_a_class(candidates):
    for row in candidates:
        if row["identity_confidence"] == "PROBABLE":
            assert row["identity_class"] == row["population"]
        else:
            assert row["identity_class"] == ""


def test_cli_regenerates_the_published_tables(tmp_path):
    out = tmp_path / "out"
    code = audit.main([
        "--out-dir", str(out),
        "--summary", str(out / "summary.json"),
    ])
    assert code == 0
    regenerated = read_csv(out / "four_population_counts.csv")
    published = read_csv(RESULTS / "four_population_counts.csv")
    assert regenerated == published
    assert (out / "four_population_candidates.csv").exists()
    assert (out / "four_population_exclusions.csv").exists()
    assert (out / "four_population_model_availability.csv").exists()


def test_report_quotes_the_published_counts():
    if not REPORT.exists():
        pytest.skip("report not written yet")
    text = REPORT.read_text(encoding="utf-8")
    final = ", ".join(f"{key}={value}" for key, value in FINAL_COUNTS.items())
    both = ", ".join(f"{key}={value}" for key, value in BOTH_COUNTS.items())
    identity = ", ".join(f"{key}={value}" for key, value in IDENTITY_COUNTS.items())
    confidence = ", ".join(f"{key}={value}" for key, value in POP_CONFIDENCE.items())
    assert final in text
    assert both in text
    assert identity in text
    assert confidence in text


def test_report_states_the_identity_limitation():
    if not REPORT.exists():
        pytest.skip("report not written yet")
    text = REPORT.read_text(encoding="utf-8")
    assert "no projection" in text.lower()
    assert "CONFIRMED" in text
    assert re.search(r"layer-defined", text, re.IGNORECASE)

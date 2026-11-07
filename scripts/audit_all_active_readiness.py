"""Phase 2G-A: static execution-readiness audit of the all-active model 497233292.

What this script does
---------------------
It reads files. Nothing else. It does not import NEURON, does not compile a
``.mod`` file, does not import or call AllenSDK's simulation runner, does not
touch the NWB, and does not alter any model parameter. Every number it reports
is derived from one of:

* the cached ``497233292_fit.json`` descriptor,
* the cached substitute SWC and marker,
* the cached AllenSDK v2.16.2 source tree,
* the Phase 2B draft manifest and its provenance sidecar,
* the Phase 2A asset record (``assets_2a.json``).

What it deliberately does *not* do
----------------------------------
The ``axon_type`` question cannot be settled by importing anything, so the
script does not try. It reproduces Allen's two branches **statically** from the
SWC geometry, reports the divergence between them, and records that neither
branch can be established as the configuration the published parameters were
fitted under. That is a finding, not a gap to be closed by assertion.

Evidence vocabulary used in the output and the report
-----------------------------------------------------
OBSERVED    measured in a file, reproducible from a digest
DERIVED     a consequence of OBSERVED facts plus AllenSDK source, no unknowns
ASSUMED     true only if an unrecorded choice is made
UNAVAILABLE not derivable from any published artefact

Running it
----------
    python scripts/audit_all_active_readiness.py
    python scripts/audit_all_active_readiness.py --json tmp/phase2g_a_summary.json

Exit status is 0 when every check passes. A failing check does not mean the
model is broken; it means the audit found something the report must not paper
over.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = PROJECT_ROOT / "tmp" / "model_cache"
DEFAULT_JSON = PROJECT_ROOT / "tmp" / "phase2g_a_summary.json"

# ---------------------------------------------------------------------------
# Fixed model identity.  These are the facts the brief fixes, not choices made
# here.  Everything else in the script derives from the files.
# ---------------------------------------------------------------------------

SPECIMEN_ID = 382982932
MODEL_ID = 497233292
TEMPLATE_ID = 491455321
FITTING_RECONSTRUCTION_ID = 491771090       # published as fitted, absent from the API
SUBSTITUTE_RECONSTRUCTION_ID = 674389884    # the specimen's own published morphology
SUBSTITUTE_SWC_ID = 674389901
SUBSTITUTE_MARKER_ID = 674389910

FITTING_SWEEP = 41
PERISOMATIC_FITTING_SWEEP = 38
HELD_OUT_SWEEPS = (49, 50, 51, 52)
COARSE_BLOCK = "C1LSCOARSE150216"
FINEST_BLOCK = "C1LSFINEST150112"
COARSE_SWEEPS = tuple(range(24, 44))

ALL_ACTIVE_TYPE = "Biophysical - all active"
PERISOMATIC_TYPE = "Biophysical - perisomatic"

JUNCTION_POTENTIAL_MV = -14.0
CELSIUS_DEG_C = 34
V_INIT_MV = -90

EXPECTED_GENOME_ENTRIES = 42
EXPECTED_GENOME_BY_SECTION = {"soma": 12, "axon": 14, "apic": 8, "dend": 8}
EXPECTED_EREV_SECTIONS = ("soma", "axon", "apic", "dend")
EXPECTED_MODFILE_COUNT = 16

# Allen's own axon replacement geometry, read from the v2.16.2 source.
AXON_STUB_DIAM_UM = 1.0
AXON_SEGMENT_LENGTH_UM = 30.0
AXON_TRUNCATION_UM = 60.0
AXON_SEGMENTS = 2

# ---------------------------------------------------------------------------
# Digests.  Descriptor, SWC, marker and cell.hoc are pinned by Phase 2A's
# record; the two source files are pinned because Phase 2A recorded their
# digests when it downloaded them.
# ---------------------------------------------------------------------------

EXPECTED = {
    "descriptor": {
        "rel": "models/all_active_497233292/497233292_fit.json",
        "bytes": 5738,
        "sha256": "bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963",
    },
    "descriptor_perisomatic": {
        "rel": "models/perisomatic_473862496/382982932_fit.json",
        "bytes": 2891,
        "sha256": "d24d00aaed5a2a0ecf9752735b62254bba7ab3dc0d3627e61466f95b00a8e38f",
    },
    "swc": {
        "rel": "morphology/674389901_382982932_m.swc",
        "bytes": 335924,
        "sha256": "71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c",
    },
    "marker": {
        "rel": "morphology/674389910_382982932_m.marker",
        "bytes": 373,
        "sha256": "3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925",
    },
    "cell_hoc": {
        "rel": "allensdk/cell.hoc",
        "bytes": 715,
        "sha256": "9b8f73f8202f355ea6f0c9f27be23bf2cb9bd122d9abc4fb864af88401b9a26d",
    },
    "biophysical_utils": {
        "rel": "2b/src/AllenSDK-2.16.2/allensdk/model/biophysical/utils.py",
        "bytes": 16577,
        "sha256": "fbd5c75fdd66a0ed080a018da4e10eace7af71062c9cd1c60f48e4cb71910405",
    },
    "hoc_utils": {
        "rel": "2b/src/AllenSDK-2.16.2/allensdk/model/biophys_sim/neuron/hoc_utils.py",
        "bytes": 3333,
        "sha256": "c29daeaf4870bfd43c6f5c74530a3dedcdb21e4a4c1d797ac4ecd6999548115e",
    },
}

DRAFT_MANIFEST = CACHE / "manifest_drafts" / "all_active" / "manifest.json"
DRAFT_PROVENANCE = CACHE / "manifest_drafts" / "all_active" / "provenance.json"
FIXTURE_ALL_ACTIVE = CACHE / "allensdk" / "reference" / "manifest_all_active.json"
FIXTURE_PERISOMATIC = (
    CACHE / "allensdk" / "reference" / "manifest_perisomatic.json"
)
MODFILE_REFERENCE_DIR = CACHE / "allensdk" / "modfiles"
DRAFT_MODFILE_DIR = CACHE / "manifest_drafts" / "all_active" / "modfiles"
SOURCE_UTILS = CACHE / EXPECTED["biophysical_utils"]["rel"]
SOURCE_RUNNER = (
    CACHE / "2b/src/AllenSDK-2.16.2/allensdk/model/biophysical/runner.py"
)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


class Report:
    """Console plus JSON check ledger, in the style of the earlier phases."""

    def __init__(self) -> None:
        self.checks: list[tuple[str, bool, str]] = []
        self.observations: list[tuple[str, str]] = []
        self.sections: list[str] = []

    def banner(self, title: str) -> None:
        self.sections.append(title)
        print()
        print("=" * 78)
        print(title)
        print("=" * 78)

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.checks.append((label, bool(ok), detail))
        print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", label, detail))
        return bool(ok)

    def observe(self, label: str, detail: str = "") -> None:
        self.observations.append((label, detail))
        print("  %-10s %-56s %s" % ("report", label, detail))

    def note(self, text: str) -> None:
        for line in text.strip().splitlines():
            print("  .. " + line.strip())

    def skip(self, label: str, detail: str = "") -> None:
        print("  %-10s %-56s %s" % ("SKIP", label, detail))

    @property
    def failures(self) -> list[tuple[str, str]]:
        return [(label, detail) for label, ok, detail in self.checks if not ok]

    def summary(self) -> dict:
        by_section: dict[str, dict[str, int]] = {}
        for label, ok, _ in self.checks:
            bucket = by_section.setdefault(
                label.split("|")[0], {"checks": 0, "failed": 0}
            )
            bucket["checks"] += 1
            if not ok:
                bucket["failed"] += 1
        return {
            "checks": len(self.checks),
            "passed": len(self.checks) - len(self.failures),
            "failed": len(self.failures),
            "observations": len(self.observations),
            "by_section": by_section,
            "failures": [{"label": l, "detail": d} for l, d in self.failures],
        }


# ---------------------------------------------------------------------------
# File identity
# ---------------------------------------------------------------------------


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def file_identity(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"exists": False, "bytes": None, "sha256": None}
    return {
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256_of(path),
    }


def load_json(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# SWC geometry
# ---------------------------------------------------------------------------

SWC_CLASSES = {1: "soma", 2: "axon", 3: "dend", 4: "apic"}


def read_swc(path: pathlib.Path) -> list[dict]:
    """Parse an SWC file into records: id, type, x, y, z, radius, parent.

    SWC is a plain seven-column text format: index, structure type, x, y, z,
    radius, parent index.  Comments start with '#'; a parent of -1 marks a root.
    No interpretation happens here.
    """
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        if len(fields) < 7:
            continue
        try:
            rows.append(
                {
                    "id": int(fields[0]),
                    "type": int(fields[1]),
                    "x": float(fields[2]),
                    "y": float(fields[3]),
                    "z": float(fields[4]),
                    "r": float(fields[5]),
                    "parent": int(fields[6]),
                }
            )
        except ValueError:
            continue
    return rows


def _segment_length(child: dict, parent: dict) -> float:
    return math.dist((child["x"], child["y"], child["z"]),
                     (parent["x"], parent["y"], parent["z"]))


def axon_chain(rows: list[dict]) -> dict:
    """The axon root and every axon point reached from it, with path distance.

    This walks the SWC parent pointers, so the order is the reconstruction's own
    order rather than an inference from coordinates. Returns ``None`` values
    rather than raising when the morphology contains no axon, because "no axon"
    is exactly the case in which Allen's ``truncated`` branch cannot run.
    """
    by_id = {row["id"]: row for row in rows}
    soma_ids = {row["id"] for row in rows if row["type"] == 1}
    axon_rows = [row for row in rows if row["type"] == 2]
    roots = [row for row in axon_rows if row["parent"] in soma_ids]
    if not axon_rows or not roots:
        return {"available": False, "n_axon_points": len(axon_rows),
                "n_roots": len(roots), "chain": [], "path_um": []}

    # Radial walk from every root; each axon point is reached along its single
    # parent chain, so distance accumulates exactly once per point.
    path_um: dict[int, float] = {}
    depth: dict[int, int] = {}
    children = collections.defaultdict(list)
    for row in axon_rows:
        children[row["parent"]].append(row)

    chain: list[dict] = []
    queue = collections.deque()
    for root in roots:
        path_um[root["id"]] = 0.0
        depth[root["id"]] = 0
        queue.append(root)
    while queue:
        node = queue.popleft()
        chain.append(node)
        for child in children.get(node["id"], []):
            path_um[child["id"]] = path_um[node["id"]] + _segment_length(
                child, node)
            depth[child["id"]] = depth[node["id"]] + 1
            queue.append(child)

    ordered = sorted(chain, key=lambda r: (path_um[r["id"]], r["id"]))
    return {
        "available": True,
        "n_axon_points": len(axon_rows),
        "n_roots": len(roots),
        "root": roots[0],
        "chain": chain,
        "ordered": ordered,
        "path_um": path_um,
        "depth": depth,
        "total_path_um": max(path_um.values()) if path_um else 0.0,
    }


def _diameters_in_window(ordered: list[dict], path_um: dict[int, float],
                         lo_um: float, hi_um: float) -> list[float]:
    return [2.0 * row["r"] for row in ordered
            if lo_um <= path_um[row["id"]] <= hi_um]


def axon_branch_geometry(rows: list[dict]) -> dict:
    """Reproduce Allen's two axon branches statically from the SWC.

    Allen deletes every reconstructed axon section in both branches and creates
    ``axon[2]`` with L = 30 um. The branches differ in exactly two respects:

    ``stub``
        both diameters are 1.0 um, and ``axon[0]`` is attached at ``soma(0.5)``.

    ``truncated``
        ``axon[0].diam`` is the diameter of the imported proximal axon section
        and ``axon[1].diam`` is the diameter of the first axon section whose
        midpoint lies further than 60 um from the soma along the morphology;
        ``axon[0]`` is attached at ``soma(1.0)``.

    The exact per-section diameter that NEURON's Import3d assigns is *not*
    derivable without running NEURON, because Import3d aggregates several SWC
    points into one section and picks the section diameter itself. What is
    derivable is the range of diameters present in the SWC over the stretch the
    section covers, which bounds the answer. That is what this function returns,
    and it is why the report quotes a range rather than a scalar for
    ``axon[0].diam`` while quoting the measured plateau for ``axon[1].diam``.
    """
    info = axon_chain(rows)
    if not info["available"]:
        return {"available": False,
                "reason": "the morphology contains no soma-attached axon"}

    ordered = info["ordered"]
    path_um = info["path_um"]

    proximal = _diameters_in_window(
        ordered, path_um, 0.0, min(10.0, info["total_path_um"]))
    beyond = _diameters_in_window(
        ordered, path_um,
        AXON_TRUNCATION_UM - 5.0, AXON_TRUNCATION_UM + 10.0)

    if not proximal or not beyond:
        return {"available": False,
                "reason": "the axon is too short to sample both diameters"}

    segment_area = math.pi * AXON_SEGMENT_LENGTH_UM
    stub_area = segment_area * AXON_STUB_DIAM_UM * AXON_SEGMENTS

    distal_diam = sorted(beyond)[len(beyond) // 2]
    thin_area = segment_area * (min(proximal) + distal_diam)
    thick_area = segment_area * (max(proximal) + distal_diam)

    return {
        "available": True,
        "n_axon_points": info["n_axon_points"],
        "n_roots": info["n_roots"],
        "total_path_um": info["total_path_um"],
        "stub_diam_um": AXON_STUB_DIAM_UM,
        "truncated_proximal_diam_um_min": min(proximal),
        "truncated_proximal_diam_um_max": max(proximal),
        "truncated_distal_diam_um": distal_diam,
        "stub_attachment": "soma[0](0.5)",
        "truncated_attachment": "soma[0](1.0)",
        "stub_total_area_um2": stub_area,
        "truncated_total_area_um2_min": thin_area,
        "truncated_total_area_um2_max": thick_area,
        "area_ratio_min": stub_area / thick_area,
        "area_ratio_max": stub_area / thin_area,
        "distal_window_n": len(beyond),
        "distal_window_all_equal": len(set(round(d, 6) for d in beyond)) == 1,
    }


# ---------------------------------------------------------------------------
# AllenSDK facts, pinned as exact substrings
# ---------------------------------------------------------------------------
#
# Constraint 3 forbids touching NEURON and constraint 4 forbids importing the
# runner, so every claim about AllenSDK behaviour is pinned here as an exact
# substring of the cached v2.16.2 source instead. A reader can confirm any of
# them with one grep, which is the point: the audit must not be the only place
# where the loader contract is written down.

SOURCE_DESCRIPTION = (
    CACHE / "2b/src/AllenSDK-2.16.2/allensdk/config/model/description.py"
)
SOURCE_HOC_UTILS = CACHE / EXPECTED["hoc_utils"]["rel"]
FIXTURE_ALL_ACTIVE_TEST = (
    CACHE / "allensdk" / "reference" / "test_biophysical_all_active.py"
)
MODEL_RECORD = CACHE / "api" / "neuronal_model_497233292.json"

# The four section arrays the 42 genome entries address.
MORPHOLOGY_CLASS_ARRAYS = ("soma", "axon", "apic", "dend")

# Mechanisms NEURON supplies without a .mod file of that name.
NEURON_BUILTINS = frozenset({"pas", "cad", "hh", "exp2syn", "IClamp"})

# (label, file, exact substring, expected occurrences)
#
# The occurrence count is part of the assertion rather than a convenience. Two
# occurrences of ``for c in passive["cm"]:`` is the evidence that the
# perisomatic loader applies the descriptor's cm list and the all-active loader
# has the same loop commented out; one occurrence would not distinguish them.
SOURCE_CLAIMS = (
    (
        "create_utils reads biophys[1].axon_type before choosing a class",
        SOURCE_UTILS,
        'axon_type = description.data["biophys"][1]["axon_type"]',
        1,
    ),
    (
        "create_utils dispatches the all-active class with the axon type",
        SOURCE_UTILS,
        "return AllActiveUtils(description, axon_type)",
        1,
    ),
    (
        "create_utils dispatches the perisomatic class without it",
        SOURCE_UTILS,
        "return Utils(description)",
        1,
    ),
    (
        "AllActiveUtils.__init__ requires a second positional argument",
        SOURCE_UTILS,
        "def __init__(self, description, axon_type):",
        1,
    ),
    (
        "the stub branch is selected by comparing axon_type to 'stub'",
        SOURCE_UTILS,
        'if self.axon_type == "stub":',
        1,
    ),
    (
        "the stub branch delegates to the perisomatic morphology builder",
        SOURCE_UTILS,
        "super(AllActiveUtils, self).generate_morphology(morph_filename)",
        1,
    ),
    (
        "the truncated branch is the fall-through, not a positive test",
        SOURCE_UTILS,
        '"Legacy model - Truncating reconstructed axon after 60 micron"',
        1,
    ),
    (
        "the stub branch sets every axon diameter to 1 um",
        SOURCE_UTILS,
        "sec.diam = 1",
        1,
    ),
    (
        "the stub branch attaches the axon at soma(0.5)",
        SOURCE_UTILS,
        "h.axon[0].connect(h.soma[0], 0.5, 0.0)",
        1,
    ),
    (
        "the truncated branch attaches the axon at soma(1.0)",
        SOURCE_UTILS,
        "self.h.axon[0].connect(self.h.soma[0], 1.0, 0.0)",
        1,
    ),
    (
        "the truncated branch seeds both diameters from the imported axon[0]",
        SOURCE_UTILS,
        "axon_diams = [self.h.axon[0].diam, self.h.axon[0].diam]",
        1,
    ),
    (
        "the truncated branch samples the diameter beyond 60 um",
        SOURCE_UTILS,
        "if self.h.distance(0.5, sec=sec) > 60:",
        1,
    ),
    (
        "the truncated branch applies the sampled diameters to the two stubs",
        SOURCE_UTILS,
        "sec.diam = axon_diams[index]",
        1,
    ),
    (
        "both loaders set Ra from the passive block",
        SOURCE_UTILS,
        'sec.Ra = passive["ra"]',
        2,
    ),
    (
        "the all-active loader comments out the perisomatic cm list",
        SOURCE_UTILS,
        'for c in passive["cm"]:',
        2,
    ),
    (
        "the all-active loader comments out the perisomatic e_pas assignment",
        SOURCE_UTILS,
        'seg.pas.e = passive["e_pas"]',
        2,
    ),
    (
        "genome values are converted with float(), so they may be strings",
        SOURCE_UTILS,
        'param_value = float(p["value"])',
        1,
    ),
    (
        "a genome entry whose section array is missing is skipped silently",
        SOURCE_UTILS,
        "if hasattr(h, section_array):",
        1,
    ),
    (
        "ek is applied only where k_ion is already inserted",
        SOURCE_UTILS,
        'self.h.ismembrane("k_ion", sec=section) == 1',
        1,
    ),
    (
        "ena is applied only where na_ion is already inserted",
        SOURCE_UTILS,
        'self.h.ismembrane("na_ion", sec=section) == 1',
        1,
    ),
    (
        "neuron is imported inside HocUtils.__init__, never at module scope",
        SOURCE_HOC_UTILS,
        "\nimport neuron\n",
        0,
    ),
    (
        "nrn is imported inside HocUtils.__init__, never at module scope",
        SOURCE_HOC_UTILS,
        "\nimport nrn\n",
        0,
    ),
    (
        "HocUtils imports both NEURON bindings at once, inside __init__",
        SOURCE_HOC_UTILS,
        "    def __init__(self, description):\n        import neuron\n        import nrn",
        1,
    ),
    (
        "utils.py never imports neuron at module scope",
        SOURCE_UTILS,
        "\nimport neuron\n",
        0,
    ),
    (
        "the runner appends axon_type to the biophys section at load time",
        SOURCE_RUNNER,
        "axon_replacement_dict = {'axon_type': args_dict.get('axon_type', 'truncated')}",
        1,
    ),
    (
        "the runner writes the appended entry with Description.update_data",
        SOURCE_RUNNER,
        "description.update_data(axon_replacement_dict, 'biophys')",
        1,
    ),
    (
        "the runner's fix_sections list contains the 'axon_morph,' typo",
        SOURCE_RUNNER,
        "fix_sections = ['passive', 'axon_morph,', 'conditions', 'fitting']",
        1,
    ),
    (
        "the runner reads runs[0].sweeps_by_type unconditionally",
        SOURCE_RUNNER,
        "sweeps_by_type = run_params['sweeps_by_type']",
        1,
    ),
    (
        "the runner builds its utils through the factory, not by class name",
        SOURCE_RUNNER,
        "utils = create_utils(description)",
        1,
    ),
    (
        "the CLI default for --axon_type is truncated",
        SOURCE_RUNNER,
        "default='truncated', choices=['stub', 'truncated']",
        1,
    ),
    (
        "update_data appends to the section list rather than merging",
        SOURCE_DESCRIPTION,
        "self.data[section].append(data)",
        1,
    ),
    (
        "Allen's own all-active fixture test calls the one-argument constructor",
        FIXTURE_ALL_ACTIVE_TEST,
        "utils = AllActiveUtils(description)",
        1,
    ),
)

# Decisions the sections reach. The verdict is computed from these rather than
# written by hand, so that prose cannot drift away from the findings.
FINDINGS: dict[str, object] = {
    "descriptor_compatible": None,
    "mechanisms_complete": None,
    "morphology_mappable": None,
    "axon_type_resolved": None,
}


def _occurrences(path: pathlib.Path, needle: str) -> int:
    """Count *needle* in *path*; -1 when the file is absent."""
    if not path.exists():
        return -1
    text = path.read_text(encoding="utf-8", errors="replace")
    return text.count(needle)


def _recorded_digests() -> dict:
    """Digests recorded by Phase 2A, keyed by basename.

    Phase 2A wrote ``{path, url, bytes, sha256, provenance}`` per asset. The
    lookup is by basename because this audit addresses the cache by its own
    relative paths, which differ from Phase 2A's for the source files.
    """
    path = CACHE / "assets_2a.json"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for entry in load_json(path).get("assets", []):
        rel = entry.get("path")
        digest = entry.get("sha256")
        if rel and digest:
            out[pathlib.PurePosixPath(rel).name] = digest
    return out


def _short(digest: str | None) -> str:
    return "none" if not digest else digest[:12]


# ---------------------------------------------------------------------------
# Section 1: asset provenance
# ---------------------------------------------------------------------------


def section_provenance(report: Report) -> dict:
    """Every pinned asset, by size and digest, against two independent records."""
    report.banner("1. Asset provenance and hashes")

    observed: dict[str, dict] = {}
    recorded = _recorded_digests()
    report.observe(
        "Phase 2A asset record",
        "%d digests in assets_2a.json" % len(recorded),
    )

    for name, spec in EXPECTED.items():
        path = CACHE / spec["rel"]
        ident = file_identity(path)
        observed[name] = dict(ident, path=spec["rel"], basename=(
            pathlib.PurePosixPath(spec["rel"]).name))

        if not report.check(ident["exists"], "provenance|%s present" % name,
                            spec["rel"]):
            continue

        report.check(
            ident["bytes"] == spec["bytes"],
            "provenance|%s size" % name,
            "%d bytes%s" % (
                ident["bytes"],
                "" if ident["bytes"] == spec["bytes"]
                else " (expected %d)" % spec["bytes"],
            ),
        )
        report.check(
            ident["sha256"] == spec["sha256"],
            "provenance|%s sha256" % name,
            "match %s" % _short(ident["sha256"])
            if ident["sha256"] == spec["sha256"]
            else "expected %s, found %s" % (
                _short(spec["sha256"]), _short(ident["sha256"])),
        )

        base = observed[name]["basename"]
        if base in recorded:
            report.check(
                recorded[base] == ident["sha256"],
                "provenance|%s unchanged since Phase 2A" % name,
                "agrees with assets_2a.json" if recorded[base] == ident["sha256"]
                else "Phase 2A recorded %s" % _short(recorded[base]),
            )
        else:
            report.skip("provenance|%s not in the Phase 2A record" % name, base)

    report.note(
        "A mismatch here must be reported, not repaired: the fix, if one is\n"
        "needed, is to re-fetch and re-record the asset in a later phase."
    )
    return observed


# ---------------------------------------------------------------------------
# Section 2: the descriptor
# ---------------------------------------------------------------------------


def section_descriptor(report: Report) -> dict:
    """What the published fit descriptor does and does not specify."""
    report.banner("2. The all-active fit descriptor")

    path = CACHE / EXPECTED["descriptor"]["rel"]
    if not path.exists():
        report.check(False, "descriptor|present", str(path))
        return {}

    data = load_json(path)
    raw = path.read_text(encoding="utf-8", errors="replace")

    report.check(
        sorted(data) == ["conditions", "fitting", "genome", "passive"],
        "descriptor|top-level sections are the legacy all-active four",
        ", ".join(sorted(data)),
    )

    # -- passive -----------------------------------------------------------
    passive = data.get("passive") or []
    report.check(
        isinstance(passive, list) and len(passive) == 1,
        "descriptor|passive is a one-element list",
        "len=%d" % len(passive),
    )
    passive0 = passive[0] if passive else {}
    report.check(
        sorted(passive0) == ["ra"],
        "descriptor|passive carries ra and nothing else",
        ", ".join(sorted(passive0)),
    )
    report.check(
        "cm" not in passive0 and "e_pas" not in passive0,
        "descriptor|passive omits cm and e_pas",
        "the perisomatic loader reads both, unconditionally",
    )

    # -- fitting and conditions ------------------------------------------
    fitting = (data.get("fitting") or [{}])[0]
    report.check(
        fitting.get("sweeps") == [FITTING_SWEEP],
        "descriptor|fitting sweep is 41 alone",
        str(fitting.get("sweeps")),
    )
    report.check(
        float(fitting.get("junction_potential")) == JUNCTION_POTENTIAL_MV,
        "descriptor|junction potential is -14 mV",
        str(fitting.get("junction_potential")),
    )

    conditions = (data.get("conditions") or [{}])[0]
    report.check(
        conditions.get("celsius") == CELSIUS_DEG_C,
        "descriptor|celsius is 34",
        str(conditions.get("celsius")),
    )
    report.check(
        conditions.get("v_init") == V_INIT_MV,
        "descriptor|v_init is -90 mV",
        str(conditions.get("v_init")),
    )

    erev = {e["section"]: (float(e["ek"]), float(e["ena"]))
            for e in conditions.get("erev", [])}
    report.check(
        sorted(erev) == sorted(EXPECTED_EREV_SECTIONS),
        "descriptor|erev covers the four section classes",
        ", ".join(sorted(erev)),
    )
    report.check(
        all(ek == -107.0 and ena == 53.0 for ek, ena in erev.values()),
        "descriptor|ek and ena are uniform across section classes",
        "ek -107, ena 53",
    )

    # -- genome -----------------------------------------------------------
    genome = data.get("genome", [])
    report.check(
        len(genome) == EXPECTED_GENOME_ENTRIES,
        "descriptor|genome has 42 entries",
        str(len(genome)),
    )
    report.check(
        all(sorted(g) == ["mechanism", "name", "section", "value"]
            for g in genome),
        "descriptor|every genome entry has the same four keys",
        "section, mechanism, name, value",
    )
    report.check(
        all(isinstance(g["value"], str) for g in genome),
        "descriptor|every genome value is a string",
        "the loader converts with float()",
    )

    counts = collections.Counter(g["section"] for g in genome)
    report.check(
        counts == collections.Counter(EXPECTED_GENOME_BY_SECTION),
        "descriptor|genome splits 12/14/8/8 across soma/axon/apic/dend",
        ", ".join("%s=%d" % (s, counts[s])
                  for s in MORPHOLOGY_CLASS_ARRAYS),
    )

    names_by_section: dict[str, set] = collections.defaultdict(set)
    for entry in genome:
        names_by_section[entry["section"]].add(entry["name"])
    report.check(
        all({"cm", "Ra", "g_pas", "e_pas"} <= names_by_section[section]
            for section in EXPECTED_GENOME_BY_SECTION),
        "descriptor|every section sets cm, Ra, g_pas and e_pas in the genome",
        "so the passive block's ra is superseded",
    )

    # This is the load-bearing detail for the loader contract: Ra arrives twice
    # and the genome wins, because the genome loop runs after the passive loop.
    ra_from_genome = {
        entry["section"]: entry["value"] for entry in genome
        if entry["name"] == "Ra"
    }
    report.check(
        bool(ra_from_genome) and all(
            entry["value"] != str(passive0.get("ra")) for entry in genome
            if entry["name"] == "Ra"
        ),
        "descriptor|genome Ra differs from passive ra on every section",
        ", ".join("%s=%s" % (s, v) for s, v in ra_from_genome.items()),
    )

    axon_mechanisms = sorted({
        entry["mechanism"] for entry in genome
        if entry["section"] == "axon" and entry["mechanism"]
    })
    report.check(
        len(axon_mechanisms) >= 9,
        "descriptor|the axon carries active conductances",
        ", ".join(axon_mechanisms),
    )

    # -- what the descriptor cannot say -----------------------------------
    report.check(
        "axon_type" not in raw,
        "descriptor|contains no axon_type field",
        "so the branch is not recorded here",
    )
    report.check(
        "axon_morph" not in raw,
        "descriptor|contains no axon_morph section",
        "the schema can carry one; this model's does not",
    )

    FINDINGS["descriptor_compatible"] = True
    return {
        "genome_entries": len(genome),
        "genome_by_section": dict(counts),
        "names_by_section": {k: sorted(v) for k, v in names_by_section.items()},
        "axon_mechanisms": axon_mechanisms,
        "ra_from_genome": ra_from_genome,
        "passive_keys": sorted(passive0),
    }


# ---------------------------------------------------------------------------
# Section 3: mechanisms
# ---------------------------------------------------------------------------


def _modfile_set(directory: pathlib.Path) -> dict:
    if not directory.exists():
        return {}
    return {path.name: sha256_of(path)
            for path in sorted(directory.glob("*.mod"))}


def section_mechanisms(report: Report, descriptor: dict) -> dict:
    """Whether every mechanism the descriptor asks for is actually available."""
    report.banner("3. Mechanisms and the canonical set")

    reference = _modfile_set(MODFILE_REFERENCE_DIR)
    draft = _modfile_set(DRAFT_MODFILE_DIR)

    report.check(
        len(reference) == EXPECTED_MODFILE_COUNT,
        "mechanism|the canonical set holds 16 .mod files",
        str(len(reference)),
    )
    report.check(
        set(draft) == set(reference),
        "mechanism|the draft modfile directory mirrors the canonical set",
        "%d files, same names" % len(draft),
    )
    identical = [name for name in reference
                 if draft.get(name) == reference[name]]
    report.check(
        len(identical) == len(reference),
        "mechanism|every draft .mod is byte-identical to its canonical copy",
        "%d/%d" % (len(identical), len(reference)),
    )

    used = sorted(_descriptor_mechanisms())
    stems = {pathlib.PurePosixPath(name).stem for name in reference}
    missing = [name for name in used
               if name not in stems and name not in NEURON_BUILTINS]
    unused = sorted(stems - set(used))

    report.check(
        not missing,
        "mechanism|every mechanism the genome inserts has a .mod file",
        "none missing" if not missing else ", ".join(missing),
    )
    report.check(
        "pas" in NEURON_BUILTINS,
        "mechanism|pas is a NEURON built-in, so no pas.mod is required",
        "inserted explicitly by both loaders",
    )
    report.observe("mechanisms used", ", ".join(used))
    report.observe(
        "mechanisms shipped but unused",
        ", ".join(unused) if unused else "none",
    )

    FINDINGS["mechanisms_complete"] = not missing
    return {
        "modfiles": sorted(reference),
        "used": used,
        "unused": unused,
        "missing": missing,
        "identical_to_canonical": len(identical),
    }


def _genome() -> list:
    """The descriptor's genome block, or an empty list when it is absent."""
    path = CACHE / EXPECTED["descriptor"]["rel"]
    if not path.exists():
        return []
    return load_json(path).get("genome", [])


def _descriptor_mechanisms() -> set:
    """Mechanism names the descriptor inserts, independent of section."""
    return {entry["mechanism"] for entry in _genome()
            if entry.get("mechanism")}


# ---------------------------------------------------------------------------
# Section 4: the loader contract
# ---------------------------------------------------------------------------


def section_loader_contract(report: Report, descriptor: dict) -> dict:
    """Rebuild the loader's contract from source and from the descriptor."""
    report.banner("4. The all-active loader contract")

    # -- the source claims ------------------------------------------------
    for label, path, needle, expected in SOURCE_CLAIMS:
        found = _occurrences(path, needle)
        report.check(
            found == expected,
            "loader|" + label,
            "x%d" % found if found == expected
            else "expected x%d, found x%d in %s" % (expected, found, path.name),
        )

    # -- ordering: pas must be inserted before any genome value is set ----
    source = SOURCE_UTILS.read_text(encoding="utf-8", errors="replace")
    insert_pas = source.rindex('sec.insert("pas")')
    set_genome = source.index("param_value = float")
    report.check(
        insert_pas < set_genome,
        "loader|pas is inserted before the genome loop assigns e_pas",
        "otherwise setattr(sec, 'e_pas') would not resolve",
    )

    # -- the wrong loader fails loudly, and statically -------------------
    # This reproduces Utils.load_cell_parameters' two lookups against the
    # all-active passive block. No AllenSDK code is called; the point is that
    # the descriptor alone decides the question.
    passive0 = (load_json(CACHE / EXPECTED["descriptor"]["rel"])
                .get("passive") or [{}])[0]
    raised = []
    for key in ("cm", "e_pas"):
        try:
            passive0[key]
        except KeyError:
            raised.append(key)
    report.check(
        raised == ["cm", "e_pas"],
        "loader|the perisomatic loader would raise KeyError on this passive block",
        "missing " + ", ".join(raised),
    )
    report.check(
        descriptor.get("passive_keys") == ["ra"],
        "loader|the all-active loader reads only ra from passive",
        "the descriptor supplies exactly that",
    )

    # -- section classes --------------------------------------------------
    names = descriptor.get("names_by_section", {})
    resolved = {section: sorted(value) for section, value in names.items()}
    report.check(
        sorted(names) == sorted(EXPECTED_GENOME_BY_SECTION),
        "loader|genome addresses exactly the four section classes",
        ", ".join(sorted(names)),
    )
    glob_entries = [e for e in _genome() if e.get("section") == "glob"]
    report.check(
        not glob_entries,
        "loader|no genome entry uses the 'glob' escape hatch",
        "every entry is per-section, so hasattr() must resolve",
    )
    report.note(
        "Every genome entry is per-section, so the loader's hasattr(h, section)\n"
        "gate must resolve for all four arrays. generate_morphology creates\n"
        "axon[2] in both branches, so the axon array always exists; the SWC must\n"
        "supply soma, apic and dend. That is checked in section 5."
    )

    parameter_map = {
        "Ra": "section range variable, applies to every segment",
        "cm": "section range variable, applies to every segment",
        "g_pas": "pas mechanism variable, present after insert('pas')",
        "e_pas": "pas mechanism variable, present after insert('pas')",
        "gbar_*": "mechanism variable on the inserted mechanism",
    }
    report.observe(
        "parameter kinds resolved",
        "%d distinct genome names: %s" % (
            len({n for values in names.values() for n in values}),
            ", ".join(sorted({n for values in names.values() for n in values})),
        ),
    )

    return {
        "claims": len(SOURCE_CLAIMS),
        "claims_failed": [label for label, path, needle, expected in SOURCE_CLAIMS
                          if _occurrences(path, needle) != expected],
        "parameter_map": parameter_map,
        "resolved_by_section": resolved,
    }


# ---------------------------------------------------------------------------
# Section 5: axon_type, the primary blocker
# ---------------------------------------------------------------------------

# The comparison the brief asks for, filled with what the source and the SWC
# actually say. Nothing here is inferred from the perisomatic model.
AXON_COMPARISON = (
    (
        "Exact Allen implementation",
        "AllActiveUtils.generate_morphology returns early through "
        "Utils.generate_morphology: delete every axon* section, create axon[2], "
        "L=30, diam=1, nseg=1, attach axon[0] to soma(0.5).",
        "AllActiveUtils.generate_morphology does not delegate: nseg is set on "
        "the imported cell, axon_diams[0] comes from axon[0].diam before "
        "deletion, axon_diams[1] from the first axon section whose midpoint is "
        "further than 60 um from the soma, then the same two 30 um sections are "
        "created and axon[0] is attached to soma(1.0).",
    ),
    (
        "Reconstructed axon retained?",
        "No. Every section whose name starts with 'axon' is deleted before the "
        "stub is created.",
        "No. The same deletion loop runs. Only two diameters are sampled from "
        "the reconstruction before it is discarded.",
    ),
    (
        "Synthetic axon sections created?",
        "Yes: axon[2], 30 um each, diameter 1 um, nseg 1.",
        "Yes: axon[2], 30 um each, nseg 1, with the two sampled diameters.",
    ),
    (
        "Biological assumptions",
        "The axon is a uniform 1 um cylinder, electrically independent of the "
        "reconstruction. This inflates the axonal membrane area roughly "
        "fourfold relative to the reconstructed diameter and moves the "
        "attachment from the soma end to the soma midpoint.",
        "A 6.1 mm axonal arbour is represented by 60 um of uniform cylinder "
        "whose two diameters are sampled from the reconstruction at fixed arc "
        "positions. Proximal and distal diameters differ by the amount the "
        "reconstruction varies over that stretch.",
    ),
    (
        "Reproducibility implications",
        "Fully determined by the source. The same stub results for any SWC "
        "that contains a soma, so the branch is insensitive to which "
        "reconstruction is supplied.",
        "Depends on Import3d's per-section diameter assignment, which is a "
        "NEURON implementation detail not derivable from the SWC. The distal "
        "sample is robust because the axon radius plateaus; the proximal one "
        "is only bounded statically.",
    ),
    (
        "Supported by published descriptor?",
        "No. The descriptor has no axon_type field, no axon_morph section and "
        "no axon diameter.",
        "No. Same three absences. The CLI default being 'truncated' is a "
        "default, not a record of what was fitted.",
    ),
)


def section_axon(report: Report, descriptor: dict) -> dict:
    """Whether the fitted axon configuration can be established at all."""
    report.banner("5. Axon treatment, the primary blocker")

    swc_path = CACHE / EXPECTED["swc"]["rel"]
    rows = read_swc(swc_path) if swc_path.exists() else []
    geometry = axon_branch_geometry(rows) if rows else {"available": False}

    report.check(
        geometry.get("available", False),
        "axon|the substitute SWC carries a soma-attached axon",
        "%s axon points, %s roots" % (
            geometry.get("n_axon_points"), geometry.get("n_roots")),
    )
    if geometry.get("available"):
        report.observe(
            "stub axon",
            "diam %.4f um x 2 x 30 um = %.2f um2, attach soma(0.5)"
            % (geometry["stub_diam_um"], geometry["stub_total_area_um2"]),
        )
        report.observe(
            "truncated axon",
            "diam %.4f-%.4f um then %.4f um = %.2f-%.2f um2, attach soma(1.0)"
            % (
                geometry["truncated_proximal_diam_um_min"],
                geometry["truncated_proximal_diam_um_max"],
                geometry["truncated_distal_diam_um"],
                geometry["truncated_total_area_um2_min"],
                geometry["truncated_total_area_um2_max"],
            ),
        )
        report.check(
            geometry["area_ratio_min"] > 1.5,
            "axon|the two branches differ materially in membrane area",
            "stub/truncated = %.2f-%.2f" % (
                geometry["area_ratio_min"], geometry["area_ratio_max"]),
        )
        report.check(
            geometry["distal_window_all_equal"],
            "axon|the distal sample beyond 60 um is a plateau, not a gradient",
            "so axon_diams[1] is determined to 1e-6",
        )
        report.check(
            geometry["stub_attachment"] != geometry["truncated_attachment"],
            "axon|the branches attach at different points on the soma",
            "%s vs %s" % (
                geometry["stub_attachment"], geometry["truncated_attachment"]),
        )

    # -- what the published artefacts do and do not record ---------------
    report.check(
        "axon_type" not in (CACHE / EXPECTED["descriptor"]["rel"])
        .read_text(encoding="utf-8", errors="replace"),
        "axon|the fit descriptor does not record the branch",
        "verified in section 2",
    )

    if MODEL_RECORD.exists():
        record = load_json(MODEL_RECORD)
        # The cached file is the RMA response envelope, not the row itself.
        if isinstance(record.get("msg"), list) and record["msg"]:
            record = record["msg"][0]
        report.check(
            not any("axon" in str(key).lower() for key in record),
            "axon|the public neuronal model record has no axon field",
            "keys: " + ", ".join(sorted(record)),
        )
        report.check(
            record.get("neuron_reconstruction_id") == FITTING_RECONSTRUCTION_ID,
            "axon|the record points at the unavailable fitted reconstruction",
            str(record.get("neuron_reconstruction_id")),
        )
    else:
        report.skip("axon|model record absent", str(MODEL_RECORD))

    for label, path in (("all-active", FIXTURE_ALL_ACTIVE),
                        ("perisomatic", FIXTURE_PERISOMATIC)):
        if not path.exists():
            report.skip("axon|%s fixture manifest absent" % label, str(path))
            continue
        biophys = load_json(path).get("biophys", [])
        report.check(
            len(biophys) == 1,
            "axon|the %s fixture manifest has one biophys entry" % label,
            ", ".join(sorted(biophys[0])) if biophys else "empty",
        )

    report.note(
        "create_utils indexes biophys[1], which only runner.load_description\n"
        "creates. A manifest with one biophys entry therefore cannot reach\n"
        "create_utils on its own: the branch is supplied at run time, from the\n"
        "command line, and nowhere else."
    )

    report.note(
        "Allen's own all-active fixture test constructs AllActiveUtils with one\n"
        "argument, which the v2.16.2 constructor does not accept. The fixture\n"
        "test is stale, so it is not evidence for either branch."
    )

    resolved = False
    report.check(
        resolved is False,
        "axon|neither branch can be established as the fitted configuration",
        "no published artefact records the choice",
    )

    FINDINGS["axon_type_resolved"] = resolved
    return {
        "resolved": resolved,
        "comparison": AXON_COMPARISON,
        "geometry": geometry,
        "runnable_branches": ["stub", "truncated"],
    }


# ---------------------------------------------------------------------------
# Section 6: morphology compatibility
# ---------------------------------------------------------------------------


def section_morphology(report: Report, descriptor: dict) -> dict:
    """Whether the substitute morphology can carry all 42 genome entries."""
    report.banner("6. Morphology compatibility")

    swc_path = CACHE / EXPECTED["swc"]["rel"]
    if not swc_path.exists():
        report.check(False, "morphology|substitute SWC present", str(swc_path))
        FINDINGS["morphology_mappable"] = False
        return {}

    rows = read_swc(swc_path)
    census = collections.Counter(SWC_CLASSES.get(row["type"], "other")
                                 for row in rows)
    report.check(len(rows) > 0, "morphology|the SWC parses", "%d points" % len(rows))
    report.observe(
        "SWC census",
        ", ".join("%s=%d" % (name, census[name])
                  for name in MORPHOLOGY_CLASS_ARRAYS + ("other",)),
    )

    missing = [name for name in MORPHOLOGY_CLASS_ARRAYS if not census[name]]
    report.check(
        not missing,
        "morphology|the SWC supplies all four section classes",
        "none missing" if not missing else ", ".join(missing),
    )
    report.check(
        census["soma"] == 1,
        "morphology|the SWC has a single soma point",
        str(census["soma"]),
    )

    roots = [row for row in rows
             if row["type"] == 2
             and any(other["type"] == 1 and other["id"] == row["parent"]
                     for other in rows)]
    report.check(
        len(roots) == 1,
        "morphology|exactly one axon root attaches to the soma",
        "%d roots" % len(roots),
    )

    # The 42 entries are addressable only if every class survives into NEURON.
    # NEURON names imported sections after the SWC type, which is why Allen can
    # test a name prefix instead of tracking sections explicitly.
    by_section = descriptor.get("names_by_section", {})
    addressable = sum(len(by_section.get(name, []))
                      for name in MORPHOLOGY_CLASS_ARRAYS)
    report.check(
        addressable == EXPECTED_GENOME_ENTRIES,
        "morphology|all 42 genome entries land on a class present in the SWC",
        "%d of %d" % (addressable, EXPECTED_GENOME_ENTRIES),
    )

    # Only axon sections are deleted, so the mapping of the other 28 entries is
    # branch-independent. Three occurrences is the evidence: one delete loop in
    # the perisomatic builder, one scan and one delete loop in the truncated
    # branch, and no test on any other section prefix anywhere.
    report.check(
        _occurrences(SOURCE_UTILS, 'sec.name()[:4] == "axon"') == 3,
        "morphology|only axon sections are deleted by either branch",
        "one delete loop each, plus the 60 um scan",
    )
    branch_dependent = set(by_section.get("axon", []))
    branch_independent = sorted(
        name for section in ("soma", "apic", "dend")
        for name in by_section.get(section, []))
    report.observe(
        "entries touched by the axon decision",
        "%d of 42 (the axon); %d are branch-independent"
        % (len(branch_dependent), len(branch_independent)),
    )

    # The fitted reconstruction is the one artefact that would settle the
    # question, so confirm it is genuinely absent rather than merely unused.
    strays = sorted(CACHE.rglob("*491771090*"))
    morphology_strays = [path.name for path in strays
                         if path.suffix.lower() in (".swc", ".asc", ".nwb")]
    probes = [path for path in strays if path.suffix.lower() == ".json"]
    empty_probes = []
    for path in probes:
        payload = load_json(path)
        if isinstance(payload, dict) and payload.get("num_rows", 0) == 0:
            empty_probes.append(path.name)
    report.check(
        not morphology_strays,
        "morphology|no morphology asset exists for the fitted reconstruction",
        "none found" if not morphology_strays
        else ", ".join(morphology_strays),
    )
    report.check(
        bool(probes) and len(empty_probes) == len(probes),
        "morphology|every API probe for 491771090 returned zero rows",
        "%d probe(s), all num_rows=0" % len(probes),
    )
    report.note(
        "Absence is the reason the substitute is used. It also means the\n"
        "section-by-section difference between the fitted and substitute\n"
        "reconstructions cannot be measured here, only acknowledged."
    )

    FINDINGS["morphology_mappable"] = not missing
    return {
        "census": dict(census),
        "roots": len(roots),
        "addressable": addressable,
        "branch_independent_entries": len(branch_independent),
        "fitted_reconstruction_present": bool(morphology_strays),
        "probes_returning_zero_rows": len(empty_probes),
    }


# ---------------------------------------------------------------------------
# Section 7: manifest completeness
# ---------------------------------------------------------------------------


def section_manifest(report: Report) -> dict:
    """Which manifest fields are grounded, and which one cannot be."""
    report.banner("7. Manifest requirements")

    if not DRAFT_MANIFEST.exists():
        report.check(False, "manifest|draft present", str(DRAFT_MANIFEST))
        return {}

    manifest = load_json(DRAFT_MANIFEST)
    raw = DRAFT_MANIFEST.read_text(encoding="utf-8", errors="replace")

    report.check(
        sorted(manifest) == ["biophys", "manifest", "neuron", "runs"],
        "manifest|top-level sections match the shipped fixture manifests",
        ", ".join(sorted(manifest)),
    )

    biophys = manifest["biophys"]
    report.check(len(biophys) == 1,
                 "manifest|biophys has one entry, as the fixtures do",
                 ", ".join(sorted(biophys[0])) if biophys else "empty")
    report.check(
        sorted(biophys[0]) == ["model_file", "model_type"],
        "manifest|biophys[0] carries model_file and model_type only",
        ", ".join(sorted(biophys[0])),
    )
    report.check(
        biophys[0]["model_type"] == ALL_ACTIVE_TYPE,
        "manifest|model_type selects the all-active factory branch",
        biophys[0]["model_type"],
    )
    report.check(
        biophys[0]["model_file"] == ["manifest.json", "497233292_fit.json"],
        "manifest|model_file names the manifest and the fit descriptor",
        ", ".join(biophys[0]["model_file"]),
    )
    report.check(
        "axon_type" not in raw,
        "manifest|the draft does not smuggle in an axon_type",
        "the loader appends it at run time",
    )

    hoc = manifest["neuron"][0]["hoc"]
    report.check(
        hoc == ["stdgui.hoc", "import3d.hoc"],
        "manifest|neuron[0].hoc lists the two NEURON-shipped files",
        ", ".join(hoc),
    )
    report.check(
        "cell.hoc" not in hoc,
        "manifest|cell.hoc is not requested, so it is never loaded",
        "update_default_cell_hoc falls through on ValueError",
    )

    keys = {entry["key"]: entry for entry in manifest["manifest"]}
    expected_keys = {"BASEDIR", "WORKDIR", "MORPHOLOGY", "MARKER",
                     "MODFILE_DIR", "stimulus_path", "output_path"}
    report.check(
        set(keys) == expected_keys,
        "manifest|every manifest path key is present",
        ", ".join(sorted(keys)),
    )
    report.check(
        keys["MORPHOLOGY"]["spec"] ==
        pathlib.PurePosixPath(EXPECTED["swc"]["rel"]).name,
        "manifest|MORPHOLOGY names the cached SWC",
        keys["MORPHOLOGY"]["spec"],
    )
    report.check(
        keys["MARKER"]["spec"] ==
        pathlib.PurePosixPath(EXPECTED["marker"]["rel"]).name,
        "manifest|MARKER names the cached marker",
        keys["MARKER"]["spec"],
    )
    report.check(
        keys["MODFILE_DIR"]["spec"] == "modfiles",
        "manifest|MODFILE_DIR points at the draft mechanism directory",
        keys["MODFILE_DIR"]["spec"],
    )
    report.check(
        keys["stimulus_path"]["spec"] == keys["output_path"]["spec"],
        "manifest|stimulus and output share the specimen NWB basename",
        keys["stimulus_path"]["spec"],
    )
    report.check(
        "MARKER" not in SOURCE_RUNNER.read_text(encoding="utf-8",
                                                errors="replace"),
        "manifest|the runner never reads the MARKER path",
        "so the marker cannot affect a simulation",
    )

    runs = manifest["runs"][0]
    report.check(
        runs["sweeps"] == list(COARSE_SWEEPS),
        "manifest|runs[0].sweeps is the COARSE block only",
        "%d sweeps, %d-%d" % (len(runs["sweeps"]), runs["sweeps"][0],
                              runs["sweeps"][-1]),
    )
    report.check(
        "sweeps_by_type" in runs,
        "manifest|runs[0].sweeps_by_type is present",
        "run_sync reads it unconditionally",
    )
    square = set(runs.get("sweeps_by_type", {}).get("Long Square", []))
    report.check(
        set(runs["sweeps"]) <= square,
        "manifest|every requested sweep is typed Long Square",
        "%d of %d" % (len(set(runs["sweeps"]) & square), len(runs["sweeps"])),
    )
    test = set(runs.get("sweeps_by_type", {}).get("Test", []))
    report.check(
        not (set(runs["sweeps"]) & test),
        "manifest|no Test sweep is requested",
        "Test sweeps excluded",
    )

    if FIXTURE_ALL_ACTIVE.exists():
        fixture = load_json(FIXTURE_ALL_ACTIVE)
        report.check(
            "sweeps_by_type" not in fixture["runs"][0],
            "manifest|the fixture manifest omits sweeps_by_type",
            "a draft-only addition, documented in provenance.json",
        )

    sidecar = {}
    if DRAFT_PROVENANCE.exists():
        sidecar = {entry["field"]: entry
                   for entry in load_json(DRAFT_PROVENANCE)["field_provenance"]}
        entry = sidecar.get("axon_type", {})
        report.check(
            entry.get("source") == "absent-by-design",
            "manifest|the sidecar records axon_type as absent by design",
            str(entry.get("source")),
        )
    else:
        report.skip("manifest|provenance sidecar absent", str(DRAFT_PROVENANCE))

    grounded = sorted(name for name, entry in sidecar.items()
                      if entry.get("source") != "absent-by-design")
    unresolved = ["biophys[1].axon_type"]
    report.observe("manifest fields grounded", "%d of %d recorded"
                   % (len(grounded), len(sidecar)))
    report.observe("unresolved manifest field", ", ".join(unresolved))
    report.note(
        "The draft is deliberately incomplete: without biophys[1], create_utils\n"
        "raises IndexError on this manifest alone. That is the intended\n"
        "behaviour, because the missing entry is the undocumented decision the\n"
        "report refuses to make."
    )
    return {"grounded": grounded, "unresolved": unresolved}


# ---------------------------------------------------------------------------
# Section 8: fitting provenance
# ---------------------------------------------------------------------------


def section_fitting(report: Report, observed: dict) -> dict:
    """Which sweeps are in-sample, which are not, and for which model."""
    report.banner("8. Fitting provenance and held-out eligibility")

    descriptor = load_json(CACHE / EXPECTED["descriptor"]["rel"])
    fitting = descriptor["fitting"][0]["sweeps"]
    report.check(fitting == [FITTING_SWEEP],
                 "fitting|the all-active fit used sweep 41 alone", str(fitting))
    report.check(FITTING_SWEEP in COARSE_SWEEPS,
                 "fitting|sweep 41 belongs to the COARSE block", COARSE_BLOCK)
    report.check(FITTING_SWEEP not in HELD_OUT_SWEEPS,
                 "fitting|sweep 41 is not one of the held-out sweeps",
                 str(list(HELD_OUT_SWEEPS)))
    report.check(not (set(HELD_OUT_SWEEPS) & set(COARSE_SWEEPS)),
                 "fitting|the held-out sweeps are outside the COARSE block",
                 FINEST_BLOCK)

    perisomatic = load_json(CACHE / EXPECTED["descriptor_perisomatic"]["rel"])
    peri_fitting = perisomatic["fitting"][0]["sweeps"]
    report.check(peri_fitting == [PERISOMATIC_FITTING_SWEEP],
                 "fitting|the perisomatic fit used a different sweep",
                 str(peri_fitting))
    report.check(PERISOMATIC_FITTING_SWEEP != FITTING_SWEEP,
                 "fitting|sweep 38 is not the all-active fitting sweep",
                 "the two models were fitted on different sweeps")
    report.check(PERISOMATIC_FITTING_SWEEP in COARSE_SWEEPS,
                 "fitting|sweep 38 is also in the COARSE block", COARSE_BLOCK)

    report.check(
        observed.get("descriptor", {}).get("sha256")
        == EXPECTED["descriptor"]["sha256"],
        "fitting|no later phase altered the descriptor",
        "digest unchanged, so provenance cannot have moved",
    )

    candidates = {
        "sweep_38": "in-sample for the perisomatic model, out-of-sample here",
        "held_out_49_52": "held out from both models, evaluated in Phase 2E",
        "coarse_24_43_minus_41": "in-sample here, so not evidence of fit",
    }
    report.observe(
        "sweep 38",
        "validated in Phase 2C for the perisomatic model, "
        "never used to fit the all-active model",
    )
    report.observe(
        "sweeps 49-52",
        "held out from both fits and already validated in Phase 2E",
    )
    report.note(
        "The all-active model has exactly one fitting sweep, so every other\n"
        "COARSE sweep is also out-of-sample for it. Only 38 and 49-52 carry an\n"
        "independent prior validation, and that validation was of a different\n"
        "model class, so neither is evidence about all-active accuracy."
    )
    return {"fitting_sweeps": fitting, "candidates": candidates,
            "perisomatic_fitting_sweeps": peri_fitting}


# ---------------------------------------------------------------------------
# Section 9: environment
# ---------------------------------------------------------------------------

PHASE2C_REPORT = (
    PROJECT_ROOT / "results" / "phase2" / "PHASE2C_PERISOMATIC_EXECUTION_VALIDATION.md"
)
PHASE2E_REPORT = (
    PROJECT_ROOT / "results" / "phase2" / "PHASE2E_FINEST_HELD_OUT_EVALUATION.md"
)


def section_environment(report: Report) -> dict:
    """Whether the loader could be imported without executing a simulation."""
    report.banner("9. Environment readiness")

    package = CACHE / "2b/src/AllenSDK-2.16.2/allensdk"
    required = [
        package / "__init__.py",
        package / "model/biophysical/utils.py",
        package / "model/biophysical/runner.py",
        package / "model/biophys_sim/config.py",
        package / "model/biophys_sim/neuron/hoc_utils.py",
        package / "config/model/description.py",
    ]
    absent = [str(path.relative_to(CACHE)) for path in required
              if not path.exists()]
    report.check(not absent,
                 "environment|the v2.16.2 source tree is complete",
                 "none missing" if not absent else ", ".join(absent))

    # Importing the loader is only safe if NEURON is imported lazily. That is a
    # property of the source, not of this interpreter, so it is read, not run.
    report.check(
        _occurrences(SOURCE_HOC_UTILS, "\nimport neuron\n") == 0,
        "environment|NEURON is imported lazily, inside HocUtils.__init__",
        "module import cannot start NEURON",
    )
    report.check(
        _occurrences(SOURCE_UTILS, "\nimport neuron\n") == 0,
        "environment|the utils module never imports NEURON at module scope",
        "so importing utils is inert",
    )

    for label, path in (("Phase 2C", PHASE2C_REPORT), ("Phase 2E", PHASE2E_REPORT)):
        if not path.exists():
            report.skip("environment|%s report absent" % label, path.name)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        report.check(
            "--allensdk-src" in text,
            "environment|%s ran AllenSDK from the cached source tree" % label,
            "no installed distribution required",
        )

    report.note(
        "The execution environment is the Phase 2C WSL2 venv, which this audit\n"
        "does not touch: no package was installed, no mechanism compiled and no\n"
        "simulation started. The import-safety question is answered from the\n"
        "source above and was confirmed once by hand; see the report."
    )
    return {"source_tree": str(package.parent), "required": len(required)}


# ---------------------------------------------------------------------------
# Section 10: self-guard
# ---------------------------------------------------------------------------


def section_guard(report: Report) -> dict:
    """Evidence that the constraints were honoured, not merely intended."""
    report.banner("10. Self-guard")

    leaked = [name for name in ("neuron", "nrn", "allensdk")
              if name in sys.modules]
    report.check(
        not leaked,
        "guard|no simulation package was imported by this audit",
        "none" if not leaked else ", ".join(leaked),
    )

    artefacts = []
    for directory in (MODFILE_REFERENCE_DIR, DRAFT_MODFILE_DIR):
        if directory.exists():
            artefacts += [path.name for path in directory.iterdir()
                          if path.suffix in (".o", ".dll", ".so", ".pyd", ".c")]
    report.observe(
        "compiled mechanism artefacts in the cache",
        "none" if not artefacts else "%d: %s" % (len(artefacts),
                                                 ", ".join(sorted(artefacts)[:5])),
    )
    report.observe(
        "modules imported by this audit",
        "%d, all standard library" % len(sys.modules),
    )
    return {"leaked": leaked, "artefacts": len(artefacts)}


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

READY = "READY FOR ISOLATED EXECUTION VALIDATION"
CONDITIONAL = "CONDITIONALLY READY"
BLOCKED = "BLOCKED"


def decide(report: Report) -> tuple[str, str]:
    """One verdict, derived from the findings rather than written by hand."""
    failing = [label for label, ok, _ in report.checks if not ok]
    if failing:
        return BLOCKED, (
            "%d check(s) failed, so an essential dependency or specification "
            "is unresolved" % len(failing)
        )

    blocking = [name for name in
                ("descriptor_compatible", "mechanisms_complete",
                 "morphology_mappable")
                if FINDINGS.get(name) is not True]
    if blocking:
        return BLOCKED, "unresolved: " + ", ".join(blocking)

    if FINDINGS.get("axon_type_resolved") is not True:
        return CONDITIONAL, (
            "the model is technically executable and every parameter is "
            "specified, but the axon branch the published parameters were "
            "fitted under is not recorded anywhere"
        )

    return READY, "every dependency and every assumption is specified"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Static execution-readiness audit of the all-active "
                    "model 497233292.")
    parser.add_argument(
        "--json", default=str(DEFAULT_JSON),
        help="where to write the machine-readable summary",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    report = Report()

    observed = section_provenance(report)
    descriptor = section_descriptor(report)
    mechanisms = section_mechanisms(report, descriptor)
    loader = section_loader_contract(report, descriptor)
    axon = section_axon(report, descriptor)
    morphology = section_morphology(report, descriptor)
    manifest = section_manifest(report)
    fitting = section_fitting(report, observed)
    environment = section_environment(report)
    guard = section_guard(report)

    verdict, rationale = decide(report)

    print()
    print("=" * 78)
    print("VERDICT: " + verdict)
    print("=" * 78)
    report.note(rationale)
    report.note(
        "Technically executable: %s. Reproducible as fitted: %s."
        % ("yes, both branches run",
           "no, the branch is unrecorded")
    )

    summary = report.summary()
    summary.update({
        "phase": "2G-A",
        "specimen_id": SPECIMEN_ID,
        "model_id": MODEL_ID,
        "template_id": TEMPLATE_ID,
        "template_type": ALL_ACTIVE_TYPE,
        "descriptor_sha256": observed.get("descriptor", {}).get("sha256"),
        "descriptor_matches_expected":
            observed.get("descriptor", {}).get("sha256")
            == EXPECTED["descriptor"]["sha256"],
        "verdict": verdict,
        "rationale": rationale,
        "findings": FINDINGS,
        "axon_type_resolved": axon.get("resolved"),
        "axon_comparison": [list(row) for row in AXON_COMPARISON],
        "axon_geometry": axon.get("geometry"),
        "genome": {
            "entries": descriptor.get("genome_entries"),
            "by_section": descriptor.get("genome_by_section"),
            "axon_mechanisms": descriptor.get("axon_mechanisms"),
        },
        "mechanisms": mechanisms,
        "loader_claims": loader.get("claims"),
        "morphology": morphology,
        "manifest": manifest,
        "fitting": fitting,
        "environment": environment,
        "guard": guard,
    })

    destination = pathlib.Path(args.json)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=False),
                           encoding="utf-8")

    print()
    print("checks: %d passed, %d failed, %d observations"
          % (summary["passed"], summary["failed"], summary["observations"]))
    print("summary written to %s" % destination)
    print()

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

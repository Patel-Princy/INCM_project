#!/usr/bin/env python
"""Phase 0B -- four V1 neuronal population feasibility audit.

The supervisor asked whether four biologically distinct V1 populations can be
studied with the Allen Cell Types Database.  This script answers that question
from the metadata that Phase 0 already downloaded and committed.  It does not
call the Allen API, download an NWB file, download a model archive, or execute a
model.  The only network evidence it carries is the small identity-schema probe
recorded in ``IDENTITY_SCHEMA_PROBE`` (run once on 2026-11-07); the probe's job is
to show that the fields the audit *needs* for projection identity do not exist.

The audit deliberately separates four kinds of statement:

  OBSERVED  a value read from the committed inventory;
  DERIVED   a count computed from those values by a named rule;
  ASSUMED   a convention that the inventory cannot prove (e.g. that a Cre line
            is an indirect marker of a projection class);
  UNAVAILABLE  something the database does not carry at all.

The four candidate populations are biological hypotheses, not labels to assign:

  A  VISp layer 4   excitatory spiny stellate / IT-like
  B  VISp layer 2/3 IT pyramidal
  C  VISp layer 5   ET/PT pyramidal
  D  VISp layer 6   corticothalamic

No specimen is ever marked CONFIRMED.  The database has no projection field, so
the strongest honest label is PROBABLE (converging indirect metadata) and the
population-level recommendation is layer-defined rather than projection-defined.

Outputs (all under ``results/dataset_inventory/`` unless overridden):

  four_population_counts.csv
  four_population_candidates.csv
  four_population_exclusions.csv
  four_population_model_availability.csv
  four_population_audit_summary.json

Usage:
    python src/data_audit/four_population_audit.py
    python src/data_audit/four_population_audit.py --print-tables
    python src/data_audit/four_population_audit.py --out-dir tmp/audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

# ---------------------------------------------------------------------------
# Paths and frozen configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
RESULTS_DIR = PROJECT_ROOT / "results" / "dataset_inventory"

CELL_CSV = METADATA_DIR / "cell_inventory.csv"
SWEEP_CSV = METADATA_DIR / "sweep_inventory.csv"
MODEL_CSV = METADATA_DIR / "model_inventory.csv"
MANIFEST_JSON = METADATA_DIR / ".generated_manifest.json"

DEFAULT_OUT_DIR = RESULTS_DIR
DEFAULT_SUMMARY = RESULTS_DIR / "four_population_audit_summary.json"

PHASE = "0B"
REGION = "VISp"
SPECIES = "Mus musculus"

#: Phase 0's audit threshold, retained unchanged.  The extra requirement that the
#: cell have >= 2 distinct depolarising amplitudes is what makes a calibration /
#: held-out amplitude split possible.
MIN_LONG_SQUARE = 6
MIN_DEPOLARIZING = 3
MIN_DISTINCT_AMPLITUDES = 2

#: Amplitude values are float32 DAC read-backs (e.g. 170.000000188).  Rounding
#: to 1e-3 pA collapses numerical noise without merging real 20 pA steps.
AMPLITUDE_DECIMALS = 3

#: Model classes are identified by template id, never by well_known_file_type_id:
#: the biophysical fit JSON and the GLIF neuron_config JSON share a file type.
PERISOMATIC_TEMPLATE_ID = 329230710
ALL_ACTIVE_TEMPLATE_ID = 491455321
BIOPHYSICAL_CLASSES = ("biophysical_perisomatic", "biophysical_all_active")

#: The one specimen whose models have actually been executed in this repository.
#: This is evidence of *execution*, not of scientific reproduction.
EXECUTED_SPECIMENS = {
    382982932: {
        "perisomatic": "Phase 2C execution validation",
        "all_active": "Phase 2G-B / 2G-C execution and measurement",
        "executed": True,
        "validated_against_recording": False,
    }
}

#: Four candidate populations.  Layer membership is the only hard grouping
#: variable; projection identity is assessed separately and never assumed.
POPULATIONS: tuple[dict[str, Any], ...] = (
    {
        "key": "A",
        "label": "VISp L4 excitatory (spiny stellate / IT-like)",
        "short": "L4 excitatory",
        "layers": ("4",),
        "proposed": "excitatory spiny stellate / IT-like",
    },
    {
        "key": "B",
        "label": "VISp L2/3 IT pyramidal",
        "short": "L2/3 IT",
        "layers": ("2/3",),
        "proposed": "IT pyramidal",
    },
    {
        "key": "C",
        "label": "VISp L5 ET/PT pyramidal",
        "short": "L5 ET/PT",
        "layers": ("5",),
        "proposed": "ET/PT pyramidal",
    },
    {
        "key": "D",
        "label": "VISp L6 corticothalamic",
        "short": "L6 CT",
        "layers": ("6a", "6b"),
        "proposed": "corticothalamic",
    },
)
POP_BY_LAYER = {layer: pop for pop in POPULATIONS for layer in pop["layers"]}

#: Identity evidence is *indirect*.  A line is listed only where its Allen use is
#: a well-established layer/class targeting tool, and even then it is PROBABLE at
#: best.  Lines not listed here do not establish a projection class.
CLASS_LINE_SUPPORT: dict[str, set[str]] = {
    "A": {"Scnn1a-Tg3-Cre", "Scnn1a-Tg2-Cre", "Nr5a1-Cre",
          "Rorb-IRES2-Cre", "Cux2-CreERT2"},
    "B": {"Cux2-CreERT2"},
    "C": {"Rbp4-Cre_KL100"},
    "D": {"Ntsr1-Cre_GN220"},
}
CLASS_LAYERS: dict[str, set[str]] = {
    "A": {"4"},
    "B": {"2/3"},
    "C": {"5"},
    "D": {"6a", "6b"},
}
CLASS_NAMES = {
    "A": "L4 excitatory (stellate vs star pyramidal unresolved)",
    "B": "L2/3 IT-compatible",
    "C": "L5 ET/PT-compatible (ET vs PT unresolved)",
    "D": "L6 CT-compatible",
}
#: GABAergic markers.  Used only to flag a line/morphology conflict; it is never
#: used to exclude a specimen from the layer-level count.
GABAERGIC_MARKERS = (
    "Pvalb", "Sst", "Vip", "Htr3a", "Gad2", "Chat", "Ndnf", "Nos1",
    "Nkx2-1", "Vipr2", "Slc32a1",
)

#: The identity-schema probe.  These are literal API observations, not derived
#: values.  The negative results are the evidence that no projection field exists.
IDENTITY_SCHEMA_PROBE = {
    "endpoint": "http://api.brain-map.org/api/v2/data/query.json",
    "observed_on": "2026-11-07",
    "specimen_payload_fields": [
        "cell_prep_sample_id", "cell_reporter_id", "cortex_layer_id", "data",
        "donor", "donor_id", "ephys_result_id", "external_specimen_name",
        "failed_facet", "hemisphere", "id", "is_cell_specimen", "is_ish", "name",
        "parent_id", "parent_x_coord", "parent_y_coord", "parent_z_coord",
        "pinned_radius", "rna_integrity_number", "specimen_id_path", "sphinx_id",
        "structure", "structure_id", "tissue_ph", "treatment_id", "weight",
    ],
    "column_probes": {
        field: {
            "query": "model::Specimen,rma::criteria,[%s$eq'CT']" % field,
            "http": 200,
            "success": False,
            "error": "Data Access error (column does not exist)",
        }
        for field in (
            "projection", "projection_class", "cell_type", "cell_class",
            "projection_target", "target_structure_id", "cre_line", "line_name",
        )
    },
    "model_probes": {
        model: {
            "query": model,
            "http": 200,
            "success": False,
            "error": "uninitialized constant",
        }
        for model in (
            "model::Projection", "model::ProjectionTarget",
            "model::CellType", "model::TranscriptomicType",
        )
    },
    "baseline_control": {
        "query": "model::Specimen,rma::criteria,[structure_id$eq721]",
        "http": 200,
        "success": True,
        "total_rows": 458,
        "note": "VISp layer 4; proves the query pattern works when the column exists",
    },
}

#: The 12 required stages.  ``base`` names the stage a facet is computed over;
#: sequential stages are cumulative by construction.
STAGES: tuple[dict[str, Any], ...] = (
    {"number": 1, "key": "stage_01", "name": "Total mouse V1 specimens",
     "definition": "Mus musculus specimens in the population's VISp layer(s)",
     "kind": "sequential", "base": None},
    {"number": 2, "key": "stage_02", "name": "Long-square current clamp",
     "definition": "non-failed EphysResult with >= 1 long-square sweep under "
                   "the units-aware current-clamp rule",
     "kind": "sequential", "base": "stage_01"},
    {"number": 3, "key": "stage_03", "name": "Depolarising long square",
     "definition": ">= 1 depolarising long-square current-clamp sweep "
                   "(stimulus amplitude > 0 pA)",
     "kind": "sequential", "base": "stage_02"},
    {"number": 4, "key": "stage_04", "name": "Two distinct amplitudes",
     "definition": ">= 2 distinct depolarising amplitudes (1e-3 pA rounding)",
     "kind": "sequential", "base": "stage_03"},
    {"number": 5, "key": "stage_05", "name": "Sufficient conditions",
     "definition": ">= 6 long-square CC sweeps AND >= 3 depolarising AND "
                   ">= 2 distinct depolarising amplitudes",
     "kind": "sequential", "base": "stage_04"},
    {"number": 6, "key": "stage_06", "name": "Downloadable NWB",
     "definition": "NWB download reference resolved in the inventory",
     "kind": "sequential", "base": "stage_05"},
    {"number": 7, "key": "stage_07", "name": "Perisomatic model",
     "definition": ">= 1 Biophysical - perisomatic model",
     "kind": "facet", "base": "stage_06"},
    {"number": 8, "key": "stage_08", "name": "All-active model",
     "definition": ">= 1 Biophysical - all active model",
     "kind": "facet", "base": "stage_06"},
    {"number": 9, "key": "stage_09", "name": "Both model classes",
     "definition": ">= 1 perisomatic AND >= 1 all-active model",
     "kind": "facet", "base": "stage_06"},
    {"number": 10, "key": "stage_10", "name": "Morphology asset",
     "definition": "has_morphology AND reconstruction id AND download URL AND "
                   "not superseded",
     "kind": "facet", "base": "stage_06"},
    {"number": 11, "key": "stage_11", "name": "Fit descriptor",
     "definition": ">= 1 biophysical model with a resolved fit-descriptor "
                   "reference (metadata level; JSON not opened)",
     "kind": "facet", "base": "stage_06"},
    {"number": 12, "key": "stage_12", "name": "Final eligible",
     "definition": "stages 1-6 plus >= 1 biophysical model with a resolved "
                   "fit descriptor plus a usable morphology asset",
     "kind": "final", "base": "stage_06"},
)

COUNT_COLUMNS = [
    "population", "population_label", "population_total", "stage",
    "stage_name", "stage_definition", "stage_kind", "base_stage", "base_n",
    "n", "pct_of_population", "pct_of_base", "phase0_pass",
]

CANDIDATE_COLUMNS = [
    "population", "population_label", "rank_within_population", "specimen_id",
    "layer", "structure_acronym", "driver_line", "reporter_line", "genotype",
    "dendrite_type", "apical_dendrite_status", "ephys_result_id",
    "sampling_rate_hz", "n_long_square_cc", "n_depolarizing_sweeps",
    "n_distinct_depolarizing_amplitudes", "n_repeated_depolarizing_amplitudes",
    "depolarizing_min_pa", "depolarizing_max_pa", "nwb_file_id",
    "nwb_download_url", "perisomatic_model_id", "perisomatic_template_id",
    "perisomatic_fit_file_id", "perisomatic_reconstruction_id",
    "all_active_model_id", "all_active_template_id",
    "all_active_fit_file_id", "all_active_reconstruction_id",
    "model_reconstruction_matches_specimen", "has_morphology",
    "reconstruction_id", "reconstruction_type", "reconstruction_superseded",
    "morphology_download_url", "has_perisomatic", "has_all_active", "has_both",
    "identity_class", "identity_confidence", "identity_evidence",
    "is_spiny_excitatory", "is_identity_compatible", "eligible_any_model",
    "eligible_both_models", "phase0_eligibility",
]

EXCLUSION_COLUMNS = [
    "population", "population_label", "specimen_id", "layer", "driver_line",
    "dendrite_type", "ephys_failed", "n_long_square_cc",
    "n_depolarizing_sweeps", "n_distinct_depolarizing_amplitudes",
    "has_perisomatic", "has_all_active", "has_morphology",
    "has_fit_descriptor", "first_failing_requirement", "failed_requirements",
    "identity_confidence",
]

MODEL_COLUMNS = [
    "population", "population_label", "population_total",
    "n_any_biophysical", "n_perisomatic", "n_all_active", "n_both", "n_glif_only",
    "n_fit_descriptor_resolved", "n_morphology_usable", "n_final_any_model",
    "n_final_perisomatic", "n_final_all_active", "n_final_both_models",
    "n_final_spiny", "n_final_identity_compatible",
    "n_final_identity_perisomatic", "n_final_identity_all_active",
    "n_final_identity_both", "n_model_reconstruction_matches",
    "n_model_reconstruction_differs", "perisomatic_template_id",
    "all_active_template_id", "n_listed_any", "n_descriptor_resolved",
    "n_assets_in_repo", "n_executable_in_repo", "n_validated_against_recording",
]


# ---------------------------------------------------------------------------
# Small parsing helpers
# ---------------------------------------------------------------------------
def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _float(value: Any) -> float | None:
    text = _text(value)
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return None if number != number else number  # NaN


def _int(value: Any) -> int | None:
    number = _float(value)
    return None if number is None else int(number)


def _bool(value: Any) -> bool:
    return _text(value).lower() in {"true", "1", "yes"}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, columns: Sequence[str], rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n",
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in columns})
            count += 1
    return count


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6g}"
    return value


# ---------------------------------------------------------------------------
# Source verification
# ---------------------------------------------------------------------------
def verify_sources(paths: Sequence[Path], manifest_path: Path = MANIFEST_JSON) -> list[dict[str, Any]]:
    """Compare the three inventory CSVs with the Phase 0 SHA-256 manifest."""
    if not manifest_path.exists():
        raise RuntimeError(f"missing Phase 0 manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("files", {})
    report: list[dict[str, Any]] = []
    for path in paths:
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        actual = sha256_of(path)
        want = expected.get(rel)
        report.append({
            "path": rel,
            "expected_sha256": want,
            "actual_sha256": actual,
            "ok": bool(want) and actual == want,
            "bytes": path.stat().st_size,
        })
    bad = [item for item in report if not item["ok"]]
    if bad:
        lines = "\n".join(
            f"  {item['path']}: expected {item['expected_sha256']}, got {item['actual_sha256']}"
            for item in bad
        )
        raise RuntimeError(
            "source inventory differs from the Phase 0 manifest; the audit will not "
            "run on changed inputs:\n" + lines
        )
    return report


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_cells(path: Path = CELL_CSV) -> list[dict[str, Any]]:
    """Load and parse VISp mouse specimens.  One row per specimen; no pooling."""
    cells: list[dict[str, Any]] = []
    for raw in read_rows(path):
        if _text(raw.get("region_acronym")) != REGION:
            continue
        if _text(raw.get("species")) != SPECIES:
            continue
        cells.append({
            "specimen_id": _int(raw.get("specimen_id")),
            "region_acronym": _text(raw.get("region_acronym")),
            "layer": _text(raw.get("cortical_layer")),
            "structure_id": _int(raw.get("structure_id")),
            "structure_acronym": _text(raw.get("structure_acronym")),
            "species": _text(raw.get("species")),
            "driver_line": _text(raw.get("transgenic_driver_line")),
            "reporter_line": _text(raw.get("transgenic_reporter_line")),
            "genotype": _text(raw.get("donor_full_genotype")),
            "dendrite_type": _text(raw.get("dendrite_type")),
            "apical_status": _text(raw.get("apical_dendrite_status")),
            "ephys_result_id": _int(raw.get("ephys_result_id")),
            "ephys_available": _bool(raw.get("ephys_available")),
            "ephys_failed": _bool(raw.get("ephys_failed")),
            "sampling_rate_hz": _int(raw.get("ephys_sampling_rate")),
            "nwb_file_id": _int(raw.get("nwb_file_id")),
            "nwb_download_url": _text(raw.get("nwb_download_url")),
            "has_morphology": _bool(raw.get("has_morphology")),
            "reconstruction_id": _int(raw.get("reconstruction_id")),
            "reconstruction_type": _text(raw.get("reconstruction_type")),
            "reconstruction_superseded": _bool(raw.get("reconstruction_superseded")),
            "morphology_download_url": _text(raw.get("morphology_download_url")),
            "phase0_eligibility": _text(raw.get("eligibility")),
            "phase0_n_long_square_cc": _int(raw.get("n_long_square_cc")),
            "phase0_n_biophysical": _int(raw.get("n_biophysical_models")),
            "phase0_n_perisomatic": _int(raw.get("n_biophysical_perisomatic")),
            "phase0_n_all_active": _int(raw.get("n_biophysical_all_active")),
            "phase0_n_glif": _int(raw.get("n_glif_models")),
        })
    ids = [cell["specimen_id"] for cell in cells]
    if len(ids) != len(set(ids)):
        raise RuntimeError("cell_inventory contains duplicate VISp specimen_id rows")
    return cells


def load_sweeps(path: Path = SWEEP_CSV) -> dict[int, list[dict[str, Any]]]:
    """Long-square sweeps for VISp, grouped by specimen."""
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw in read_rows(path):
        if _text(raw.get("region_acronym")) != REGION:
            continue
        if _text(raw.get("stimulus_category")) != "long_square":
            continue
        specimen_id = _int(raw.get("specimen_id"))
        if specimen_id is None:
            continue
        grouped[specimen_id].append({
            "sweep_id": _int(raw.get("sweep_id")),
            "sweep_number": _int(raw.get("sweep_number")),
            "stimulus_name": _text(raw.get("stimulus_name")),
            "stimulus_description": _text(raw.get("stimulus_description")),
            "stimulus_units": _text(raw.get("stimulus_units")),
            "clamp_mode": _text(raw.get("clamp_mode")),
            "amplitude": _float(raw.get("stimulus_absolute_amplitude")),
            "duration": _float(raw.get("stimulus_duration")),
            "num_spikes": _int(raw.get("num_spikes")),
        })
    return dict(grouped)


def load_models(path: Path = MODEL_CSV) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw in read_rows(path):
        specimen_id = _int(raw.get("specimen_id"))
        if specimen_id is None:
            continue
        grouped[specimen_id].append({
            "model_id": _int(raw.get("model_id")),
            "model_name": _text(raw.get("model_name")),
            "template_id": _int(raw.get("neuronal_model_template_id")),
            "template_name": _text(raw.get("template_name")),
            "model_class": _text(raw.get("model_class")),
            "reconstruction_id": _int(raw.get("neuron_reconstruction_id")),
            "availability_status": _text(raw.get("availability_status")),
            "well_known_file_id": _int(raw.get("well_known_file_id")),
            "file_path": _text(raw.get("file_path")),
            "download_url": _text(raw.get("download_url")),
        })
    return dict(grouped)


# ---------------------------------------------------------------------------
# Sweep and model summaries
# ---------------------------------------------------------------------------
def units_aware_current_clamp(clamp_mode: str, stimulus_units: str) -> bool:
    """Phase 0's units-aware rule, unchanged.

    The ``pA`` label and a null ``clamp_mode`` are perfectly confounded; Phase 1B
    validated 236 sweeps and found the inventory number is in picoamperes.  A
    voltage-clamp row is never current clamp, even if its label is odd.
    """
    mode = _text(clamp_mode).lower()
    return mode == "current_clamp" or (mode == "" and _text(stimulus_units) == "pA")


def summarise_sweeps(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    cc = [row for row in rows
          if units_aware_current_clamp(row.get("clamp_mode", ""),
                                       row.get("stimulus_units", ""))]
    explicit = [row for row in cc if _text(row.get("clamp_mode")).lower() == "current_clamp"]
    implicit = [row for row in cc if not _text(row.get("clamp_mode"))]
    with_amplitude = [row for row in cc if _float(row.get("amplitude")) is not None]
    depolarising = [row for row in with_amplitude if float(row["amplitude"]) > 0]
    hyperpolarising = [row for row in with_amplitude if float(row["amplitude"]) < 0]

    amplitudes = [round(float(row["amplitude"]), AMPLITUDE_DECIMALS)
                  for row in depolarising]
    counts = Counter(amplitudes)
    distinct = sorted(counts)

    return {
        "n_long_square_rows": len(rows),
        "n_long_square_cc": len(cc),
        "n_explicit_cc": len(explicit),
        "n_implicit_cc": len(implicit),
        "n_depolarizing": len(depolarising),
        "n_hyperpolarizing": len(hyperpolarising),
        "n_distinct_depolarizing": len(distinct),
        "n_repeated_depolarizing": sum(1 for count in counts.values() if count >= 2),
        "depolarizing_min_pa": min(amplitudes) if amplitudes else None,
        "depolarizing_max_pa": max(amplitudes) if amplitudes else None,
        "hyperpolarizing_min_pa": min(
            round(float(row["amplitude"]), AMPLITUDE_DECIMALS) for row in hyperpolarising
        ) if hyperpolarising else None,
        "hyperpolarizing_max_pa": max(
            round(float(row["amplitude"]), AMPLITUDE_DECIMALS) for row in hyperpolarising
        ) if hyperpolarising else None,
        "distinct_depolarizing_pa": distinct,
        "units_observed": sorted({_text(row.get("stimulus_units")) for row in rows}),
        "n_missing_amplitude": len(cc) - len(with_amplitude),
        "n_sweeps_with_spikes": sum(
            1 for row in cc if (_int(row.get("num_spikes")) or 0) > 0
        ),
        "has_any_long_square": bool(rows),
    }


def summarise_models(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    def first_of(model_class: str) -> dict[str, Any] | None:
        for row in rows:
            if _text(row.get("model_class")) == model_class:
                return row
        return None

    perisomatic = [row for row in rows
                   if _text(row.get("model_class")) == "biophysical_perisomatic"]
    all_active = [row for row in rows
                  if _text(row.get("model_class")) == "biophysical_all_active"]
    glif = [row for row in rows if _text(row.get("model_class")) == "glif"]
    biophysical = perisomatic + all_active

    def descriptor_ok(row: dict[str, Any]) -> bool:
        return (_text(row.get("availability_status"))
                == "metadata_present_download_reference_resolved"
                and row.get("well_known_file_id") is not None)

    peri = first_of("biophysical_perisomatic")
    allact = first_of("biophysical_all_active")
    return {
        "n_total": len(rows),
        "n_perisomatic": len(perisomatic),
        "n_all_active": len(all_active),
        "n_biophysical": len(biophysical),
        "n_glif": len(glif),
        "n_descriptor_resolved": sum(1 for row in biophysical if descriptor_ok(row)),
        "perisomatic": peri,
        "all_active": allact,
        "model_reconstruction_ids": sorted({
            row["reconstruction_id"] for row in biophysical
            if row.get("reconstruction_id") is not None
        }),
    }


def morphology_usable(cell: dict[str, Any]) -> tuple[bool, str]:
    if not cell.get("has_morphology"):
        return False, "no morphology reconstruction in the inventory"
    if cell.get("reconstruction_id") is None:
        return False, "missing reconstruction id"
    if not _text(cell.get("morphology_download_url")):
        return False, "missing morphology download reference"
    if cell.get("reconstruction_superseded"):
        return False, "reconstruction marked superseded"
    return True, "usable reconstruction reference"


# ---------------------------------------------------------------------------
# Identity evidence
# ---------------------------------------------------------------------------
def base_driver_line(driver: str) -> str:
    parts = [part.strip() for part in _text(driver).split(";")
             if part.strip() and part.strip().lower() != "wt"]
    return parts[0] if parts else ""


def line_is_gabaergic(driver: str) -> bool:
    return any(marker in _text(driver) for marker in GABAERGIC_MARKERS)


def line_is_class_marker(driver: str) -> bool:
    base = base_driver_line(driver)
    return any(base in lines for lines in CLASS_LINE_SUPPORT.values())


def class_for_line_and_layer(driver: str, layer: str) -> str | None:
    base = base_driver_line(driver)
    for class_key, lines in CLASS_LINE_SUPPORT.items():
        if base in lines and layer in CLASS_LAYERS[class_key]:
            return class_key
    return None


def classify_identity(layer: str, driver: str, dendrite: str, apical: str) -> dict[str, Any]:
    """Return a confidence label, candidate class, and an auditable reason.

    CONFIRMED is never returned.  The database has no projection field; the
    strongest permitted label is PROBABLE, and only when layer, dendrite type and
    a class-compatible line converge.
    """
    layer = _text(layer)
    driver_text = _text(driver)
    dendrite = _text(dendrite)
    apical_text = _text(apical)
    base = base_driver_line(driver_text)
    class_key = class_for_line_and_layer(driver_text, layer)

    def evidence(suffix: str) -> str:
        return (
            f"layer {layer}; dendrite {dendrite or 'unknown'}; apical "
            f"{apical_text or 'unknown'}; driver {base or 'none'}; {suffix}. "
            "Indirect metadata only: projection identity is not measured."
        )

    if dendrite in {"aspiny", "sparsely spiny"}:
        if line_is_class_marker(driver_text):
            return {
                "confidence": "UNRESOLVED", "class": None,
                "reason": evidence("excitatory-class line conflicts with non-spiny morphology"),
            }
        if line_is_gabaergic(driver_text):
            return {
                "confidence": "NOT-CANDIDATE", "class": None,
                "reason": evidence("GABAergic line and non-spiny morphology; not one of the four excitatory candidates"),
            }
        return {
            "confidence": "NOT-CANDIDATE", "class": None,
            "reason": evidence("non-spiny morphology; not one of the four excitatory candidates"),
        }

    if dendrite == "spiny":
        if class_key:
            return {
                "confidence": "PROBABLE", "class": class_key,
                "reason": evidence(f"{CLASS_NAMES[class_key]} line/layer convergence; class label is probable, not confirmed"),
            }
        if line_is_class_marker(driver_text):
            return {
                "confidence": "UNRESOLVED", "class": None,
                "reason": evidence("class-compatible line appears in a different layer; conflicting evidence"),
            }
        if line_is_gabaergic(driver_text):
            return {
                "confidence": "UNRESOLVED", "class": None,
                "reason": evidence("GABAergic line conflicts with spiny morphology"),
            }
        return {
            "confidence": "LAYER-ONLY", "class": None,
            "reason": evidence("layer is known but the line and morphology do not establish a projection class"),
        }

    if line_is_class_marker(driver_text) and class_key is None:
        return {
            "confidence": "UNRESOLVED", "class": None,
            "reason": evidence("class-compatible line without matching layer; dendrite unknown"),
        }
    return {
        "confidence": "UNRESOLVED", "class": None,
        "reason": evidence("dendrite type unavailable; identity cannot be assessed"),
    }


def population_confidence(records: Sequence[dict[str, Any]]) -> str:
    final = [record for record in records if record["flags"]["stage_12"]]
    counts = Counter(record["identity"]["confidence"] for record in final)
    if counts.get("CONFIRMED", 0) > 0:
        return "CONFIRMED"
    if counts.get("PROBABLE", 0) >= 3:
        return "PROBABLE"
    if counts.get("LAYER-ONLY", 0) >= 1:
        return "LAYER-ONLY"
    return "UNRESOLVED"


# ---------------------------------------------------------------------------
# Eligibility stages
# ---------------------------------------------------------------------------
def build_stage_flags(cell: dict[str, Any], sweep: dict[str, Any],
                      model: dict[str, Any], morph_ok: bool) -> dict[str, bool]:
    ephys_ok = bool(cell.get("ephys_available")) and not bool(cell.get("ephys_failed"))
    has_model = (model["n_perisomatic"] + model["n_all_active"]) >= 1
    flags = {
        "stage_01": True,
        "stage_02": ephys_ok and sweep["n_long_square_cc"] >= 1,
        "stage_03": ephys_ok and sweep["n_depolarizing"] >= 1,
        "stage_04": ephys_ok and sweep["n_depolarizing"] >= 1
                    and sweep["n_distinct_depolarizing"] >= MIN_DISTINCT_AMPLITUDES,
        "stage_05": ephys_ok
                    and sweep["n_long_square_cc"] >= MIN_LONG_SQUARE
                    and sweep["n_depolarizing"] >= MIN_DEPOLARIZING
                    and sweep["n_distinct_depolarizing"] >= MIN_DISTINCT_AMPLITUDES,
        "stage_06": False,
        "stage_07": False,
        "stage_08": False,
        "stage_09": False,
        "stage_10": False,
        "stage_11": False,
        "stage_12": False,
        "stage_12b": False,
        "stage_12c": False,
        "stage_12d": False,
        "stage_12e": False,
    }
    flags["stage_06"] = flags["stage_05"] and bool(cell.get("nwb_download_url"))
    flags["stage_07"] = flags["stage_06"] and model["n_perisomatic"] >= 1
    flags["stage_08"] = flags["stage_06"] and model["n_all_active"] >= 1
    flags["stage_09"] = flags["stage_06"] and model["n_perisomatic"] >= 1 and model["n_all_active"] >= 1
    flags["stage_10"] = flags["stage_06"] and morph_ok
    flags["stage_11"] = flags["stage_06"] and model["n_descriptor_resolved"] >= 1
    flags["stage_12"] = (flags["stage_06"] and has_model
                         and model["n_descriptor_resolved"] >= 1 and morph_ok)
    flags["stage_12b"] = flags["stage_12"] and flags["stage_09"]
    flags["stage_12e"] = flags["stage_12"] and _text(cell.get("dendrite_type")) == "spiny"
    return flags


REQUIREMENTS = (
    ("ephys_available_and_not_failed", "EphysResult available and not failed"),
    ("long_square_current_clamp", ">= 1 long-square current-clamp sweep"),
    ("depolarizing_long_square", ">= 1 depolarising long-square sweep"),
    ("two_distinct_amplitudes", ">= 2 distinct depolarising amplitudes"),
    ("sufficient_conditions", ">= 6 long-square, >= 3 depolarising, >= 2 distinct"),
    ("nwb_reference", "NWB download reference resolved"),
    ("biophysical_model", ">= 1 biophysical model"),
    ("fit_descriptor", "fit-descriptor reference resolved"),
    ("morphology_asset", "usable morphology reconstruction"),
)


def requirement_status(cell: dict[str, Any], sweep: dict[str, Any],
                       model: dict[str, Any], morph_ok: bool) -> dict[str, bool]:
    ephys_ok = bool(cell.get("ephys_available")) and not bool(cell.get("ephys_failed"))
    return {
        "ephys_available_and_not_failed": ephys_ok,
        "long_square_current_clamp": sweep["n_long_square_cc"] >= 1,
        "depolarizing_long_square": sweep["n_depolarizing"] >= 1,
        "two_distinct_amplitudes": sweep["n_distinct_depolarizing"] >= MIN_DISTINCT_AMPLITUDES,
        "sufficient_conditions": (
            sweep["n_long_square_cc"] >= MIN_LONG_SQUARE
            and sweep["n_depolarizing"] >= MIN_DEPOLARIZING
            and sweep["n_distinct_depolarizing"] >= MIN_DISTINCT_AMPLITUDES
        ),
        "nwb_reference": bool(cell.get("nwb_download_url")),
        "biophysical_model": (model["n_perisomatic"] + model["n_all_active"]) >= 1,
        "fit_descriptor": model["n_descriptor_resolved"] >= 1,
        "morphology_asset": morph_ok,
    }


def first_failing_requirement(status: dict[str, bool]) -> str:
    for key, _label in REQUIREMENTS:
        if not status[key]:
            return key
    return ""


def failed_requirements(status: dict[str, bool]) -> str:
    return ";".join(key for key, _label in REQUIREMENTS if not status[key])


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------
def population_for_layer(layer: str) -> dict[str, Any] | None:
    return POP_BY_LAYER.get(_text(layer))


def build_record(cell: dict[str, Any], sweep_rows: Sequence[dict[str, Any]],
                 model_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    sweep = summarise_sweeps(sweep_rows)
    model = summarise_models(model_rows)
    morph_ok, morph_reason = morphology_usable(cell)
    identity = classify_identity(cell["layer"], cell["driver_line"],
                                 cell["dendrite_type"], cell["apical_status"])
    flags = build_stage_flags(cell, sweep, model, morph_ok)
    flags["stage_12c"] = flags["stage_12"] and identity["confidence"] == "PROBABLE"
    flags["stage_12d"] = flags["stage_12c"] and flags["stage_09"]
    status = requirement_status(cell, sweep, model, morph_ok)

    record = {
        "cell": cell,
        "sweep": sweep,
        "model": model,
        "morphology": {"usable": morph_ok, "reason": morph_reason},
        "identity": identity,
        "flags": flags,
        "requirements": status,
        "population": population_for_layer(cell["layer"]),
    }
    record["first_failing_requirement"] = first_failing_requirement(status)
    record["failed_requirements"] = failed_requirements(status)
    return record


def build_records(cells: Sequence[dict[str, Any]],
                  sweeps: dict[int, list[dict[str, Any]]],
                  models: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    records = []
    for cell in cells:
        population = population_for_layer(cell["layer"])
        if population is None:
            continue  # L1 and any other layer outside the four candidates
        specimen_id = cell["specimen_id"]
        record = build_record(cell, sweeps.get(specimen_id, []), models.get(specimen_id, []))
        record["population"] = population
        # Integrity cross-check: the audit re-derives the model counts Phase 0
        # stored, so a silent model_inventory / cell_inventory disagreement
        # stops the audit instead of producing a plausible-looking number.
        expected = {
            "n_perisomatic": cell["phase0_n_perisomatic"],
            "n_all_active": cell["phase0_n_all_active"],
            "n_glif": cell["phase0_n_glif"],
        }
        for key, want in expected.items():
            got = record["model"][key]
            if want is not None and got != want:
                raise RuntimeError(
                    f"specimen {specimen_id}: model_inventory gives {key}={got}, "
                    f"cell_inventory gives {want}"
                )
        records.append(record)
    return records


# ---------------------------------------------------------------------------
# Counting and tables
# ---------------------------------------------------------------------------
def records_for(records: Sequence[dict[str, Any]], pop_key: str) -> list[dict[str, Any]]:
    return [record for record in records if record["population"]["key"] == pop_key]


def stage_rows(records: Sequence[dict[str, Any]], pop: dict[str, Any]) -> list[dict[str, Any]]:
    subset = records_for(records, pop["key"])
    total = len(subset)
    rows = []
    for stage in STAGES:
        if stage["base"] is None:
            base_n = total
        else:
            base_n = sum(1 for record in subset if record["flags"][stage["base"]])
        n = sum(1 for record in subset if record["flags"][stage["key"]])
        rows.append({
            "population": pop["key"],
            "population_label": pop["label"],
            "population_total": total,
            "stage": stage["number"],
            "stage_name": stage["name"],
            "stage_definition": stage["definition"],
            "stage_kind": stage["kind"],
            "base_stage": stage["base"] or "population",
            "base_n": base_n,
            "n": n,
            "pct_of_population": round(100.0 * n / total, 1) if total else None,
            "pct_of_base": round(100.0 * n / base_n, 1) if base_n else None,
            "phase0_pass": sum(1 for record in subset
                               if record["cell"]["phase0_eligibility"] == "PASS"),
        })
    return rows


def model_availability_row(records: Sequence[dict[str, Any]],
                           pop: dict[str, Any]) -> dict[str, Any]:
    subset = records_for(records, pop["key"])
    total = len(subset)
    final = [record for record in subset if record["flags"]["stage_12"]]

    def count(selected: Sequence[dict[str, Any]], predicate) -> int:
        return sum(1 for record in selected if predicate(record))

    perisomatic = lambda record: record["model"]["n_perisomatic"] >= 1
    all_active = lambda record: record["model"]["n_all_active"] >= 1
    both = lambda record: perisomatic(record) and all_active(record)
    identity_ok = lambda record: record["identity"]["confidence"] == "PROBABLE"

    matches = count(
        [record for record in subset if record["model"]["n_biophysical"]],
        lambda record: _model_reconstruction_matches(record) is True,
    )
    differs = count(
        [record for record in subset if record["model"]["n_biophysical"]],
        lambda record: _model_reconstruction_matches(record) is False,
    )
    executed = [record for record in subset if record["cell"]["specimen_id"] in EXECUTED_SPECIMENS]
    return {
        "population": pop["key"],
        "population_label": pop["label"],
        "population_total": total,
        "n_any_biophysical": count(subset, lambda record: record["model"]["n_biophysical"] >= 1),
        "n_perisomatic": count(subset, perisomatic),
        "n_all_active": count(subset, all_active),
        "n_both": count(subset, both),
        "n_glif_only": count(subset, lambda record: record["model"]["n_glif"] >= 1
                              and record["model"]["n_biophysical"] == 0),
        "n_fit_descriptor_resolved": count(subset, lambda record: record["model"]["n_descriptor_resolved"] >= 1),
        "n_morphology_usable": count(subset, lambda record: record["morphology"]["usable"]),
        "n_final_any_model": len(final),
        "n_final_perisomatic": count(final, perisomatic),
        "n_final_all_active": count(final, all_active),
        "n_final_both_models": count(final, both),
        "n_final_spiny": count(final, lambda record: record["cell"]["dendrite_type"] == "spiny"),
        "n_final_identity_compatible": count(final, identity_ok),
        "n_final_identity_perisomatic": count(final, lambda record: identity_ok(record) and perisomatic(record)),
        "n_final_identity_all_active": count(final, lambda record: identity_ok(record) and all_active(record)),
        "n_final_identity_both": count(final, lambda record: identity_ok(record) and both(record)),
        "n_model_reconstruction_matches": matches,
        "n_model_reconstruction_differs": differs,
        "perisomatic_template_id": PERISOMATIC_TEMPLATE_ID,
        "all_active_template_id": ALL_ACTIVE_TEMPLATE_ID,
        "n_listed_any": count(subset, lambda record: record["model"]["n_biophysical"] >= 1),
        "n_descriptor_resolved": count(subset, lambda record: record["model"]["n_descriptor_resolved"] >= 1),
        "n_assets_in_repo": 1 if executed else 0,
        "n_executable_in_repo": 1 if executed else 0,
        "n_validated_against_recording": 0,
    }


def _model_reconstruction_matches(record: dict[str, Any]) -> bool | None:
    cell_recon = record["cell"]["reconstruction_id"]
    model_recons = record["model"]["model_reconstruction_ids"]
    if cell_recon is None or not model_recons:
        return None
    return all(recon == cell_recon for recon in model_recons)


def ranking_key(record: dict[str, Any]) -> tuple:
    cell = record["cell"]
    identity_rank = 0 if record["identity"]["confidence"] == "PROBABLE" else 1
    both_rank = 0 if record["model"]["n_perisomatic"] and record["model"]["n_all_active"] else 1
    full_rank = 0 if cell["reconstruction_type"] == "full" else 1
    rate_rank = -(cell["sampling_rate_hz"] or 0)
    return (
        identity_rank,
        both_rank,
        full_rank,
        -record["sweep"]["n_distinct_depolarizing"],
        -record["sweep"]["n_long_square_cc"],
        rate_rank,
        cell["specimen_id"],
    )


def candidate_rows(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for pop in POPULATIONS:
        final = [record for record in records_for(records, pop["key"])
                 if record["flags"]["stage_12"]]
        final.sort(key=ranking_key)
        for rank, record in enumerate(final, start=1):
            cell = record["cell"]
            model = record["model"]
            peri = model["perisomatic"] or {}
            allact = model["all_active"] or {}
            rows.append({
                "population": pop["key"],
                "population_label": pop["label"],
                "rank_within_population": rank,
                "specimen_id": cell["specimen_id"],
                "layer": cell["layer"],
                "structure_acronym": cell["structure_acronym"],
                "driver_line": cell["driver_line"],
                "reporter_line": cell["reporter_line"],
                "genotype": cell["genotype"],
                "dendrite_type": cell["dendrite_type"],
                "apical_dendrite_status": cell["apical_status"],
                "ephys_result_id": cell["ephys_result_id"],
                "sampling_rate_hz": cell["sampling_rate_hz"],
                "n_long_square_cc": record["sweep"]["n_long_square_cc"],
                "n_depolarizing_sweeps": record["sweep"]["n_depolarizing"],
                "n_distinct_depolarizing_amplitudes": record["sweep"]["n_distinct_depolarizing"],
                "n_repeated_depolarizing_amplitudes": record["sweep"]["n_repeated_depolarizing"],
                "depolarizing_min_pa": record["sweep"]["depolarizing_min_pa"],
                "depolarizing_max_pa": record["sweep"]["depolarizing_max_pa"],
                "nwb_file_id": cell["nwb_file_id"],
                "nwb_download_url": cell["nwb_download_url"],
                "perisomatic_model_id": peri.get("model_id"),
                "perisomatic_template_id": peri.get("template_id"),
                "perisomatic_fit_file_id": peri.get("well_known_file_id"),
                "perisomatic_reconstruction_id": peri.get("reconstruction_id"),
                "all_active_model_id": allact.get("model_id"),
                "all_active_template_id": allact.get("template_id"),
                "all_active_fit_file_id": allact.get("well_known_file_id"),
                "all_active_reconstruction_id": allact.get("reconstruction_id"),
                "model_reconstruction_matches_specimen": _model_reconstruction_matches(record),
                "has_morphology": cell["has_morphology"],
                "reconstruction_id": cell["reconstruction_id"],
                "reconstruction_type": cell["reconstruction_type"],
                "reconstruction_superseded": cell["reconstruction_superseded"],
                "morphology_download_url": cell["morphology_download_url"],
                "has_perisomatic": record["model"]["n_perisomatic"] >= 1,
                "has_all_active": record["model"]["n_all_active"] >= 1,
                "has_both": (record["model"]["n_perisomatic"] >= 1
                             and record["model"]["n_all_active"] >= 1),
                "identity_class": record["identity"]["class"] or "",
                "identity_confidence": record["identity"]["confidence"],
                "identity_evidence": record["identity"]["reason"],
                "is_spiny_excitatory": cell["dendrite_type"] == "spiny",
                "is_identity_compatible": record["identity"]["confidence"] == "PROBABLE",
                "eligible_any_model": record["flags"]["stage_12"],
                "eligible_both_models": record["flags"]["stage_12b"],
                "phase0_eligibility": cell["phase0_eligibility"],
            })
    return rows


def exclusion_rows(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        if record["flags"]["stage_12"]:
            continue
        cell = record["cell"]
        rows.append({
            "population": record["population"]["key"],
            "population_label": record["population"]["label"],
            "specimen_id": cell["specimen_id"],
            "layer": cell["layer"],
            "driver_line": cell["driver_line"],
            "dendrite_type": cell["dendrite_type"],
            "ephys_failed": cell["ephys_failed"],
            "n_long_square_cc": record["sweep"]["n_long_square_cc"],
            "n_depolarizing_sweeps": record["sweep"]["n_depolarizing"],
            "n_distinct_depolarizing_amplitudes": record["sweep"]["n_distinct_depolarizing"],
            "has_perisomatic": record["model"]["n_perisomatic"] >= 1,
            "has_all_active": record["model"]["n_all_active"] >= 1,
            "has_morphology": cell["has_morphology"],
            "has_fit_descriptor": record["model"]["n_descriptor_resolved"] >= 1,
            "first_failing_requirement": record["first_failing_requirement"],
            "failed_requirements": record["failed_requirements"],
            "identity_confidence": record["identity"]["confidence"],
        })
    return rows


# ---------------------------------------------------------------------------
# Recording, model, identity and balance summaries
# ---------------------------------------------------------------------------
def _median(values: Sequence[float]) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def recording_summary(records: Sequence[dict[str, Any]], pop: dict[str, Any]) -> dict[str, Any]:
    subset = records_for(records, pop["key"])
    ls_counts = [record["sweep"]["n_long_square_cc"] for record in subset]
    dep_counts = [record["sweep"]["n_depolarizing"] for record in subset]
    distinct = [record["sweep"]["n_distinct_depolarizing"] for record in subset]
    repeated = [record["sweep"]["n_repeated_depolarizing"] for record in subset]
    units = Counter()
    for record in subset:
        for unit in record["sweep"]["units_observed"]:
            units[unit] += 1
    return {
        "population": pop["key"],
        "specimens": len(subset),
        "recording_sessions": len({record["cell"]["ephys_result_id"] for record in subset}),
        "nwb_files_referenced": sum(1 for record in subset
                                    if record["cell"]["nwb_download_url"]),
        "nwb_files_opened_in_repo": sum(1 for record in subset
                                        if record["cell"]["specimen_id"] in EXECUTED_SPECIMENS),
        "sampling_50khz": sum(1 for record in subset
                              if record["cell"]["sampling_rate_hz"] == 50_000),
        "sampling_200khz": sum(1 for record in subset
                               if record["cell"]["sampling_rate_hz"] == 200_000),
        "n_long_square_cc_total": sum(ls_counts),
        "n_long_square_cc_median": _median(ls_counts),
        "n_long_square_cc_min": min(ls_counts) if ls_counts else None,
        "n_long_square_cc_max": max(ls_counts) if ls_counts else None,
        "n_depolarizing_total": sum(dep_counts),
        "n_distinct_depolarizing_median": _median(distinct),
        "n_distinct_depolarizing_min": min(distinct) if distinct else None,
        "n_distinct_depolarizing_max": max(distinct) if distinct else None,
        "n_with_ge3_distinct": sum(1 for value in distinct if value >= 3),
        "n_with_ge5_distinct": sum(1 for value in distinct if value >= 5),
        "n_with_repeated_amplitude": sum(1 for value in repeated if value >= 1),
        "units_label_counts": dict(sorted(units.items())),
        "n_failed_ephys": sum(1 for record in subset if record["cell"]["ephys_failed"]),
        "n_implicit_clamp_mode_only": sum(
            1 for record in subset
            if record["sweep"]["n_implicit_cc"] > 0 and record["sweep"]["n_explicit_cc"] == 0
        ),
        "depolarizing_range_pa": [
            min((record["sweep"]["depolarizing_min_pa"] for record in subset
                 if record["sweep"]["depolarizing_min_pa"] is not None), default=None),
            max((record["sweep"]["depolarizing_max_pa"] for record in subset
                 if record["sweep"]["depolarizing_max_pa"] is not None), default=None),
        ],
    }


def identity_summary(records: Sequence[dict[str, Any]], pop: dict[str, Any]) -> dict[str, Any]:
    subset = records_for(records, pop["key"])
    final = [record for record in subset if record["flags"]["stage_12"]]
    all_counts = Counter(record["identity"]["confidence"] for record in subset)
    final_counts = Counter(record["identity"]["confidence"] for record in final)
    class_counts = Counter(record["identity"]["class"] for record in final
                           if record["identity"]["class"])
    return {
        "population": pop["key"],
        "population_total": len(subset),
        "all_confidence_counts": dict(sorted(all_counts.items())),
        "final_confidence_counts": dict(sorted(final_counts.items())),
        "final_class_counts": dict(sorted(class_counts.items())),
        "population_confidence": population_confidence(subset),
    }


def build_summary(records: Sequence[dict[str, Any]], source_report: list[dict[str, Any]],
                  counts: Sequence[dict[str, Any]], models: Sequence[dict[str, Any]],
                  visp_total: int) -> dict[str, Any]:
    populations = []
    for pop in POPULATIONS:
        subset = records_for(records, pop["key"])
        populations.append({
            "key": pop["key"],
            "label": pop["label"],
            "proposed_identity": pop["proposed"],
            "layers": list(pop["layers"]),
            "total": len(subset),
            "stage_counts": {row["stage"]: row["n"] for row in counts
                             if row["population"] == pop["key"]},
            "stage_rows": [dict(row) for row in counts if row["population"] == pop["key"]],
            "final_both_models": sum(1 for record in subset if record["flags"]["stage_12b"]),
            "final_spiny": sum(1 for record in subset if record["flags"]["stage_12e"]),
            "final_identity_compatible": sum(1 for record in subset if record["flags"]["stage_12c"]),
            "final_identity_both": sum(1 for record in subset if record["flags"]["stage_12d"]),
            "phase0_pass": sum(1 for record in subset
                               if record["cell"]["phase0_eligibility"] == "PASS"),
            "recording": recording_summary(records, pop),
            "models": dict(next(row for row in models if row["population"] == pop["key"])),
            "identity": identity_summary(records, pop),
        })
    return {
        "phase": PHASE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "src/data_audit/four_population_audit.py",
        "region": REGION,
        "species": SPECIES,
        "thresholds": {
            "min_long_square": MIN_LONG_SQUARE,
            "min_depolarizing": MIN_DEPOLARIZING,
            "min_distinct_amplitudes": MIN_DISTINCT_AMPLITUDES,
            "amplitude_decimals": AMPLITUDE_DECIMALS,
        },
        "source_verification": source_report,
        "identity_schema_probe": IDENTITY_SCHEMA_PROBE,
        "population_definitions": [
            {"key": pop["key"], "label": pop["label"], "layers": list(pop["layers"]),
             "proposed_identity": pop["proposed"]}
            for pop in POPULATIONS
        ],
        "populations": populations,
        "totals": {
            "visp_mouse_specimens": visp_total,
            "four_population_specimens": len(records),
            "outside_populations": visp_total - len(records),
            "four_population_final_any": sum(1 for record in records if record["flags"]["stage_12"]),
            "four_population_final_both": sum(1 for record in records if record["flags"]["stage_12b"]),
            "four_population_final_spiny": sum(1 for record in records if record["flags"]["stage_12e"]),
            "four_population_final_identity": sum(1 for record in records if record["flags"]["stage_12c"]),
        },
        "quality_checks": [],
    }


def quality_checks(records: Sequence[dict[str, Any]],
                   counts: Sequence[dict[str, Any]],
                   models: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    ids = [record["cell"]["specimen_id"] for record in records]
    add("specimen_ids_unique", len(ids) == len(set(ids)),
        f"{len(ids)} records, {len(set(ids))} distinct specimen ids")

    group_sum = sum(1 for _ in records)
    add("groups_are_disjoint_and_cover_the_four_layers",
        group_sum == 1546 and len(set(ids)) == 1546,
        f"four-group specimens={group_sum}; expected 1546 (1588 VISp minus 42 L1)")

    add("no_specimen_in_two_populations",
        all(sum(1 for record in records if record["cell"]["specimen_id"] == sid) == 1
            for sid in set(ids)),
        "each specimen id appears in exactly one population")

    add("every_model_maps_to_a_group_specimen",
        all(record["cell"]["specimen_id"] in set(ids) for record in records),
        "all model rows used by the audit belong to inventoried specimens")

    peri_ids = [record["model"]["perisomatic"]["model_id"] for record in records
                if record["model"]["perisomatic"]]
    all_ids = [record["model"]["all_active"]["model_id"] for record in records
               if record["model"]["all_active"]]
    overlap = set(peri_ids) & set(all_ids)
    add("all_model_ids_are_unique",
        len(peri_ids) == len(set(peri_ids)) and len(all_ids) == len(set(all_ids))
        and not overlap,
        f"perisomatic {len(peri_ids)} ids / {len(set(peri_ids))} distinct; "
        f"all-active {len(all_ids)} ids / {len(set(all_ids))} distinct; "
        f"cross-class overlap {len(overlap)}")

    add("final_is_a_subset_of_every_required_facet",
        all(not record["flags"]["stage_12"] or (
            record["flags"]["stage_06"] and record["flags"]["stage_10"]
            and record["flags"]["stage_11"])
            for record in records),
        "every final specimen has recording, NWB, morphology and descriptor")

    add("stage_counts_are_monotonic",
        all(row["n"] <= row["base_n"] for row in counts),
        "no stage exceeds its base")

    add("every_nonfinal_specimen_has_a_reason",
        all(record["first_failing_requirement"] for record in records
            if not record["flags"]["stage_12"]),
        "first failing requirement recorded for every exclusion")

    add("every_final_specimen_has_a_morphology_and_a_model",
        all(record["morphology"]["usable"] and record["model"]["n_biophysical"] >= 1
            for record in records if record["flags"]["stage_12"]),
        "final eligibility includes both assets")

    add("identity_is_never_confirmed",
        all(record["identity"]["confidence"] != "CONFIRMED" for record in records),
        "no projection field exists, so no specimen can be CONFIRMED")

    for pop in POPULATIONS:
        subset = records_for(records, pop["key"])
        pass_n = sum(1 for record in subset
                     if record["cell"]["phase0_eligibility"] == "PASS")
        final_n = sum(1 for record in subset if record["flags"]["stage_12"])
        add(f"phase0_pass_covers_final_{pop['key']}", pass_n >= final_n,
            f"{pop['key']}: {pass_n} Phase 0 PASS vs {final_n} final eligible; "
            "final adds a morphology requirement, so final must not exceed PASS")

    return checks


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def print_tables(summary: dict[str, Any]) -> None:
    print("\nPOPULATION COUNTS (stage 12 = final eligible)\n")
    header = "pop  total  LSCC  dep  dist  suff  NWB  peri  all  both  morph  desc  final  both  spiny  ident  ident+both  phase0PASS"
    print(header)
    for pop in summary["populations"]:
        stages = pop["stage_counts"]
        print(
            f"{pop['key']:>3} {pop['total']:>6} {stages[2]:>5} {stages[3]:>4} "
            f"{stages[4]:>5} {stages[5]:>5} {stages[6]:>4} {stages[7]:>5} "
            f"{stages[8]:>4} {stages[9]:>5} {stages[10]:>6} {stages[11]:>5} "
            f"{stages[12]:>6} {pop['final_both_models']:>5} {pop['final_spiny']:>6} "
            f"{pop['final_identity_compatible']:>6} {pop['final_identity_both']:>11} "
            f"{pop['phase0_pass']:>10}"
        )
    print("\nIDENTITY\n")
    for pop in summary["populations"]:
        identity = pop["identity"]
        print(f"{pop['key']}: {identity['population_confidence']:>10}  "
              f"all={identity['all_confidence_counts']}  "
              f"final={identity['final_confidence_counts']}  "
              f"class={identity['final_class_counts']}")
    print("\nMODEL EVIDENCE\n")
    for pop in summary["populations"]:
        model = pop["models"]
        print(f"{pop['key']}: listed={model['n_listed_any']} "
              f"descriptor={model['n_descriptor_resolved']} "
              f"assets_in_repo={model['n_assets_in_repo']} "
              f"executable={model['n_executable_in_repo']} "
              f"validated_against_recording={model['n_validated_against_recording']}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell-inventory", type=Path, default=CELL_CSV)
    parser.add_argument("--sweep-inventory", type=Path, default=SWEEP_CSV)
    parser.add_argument("--model-inventory", type=Path, default=MODEL_CSV)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_JSON)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--print-tables", action="store_true")
    args = parser.parse_args(argv)

    source_report = verify_sources(
        [args.cell_inventory, args.sweep_inventory, args.model_inventory],
        manifest_path=args.manifest,
    )

    cells = load_cells(args.cell_inventory)
    sweeps = load_sweeps(args.sweep_inventory)
    models = load_models(args.model_inventory)
    records = build_records(cells, sweeps, models)

    counts: list[dict[str, Any]] = []
    for pop in POPULATIONS:
        counts.extend(stage_rows(records, pop))
    model_rows = [model_availability_row(records, pop) for pop in POPULATIONS]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_rows(args.out_dir / "four_population_counts.csv", COUNT_COLUMNS, counts)
    write_rows(args.out_dir / "four_population_candidates.csv", CANDIDATE_COLUMNS,
               candidate_rows(records))
    write_rows(args.out_dir / "four_population_exclusions.csv", EXCLUSION_COLUMNS,
               exclusion_rows(records))
    write_rows(args.out_dir / "four_population_model_availability.csv", MODEL_COLUMNS,
               model_rows)

    summary = build_summary(records, source_report, counts, model_rows, len(cells))
    summary["quality_checks"] = quality_checks(records, counts, model_rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if args.print_tables:
        print_tables(summary)

    print(f"specimens audited: {len(records)}")
    print(f"counts:     {args.out_dir / 'four_population_counts.csv'}")
    print(f"candidates: {args.out_dir / 'four_population_candidates.csv'}")
    print(f"exclusions: {args.out_dir / 'four_population_exclusions.csv'}")
    print(f"models:     {args.out_dir / 'four_population_model_availability.csv'}")
    print(f"summary:    {args.summary}")

    failed = [check for check in summary["quality_checks"] if not check["ok"]]
    for check in summary["quality_checks"]:
        print(f"  {'PASS' if check['ok'] else 'FAIL'}  {check['check']}: {check['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

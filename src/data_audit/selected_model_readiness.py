"""Phase 0C: validate selected V1 model and recording readiness.

Purpose
-------
Phase 0B established *metadata-level* availability: how many VISp specimens per
layer-defined excitatory population have a perisomatic biophysical model listed
against them.  It did not open a single fit descriptor, download a model asset,
or check that a specimen's sweeps could be split without leaking the fitting
data into held-out evaluation.

This script answers the narrower, harder question the supervisor actually asked:

    Is a 4 population x 4 neuron **perisomatic** study executable *here*, with
    assets we can obtain, descriptors we can parse, fitting sweeps we can
    identify, and held-out conditions that do not overlap the fit?

It is a readiness audit.  It downloads 16 fit descriptors and four representative
NWB recordings, verifies references through the Allen RMA v2 API, and performs
static asset checks.  It does **not** compile NEURON, run any model, or start the
FHN work.

Why the implementation looks the way it does
--------------------------------------------
1. **Populations are layer-defined, nothing more.**  Allen's specimen metadata
   carries no projection identity, so A is "VISp L4 spiny excitatory", not
   "spiny stellate"; B is "VISp L2/3 spiny excitatory", not "IT"; C is
   "VISp L5 spiny excitatory", not "ET/PT"; D is "VISp L6a spiny excitatory",
   not "corticothalamic".  Phase 0B put L6a and L6b in one population; Phase 0C
   freezes D to L6a because that is what the brief names, so the population is a
   strict subset of B's Phase 0B pool and the count is reported as such.
2. **Selection follows the brief's seven priorities in order**, as a cascade:
   candidates satisfying an earlier priority are never displaced by a candidate
   that only satisfies a later one.  After the cascade, ties are broken by
   independent-condition richness (distinct depolarising amplitudes, then
   long-square sweeps) because the brief's own section 7 warns that many sweeps
   are not many conditions.  The specimen id is the final tie-break, so the
   frozen table is reproducible to the row.
3. **A missing fit descriptor is not a model.**  Every downstream level (fitting
   sweeps, held-out split, asset readiness) is derived from the *downloaded
   bytes*, and a download failure propagates as an explicit blocker rather than
   as a silently absent value.  This is the rule the brief calls "download
   failures are not counted as successful asset availability".
4. **Fitting sweeps are read, never guessed.**  ``fitting[].sweeps`` is present in
   the perisomatic documents, but nothing here assumes it: the parser reports an
   empty list when the key is absent and the held-out planner then returns
   ``UNRESOLVED_NO_FITTING_SWEEPS``.  A fitting sweep that cannot be found in the
   specimen's own sweep inventory is reported as unmapped rather than dropped.
5. **NWB validation is delegated.**  ``scripts/validate_nwb_stimulus_units.py``
   already carries the Phase 1B/1C units-aware rule and the embedded-probe
   handling that was validated against 236 sweeps.  Re-implementing it here would
   create a second, divergent definition of "the raw stimulus is in amperes", so
   this script shells out to it with ``--json-out`` and only reduces the result.

Usage
-----
    python src/data_audit/selected_model_readiness.py
    python src/data_audit/selected_model_readiness.py --no-download
    python src/data_audit/selected_model_readiness.py --evidence-out tmp/p0c.json

Exit code 0 means every self-check passed.  1 means a self-check failed.  2 means
the audit ran but a required asset could not be obtained (reported, not hidden).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
RESULTS_DIR = PROJECT_ROOT / "results" / "dataset_inventory"

CELL_CSV = METADATA_DIR / "cell_inventory.csv"
SWEEP_CSV = METADATA_DIR / "sweep_inventory.csv"
PHASE0B_CANDIDATES = RESULTS_DIR / "four_population_candidates.csv"

DEFAULT_OUT_DIR = RESULTS_DIR
FIT_CACHE = PROJECT_ROOT / "tmp" / "fit_cache"
NWB_CACHE = PROJECT_ROOT / "data" / "nwb_cache"
MORPHOLOGY_CACHE = PROJECT_ROOT / "tmp" / "morphology_cache"
VALIDATOR = PROJECT_ROOT / "scripts" / "validate_nwb_stimulus_units.py"

PHASE = "0C"
REGION = "VISp"
SPECIES = "Mus musculus"

#: Allen RMA v2, the same endpoint Phase 0 used.
API_QUERY_URL = "http://api.brain-map.org/api/v2/data/query.json"
API_BASE = "http://api.brain-map.org"
USER_AGENT = ("INCM-Phase0C-ReadinessAudit/1.0 "
              "(academic research; Allen Cell Types DB metadata only)")
HTTP_TIMEOUT = 180
MAX_TRIES = 4
MIN_DELAY_S = 0.15
ID_CHUNK = 100

#: Well-known-file type ids.  Logged, never used to *classify* a model: the fit
#: JSON and the GLIF neuron_config JSON share type 329230374.
WKFT_MODEL_PARAMETERS = 329230374
WKFT_3D_RECONSTRUCTION = 303941301

#: Phase 0's evidence thresholds, retained so Phase 0C cannot silently redefine
#: "usable recording".
MIN_LONG_SQUARE = 6
MIN_DEPOLARIZING = 3
AMPLITUDE_DECIMALS = 3

#: The brief's selection priority 4: at least five distinct depolarising
#: amplitudes.  Phase 0B's eligibility floor was two; this is a *preference* used
#: to rank, and violations are reported rather than hidden.
PREFERRED_MIN_DISTINCT = 5
PREFERRED_RATE_HZ = 200000
TARGET_PER_POPULATION = 4

#: Model classes are identified by template id, never by file type.
PERISOMATIC_TEMPLATE_ID = 329230710
ALL_ACTIVE_TEMPLATE_ID = 491455321

#: The four frozen, layer-defined populations.  ``not_claimed`` is the phrasing
#: the report is required to use: the layer is measured, the projection class is
#: not, so every identity statement stops at "spiny excitatory".
POPULATIONS: tuple[dict[str, Any], ...] = (
    {
        "key": "A",
        "label": "VISp L4 spiny excitatory neuron",
        "short": "L4",
        "layers": ("4",),
        "not_claimed": "spiny stellate",
    },
    {
        "key": "B",
        "label": "VISp L2/3 spiny excitatory neuron",
        "short": "L2/3",
        "layers": ("2/3",),
        "not_claimed": "IT (intratelencephalic)",
    },
    {
        "key": "C",
        "label": "VISp L5 spiny excitatory neuron",
        "short": "L5",
        "layers": ("5",),
        "not_claimed": "ET (extratelencephalic) / PT (pyramidal tract)",
    },
    {
        "key": "D",
        "label": "VISp L6a spiny excitatory neuron",
        "short": "L6a",
        "layers": ("6a",),
        "not_claimed": "corticothalamic",
    },
)
POP_BY_KEY = {pop["key"]: pop for pop in POPULATIONS}

#: Eight separated evidence levels.  Kept as an ordered tuple because the whole
#: point of the audit is that these are *not* interchangeable.
EVIDENCE_LEVELS = (
    ("L1", "L1_listed_in_metadata"),
    ("L2", "L2_fit_descriptor_downloaded_and_parsed"),
    ("L3", "L3_morphology_asset_available"),
    ("L4", "L4_model_archive_or_mechanisms_available"),
    ("L5", "L5_model_reconstruction_matches_specimen"),
    ("L6", "L6_fitting_sweeps_identifiable"),
    ("L7", "L7_potentially_executable"),
    ("L8", "L8_actually_executed_and_validated"),
)

CANDIDATE_COLUMNS = (
    "population", "population_label", "selection_rank", "specimen_id",
    "ephys_result_id", "layer", "structure_acronym", "driver_line",
    "dendrite_type", "apical_dendrite_status",
    "perisomatic_model_id", "perisomatic_template_id", "fit_file_id",
    "model_reconstruction_id", "specimen_reconstruction_id",
    "reconstruction_match", "reconstruction_type", "sampling_rate_hz",
    "n_long_square_sweeps", "n_long_square_rows", "n_depolarizing_sweeps",
    "n_distinct_depolarizing_amplitudes", "n_repeated_depolarizing_amplitudes",
    "depolarizing_min_pa", "depolarizing_max_pa", "nwb_reference",
    "morphology_reference", "identity_confidence", "identity_evidence",
    "selection_tier", "selection_rationale",
)

FIT_COLUMNS = (
    "population", "specimen_id", "perisomatic_model_id", "fit_file_id",
    "download_url", "download_status", "http_status", "file_name",
    "size_bytes", "sha256", "parsed_ok", "top_level_keys", "model_type",
    "passive_keys", "genome_length", "genome_value_types", "mechanisms",
    "n_fitting_blocks", "fitting_block_keys", "fitting_sweeps",
    "n_fitting_sweeps", "conditions_keys", "junction_potential_mv",
    "celsius_c", "v_init_mv", "missing_fields", "ambiguous_fields",
    "descriptor_matches_model", "descriptor_matches_specimen",
    "fitting_sweeps_mapped", "unmapped_fitting_sweeps",
    "fitting_sweep_amplitudes", "fitting_protocol_blocks", "note",
)

RECORDING_COLUMNS = (
    "population", "specimen_id", "ephys_result_id", "nwb_file_id",
    "nwb_reference", "nwb_cached", "sampling_rate_hz", "n_long_square_rows",
    "n_long_square_cc", "n_depolarizing_sweeps",
    "n_distinct_depolarizing_amplitudes", "n_repeated_depolarizing_amplitudes",
    "depolarizing_min_pa", "depolarizing_max_pa", "protocol_families",
    "protocol_blocks", "n_coarse_sweeps", "n_finest_sweeps", "n_c2_sweeps",
    "is_representative", "nwb_verdict", "nwb_identity_match",
    "nwb_n_stimulus_series", "nwb_n_long_square_series",
    "nwb_matched_by_sweep_number", "nwb_inventory_only_count",
    "nwb_conversion_counts", "nwb_embedded_probe_sweeps",
    "nwb_step_onset_s", "nwb_step_duration_ms", "nwb_sampling_rate_hz",
    "nwb_file_size_bytes", "nwb_sha256", "note",
)

ASSET_COLUMNS = (
    "population", "specimen_id", "perisomatic_model_id", "template_id",
    "fit_file_id", "is_representative",
    "L1_listed_in_metadata", "L2_fit_descriptor_downloaded_and_parsed",
    "L3_morphology_asset_available", "L4_model_archive_or_mechanisms_available",
    "L5_model_reconstruction_matches_specimen", "L6_fitting_sweeps_identifiable",
    "L7_potentially_executable", "L8_actually_executed_and_validated",
    "morphology_evidence", "mechanism_evidence", "blockers", "note",
)

HELDOUT_COLUMNS = (
    "population", "specimen_id", "fit_file_id", "heldout_status",
    "fitting_sweeps", "n_fitting_sweeps", "n_fitting_depolarizing",
    "fitting_amplitudes_pa", "fitting_protocol_blocks",
    "n_heldout_depolarizing_sweeps", "n_heldout_distinct_amplitudes",
    "heldout_amplitudes_pa", "n_heldout_repeated_amplitudes",
    "heldout_protocol_blocks", "family_split_available",
    "proposed_calibration_condition", "proposed_heldout_condition",
    "leakage_safe", "split_frozen", "reason",
)


# ---------------------------------------------------------------------------
# Small I/O helpers
# ---------------------------------------------------------------------------
def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, columns: Sequence[str],
               rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns),
                                lineterminator="\n")
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
        if value != value or value in (float("inf"), float("-inf")):
            return ""
        return repr(round(value, 6))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return ";".join(str(_csv_value(item)) for item in value)
    return value


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if out != out else out


def _bool(value: Any) -> bool:
    return _text(value).lower() in ("true", "1", "yes", "t")


def _flagged(value: Any) -> bool:
    """Tristate helper for a CSV boolean that may be blank."""
    if value is None or value == "":
        return False
    return _bool(value)


# ---------------------------------------------------------------------------
# Metadata loading
# ---------------------------------------------------------------------------
def load_sweeps(path: Path = SWEEP_CSV) -> dict[int, list[dict[str, Any]]]:
    """Long-square VISp rows, grouped by specimen.

    Kept identical in shape to Phase 0B's loader so an amplitude counted here is
    the same amplitude Phase 0B counted.
    """
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


def units_aware_current_clamp(clamp_mode: str, stimulus_units: str) -> bool:
    """Phase 0's units-aware rule, restated.

    The ``pA`` label and a null ``clamp_mode`` are perfectly confounded in this
    database; Phase 1B validated the inventory number as picoamperes.  A row that
    explicitly says voltage clamp is never current clamp.  A test asserts this
    function agrees with ``four_population_audit.units_aware_current_clamp`` over
    the whole sweep inventory, so the duplication cannot drift.
    """
    mode = _text(clamp_mode).lower()
    return mode == "current_clamp" or (mode == "" and _text(stimulus_units) == "pA")


def protocol_family(stimulus_name: str) -> str:
    """Reduce an Allen long-square stimulus name to its protocol family.

    Names look like ``C1LSCOARSE150216`` / ``C1LSFINEST150112``.  The family is
    what matters for held-out design: COARSE and FINEST are different protocols,
    so a split across them tests a protocol shift, not just an amplitude shift.
    """
    name = _text(stimulus_name).upper()
    if not name:
        return "UNKNOWN"
    if "FINEST" in name:
        return "FINEST"
    if "COARSE" in name:
        return "COARSE"
    if name.startswith("C2") or "C2LS" in name:
        return "C2"
    return "OTHER"


def summarise_sweeps(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    cc = [row for row in rows
          if units_aware_current_clamp(row.get("clamp_mode", ""),
                                       row.get("stimulus_units", ""))]
    with_amplitude = [row for row in cc if row.get("amplitude") is not None]
    depolarising = [row for row in with_amplitude if float(row["amplitude"]) > 0]
    amplitudes = [round(float(row["amplitude"]), AMPLITUDE_DECIMALS)
                  for row in depolarising]
    counts = Counter(amplitudes)
    families = Counter(protocol_family(row.get("stimulus_name", "")) for row in cc)
    blocks = Counter(_text(row.get("stimulus_name")) for row in cc)
    return {
        "n_long_square_rows": len(rows),
        "n_long_square_cc": len(cc),
        "n_depolarizing": len(depolarising),
        "n_distinct_depolarizing": len(counts),
        "n_repeated_depolarizing": sum(1 for c in counts.values() if c >= 2),
        "depolarizing_min_pa": min(amplitudes) if amplitudes else None,
        "depolarizing_max_pa": max(amplitudes) if amplitudes else None,
        "distinct_depolarizing_pa": sorted(counts),
        "amplitude_counts": dict(sorted(counts.items())),
        "families": dict(sorted(families.items())),
        "blocks": dict(sorted(blocks.items())),
        "sweep_numbers": sorted(row["sweep_number"] for row in cc
                                if row.get("sweep_number") is not None),
        "units_observed": sorted({_text(row.get("stimulus_units")) for row in rows}),
    }


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------
def is_available_for_selection(row: dict[str, str], pop: dict[str, Any]) -> bool:
    """The brief's priority-1 and priority-2 gates, and nothing else.

    Priority 1 is the layer/spiny definition of the population; priority 2 is a
    perisomatic model.  A candidate failing either is not a candidate for *this*
    study, which is why all-active availability is never part of the filter.
    """
    return (row["population"] == pop["key"]
            and row["layer"] in pop["layers"]
            and row["dendrite_type"] == "spiny"
            and _flagged(row["has_perisomatic"]))


def selection_sort_key(row: dict[str, str]) -> tuple:
    """Priorities 3-7 as a cascade, then independent-condition richness.

    Priority 3 (model reconstruction matches specimen) outranks priority 4 (>= 5
    distinct amplitudes), which outranks priority 5 (200 kHz), which outranks
    priority 6 (sufficient long-square sweeps).  Priority 7 is a resolution gate
    already carried by :func:`is_available_for_selection` plus the fit-file id,
    and is re-asserted by :func:`selection_rationale`.

    After the cascade, more *distinct* amplitudes beat more sweeps: the brief's
    section 7 explicitly warns that repeated sweeps are not repeated conditions.
    """
    distinct = _int(row["n_distinct_depolarizing_amplitudes"]) or 0
    long_square = _int(row["n_long_square_cc"]) or 0
    rate = _int(row["sampling_rate_hz"]) or 0
    return (
        0 if _flagged(row["model_reconstruction_matches_specimen"]) else 1,
        0 if distinct >= PREFERRED_MIN_DISTINCT else 1,
        0 if rate >= PREFERRED_RATE_HZ else 1,
        -distinct,
        -long_square,
        _int(row["specimen_id"]) or 0,
    )


def selection_rationale(row: dict[str, str]) -> str:
    """State which priorities the candidate satisfies and which it does not."""
    parts = [f"P1 layer {row['layer']} + {row['dendrite_type']}"]
    parts.append(f"P2 perisomatic model {row['perisomatic_model_id']}")
    if _flagged(row["model_reconstruction_matches_specimen"]):
        parts.append(f"P3 model/specimen reconstruction {row['reconstruction_id']} match")
    else:
        parts.append("P3 NOT met: model reconstruction "
                     f"{row['perisomatic_reconstruction_id']} != specimen "
                     f"{row['reconstruction_id']}")
    distinct = _int(row["n_distinct_depolarizing_amplitudes"]) or 0
    marker = "" if distinct >= PREFERRED_MIN_DISTINCT else " NOT met:"
    parts.append(f"P4{marker} {distinct} distinct depolarising amplitudes")
    rate = _int(row["sampling_rate_hz"]) or 0
    parts.append(f"P5 {rate} Hz")
    parts.append(f"P6 {row['n_long_square_cc']} long-square sweeps")
    parts.append(f"P7 NWB {row['nwb_file_id']}, fit {row['perisomatic_fit_file_id']}, "
                 f"morphology {'resolved' if _flagged(row['has_morphology']) else 'MISSING'}")
    return "; ".join(parts)


def selection_tier(row: dict[str, str]) -> str:
    """PRIMARY when every stated priority is satisfied, else CONDITIONAL."""
    problems = []
    if not _flagged(row["model_reconstruction_matches_specimen"]):
        problems.append("reconstruction-mismatch")
    if (_int(row["n_distinct_depolarizing_amplitudes"]) or 0) < PREFERRED_MIN_DISTINCT:
        problems.append("fewer-than-5-distinct-amplitudes")
    if (_int(row["sampling_rate_hz"]) or 0) < PREFERRED_RATE_HZ:
        problems.append("sub-200kHz")
    if (_int(row["n_long_square_cc"]) or 0) < MIN_LONG_SQUARE:
        problems.append("fewer-than-6-long-square")
    if not _flagged(row["has_morphology"]):
        problems.append("no-morphology")
    if _int(row["perisomatic_fit_file_id"]) is None:
        problems.append("no-fit-file-id")
    return "PRIMARY" if not problems else "CONDITIONAL:" + ",".join(problems)


def morphology_file_id(url: str) -> int | None:
    tail = _text(url).rstrip("/").split("/")[-1]
    return _int(tail)


def select_candidates(rows: Sequence[dict[str, str]],
                      per_population: int = TARGET_PER_POPULATION
                      ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Freeze up to ``per_population`` candidates per population.

    Returns ``(selected, pool_summary)``.  The pool summary records the honest
    denominator: how many specimens were eligible before ranking, so a population
    that could not supply four is visible as a shortfall rather than as a smaller
    table.
    """
    selected: list[dict[str, Any]] = []
    pools: list[dict[str, Any]] = []
    for pop in POPULATIONS:
        pool = [row for row in rows if is_available_for_selection(row, pop)]
        pool.sort(key=selection_sort_key)
        chosen = pool[:per_population]
        pools.append({
            "population": pop["key"],
            "population_label": pop["label"],
            "layers": "/".join(pop["layers"]),
            "available": len(pool),
            "selected": len(chosen),
            "shortfall": max(0, per_population - len(chosen)),
            "primary": sum(1 for row in chosen
                           if selection_tier(row) == "PRIMARY"),
            "available_reconstruction_match": sum(
                1 for row in pool
                if _flagged(row["model_reconstruction_matches_specimen"])),
        })
        for rank, row in enumerate(chosen, start=1):
            selected.append(_candidate_record(pop, row, rank))
    ids = [item["specimen_id"] for item in selected]
    if len(ids) != len(set(ids)):
        raise RuntimeError("selection produced duplicate specimen ids")
    return selected, pools


def _candidate_record(pop: dict[str, Any], row: dict[str, str],
                      rank: int) -> dict[str, Any]:
    return {
        "population": pop["key"],
        "population_label": pop["label"],
        "population_short": pop["short"],
        "selection_rank": rank,
        "specimen_id": _int(row["specimen_id"]),
        "ephys_result_id": _int(row["ephys_result_id"]),
        "layer": row["layer"],
        "structure_acronym": row["structure_acronym"],
        "driver_line": row["driver_line"],
        "reporter_line": row["reporter_line"],
        "dendrite_type": row["dendrite_type"],
        "apical_status": row["apical_dendrite_status"],
        "sampling_rate_hz": _int(row["sampling_rate_hz"]),
        "n_long_square_cc": _int(row["n_long_square_cc"]),
        "n_long_square_rows": _int(row["n_long_square_cc"]),
        "n_depolarizing": _int(row["n_depolarizing_sweeps"]),
        "n_distinct_depolarizing": _int(row["n_distinct_depolarizing_amplitudes"]),
        "n_repeated_depolarizing": _int(row["n_repeated_depolarizing_amplitudes"]),
        "depolarizing_min_pa": _float(row["depolarizing_min_pa"]),
        "depolarizing_max_pa": _float(row["depolarizing_max_pa"]),
        "nwb_file_id": _int(row["nwb_file_id"]),
        "nwb_download_url": row["nwb_download_url"],
        "model_id": _int(row["perisomatic_model_id"]),
        "template_id": _int(row["perisomatic_template_id"]),
        "fit_file_id": _int(row["perisomatic_fit_file_id"]),
        "model_reconstruction_id": _int(row["perisomatic_reconstruction_id"]),
        "specimen_reconstruction_id": _int(row["reconstruction_id"]),
        "reconstruction_match": _flagged(row["model_reconstruction_matches_specimen"]),
        "reconstruction_type": row["reconstruction_type"],
        "morphology_download_url": row["morphology_download_url"],
        "morphology_file_id": morphology_file_id(row["morphology_download_url"]),
        "identity_class": row["identity_class"],
        "identity_confidence": row["identity_confidence"],
        "identity_evidence": row["identity_evidence"],
        "selection_rationale": selection_rationale(row),
        "selection_tier": selection_tier(row),
    }


def candidate_rows(selected: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in selected:
        rows.append({
            "population": item["population"],
            "population_label": item["population_label"],
            "selection_rank": item["selection_rank"],
            "specimen_id": item["specimen_id"],
            "ephys_result_id": item["ephys_result_id"],
            "layer": item["layer"],
            "structure_acronym": item["structure_acronym"],
            "driver_line": item["driver_line"],
            "dendrite_type": item["dendrite_type"],
            "apical_dendrite_status": item["apical_status"],
            "perisomatic_model_id": item["model_id"],
            "perisomatic_template_id": item["template_id"],
            "fit_file_id": item["fit_file_id"],
            "model_reconstruction_id": item["model_reconstruction_id"],
            "specimen_reconstruction_id": item["specimen_reconstruction_id"],
            "reconstruction_match": item["reconstruction_match"],
            "reconstruction_type": item["reconstruction_type"],
            "sampling_rate_hz": item["sampling_rate_hz"],
            "n_long_square_sweeps": item["n_long_square_cc"],
            "n_long_square_rows": item["n_long_square_rows"],
            "n_depolarizing_sweeps": item["n_depolarizing"],
            "n_distinct_depolarizing_amplitudes": item["n_distinct_depolarizing"],
            "n_repeated_depolarizing_amplitudes": item["n_repeated_depolarizing"],
            "depolarizing_min_pa": item["depolarizing_min_pa"],
            "depolarizing_max_pa": item["depolarizing_max_pa"],
            "nwb_reference": item["nwb_download_url"],
            "morphology_reference": item["morphology_download_url"],
            "identity_confidence": item["identity_confidence"],
            "identity_evidence": item["identity_evidence"],
            "selection_tier": item["selection_tier"],
            "selection_rationale": item["selection_rationale"],
        })
    return rows

# ---------------------------------------------------------------------------
# Allen RMA v2 access
# ---------------------------------------------------------------------------
class RmaClient:
    """Cached, retrying RMA v2 query client.

    Deliberately separate from ``allen_inventory.AllenRmaClient``: that client is
    built around paged inventory pulls and an error log file, whereas this one is
    used for 16-record lookups whose failure must surface per candidate.  The
    endpoint, user agent and courtesy delay are shared constants.
    """

    def __init__(self, cache_dir: Path, use_cache: bool = True,
                 verbose: bool = False) -> None:
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        self.verbose = verbose
        self.requests = 0
        self.cache_hits = 0
        self.errors: list[str] = []
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._last = 0.0

    def _cache_path(self, params: dict[str, Any]) -> Path:
        blob = json.dumps(params, sort_keys=True, default=str)
        digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]
        return self.cache_dir / f"{digest}.json"

    def query(self, model_class: str, criteria: str,
              num_rows: int = 500) -> dict[str, Any] | None:
        params = {"q": f"{model_class},rma::criteria,{criteria}",
                  "num_rows": num_rows}
        cache_path = self._cache_path(params)
        if self.use_cache and cache_path.exists():
            self.cache_hits += 1
            with cache_path.open(encoding="utf-8") as handle:
                return json.load(handle)

        last_detail = "unknown"
        for attempt in range(1, MAX_TRIES + 1):
            wait = max(0.0, MIN_DELAY_S - (time.monotonic() - self._last))
            if wait:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                self.requests += 1
                response = self.session.get(API_QUERY_URL, params=params,
                                            timeout=HTTP_TIMEOUT)
            except requests.RequestException as exc:
                last_detail = f"{type(exc).__name__}: {exc}"
                time.sleep(2 * attempt)
                continue
            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError as exc:
                    last_detail = f"invalid JSON: {exc}"
                    break
                if isinstance(payload, dict) and payload.get("success"):
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    with cache_path.open("w", encoding="utf-8") as handle:
                        json.dump(payload, handle, default=str)
                    return payload
                msg = payload.get("msg") if isinstance(payload, dict) else payload
                last_detail = f"success=false: {str(msg)[:200]}"
                break
            if response.status_code in (429, 500, 502, 503, 504):
                last_detail = f"HTTP {response.status_code}"
                time.sleep(2 * attempt)
                continue
            last_detail = f"HTTP {response.status_code}"
            break
        self.errors.append(f"{model_class} {criteria[:120]} -> {last_detail}")
        return None

    def rows(self, model_class: str, criteria: str,
             num_rows: int = 500) -> list[dict[str, Any]]:
        payload = self.query(model_class, criteria, num_rows=num_rows)
        if not payload:
            return []
        msg = payload.get("msg")
        if not isinstance(msg, list):
            return []
        return [row for row in msg if isinstance(row, dict)]

    def rows_by_id(self, model_class: str,
                   ids: Sequence[int]) -> dict[int, dict[str, Any]]:
        """Fetch records for ``ids`` (chunked) and return them keyed by id."""
        found: dict[int, dict[str, Any]] = {}
        ids = [int(value) for value in ids if value is not None]
        for start in range(0, len(ids), ID_CHUNK):
            chunk = ids[start:start + ID_CHUNK]
            rows = self.rows(model_class, "[id$in%s]" % ",".join(map(str, chunk)),
                             num_rows=len(chunk) + 10)
            for row in rows:
                key = _int(row.get("id"))
                if key is not None:
                    found[key] = row
        return found


def fetch_well_known_files(client: RmaClient,
                           file_ids: Sequence[int]) -> dict[int, dict[str, Any]]:
    """Second lookup path, because ``NeuronalModel.well_known_file_id`` is null.

    The published models do not carry the fit file id on the model record; the
    file record points back with ``attachable_id``/``attachable_type``.  Both
    directions are queried and the answer is required to agree.
    """
    return client.rows_by_id("model::WellKnownFile", file_ids)


# ---------------------------------------------------------------------------
# Asset downloads
# ---------------------------------------------------------------------------
def download_to(url: str, dest: Path, refresh: bool = False,
                timeout: int = HTTP_TIMEOUT) -> dict[str, Any]:
    """Stream ``url`` into ``dest``, resuming nothing and trusting no length.

    A partial file is written to ``dest.part`` and only renamed after the stream
    closes, so an interrupted download can never be mistaken for an asset.  Any
    exception is returned as a status, never raised: the caller must decide
    whether a failure is fatal, and the audit must record it either way.
    """
    result: dict[str, Any] = {"path": dest, "status": "FAILED",
                              "http_status": None, "size_bytes": None,
                              "sha256": None, "file_name": None, "error": None}
    if dest.exists() and not refresh:
        result.update(status="CACHED", size_bytes=dest.stat().st_size,
                      sha256=sha256_of(dest), file_name=dest.name)
        return result

    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, MAX_TRIES + 1):
        try:
            with requests.get(url, stream=True, timeout=timeout,
                              headers={"User-Agent": USER_AGENT}) as response:
                result["http_status"] = response.status_code
                if response.status_code != 200:
                    result["error"] = f"HTTP {response.status_code}"
                    if response.status_code in (429, 500, 502, 503, 504):
                        time.sleep(2 * attempt)
                        continue
                    return result
                disposition = response.headers.get("Content-Disposition", "")
                if "filename=" in disposition:
                    result["file_name"] = (disposition.split("filename=")[-1]
                                           .strip().strip('";'))
                with part.open("wb") as handle:
                    for block in response.iter_content(1 << 20):
                        if block:
                            handle.write(block)
            part.replace(dest)
            result.update(status="DOWNLOADED", size_bytes=dest.stat().st_size,
                          sha256=sha256_of(dest))
            if not result["file_name"]:
                result["file_name"] = dest.name
            return result
        except (requests.RequestException, OSError) as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            time.sleep(2 * attempt)
        finally:
            if part.exists() and not dest.exists():
                part.unlink(missing_ok=True)
    return result


def fit_download_url(fit_file_id: int) -> str:
    return f"{API_BASE}/api/v2/well_known_file_download/{int(fit_file_id)}"


def probe_reference(url: str) -> dict[str, Any]:
    """Ask for one byte, to prove a reference resolves without fetching it."""
    try:
        response = requests.get(url, timeout=HTTP_TIMEOUT,
                                headers={"User-Agent": USER_AGENT,
                                         "Range": "bytes=0-0"})
    except requests.RequestException as exc:
        return {"ok": False, "http_status": None,
                "error": f"{type(exc).__name__}: {exc}"}
    ok = response.status_code in (200, 206)
    return {"ok": ok, "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "error": None if ok else f"HTTP {response.status_code}"}


# ---------------------------------------------------------------------------
# Fit descriptor parsing
# ---------------------------------------------------------------------------
EXPECTED_TOP_LEVEL = ("passive", "fitting", "conditions", "genome")

#: Mechanism modules Allen's perisomatic template can load, from the AllenSDK
#: ``allensdk/test/model/peri_model/modfiles`` fixture.  A genome naming a
#: mechanism outside this set would need an extra compiled module, which is a
#: genuine execution blocker rather than a formatting difference.
KNOWN_PERISOMATIC_MECHANISMS = frozenset({
    "CaDynamics", "Ca_HVA", "Ca_LVA", "Ih", "Im", "Im_v2", "K_P", "K_T",
    "Kd", "Kv2like", "Kv3_1", "Nap", "NaTa", "NaTs", "NaV", "SK",
})


def infer_model_type(payload: dict[str, Any]) -> str:
    """Classify a descriptor by *schema*, not by the record that pointed at it.

    Perisomatic documents carry ``passive = [{ra, cm, e_pas}]`` and a genome of
    floats; all-active documents carry ``passive = [{ra}]`` and move Ra/cm/e_pas
    into a 42-entry genome whose values are JSON *strings*.  A document that
    matches neither is reported as UNKNOWN rather than forced into a class.

    Note: Allen's fit descriptors wrap passive in a list of length 1, not a plain
    dict.  Both ``passive`` as list and as dict are handled here.
    """
    passive_raw = payload.get("passive")
    genome = payload.get("genome")
    # Unwrap list-of-one convention used by Allen
    if isinstance(passive_raw, list) and len(passive_raw) == 1:
        passive = passive_raw[0]
    else:
        passive = passive_raw
    if not isinstance(passive, dict) or not isinstance(genome, list) or not genome:
        return "UNKNOWN"
    values = [entry.get("value") for entry in genome if isinstance(entry, dict)]
    all_str = bool(values) and all(isinstance(value, str) for value in values)
    all_num = bool(values) and all(isinstance(value, (int, float))
                                   and not isinstance(value, bool)
                                   for value in values)
    has_cm = "cm" in passive
    has_e_pas = "e_pas" in passive
    if has_cm and has_e_pas and all_num:
        return "perisomatic"
    if not has_cm and not has_e_pas and all_str:
        return "all_active"
    return "UNKNOWN"


def parse_fit_descriptor(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the fields the audit is allowed to claim, and what is missing.

    ``fitting_sweeps`` is the only source of fitting-condition truth used here.
    It is read from every ``fitting`` block and de-duplicated; if the key is
    absent the list is empty and no sweep number is invented from ``conditions``
    or from the protocol name.
    """
    top_keys = sorted(payload.keys())
    fitting_blocks = payload.get("fitting")
    if not isinstance(fitting_blocks, list):
        fitting_blocks = []
    sweeps: list[int] = []
    block_keys: set[str] = set()
    junction: Any = None
    for block in fitting_blocks:
        if not isinstance(block, dict):
            continue
        block_keys.update(block.keys())
        if junction is None and block.get("junction_potential") is not None:
            junction = block.get("junction_potential")
        for value in block.get("sweeps") or []:
            sweep_no = _int(value)
            if sweep_no is not None and sweep_no not in sweeps:
                sweeps.append(sweep_no)

    conditions = payload.get("conditions")
    conditions = conditions if isinstance(conditions, list) else []
    first = conditions[0] if conditions and isinstance(conditions[0], dict) else {}
    celsius_values = sorted({_float(block.get("celsius"))
                             for block in conditions
                             if isinstance(block, dict)
                             and _float(block.get("celsius")) is not None})
    v_init_values = sorted({_float(block.get("v_init"))
                            for block in conditions
                            if isinstance(block, dict)
                            and _float(block.get("v_init")) is not None})

    genome = payload.get("genome")
    genome = genome if isinstance(genome, list) else []
    mechanisms = sorted({_text(entry.get("mechanism")) for entry in genome
                         if isinstance(entry, dict) and _text(entry.get("mechanism"))})
    sections = sorted({_text(entry.get("section")) for entry in genome
                       if isinstance(entry, dict)})
    value_types = sorted({type(entry.get("value")).__name__ for entry in genome
                          if isinstance(entry, dict)})
    passive = payload.get("passive")
    # Unwrap list-of-one convention used by Allen fit descriptors
    if isinstance(passive, list) and len(passive) == 1:
        passive = passive[0]
    passive_keys = sorted(passive.keys()) if isinstance(passive, dict) else []

    missing = [key for key in EXPECTED_TOP_LEVEL if key not in payload]
    ambiguous: list[str] = []
    if "fitting" in payload and not sweeps:
        ambiguous.append("fitting present but no sweeps listed")
    if len(conditions) > 1 and len(celsius_values) > 1:
        ambiguous.append(f"{len(celsius_values)} distinct celsius values")
    if len(conditions) > 1 and len(v_init_values) > 1:
        ambiguous.append(f"{len(v_init_values)} distinct v_init values")
    if genome and any(not _text(entry.get("mechanism"))
                      for entry in genome if isinstance(entry, dict)):
        ambiguous.append("genome entries without a mechanism")
    if junction is None and "fitting" in payload:
        ambiguous.append("no junction_potential")

    return {
        "top_level_keys": top_keys,
        "model_type": infer_model_type(payload),
        "passive_keys": passive_keys,
        "genome_length": len(genome),
        "genome_value_types": value_types,
        "mechanisms": mechanisms,
        "sections": sections,
        "n_fitting_blocks": len(fitting_blocks),
        "fitting_block_keys": sorted(block_keys),
        "fitting_sweeps": sorted(sweeps),
        "conditions_keys": sorted(first.keys()),
        "celsius_c": celsius_values[0] if celsius_values else None,
        "v_init_mv": v_init_values[0] if v_init_values else None,
        "junction_potential_mv": _float(junction),
        "missing_fields": missing,
        "ambiguous_fields": ambiguous,
        "unknown_mechanisms": sorted(set(mechanisms)
                                     - KNOWN_PERISOMATIC_MECHANISMS),
    }


def build_fit_row(candidate: dict[str, Any], download: dict[str, Any],
                  payload: dict[str, Any] | None, api_model: dict[str, Any] | None,
                  api_file: dict[str, Any] | None,
                  sweep_by_number: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """One row of ``four_v1_fit_descriptor_audit.csv``.

    Every correspondence claim is a boolean with its evidence in the note, so a
    reader can tell "the descriptor parses" from "the descriptor belongs to this
    model and specimen".
    """
    row: dict[str, Any] = {
        "population": candidate["population"],
        "specimen_id": candidate["specimen_id"],
        "perisomatic_model_id": candidate["model_id"],
        "fit_file_id": candidate["fit_file_id"],
        "download_url": fit_download_url(candidate["fit_file_id"]),
        "download_status": download.get("status"),
        "http_status": download.get("http_status"),
        "file_name": download.get("file_name"),
        "size_bytes": download.get("size_bytes"),
        "sha256": download.get("sha256"),
        "parsed_ok": False,
        "note": "",
    }
    notes: list[str] = []
    if download.get("status") == "FAILED":
        row["note"] = f"download failed: {download.get('error')}"
        return row
    if payload is None:
        row["note"] = "descriptor bytes present but not parseable as JSON"
        return row

    parsed = parse_fit_descriptor(payload)
    row.update({
        "parsed_ok": True,
        "top_level_keys": parsed["top_level_keys"],
        "model_type": parsed["model_type"],
        "passive_keys": parsed["passive_keys"],
        "genome_length": parsed["genome_length"],
        "genome_value_types": parsed["genome_value_types"],
        "mechanisms": parsed["mechanisms"],
        "n_fitting_blocks": parsed["n_fitting_blocks"],
        "fitting_block_keys": parsed["fitting_block_keys"],
        "fitting_sweeps": parsed["fitting_sweeps"],
        "n_fitting_sweeps": len(parsed["fitting_sweeps"]),
        "conditions_keys": parsed["conditions_keys"],
        "junction_potential_mv": parsed["junction_potential_mv"],
        "celsius_c": parsed["celsius_c"],
        "v_init_mv": parsed["v_init_mv"],
        "missing_fields": parsed["missing_fields"],
        "ambiguous_fields": parsed["ambiguous_fields"],
    })

    # -- correspondence ------------------------------------------------------
    model_ok = api_model is not None
    file_ok = api_file is not None
    # The model record must name the selected specimen, the perisomatic template,
    # and the very reconstruction Phase 0B resolved for that model.  Whether that
    # reconstruction equals the specimen's own is level 5, not this check.
    matches_model = bool(
        model_ok
        and _int(api_model.get("specimen_id")) == candidate["specimen_id"]
        and _int(api_model.get("neuronal_model_template_id")) == candidate["template_id"]
        and _int(api_model.get("neuron_reconstruction_id"))
        == candidate["model_reconstruction_id"]
    )
    file_points_at_model = (
        file_ok
        and _int(api_file.get("attachable_id")) == candidate["model_id"]
        and _text(api_file.get("attachable_type")) == "NeuronalModel"
        and _int(api_file.get("well_known_file_type_id")) == WKFT_MODEL_PARAMETERS
    )
    row["descriptor_matches_model"] = bool(matches_model and file_points_at_model)
    row["descriptor_matches_specimen"] = bool(
        model_ok and _int(api_model.get("specimen_id")) == candidate["specimen_id"])
    if not model_ok:
        notes.append("model record not returned by RMA")
    if not file_ok:
        notes.append("well-known-file record not returned by RMA")
    if parsed["model_type"] != "perisomatic":
        notes.append(f"model type is {parsed['model_type']}, not perisomatic")
    if file_ok:
        notes.append(f"file path {_text(api_file.get('path'))}")
    if parsed["unknown_mechanisms"]:
        notes.append("mechanisms outside the supported set: "
                     + ",".join(parsed["unknown_mechanisms"]))

    # -- fitting sweep mapping ----------------------------------------------
    fitting = parsed["fitting_sweeps"]
    mapped = [number for number in fitting if number in sweep_by_number]
    unmapped = [number for number in fitting if number not in sweep_by_number]
    row["fitting_sweeps_mapped"] = bool(fitting) and not unmapped
    row["unmapped_fitting_sweeps"] = unmapped
    amps = sorted({round(float(sweep_by_number[number]["amplitude"]),
                         AMPLITUDE_DECIMALS)
                   for number in mapped
                   if sweep_by_number[number].get("amplitude") is not None})
    row["fitting_sweep_amplitudes"] = amps
    row["fitting_protocol_blocks"] = sorted({
        _text(sweep_by_number[number].get("stimulus_name"))
        for number in mapped})
    if fitting and unmapped:
        notes.append("fitting sweeps absent from the specimen sweep inventory: "
                     + ",".join(map(str, unmapped)))
    if not fitting:
        notes.append("no fitting sweep ids in the descriptor")

    row["note"] = "; ".join(notes)
    return row


# ---------------------------------------------------------------------------
# Held-out split planning
# ---------------------------------------------------------------------------
def heldout_plan(candidate: dict[str, Any], fit_row: dict[str, Any],
                 sweeps: list[dict[str, Any]]) -> dict[str, Any]:
    """Decide whether a leakage-free calibration/held-out split exists.

    The rule is deliberately stricter than "the sweep number is not a fitting
    sweep".  A held-out sweep that repeats a *fitted amplitude* tests nothing new
    about amplitude generalisation, so it is reported as sweep-level-only rather
    than counted as an independent condition.  Only amplitudes never used in the
    fit count towards the two-condition requirement.
    """
    cc = [sweep for sweep in sweeps
          if units_aware_current_clamp(sweep.get("clamp_mode", ""),
                                       sweep.get("stimulus_units", ""))]
    by_number: dict[int, dict[str, Any]] = {}
    for sweep in cc:
        number = sweep.get("sweep_number")
        if number is not None:
            by_number.setdefault(number, sweep)

    depolarising = [sweep for sweep in cc
                    if (sweep.get("amplitude") or 0) > 0]
    fitting = [int(number) for number in (fit_row.get("fitting_sweeps") or [])]
    fitting_set = set(fitting)
    unmapped = [number for number in fitting if number not in by_number]

    fitting_dep = [by_number[number] for number in fitting
                   if number in by_number
                   and (by_number[number].get("amplitude") or 0) > 0]
    fitting_amps = sorted({round(float(sweep["amplitude"]), AMPLITUDE_DECIMALS)
                           for sweep in fitting_dep})
    fitting_blocks = sorted({_text(sweep.get("stimulus_name"))
                             for sweep in fitting_dep})

    heldout = [sweep for sweep in depolarising
               if sweep.get("sweep_number") not in fitting_set]
    heldout_amps = sorted({round(float(sweep["amplitude"]), AMPLITUDE_DECIMALS)
                           for sweep in heldout})
    independent = [amp for amp in heldout_amps if amp not in set(fitting_amps)]
    counts = Counter(round(float(sweep["amplitude"]), AMPLITUDE_DECIMALS)
                     for sweep in heldout)
    repeated = sorted(amp for amp, count in counts.items() if count >= 2)
    heldout_blocks = sorted({_text(sweep.get("stimulus_name")) for sweep in heldout})
    heldout_families = {protocol_family(block) for block in heldout_blocks}
    fitting_families = {protocol_family(block) for block in fitting_blocks}
    family_split = sorted(heldout_families - fitting_families)

    descriptor_ok = bool(fit_row.get("parsed_ok"))
    if not descriptor_ok:
        status = "UNRESOLVED_DESCRIPTOR_UNAVAILABLE"
        reason = "fit descriptor was not downloaded and parsed"
    elif not fitting:
        status = "UNRESOLVED_NO_FITTING_SWEEPS"
        reason = ("the descriptor lists no fitting sweeps, so the fitted "
                  "conditions cannot be excluded")
    elif unmapped:
        status = "UNRESOLVED_FITTING_SWEEP_UNMAPPED"
        reason = ("fitting sweeps not found in the specimen sweep inventory: "
                  + ",".join(map(str, unmapped)))
    elif len(independent) >= 2:
        status = "RESOLVED_LEAKAGE_SAFE"
        reason = (f"{len(independent)} depolarising amplitudes remain that the "
                  f"fit never saw: {independent}")
    elif len(independent) == 1:
        status = "RESOLVED_SWEEP_LEVEL_ONLY"
        reason = ("only one depolarising amplitude remains unseen by the fit; "
                  "held-out sweeps would repeat fitted conditions")
    else:
        status = "UNRESOLVED_INSUFFICIENT"
        reason = ("every remaining depolarising sweep repeats an amplitude the "
                  "fit consumed")

    if family_split:
        proposed = ("PROTOCOL_FAMILY=" + "/".join(family_split)
                    + f" ({len(heldout)} sweeps, {len(heldout_amps)} amplitudes)")
    elif independent:
        proposed = "AMPLITUDE=" + "/".join(str(amp) for amp in independent[:2])
    else:
        proposed = "NONE"
    calibration = ("PROTOCOL_FAMILY=" + "/".join(sorted(fitting_families))
                   if fitting_blocks else "UNKNOWN")

    if status == "RESOLVED_LEAKAGE_SAFE" and candidate.get("nwb_validated"):
        frozen = "FROZEN"
    elif status == "RESOLVED_LEAKAGE_SAFE":
        frozen = "PROVISIONAL"
    else:
        frozen = "PROPOSED"

    return {
        "population": candidate["population"],
        "specimen_id": candidate["specimen_id"],
        "fit_file_id": candidate["fit_file_id"],
        "heldout_status": status,
        "fitting_sweeps": fitting,
        "n_fitting_sweeps": len(fitting),
        "n_fitting_depolarizing": len(fitting_dep),
        "fitting_amplitudes_pa": fitting_amps,
        "fitting_protocol_blocks": fitting_blocks,
        "n_heldout_depolarizing_sweeps": len(heldout),
        "n_heldout_distinct_amplitudes": len(heldout_amps),
        "heldout_amplitudes_pa": heldout_amps,
        "n_heldout_repeated_amplitudes": len(repeated),
        "heldout_protocol_blocks": heldout_blocks,
        "family_split_available": bool(family_split),
        "proposed_calibration_condition": calibration,
        "proposed_heldout_condition": proposed,
        "leakage_safe": status == "RESOLVED_LEAKAGE_SAFE",
        "split_frozen": frozen,
        "reason": reason,
    }

# ---------------------------------------------------------------------------
# Recording validation
# ---------------------------------------------------------------------------
def build_recording_row(candidate: dict[str, Any], sweep_summary: dict[str, Any],
                        nwb_record: dict[str, Any] | None, role: str,
                        nwb_cached: bool) -> dict[str, Any]:
    """One row of ``four_v1_recording_validation.csv``.

    Inventory columns are filled for all sixteen candidates; NWB columns stay
    explicitly ``NOT_INSPECTED`` for the twelve that were not opened, so an empty
    cell can never be read as a pass.
    """
    row: dict[str, Any] = {
        "population": candidate["population"],
        "specimen_id": candidate["specimen_id"],
        "ephys_result_id": candidate["ephys_result_id"],
        "nwb_file_id": candidate["nwb_file_id"],
        "nwb_reference": candidate["nwb_download_url"],
        "nwb_cached": nwb_cached,
        "sampling_rate_hz": candidate["sampling_rate_hz"],
        "n_long_square_rows": sweep_summary.get("n_long_square_rows"),
        "n_long_square_cc": sweep_summary.get("n_long_square_cc"),
        "n_depolarizing_sweeps": sweep_summary.get("n_depolarizing"),
        "n_distinct_depolarizing_amplitudes": sweep_summary.get(
            "n_distinct_depolarizing"),
        "n_repeated_depolarizing_amplitudes": sweep_summary.get(
            "n_repeated_depolarizing"),
        "depolarizing_min_pa": sweep_summary.get("depolarizing_min_pa"),
        "depolarizing_max_pa": sweep_summary.get("depolarizing_max_pa"),
        "protocol_families": sorted(sweep_summary.get("families", {})),
        "protocol_blocks": sorted(sweep_summary.get("blocks", {})),
        "n_coarse_sweeps": sweep_summary.get("families", {}).get("COARSE", 0),
        "n_finest_sweeps": sweep_summary.get("families", {}).get("FINEST", 0),
        "n_c2_sweeps": sweep_summary.get("families", {}).get("C2", 0),
        "is_representative": role,
        "nwb_verdict": "NOT_INSPECTED",
        "note": "",
    }
    notes: list[str] = []
    if sweep_summary.get("n_long_square_cc", 0) < MIN_LONG_SQUARE:
        notes.append(f"only {sweep_summary.get('n_long_square_cc')} long-square "
                     f"current-clamp sweeps (< {MIN_LONG_SQUARE})")
    if sweep_summary.get("n_distinct_depolarizing", 0) < PREFERRED_MIN_DISTINCT:
        notes.append("fewer than five distinct depolarising amplitudes")
    if (candidate["sampling_rate_hz"] or 0) < PREFERRED_RATE_HZ:
        notes.append("sampling rate below 200 kHz")
    if sweep_summary.get("families", {}).get("C2"):
        notes.append("C2 protocol sweeps present; treat as a separate protocol")
    if nwb_record is None:
        row["note"] = "; ".join(notes)
        return row
    if nwb_record.get("verdict") == "UNRESOLVED":
        row["nwb_verdict"] = "UNRESOLVED"
        notes.append(str(nwb_record.get("reason")))
        row["note"] = "; ".join(notes)
        return row

    sweeps = nwb_record.get("sweeps") or []
    coverage = nwb_record.get("coverage") or {}
    file_info = nwb_record.get("file") or {}
    identity = nwb_record.get("identity_chain") or {}
    declared = identity.get("/general/aibs_specimen_id")
    identity_ok = _text(declared) == str(candidate["specimen_id"])
    verdicts = Counter(sweep.get("verdict") for sweep in sweeps)
    rates = sorted({round(float(sweep.get("rate_hz")), 3) for sweep in sweeps
                    if sweep.get("rate_hz")})
    onsets = sorted({round(float((sweep.get("trace") or {}).get("onset_s")), 4)
                     for sweep in sweeps
                     if (sweep.get("trace") or {}).get("onset_s") is not None})
    durations = sorted({round(float((sweep.get("trace") or {}).get("level_ms")), 3)
                        for sweep in sweeps
                        if (sweep.get("trace") or {}).get("level_ms") is not None})
    embedded = sum(1 for sweep in sweeps
                   if (sweep.get("trace") or {}).get("extra_runs"))

    row.update({
        "nwb_verdict": nwb_record.get("verdict"),
        "nwb_identity_match": identity_ok,
        "nwb_n_stimulus_series": (nwb_record.get("nwb") or {}).get(
            "n_stimulus_series"),
        "nwb_n_long_square_series": coverage.get("nwb_long_square_series"),
        "nwb_matched_by_sweep_number": coverage.get("matched_by_sweep_number"),
        "nwb_inventory_only_count": len(coverage.get("inventory_only") or []),
        "nwb_conversion_counts": [f"{key}={value}"
                                  for key, value in sorted(verdicts.items())],
        "nwb_embedded_probe_sweeps": embedded,
        "nwb_step_onset_s": onsets,
        "nwb_step_duration_ms": durations,
        "nwb_sampling_rate_hz": rates,
        "nwb_file_size_bytes": file_info.get("size_bytes"),
        "nwb_sha256": file_info.get("sha256"),
    })
    if not identity_ok:
        notes.append(f"NWB names specimen {declared}, not {candidate['specimen_id']}")
    if coverage.get("inventory_only"):
        notes.append("inventory sweeps absent from the NWB: "
                     + ",".join(map(str, coverage["inventory_only"])))
    if verdicts.get("MISMATCH") or verdicts.get("MISMATCH_SCALE"):
        notes.append("raw stimulus does not reproduce the inventory amplitude")
    if verdicts.get("MATCH_CONVERSION_CONFLICT"):
        notes.append("declared conversion contradicts the file's own samples; "
                     "unit-only reading matches the inventory")
    row["note"] = "; ".join(notes)
    return row


def run_nwb_validator(specimen_ids: Sequence[int], cache_dir: Path,
                      json_out: Path) -> tuple[dict[int, dict[str, Any]], str]:
    """Delegate to the validated units-aware validator, then read its JSON.

    The validator returns 2 when any verdict is not a clean MATCH; that is data,
    not a crash, so the exit code is recorded rather than raised.
    """
    json_out.parent.mkdir(parents=True, exist_ok=True)
    if json_out.exists():
        json_out.unlink()
    command = [sys.executable, str(VALIDATOR)]
    for specimen_id in specimen_ids:
        command += ["--specimen", str(specimen_id)]
    command += ["--repo-root", str(PROJECT_ROOT), "--cache-dir", str(cache_dir),
                "--json-out", str(json_out)]
    completed = subprocess.run(command, capture_output=True, text=True,
                               cwd=str(PROJECT_ROOT), check=False)
    if not json_out.exists():
        tail = (completed.stderr or completed.stdout or "").strip().splitlines()
        return {}, f"validator produced no JSON (exit {completed.returncode}): " \
                   f"{tail[-1] if tail else 'no output'}"
    records = json.loads(json_out.read_text(encoding="utf-8"))
    return ({int(record["specimen_id"]): record for record in records},
            f"validator exit {completed.returncode}")


# ---------------------------------------------------------------------------
# Model asset readiness
# ---------------------------------------------------------------------------
def modfile_support(mechanisms: Sequence[str]) -> dict[str, Any]:
    """Check the genome's mechanisms against the locally cached .mod sources.

    Allen publishes no per-model archive: execution needs the fit JSON, a
    ``manifest.json`` that AllenSDK ships as a fixture, and the mechanism
    sources.  Whether those are present *here* is a separate question from
    whether Allen lists the model, which is the whole point of level 4.
    """
    candidates = [
        PROJECT_ROOT / "tmp" / "model_cache" / "allensdk" / "modfiles",
        PROJECT_ROOT / "data" / "model_cache" / "allensdk" / "modfiles",
    ]
    manifests = [
        PROJECT_ROOT / "tmp" / "model_cache" / "allensdk" / "reference"
        / "manifest_perisomatic.json",
        PROJECT_ROOT / "data" / "model_cache" / "allensdk" / "reference"
        / "manifest_perisomatic.json",
    ]
    mod_dir = next((path for path in candidates if path.is_dir()), None)
    manifest = next((path for path in manifests if path.is_file()), None)
    provided = (sorted(path.stem for path in mod_dir.glob("*.mod"))
                if mod_dir else [])
    needed = set(mechanisms)
    missing = sorted(needed - set(provided)) if provided else sorted(needed)
    return {
        "mod_dir": str(mod_dir) if mod_dir else None,
        "manifest": str(manifest) if manifest else None,
        "provided": provided,
        "missing": missing,
        "complete": bool(mod_dir and manifest and provided and not missing),
    }


def build_asset_row(candidate: dict[str, Any], fit_row: dict[str, Any],
                    morphology: dict[str, Any],
                    support: dict[str, Any]) -> dict[str, Any]:
    """One row of ``four_v1_model_asset_readiness.csv``, level by level."""
    blockers: list[str] = []
    notes: list[str] = []

    l1 = "YES"
    l2 = "YES" if (fit_row.get("parsed_ok")
                   and fit_row.get("download_status") in ("DOWNLOADED", "CACHED")) else "NO"
    if l2 == "NO":
        blockers.append(f"fit descriptor {fit_row.get('download_status')}")

    l3 = morphology.get("level", "UNAVAILABLE")
    if l3 == "UNAVAILABLE":
        blockers.append("morphology asset not retrievable")

    if not support.get("complete"):
        if support.get("missing"):
            blockers.append("mechanism sources missing: "
                            + ",".join(support["missing"]))
        elif not support.get("mod_dir"):
            blockers.append("no local mechanism sources to check against")
        else:
            blockers.append("no manifest.json available")
        l4 = "NO"
    else:
        l4 = "YES"

    l5 = "YES" if candidate["reconstruction_match"] else "NO"
    if l5 == "NO":
        blockers.append(f"model reconstruction {candidate['model_reconstruction_id']} "
                        f"!= specimen reconstruction "
                        f"{candidate['specimen_reconstruction_id']}")

    l6 = "YES" if fit_row.get("fitting_sweeps_mapped") else "NO"
    if l6 == "NO":
        if fit_row.get("fitting_sweeps"):
            blockers.append("fitting sweeps do not map to the inventory")
        else:
            blockers.append("no fitting sweep ids in the descriptor")

    executable = all(level == "YES" for level in (l2, l4, l6)) and \
        l3 in ("VERIFIED", "REFERENCE_RESOLVED")

    executed = "NOT_EXECUTED"
    if candidate["specimen_id"] == 382982932:
        executed = "EXECUTED_NOT_VALIDATED"
        notes.append("Phase 2C executed the perisomatic model; Phase 2E found the "
                     "held-out prediction mismatched, so this is execution "
                     "evidence, not reproduction evidence")
    notes.append(f"levels: L1={l1} L2={l2} L3={l3} L4={l4} L5={l5} L6={l6}")

    return {
        "population": candidate["population"],
        "specimen_id": candidate["specimen_id"],
        "perisomatic_model_id": candidate["model_id"],
        "template_id": candidate["template_id"],
        "fit_file_id": candidate["fit_file_id"],
        "is_representative": candidate.get("nwb_role", "NOT_SELECTED"),
        "L1_listed_in_metadata": l1,
        "L2_fit_descriptor_downloaded_and_parsed": l2,
        "L3_morphology_asset_available": l3,
        "L4_model_archive_or_mechanisms_available": l4,
        "L5_model_reconstruction_matches_specimen": l5,
        "L6_fitting_sweeps_identifiable": l6,
        "L7_potentially_executable": "YES" if executable else "NO",
        "L8_actually_executed_and_validated": executed,
        "morphology_evidence": morphology.get("evidence", ""),
        "mechanism_evidence": (f"{len(support.get('provided') or [])} .mod files; "
                               f"manifest={'present' if support.get('manifest') else 'absent'}"),
        "blockers": blockers,
        "note": "; ".join(notes),
    }


# ---------------------------------------------------------------------------
# Aggregation and self-checks
# ---------------------------------------------------------------------------
def population_summary(pools: Sequence[dict[str, Any]],
                       candidate_list: Sequence[dict[str, Any]],
                       fit_rows: dict[int, dict[str, Any]],
                       heldout_rows: dict[int, dict[str, Any]],
                       asset_rows: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for pool in pools:
        key = pool["population"]
        members = [item for item in candidate_list if item["population"] == key]
        out.append({
            "population": key,
            "label": pool["population_label"],
            "available": pool["available"],
            "selected": pool["selected"],
            "shortfall": pool["shortfall"],
            "primary_tier": sum(1 for item in members
                                if item["selection_tier"] == "PRIMARY"),
            "descriptor_ok": sum(1 for item in members
                                 if fit_rows[item["specimen_id"]].get("parsed_ok")),
            "fitting_sweeps_identified": sum(
                1 for item in members
                if fit_rows[item["specimen_id"]].get("fitting_sweeps_mapped")),
            "leakage_safe": sum(
                1 for item in members
                if heldout_rows[item["specimen_id"]]["leakage_safe"]),
            "assets_verified": sum(
                1 for item in members
                if asset_rows[item["specimen_id"]]["L7_potentially_executable"] == "YES"),
            "executed": sum(
                1 for item in members
                if asset_rows[item["specimen_id"]]["L8_actually_executed_and_validated"]
                != "NOT_EXECUTED"),
        })
    return out


def self_checks(candidate_list: Sequence[dict[str, Any]],
                api_models: dict[int, dict[str, Any]],
                fit_rows: dict[int, dict[str, Any]],
                heldout_rows: dict[int, dict[str, Any]],
                asset_rows: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    """The checks the brief asks for, evaluated on the artefacts just built."""
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    counts = Counter(item["population"] for item in candidate_list)
    add("four_candidates_per_population",
        all(counts.get(pop["key"], 0) == TARGET_PER_POPULATION
            for pop in POPULATIONS),
        ", ".join(f"{pop['key']}={counts.get(pop['key'], 0)}" for pop in POPULATIONS))

    ids = [item["specimen_id"] for item in candidate_list]
    add("no_duplicate_specimens", len(ids) == len(set(ids)),
        f"{len(ids)} specimens, {len(set(ids))} unique")

    wrong = []
    for item in candidate_list:
        record = api_models.get(item["model_id"])
        if record is None or _int(record.get("specimen_id")) != item["specimen_id"]:
            wrong.append(item["specimen_id"])
    add("model_ids_map_to_correct_specimens", not wrong,
        "all match" if not wrong else f"mismatched: {wrong}")

    bad_fit = [item["specimen_id"] for item in candidate_list
               if not fit_rows[item["specimen_id"]].get("descriptor_matches_model")]
    add("fit_descriptors_map_to_correct_models", not bad_fit,
        "all match" if not bad_fit else f"unmatched: {bad_fit}")

    leaking = []
    for item in candidate_list:
        plan = heldout_rows[item["specimen_id"]]
        if set(plan["fitting_sweeps"]) & set(plan.get("heldout_sweeps", [])):
            leaking.append(item["specimen_id"])
    add("fitting_sweeps_excluded_from_heldout", not leaking,
        "no overlap" if not leaking else f"overlap: {leaking}")

    no_fit = [item["specimen_id"] for item in candidate_list
              if not fit_rows[item["specimen_id"]].get("fitting_sweeps")]
    marked = [sid for sid in no_fit
              if heldout_rows[sid]["heldout_status"].startswith("UNRESOLVED")]
    add("missing_fitting_metadata_marked_unresolved",
        len(no_fit) == len(marked),
        f"{len(no_fit)} candidates without fitting sweeps, {len(marked)} unresolved")

    failed_downloads = [item["specimen_id"] for item in candidate_list
                        if fit_rows[item["specimen_id"]].get("download_status") == "FAILED"]
    counted = [sid for sid in failed_downloads
               if fit_rows[sid].get("parsed_ok")
               or asset_rows[sid]["L2_fit_descriptor_downloaded_and_parsed"] == "YES"]
    add("failed_downloads_not_counted_as_assets", not counted,
        f"{len(failed_downloads)} failures, {len(counted)} counted as available")

    return checks


def print_tables(summary: Sequence[dict[str, Any]],
                 heldout_rows: dict[int, dict[str, Any]],
                 asset_rows: dict[int, dict[str, Any]],
                 checks: Sequence[dict[str, Any]]) -> None:
    print()
    print("=" * 78)
    print("SELECTED POPULATIONS")
    print("%-4s %-34s %8s %8s %8s" % ("pop", "label", "avail", "sel", "primary"))
    for row in summary:
        print("%-4s %-34s %8d %8d %8d" % (row["population"], row["label"][:34],
                                          row["available"], row["selected"],
                                          row["primary_tier"]))
    print()
    print("READINESS BY POPULATION")
    print("%-4s %10s %10s %10s %12s %10s" % ("pop", "descriptor", "fit_sweeps",
                                             "heldout", "assets", "executed"))
    for row in summary:
        print("%-4s %10d %10d %10d %12d %10d" % (
            row["population"], row["descriptor_ok"],
            row["fitting_sweeps_identified"], row["leakage_safe"],
            row["assets_verified"], row["executed"]))
    print()
    print("HELD-OUT STATUS")
    for status, count in sorted(Counter(
            row["heldout_status"] for row in heldout_rows.values()).items()):
        print("  %-38s %d" % (status, count))
    print()
    print("ASSET LEVELS")
    for level, key in EVIDENCE_LEVELS:
        values = Counter(row[key] for row in asset_rows.values())
        print("  %-4s %-46s %s" % (level, key,
                                   ", ".join(f"{k}={v}" for k, v in sorted(values.items()))))
    print()
    print("SELF-CHECKS")
    for check in checks:
        print("  %-4s %-46s %s" % ("ok" if check["ok"] else "FAIL",
                                   check["check"], check["detail"]))
    failed = [check for check in checks if not check["ok"]]
    print("\n%d/%d checks passed" % (len(checks) - len(failed), len(checks)))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--fit-cache", type=Path, default=FIT_CACHE)
    parser.add_argument("--nwb-cache", type=Path, default=NWB_CACHE)
    parser.add_argument("--api-cache", type=Path,
                        default=PROJECT_ROOT / "tmp" / "p0c_api_cache")
    parser.add_argument("--no-download", action="store_true",
                        help="use only what is already cached")
    parser.add_argument("--refresh-fit", action="store_true",
                        help="re-download fit descriptors even if cached")
    parser.add_argument("--no-nwb", action="store_true",
                        help="skip NWB inspection entirely")
    parser.add_argument("--evidence-out", type=Path, default=None,
                        help="write raw per-candidate evidence JSON (keep out of Git)")
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.fit_cache.mkdir(parents=True, exist_ok=True)

    rows = read_rows(PHASE0B_CANDIDATES)
    selected, pools = select_candidates(rows)
    sweeps_by_specimen = load_sweeps()

    client = RmaClient(args.api_cache)
    api_models = client.rows_by_id("model::NeuronalModel",
                                   [item["model_id"] for item in selected])
    api_files = fetch_well_known_files(client, [item["fit_file_id"]
                                                for item in selected])
    morph_ids = [item["morphology_file_id"] for item in selected
                 if item["morphology_file_id"]]
    api_morph = fetch_well_known_files(client, morph_ids)

    # -- fit descriptors ----------------------------------------------------
    fit_rows: dict[int, dict[str, Any]] = {}
    for item in selected:
        destination = args.fit_cache / f"{item['fit_file_id']}.json"
        if args.no_download and not destination.exists():
            download = {"status": "FAILED", "error": "not cached and --no-download",
                        "http_status": None, "size_bytes": None, "sha256": None,
                        "file_name": None}
        else:
            download = download_to(fit_download_url(item["fit_file_id"]),
                                   destination, refresh=args.refresh_fit)
        payload = None
        if download["status"] != "FAILED" and destination.exists():
            try:
                payload = json.loads(destination.read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                download = dict(download)
                download["status"] = "FAILED"
                download["error"] = f"unparseable JSON: {exc}"
                payload = None
        by_number = {sweep["sweep_number"]: sweep
                     for sweep in sweeps_by_specimen.get(item["specimen_id"], [])
                     if sweep.get("sweep_number") is not None}
        fit_rows[item["specimen_id"]] = build_fit_row(
            item, download, payload, api_models.get(item["model_id"]),
            api_files.get(item["fit_file_id"]), by_number)

    # -- representatives ----------------------------------------------------
    representatives: dict[str, dict[str, Any]] = {}
    for pop in POPULATIONS:
        members = [item for item in selected if item["population"] == pop["key"]]
        if members:
            representatives[pop["key"]] = members[0]
    for item in selected:
        item["nwb_role"] = "NOT_SELECTED"
    for key, item in representatives.items():
        item["nwb_role"] = "REPRESENTATIVE"
    # A selected specimen whose NWB is already cached costs nothing to add and
    # strengthens the campaign-level claim, so it is validated too.
    extra: list[dict[str, Any]] = []
    if not args.no_nwb:
        for item in selected:
            if item["nwb_role"] != "NOT_SELECTED":
                continue
            if (args.nwb_cache / f"{item['specimen_id']}.nwb").exists():
                item["nwb_role"] = "SUPPLEMENTARY_CACHED"
                extra.append(item)

    # -- NWB acquisition and validation -------------------------------------
    nwb_records: dict[int, dict[str, Any]] = {}
    nwb_status = "skipped (--no-nwb)"
    if not args.no_nwb:
        targets = list(representatives.values()) + extra
        for item in targets:
            destination = args.nwb_cache / f"{item['specimen_id']}.nwb"
            if destination.exists():
                continue
            if args.no_download:
                continue
            result = download_to(item["nwb_download_url"], destination)
            print(f"NWB {item['specimen_id']}: {result['status']} "
                  f"{result.get('size_bytes')} bytes")
            if result["status"] == "FAILED":
                print(f"  error: {result.get('error')}")
        present = [item["specimen_id"] for item in targets
                   if (args.nwb_cache / f"{item['specimen_id']}.nwb").exists()]
        if present:
            nwb_records, nwb_status = run_nwb_validator(
                present, args.nwb_cache, PROJECT_ROOT / "tmp" / "p0c_nwb_validation.json")

    # -- morphology for representatives -------------------------------------
    morphology: dict[int, dict[str, Any]] = {}
    for item in selected:
        url = item["morphology_download_url"]
        if not url:
            morphology[item["specimen_id"]] = {"level": "UNAVAILABLE",
                                               "evidence": "no reference"}
            continue
        reference = probe_reference(url)
        if not reference["ok"]:
            morphology[item["specimen_id"]] = {
                "level": "UNAVAILABLE",
                "evidence": f"reference probe failed: {reference['error']}"}
            continue
        if item["nwb_role"] in ("REPRESENTATIVE", "SUPPLEMENTARY_CACHED") \
                and not args.no_download:
            destination = MORPHOLOGY_CACHE / f"{item['specimen_id']}.swc"
            fetched = download_to(url, destination)
            if fetched["status"] in ("DOWNLOADED", "CACHED"):
                morphology[item["specimen_id"]] = {
                    "level": "VERIFIED",
                    "evidence": f"{fetched['size_bytes']} bytes, sha256 "
                                f"{str(fetched['sha256'])[:16]}..., "
                                f"path {destination.relative_to(PROJECT_ROOT)}"}
                continue
        morphology[item["specimen_id"]] = {
            "level": "REFERENCE_RESOLVED",
            "evidence": f"HTTP {reference['http_status']} on a one-byte range "
                        f"request; asset not downloaded"}

    # -- held-out plans and asset rows --------------------------------------
    for item in selected:
        record = nwb_records.get(item["specimen_id"])
        item["nwb_validated"] = bool(record and record.get("verdict") not in
                                     (None, "UNRESOLVED"))
    heldout_rows: dict[int, dict[str, Any]] = {}
    for item in selected:
        heldout_rows[item["specimen_id"]] = heldout_plan(
            item, fit_rows[item["specimen_id"]],
            sweeps_by_specimen.get(item["specimen_id"], []))

    support = modfile_support(sorted({mechanism
                                      for item in selected
                                      for mechanism in
                                      (fit_rows[item["specimen_id"]].get("mechanisms")
                                       or [])}))
    asset_rows: dict[int, dict[str, Any]] = {}
    for item in selected:
        asset_rows[item["specimen_id"]] = build_asset_row(
            item, fit_rows[item["specimen_id"]],
            morphology[item["specimen_id"]], support)

    # -- held-out sweep members (for the exclusion self-check) --------------
    for item in selected:
        plan = heldout_rows[item["specimen_id"]]
        fitting = set(plan["fitting_sweeps"])
        plan["heldout_sweeps"] = [
            sweep["sweep_number"]
            for sweep in sweeps_by_specimen.get(item["specimen_id"], [])
            if sweep.get("sweep_number") is not None
            and sweep["sweep_number"] not in fitting
            and units_aware_current_clamp(sweep.get("clamp_mode", ""),
                                          sweep.get("stimulus_units", ""))
            and (sweep.get("amplitude") or 0) > 0]

    # -- recording rows -----------------------------------------------------
    recording_rows = []
    for item in selected:
        sweep_summary = summarise_sweeps(
            sweeps_by_specimen.get(item["specimen_id"], []))
        recording_rows.append(build_recording_row(
            item, sweep_summary, nwb_records.get(item["specimen_id"]),
            item["nwb_role"],
            (args.nwb_cache / f"{item['specimen_id']}.nwb").exists()))

    # -- write artefacts ----------------------------------------------------
    candidate_csv = args.out_dir / "four_v1_selected_candidates.csv"
    fit_csv = args.out_dir / "four_v1_fit_descriptor_audit.csv"
    recording_csv = args.out_dir / "four_v1_recording_validation.csv"
    asset_csv = args.out_dir / "four_v1_model_asset_readiness.csv"
    heldout_csv = args.out_dir / "four_v1_heldout_feasibility.csv"

    n_candidates = write_rows(candidate_csv, CANDIDATE_COLUMNS,
                              candidate_rows(selected))
    n_fit = write_rows(fit_csv, FIT_COLUMNS,
                       [fit_rows[item["specimen_id"]] for item in selected])
    n_recording = write_rows(recording_csv, RECORDING_COLUMNS, recording_rows)
    n_assets = write_rows(asset_csv, ASSET_COLUMNS,
                          [asset_rows[item["specimen_id"]] for item in selected])
    n_heldout = write_rows(heldout_csv, HELDOUT_COLUMNS,
                           [heldout_rows[item["specimen_id"]] for item in selected])

    summary = population_summary(pools, selected, fit_rows, heldout_rows, asset_rows)
    checks = self_checks(selected, api_models, fit_rows, heldout_rows, asset_rows)
    print_tables(summary, heldout_rows, asset_rows, checks)
    print()
    print("wrote %s (%d rows)" % (candidate_csv.name, n_candidates))
    print("wrote %s (%d rows)" % (fit_csv.name, n_fit))
    print("wrote %s (%d rows)" % (recording_csv.name, n_recording))
    print("wrote %s (%d rows)" % (asset_csv.name, n_assets))
    print("wrote %s (%d rows)" % (heldout_csv.name, n_heldout))
    print("NWB validation: %s" % nwb_status)
    print("RMA requests: %d (%d cache hits), %d error(s)"
          % (client.requests, client.cache_hits, len(client.errors)))
    for error in client.errors:
        print("  ! %s" % error)

    if args.evidence_out:
        evidence = {
            "phase": PHASE,
            "pools": pools,
            "summary": summary,
            "nwb_validation_status": nwb_status,
            "self_checks": checks,
            "candidates": [
                {
                    "population": item["population"],
                    "specimen_id": item["specimen_id"],
                    "nwb_role": item["nwb_role"],
                    "selection_tier": item["selection_tier"],
                    "fit_descriptor": {key: value for key, value in
                                       fit_rows[item["specimen_id"]].items()
                                       if key not in ("sha256",)},
                    "heldout": heldout_rows[item["specimen_id"]],
                    "assets": asset_rows[item["specimen_id"]],
                    "morphology": morphology[item["specimen_id"]],
                }
                for item in selected],
            "nwb_records": {str(key): value for key, value in nwb_records.items()},
            "mechanisms": support,
        }
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_out.write_text(json.dumps(evidence, indent=2, default=str),
                                     encoding="utf-8")
        print("evidence written to %s" % args.evidence_out)

    failed = [check for check in checks if not check["ok"]]
    if failed:
        return 1
    missing_nwb = [item["specimen_id"] for item in selected
                   if item["nwb_role"] != "NOT_SELECTED"
                   and item["specimen_id"] not in nwb_records]
    return 2 if missing_nwb else 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

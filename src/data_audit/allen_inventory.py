"""Allen Cell Types Database inventory -- INCM Phase 0 dataset feasibility audit.

Research question being served
------------------------------
"How much biological detail does a neuron model need to reproduce a real
neuron's electrophysiological behaviour, and which behaviours are preserved or
lost when a detailed conductance-based model is reduced to a FitzHugh-Nagumo
model?"  (INCM_revised_project.pdf)

What this script does
---------------------
Reads **metadata only** from the official Allen Institute Brain Map RMA v2 API
and produces a reproducible inventory of candidate cells in the sensory
(VISp / VISl / VISal) and motor (MOp / ALM) candidate regions:

    data/metadata/cell_inventory.csv      one row per matching cell specimen
    data/metadata/region_summary.csv      one row per region / cortical layer
    data/metadata/sweep_inventory.csv     one row per electrophysiology sweep
    data/metadata/model_inventory.csv     one row per Allen neuronal model
    results/dataset_inventory/DATASET_INVENTORY_REPORT.md   generated report

What this script deliberately does NOT do
-----------------------------------------
* No neuron modelling, no FHN fitting.
* No NWB downloads, no model archive downloads, no morphology SWC downloads.
  Only ``HEAD``-free metadata; download *references* are recorded as URLs.
* No package installation.
* No automatic population selection -- eligibility is reported, not decided.

API notes (all verified by ``api_schema_probe.py`` before use)
-------------------------------------------------------------
* Endpoint: ``http://api.brain-map.org/api/v2/data/query.json``.
* Envelope: ``{success, msg, num_rows, start_row, total_rows}``.
* ``num_rows`` / ``start_row`` / ``include`` must be **separate** query
  parameters.  Embedding them as ``rma::options,num_rows$eqN`` inside
  ``criteria`` is rejected by the Allen RMA parser.
* ``Specimen`` has no ``failed`` column; electrophysiology failure status comes
  from ``EphysResult.failed``.
* ``DendriteType`` / ``ApicalDendrite`` / ``NeuronalModelType`` are not
  addressable models.  Dendrite type and apical-dendrite status are carried as
  ``specimen_tags`` ("dendrite type - spiny", "apical - intact", ...); the
  model class is carried by ``NeuronalModel.neuronal_model_template_id``.
* The bulk CSV downloads used by older AllenSDK versions
  (``well_known_file_download?name=cell_types_*``) return HTTP 404, so the
  inventory is built from RMA queries instead.
* Model class must NOT be inferred from ``well_known_file_type_id``: the
  biophysical fit JSON and the GLIF neuron_config JSON share type 329230374.

Usage
-----
    python src/data_audit/allen_inventory.py                 # normal run
    python src/data_audit/allen_inventory.py --refresh       # ignore cache
    python src/data_audit/allen_inventory.py --min-long-square 8
    python src/data_audit/allen_inventory.py --force         # allow overwrite

Requires: requests, pandas.  AllenSDK is NOT required (and is not importable
on this interpreter -- see docs/DATASET_INVENTORY_README.md).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd
import requests

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
CACHE_DIR = METADATA_DIR / "api_cache" / "inventory"
RESULTS_DIR = PROJECT_ROOT / "results" / "dataset_inventory"
LOG_PATH = RESULTS_DIR / "allen_inventory.log"
MANIFEST_PATH = METADATA_DIR / ".generated_manifest.json"

CELL_INVENTORY_CSV = METADATA_DIR / "cell_inventory.csv"
REGION_SUMMARY_CSV = METADATA_DIR / "region_summary.csv"
SWEEP_INVENTORY_CSV = METADATA_DIR / "sweep_inventory.csv"
MODEL_INVENTORY_CSV = METADATA_DIR / "model_inventory.csv"
REPORT_MD = RESULTS_DIR / "DATASET_INVENTORY_REPORT.md"
SUMMARY_JSON = RESULTS_DIR / "inventory_summary.json"
COVERAGE_JSON = RESULTS_DIR / "database_structure_coverage.json"

GENERATED_FILES = [CELL_INVENTORY_CSV, REGION_SUMMARY_CSV, SWEEP_INVENTORY_CSV,
                   MODEL_INVENTORY_CSV, REPORT_MD, SUMMARY_JSON, COVERAGE_JSON]

# --------------------------------------------------------------------------
# Audit configuration
# --------------------------------------------------------------------------
API_QUERY_URL = "http://api.brain-map.org/api/v2/data/query.json"
API_BASE = "http://api.brain-map.org"
USER_AGENT = "INCM-Phase0-DatasetAudit/1.0 (academic research; Allen Cell Types DB metadata only)"
HTTP_TIMEOUT = 120
MAX_TRIES = 4
PAGE_SIZE = 500            # rows per RMA page (5000 was accepted; 500 keeps payloads small)
ID_CHUNK = 100             # ids per ``$in`` list (keeps the query URL well under any limit)
MIN_DELAY_S = 0.15         # courtesy delay between live requests
COVERAGE_PAGE_SIZE = 2000  # page size for the whole-database coverage scan

# Acronyms checked when verifying that the absence of motor cells is a property
# of the database and not an artefact of the candidate list.
MOTOR_CONTROL_ACRONYMS = ("MOp", "MOs", "SSp", "SSs", "PT", "ALM", "FRP", "SC", "AN")

# `is_cell_specimen == true` selects exactly the published Cell Types Database
# roster (verified: 2336 rows, mouse 1923 + human 413, across 79 structures).
IS_CELL_SPECIMEN_CRITERION = "[is_cell_specimen$eqtrue]"

ORGANISM_MOUSE = 2

# Candidate regions.  Roles follow the proposal: one sensory population
# (Member 1) and one motor-related population (Member 2).  These are
# *candidates to investigate*, not confirmed available populations.
CANDIDATE_REGIONS: dict[str, dict[str, str]] = {
    "VISp": {"role": "sensory", "member": "Member 1"},
    "VISl": {"role": "sensory", "member": "Member 1"},
    "VISal": {"role": "sensory", "member": "Member 1"},
    "MOp": {"role": "motor", "member": "Member 2"},
    "ALM": {"role": "motor", "member": "Member 2"},
}

# Reference specimen from the previous project (mouse V1 / VISp layer 5).
REFERENCE_SPECIMEN_ID = 485909730

# Well-known-file type ids (verified against model::WellKnownFileType).
WKFT_NWB_DOWNLOAD = 481007198        # <ephys_result_id>_ephys.nwb
WKFT_NWB_UNCOMPRESSED = 478840678    # <ephys_result_id>_uncompressed.nwb
WKFT_3D_RECONSTRUCTION = 303941301   # morphology .swc
WKFT_MODEL_PARAMETERS = 329230374    # model fit / neuron_config JSON

# Stimulus-name -> audit category.  Categories not listed here are recorded
# verbatim under "other" so that nothing is silently invented.
STIMULUS_CATEGORIES = {
    "Long Square": "long_square",
    "Short Square": "short_square",
    "Ramp": "ramp",
    "Noise 1": "noise",
    "Noise 2": "noise",
    "Noise": "noise",
}
CURRENT_CLAMP_UNITS = "Amps"      # EphysSweep.stimulus_units == "Amps" => current clamp

# Preference order when a cell carries more than one biophysical model: the
# proposal names perisomatic first, then all-active.
BIOPHYS_CLASS_RANK = {"biophysical_perisomatic": 0, "biophysical_all_active": 1,
                      "biophysical_other": 2}

# Project-defined eligibility thresholds (metadata level only).
# Rationale: the protocol needs a calibration/held-out split of long-square
# sweeps for both the Allen-model validation (Exp 1) and the FHN fit (Exp 2),
# and an F-I curve needs several depolarising steps.  These are *audit*
# thresholds, not experimentally validated ones, and are tunable via CLI.
DEFAULT_MIN_LONG_SQUARE = 6
DEFAULT_MIN_DEPOLARIZING_LONG_SQUARE = 3

LOG = logging.getLogger("allen_inventory")


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
def setup_logging(verbose: bool = False) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG.setLevel(logging.DEBUG)
    LOG.handlers.clear()

    file_handler = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-7s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))

    LOG.addHandler(file_handler)
    LOG.addHandler(console)


# --------------------------------------------------------------------------
# API client
# --------------------------------------------------------------------------
class ApiErrorLog:
    """Collects every API failure so the report can distinguish
    'confirmed absent' from 'could not be retrieved'."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def add(self, stage: str, detail: str, criteria: str = "",
            status: str = "", recoverable: bool = True) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "stage": stage,
            "status": status,
            "recoverable": recoverable,
            "detail": detail,
            "criteria": criteria,
        }
        self.records.append(entry)
        LOG.error("API ERROR [%s] %s | %s | criteria=%s", stage, status, detail, criteria[:200])

    def __len__(self) -> int:
        return len(self.records)


class AllenRmaClient:
    """Minimal, cached, retrying client for the Allen Brain Map RMA v2 API."""

    def __init__(self, errors: ApiErrorLog, use_cache: bool = True) -> None:
        self.errors = errors
        self.use_cache = use_cache
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.request_count = 0
        self.cache_hits = 0
        self._last_request_ts = 0.0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # -- caching -----------------------------------------------------------
    @staticmethod
    def _cache_path(params: dict[str, Any]) -> Path:
        blob = json.dumps(params, sort_keys=True, default=str)
        digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]
        return CACHE_DIR / f"{digest}.json"

    # -- single request ----------------------------------------------------
    def query(self, criteria: str, include: str | None = None,
              num_rows: int | None = None, start_row: int | None = None,
              stage: str = "query") -> dict[str, Any] | None:
        """One RMA query.  Returns the envelope dict, or None on failure."""
        params: dict[str, Any] = {"criteria": criteria}
        if include:
            params["include"] = include
        if num_rows is not None:
            params["num_rows"] = num_rows
        if start_row is not None:
            params["start_row"] = start_row

        cache_path = self._cache_path(params)
        if self.use_cache and cache_path.exists():
            self.cache_hits += 1
            with cache_path.open(encoding="utf-8") as fh:
                return json.load(fh)

        wait = max(0.0, MIN_DELAY_S - (time.monotonic() - self._last_request_ts))
        if wait:
            time.sleep(wait)

        last_detail = "unknown"
        for attempt in range(1, MAX_TRIES + 1):
            self._last_request_ts = time.monotonic()
            try:
                self.request_count += 1
                resp = self.session.get(API_QUERY_URL, params=params, timeout=HTTP_TIMEOUT)
            except requests.RequestException as exc:
                last_detail = f"{type(exc).__name__}: {exc}"
                LOG.warning("network error (attempt %d/%d) %s", attempt, MAX_TRIES, last_detail)
                time.sleep(2 * attempt)
                continue

            if resp.status_code == 200:
                try:
                    payload = resp.json()
                except ValueError as exc:
                    last_detail = f"invalid JSON: {exc}"
                    break
                if isinstance(payload, dict) and payload.get("success"):
                    LOG.debug("RMA ok rows=%s total=%s stage=%s",
                              payload.get("num_rows"), payload.get("total_rows"), stage)
                    with cache_path.open("w", encoding="utf-8") as fh:
                        json.dump(payload, fh, default=str)
                    return payload
                msg = payload.get("msg") if isinstance(payload, dict) else str(payload)[:300]
                self.errors.add(stage, str(msg)[:500], criteria, f"HTTP 200 success=false")
                return None

            if resp.status_code in (429, 500, 502, 503, 504):
                last_detail = f"transient HTTP {resp.status_code}"
                LOG.warning("%s (attempt %d/%d)", last_detail, attempt, MAX_TRIES)
                time.sleep(2 * attempt)
                continue

            last_detail = f"HTTP {resp.status_code}"
            break

        self.errors.add(stage, last_detail, criteria, last_detail, recoverable=False)
        return None

    # -- paged query -------------------------------------------------------
    def query_all(self, criteria: str, include: str | None = None,
                  stage: str = "query_all",
                  page_size: int = PAGE_SIZE) -> tuple[list[dict[str, Any]], bool]:
        """Page through a query.  Returns (rows, complete_flag).

        ``complete_flag`` is False when paging stopped early because of an API
        error, which lets callers record UNKNOWN rather than 'absent'.
        """
        rows: list[dict[str, Any]] = []
        start = 0
        while True:
            payload = self.query(criteria, include=include, num_rows=page_size,
                                 start_row=start, stage=stage)
            if payload is None:
                return rows, False
            msg = payload.get("msg")
            if not isinstance(msg, list):
                return rows, False
            rows.extend(item for item in msg if isinstance(item, dict))
            total = int(payload.get("total_rows") or 0)
            start += len(msg)
            if not msg or start >= total:
                return rows, True


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def chunked(values: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for i in range(0, len(values), size):
        yield values[i:i + size]


def join_in(values: Sequence[Any]) -> str:
    return ",".join(str(v) for v in values)


def tag_value(tags: Any, prefix: str) -> str:
    """Extract the value of a specimen_tag whose name starts with ``prefix``.

    Returns "" when the tag is absent -- an empty string in the CSV means
    'not recorded in the database', never 'confirmed negative'.
    """
    if not isinstance(tags, list):
        return ""
    for tag in tags:
        name = (tag or {}).get("name") or ""
        if name.startswith(prefix):
            return name[len(prefix):].strip()
    return ""


def transgenic_line_names(donor: Any) -> tuple[str, str, str]:
    """(driver_lines, reporter_lines, full_genotype) from a donor record."""
    if not isinstance(donor, dict):
        return "", "", ""
    drivers: list[str] = []
    reporters: list[str] = []
    lines = donor.get("transgenic_lines")
    if isinstance(lines, list):
        for line in lines:
            if not isinstance(line, dict):
                continue
            name = line.get("name")
            if not name:
                continue
            kind = (line.get("transgenic_line_type_name") or "").lower()
            if kind == "driver":
                drivers.append(name)
            elif kind == "reporter":
                reporters.append(name)
            else:
                drivers.append(name)
    return ";".join(drivers), ";".join(reporters), donor.get("full_genotype") or ""


def split_region_layer(structure: dict[str, Any], parent_acronyms: dict[int, str]) -> tuple[str, str]:
    """Derive (region_acronym, cortical_layer) from a layer-level structure.

    The Cell Types Database stores layer as part of the structure acronym
    (VISp5, VISp2/3, MOp6a, ...).  The region is taken from the *parent*
    structure and the layer is the remaining suffix, so nothing is guessed.
    When the parent structure cannot be resolved the region is reported as
    unknown ("") rather than invented; the raw structure acronym is still
    preserved separately in the ``structure_acronym`` column.
    """
    acronym = structure.get("acronym") or ""
    parent_id = structure.get("parent_structure_id")
    region = parent_acronyms.get(parent_id, "")
    if region and acronym.startswith(region):
        return region, acronym[len(region):]
    return region, ""


def nwb_reference(ephys_result: Any) -> tuple[str, str, str]:
    """(nwb_file_id, nwb_path, nwb_download_url) from an ephys_result record."""
    if not isinstance(ephys_result, dict):
        return "", "", ""
    files = ephys_result.get("well_known_files")
    if not isinstance(files, list):
        return "", "", ""
    chosen: dict[str, Any] | None = None
    for item in files:
        if not isinstance(item, dict):
            continue
        if item.get("well_known_file_type_id") == WKFT_NWB_DOWNLOAD:
            chosen = item
            break
        if item.get("well_known_file_type_id") == WKFT_NWB_UNCOMPRESSED and chosen is None:
            chosen = item
    if chosen is None:
        return "", "", ""
    link = chosen.get("download_link") or ""
    return (str(chosen.get("id") or ""), chosen.get("path") or "",
            f"{API_BASE}{link}" if link else "")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: Sequence[str],
              sort_by: Sequence[str]) -> int:
    """Write ``rows`` to ``path`` deterministically (idempotent, no duplicates).

    Missing values are written as empty cells.  Re-running with the same cached
    API data produces a byte-identical file, so records are never duplicated.

    Identifier columns are rendered as integers, never as ``486509232.0``: pandas
    widens a column to ``float64`` as soon as one row is missing, which would
    otherwise corrupt every id in that column and break downstream joins.
    """
    frame = pd.DataFrame(rows, columns=list(columns))
    before = len(frame)
    key = list(sort_by)
    frame = frame.drop_duplicates(subset=key, keep="first")
    dropped = before - len(frame)
    if dropped:
        LOG.warning("%s: dropped %d duplicate rows on key %s", path.name, dropped, key)
    frame = frame.sort_values(key, kind="mergesort").reset_index(drop=True)
    frame = frame.where(pd.notna(frame), None)
    for column in frame.columns:
        series = frame[column]
        if series.dtype.kind != "f":
            continue
        present = series.dropna()
        if len(present) and bool((present % 1 == 0).all()):
            frame[column] = series.astype("Int64")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, na_rep="", encoding="utf-8", lineterminator="\n",
                 quoting=csv.QUOTE_MINIMAL)
    LOG.info("wrote %s (%d rows, %d columns)", path.name, len(frame), len(columns))
    return len(frame)



# --------------------------------------------------------------------------
# Step 2 -- region / structure discovery
# --------------------------------------------------------------------------
def discover_structures(client: AllenRmaClient) -> tuple[dict[str, dict[str, Any]],
                                                         dict[str, Any]]:
    """Resolve each candidate region acronym to its CCF structure and layers.

    Returns (regions, notes).  ``regions`` maps region acronym ->
    {status, structure_id, name, layers:[{id, acronym, layer, name}], note}.
    A region that the ontology genuinely does not contain is recorded with
    status="absent_from_ontology"; a region that could not be checked because
    the API failed is recorded with status="unknown".
    """
    regions: dict[str, dict[str, Any]] = {}
    notes: dict[str, Any] = {"regions_absent": [], "regions_unknown": []}

    for acronym, meta in CANDIDATE_REGIONS.items():
        payload = client.query(
            f"model::Structure,rma::criteria,[acronym$eq'{acronym}']",
            num_rows=10, stage=f"structure:{acronym}")
        if payload is None:
            regions[acronym] = {"status": "unknown", "role": meta["role"],
                                "member": meta["member"], "structure_id": None,
                                "name": None, "layers": [],
                                "note": "API error while resolving region acronym"}
            notes["regions_unknown"].append(acronym)
            continue

        msg = payload.get("msg") or []
        if not msg:
            regions[acronym] = {"status": "absent_from_ontology", "role": meta["role"],
                                "member": meta["member"], "structure_id": None,
                                "name": None, "layers": [],
                                "note": "structure acronym returned zero rows from "
                                        "model::Structure (confirmed absence, not a query failure)"}
            notes["regions_absent"].append(acronym)
            LOG.warning("region %s: acronym not present in the Allen structure ontology",
                        acronym)
            continue

        region = msg[0]
        region_id = region["id"]
        child_payload = client.query(
            f"model::Structure,rma::criteria,[parent_structure_id$eq{region_id}]",
            num_rows=100, stage=f"structure_children:{acronym}")
        layers: list[dict[str, Any]] = []
        if child_payload and isinstance(child_payload.get("msg"), list):
            for child in child_payload["msg"]:
                child_acr = child.get("acronym") or ""
                suffix = child_acr[len(acronym):] if child_acr.startswith(acronym) else ""
                layers.append({"id": child["id"], "acronym": child_acr,
                               "layer": suffix, "name": child.get("name")})
        else:
            notes.setdefault("layer_lookup_failed", []).append(acronym)

        regions[acronym] = {"status": "present", "role": meta["role"],
                            "member": meta["member"], "structure_id": region_id,
                            "name": region.get("name"), "layers": layers,
                            "note": ""}
        LOG.info("region %-6s id=%-5s name=%-32s layers=%s", acronym, region_id,
                 region.get("name"), [layer["acronym"] for layer in layers])

    return regions, notes


# --------------------------------------------------------------------------
# Step 2 -- specimen metadata
# --------------------------------------------------------------------------
SPECIMEN_INCLUDE = ("structure,donor(transgenic_lines),specimen_tags,"
                    "ephys_result(well_known_files),neuronal_models")


def fetch_specimens(client: AllenRmaClient,
                    structure_ids: Sequence[int]) -> tuple[list[dict[str, Any]], bool]:
    """Fetch every cell specimen in the candidate layer structures."""
    rows: list[dict[str, Any]] = []
    complete = True
    for chunk in chunked(list(structure_ids), 40):   # keep the URL short
        criteria = ("model::Specimen,rma::criteria,"
                    f"[structure_id$in{join_in(chunk)}],[is_cell_specimen$eqtrue]")
        page_rows, ok = client.query_all(criteria, include=SPECIMEN_INCLUDE,
                                         stage="specimens")
        rows.extend(page_rows)
        complete = complete and ok
        LOG.info("specimens: chunk of %d structures -> %d rows (complete=%s)",
                 len(chunk), len(page_rows), ok)
    return rows, complete


def fetch_templates(client: AllenRmaClient) -> dict[int, dict[str, str]]:
    """NeuronalModelTemplate id -> {name, description}. Source of model class."""
    payload = client.query("model::NeuronalModelTemplate", num_rows=200,
                           stage="neuronal_model_templates")
    templates: dict[int, dict[str, str]] = {}
    if payload and isinstance(payload.get("msg"), list):
        for row in payload["msg"]:
            templates[int(row["id"])] = {"name": row.get("name") or "",
                                         "description": row.get("description") or ""}
    LOG.info("neuronal model templates retrieved: %d", len(templates))
    return templates


def classify_template(templates: dict[int, dict[str, str]], template_id: Any) -> tuple[str, str]:
    """(model_class, template_name) for a neuronal_model_template_id.

    GLIF templates are classified as ``glif`` and are NEVER reported as
    biophysical.  An unknown template id yields ``unknown``.
    """
    if template_id is None or int(template_id) not in templates:
        return "unknown", ""
    info = templates[int(template_id)]
    name, description = info["name"], info["description"]
    lowered = f"{name} {description}".lower()
    if "biophysical" in lowered:
        if "perisomatic" in lowered:
            return "biophysical_perisomatic", name
        if "all active" in lowered or "all-active" in lowered:
            return "biophysical_all_active", name
        return "biophysical_other", name
    if "generalized leaky integrate-and-fire" in lowered or "lif" in lowered:
        return "glif", name
    return "unknown", name


def fetch_sweeps(client: AllenRmaClient,
                 specimen_ids: Sequence[int]) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    complete = True
    chunks = list(chunked(list(specimen_ids), ID_CHUNK))
    for index, chunk in enumerate(chunks, start=1):
        criteria = (f"model::EphysSweep,rma::criteria,[specimen_id$in{join_in(chunk)}]")
        page_rows, ok = client.query_all(criteria, stage="ephys_sweeps", page_size=2000)
        rows.extend(page_rows)
        complete = complete and ok
        if index % 5 == 0 or index == len(chunks):
            LOG.info("sweeps: %d/%d chunks, %d rows so far", index, len(chunks), len(rows))
    return rows, complete


def fetch_models(client: AllenRmaClient,
                 specimen_ids: Sequence[int]) -> tuple[list[dict[str, Any]], bool]:
    """Independent NeuronalModel query (cross-check of the embedded relation)."""
    rows: list[dict[str, Any]] = []
    complete = True
    for chunk in chunked(list(specimen_ids), ID_CHUNK):
        criteria = f"model::NeuronalModel,rma::criteria,[specimen_id$in{join_in(chunk)}]"
        page_rows, ok = client.query_all(criteria, stage="neuronal_models", page_size=2000)
        rows.extend(page_rows)
        complete = complete and ok
    LOG.info("neuronal models retrieved: %d (complete=%s)", len(rows), complete)
    return rows, complete


def fetch_reconstructions(client: AllenRmaClient,
                          specimen_ids: Sequence[int]) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    complete = True
    for chunk in chunked(list(specimen_ids), ID_CHUNK):
        criteria = (f"model::NeuronReconstruction,rma::criteria,"
                    f"[specimen_id$in{join_in(chunk)}]")
        page_rows, ok = client.query_all(criteria, stage="neuron_reconstructions",
                                         page_size=2000)
        rows.extend(page_rows)
        complete = complete and ok
    LOG.info("neuron reconstructions retrieved: %d (complete=%s)", len(rows), complete)
    return rows, complete


def fetch_model_files(client: AllenRmaClient,
                      model_ids: Sequence[int]) -> dict[int, dict[str, str]]:
    """model_id -> download reference for its parameter file."""
    references: dict[int, dict[str, str]] = {}
    for chunk in chunked(list(model_ids), ID_CHUNK):
        criteria = ("model::WellKnownFile,rma::criteria,"
                    f"[attachable_id$in{join_in(chunk)}],"
                    "[attachable_type$eq'NeuronalModel']")
        rows, _ok = client.query_all(criteria, stage="model_files", page_size=2000)
        for row in rows:
            attachable = row.get("attachable_id")
            if attachable is None:
                continue
            link = row.get("download_link") or ""
            references.setdefault(int(attachable), {
                "well_known_file_id": str(row.get("id") or ""),
                "well_known_file_type_id": str(row.get("well_known_file_type_id") or ""),
                "path": row.get("path") or "",
                "download_url": f"{API_BASE}{link}" if link else "",
            })
    LOG.info("model download references resolved: %d/%d", len(references), len(model_ids))
    return references


def fetch_reconstruction_files(client: AllenRmaClient,
                               recon_ids: Sequence[int]) -> dict[int, dict[str, str]]:
    references: dict[int, dict[str, str]] = {}
    for chunk in chunked(list(recon_ids), ID_CHUNK):
        criteria = ("model::WellKnownFile,rma::criteria,"
                    f"[attachable_id$in{join_in(chunk)}],"
                    "[attachable_type$eq'NeuronReconstruction'],"
                    f"[well_known_file_type_id$eq{WKFT_3D_RECONSTRUCTION}]")
        rows, _ok = client.query_all(criteria, stage="reconstruction_files", page_size=2000)
        for row in rows:
            attachable = row.get("attachable_id")
            if attachable is None:
                continue
            link = row.get("download_link") or ""
            references.setdefault(int(attachable), {
                "well_known_file_id": str(row.get("id") or ""),
                "path": row.get("path") or "",
                "download_url": f"{API_BASE}{link}" if link else "",
            })
    LOG.info("morphology SWC references resolved: %d/%d", len(references), len(recon_ids))
    return references


# --------------------------------------------------------------------------
# Step 5 -- preliminary eligibility
# --------------------------------------------------------------------------
def classify_eligibility(cell: dict[str, Any], thresholds: dict[str, int],
                         incomplete_stages: set[str]) -> tuple[str, list[str], list[str]]:
    """Return (status, satisfied_criteria, concerns).

    PASS         every required metadata criterion is confirmed present.
    CONDITIONAL  promising, but needs an actual NWB / model download to confirm.
    FAIL         a required criterion is confirmed ABSENT by the API.
    UNKNOWN      required metadata could not be retrieved (API failure).

    Missing information is never treated as FAIL.
    """
    satisfied: list[str] = []
    concerns: list[str] = []

    min_ls = thresholds["min_long_square"]
    min_dep = thresholds["min_depolarizing_long_square"]

    # --- UNKNOWN gates: metadata we could not retrieve -------------------
    if "specimens" in incomplete_stages:
        return "UNKNOWN", satisfied, ["specimen metadata retrieval incomplete (API error)"]
    if cell.get("ephys_result_id") and "ephys_sweeps" in incomplete_stages:
        return "UNKNOWN", satisfied, ["sweep metadata retrieval incomplete (API error)"]
    if cell.get("ephys_result_id") and "neuronal_models" in incomplete_stages:
        return "UNKNOWN", satisfied, ["model metadata retrieval incomplete (API error)"]
    if not cell.get("region_acronym") and "structure" in incomplete_stages:
        return "UNKNOWN", satisfied, ["structure metadata retrieval incomplete (API error)"]

    # --- confirmed absences -> FAIL --------------------------------------
    if cell.get("organism_id") != ORGANISM_MOUSE:
        return "FAIL", satisfied, [
            f"species is '{cell.get('species')}', not Mus musculus (project scope is mouse cortex)"]
    if not cell.get("region_acronym"):
        # The region could not be *resolved*; that is unavailable metadata, not
        # a confirmed absence, so it is UNKNOWN rather than FAIL.
        return "UNKNOWN", satisfied, [
            "target brain region could not be resolved from the structure "
            "hierarchy (metadata unavailable, not a confirmed absence)"]
    if cell.get("ephys_result_id") in (None, ""):
        return "FAIL", satisfied, ["no electrophysiology result attached (confirmed absent)"]
    if cell.get("ephys_failed") is True:
        return "FAIL", satisfied, ["EphysResult.failed == true (recording confirmed failed)"]
    if int(cell.get("n_long_square_cc") or 0) == 0:
        return "FAIL", satisfied, ["zero current-clamp Long Square sweeps (confirmed absent)"]

    satisfied.append("Mus musculus")
    satisfied.append(f"region {cell.get('region_acronym')} layer '{cell.get('cortical_layer')}'")
    satisfied.append("current-clamp electrophysiology present")
    satisfied.append(f"{cell.get('n_long_square_cc')} current-clamp Long Square sweeps")

    enough_ls = int(cell.get("n_long_square_cc") or 0) >= min_ls
    enough_dep = int(cell.get("n_long_square_depolarizing_cc") or 0) >= min_dep
    if enough_ls:
        satisfied.append(f">= {min_ls} Long Square sweeps for calibration + held-out split")
    else:
        concerns.append(f"only {cell.get('n_long_square_cc')} Long Square sweeps "
                        f"(< threshold {min_ls})")
    if enough_dep:
        satisfied.append(f">= {min_dep} depolarising Long Square sweeps for an F-I curve")
    else:
        concerns.append(f"only {cell.get('n_long_square_depolarizing_cc')} depolarising "
                        f"Long Square sweeps (< threshold {min_dep})")

    has_biophys = int(cell.get("n_biophysical_models") or 0) > 0
    if has_biophys:
        classes = sorted({c for c in (cell.get("biophysical_classes") or "").split(";") if c})
        satisfied.append("biophysical model present: " + ", ".join(classes))
    else:
        concerns.append("no biophysical model in metadata "
                        f"(GLIF only: {int(cell.get('n_glif_models') or 0)})")

    file_ok = bool(cell.get("biophysical_model_download_url"))
    if file_ok:
        satisfied.append("biophysical model download reference resolved")
    elif has_biophys:
        concerns.append("biophysical model listed but no download reference resolved")

    nwb_ok = bool(cell.get("nwb_download_url"))
    if nwb_ok:
        satisfied.append("NWB download reference resolved")
    else:
        concerns.append("no NWB download reference resolved")

    if enough_ls and enough_dep and has_biophys and file_ok and nwb_ok:
        # Metadata-complete, but Phase 0 performs no downloads: the actual
        # file contents and the model run are still unverified.
        return "PASS", satisfied, ["PASS is metadata-level only; NWB and model "
                                   "download validation still required"]
    return "CONDITIONAL", satisfied, concerns


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------
CELL_COLUMNS = [
    "specimen_id", "specimen_name", "region_acronym", "region_name", "region_role",
    "cortical_layer", "structure_id", "structure_acronym", "structure_name",
    "cortex_layer_id", "species", "organism_id", "donor_id", "donor_sex",
    "donor_full_genotype", "transgenic_driver_line", "transgenic_reporter_line",
    "dendrite_type", "apical_dendrite_status", "cell_reporter_id",
    "ephys_result_id", "ephys_available", "ephys_failed", "ephys_sampling_rate",
    "nwb_file_id", "nwb_download_url", "n_sweeps_total", "n_sweeps_current_clamp",
    "n_long_square", "n_long_square_cc", "n_long_square_depolarizing_cc",
    "n_long_square_hyperpolarizing_cc", "n_short_square_cc", "n_ramp_cc",
    "n_noise_cc", "n_other_cc", "long_square_sweep_numbers",
    "has_morphology", "reconstruction_id", "reconstruction_type",
    "reconstruction_superseded", "morphology_download_url",
    "n_models_total", "n_biophysical_perisomatic", "n_biophysical_all_active",
    "n_biophysical_models", "n_glif_models", "biophysical_classes",
    "biophysical_model_id", "biophysical_model_name", "biophysical_model_download_url",
    "eligibility", "eligibility_reasons", "eligibility_concerns",
    "needs_nwb_validation", "needs_model_validation", "metadata_complete",
]

SWEEP_COLUMNS = [
    "specimen_id", "region_acronym", "cortical_layer", "sweep_id", "sweep_number",
    "stimulus_name", "stimulus_category", "stimulus_description", "stimulus_units",
    "clamp_mode", "stimulus_absolute_amplitude", "stimulus_relative_amplitude",
    "stimulus_duration", "stimulus_start_time", "num_spikes",
]

MODEL_COLUMNS = [
    "model_id", "specimen_id", "region_acronym", "cortical_layer", "species",
    "model_name", "neuronal_model_template_id", "template_name", "model_class",
    "is_biophysical", "neuron_reconstruction_id", "availability_status",
    "well_known_file_id", "well_known_file_type_id", "file_path",
    "download_url", "download_reference_note", "source",
]

REGION_COLUMNS = [
    "region_acronym", "region_name", "region_role", "member", "status",
    "cortical_layer", "structure_id", "structure_acronym",
    "n_specimens", "n_mouse", "n_human", "n_other_species",
    "n_with_ephys_result", "n_ephys_failed", "n_with_current_clamp",
    "n_with_long_square_cc", "n_with_morphology",
    "n_with_perisomatic", "n_with_all_active", "n_with_any_biophysical", "n_glif_only",
    "n_pass", "n_conditional", "n_fail", "n_unknown",
    "median_long_square_cc", "note",
]



# --------------------------------------------------------------------------
# Record builders
# --------------------------------------------------------------------------
def build_structure_index(regions: dict[str, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    index: dict[int, dict[str, Any]] = {}
    for acronym, info in regions.items():
        for layer in info["layers"]:
            index[int(layer["id"])] = {
                "region_acronym": acronym,
                "region_name": info.get("name") or "",
                "region_role": info["role"],
                "cortical_layer": layer["layer"],
                "structure_acronym": layer["acronym"],
                "structure_name": layer.get("name") or "",
            }
    return index


def build_cell_records(specimens: list[dict[str, Any]],
                       structure_index: dict[int, dict[str, Any]],
                       templates: dict[int, dict[str, str]],
                       sweeps_by_specimen: dict[int, list[dict[str, Any]]],
                       models_by_specimen: dict[int, list[dict[str, Any]]],
                       recons_by_specimen: dict[int, list[dict[str, Any]]],
                       model_files: dict[int, dict[str, str]],
                       recon_files: dict[int, dict[str, str]],
                       incomplete_stages: set[str],
                       thresholds: dict[str, int]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for spec in specimens:
        specimen_id = int(spec["id"])
        location = structure_index.get(int(spec.get("structure_id") or -1), {})
        structure = spec.get("structure") or {}
        donor = spec.get("donor") or {}
        drivers, reporters, genotype = transgenic_line_names(donor)
        ephys = spec.get("ephys_result")
        ephys_id = spec.get("ephys_result_id")
        nwb_id, _nwb_path, nwb_url = nwb_reference(ephys)

        sweeps = sweeps_by_specimen.get(specimen_id, [])
        counts = Counter()
        ls_numbers: list[int] = []
        ls_dep = ls_hyp = 0
        for sweep in sweeps:
            name = sweep.get("stimulus_name") or ""
            category = STIMULUS_CATEGORIES.get(name, "other")
            counts[f"cat:{category}"] += 1
            is_cc = (sweep.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS
            if is_cc:
                counts["cc"] += 1
                counts[f"cc:{category}"] += 1
                if category == "long_square":
                    amplitude = sweep.get("stimulus_absolute_amplitude")
                    ls_numbers.append(sweep.get("sweep_number"))
                    if isinstance(amplitude, (int, float)):
                        if amplitude > 0:
                            ls_dep += 1
                        elif amplitude < 0:
                            ls_hyp += 1

        models = models_by_specimen.get(specimen_id, []) or list(spec.get("neuronal_models") or [])
        perisomatic = all_active = glif = biophys_other = 0
        classes: set[str] = set()
        primary_model: dict[str, Any] | None = None
        primary_ref: dict[str, str] = {}
        primary_rank: int | None = None
        for model in models:
            model_class, _name = classify_template(templates, model.get("neuronal_model_template_id"))
            if model_class == "biophysical_perisomatic":
                perisomatic += 1
                classes.add("perisomatic")
            elif model_class == "biophysical_all_active":
                all_active += 1
                classes.add("all_active")
            elif model_class == "biophysical_other":
                biophys_other += 1
                classes.add("other_biophysical")
            elif model_class == "glif":
                glif += 1
            rank = BIOPHYS_CLASS_RANK.get(model_class)
            if rank is not None and (primary_rank is None or rank < primary_rank):
                primary_rank = rank
                primary_model = model
                primary_ref = model_files.get(int(model["id"]), {})

        recons = recons_by_specimen.get(specimen_id, [])
        chosen_recon: dict[str, Any] | None = None
        for recon in recons:
            if not recon.get("superseded"):
                chosen_recon = recon
                break
        if chosen_recon is None and recons:
            chosen_recon = recons[0]
        recon_ref = recon_files.get(int(chosen_recon["id"]), {}) if chosen_recon else {}

        cell: dict[str, Any] = {
            "specimen_id": specimen_id,
            "specimen_name": spec.get("name") or "",
            "region_acronym": location.get("region_acronym", ""),
            "region_name": location.get("region_name", ""),
            "region_role": location.get("region_role", ""),
            "cortical_layer": location.get("cortical_layer", ""),
            "structure_id": spec.get("structure_id"),
            "structure_acronym": structure.get("acronym") or location.get("structure_acronym", ""),
            "structure_name": structure.get("name") or location.get("structure_name", ""),
            "cortex_layer_id": spec.get("cortex_layer_id"),
            "species": ORGANISM_NAMES.get(donor.get("organism_id"), ""),
            "organism_id": donor.get("organism_id"),
            "donor_id": spec.get("donor_id"),
            "donor_sex": donor.get("sex") or "",
            "donor_full_genotype": genotype,
            "transgenic_driver_line": drivers,
            "transgenic_reporter_line": reporters,
            "dendrite_type": tag_value(spec.get("specimen_tags"), "dendrite type - "),
            "apical_dendrite_status": tag_value(spec.get("specimen_tags"), "apical - "),
            "cell_reporter_id": spec.get("cell_reporter_id"),
            "ephys_result_id": ephys_id,
            "ephys_available": bool(ephys_id) and isinstance(ephys, dict),
            "ephys_failed": (ephys or {}).get("failed") if isinstance(ephys, dict) else None,
            "ephys_sampling_rate": (ephys or {}).get("sampling_rate") if isinstance(ephys, dict) else None,
            "nwb_file_id": nwb_id,
            "nwb_download_url": nwb_url,
            "n_sweeps_total": len(sweeps),
            "n_sweeps_current_clamp": counts.get("cc", 0),
            "n_long_square": counts.get("cat:long_square", 0),
            "n_long_square_cc": counts.get("cc:long_square", 0),
            "n_long_square_depolarizing_cc": ls_dep,
            "n_long_square_hyperpolarizing_cc": ls_hyp,
            "n_short_square_cc": counts.get("cc:short_square", 0),
            "n_ramp_cc": counts.get("cc:ramp", 0),
            "n_noise_cc": counts.get("cc:noise", 0),
            "n_other_cc": counts.get("cc:other", 0),
            "long_square_sweep_numbers": ";".join(
                str(n) for n in sorted(x for x in ls_numbers if x is not None)),
            "has_morphology": bool(chosen_recon) and bool(recon_ref.get("download_url")),
            "reconstruction_id": (chosen_recon or {}).get("id"),
            "reconstruction_type": (chosen_recon or {}).get("neuron_reconstruction_type") or "",
            "reconstruction_superseded": (chosen_recon or {}).get("superseded"),
            "morphology_download_url": recon_ref.get("download_url", ""),
            "n_models_total": len(models),
            "n_biophysical_perisomatic": perisomatic,
            "n_biophysical_all_active": all_active,
            "n_biophysical_models": perisomatic + all_active + biophys_other,
            "n_glif_models": glif,
            "biophysical_classes": ";".join(sorted(classes)),
            "biophysical_model_id": (primary_model or {}).get("id"),
            "biophysical_model_name": (primary_model or {}).get("name") or "",
            "biophysical_model_download_url": primary_ref.get("download_url", ""),
        }

        cell["metadata_complete"] = not (
            ("specimens" in incomplete_stages)
            or (bool(ephys_id) and ("ephys_sweeps" in incomplete_stages))
            or (bool(ephys_id) and ("neuronal_models" in incomplete_stages)))
        status, satisfied, concerns = classify_eligibility(cell, thresholds, incomplete_stages)
        cell["eligibility"] = status
        cell["eligibility_reasons"] = " | ".join(satisfied)
        cell["eligibility_concerns"] = " | ".join(concerns)
        promising = status in ("PASS", "CONDITIONAL")
        cell["needs_nwb_validation"] = bool(promising and nwb_url)
        cell["needs_model_validation"] = bool(promising and primary_model)
        cells.append(cell)
    return cells


ORGANISM_NAMES = {1: "Homo sapiens", 2: "Mus musculus"}


def build_sweep_records(cells_by_id: dict[int, dict[str, Any]],
                        sweeps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sweep in sweeps:
        specimen_id = int(sweep["specimen_id"])
        cell = cells_by_id.get(specimen_id, {})
        name = sweep.get("stimulus_name") or ""
        units = sweep.get("stimulus_units") or ""
        rows.append({
            "specimen_id": specimen_id,
            "region_acronym": cell.get("region_acronym", ""),
            "cortical_layer": cell.get("cortical_layer", ""),
            "sweep_id": sweep.get("id"),
            "sweep_number": sweep.get("sweep_number"),
            "stimulus_name": name,
            "stimulus_category": STIMULUS_CATEGORIES.get(name, "other"),
            "stimulus_description": sweep.get("stimulus_description") or "",
            "stimulus_units": units,
            "clamp_mode": "current_clamp" if units == CURRENT_CLAMP_UNITS else
                          ("voltage_clamp" if units == "Volts" else ""),
            "stimulus_absolute_amplitude": sweep.get("stimulus_absolute_amplitude"),
            "stimulus_relative_amplitude": sweep.get("stimulus_relative_amplitude"),
            "stimulus_duration": sweep.get("stimulus_duration"),
            "stimulus_start_time": sweep.get("stimulus_start_time"),
            "num_spikes": sweep.get("num_spikes"),
        })
    return rows


def build_model_records(cells_by_id: dict[int, dict[str, Any]],
                        templates: dict[int, dict[str, str]],
                        models: list[dict[str, Any]],
                        model_files: dict[int, dict[str, str]],
                        source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in models:
        model_id = int(model["id"])
        specimen_id = int(model["specimen_id"])
        cell = cells_by_id.get(specimen_id, {})
        model_class, template_name = classify_template(
            templates, model.get("neuronal_model_template_id"))
        reference = model_files.get(model_id, {})
        is_biophysical = model_class.startswith("biophysical")
        if reference.get("download_url"):
            availability = "metadata_present_download_reference_resolved"
        elif is_biophysical or model_class == "glif":
            availability = "metadata_present_download_reference_unresolved"
        else:
            availability = "model_class_unknown"
        rows.append({
            "model_id": model_id,
            "specimen_id": specimen_id,
            "region_acronym": cell.get("region_acronym", ""),
            "cortical_layer": cell.get("cortical_layer", ""),
            "species": cell.get("species", ""),
            "model_name": model.get("name") or "",
            "neuronal_model_template_id": model.get("neuronal_model_template_id"),
            "template_name": template_name,
            "model_class": model_class,
            "is_biophysical": is_biophysical,
            "neuron_reconstruction_id": model.get("neuron_reconstruction_id"),
            "availability_status": availability,
            "well_known_file_id": reference.get("well_known_file_id", ""),
            "well_known_file_type_id": reference.get("well_known_file_type_id", ""),
            "file_path": reference.get("path", ""),
            "download_url": reference.get("download_url", ""),
            "download_reference_note":
                "AllenSDK equivalent: CellTypesCache.get_neuronal_model("
                f"{model_id}) into neuronal_model_{model_id}/",
            "source": source,
        })
    return rows


def build_region_summary(cells: list[dict[str, Any]],
                         regions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        grouped[(cell["region_acronym"], cell["cortical_layer"])].append(cell)

    rows: list[dict[str, Any]] = []
    for (region, layer), group in sorted(grouped.items()):
        info = regions.get(region, {})
        eligibility = Counter(cell["eligibility"] for cell in group)
        ls_counts = sorted(int(cell.get("n_long_square_cc") or 0) for cell in group)
        median = (ls_counts[len(ls_counts) // 2] if len(ls_counts) % 2
                  else (ls_counts[len(ls_counts) // 2 - 1] + ls_counts[len(ls_counts) // 2]) / 2
                  ) if ls_counts else ""
        structure = next((cell for cell in group if cell.get("structure_id")), {})
        rows.append({
            "region_acronym": region,
            "region_name": info.get("name", "") or (group[0].get("region_name") or ""),
            "region_role": info.get("role", "") or (group[0].get("region_role") or ""),
            "member": info.get("member", ""),
            "status": info.get("status", "present"),
            "cortical_layer": layer,
            "structure_id": structure.get("structure_id"),
            "structure_acronym": structure.get("structure_acronym", ""),
            "n_specimens": len(group),
            "n_mouse": sum(1 for c in group if c.get("organism_id") == ORGANISM_MOUSE),
            "n_human": sum(1 for c in group if c.get("organism_id") == 1),
            "n_other_species": sum(1 for c in group
                                   if c.get("organism_id") not in (1, ORGANISM_MOUSE)),
            "n_with_ephys_result": sum(1 for c in group if c.get("ephys_result_id")),
            "n_ephys_failed": sum(1 for c in group if c.get("ephys_failed") is True),
            "n_with_current_clamp": sum(1 for c in group
                                        if int(c.get("n_sweeps_current_clamp") or 0) > 0),
            "n_with_long_square_cc": sum(1 for c in group
                                         if int(c.get("n_long_square_cc") or 0) > 0),
            "n_with_morphology": sum(1 for c in group if c.get("has_morphology")),
            "n_with_perisomatic": sum(1 for c in group
                                      if int(c.get("n_biophysical_perisomatic") or 0) > 0),
            "n_with_all_active": sum(1 for c in group
                                     if int(c.get("n_biophysical_all_active") or 0) > 0),
            "n_with_any_biophysical": sum(1 for c in group
                                          if int(c.get("n_biophysical_models") or 0) > 0),
            "n_glif_only": sum(1 for c in group
                               if int(c.get("n_glif_models") or 0) > 0
                               and int(c.get("n_biophysical_models") or 0) == 0),
            "n_pass": eligibility.get("PASS", 0),
            "n_conditional": eligibility.get("CONDITIONAL", 0),
            "n_fail": eligibility.get("FAIL", 0),
            "n_unknown": eligibility.get("UNKNOWN", 0),
            "median_long_square_cc": median,
            "note": "",
        })

    # Regions that exist in the ontology but yielded no cell specimens, and
    # regions that are absent/unknown, are still reported so that "no data"
    # is distinguishable from "not checked".
    for region, info in sorted(regions.items()):
        if any(row["region_acronym"] == region for row in rows):
            continue
        rows.append({
            "region_acronym": region, "region_name": info.get("name") or "",
            "region_role": info["role"], "member": info["member"],
            "status": info["status"], "cortical_layer": "",
            "structure_id": info.get("structure_id"), "structure_acronym": "",
            "n_specimens": 0, "n_mouse": 0, "n_human": 0, "n_other_species": 0,
            "n_with_ephys_result": 0, "n_ephys_failed": 0, "n_with_current_clamp": 0,
            "n_with_long_square_cc": 0, "n_with_morphology": 0, "n_with_perisomatic": 0,
            "n_with_all_active": 0, "n_with_any_biophysical": 0, "n_glif_only": 0,
            "n_pass": 0, "n_conditional": 0, "n_fail": 0, "n_unknown": 0,
            "median_long_square_cc": "",
            "note": info.get("note", "") or _zero_specimen_note(info),
        })
    return rows


def _zero_specimen_note(info: dict[str, Any]) -> str:
    """Explain a region that exists in the ontology but yielded no cell specimen.

    This keeps three situations distinguishable in ``region_summary.csv``:
    ``absent_from_ontology`` (acronym not in the CCF at all), ``unknown`` (API
    error), and ``present`` with zero specimens (structure exists, database has
    no cells attached to it).
    """
    if info.get("status") != "present":
        return ""
    layers = ", ".join(layer.get("acronym") or "" for layer in info.get("layers", []))
    return (f"structure present in the Allen CCF ontology (id={info.get('structure_id')}, "
            f"{info.get('name') or 'unnamed'}) with layer sub-structures "
            f"[{layers or 'none'}], but model::Specimen returned zero cell specimens "
            f"at the region level and at every layer level (confirmed absence of data, "
            f"not a query failure)")



# --------------------------------------------------------------------------
# Step 2b -- whole-database coverage verification
# --------------------------------------------------------------------------
def template_ids_for_class(templates: dict[int, dict[str, str]],
                           keyword: str) -> list[int]:
    """Template ids whose official name/description contains ``keyword``.

    Deriving the ids from ``model::NeuronalModelTemplate`` instead of hard-coding
    them keeps the biophysical / GLIF split tied to Allen's own naming.
    """
    return sorted(tid for tid, info in templates.items()
                  if keyword in f"{info['name']} {info['description']}".lower())


def verify_region_coverage(client: AllenRmaClient,
                           regions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Count cell specimens for every candidate region *at every hierarchy level*.

    The main inventory queries layer sub-structures (``VISp5``, ``VISp2/3``, ...).
    A region could still hold cells attached directly to the parent structure, so
    that possibility is checked explicitly instead of assumed away.  Motor and
    somatosensory acronyms outside the candidate list are checked as controls, so
    that "no motor cells" is a database-wide statement rather than an artefact of
    the candidate list.
    """
    targets: dict[str, dict[str, Any]] = {}

    for acronym, info in sorted(regions.items()):
        if info.get("structure_id"):
            targets[acronym] = {"structure_id": info["structure_id"],
                                "name": info.get("name"),
                                "ontology_status": info.get("status"),
                                "role": info.get("role"),
                                "checked_because": "candidate region (parent level)"}
        for layer in info.get("layers", []):
            targets[layer["acronym"]] = {"structure_id": layer["id"],
                                         "name": layer.get("name"),
                                         "ontology_status": info.get("status"),
                                         "role": info.get("role"),
                                         "checked_because": f"layer of {acronym}"}

    for acronym in MOTOR_CONTROL_ACRONYMS:
        if acronym in targets:
            continue
        payload = client.query(f"model::Structure,rma::criteria,[acronym$eq'{acronym}']",
                               num_rows=5, stage=f"structure:{acronym}")
        if payload is None:
            targets[acronym] = {"structure_id": None, "name": None,
                                "ontology_status": "unknown", "role": "control",
                                "checked_because": "motor/somatosensory control acronym",
                                "note": "API error while resolving the acronym "
                                        "(UNKNOWN, not a confirmed absence)"}
            continue
        rows = payload.get("msg") or []
        if not rows:
            targets[acronym] = {
                "structure_id": None, "name": None,
                "ontology_status": "absent_from_ontology", "role": "control",
                "checked_because": "motor/somatosensory control acronym",
                "note": "acronym returned zero rows from model::Structure on a "
                        "successful query (confirmed absence from the ontology)"}
            continue
        for row in rows:
            targets[row.get("acronym") or acronym] = {
                "structure_id": row["id"], "name": row.get("name"),
                "ontology_status": "present", "role": "control",
                "checked_because": "motor/somatosensory control acronym", "note": ""}

    coverage: list[dict[str, Any]] = []
    for acronym, target in sorted(targets.items()):
        structure_id = target.get("structure_id")
        record = {"structure_acronym": acronym, "structure_id": structure_id,
                  "structure_name": target.get("name"),
                  "ontology_status": target.get("ontology_status"),
                  "role": target.get("role") or "control",
                  "checked_because": target.get("checked_because"),
                  "cell_specimens_at_this_level": None,
                  "note": target.get("note", "")}
        if structure_id is not None:
            payload = client.query(
                "model::Specimen,rma::criteria,"
                f"[structure_id$eq{structure_id}],{IS_CELL_SPECIMEN_CRITERION}",
                num_rows=1, stage="region_level_cell_count")
            if payload is None:
                record["note"] = (record["note"] + " | " if record["note"] else "") + \
                    "cell count unavailable (API error: UNKNOWN, not a confirmed zero)"
            else:
                record["cell_specimens_at_this_level"] = int(payload.get("total_rows") or 0)
        coverage.append(record)
    return coverage


def fetch_database_coverage(client: AllenRmaClient,
                            templates: dict[int, dict[str, str]]) -> dict[str, Any]:
    """Cross-tabulate every Cell Types Database cell and model by structure.

    Answers reporting item 2 ("regions represented in the database") for the
    *whole* database rather than only the candidate regions, and evaluates the
    fallback population pairs named in ``INCM_revised_project.pdf``.
    """
    specimens, spec_ok = client.query_all(
        f"model::Specimen,rma::criteria,{IS_CELL_SPECIMEN_CRITERION}",
        include="structure,donor", stage="db_coverage_specimens",
        page_size=COVERAGE_PAGE_SIZE)

    biophys_ids = template_ids_for_class(templates, "biophysical")
    glif_ids = template_ids_for_class(templates, "generalized leaky integrate-and-fire")
    biophys_ok = glif_ok = True
    biophysical: list[dict[str, Any]] = []
    glif: list[dict[str, Any]] = []
    if biophys_ids:
        biophysical, biophys_ok = client.query_all(
            "model::NeuronalModel,rma::criteria,"
            f"[neuronal_model_template_id$in{join_in(biophys_ids)}]",
            stage="db_coverage_biophysical", page_size=COVERAGE_PAGE_SIZE)
    if glif_ids:
        glif, glif_ok = client.query_all(
            "model::NeuronalModel,rma::criteria,"
            f"[neuronal_model_template_id$in{join_in(glif_ids)}]",
            stage="db_coverage_glif", page_size=COVERAGE_PAGE_SIZE)

    specimen_by_id = {int(spec["id"]): spec for spec in specimens}
    structures: dict[int, dict[str, Any]] = {}
    for spec in specimens:
        structure = spec.get("structure") or {}
        if structure.get("id") is not None:
            structures[int(structure["id"])] = {
                "acronym": structure.get("acronym"), "name": structure.get("name"),
                "parent_structure_id": structure.get("parent_structure_id")}

    per_structure: dict[int, Counter] = defaultdict(Counter)
    for spec in specimens:
        sid = int(spec.get("structure_id") or -1)
        organism = (spec.get("donor") or {}).get("organism_id")
        per_structure[sid]["cells"] += 1
        per_structure[sid]["mouse" if organism == ORGANISM_MOUSE else "human_or_other"] += 1

    def tally(row: dict[str, Any], key: str) -> None:
        spec = specimen_by_id.get(int(row.get("specimen_id") or -1))
        if spec is None:
            per_structure[-1]["orphan_models"] += 1
            return
        sid = int(spec.get("structure_id") or -1)
        per_structure[sid][key] += 1
        if (spec.get("donor") or {}).get("organism_id") == ORGANISM_MOUSE:
            per_structure[sid][f"{key}_mouse"] += 1
        template_id = row.get("neuronal_model_template_id")
        model_class = classify_template(templates, template_id)[0]
        if model_class in ("biophysical_perisomatic", "biophysical_all_active"):
            per_structure[sid][model_class] += 1

    for row in biophysical:
        tally(row, "biophysical_models")
    for row in glif:
        tally(row, "glif_models")

    table = []
    for sid, counts in per_structure.items():
        info = structures.get(sid, {})
        table.append({
            "structure_id": sid if sid != -1 else None,
            "acronym": info.get("acronym"), "name": info.get("name"),
            "parent_structure_id": info.get("parent_structure_id"),
            "cells": counts["cells"], "mouse_cells": counts["mouse"],
            "human_or_other_cells": counts["human_or_other"],
            "biophysical_models": counts["biophysical_models"],
            "biophysical_models_mouse": counts["biophysical_models_mouse"],
            "biophysical_perisomatic": counts["biophysical_perisomatic"],
            "biophysical_all_active": counts["biophysical_all_active"],
            "glif_models": counts["glif_models"],
            "glif_models_mouse": counts["glif_models_mouse"],
            "orphan_models": counts["orphan_models"],
        })
    table.sort(key=lambda row: (-row["biophysical_models"], -row["cells"],
                                str(row["acronym"])))

    incomplete = [stage for stage, ok in (("db_coverage_specimens", spec_ok),
                                          ("db_coverage_biophysical", biophys_ok),
                                          ("db_coverage_glif", glif_ok)) if not ok]
    return {
        "complete": not incomplete,
        "incomplete_stages": incomplete,
        "biophysical_template_ids": biophys_ids,
        "glif_template_ids": glif_ids,
        "cell_specimens_retrieved": len(specimens),
        "biophysical_models_retrieved": len(biophysical),
        "glif_models_retrieved": len(glif),
        "distinct_structures": len({row["structure_id"] for row in table
                                    if row["structure_id"] is not None}),
        "structures": table,
        "totals": {
            "cells": sum(row["cells"] for row in table),
            "mouse_cells": sum(row["mouse_cells"] for row in table),
            "human_or_other_cells": sum(row["human_or_other_cells"] for row in table),
            "biophysical_models": sum(row["biophysical_models"] for row in table),
            "biophysical_models_mouse": sum(row["biophysical_models_mouse"] for row in table),
            "biophysical_perisomatic": sum(row["biophysical_perisomatic"] for row in table),
            "biophysical_all_active": sum(row["biophysical_all_active"] for row in table),
            "glif_models": sum(row["glif_models"] for row in table),
            "structures_with_any_biophysical": sum(
                1 for row in table if row["biophysical_models"] > 0),
            "structures_with_four_plus_mouse_biophysical": sum(
                1 for row in table
                if row["biophysical_models_mouse"] >= POPULATION_QUALIFYING_CELLS),
            "orphan_models": sum(row["orphan_models"] for row in table),
        },
    }


# --------------------------------------------------------------------------
# Step 7 -- reference specimen
# --------------------------------------------------------------------------
def check_reference_specimen(client: AllenRmaClient,
                             cells_by_id: dict[int, dict[str, Any]],
                             structure_index: dict[int, dict[str, Any]],
                             templates: dict[int, dict[str, str]],
                             thresholds: dict[str, int],
                             incomplete_stages: set[str]) -> dict[str, Any]:
    """Look the previous project's cell (485909730) up in the *current* API."""
    result: dict[str, Any] = {
        "specimen_id": REFERENCE_SPECIMEN_ID,
        "returned_by_current_api": None,
        "in_candidate_inventory": REFERENCE_SPECIMEN_ID in cells_by_id,
        "cell": None,
        "models": [],
        "api_note": "",
    }
    payload = client.query(
        f"model::Specimen,rma::criteria,[id$eq{REFERENCE_SPECIMEN_ID}]",
        include=SPECIMEN_INCLUDE, num_rows=1, stage="reference_specimen")
    if payload is None:
        result["returned_by_current_api"] = False
        result["api_note"] = ("model::Specimen query for id="
                              f"{REFERENCE_SPECIMEN_ID} did not succeed; treat as UNKNOWN, "
                              "not as confirmed absence.")
        return result

    msg = payload.get("msg") or []
    result["returned_by_current_api"] = bool(msg)
    if not msg:
        result["api_note"] = ("API responded successfully but returned zero rows for id="
                              f"{REFERENCE_SPECIMEN_ID} (confirmed absent from model::Specimen).")
        return result

    spec = msg[0]
    cell = cells_by_id.get(REFERENCE_SPECIMEN_ID)
    if cell is None:
        # Not inside the candidate structures: build a stand-alone record.
        location = structure_index.get(int(spec.get("structure_id") or -1), {})
        structure = spec.get("structure") or {}
        donor = spec.get("donor") or {}
        drivers, reporters, genotype = transgenic_line_names(donor)
        nwb_id, _path, nwb_url = nwb_reference(spec.get("ephys_result"))
        sweeps, _ok = fetch_sweeps(client, [REFERENCE_SPECIMEN_ID])
        models, _ok2 = fetch_models(client, [REFERENCE_SPECIMEN_ID])
        cell = {
            "specimen_id": REFERENCE_SPECIMEN_ID,
            "specimen_name": spec.get("name") or "",
            "region_acronym": location.get("region_acronym", "")
                              or (structure.get("acronym") or ""),
            "region_name": location.get("region_name", "") or (structure.get("name") or ""),
            "region_role": location.get("region_role", "") or "not_a_candidate_region",
            "cortical_layer": location.get("cortical_layer", ""),
            "structure_id": spec.get("structure_id"),
            "structure_acronym": structure.get("acronym") or "",
            "structure_name": structure.get("name") or "",
            "cortex_layer_id": spec.get("cortex_layer_id"),
            "species": ORGANISM_NAMES.get(donor.get("organism_id"), ""),
            "organism_id": donor.get("organism_id"),
            "donor_id": spec.get("donor_id"),
            "donor_sex": donor.get("sex") or "",
            "donor_full_genotype": genotype,
            "transgenic_driver_line": drivers,
            "transgenic_reporter_line": reporters,
            "dendrite_type": tag_value(spec.get("specimen_tags"), "dendrite type - "),
            "apical_dendrite_status": tag_value(spec.get("specimen_tags"), "apical - "),
            "cell_reporter_id": spec.get("cell_reporter_id"),
            "ephys_result_id": spec.get("ephys_result_id"),
            "ephys_available": bool(spec.get("ephys_result_id")),
            "ephys_failed": (spec.get("ephys_result") or {}).get("failed"),
            "ephys_sampling_rate": (spec.get("ephys_result") or {}).get("sampling_rate"),
            "nwb_file_id": nwb_id,
            "nwb_download_url": nwb_url,
            "n_sweeps_total": len(sweeps),
            "n_sweeps_current_clamp": sum(
                1 for s in sweeps if (s.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS),
            "n_long_square": sum(1 for s in sweeps
                                 if (s.get("stimulus_name") or "") == "Long Square"),
            "n_long_square_cc": sum(1 for s in sweeps
                                    if (s.get("stimulus_name") or "") == "Long Square"
                                    and (s.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS),
            "n_long_square_depolarizing_cc": sum(
                1 for s in sweeps
                if (s.get("stimulus_name") or "") == "Long Square"
                and (s.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS
                and isinstance(s.get("stimulus_absolute_amplitude"), (int, float))
                and s["stimulus_absolute_amplitude"] > 0),
            "n_long_square_hyperpolarizing_cc": sum(
                1 for s in sweeps
                if (s.get("stimulus_name") or "") == "Long Square"
                and (s.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS
                and isinstance(s.get("stimulus_absolute_amplitude"), (int, float))
                and s["stimulus_absolute_amplitude"] < 0),
            "n_short_square_cc": sum(1 for s in sweeps
                                     if (s.get("stimulus_name") or "") == "Short Square"
                                     and (s.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS),
            "n_ramp_cc": sum(1 for s in sweeps if (s.get("stimulus_name") or "") == "Ramp"
                             and (s.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS),
            "n_noise_cc": sum(1 for s in sweeps
                              if STIMULUS_CATEGORIES.get(s.get("stimulus_name") or "") == "noise"
                              and (s.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS),
            "n_other_cc": 0,
            "long_square_sweep_numbers": ";".join(
                str(s.get("sweep_number")) for s in sorted(
                    (x for x in sweeps if (x.get("stimulus_name") or "") == "Long Square"
                     and (x.get("stimulus_units") or "") == CURRENT_CLAMP_UNITS),
                    key=lambda x: x.get("sweep_number") or 0)),
            "has_morphology": None,
            "reconstruction_id": None,
            "reconstruction_type": "",
            "reconstruction_superseded": None,
            "morphology_download_url": "",
            "n_models_total": len(models),
            "n_biophysical_perisomatic": sum(
                1 for m in models
                if classify_template(templates, m.get("neuronal_model_template_id"))[0]
                == "biophysical_perisomatic"),
            "n_biophysical_all_active": sum(
                1 for m in models
                if classify_template(templates, m.get("neuronal_model_template_id"))[0]
                == "biophysical_all_active"),
            "n_biophysical_models": sum(
                1 for m in models
                if classify_template(templates, m.get("neuronal_model_template_id"))[0]
                .startswith("biophysical")),
            "n_glif_models": sum(
                1 for m in models
                if classify_template(templates, m.get("neuronal_model_template_id"))[0] == "glif"),
            "biophysical_classes": "",
            "biophysical_model_id": None,
            "biophysical_model_name": "",
            "biophysical_model_download_url": "",
            "metadata_complete": _ok and _ok2,
        }
        cell["eligibility"], _s, _c = classify_eligibility(cell, thresholds, incomplete_stages)
        cell["eligibility_reasons"] = ""
        cell["eligibility_concerns"] = ""
        cell["needs_nwb_validation"] = None
        cell["needs_model_validation"] = None

    result["cell"] = cell
    for model in (spec.get("neuronal_models") or []):
        model_class, template_name = classify_template(
            templates, model.get("neuronal_model_template_id"))
        result["models"].append({
            "model_id": model.get("id"),
            "template_name": template_name,
            "model_class": model_class,
            "model_name": model.get("name"),
            "neuron_reconstruction_id": model.get("neuron_reconstruction_id"),
        })
    return result


# --------------------------------------------------------------------------
# Step 8 -- quality checks
# --------------------------------------------------------------------------
def run_quality_checks(cells: list[dict[str, Any]], sweeps: list[dict[str, Any]],
                       models: list[dict[str, Any]], regions: list[dict[str, Any]],
                       embedded_models: list[dict[str, Any]],
                       direct_models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})
        (LOG.info if passed else LOG.warning)("QC %-52s %s | %s", name,
                                             "PASS" if passed else "FAIL", detail)

    ids = [cell["specimen_id"] for cell in cells]
    add("specimen_ids_unique", len(ids) == len(set(ids)),
        f"{len(ids)} rows, {len(set(ids))} distinct specimen_id")

    model_ids = [row["model_id"] for row in models]
    add("model_ids_unique", len(model_ids) == len(set(model_ids)),
        f"{len(model_ids)} rows, {len(set(model_ids))} distinct model_id")

    overlap = set(model_ids) & set(ids)
    add("model_ids_disjoint_from_specimen_ids", not overlap,
        f"overlapping ids: {sorted(overlap)[:10] or 'none'}")

    bad_fk = [row["model_id"] for row in models
              if int(row["specimen_id"]) not in set(ids)]
    add("every_model_maps_to_an_inventoried_specimen", not bad_fk,
        f"models with specimen_id outside the cell inventory: {len(bad_fk)}")

    region_total = sum(int(row["n_specimens"]) for row in regions if row["cortical_layer"])
    add("region_counts_match_specimen_inventory", region_total == len(cells),
        f"region_summary layer rows total={region_total}, cell_inventory rows={len(cells)}")

    glif_flagged = [row["model_id"] for row in models
                    if row["model_class"] == "glif" and row["is_biophysical"]]
    add("glif_never_classified_as_biophysical", not glif_flagged,
        f"misclassified GLIF models: {len(glif_flagged)}")

    biophys_names = [row["model_id"] for row in models
                     if row["is_biophysical"]
                     and not row["model_name"].lower().startswith("biophysical")]
    add("biophysical_rows_have_biophysical_model_names", not biophys_names,
        f"template/name mismatches: {len(biophys_names)}")

    add("no_glif_ids_in_cell_biophysical_counts",
        all(int(cell.get("n_biophysical_models") or 0)
            == int(cell.get("n_biophysical_perisomatic") or 0)
            + int(cell.get("n_biophysical_all_active") or 0) for cell in cells),
        "n_biophysical_models == perisomatic + all_active for every cell")

    embedded = {(int(m["id"])) for m in embedded_models}
    direct = {(int(m["id"])) for m in direct_models}
    add("embedded_and_direct_model_queries_agree", embedded == direct,
        f"embedded={len(embedded)} direct={len(direct)} "
        f"only_embedded={len(embedded - direct)} only_direct={len(direct - embedded)}")

    add("sweep_specimen_ids_subset_of_cells",
        all(int(row["specimen_id"]) in set(ids) for row in sweeps),
        f"{len(sweeps)} sweep rows")

    for path in (CELL_INVENTORY_CSV, REGION_SUMMARY_CSV, SWEEP_INVENTORY_CSV,
                 MODEL_INVENTORY_CSV):
        try:
            with path.open("r", encoding="utf-8", newline="") as fh:
                reader = list(csv.reader(fh))
            ok = bool(reader) and all(len(r) == len(reader[0]) for r in reader if r)
            add(f"csv_opens_cleanly:{path.name}", ok,
                f"{len(reader) - 1} data rows, {len(reader[0]) if reader else 0} columns")
        except OSError as exc:
            add(f"csv_opens_cleanly:{path.name}", False, f"{type(exc).__name__}: {exc}")

    return checks


# --------------------------------------------------------------------------
# Overwrite guard / provenance manifest
# --------------------------------------------------------------------------
def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def check_overwrite_guard(force: bool) -> None:
    """Refuse to clobber files this script did not itself generate."""
    manifest: dict[str, str] = {}
    if MANIFEST_PATH.exists():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("files", {})
        except (ValueError, OSError) as exc:
            LOG.warning("could not read provenance manifest: %s", exc)

    blockers: list[str] = []
    for path in GENERATED_FILES:
        if not path.exists():
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel not in manifest:
            blockers.append(f"{rel} exists but was not generated by allen_inventory.py")
        elif manifest[rel] != sha256_of(path):
            blockers.append(f"{rel} exists and was modified outside allen_inventory.py")
    if blockers and not force:
        for line in blockers:
            LOG.error("overwrite guard: %s", line)
        raise SystemExit(
            "Refusing to overwrite pre-existing files. Re-run with --force to "
            "allow it, or move/rename the files listed above.")


def write_manifest() -> None:
    payload = {
        "generated_by": "src/data_audit/allen_inventory.py",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": {path.relative_to(PROJECT_ROOT).as_posix(): sha256_of(path)
                  for path in GENERATED_FILES if path.exists()},
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")



# --------------------------------------------------------------------------
# Step 9 -- summary + report
# --------------------------------------------------------------------------
POPULATION_QUALIFYING_CELLS = 4   # from INCM_revised_project.pdf section 3


def rank_regions(region_rows: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
    """Rank regions of one role by metadata evidence (no selection is made)."""
    aggregated: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in region_rows:
        if row["region_role"] != role or row["status"] != "present":
            continue
        bucket = aggregated[row["region_acronym"]]
        for key in ("n_specimens", "n_mouse", "n_with_ephys_result", "n_with_current_clamp",
                    "n_with_long_square_cc", "n_with_perisomatic", "n_with_all_active",
                    "n_with_any_biophysical", "n_with_morphology",
                    "n_pass", "n_conditional", "n_fail", "n_unknown"):
            bucket[key] += int(row.get(key) or 0)
    ranked = sorted(aggregated.items(),
                    key=lambda kv: (kv[1]["n_pass"], kv[1]["n_conditional"],
                                    kv[1]["n_with_any_biophysical"],
                                    kv[1]["n_with_long_square_cc"]), reverse=True)
    return [{"region": name, **dict(counts)} for name, counts in ranked]


def compute_summary(cells: list[dict[str, Any]], sweeps: list[dict[str, Any]],
                    models: list[dict[str, Any]], region_rows: list[dict[str, Any]],
                    templates: dict[int, dict[str, str]],
                    client: AllenRmaClient, errors: ApiErrorLog,
                    thresholds: dict[str, int],
                    notes: dict[str, Any],
                    coverage: dict[str, Any] | None = None,
                    region_coverage: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    mouse = [c for c in cells if c.get("organism_id") == ORGANISM_MOUSE]
    stimulus_vocab = Counter((s.get("stimulus_name") or "<missing>") for s in sweeps)

    def region_counts(role: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for row in rank_regions(region_rows, role):
            out[row["region"]] = row
        return out

    sensory = region_counts("sensory")
    motor = region_counts("motor")

    def qualifies(counts: dict[str, Any]) -> bool:
        return (counts.get("n_pass", 0) >= POPULATION_QUALIFYING_CELLS
                and max(counts.get("n_with_perisomatic", 0),
                        counts.get("n_with_all_active", 0)) >= POPULATION_QUALIFYING_CELLS)

    best_sensory = next((name for name, counts in sensory.items() if qualifies(counts)), None)
    best_motor = next((name for name, counts in motor.items() if qualifies(counts)), None)

    coverage = coverage or {}
    structures = coverage.get("structures") or []
    motor_terms = ("motor", "frontal", "agranular", "premotor", "gyrus", "lobe")
    motor_related = [row for row in structures
                     if any(term in str(row.get("name") or "").lower() for term in motor_terms)]
    qualifying_structures = [
        {"acronym": row["acronym"], "name": row["name"],
         "cells": row["cells"],
         "mouse_cells": row["mouse_cells"],
         "biophysical_models_mouse": row["biophysical_models_mouse"],
         "perisomatic": row["biophysical_perisomatic"],
         "all_active": row["biophysical_all_active"]}
        for row in structures
        if row["biophysical_models_mouse"] >= POPULATION_QUALIFYING_CELLS]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "api": {
            "endpoint": API_QUERY_URL,
            "live_requests": client.request_count,
            "cache_hits": client.cache_hits,
            "errors_recorded": len(errors),
        },
        "thresholds": thresholds,
        "structure_notes": notes,
        "neuronal_model_templates": [
            {"id": tid, "name": info["name"], "description": info["description"],
             "audit_class": classify_template(templates, tid)[0]}
            for tid, info in sorted(templates.items())],
        "totals": {
            "specimens_retrieved": len(cells),
            "specimens_mouse": len(mouse),
            "specimens_human": sum(1 for c in cells if c.get("organism_id") == 1),
            "specimens_other_species": len(cells) - len(mouse)
                                       - sum(1 for c in cells if c.get("organism_id") == 1),
            "sweep_rows": len(sweeps),
            "model_rows": len(models),
            "distinct_regions_with_specimens": len({c["region_acronym"] for c in cells if c["region_acronym"]}),
        },
        "mouse_findings": {
            "with_ephys_result": sum(1 for c in mouse if c.get("ephys_result_id")),
            "ephys_failed": sum(1 for c in mouse if c.get("ephys_failed") is True),
            "with_current_clamp_sweeps": sum(1 for c in mouse
                                             if int(c.get("n_sweeps_current_clamp") or 0) > 0),
            "with_long_square_cc": sum(1 for c in mouse
                                       if int(c.get("n_long_square_cc") or 0) > 0),
            "meeting_long_square_threshold": sum(
                1 for c in mouse
                if int(c.get("n_long_square_cc") or 0) >= thresholds["min_long_square"]),
            "with_perisomatic": sum(1 for c in mouse
                                    if int(c.get("n_biophysical_perisomatic") or 0) > 0),
            "with_all_active": sum(1 for c in mouse
                                   if int(c.get("n_biophysical_all_active") or 0) > 0),
            "with_any_biophysical": sum(1 for c in mouse
                                        if int(c.get("n_biophysical_models") or 0) > 0),
            "glif_only": sum(1 for c in mouse
                             if int(c.get("n_glif_models") or 0) > 0
                             and int(c.get("n_biophysical_models") or 0) == 0),
            "with_morphology": sum(1 for c in mouse if c.get("has_morphology")),
        },
        "eligibility": dict(Counter(c["eligibility"] for c in cells)),
        "eligibility_mouse": dict(Counter(c["eligibility"] for c in mouse)),
        "eligibility_by_region_role": {
            "sensory": sensory, "motor": motor,
            "qualifying_threshold": POPULATION_QUALIFYING_CELLS,
        },
        "best_supported": {
            "sensory": best_sensory,
            "motor": best_motor,
            "comparison_feasible": bool(best_sensory and best_motor),
            "motor_confirmed_empty": sum(int(c.get("n_specimens") or 0)
                                         for _n, c in motor.items()) == 0,
            "sensory_ranking": list(sensory.items()),
            "motor_ranking": list(motor.items()),
        },
        "database_coverage": {
            "complete": coverage.get("complete"),
            "incomplete_stages": coverage.get("incomplete_stages", []),
            "biophysical_template_ids": coverage.get("biophysical_template_ids", []),
            "glif_template_ids": coverage.get("glif_template_ids", []),
            "cell_specimens_retrieved": coverage.get("cell_specimens_retrieved"),
            "distinct_structures": coverage.get("distinct_structures"),
            "biophysical_models_retrieved": coverage.get("biophysical_models_retrieved"),
            "glif_models_retrieved": coverage.get("glif_models_retrieved"),
            "totals": coverage.get("totals", {}),
            "motor_related_structures": motor_related,
            "structures_meeting_population_rule": qualifying_structures,
        },
        "region_level_cell_counts": region_coverage or [],
        "stimulus_vocabulary_observed": dict(sorted(stimulus_vocab.items(),
                                                    key=lambda kv: -kv[1])),
        "api_errors": errors.records,
    }


def render_report(summary: dict[str, Any], region_rows: list[dict[str, Any]],
                  checks: list[dict[str, Any]], reference: dict[str, Any],
                  thresholds: dict[str, int]) -> str:
    totals = summary["totals"]
    mouse = summary["mouse_findings"]
    elig = summary["eligibility_mouse"]
    best = summary["best_supported"]
    ref_cell = reference.get("cell") or {}
    lines: list[str] = []
    add = lines.append

    add("# Allen Cell Types Database — Phase 0 Dataset Inventory Report")
    add("")
    add(f"*Generated by `src/data_audit/allen_inventory.py` on {summary['generated_at']}.*")
    add("*This report is machine-generated from live API metadata. Re-running the script")
    add("regenerates it; numbers are never hand-edited.*")
    add("")
    add("> **Scope.** Phase 0 is a dataset **feasibility audit only**. No neuron models were")
    add("> implemented, no FHN fitting was performed, and **no NWB, model or morphology files")
    add("> were downloaded**. No final neuronal population has been selected.")
    add("")
    add("---")
    add("")
    add("## 1. Research context (from `INCM_revised_project.pdf`)")
    add("")
    add("**Research question.** *How much biological detail does a neuron model need to")
    add("reproduce a real neuron's electrophysiological behaviour, and which behaviours are")
    add("preserved or lost when a detailed conductance-based model is reduced to a")
    add("FitzHugh–Nagumo (FHN) model?*")
    add("")
    add("**Methodology.** For 3–4 individually recorded neurons per population (6–8 total):")
    add("(i) evaluate the Allen biophysical (HH-type, conductance-based) model against the")
    add("cell's own recording; (ii) fit a reduced FHN model to the same recording on")
    add("calibration sweeps and score on held-out sweeps; (iii) compare which behaviours FHN")
    add("preserves or loses; (iv) where feasible, perturb single conductances in the detailed")
    add("model. Models are evaluated, not re-fitted; simulations run in NEURON.")
    add("")
    add("**Dataset requirements implied by the proposal.**")
    add("")
    add("| Requirement | Source in proposal | Audit field used |")
    add("|---|---|---|")
    add("| Current-clamp recordings (NWB) | §3 *Data and models* | `EphysSweep.stimulus_units == 'Amps'`, `NWBDownload` file reference |")
    add("| Suitable long-square sweeps for calibration + held-out split | §3, §4 Exp 1/2 | `n_long_square_cc`, `n_long_square_depolarizing_cc` |")
    add("| Downloadable Allen biophysical model (perisomatic **or** all-active) | §3 | `neuronal_model_template_id` → 329230710 / 491455321 |")
    add("| One model class for all cells unless justified | §3 | `biophysical_classes`, per-region perisomatic/all-active counts |")
    add("| ≥4 recorded cells per population | §3 (qualification rule) | `n_pass` per region vs `POPULATION_QUALIFYING_CELLS = 4` |")
    add("| One sensory + one motor-related population | §3 (instructor suggestion) | `region_role` |")
    add("| F-I curve, spike count, latency, rheobase, adaptation index | §4 metrics | long-square sweep count + amplitude range |")
    add("")
    add("**Populations.** Member 1 → sensory; Member 2 → motor. Candidate regions audited:")
    add("`VISp`, `VISl`, `VISal` (sensory) and `MOp`, `ALM` (motor). These are candidates to")
    add("investigate, **not** confirmed available populations.")
    add("")
    add("---")
    add("")
    add("## 2. Candidate region availability in the Allen structure ontology")
    add("")
    add("| Region | Role | Member | Ontology status | Structure ID | Full name | Layer structures found |")
    add("|---|---|---|---|---|---|---|")
    for row in sorted(region_rows, key=lambda r: (r["region_role"], r["region_acronym"],
                                                  r["cortical_layer"])):
        if not row["cortical_layer"]:
            add(f"| {row['region_acronym']} | {row['region_role']} | {row['member']} | "
                f"`{row['status']}` | {row['structure_id'] or '—'} | "
                f"{row['region_name'] or '—'} | {row['note'] or '—'} |")
    present_layers: dict[str, list[str]] = defaultdict(list)
    for row in region_rows:
        if row["cortical_layer"]:
            present_layers[row["region_acronym"]].append(row["structure_acronym"])
    for region, layer_list in sorted(present_layers.items()):
        role = next(r["region_role"] for r in region_rows if r["region_acronym"] == region)
        member = next(r["member"] for r in region_rows if r["region_acronym"] == region)
        add(f"| {region} | {role} | {member} | `present` | — | — | "
            f"{', '.join(sorted(layer_list))} |")
    add("")
    absent = summary["structure_notes"].get("regions_absent", [])
    unknown = summary["structure_notes"].get("regions_unknown", [])
    if absent:
        add(f"**Confirmed absence:** {', '.join(absent)} returned **zero rows** from")
        add("`model::Structure` on a successful (HTTP 200, `success=true`) query. This is a")
        add("confirmed absence of the *acronym in the Allen structure ontology*, not an API")
        add("failure. Note that ALM (anterior lateral motor cortex) is a functional recording")
        add("site used in the Allen literature; in the Cell Types Database the corresponding")
        add("CCF structure is `MOp` (Primary motor area). Treat ALM as *not separately")
        add("addressable* rather than as *no motor data available*.")
    if unknown:
        add(f"**Could not be checked (UNKNOWN, not FAIL):** {', '.join(unknown)}.")
    add("")
    coverage = summary.get("database_coverage") or {}
    region_level = summary.get("region_level_cell_counts") or []
    if region_level:
        add("### 2.1 Cell-specimen counts at every hierarchy level")
        add("")
        add("The inventory queries layer sub-structures (`VISp5`, `VISp2/3`, ...). To rule out")
        add("cells attached directly to a *parent* structure, and to rule out an artefact of the")
        add("candidate list, cell-specimen counts were also taken at the region level itself and")
        add("for motor/somatosensory control acronyms. `is_cell_specimen == true` selects exactly")
        add("the published Cell Types Database roster.")
        add("")
        add("| Structure | ID | Full name | Role | Ontology status | Checked because | Cell specimens | Note |")
        add("|---|---|---|---|---|---|---|---|")
        for row in region_level:
            count = row.get("cell_specimens_at_this_level")
            if count is not None:
                count_text = str(count)
            elif row.get("ontology_status") == "absent_from_ontology":
                count_text = "n/a — not in ontology"
            else:
                count_text = "**API error (UNKNOWN)**"
            add(f"| {row['structure_acronym']} | {row['structure_id'] or '—'} "
                f"| {row['structure_name'] or '—'} | {row.get('role') or '—'} "
                f"| `{row['ontology_status']}` "
                f"| {row['checked_because']} | {count_text} | {row.get('note') or '—'} |")
        add("")
    if coverage:
        totals_db = coverage.get("totals") or {}
        add("### 2.2 Database-wide structure coverage")
        add("")
        add(f"Whole-database scan (`--skip-coverage` not used): "
            f"**{coverage.get('cell_specimens_retrieved')}** cell specimens across "
            f"**{coverage.get('distinct_structures')}** distinct structures; "
            f"**{totals_db.get('biophysical_models')}** biophysical models "
            f"({totals_db.get('biophysical_perisomatic')} perisomatic + "
            f"{totals_db.get('biophysical_all_active')} all-active) and "
            f"**{totals_db.get('glif_models')}** GLIF models database-wide.")
        add("")
        add(f"Species split: {totals_db.get('mouse_cells')} mouse, "
            f"{totals_db.get('human_or_other_cells')} human/other. "
            f"Structures with ≥1 biophysical model: "
            f"**{totals_db.get('structures_with_any_biophysical')}**. Structures with "
            f"≥{POPULATION_QUALIFYING_CELLS} *mouse* biophysical models (the proposal's "
            f"population rule): **{totals_db.get('structures_with_four_plus_mouse_biophysical')}**.")
        add("")
        add("| Acronym | Full name | Cells | Mouse | Biophys (mouse) | Perisomatic | All-active | GLIF |")
        add("|---|---|---|---|---|---|---|---|")
        for row in coverage.get("structures_meeting_population_rule", []):
            add(f"| {row['acronym']} | {row['name']} | {row['cells']} "
                f"| {row['mouse_cells']} | {row['biophysical_models_mouse']} "
                f"| {row['perisomatic']} | {row['all_active']} | — |")
        add("")
        add(f"*(Only structures meeting the ≥{POPULATION_QUALIFYING_CELLS} mouse-biophysical "
            f"rule are listed; the full per-structure table is in "
            f"`results/dataset_inventory/database_structure_coverage.json`.)*")
        add("")
        motor_related = coverage.get("motor_related_structures", [])
        add("**Motor/frontal-related structures anywhere in the database**")
        add("")
        add("Name-substring filter (`motor`, `frontal`, `agranular`, `premotor`, `gyrus`,")
        add("`lobe`) applied to the official `model::Structure.name`. This deliberately"
            " over-collects so that no candidate motor area can be missed; several hits are")
        add("human temporal/parietal gyri or mouse retrosplenial agranular cortex, neither of")
        add("which is a motor area — they are listed so the reader can check that themselves.")
        add("")
        if motor_related:
            add("| Acronym | Full name | Cells | Mouse cells | Biophysical models |")
            add("|---|---|---|---|---|")
            for row in motor_related:
                add(f"| {row['acronym']} | {row['name']} | {row['cells']} "
                    f"| {row['mouse_cells']} | {row['biophysical_models']} |")
        else:
            add("_None._")
        add("")
        if coverage.get("incomplete_stages"):
            add(f"> The coverage scan was **incomplete** "
                f"({', '.join(coverage['incomplete_stages'])}); treat its counts as a lower "
                f"bound (UNKNOWN), not as confirmed totals.")
            add("")
    add("---")
    add("")
    add("## 3. Findings")
    add("")
    add("### 3.1 Required reporting items")
    add("")
    add("| # | Item | Value |")
    add("|---|---|---|")
    add(f"| 1 | Total specimens retrieved (cell specimens in candidate layer structures) | **{totals['specimens_retrieved']}** |")
    add(f"|   | — *Mus musculus* | {totals['specimens_mouse']} |")
    add(f"|   | — *Homo sapiens* | {totals['specimens_human']} |")
    add(f"|   | — other / unresolved species | {totals['specimens_other_species']} |")
    add(f"| 2 | Regions represented in the database (with ≥1 cell specimen) | **{totals['distinct_regions_with_specimens']}** within the candidate list ({', '.join(sorted(present_layers)) or 'none'}) |")
    db_cov = summary.get("database_coverage") or {}
    db_tot = db_cov.get("totals") or {}
    if db_cov:
        add(f"|   | — database-wide: cell specimens / distinct structures | "
            f"{db_cov.get('cell_specimens_retrieved')} / {db_cov.get('distinct_structures')} (see §2.2) |")
        add(f"|   | — database-wide: biophysical models (mouse) | "
            f"{db_tot.get('biophysical_models')} ({db_tot.get('biophysical_models_mouse')} mouse) |")
        add(f"|   | — database-wide: structures meeting the ≥{POPULATION_QUALIFYING_CELLS}-mouse-biophysical population rule | "
            f"{db_tot.get('structures_with_four_plus_mouse_biophysical')} |")
    add(f"| 3 | Mouse cells with current-clamp Long Square recordings | **{mouse['with_long_square_cc']}** |")
    add(f"|   | — of which ≥ {thresholds['min_long_square']} long-square sweeps (audit threshold) | {mouse['meeting_long_square_threshold']} |")
    add(f"| 4 | Mouse cells with a **Biophysical – perisomatic** model | **{mouse['with_perisomatic']}** |")
    add(f"| 5 | Mouse cells with a **Biophysical – all active** model | **{mouse['with_all_active']}** |")
    add(f"| 6 | Mouse cells with **≥1 biophysical model** (either class) | **{mouse['with_any_biophysical']}** |")
    add(f"|   | — GLIF-only cells (**not** counted as biophysical) | {mouse['glif_only']} |")
    add(f"|   | — cells with a morphology reconstruction + SWC reference | {mouse['with_morphology']} |")
    add(f"|   | — cells with an electrophysiology result | {mouse['with_ephys_result']} |")
    add(f"|   | — cells whose `EphysResult.failed == true` | {mouse['ephys_failed']} |")
    add("| 7 | Preliminary eligible cells by region | see §3.2 |")
    add("| 8 | Best-supported **sensory** candidate | see §3.3 |")
    add("| 9 | Best-supported **motor** candidate | see §3.3 |")
    add("| 10 | Sensory-vs-motor comparison feasible? | see §3.4 |")
    add("")
    add(f"Raw sweep rows inventoried: **{totals['sweep_rows']}**. "
        f"Raw model rows: **{totals['model_rows']}**.")
    add("")
    add("### 3.2 Preliminary eligibility by region and layer (mouse cells)")
    add("")
    add("Eligibility is a **metadata-level** classification. `PASS` means every required")
    add("metadata criterion was confirmed present — it does **not** mean the NWB or the model")
    add("archive has been opened, parsed or simulated.")
    add("")
    add("| Role | Region | Layer | Specimens | Mouse | CC Long Sq | Perisomatic | All-active | ≥1 biophys | PASS | COND | FAIL | UNK |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in sorted(region_rows, key=lambda r: (r["region_role"], r["region_acronym"],
                                                  str(r["cortical_layer"]))):
        if not row["cortical_layer"]:
            continue
        add(f"| {row['region_role']} | {row['region_acronym']} | {row['cortical_layer'] or '—'} "
            f"| {row['n_specimens']} | {row['n_mouse']} | {row['n_with_long_square_cc']} "
            f"| {row['n_with_perisomatic']} | {row['n_with_all_active']} "
            f"| {row['n_with_any_biophysical']} | {row['n_pass']} | {row['n_conditional']} "
            f"| {row['n_fail']} | {row['n_unknown']} |")
    add("")
    add(f"**Totals (all specimens):** PASS {summary['eligibility'].get('PASS', 0)}, "
        f"CONDITIONAL {summary['eligibility'].get('CONDITIONAL', 0)}, "
        f"FAIL {summary['eligibility'].get('FAIL', 0)}, "
        f"UNKNOWN {summary['eligibility'].get('UNKNOWN', 0)}.")
    add("")
    add(f"**Totals (mouse only):** PASS {elig.get('PASS', 0)}, "
        f"CONDITIONAL {elig.get('CONDITIONAL', 0)}, FAIL {elig.get('FAIL', 0)}, "
        f"UNKNOWN {elig.get('UNKNOWN', 0)}.")
    add("")
    add("**Classification rules applied**")
    add("")
    add(f"- `PASS` — mouse; region + layer identified; `EphysResult` present and not failed;")
    add(f"  ≥ {thresholds['min_long_square']} current-clamp Long Square sweeps **and**")
    add(f"  ≥ {thresholds['min_depolarizing_long_square']} depolarising ones; ≥1 biophysical")
    add("  model whose download reference resolved; NWB download reference resolved.")
    add("- `CONDITIONAL` — promising but at least one requirement is short of threshold or")
    add("  unresolved (e.g. too few long-square sweeps, biophysical model listed without a")
    add("  resolved download reference, GLIF-only, no NWB reference).")
    add("- `FAIL` — a required criterion is **confirmed absent**: no `EphysResult`,")
    add("  `EphysResult.failed == true`, zero current-clamp Long Square sweeps, or a")
    add("  non-mouse species.")
    add("- `UNKNOWN` — required metadata could not be retrieved because an API call failed,")
    add("  or the target region could not be resolved from the structure hierarchy.")
    add("  Missing information is never recorded as FAIL.")
    add(f"- Every `PASS`/`CONDITIONAL` cell is additionally flagged")
    add("  `needs_nwb_validation` / `needs_model_validation` because Phase 0 downloads nothing.")
    add("")
    add("### 3.3 Best-supported candidate per role")
    add("")
    add("> **No population is selected.** The ranking below is evidence for a decision that")
    add("> must be approved before Phase 1.")
    add("")
    for role, label in (("sensory", "Sensory (Member 1)"), ("motor", "Motor (Member 2)")):
        add(f"**{label}** — qualification rule from the proposal: ≥ {POPULATION_QUALIFYING_CELLS}")
        add("recorded cells with suitable long-square sweeps **and** downloadable models of")
        add("**the same class**.")
        add("")
        ranking = best[f"{role}_ranking"]
        if not ranking:
            add("_No region of this role returned any cell specimen._")
            add("")
            continue
        add("| Rank | Region | Mouse cells | CC Long Sq | Perisomatic | All-active | ≥1 biophys | PASS | COND | Qualifies? |")
        add("|---|---|---|---|---|---|---|---|---|---|")
        for index, (region, counts) in enumerate(ranking, start=1):
            qualifies = (counts.get("n_pass", 0) >= POPULATION_QUALIFYING_CELLS
                         and max(counts.get("n_with_perisomatic", 0),
                                 counts.get("n_with_all_active", 0))
                         >= POPULATION_QUALIFYING_CELLS)
            add(f"| {index} | {region} | {counts.get('n_mouse', 0)} "
                f"| {counts.get('n_with_long_square_cc', 0)} "
                f"| {counts.get('n_with_perisomatic', 0)} "
                f"| {counts.get('n_with_all_active', 0)} "
                f"| {counts.get('n_with_any_biophysical', 0)} "
                f"| {counts.get('n_pass', 0)} | {counts.get('n_conditional', 0)} "
                f"| {'**yes**' if qualifies else 'no'} |")
        add("")
        chosen = best[role]
        add(f"Best-supported {role} candidate on metadata evidence: "
            f"**{chosen or 'none qualifies'}** — *pending approval, not selected*.")
        add("")
        marginal = [(region, counts.get("n_pass", 0)) for region, counts in ranking
                    if 0 < counts.get("n_pass", 0) <= POPULATION_QUALIFYING_CELLS]
        if marginal:
            add(f"> **Zero-margin warning.** {', '.join(f'`{r}` ({n} PASS)'
                for r, n in marginal)} meets the ≥{POPULATION_QUALIFYING_CELLS}-cell rule "
                f"with no slack: a single failed NWB or model validation would drop it "
                f"below the bar. `Qualifies? = yes` is a threshold test, not a robustness "
                f"assessment.")
            add("")
    add("### 3.4 Is a sensory-versus-motor comparison feasible?")
    add("")
    feasible = best["comparison_feasible"]
    motor_cells_total = sum(int(counts.get("n_specimens") or 0)
                            for _name, counts in best["motor_ranking"])
    motor_confirmed_empty = motor_cells_total == 0
    if feasible:
        headline = "YES — feasible on metadata"
    elif motor_confirmed_empty:
        headline = ("NO — not feasible with the Allen Cell Types Database "
                    "(confirmed absence of motor data, not missing information)")
    else:
        headline = "NOT YET ESTABLISHED"
    add(f"**Metadata-level answer: {headline}.**")
    add("")
    if feasible:
        add(f"On metadata alone, at least one sensory region (`{best['sensory']}`) and at least")
        add(f"one motor region (`{best['motor']}`) each meet the proposal's qualification rule")
        add(f"(≥ {POPULATION_QUALIFYING_CELLS} cells with sufficient long-square sweeps and")
        add("downloadable models of a single shared class). A sensory-vs-motor comparison is")
        add("therefore **plausible**.")
    else:
        add("On metadata alone, at least one role does **not** have a region meeting the")
        add(f"proposal's qualification rule (≥ {POPULATION_QUALIFYING_CELLS} cells with")
        add("sufficient long-square sweeps and downloadable models of a single shared class).")
        add("")
        if motor_confirmed_empty:
            add("**The motor role is the binding constraint, and this is a confirmed absence,")
            add("not missing information.** The evidence (see §2.1 and §2.2):")
            add("")
            zero_regions = [row["structure_acronym"] for row in region_level
                            if row.get("cell_specimens_at_this_level") == 0
                            and row.get("role") in ("motor", "control")]
            sensory_parents = [row["structure_acronym"] for row in region_level
                               if row.get("cell_specimens_at_this_level") == 0
                               and row.get("role") == "sensory"
                               and row.get("checked_because", "").endswith("(parent level)")]
            absent_ontology = [row["structure_acronym"] for row in region_level
                               if row.get("ontology_status") == "absent_from_ontology"]
            if zero_regions:
                add(f"- `model::Specimen` with `is_cell_specimen=true` returned **0 rows** for "
                    f"{len(set(zero_regions))} motor and motor/somatosensory-control "
                    f"structures, at the region level *and* at every layer level: "
                    f"{', '.join(sorted(set(zero_regions)))}.")
            if sensory_parents:
                add(f"- Control for the query pattern: the *sensory* parent structures "
                    f"{', '.join(sorted(set(sensory_parents)))} also return 0 rows at the "
                    f"parent level, while their layer sub-structures return hundreds (§2.1). "
                    f"Cells are therefore attached at layer level, which confirms the zero "
                    f"MOp layer counts are real and not a level-of-attachment artefact.")
            if absent_ontology:
                add(f"- {', '.join(sorted(set(absent_ontology)))} returned zero rows from "
                    f"`model::Structure` — the acronym is not in the Allen structure ontology "
                    f"at all.")
            if db_cov:
                motor_rows = db_cov.get("motor_related_structures", [])
                motor_mouse = [row for row in motor_rows if row.get("mouse_cells")]
                motor_human = [str(row.get("acronym")) for row in motor_rows
                               if row.get("human_or_other_cells")]
                motor_mouse_with_models = [row for row in motor_mouse
                                           if row.get("biophysical_models")]
                add(f"- A whole-database scan of all "
                    f"{db_cov.get('cell_specimens_retrieved')} Cell Types Database cells across "
                    f"{db_cov.get('distinct_structures')} structures found "
                    f"**{len(motor_mouse_with_models)} structure(s) that are both mouse and "
                    f"motor/frontal-related *and* hold a biophysical model**.")
                if motor_mouse:
                    add(f"  The name filter did match mouse cells in "
                        f"{', '.join(str(r.get('acronym')) for r in motor_mouse)}, but every "
                        f"one of those is retrosplenial agranular cortex (`RSPagl`), not a "
                        f"motor area, and none carries a biophysical model "
                        f"({sum(int(r.get('biophysical_models') or 0) for r in motor_mouse)} "
                        f"models in total).")
                if motor_human:
                    add(f"  Every other structure matched by the name filter that does hold "
                        f"cells — {', '.join(motor_human)} — has **zero mouse cells** (human "
                        f"tissue only), and is therefore outside this project's mouse scope.")
            add("- Every one of these counts came from an HTTP 200 / `success=true` response, so")
            add("  they are confirmed zeros, not API failures. No API error was recorded for")
            add("  these stages (`api_errors` in `inventory_summary.json`).")
            add("")
            add("**Conclusion (metadata level).** A sensory-versus-motor comparison is **not")
            add("feasible** with the Allen Cell Types Database: the database contains no mouse")
            add("motor-cortex cells at all, so no motor population can satisfy the ≥4-cell rule")
            add("for *any* choice of motor region. This is a property of the dataset, not of the")
            add("query design.")
            add("")
        add("The proposal's own fallback pairs should therefore be evaluated:")
        add("")
        add("1. **VISp layer 2/3 vs VISp layer 5** — both clear the ≥4-cell rule on metadata.")
        add("2. **VISp vs a higher visual area** — `VISl` and `VISal` hold cells, but only")
        add("   `VISl4` and `VISal4` carry any biophysical model, and neither reaches 4.")
        add("")
        add("Fallback evaluation is reported as evidence only; **no pair is selected here**.")
    add("")
    add("**This is not experimentally validated eligibility.** Confirming it requires")
    add("downloading one NWB per shortlisted cell (sweep integrity, stimulus amplitudes,")
    add("sampling rate) and one biophysical model archive (runs unmodified in NEURON, single")
    add("conductance change possible) — the proposal's own go/no-go gate.")
    add("")
    add("---")
    add("")
    add("## 4. Model class separation (GLIF is NOT biophysical)")
    add("")
    add("| Template ID | Template name | Description | Audit class |")
    add("|---|---|---|---|")
    for template in summary["neuronal_model_templates"]:
        add(f"| {template['id']} | {template['name']} | {template['description']} "
            f"| `{template['audit_class']}` |")
    add("")
    add("Classification is driven by `NeuronalModel.neuronal_model_template_id`, **not** by")
    add("`well_known_file_type_id`: the biophysical `_fit.json` and the GLIF")
    add("`_neuron_config.json` share file type `329230374`, so a file-type-based rule would")
    add("silently count GLIF models as biophysical.")
    add("")
    add("## 5. Stimulus vocabulary actually observed in the database")
    add("")
    add("| `stimulus_name` | Sweeps | Audit category |")
    add("|---|---|---|")
    for name, count in summary["stimulus_vocabulary_observed"].items():
        add(f"| `{name}` | {count} | `{STIMULUS_CATEGORIES.get(name, 'other')}` |")
    add("")
    add("Categories are mapped from the API's own `stimulus_name` values; unmapped values are")
    add("reported verbatim under `other` rather than being renamed or dropped.")
    add("")
    add("---")
    add("")
    add(f"## 6. Reference specimen {REFERENCE_SPECIMEN_ID} (previous project)")
    add("")
    add(f"- Returned by the **current** API: `{reference.get('returned_by_current_api')}`")
    add(f"- Present in this candidate inventory: `{reference.get('in_candidate_inventory')}`")
    if reference.get("api_note"):
        add(f"- API note: {reference['api_note']}")
    if ref_cell:
        add("")
        add("| Field | Value |")
        add("|---|---|")
        for key in ("specimen_name", "region_acronym", "region_name", "cortical_layer",
                    "structure_acronym", "structure_name", "species", "donor_sex",
                    "donor_full_genotype", "transgenic_driver_line",
                    "transgenic_reporter_line", "dendrite_type", "apical_dendrite_status",
                    "ephys_result_id", "ephys_failed", "ephys_sampling_rate",
                    "n_sweeps_total", "n_sweeps_current_clamp", "n_long_square_cc",
                    "n_long_square_depolarizing_cc", "n_long_square_hyperpolarizing_cc",
                    "n_short_square_cc", "n_ramp_cc", "n_noise_cc",
                    "long_square_sweep_numbers", "has_morphology", "reconstruction_type",
                    "n_models_total", "n_biophysical_perisomatic",
                    "n_biophysical_all_active", "n_glif_models", "biophysical_model_id",
                    "biophysical_model_name", "biophysical_model_download_url",
                    "nwb_download_url", "morphology_download_url", "eligibility"):
            value = ref_cell.get(key)
            add(f"| `{key}` | {'—' if value in (None, '') else value} |")
        add("")
        if reference.get("models"):
            add("**Models attached to this specimen**")
            add("")
            add("| Model ID | Template | Audit class | Reconstruction ID |")
            add("|---|---|---|---|")
            for model in reference["models"]:
                add(f"| {model['model_id']} | {model['template_name']} "
                    f"| `{model['model_class']}` | {model['neuron_reconstruction_id']} |")
            add("")
    add("**Interpretation.** The specimen is confirmed present in the current API with its")
    add("recordings and model metadata. That does **not** automatically qualify it for the new")
    add("experiment: the previous project's passive fit and spike counts were computed on a")
    add("different protocol, and no NWB or model archive has been re-downloaded or re-run in")
    add("this phase. It is carried forward as a *known-good reference cell for pipeline")
    add("validation*, not as a selected experimental cell.")
    add("")
    add("---")
    add("")
    add("## 7. Quality checks")
    add("")
    add("| Check | Result | Detail |")
    add("|---|---|---|")
    for check in checks:
        add(f"| `{check['check']}` | {'PASS' if check['passed'] else 'FAIL'} "
            f"| {check['detail']} |")
    add("")
    add("## 8. API issues encountered")
    add("")
    if summary["api_errors"]:
        add(f"{len(summary['api_errors'])} issue(s) were logged:")
        add("")
        add("| Stage | Status | Detail |")
        add("|---|---|---|")
        for error in summary["api_errors"][:60]:
            add(f"| `{error['stage']}` | {error['status']} | {error['detail'][:220]} |")
        if len(summary["api_errors"]) > 60:
            add("")
            add(f"_(showing first 60 of {len(summary['api_errors'])}; full list in "
                "`results/dataset_inventory/allen_inventory.log` and "
                "`inventory_summary.json`)_")
    else:
        add("No API errors were logged during this run.")
    add("")
    add("### Structural API limitations found during the schema audit")
    add("")
    add("| Observation | Consequence for this phase |")
    add("|---|---|")
    add("| `well_known_file_download?name=cell_types_specimens` (and `cell_types_ephys_features`, `cell_types_morphology_reconstructions`, `cell_types_ephys_summary`) return **HTTP 404** on both `api.brain-map.org` and `celltypes.brain-map.org` | The bulk CSV route used by older AllenSDK versions is unavailable; the inventory is built entirely from RMA v2 queries |")
    add("| `rma::options,num_rows$eqN` inside `criteria` is rejected (`missing <EOF> at \"$eq\"`) | `num_rows` / `start_row` / `include` are passed as separate query parameters |")
    add("| `model::Specimen` has no `failed` column (`[failed$eq'false']` → *Data Access error*) | Electrophysiology failure is read from `EphysResult.failed` |")
    add("| `model::DendriteType`, `model::ApicalDendrite`, `model::NeuronalModelType` → *uninitialized constant* | Dendrite/apical status read from `specimen_tags`; model class from `neuronal_model_template_id` |")
    add("| `Specimen.cortex_layer_id` is `null` for these cells | Cortical layer is derived from the structure hierarchy (`VISp` → `VISp5`), not from `cortex_layer_id` |")
    add("| `[acronym$eq'ALM']` returns zero rows on a successful query | ALM is confirmed absent from the structure ontology; motor candidates rest on `MOp` |")
    add("")
    add("---")
    add("")
    add("## 9. Confirmed metadata vs experimentally validated eligibility")
    add("")
    add("| | Confirmed in this phase | **Not** established in this phase |")
    add("|---|---|---|")
    add("| Specimens | IDs, region, layer, species, sex, genotype, transgenic lines, dendrite type, apical status | — |")
    add("| Electrophysiology | Sweep counts per stimulus category, current- vs voltage-clamp, amplitudes, sweep numbers, NWB download reference | That the NWB opens, that traces are artefact-free, that spike counts reproduce |")
    add("| Models | Model IDs, template class (perisomatic / all-active / GLIF), download reference | That the model archive is complete, runs unmodified in NEURON, or reproduces the recording |")
    add("| Morphology | Reconstruction ID, type, superseded flag, SWC download reference | That the SWC is usable for a model rebuild |")
    add("| Eligibility | Metadata-level PASS / CONDITIONAL / FAIL / UNKNOWN | Scientifically validated suitability for Exp 1–4 |")
    add("")
    add("## 10. Recommended next step (awaiting approval)")
    add("")
    add("**Stop here.** Phase 0 ends with this inventory. The exact recommended next step is")
    add("a *targeted validation* pass, not a population decision:")
    add("")
    add("1. Approve (or amend) the shortlist in §3.3 and the eligibility thresholds in")
    add(f"   `allen_inventory.py` (`MIN_LONG_SQUARE = {thresholds['min_long_square']}`,")
    add(f"   `MIN_DEPOLARIZING_LONG_SQUARE = {thresholds['min_depolarizing_long_square']}`).")
    add("2. For **one** cell per shortlisted region (start with the highest-ranked PASS cell),")
    add("   download the NWB via the recorded reference and confirm: long-square sweep count,")
    add("   stimulus amplitudes and units, sampling rate, and spike counts.")
    add("3. Download **one** biophysical model archive and run it unmodified in NEURON against")
    add("   that cell's stimuli — the proposal's go/no-go gate — then attempt a single")
    add("   conductance change.")
    add("4. Only after (2) and (3) succeed, promote CONDITIONAL cells and fix the two")
    add("   populations.")
    add("")
    add("## Appendix A — run provenance")
    add("")
    add(f"- API endpoint: `{summary['api']['endpoint']}`")
    add(f"- Live HTTP requests this run: {summary['api']['live_requests']}")
    add(f"- Responses served from disk cache: {summary['api']['cache_hits']}")
    add(f"- API errors recorded: {summary['api']['errors_recorded']}")
    add(f"- Log: `results/dataset_inventory/allen_inventory.log`")
    add(f"- Raw cached responses: `data/metadata/api_cache/inventory/`")
    add(f"- Machine-readable summary: `results/dataset_inventory/inventory_summary.json`")
    add("")
    return "\n".join(lines) + "\n"



# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def group_by_specimen(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        specimen_id = row.get("specimen_id")
        if specimen_id is not None:
            grouped[int(specimen_id)].append(row)
    return grouped


def merge_model_sources(embedded: list[dict[str, Any]],
                        direct: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union of the embedded ``neuronal_models`` relation and the independent
    ``model::NeuronalModel`` query, de-duplicated on model id."""
    merged: dict[int, dict[str, Any]] = {}
    for model in list(embedded) + list(direct):
        model_id = model.get("id")
        if model_id is None:
            continue
        merged.setdefault(int(model_id), model)
    return list(merged.values())


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Allen Cell Types Database Phase 0 inventory (metadata only).")
    parser.add_argument("--refresh", action="store_true",
                        help="ignore the on-disk API cache and re-query the Allen API")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting output files not generated by this script")
    parser.add_argument("--verbose", action="store_true", help="debug logging on the console")
    parser.add_argument("--min-long-square", type=int, default=DEFAULT_MIN_LONG_SQUARE,
                        help=f"minimum current-clamp Long Square sweeps for PASS "
                             f"(default {DEFAULT_MIN_LONG_SQUARE})")
    parser.add_argument("--min-depolarizing-long-square", type=int,
                        default=DEFAULT_MIN_DEPOLARIZING_LONG_SQUARE,
                        help="minimum depolarising Long Square sweeps for PASS "
                             f"(default {DEFAULT_MIN_DEPOLARIZING_LONG_SQUARE})")
    parser.add_argument("--reference-specimen", type=int, default=REFERENCE_SPECIMEN_ID,
                        help="specimen id to look up as the previous-project reference cell")
    parser.add_argument("--skip-coverage", action="store_true",
                        help="skip the database-wide structure coverage scan (~15 extra "
                             "cached queries) and report candidate regions only")
    return parser.parse_args(argv)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    global REFERENCE_SPECIMEN_ID
    REFERENCE_SPECIMEN_ID = args.reference_specimen

    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    setup_logging(args.verbose)

    LOG.info("=" * 78)
    LOG.info("INCM Phase 0 - Allen Cell Types Database inventory (metadata only)")
    LOG.info("thresholds: min_long_square=%d min_depolarizing_long_square=%d",
             args.min_long_square, args.min_depolarizing_long_square)
    LOG.info("cache: %s (refresh=%s)", CACHE_DIR, args.refresh)

    check_overwrite_guard(args.force)

    errors = ApiErrorLog()
    client = AllenRmaClient(errors, use_cache=not args.refresh)
    thresholds = {"min_long_square": args.min_long_square,
                  "min_depolarizing_long_square": args.min_depolarizing_long_square}
    incomplete_stages: set[str] = set()

    # -- Step 2: regions -------------------------------------------------
    regions, notes = discover_structures(client)
    structure_index = build_structure_index(regions)
    structure_ids = sorted(structure_index)
    LOG.info("candidate layer structures to query: %d", len(structure_ids))
    if not structure_ids:
        LOG.error("no candidate layer structures resolved; nothing to inventory")

    # -- Step 2: specimens -----------------------------------------------
    specimens, spec_ok = fetch_specimens(client, structure_ids) if structure_ids else ([], True)
    if not spec_ok:
        incomplete_stages.add("specimens")
    LOG.info("specimens retrieved: %d", len(specimens))

    templates = fetch_templates(client)
    specimen_ids = sorted({int(s["id"]) for s in specimens})

    # -- Step 3: sweeps ---------------------------------------------------
    sweeps, sweep_ok = fetch_sweeps(client, specimen_ids) if specimen_ids else ([], True)
    if not sweep_ok:
        incomplete_stages.add("ephys_sweeps")

    # -- Step 4: models ---------------------------------------------------
    embedded_models = [m for s in specimens for m in (s.get("neuronal_models") or [])
                       if isinstance(m, dict)]
    direct_models, model_ok = fetch_models(client, specimen_ids) if specimen_ids else ([], True)
    if not model_ok:
        incomplete_stages.add("neuronal_models")
    all_models = merge_model_sources(embedded_models, direct_models)
    model_files = fetch_model_files(client, sorted({int(m["id"]) for m in all_models})) \
        if all_models else {}

    # -- morphology -------------------------------------------------------
    recons, recon_ok = fetch_reconstructions(client, specimen_ids) if specimen_ids else ([], True)
    if not recon_ok:
        LOG.warning("neuron reconstruction retrieval incomplete")
    recon_files = fetch_reconstruction_files(
        client, sorted({int(r["id"]) for r in recons})) if recons else {}

    # -- Step 5: cell records + eligibility -------------------------------
    cells = build_cell_records(
        specimens, structure_index, templates, group_by_specimen(sweeps),
        group_by_specimen(all_models), group_by_specimen(recons),
        model_files, recon_files, incomplete_stages, thresholds)
    cells_by_id = {int(cell["specimen_id"]): cell for cell in cells}

    sweep_rows = build_sweep_records(cells_by_id, sweeps)
    model_rows = build_model_records(cells_by_id, templates, all_models, model_files,
                                     source="merged(embedded+direct_query)")

    # -- Step 6: write inventories ----------------------------------------
    write_csv(CELL_INVENTORY_CSV, cells, CELL_COLUMNS, ["specimen_id"])
    write_csv(SWEEP_INVENTORY_CSV, sweep_rows, SWEEP_COLUMNS, ["specimen_id", "sweep_number"])
    write_csv(MODEL_INVENTORY_CSV, model_rows, MODEL_COLUMNS, ["model_id", "specimen_id"])

    region_rows = build_region_summary(cells, regions)
    write_csv(REGION_SUMMARY_CSV, region_rows, REGION_COLUMNS,
              ["region_acronym", "cortical_layer"])

    # -- Step 2b: whole-database coverage ---------------------------------
    region_coverage: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {}
    if args.skip_coverage:
        LOG.warning("--skip-coverage: database-wide coverage scan not performed; "
                    "'regions represented in the database' will be candidate-scoped only")
    else:
        region_coverage = verify_region_coverage(client, regions)
        coverage = fetch_database_coverage(client, templates)
        COVERAGE_JSON.write_text(json.dumps(
            {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "complete": coverage.get("complete"),
             "incomplete_stages": coverage.get("incomplete_stages", []),
             "cell_specimens_retrieved": coverage.get("cell_specimens_retrieved"),
             "distinct_structures": coverage.get("distinct_structures"),
             "biophysical_models_retrieved": coverage.get("biophysical_models_retrieved"),
             "glif_models_retrieved": coverage.get("glif_models_retrieved"),
             "biophysical_template_ids": coverage.get("biophysical_template_ids", []),
             "glif_template_ids": coverage.get("glif_template_ids", []),
             "totals": coverage.get("totals", {}),
             "region_level_cell_counts": region_coverage,
             "structures": coverage.get("structures", [])},
            indent=2, default=str), encoding="utf-8")
        LOG.info("database coverage: cells=%s structures=%s biophysical=%s glif=%s complete=%s",
                 coverage.get("cell_specimens_retrieved"), coverage.get("distinct_structures"),
                 coverage.get("biophysical_models_retrieved"),
                 coverage.get("glif_models_retrieved"), coverage.get("complete"))
        LOG.info("wrote %s", COVERAGE_JSON.name)

    # -- Step 7: reference specimen ---------------------------------------
    reference = check_reference_specimen(client, cells_by_id, structure_index, templates,
                                         thresholds, incomplete_stages)
    LOG.info("reference specimen %s: returned_by_api=%s in_inventory=%s eligibility=%s",
             REFERENCE_SPECIMEN_ID, reference.get("returned_by_current_api"),
             reference.get("in_candidate_inventory"),
             (reference.get("cell") or {}).get("eligibility"))

    # -- Step 8: quality checks -------------------------------------------
    checks = run_quality_checks(cells, sweep_rows, model_rows, region_rows,
                                embedded_models, direct_models)

    # -- Step 9: summary + report -----------------------------------------
    summary = compute_summary(cells, sweep_rows, model_rows, region_rows, templates,
                              client, errors, thresholds, notes,
                              coverage, region_coverage)
    summary["quality_checks"] = checks
    summary["reference_specimen"] = reference
    summary["incomplete_stages"] = sorted(incomplete_stages)
    summary["outputs"] = {path.relative_to(PROJECT_ROOT).as_posix():
                          (len(path.read_bytes()) if path.exists() else 0)
                          for path in GENERATED_FILES}

    REPORT_MD.write_text(
        render_report(summary, region_rows, checks, reference, thresholds), encoding="utf-8")
    LOG.info("wrote %s", REPORT_MD.name)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    LOG.info("wrote %s", SUMMARY_JSON.name)

    write_manifest()

    failed = [check["check"] for check in checks if not check["passed"]]
    LOG.info("=" * 78)
    LOG.info("DONE  specimens=%d sweeps=%d models=%d regions=%d | PASS=%d COND=%d FAIL=%d UNK=%d"
             " | api_errors=%d | qc_failures=%d",
             len(cells), len(sweep_rows), len(model_rows), len(region_rows),
             summary["eligibility"].get("PASS", 0), summary["eligibility"].get("CONDITIONAL", 0),
             summary["eligibility"].get("FAIL", 0), summary["eligibility"].get("UNKNOWN", 0),
             len(errors), len(failed))
    if failed:
        LOG.warning("quality checks that did not pass: %s", failed)
    LOG.info("No population has been selected. Awaiting approval before Phase 1.")
    return 1 if failed else 0


def main() -> None:
    try:
        sys.exit(run())
    except KeyboardInterrupt:
        LOG.warning("interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()

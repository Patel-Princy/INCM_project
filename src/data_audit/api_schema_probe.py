"""Read-only probe of the Allen Cell Types Database API surface (schema audit).

Purpose
-------
Phase 0 requires inspecting the *actual* API schemas before any field is used
by the inventory script.  This module issues official Allen Institute RMA v2
queries, caches the raw responses on disk and prints the verified structure
(envelope keys, relation keys, sample records) so that field names are
confirmed rather than assumed.

Verified API behaviour recorded here (used by allen_inventory.py):
  * RMA envelope: {success, msg, num_rows, start_row, total_rows}.
  * ``num_rows`` / ``start_row`` / ``include`` MUST be separate query params;
    embedding them as ``rma::options,num_rows$eqN`` inside ``criteria`` is
    rejected by the Allen RMA parser.
  * ``Specimen`` has NO ``failed`` column (use ``EphysResult.failed``).
  * ``DendriteType`` / ``ApicalDendrite`` / ``NeuronalModelType`` are NOT
    addressable models (``uninitialized constant``); the equivalent content is
    reached through ``specimen_tags`` and ``neuronal_model_template_id``.
  * Bulk ``well_known_file_download?name=cell_types_*`` CSVs return HTTP 404.

Metadata only.  No NWB files, no model archives, no writes outside
``data/metadata/api_cache`` and ``results/dataset_inventory``.

Usage
-----
    python src/data_audit/api_schema_probe.py

Requires: requests.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT_ROOT / "data" / "metadata" / "api_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

QUERY_URL = "http://api.brain-map.org/api/v2/data/query.json"
WKF_DOWNLOAD = "http://celltypes.brain-map.org/api/v2/well_known_file_download"

HEADERS = {"User-Agent": "INCM-Phase0-DatasetAudit/0.1 (academic)"}
TIMEOUT = 90
MAX_TRIES = 3

REFERENCE_SPECIMEN = 485909730


def get(url: str, params: dict | None = None,
        cache_key: str | None = None) -> tuple[Any, str]:
    """GET an Allen endpoint. Returns (payload_or_None, status_string). Disk-cached."""
    if cache_key:
        cached = CACHE_DIR / f"{cache_key}.json"
        if cached.exists():
            with cached.open(encoding="utf-8") as fh:
                return json.load(fh), "cached"

    last_err: Exception | None = None
    for attempt in range(1, MAX_TRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                ctype = resp.headers.get("Content-Type", "")
                payload: Any = resp.json() if "json" in ctype else resp.text
                if cache_key:
                    with (CACHE_DIR / f"{cache_key}.json").open("w", encoding="utf-8") as fh:
                        json.dump(payload, fh, indent=2, default=str)
                return payload, f"HTTP 200 (attempt {attempt})"
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = RuntimeError(f"transient HTTP {resp.status_code}")
                time.sleep(2 * attempt)
                continue
            return None, f"HTTP {resp.status_code}"
        except requests.RequestException as exc:
            last_err = exc
            time.sleep(2 * attempt)
    return None, f"FAILED: {last_err}"


def rma(criteria: str, include: str | None = None, num_rows: int | None = None,
        start_row: int | None = None, cache_key: str | None = None,
        label: str = "", keys: list[str] | None = None,
        max_dump: int = 2500) -> Any:
    """Run one RMA query and print a compact structural summary."""
    params: dict[str, Any] = {"criteria": criteria}
    if include:
        params["include"] = include
    if num_rows is not None:
        params["num_rows"] = num_rows
    if start_row is not None:
        params["start_row"] = start_row
    payload, status = get(QUERY_URL, params=params, cache_key=cache_key)

    print("-" * 78)
    print(f"[{label or criteria[:70]}]  ->  {status}")
    if not isinstance(payload, dict):
        print("   NO PAYLOAD")
        return None
    msg = payload.get("msg")
    print(f"   success={payload.get('success')} total_rows={payload.get('total_rows')} "
          f"returned={len(msg) if isinstance(msg, list) else 'n/a'}")
    if not payload.get("success"):
        print(f"   ERROR MSG: {str(msg)[:400]}")
        return None
    if isinstance(msg, list) and msg:
        first = msg[0]
        if isinstance(first, dict):
            print(f"   item keys: {sorted(first.keys())}")
            if keys:
                for item in msg[:40]:
                    print("   row:", json.dumps({k: item.get(k) for k in keys}, default=str))
            else:
                print(json.dumps(first, indent=2, default=str)[:max_dump])
    return payload


def probe_bulk_patterns() -> None:
    """Second audit stage: the query shapes allen_inventory.py depends on.

    Verified outcomes (recorded here so they are reproducible):
      * One combined ``include`` on Specimen returns structure, donor
        (transgenic_lines), specimen_tags, ephys_result(well_known_files) and
        neuronal_models in a single request.
      * Paging with num_rows=2000/5000 + start_row works; num_rows=5000 was
        accepted and returned all 505 matching rows.
      * ``$in`` list criteria works for structure_id and specimen_id
        (EphysSweep, NeuronalModel, NeuronReconstruction) and attachable_id
        (WellKnownFile).
      * Model class MUST be taken from neuronal_model_template_id: both the
        biophysical fit JSON and the GLIF neuron_config JSON share
        well_known_file_type_id 329230374.
      * Morphology SWC is reached via WellKnownFile with
        attachable_type='NeuronReconstruction' (type 303941301).
      * Organism: 1 = Homo Sapiens, 2 = Mus musculus.
    """
    layer_ids = ("778,821,721,593,33,305,613,973,421,573,121,74,"
                 "905,1114,233,601,1074,649,844,943,320,648,882")
    ref, ref_model, ref_recon, glif_model = 485909730, 486509232, 500961528, 566281640

    print("\n### 9. combined include + paging (single request, all relations)\n")
    for start in (0, 500):
        payload = rma(
            "model::Specimen,rma::criteria,"
            f"[structure_id$in{layer_ids}],[is_cell_specimen$eqtrue]",
            include="structure,donor(transgenic_lines),specimen_tags,"
                    "ephys_result(well_known_files),neuronal_models",
            num_rows=500, start_row=start,
            label=f"combined includes, page start_row={start}",
            cache_key=f"p4_page_{start}", max_dump=0)
        if payload:
            print(f"   rows={len(payload['msg'])} total_rows={payload['total_rows']}")

    print("\n### 10. bulk $in across sweeps / models / reconstructions\n")
    ids = f"{ref},313860745,313861608"
    for model in ("EphysSweep", "NeuronalModel", "NeuronReconstruction"):
        rma(f"model::{model},rma::criteria,[specimen_id$in{ids}]", num_rows=1,
            label=f"{model} bulk $in")

    print("\n### 11. download references (WellKnownFile routes)\n")
    rma(f"model::WellKnownFile,rma::criteria,[attachable_id$eq{ref_model}]", num_rows=10,
        label="biophysical model files",
        keys=["id", "attachable_type", "well_known_file_type_id", "path", "download_link"])
    rma(f"model::WellKnownFile,rma::criteria,[attachable_id$eq{glif_model}]", num_rows=10,
        label="GLIF model files (same file-type id -> classify by template)",
        keys=["id", "attachable_type", "well_known_file_type_id", "path"])
    rma(f"model::WellKnownFile,rma::criteria,[attachable_id$eq{ref_recon}]", num_rows=10,
        label="morphology reconstruction files",
        keys=["id", "attachable_type", "well_known_file_type_id", "path"])
    rma(f"model::NeuronReconstruction,rma::criteria,[specimen_id$eq{ref}]", num_rows=2,
        label="reconstruction record", keys=["id", "specimen_id",
                                             "neuron_reconstruction_type", "superseded"])

    print("\n### 12. organism ids\n")
    rma("model::Organism,rma::criteria,[id$in1,2]", num_rows=5,
        label="Organism 1/2", keys=["id", "name"])

    print("\n### 13. HEAD check that download links resolve (no payload downloaded)\n")
    for wkf_id, what in ((ref_model, "model fit json"), (ref_recon, "morphology swc")):
        payload, status = get(QUERY_URL,
                              params={"criteria": f"model::WellKnownFile,rma::criteria,"
                                                  f"[attachable_id$eq{wkf_id}]",
                                      "num_rows": 1})
        if isinstance(payload, dict) and payload.get("success"):
            link = payload["msg"][0].get("download_link")
            try:
                head = requests.head(f"http://api.brain-map.org{link}",
                                     headers=HEADERS, timeout=60, allow_redirects=True)
                print(f"   {what:18s} {link}  HEAD {head.status_code} "
                      f"content-length={head.headers.get('Content-Length')} "
                      f"({status})")
            except requests.RequestException as exc:
                print(f"   {what:18s} HEAD FAILED: {exc}")


def probe() -> None:
    print("\n### 1. SpecimenTag vocabulary (dendrite type / apical dendrite)\n")
    rma("model::SpecimenTag", num_rows=20, label="all SpecimenTag rows",
        cache_key="p3_specimen_tags_all", keys=["id", "name", "description"])
    rma(f"model::Specimen,rma::criteria,[id$eq{REFERENCE_SPECIMEN}]",
        include="specimen_tags", num_rows=1, label="reference specimen specimen_tags",
        cache_key="p3_ref_specimen_tags", max_dump=4000)

    print("\n### 2. NeuronalModelTemplate (model class source of truth)\n")
    rma("model::NeuronalModelTemplate", num_rows=60, label="all templates",
        cache_key="p3_neuronal_model_templates", keys=["id", "name", "description"])

    print("\n### 3. NeuronalModel shape + name patterns across cells\n")
    rma("model::NeuronalModel", num_rows=40, label="NeuronalModel sample (all cells)",
        cache_key="p3_neuronal_models_sample", keys=["id", "specimen_id", "name",
                                                     "neuronal_model_template_id"])

    print("\n### 4. Neuron reconstruction / morphology availability\n")
    rma("model::NeuronReconstruction,rma::criteria,[id$eq500961528]", num_rows=2,
        label="NeuronReconstruction 500961528")
    rma("model::NeuronReconstruction", num_rows=3, label="NeuronReconstruction sample")

    print("\n### 5. WellKnownFile routes (NWB + morphology downloads)\n")
    rma(f"model::WellKnownFile,rma::criteria,[attachable_id$eq{REFERENCE_SPECIMEN}]",
        num_rows=20, label="WellKnownFile attachable_id=specimen 485909730",
        cache_key="p3_wkf_specimen_ref",
        keys=["id", "attachable_id", "attachable_type", "well_known_file_type_id",
              "path", "download_link"])
    rma(f"model::Specimen,rma::criteria,[id$eq{REFERENCE_SPECIMEN}]",
        include="ephys_result(well_known_files)", num_rows=1,
        label="ephys_result(well_known_files)", cache_key="p3_ref_ephys_wkf", max_dump=5000)
    rma("model::WellKnownFileType", num_rows=2000, label="WellKnownFileType id->name map",
        cache_key="p3_wkft_all")

    print("\n### 6. RMA criteria operators supported for batch region queries\n")
    rma("model::Specimen,rma::criteria,[structure_id$in778,821],[is_cell_specimen$eqtrue]",
        num_rows=1, label="structure_id $in list")
    rma("model::Specimen,rma::criteria,[structure_id$eq778],[is_cell_specimen$eqtrue]",
        include="donor", num_rows=1, label="include donor (organism_id)",
        keys=["id", "donor_id"], max_dump=1200)

    print("\n### 7. EphysSweep stimulus vocabulary + units (current vs voltage clamp)\n")
    payload = rma(f"model::EphysSweep,rma::criteria,[specimen_id$eq{REFERENCE_SPECIMEN}]",
                  num_rows=200, label="all sweeps for reference specimen",
                  cache_key="p2_ephys_sweeps_ref")
    if payload:
        names: dict[str, int] = {}
        units: dict[str, int] = {}
        for row in payload["msg"]:
            names[row.get("stimulus_name")] = names.get(row.get("stimulus_name"), 0) + 1
            units[row.get("stimulus_units")] = units.get(row.get("stimulus_units"), 0) + 1
        print("   stimulus_name counts:", json.dumps(names, default=str))
        print("   stimulus_units counts:", json.dumps(units, default=str))

    print("\n### 8. bulk CSV well-known-file names (expected to be retired)\n")
    for name in ("cell_types_specimens", "cell_types_ephys_features",
                 "cell_types_morphology_reconstructions", "cell_types_ephys_summary"):
        _, status = get(WKF_DOWNLOAD, params={"name": name})
        print(f"   {name:38s} {status}")


if __name__ == "__main__":
    try:
        probe()
        probe_bulk_patterns()
    except KeyboardInterrupt:
        sys.exit(1)

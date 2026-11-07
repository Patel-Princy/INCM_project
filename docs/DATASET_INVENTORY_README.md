# Allen Cell Types Database — Phase 0 Inventory: How to Run and Reproduce

This document explains **how the Phase 0 dataset inventory was produced**, what the
environment supports, and how to re-run it. It is the operating manual for
`src/data_audit/allen_inventory.py`.

Phase 0 is a **dataset feasibility audit only**. No neuron model was implemented, no
FitzHugh–Nagumo fitting was performed, and **no NWB, model or morphology file was
downloaded**. No neuronal population has been selected.

---

## 1. Environment findings (Step 1)

Verified on this machine; nothing was installed, upgraded or downgraded.

| Item | Finding | Verified how |
|---|---|---|
| OS / shell | Windows, PowerShell 5.1 (`powershell.exe`) | `user_info`, `$PSVersionTable` |
| Python | **3.14.0** at `C:\Python314\python.exe` | `python --version`, `sys.executable` |
| AllenSDK | **NOT installed** | `import allensdk` → `ModuleNotFoundError`; `pip show allensdk` → not found |
| NEURON | **NOT installed** | `import neuron` → `ModuleNotFoundError` |
| `requests` | 2.32.5 (present) | `pip show requests` |
| `pandas` | 2.3.3 (present) | `pip show pandas` |
| `numpy` | **2.3.4** (present) | `pip show numpy` |
| `pytest` | 9.1.1 (present) | `pip show pytest` |
| `PyMuPDF` | 1.28.2 (present) — used to read the proposal PDF | `pip show pymupdf` |
| `pypdf` | 6.18.0 (present) | `pip show pypdf` |

### 1.1 AllenSDK: recommended installation command (NOT executed)

Per the working instructions, the command is **reported, not run**:

```powershell
python -m pip install allensdk
```

**Why it was not run, and why it is not needed for Phase 0:**

1. **Version conflict.** AllenSDK's current release is **2.16.2**, and its published
   dependency metadata on PyPI pins **`numpy (<1.24)`**. This environment has
   **numpy 2.3.4**. Installing AllenSDK would force a numpy **downgrade**, which the
   working instructions forbid without approval ("Do not install, upgrade or downgrade
   packages without approval").
2. **Interpreter support.** `INCM_revised_project.pdf` §6 itself notes that AllenSDK
   "fails on Windows/Python 3.12" and recommends a clean Python 3.9/3.10 environment
   (WSL2 or conda). This machine runs **Python 3.14 on Windows**, which is further from
   the supported range, not closer.
3. **Not required.** AllenSDK's Cell Types accessors (`CellTypesCache`) are thin
   wrappers over the same public Allen Brain Map **RMA v2** REST API used here. Phase 0
   needs *metadata only*, so it queries that API directly with `requests`. Nothing in
   Phase 0 depends on AllenSDK.

> **Approval needed later.** Phase 1 (running Allen biophysical models in NEURON) *does*
> need NEURON, and reading NWB sweeps needs `h5py`/`pynwb`. Those are environment
> decisions for the approver, not for this phase. See
> `docs/DATASET_SELECTION_DECISION.md` §5.

### 1.2 PowerShell note

PowerShell expands `$` inside double-quoted strings, which corrupts RMA criteria such as
`[id$eq485909730]` when passed via `python -c "..."`. **Always run the scripts as files**,
never as inline `-c` snippets containing `$`.

---

## 2. Repository layout

```
INCM-Project/
├── data/
│   └── metadata/
│       ├── api_cache/inventory/        # disk cache of raw RMA responses (evidence)
│       ├── .generated_manifest.json    # SHA-256 of every file this script wrote
│       ├── cell_inventory.csv          # 1 694 rows × 57 columns
│       ├── region_summary.csv          #    20 rows × 27 columns
│       ├── sweep_inventory.csv         # 128 869 rows × 15 columns
│       └── model_inventory.csv         #   3 262 rows × 18 columns
├── src/
│   └── data_audit/
│       ├── allen_inventory.py          # the audit (single entry point)
│       └── api_schema_probe.py         # API schema discovery tool (Step 2 prerequisite)
├── results/
│   └── dataset_inventory/
│       ├── DATASET_INVENTORY_REPORT.md          # machine-generated report (Step 9)
│       ├── inventory_summary.json               # machine-readable summary
│       ├── database_structure_coverage.json     # whole-database coverage scan
│       └── allen_inventory.log                  # run log
├── docs/
│   ├── DATASET_INVENTORY_README.md      # this file
│   └── DATASET_SELECTION_DECISION.md    # decision record (status: PENDING APPROVAL)
└── tests/
    ├── conftest.py
    ├── test_allen_inventory_units.py    # offline unit tests
    └── test_inventory_outputs.py        # checks over the generated artefacts
```

`INCM_revised_project.pdf` at the workspace root is the source proposal. **It was read
only and never modified.**

---

## 3. Running the inventory

From `INCM-Project/`:

```powershell
# normal run (uses the on-disk API cache when present)
python src/data_audit/allen_inventory.py

# force fresh queries against the live Allen API
python src/data_audit/allen_inventory.py --refresh

# console debug logging
python src/data_audit/allen_inventory.py --verbose

# tighten / relax the audit thresholds
python src/data_audit/allen_inventory.py --min-long-square 8 --min-depolarizing-long-square 4

# check a different reference specimen (default 485909730)
python src/data_audit/allen_inventory.py --reference-specimen 485909730

# skip the database-wide coverage scan (~15 extra queries)
python src/data_audit/allen_inventory.py --skip-coverage
```

Run the tests:

```powershell
python -m pytest tests -q
```

Re-run the schema probe (read-only, regenerates no inventory output):

```powershell
python src/data_audit/api_schema_probe.py
```

Exit code is `0` when every quality check passes and `1` otherwise.

### 3.1 Overwrite protection

Before writing anything the script reads `data/metadata/.generated_manifest.json` and
refuses to run if an output file either

* exists but was **not** generated by this script, or
* exists, **was** generated by it, but has been **modified since**.

This implements "do not overwrite existing files without permission". To deliberately
regenerate over hand-edited files, pass `--force`.

### 3.2 Caching, logging, idempotency

| Property | Implementation |
|---|---|
| **Caching** | Every RMA response is written to `data/metadata/api_cache/inventory/<sha256-of-params>.json`. Repeat runs issue **zero** live requests (last verified run: `live_requests=0`, `cache_hits=206`). `--refresh` bypasses the cache. The cache doubles as the raw evidence trail. |
| **Retry / backoff** | Up to `MAX_TRIES = 4` attempts on network errors and HTTP 429/500/502/503/504, with linear backoff (`2 × attempt` seconds). |
| **Courtesy delay** | `MIN_DELAY_S = 0.15` s between live requests. |
| **Logging** | `logging` to both console and `results/dataset_inventory/allen_inventory.log`; `--verbose` sets console level to DEBUG. |
| **Error handling** | `ApiErrorLog` records `stage`, HTTP status, detail and the exact `criteria` string for every failure, and marks whether it was recoverable. Errors surface in `inventory_summary.json → api_errors` and in the report. |
| **Idempotency** | `write_csv()` de-duplicates on the sort key, sorts with a stable `mergesort`, normalises `NaN → None`, and writes with fixed `na_rep=""`, `lineterminator="\n"`, `QUOTE_MINIMAL`. Re-running produces **byte-identical** files, so records are never duplicated. Verified: two consecutive runs gave identical SHA-256 for all four CSVs. |
| **Missing values** | Written as **empty cells**, never as `nan`/`None`/`NULL`/`-` placeholders. A test enforces this. |

---

## 4. API surface actually used (Step 2 prerequisite: "inspect actual API schemas")

All data comes from the official **Allen Brain Map RMA v2** endpoint:

```
http://api.brain-map.org/api/v2/data/query.json
```

Response envelope: `{success, msg, num_rows, start_row, total_rows}`.

`src/data_audit/api_schema_probe.py` was run **before** any inventory field was used, and
its raw responses are cached on disk. Findings that shaped the implementation:

### 4.1 What works

| Need | Working query pattern |
|---|---|
| Resolve a region acronym | `model::Structure,rma::criteria,[acronym$eq'VISp']` |
| Find a region's layer structures | `model::Structure,rma::criteria,[parent_structure_id$eq385]` |
| Cell specimens in a set of structures | `model::Specimen,rma::criteria,[structure_id$in778,821,...],[is_cell_specimen$eqtrue]` |
| Specimen detail | `include=structure,donor(transgenic_lines),specimen_tags,ephys_result(well_known_files),neuronal_models` |
| Sweeps for many cells | `model::EphysSweep,rma::criteria,[specimen_id$in...]` (chunked at 100 ids) |
| Models for many cells | `model::NeuronalModel,rma::criteria,[specimen_id$in...]` |
| Model class | `model::NeuronalModelTemplate` → `neuronal_model_template_id` |
| Recording failure flag | `EphysResult.failed` |
| Morphology | `model::NeuronReconstruction,rma::criteria,[specimen_id$in...]` + `WellKnownFile` type `303941301` |
| Paging | separate `num_rows` / `start_row` query params; verified working up to `num_rows=5000` |

### 4.2 What does **not** work (each was hit and worked around)

| Attempt | Result | Workaround adopted |
|---|---|---|
| `well_known_file_download?name=cell_types_specimens` (and `_ephys_features`, `_morphology_reconstructions`, `_ephys_summary`) | **HTTP 404** on both `api.brain-map.org` and `celltypes.brain-map.org` — the bulk CSV exports are retired | Build the whole inventory from RMA v2 queries |
| `rma::options,num_rows$eq500` embedded inside `criteria` | parse error `missing <EOF> at "$eq"` / *Data Access error* | Pass `num_rows`, `start_row`, `include` as **separate query parameters** |
| `model::Specimen,[failed$eq'false']` | *Data Access error* — `Specimen` has no `failed` column | Read failure status from `EphysResult.failed` |
| `model::DendriteType`, `model::ApicalDendrite`, `model::NeuronalModelType` | `uninitialized constant` — these models do not exist | Dendrite type / apical status from `specimen_tags`; model class from `NeuronalModelTemplate` |
| `include=cortex_layer,dendrite_type,apical_dendrite,cell_reporter,treatment` | *Data Access error* | Use the verified include set in §4.1 |
| `include=ephys_result(ephys_sweeps)`, `neuronal_models(neuronal_model_type,well_known_files)` | *Data Access error* | Fetch sweeps and model files in separate chunked queries |
| `[name$like'%ell%ype%']` | `extraneous input ... expecting RBRACKET` — `$like` is unsupported here | Use exact `$eq` / `$in` only |

### 4.3 Schema facts that matter for correctness

* **Cortical layer is encoded in the structure acronym**, not in a field: `VISp5`
  (id 778) → parent `VISp` (id 385). `Specimen.cortex_layer_id` is **always null** in
  this database. `split_region_layer()` derives `(region, layer)` from the parent
  structure and never guesses; when the parent cannot be resolved the region is left
  empty and the cell is classified `UNKNOWN` (not `FAIL`).
* **Dendrite type and apical-dendrite status live in `specimen_tags`**, e.g.
  `"dendrite type - spiny"`, `"apical - intact"`.
* **Current-clamp vs voltage-clamp** is `EphysSweep.stimulus_units == "Amps"` (current
  clamp) vs `"Volts"` (voltage clamp). Only current-clamp sweeps count toward the
  project's requirements.
* **GLIF and biophysical model parameter files share `well_known_file_type_id =
  329230374`.** Classifying by file type would silently count GLIF as biophysical.
  Classification is therefore driven **only** by `neuronal_model_template_id`, resolved
  against `model::NeuronalModelTemplate` names:
  `329230710` = *Biophysical – perisomatic*, `491455321` = *Biophysical – all active*,
  the five `GLIF1…GLIF5` templates = *glif*.
* **`is_cell_specimen == true` selects exactly the published Cell Types Database
  roster**: 2 336 rows (1 923 mouse + 413 human) across 79 structures. This was verified
  by paging the entire set, and is what makes the "database-wide" statements in the
  report safe.
* **Download references were validated with HTTP `HEAD`, never `GET`** — no payload was
  retrieved. Verified sizes: biophysical fit JSON 2 848 B, ephys NWB 17 306 774 B,
  morphology SWC 83 865 B, GLIF config 1 206 B.

---

## 5. What the audit produces

| Output | Content |
|---|---|
| `data/metadata/cell_inventory.csv` | One row per specimen: id, region acronym + full name, layer, species, dendrite type, apical status, transgenic driver/reporter lines, electrophysiology availability, morphology availability, per-category sweep counts, model counts by class, resolved download references, eligibility + reasons, validation flags. |
| `data/metadata/sweep_inventory.csv` | One row per sweep: sweep number, stimulus name (verbatim), mapped category, clamp mode, amplitudes, duration, spike count. |
| `data/metadata/model_inventory.csv` | One row per model: model id, specimen id, template id/name, `model_class`, `is_biophysical`, availability status, file id, download URL, download-reference note, provenance `source`. |
| `data/metadata/region_summary.csv` | Per region **and** per layer: specimen counts by species, ephys/morphology availability, perisomatic/all-active/any-biophysical counts, GLIF-only counts, eligibility breakdown, median long-square count, and an explanatory `note` for regions with no data. |
| `results/dataset_inventory/database_structure_coverage.json` | Whole-database scan: every structure's cell/model counts, plus region-level and control-acronym cell counts. |
| `results/dataset_inventory/DATASET_INVENTORY_REPORT.md` | The Step 9 report. Machine-generated; numbers are never hand-edited. |
| `results/dataset_inventory/inventory_summary.json` | The same numbers in machine-readable form, including `api_errors` and `quality_checks`. |

### 5.1 Eligibility vocabulary (Step 5)

| Status | Meaning |
|---|---|
| `PASS` | Every required **metadata** criterion confirmed present. Still metadata-level only — Phase 0 downloaded nothing. Every PASS row is additionally flagged `needs_nwb_validation` / `needs_model_validation`. |
| `CONDITIONAL` | Promising, but at least one requirement is short of threshold or unresolved (too few long-square sweeps, GLIF-only, model listed without a resolved download reference, no NWB reference). Requires actual NWB / model download validation. |
| `FAIL` | A required criterion is **confirmed absent**: no `EphysResult`, `EphysResult.failed == true`, zero current-clamp Long Square sweeps, or a non-mouse species. |
| `UNKNOWN` | Required metadata could **not** be retrieved (API failure), or the target region could not be resolved from the structure hierarchy. |

**Missing information is never recorded as `FAIL`.** This is enforced by code order (the
UNKNOWN gates run before the FAIL gates) and by unit tests.

Default audit thresholds: `min_long_square = 6`, `min_depolarizing_long_square = 3`
(both CLI-tunable). Rationale: the protocol needs a calibration/held-out split of
long-square sweeps for both the Allen-model validation and the FHN fit, and an F–I curve
needs several depolarising steps. These are **audit** thresholds, not experimentally
validated ones.

---

## 6. Quality checks (Step 8)

`run_quality_checks()` executes 14 checks on every run; results are logged and written to
`inventory_summary.json → quality_checks`. Last run: **all 14 passed, 0 API errors.**

1. `specimen_ids_unique`
2. `model_ids_unique`
3. `model_ids_disjoint_from_specimen_ids` — model ids are never confused with specimen ids
4. `every_model_maps_to_an_inventoried_specimen` — foreign-key integrity
5. `region_counts_match_specimen_inventory` — region summary reconciles with the cell inventory
6. `glif_never_classified_as_biophysical`
7. `biophysical_rows_have_biophysical_model_names`
8. `no_glif_ids_in_cell_biophysical_counts` — `n_biophysical == perisomatic + all_active`
9. `embedded_and_direct_model_queries_agree` — two independent model queries cross-checked
10. `sweep_specimen_ids_subset_of_cells`
11–14. `csv_opens_cleanly` for each of the four CSVs

The `tests/` suite adds 92 further checks (offline; no network):

* `test_allen_inventory_units.py` — template classification, GLIF/biophysical separation,
  tag parsing, region/layer derivation, NWB reference selection, all four eligibility
  outcomes, threshold configurability, sweep category/clamp derivation, CSV idempotency
  and missing-value preservation, region-summary reconciliation, chunking helpers.
* `test_inventory_outputs.py` — schema conformance, key uniqueness, disjoint id spaces,
  count reconciliation, absence of placeholder text, "FAIL must state a confirmed
  absence", "PASS must meet every documented criterion", provenance manifest,
  report/summary agreement, and the database-wide motor-absence evidence.

---

## 7. Known limitations

* **Metadata only.** No NWB, model archive or SWC file was opened. Every `PASS` is a
  metadata-level statement and carries `needs_nwb_validation` / `needs_model_validation`.
* **Download references are HEAD-verified, not content-verified.** A resolved URL proves
  the reference exists and the server answers; it does not prove the file parses.
* **Stimulus categories** are mapped from `EphysSweep.stimulus_name` via an explicit
  dictionary. Unmapped names are recorded verbatim under `other`, never silently dropped.
* **The API is unauthenticated and can change.** The retired bulk-CSV endpoint (§4.2) is
  proof that this happens. `--refresh` plus the cached responses make any future drift
  diagnosable.
* **Thresholds are judgement calls**, documented above and tunable; they are not derived
  from the proposal's text, which specifies only "≥ 4 recorded cells with suitable
  long-square sweeps and downloadable models of the same class".

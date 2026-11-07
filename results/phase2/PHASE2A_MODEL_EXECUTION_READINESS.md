# Phase 2A — Detailed Biophysical Model Asset Acquisition and Execution Readiness

| | |
|---|---|
| **Project** | INCM — *How much biological detail does a neuron model need?* |
| **Phase** | 2A — asset acquisition and execution readiness |
| **Specimen** | `382982932` — *Mus musculus*, VISp, cortical layer 2/3 |
| **Model classes** | `Biophysical - perisomatic` (id `473862496`) and `Biophysical - all active` (id `497233292`) |
| **Evidence base** | `results/phase1/PYRAMIDAL_CANDIDATE_VALIDATION.md`, `results/phase1/CROSS_SPECIMEN_UNIT_VALIDATION.md`, `docs/DATASET_SELECTION_DECISION.md`, Allen RMA API, AllenSDK `v2.16.2` |
| **Inspection script** | [`scripts/inspect_model_assets.py`](../../scripts/inspect_model_assets.py) — 82 checks, 0 failures |
| **Simulation executed** | **No** |
| **Verdict** | 🟠 **CONDITIONALLY READY** |

---

## 1. Executive verdict

**CONDITIONALLY READY.**

Every asset the two models need has been identified, retrieved from an authoritative
source, digest-pinned, and shown to be internally consistent and mappable onto
Allen's own NEURON template. Nothing is corrupt, truncated, or contradictory.

"Conditionally" is doing real work in that sentence, and it distinguishes two
different questions that Phase 1C deliberately left open:

| Question | Answer |
|---|---|
| Do the assets exist and are they internally consistent? | **Yes.** 23 digest-pinned assets, 77 asset-level checks pass, 5 more when re-fetched from source. |
| Can the models be executed from what Allen publishes? | **No.** The published artifact is half of a pair. |
| Can the models be executed *in this environment*? | **No.** NEURON has no Windows distribution on PyPI or conda-forge. |

The single most important structural finding is this. Allen's runner is entered
through a `manifest.json`, which then names the `fit.json` as its own
`biophys[0].model_file`; `Config.read_model_description()` merges both files into
one `Description`. **The RMA API publishes the `fit.json` and not the
`manifest.json`.** Each `NeuronalModel` record has exactly one attached
well-known file, and it is always the parameter document
(`WellKnownFileType 329230374 = NeuronalModelParameters`). No archive, no `.hoc`,
no `.mod`, no `manifest.json` is served anywhere against either model id, against
either template id, or against the specimen.

So the models are **reconstructible but not executable as published**. What is
missing is glue, not science: a manifest must be authored, and a NEURON
interpreter must be provided on a platform Allen supports. Both are bounded,
documented tasks (§8, §11), which is why the verdict is CONDITIONALLY READY rather
than BLOCKED.

Three further findings materially affect how these models may be used, and none of
them is visible from the model id or the `fit.json` alone:

1. **Both models were fitted on a single sweep**, not a population of sweeps.
   The perisomatic model on sweep 38, the all-active model on sweep 41.
2. **Both of those sweeps lie inside the 20-sweep COARSE block** that Phase 1C
   nominated for analysis. They are therefore **in-sample**, not held-out, and
   must be excluded from any held-out comparison.
3. **The perisomatic model was fitted to the one sweep Phase 1C flagged as
   biologically anomalous** (§9.3 of the Phase 1C report): 170 pA produces 14
   spikes in COARSE sweep 38 but 1 spike in FINEST sweeps 49–52. The fitted
   parameters encode that anomaly by construction.

---

## 2. What Allen actually publishes for these two models

Queried live against the RMA API; every response was HTTP 200 with
`success = true`.

### 2.1 The model records

`NeuronalModel` carries only five columns, none of which is a download reference:

| | Perisomatic | All-active |
|---|---|---|
| `id` | `473862496` | `497233292` |
| `name` | `Biophysical - perisomatic` | `Biophysical - all active` |
| `neuronal_model_template_id` | `329230710` | `491455321` |
| `neuron_reconstruction_id` | `491771090` | `491771090` |
| `specimen_id` | `382982932` | `382982932` |

Both models point at the **same** reconstruction id, `491771090`.

### 2.2 Attached files — exactly one per model

| Model id | Well-known file id | Type | Served filename |
|---|---|---|---|
| `473862496` | `497235792` | `NeuronalModelParameters` | `prod312/neuronal_model_473862496/382982932_fit.json` |
| `497233292` | `568156386` | `NeuronalModelParameters` | `prod583/neuronal_model_497233292/497233292_fit.json` |

Note the two filenames follow **different conventions** — the perisomatic file is
named after the *specimen*, the all-active file after the *model*. This is
cosmetic but confirms they were produced by different pipeline generations, and
it is the first hint of the schema divergence documented in §4.

### 2.3 The template records carry no files

| Template | `id` | Name | Attached files |
|---|---|---|---|
| Perisomatic | `329230710` | `Biophysical - perisomatic` | **0** |
| All-active | `491455321` | `Biophysical - all active` | **0** |

The template record is pure metadata (name plus the description string
*"Biophysical Neuronal Model Template"*). It does not host the template source.
The template source lives in the AllenSDK Python package, not in the database.

### 2.4 The referenced reconstruction does not exist

`neuron_reconstruction_id 491771090` returns **zero rows**. It is one of 24
unresolvable ids among the 201 distinct reconstructions referenced by
biophysical models database-wide.

The specimen's own published reconstruction is `674389884` (`full`), which carries
three attached files:

| Well-known file | Type (type id) | Path |
|---|---|---|
| `487661131` | `MorphologyThumbnail` (`480715721`) | `.../morphology_summary_674389884.png` |
| `674389910` | `3DNeuronMarker` (`486753749`) | `..._674389884_m.marker` |
| `674389901` | `3DNeuronReconstruction` (`303941301`) | `..._674389884_m.swc` |

**Consequence.** Allen's fitted geometry for this cell cannot be retrieved. The
published SWC is available and is used here as a *substitute*, but it is not
provably the geometry the parameters were fitted against. This is the reason the
models can be reconstructed but cannot be called "Allen's model, exactly"
(§6.3, §12).

---

## 3. Asset inventory

All 23 assets below are cached in a Git-ignored directory and digest-pinned inside
`scripts/inspect_model_assets.py`, so a reviewer can prove the cached copy is
byte-identical to source. `--verify-remote` re-downloads every essential artifact
into memory and compares; all five matched.

**Cache location.** The brief suggested `data/model_cache/`. The cache is
actually at **`tmp/model_cache/`**, because `.gitignore` covers `tmp/` but does
**not** cover `*.json`; a `data/model_cache/` holding `fit.json` would leave the
working tree permanently dirty, and adding a rule to `.gitignore` is outside this
phase's commit allowlist. Moving it is a one-line change (`data/model_cache/` in
`.gitignore`) whenever that is approved. The script's `--cache-dir` accepts
either path.

### 3.1 Model descriptors (the primary artifacts)

| Asset | Source | Bytes | SHA-256 |
|---|---|---|---|
| `models/perisomatic_473862496/382982932_fit.json` | RMA wkf `497235792` | 2 891 | `d24d00aaed5a2a0ecf9752735b62254bba7ab3dc0d3627e61466f95b00a8e38f` |
| `models/all_active_497233292/497233292_fit.json` | RMA wkf `568156386` | 5 738 | `bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963` |

Retrieved by direct HTTP GET on
`http://api.brain-map.org/api/v2/well_known_file_download/<wkf>`, written once in
binary, and never modified. Their digests were re-verified by a second,
independent download.

### 3.2 Morphology

| Asset | Source | Bytes | SHA-256 |
|---|---|---|---|
| `morphology/674389901_382982932_m.swc` | RMA wkf `674389901` (type `3DNeuronReconstruction`, recon `674389884`) | 335 924 | `71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c` |
| `morphology/674389910_382982932_m.marker` | RMA wkf `674389910` (type `3DNeuronMarker`) | 373 | `3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925` |

### 3.3 NEURON template

| Asset | Source | Bytes | SHA-256 |
|---|---|---|---|
| `allensdk/cell.hoc` | AllenSDK `v2.16.2`, `allensdk/model/biophysical/cell.hoc` | 715 | `9b8f73f8202f355ea6f0c9f27be23bf2cb9bd122d9abc4fb864af88401b9a26d` |

### 3.4 Mechanism sources — the 16-file canonical set

All from AllenSDK `v2.16.2`, `allensdk/test/model/peri_model/modfiles/`. The
all-active fixture directory uses an **identical** 16-file set, which is what
establishes this as the canonical library rather than a perisomatic quirk.

| Asset | Bytes | SHA-256 |
|---|---|---|
| `CaDynamics.mod` | 704 | `f012def9758f7d0244b81c54291edea6597c15fad99b9f7b5725b121a3567f16` |
| `Ca_HVA.mod` | 1 211 | `021d34cf9ef3e76b0f2afee1a1eeab40eed56d0d3b1362b7e1019f4433273c71` |
| `Ca_LVA.mod` | 1 069 | `a7a9ef262541dc96f5d19afd97778f9320808d01ce397350f1f2be3db30f920f` |
| `Ih.mod` | 1 005 | `8616325d83add9a1a6546972352b4a62e57095ba25f3c6b5a57ab8b397e2d662` |
| `Im.mod` | 859 | `e1c3bfb2186439bdb963ff2c53268efb824d8e00401aef0a14b7d2234071bb2c` |
| `Im_v2.mod` | 761 | `bc378428d3b4da76b6f9b1820dde1f52abef47389ce6edbcddb0c8fb967970fd` |
| `K_P.mod` | 1 161 | `2254697617c8da162ff8e5495e4d512fce53f77b44b86754855f11cee4ab3b3e` |
| `K_T.mod` | 1 031 | `1cb9d72f985ef028922cafafed079df5c47b87a893001304181ec48881367ba7` |
| `Kd.mod` | 705 | `1cac92486bf77c2976cad9a34e1741dc20ecda70d7b2c9bf5c3474e66f7dfcce` |
| `Kv2like.mod` | 1 433 | `9244b0eb301dacee5a844910d6b4945856b90dc60937a74ac7f4f19f778d0895` |
| `Kv3_1.mod` | 631 | `e636c3437a9d9ccb69a0a7efc09fcfe1f16ad97f0468615b70fdbc352fe0855c` |
| `Nap.mod` | 1 170 | `979d21508f5b089e7b782835ea7f60311223bdc3a8e5242056c594305d2fb220` |
| `NaTa.mod` | 1 413 | `fd6af6564b365f5ec016b453c8f540a15780dea62597053d10cc402443541caf` |
| `NaTs.mod` | 1 267 | `d75ed63d6367fe27c6e5671704594a510e8d83b57db835f30fc36e2f24bef6cf` |
| `NaV.mod` | 4 061 | `635605ba861c070f8fdc273365f3a0fca6eee24762afc9b102161fdd6e9cfc42` |
| `SK.mod` | 942 | `079f1e3cac7444696d480b8e02853b215cd93e0c7b9986dbb54925fc49eddbeb` |

### 3.5 Reference configuration and runner sources

Retrieved so that the runtime contract can be read from Allen's own code rather
than inferred. These are documentation of the dependency chain, not runtime
inputs.

| Asset | Bytes | SHA-256 |
|---|---|---|
| `reference/manifest_perisomatic.json` (Allen fixture) | 1 911 | `ee677381bf6440e909654994f0dc115cc2d001f45bbbbaf5b42a3c41f6c19c8e` |
| `reference/manifest_all_active.json` (Allen fixture) | 1 910 | `681e524427585c5a285791519d21bce226c4a0ac7abfad912551cbe817ed564d` |
| `reference/biophysical_utils.py` | 16 577 | — |
| `reference/biophys_sim_neuron_hoc_utils.py` | 3 333 | — |
| `reference/biophys_sim_config.py` | 5 623 | — |
| `reference/runner.py` | 8 540 | — |
| `reference/run_simulate.py` | 5 447 | — |
| `reference/requirements_v2.16.2.txt` | 357 | — |
| `reference/setup_v2.16.2.py` | 3 056 | — |
| `reference/LICENSE_v2.16.2.txt` | 1 843 | — |
| `reference/pyproject_master_a56bd8ea.toml` | 2 759 | — |
| `reference/test_biophysical_peri.py` | 3 419 | — |
| `reference/test_biophysical_all_active.py` | 3 471 | — |

---

## 4. The descriptors: schema and parameter comparison

Both documents have exactly four top-level keys, and all four are **lists**:
`passive`, `fitting`, `genome`, `conditions`. This is the same envelope; the
contents differ substantially.

### 4.1 Side-by-side

| Field | Perisomatic `473862496` | All-active `497233292` |
|---|---|---|
| `passive[0]` | `{ra: 95.8898309982, cm: [soma 1.0, axon 1.0, dend 3.0836283, apic 3.0836283], e_pas: -94.8687744140625}` | `{ra: 100}` **only** |
| `genome` length | 16 | 42 |
| `genome` value type | `float` (16/16) | `str` (42/42) |
| `genome` names | `g_pas`×4, `gbar_Ca_HVA`, `gbar_Ca_LVA`, `gbar_Ih`, `gbar_Im`, `gbar_K_P`, `gbar_K_T`, `gbar_Kv3_1`, `gbar_NaTs`, `gbar_Nap`, `gbar_SK`, `decay_CaDynamics`, `gamma_CaDynamics` | `Ra`×4, `cm`×4, `e_pas`×4, `g_pas`×4, `gbar_Ca_HVA`×2, `gbar_Ca_LVA`×2, `gbar_Ih`×3, `gbar_Im_v2`×2, `gbar_K_T`, `gbar_Kd`, `gbar_Kv2like`, `gbar_Kv3_1`×4, `gbar_NaV`×4, `gbar_SK`×2, `decay_CaDynamics`×2, `gamma_CaDynamics`×2 |
| `conditions[0].celsius` | `34.0` | `34` (integer literal) |
| `conditions[0].v_init` | `-94.8687744140625` (= `e_pas`) | `-90` |
| `conditions[0].erev` sections | `soma` only | `soma`, `axon`, `apic`, `dend` |
| `conditions[0].dt` / `tstop` | absent | absent |
| `fitting[0].junction_potential` | `-14.0` | `-14.0` |
| `fitting[0].sweeps` | `[38]` | `[41]` |
| Mechanisms declared | 11 (`Im`, `Ih`, `NaTs`, `Nap`, `K_P`, `K_T`, `SK`, `Kv3_1`, `Ca_HVA`, `Ca_LVA`, `CaDynamics`) | 11 (`NaV`, `K_T`, `Kd`, `Kv2like`, `Kv3_1`, `SK`, `Ca_HVA`, `Ca_LVA`, `CaDynamics`, `Ih`, `Im_v2`) |

### 4.2 These are different parameterisations, not different numbers

The two documents differ in **where** parameters live, not merely in their values:

* **Perisomatic** puts `cm` and `e_pas` in `passive`, at section-**class**
  granularity, plus a single scalar `e_pas` applied to every section. `genome`
  then carries only per-mechanism conductances plus a global `g_pas` per class.
* **All-active** reduces `passive` to a single scalar `Ra`, and moves `Ra`, `cm`,
  `e_pas` **and** `g_pas` into `genome` as per-section-class entries. `passive`
  is structurally vestigial.

Allen's own loader expects exactly this split. `allensdk/model/biophysical/utils.py`
defines two classes:

* `Utils` (perisomatic) — `load_cell_parameters` reads `passive["e_pas"]` and
  iterates `passive["cm"]`, and formats genome values with `"%g" % p["value"]`.
* `AllActiveUtils(Utils)` (all-active) — `load_cell_parameters` comments out the
  `e_pas` and `cm` lines, reads only `passive["ra"]`, and coerces genome values
  with `float(p["value"])`.

`create_utils()` dispatches on `description.data["biophys"][0]["model_type"]`.

**This matters, and it is a trap.** Applying the perisomatic loader to the
all-active document fails three ways: `KeyError: 'e_pas'`, `KeyError: 'cm'`, and
`TypeError: must be real number, not str` on all 42 genome values. Applying the
all-active loader instead succeeds. The string-valued genome is therefore a
**serialisation convention of the all-active pipeline, not a defect**, and any
inspection that scores the two documents against one shared schema will produce a
false alarm. The inspection script checks each document against its own class
contract and refuses to cross-score.

### 4.3 Parameter mapping to the template

Both documents address only the four section **classes** — `soma`, `axon`, `dend`,
`apic` — never individual section indices. The perisomatic document additionally
uses no `glob` entries; the all-active document uses none either.

This is the finding that keeps the missing reconstruction (`491771090`) from being
a hard blocker: because parameters are class-level, they can be applied to any
morphology that Import3d instantiates with those four class names. The model will
run; it will simply not run on *Allen's* geometry.

The template supplies the section arrays. `allensdk/model/biophysical/cell.hoc`
is a 715-byte hoc template whose body is:

```hoc
begintemplate cell
public init
public soma, dend, apic, axon
...
proc init() {localobj nl, import
        all = new SectionList() ... forall delete_section()
}
proc simplify_axon() { ... }
create soma[1]
create dend[1]
create apic[1]
create axon[1]
endtemplate cell
```

`Utils.update_default_cell_hoc()` looks for `"cell.hoc"` in the manifest's
`neuron[0].hoc` list and rewrites the entry to the packaged absolute path via
`resource_filename`, raising `IOError("cell.hoc does not exist!")` if it cannot.
The morphology itself is then instantiated at runtime by
`utils.generate_morphology()`:

```python
swc = self.h.Import3d_SWC_read()
swc.input(morph_filename)
imprt = self.h.Import3d_GUI(swc, 0)
h("objref this"); imprt.instantiate(h.this)
h("soma[0] area(0.5)")
for sec in h.allsec():
    sec.nseg = 1 + 2 * int(sec.L / 40.0)
    if sec.name()[:4] == "axon": h.delete_section(sec=sec)
h("create axon[2]")
for sec in h.axon: sec.L = 30; sec.diam = 1; sec.nseg = 1 + 2*int(sec.L/40.0)
```

Two consequences worth recording:

* **The perisomatic model never uses the reconstructed axon.** It is deleted and
  replaced by two 30 µm, 1 µm-diameter stubs, unconditionally. Perisomatic `axon`
  parameters therefore address the stubs.
* **`nseg` is deterministic**, `1 + 2*int(L/40)`, so discretisation is not a free
  parameter and does not threaten reproducibility.

---

## 5. The executable dependency graph

Read from AllenSDK `v2.16.2` source, not inferred.

```
manifest.json  ──► Config.load(config_path)
   │                  └─ read_model_description()
   │                       model_file = biophys[0].model_file
   │                                   = ["manifest.json", "<id>_fit.json"]
   │                       └─ both merged into one Description
   ├─ biophys[0].model_type ──────► create_utils()  ──► Utils | AllActiveUtils
   ├─ biophys[1].axon_type ───────► AllActiveUtils(axon_type)   [read for BOTH classes]
   ├─ neuron[0].hoc ──────────────► HocUtils.initialize_hoc()
   │                                  load_file() × n, then h.celsius / h.v_init
   ├─ manifest[MORPHOLOGY] ───────► utils.generate_morphology()
   ├─ manifest[stimulus_path] ────► utils.setup_iclamp()  (NwbDataSet reads the NWB)
   ├─ manifest[output_path] ──────► save_nwb()
   ├─ manifest[MODFILE_DIR] ──────► nrnivmodl ./modfiles
   └─ runs[0].sweeps / sweeps_by_type ──► which sweeps to simulate
```

`HocUtils.initialize_hoc()` then reads `description.data['conditions'][0]` and
applies `celsius`, `v_init`, `dt` and `tstop` if present — confirming that
`conditions[0]` in the `fit.json` is the operative runtime configuration, not
documentation.

### Dependency table

| Dependency | Perisomatic | All-active | Available | Authoritative source | Identifier | Model-specific | Retrievable without AllenSDK |
|---|---|---|---|---|---|---|---|
| `fit.json` parameters | ✅ | ✅ | **Yes** | RMA wkf `497235792` / `568156386` | digest-pinned §3.1 | both (different files) | **Yes** — plain HTTP |
| `manifest.json` (runner entry) | ❌ | ❌ | **No** | not published | — | both | n/a — does not exist |
| `biophys[0].model_type` | ❌ | ❌ | **No** | manifest-only key | — | per class | n/a |
| `biophys[1].axon_type` | ❌ | ❌ | **No** | manifest-only key | — | **all-active only** | n/a |
| `neuron[0].hoc` list | ❌ | ❌ | **No** | manifest-only key | — | both | n/a |
| `runs[0].sweeps_by_type` | ❌ | ❌ | **No** | manifest-only key | — | both | n/a |
| `cell.hoc` template | ✅ | ✅ | **Yes** | AllenSDK `model/biophysical/cell.hoc` | 715 B, §3.3 | shared | **Yes** — raw GitHub |
| `import3d.hoc`, `stdgui.hoc` | ✅ | ✅ | via NEURON | **shipped with NEURON** | NEURON install | shared | comes with NEURON |
| `.mod` mechanisms | 12 (11 + `pas`) | 12 (11 + `pas`) | **Yes** | AllenSDK `test/model/peri_model/modfiles/` | 16 files, §3.4 | shared library | **Yes** — raw GitHub |
| morphology | substitute | substitute | **Yes** (SWC), **No** (fitted recon `491771090`) | RMA wkf `674389901` | 7 587 points | shared | **Yes** — plain HTTP |
| marker | ✅ | ✅ | **Yes** | RMA wkf `674389910` | 373 B | shared | **Yes** — plain HTTP |
| stimulus NWB | ✅ | ✅ | **Yes** | `data/nwb_cache/382982932.nwb` | 94 207 824 B | shared | already cached |
| `NwbDataSet` (stimulus reader) | ❌ | ❌ | **No** | `allensdk.core.nwb_data_set` | AllenSDK `v2.16.2` | shared | **No** — part of AllenSDK |
| NEURON interpreter | ❌ | ❌ | **No** | Yale / PyPI / conda-forge | ≥ 7.4 era API | shared | **No** |
| `nrnivmodl` + C compiler | ❌ | ❌ | **No** | NEURON distribution | — | shared | **No** |

**Mechanism coverage is exact.** The union of mechanisms declared across both
documents is 15: `CaDynamics`, `Ca_HVA`, `Ca_LVA`, `Ih`, `Im`, `Im_v2`, `K_P`,
`K_T`, `Kd`, `Kv2like`, `Kv3_1`, `NaTa`, `NaTs`, `NaV`, `Nap`, `SK` minus
`NaTa`, which is cached but **unused**. Plus `pas`, which is a NEURON built-in
inserted unconditionally by both loaders and is not a `.mod` file. All 15 required
sources are present. Each class uses 11 mechanisms plus `pas` = 12.

The two classes deliberately use **different channel subsets**: only `K_T`,
`Kv3_1`, `SK`, `Ca_HVA`, `Ca_LVA`, `CaDynamics`, `Ih` are shared. `Im` (perisomatic)
and `Im_v2` (all-active) are distinct mechanisms with distinct `SUFFIX` names.

---

## 6. Readiness assessment by model class

### 6.1 `Biophysical - perisomatic` (id `473862496`)

**CONDITIONALLY READY — the stronger of the two.**

| Aspect | Status |
|---|---|
| Descriptor intact and consistent | ✅ 16 genome values, all native floats |
| Maps to template | ✅ class-level only; `passive` carries `cm`/`e_pas` as `Utils` expects |
| Mechanism sources complete | ✅ 11 `.mod` + built-in `pas` |
| Loader identified | ✅ `Utils` (`load_cell_parameters` reads `passive["e_pas"]`, `passive["cm"]`) |
| Morphology | ⚠️ substitute — fitted recon `491771090` unavailable |
| Fitting data | ✅ single sweep, `[38]` = `C1LSCOARSE150216[14]`, +170 pA |
| Blocked by | missing `manifest.json`; no NEURON |

### 6.2 `Biophysical - all active` (id `497233292`)

**CONDITIONALLY READY — with two class-specific caveats absent from the perisomatic case.**

| Aspect | Status |
|---|---|
| Descriptor intact and consistent | ✅ 42 genome values, all strings, all coercible |
| Maps to template | ✅ class-level only; `passive` is `{ra}` by design |
| Mechanism sources complete | ✅ 11 `.mod` + built-in `pas` |
| Loader identified | ⚠️ **must** be `AllActiveUtils`; `Utils` raises `KeyError`/`TypeError` |
| Morphology | ⚠️ substitute — same unresolvable recon |
| Axon treatment | ⚠️ **`axon_type` is a free choice with no published value** |
| Fitting data | ✅ single sweep, `[41]` = `C1LSCOARSE150216[17]`, +230 pA |
| Blocked by | missing `manifest.json`; no NEURON; **plus** `axon_type` |

The `axon_type` variable is a genuine reproducibility defect specific to this
class. `create_utils()` executes
`axon_type = description.data["biophys"][1]["axon_type"]` for **both** model types,
and `AllActiveUtils.generate_morphology` branches on it:

* `"stub"` → delegate to `Utils.generate_morphology` (delete the reconstructed axon,
  create two 30 µm × 1 µm stubs).
* `"truncated"` (documented default, "Legacy model") → keep the reconstructed axon
  but delete everything beyond 60 µm and splice in two 30 µm sections whose
  diameters are read from the SWC at the cut point.

These produce **different cells**. Allen publishes no value for this cell. Any
all-active result must therefore record which branch was chosen, and must not be
compared with a run under the other branch. The perisomatic class has no
equivalent degree of freedom, which is a concrete reason to regard it as the
better-controlled of the two.

### 6.3 The shared caveat: the fitted geometry is unavailable

Both models name reconstruction `491771090`, which does not exist in the API. The
substitute SWC (`674389901`, recon `674389884`) parses cleanly and is internally
consistent with the specimen's published metadata:

| Quantity | SWC file | Published recon `674389884` | Agreement |
|---|---|---|---|
| Point types | 1: 1, 2: 5 169, 3: 1 533, 4: 884 | — | — |
| Dendrite nodes (types 3+4) | **2 417** | `number_nodes` = **2 417** | **exact** |
| Dendrite length | 2 951.65 µm | `total_length` = 2 875.157 µm | 2.7 % (different accounting) |
| Soma nodes | 1 | `soma_surface` = 557.67 µm² | not comparable |

The comparison is meaningful because both published metrics are **dendrite-only**:
`number_nodes` = 2 417 and `total_length` = 2 875.157 µm are Allen's morphology
summary statistics, which exclude the axon, and the SWC figures above are likewise
restricted to point types 3 and 4. The file separately contains 5 169 axon points
totalling 6 116.01 µm, which Allen's summary does not count. Both published values
are therefore being compared against the one thing they describe.

The 2.7 % length difference is consistent with a difference between
point-to-point summation and the reconstruction's own compartment accounting; it
is not evidence of a wrong file. The node count agreeing exactly, while the length
differs slightly, is the signature of the same geometry measured two ways rather
than two different geometries. The header records
`# generated by Vaa3D Plugin sort_neuron_swc` and
`# source file(s): D:/BatchProcessing/469985851/...`. Specimen `469985851` returns
zero rows in the Cell Types Database, so that path component is an internal
batch identifier, not a reference to a different specimen.

An exact node-count match with independently published metadata is the strongest
available evidence that the file is this cell's morphology. It remains, however,
**a different object from the one the parameters were fitted against**, and that
is a limitation on any claim of exact reproduction.

---

## 7. Environment compatibility

Inspected without changing anything. No package was installed, upgraded,
downgraded or removed.

| Component | Present | Version | Compatible with AllenSDK `v2.16.2`? |
|---|---|---|---|
| OS | Windows 26H2, x86-64 | — | ⚠️ NEURON not distributed here |
| Python | ✅ | **3.14.0** (64-bit, `C:\Python314`) | ❌ classifiers stop at 3.11 |
| NumPy | ✅ | **2.3.4** | ❌ `requirements.txt` pins `numpy<1.24` |
| pandas | ✅ | 2.3.3 | ❌ pins `pandas==1.5.3` |
| SciPy | ✅ | 1.16.3 | ❌ pins `scipy<1.11` |
| h5py | ✅ | 3.16.0 | ✅ |
| NEURON | ❌ | — | **not installed** |
| AllenSDK | ❌ | — | **not installed** |
| pynwb | ❌ | — | not installed (only needed by other Allen modules) |
| MSVC `cl` | ❌ | — | required by `nrnivmodl` on Windows |
| `make` | ❌ | — | required by `nrnivmodl` on Windows |
| `nrniv` / `nrnivmodl` | ❌ | — | — |
| MinGW `gcc` / `g++` | ✅ | `C:\MinGW\bin` | **not sufficient** — see below |

### 7.1 Would installing AllenSDK conflict?

**Yes, decisively, at release `v2.16.2`.** That release pins `numpy<1.24`,
`pandas==1.5.3` and `scipy<1.11`. The active environment carries NumPy 2.3.4,
pandas 2.3.3 and SciPy 1.16.3. Installing it would force a coordinated downgrade
of the entire scientific stack, and its classifiers stop at Python 3.11 whereas
the interpreter is 3.14.

AllenSDK `master` (commit `a56bd8ea`) has relaxed this: `numpy<2.5.0`,
`pandas>=1.5.3,<3`, `requires-python>=3.10`, classifiers 3.10–3.13. That is
compatible with NumPy 2.3.4 but **still does not claim Python 3.14**, and it is an
unreleased development state rather than a tagged release.

The Phase 0 document's statement that AllenSDK "pins numpy < 1.24" is therefore
**correct for the release**, and should be kept; the master relaxation is a
separate, clearly-dated fact.

**NEURON is not a dependency of AllenSDK in either ref.** It appears in no
`requirements.txt`, `setup.py` or `pyproject.toml`. The simulator was always a
user-supplied prerequisite, which is why installing AllenSDK would not, on its
own, make anything runnable.

### 7.2 NEURON is not installable here by any supported route

This is the hard blocker, and it is a property of the platform rather than of the
project.

| Channel | Finding |
|---|---|
| **PyPI** — `neuron` 9.0.2 (latest), `requires_python >= 3.10` | **Zero Windows artefacts across all 31 releases ever published.** Verified by enumerating every file in every release. Wheels exist only for `macosx_10_15_x86_64`, `macosx_11_0_arm64`, and `manylinux_2_27`/`manylinux_2_28` (x86_64 and aarch64). |
| **conda-forge** — 724 files, latest 9.0.1 | `osx-64` 304, `linux-64` 303, `osx-arm64` 63, `linux-aarch64` 54, **`win-64` 0**. |
| **MinGW `gcc`/`g++` present** | Insufficient. `nrnivmodl` on Windows expects an MSVC toolchain (`cl`, `make`), neither of which is on PATH. |
| **Yale standalone Windows installer** | The only supported Windows route. A manual install, therefore outside this phase's "no environment changes" rule. |
| **WSL2 / Linux container** | Fully supported; would supply both NEURON and `nrnivmodl`/`make` in one step. |

The practical conclusion: **do not attempt to run these models on native Windows.**
Use WSL2 or a Linux container, which also resolves the AllenSDK toolchain question
and satisfies `numpy<1.24` cleanly in an isolated environment.

---

## 8. Missing dependencies and blockers

Ordered by how much work each implies, not by severity.

| # | Blocker | Affects | Nature | Resolution |
|---|---|---|---|---|
| **B1** | **`manifest.json` is not published** | both | Structural, in the data | Must be authored. Its shape is fully documented by Allen's own fixtures (§5) and by the seven path keys `BASEDIR`, `WORKDIR`, `MORPHOLOGY`, `MARKER`, `MODFILE_DIR`, `stimulus_path`, `output_path`. Needs `biophys[0].model_type`, `biophys[1].axon_type`, `neuron[0].hoc = ["cell.hoc","stdgui.hoc","import3d.hoc"]`, and `runs[0].sweeps` + `sweeps_by_type`. |
| **B2** | **No NEURON on this platform** | both | Environmental | WSL2 or Linux container (preferred), or the Yale Windows installer. |
| **B3** | **No `nrnivmodl` / MSVC toolchain** | both | Environmental | Solved by B2. |
| **B4** | **`NwbDataSet` unavailable without AllenSDK** | both | Dependency | Either install AllenSDK in the isolated Linux environment, or read the stimulus directly with `h5py`. Note the runner assumes `NwbDataSet` returns **amperes** (`* 1.0e9` to reach nA), which for `382982932` is correct because its `conversion` is `1.0` — see §10.2. |
| **B5** | **Fitted reconstruction `491771090` does not exist** | both | Structural, in the data | Not resolvable. Use the specimen's published SWC and record the substitution explicitly. Parameter transfer is legitimate because all parameters are section-*class* level. |
| **B6** | **`axon_type` has no published value** | all-active only | Under-specified | Record the chosen branch in every result. `"stub"` reproduces the perisomatic axon treatment; `"truncated"` preserves the reconstructed axon to 60 µm. Do not compare across branches. |
| **B7** | **Marker file format mismatch** | both | Cosmetic | Allen's fixture declares `..._marker_m.swc`; the published asset is `..._m.marker` (comma-separated `x,y,z,radius,shape,name,comment,colors`, 6 rows). It is declared as `MARKER` but consumed by no Python code in the runner path, so it does not block execution. |
| **B8** | **AllenSDK release pins conflict with the live stack** | both (if AllenSDK used) | Version | Use an isolated environment, or avoid AllenSDK entirely: only `NwbDataSet` and the `Utils` logic are needed, and both are small. |

**B1 is the one that matters scientifically.** It is the difference between "Allen's
model" and "a model reconstructed from Allen's published parameters". Authoring the
manifest is unproblematic technically — Allen's fixtures provide a complete
template — but it must be recorded as an authored artifact, not a retrieved one,
and any result must say so.

---

## 9. The −14 mV junction potential: convention and implementation

Both descriptors declare `fitting[0].junction_potential = -14.0`. This is not
decoration — it is applied at runtime, and the implementation is worth stating
precisely because the sign is easy to get wrong.

`Utils.get_recorded_data` (`allensdk/model/biophysical/utils.py:309-326`) reads the
value and applies it to the simulated trace only, at output time:

```python
junction_potential = self.description.data["fitting"][0]["junction_potential"]
...
mV = 1.0e-3
v = (v - junction_potential) * mV
```

With `junction_potential = -14.0`, this is:

```
V_written = V_simulated - (-14.0)  =  V_simulated + 14.0   [mV]
```

Facts that follow, all verified:

* **It is an output-stage correction, not a model parameter.** NEURON is never
  told about it. The `conditions[0]` block, which *is* applied to the simulator
  (`h.celsius`, `h.v_init`), contains no junction term.
* **The sign is additive to the simulation.** A simulated resting potential of
  −80 mV is written as −66 mV.
* **It applies identically to both classes.** `AllActiveUtils` does not override
  `get_recorded_data`, so the all-active output is shifted by the same +14 mV.
* **It is applied before any comparison.** Allen's own fixture tests assert
  `numpy.array(vec['v']) - junction_potential` against the recorded trace, i.e.
  the reference data is compared in the *already-corrected* frame. Any comparison
  we perform must therefore be made either entirely inside that frame or entirely
  outside it — never mixing a raw simulated trace with a raw recorded trace.
* **The convention is preserved unmodified in this phase.** Both original
  descriptors are stored byte-identical; the value is recorded by the inspection
  script as `junction_potential_mv` and never rewritten.

Because both classes share the value, the junction potential is **not** a
confound in a perisomatic-versus-all-active comparison. It **is** a confound in a
model-versus-recording comparison if handled inconsistently, which is the reason
this section exists.

---

## 10. Fitting provenance

### 10.1 Both models are single-sweep fits

| Model | `fitting[0].sweeps` | Template | Index | Command | Recorded spikes |
|---|---|---|---|---|---|
| Perisomatic `473862496` | `[38]` | `C1LSCOARSE150216` | `[14]` | **+170.000000188 pA** | 14 |
| All-active `497233292` | `[41]` | `C1LSCOARSE150216` | `[17]` | **+230.000005152 pA** | 25 |

Both are **one sweep**. The objective each parameter set was optimised against was
therefore a single current-clamp trace, i.e. one stimulus amplitude and one
resulting spike train. This is a material limitation on how much the models can be
said to explain, and it is invisible from the model id.

### 10.2 Both fitting sweeps are inside the nominated COARSE block

Phase 1C nominated the 20 COARSE sweeps of `C1LSCOARSE150216`, which are sweeps
**24–43**, template indices `[0]`–`[19]`, amplitudes **−110 pA to +270 pA** in
20 pA steps. Verified directly against `data/metadata/sweep_inventory.csv`:

```
LSCOARSE: 20 sweeps  (sweeps 24-43,  C1LSCOARSE150216[0..19])
LSFINEST:  9 sweeps  (sweeps 44-52,  C1LSFINEST150112[0] repeated)
```

Sweep 38 is `C1LSCOARSE150216[14]`; sweep 41 is `C1LSCOARSE150216[17]`. Both are
inside the block.

**Consequence for analysis.** These two sweeps are **in-sample**. They are the data
the parameters were fitted to, and using them as evidence that the model reproduces
the cell would be circular. Of the 20 COARSE sweeps:

* **18 are eligible for held-out comparison** (all except 38 and 41).
* The perisomatic model can be held out on 19 of 20 (only 38 is in-sample).
* The all-active model can be held out on 19 of 20 (only 41 is in-sample).

This is a scope reduction Phase 2B must respect, and it is not a defect of the
design — it is a fact about the models Allen published.

### 10.3 The perisomatic model was fitted to the sweep Phase 1C flagged as anomalous

This is the most consequential finding in this phase, and it follows from §10.2
combined with Phase 1C §9.3.

Phase 1C §9.3 established, at matched command amplitude, that `382982932` responds
dichotomously depending on which protocol block the amplitude came from:

| Amplitude | COARSE (sweep 38) | FINEST (sweeps 49–52) |
|---|---|---|
| +170 pA | **14 spikes** | **1 spike** (4/4 sweeps) |

Sweep 38 — the 14-spike outlier — is precisely the sweep the perisomatic model was
fitted to.

So the perisomatic parameters were optimised to reproduce a response that Phase 1C
identified as not reproducible under an independent protocol at the same command.
The model therefore encodes the anomaly *by construction*. If a future simulation
of model `473862496` reproduces sweep 38 closely, that is evidence the loading and
integration are correct — **not** evidence that the model captures the cell's
physiology. The two claims must be kept strictly apart.

The all-active fit used sweep 41 (+230 pA), which FINEST never reaches (FINEST
stops at 170 pA), so the same specific anomaly does not apply to it. That is not a
point in its favour; it simply means the anomaly was not probed.

### 10.4 No tuning or fitting was performed in this phase

Nothing was optimised, re-fitted, or tuned against any sweep — held-out or
otherwise. The `fit.json` documents are stored exactly as Allen served them, and
their digests were independently re-verified. No COARSE and FINEST data were
pooled at any point.

---

## 11. Reproducibility instructions

### 11.1 Verify the cached assets (no network, no NEURON)

```sh
python scripts/inspect_model_assets.py --cache-dir tmp/model_cache
```

Expected: `77 checks, 0 failure(s)`, exit code `0`.

The script verifies SHA-256 against the values pinned in §3, parses both
descriptors, checks each against its own class contract, cross-checks the 15
required mechanisms against the 16 `.mod` sources, parses the SWC, and prints a
dependency-readiness table. It imports no NEURON and executes no simulation.

### 11.2 Prove the cache matches source (network, read-only)

```sh
python scripts/inspect_model_assets.py --verify-remote
```

Re-downloads the two `fit.json`, the SWC, the marker and `cell.hoc` into memory
and compares digests. Writes nothing. Expected: `82 checks, 0 failure(s)`.

### 11.3 Assert that the models are not yet executable

```sh
python scripts/inspect_model_assets.py --require-execution-ready
```

Expected: exit code `2`, listing the outstanding blockers. This is the machine-
checkable form of the §1 verdict.

### 11.4 Rebuilding the cache from scratch

The cache is disposable and regenerable. The retrieval recipe is fully specified
by §3:

```sh
# descriptors and morphology: plain HTTP, no authentication
curl -L -o perisomatic_fit.json \
  http://api.brain-map.org/api/v2/well_known_file_download/497235792
curl -L -o all_active_fit.json \
  http://api.brain-map.org/api/v2/well_known_file_download/568156386
curl -L -o 382982932_m.swc \
  http://api.brain-map.org/api/v2/well_known_file_download/674389901
curl -L -o 382982932_m.marker \
  http://api.brain-map.org/api/v2/well_known_file_download/674389910

# template and mechanisms: raw GitHub, pinned to the release tag
BASE=https://raw.githubusercontent.com/AllenInstitute/AllenSDK/v2.16.2
curl -L -o cell.hoc $BASE/allensdk/model/biophysical/cell.hoc
for m in CaDynamics Ca_HVA Ca_LVA Ih Im Im_v2 K_P K_T Kd Kv2like Kv3_1 \
         NaTa NaTs NaV Nap SK; do
  curl -L -o $m.mod $BASE/allensdk/test/model/peri_model/modfiles/$m.mod
done
```

No API key, no authentication, no AllenSDK installation is required for any of it.

### 11.5 What Phase 2B would add (not done here)

Only recorded so the boundary is explicit. Phase 2B would need, in an isolated
Linux/WSL2 environment: NEURON ≥ 7.4 with a working `nrnivmodl`; an authored
`manifest.json` per class (B1); a decision recorded for `axon_type` (B6); and a
stimulus reader. None of these was attempted.

---

## 12. Provenance and licensing

### 12.1 Provenance

| Asset class | Origin | Retrieval date | Verified |
|---|---|---|---|
| `fit.json` ×2 | Allen RMA API, `well_known_file_download` | this phase | ✅ re-downloaded, byte-identical |
| SWC, marker | Allen RMA API, same endpoint | this phase | ✅ re-verified (SWC, marker) |
| `cell.hoc`, 16 `.mod` | `github.com/AllenInstitute/AllenSDK`, tag `v2.16.2` | this phase | ✅ `cell.hoc` re-verified |
| Runner sources | same tag | this phase | code read, not executed |
| Stimulus NWB | cached in Phase 1, `data/nwb_cache/382982932.nwb` | Phase 1 | pre-existing |

All sources are **first-party**. No third-party mirror, fork, re-upload, or
community re-distribution was used, and none would have been acceptable in place of
an official source had one been unavailable — the brief's instruction was to
document the blocker rather than substitute. The one substitution made is
*documented and first-party*: the model's own reconstruction is unpublished, so the
specimen's own published SWC is used instead (§6.3).

### 12.2 Licensing and redistribution

The AllenSDK is released under the **Allen Institute Software License**, which is
the 2-clause BSD license **plus a third clause prohibiting redistribution for
commercial purposes** without written permission. The full text is cached at
`reference/LICENSE_v2.16.2.txt` and the header appears verbatim in every source
file retrieved.

Because of that third clause:

* **No model asset has been committed to Git.** The descriptors, morphology,
  template, mechanisms and runner sources all live in a Git-ignored directory.
* The committed inspection script contains **digests and metadata only** — no Allen
  source code, no parameter values beyond what is needed to verify a file's
  identity.
* **Redistribution permissions have not been verified** and should be treated as
  not granted. This repository is non-commercial academic work, which is
  consistent with the license, but committing the assets would still be
  redistribution and is therefore avoided.
* The Cell Types Database *data* may carry different terms from the *software*. No
  conclusion is drawn here about the `fit.json` files' status as data rather than
  code; the conservative position (do not commit) is taken for both.

### 12.3 What was deliberately not done

* No additional NWB files were downloaded.
* No third-party or mirrored copies were fetched.
* No `fit.json` was edited, re-serialised, reformatted or "fixed" — including the
  all-active document's string-valued genome, which is correct for its loader.
* No Phase 0 inventory, manifest or candidate ranking was modified.

---

## 13. Confirmation: no model simulation was executed

**No NEURON simulation was run. No voltage trace was generated.**

Specifically, in this phase:

* NEURON was never imported, and is not installed.
* `nrnivmodl` was never invoked; no `.mod` file was compiled; no `.dll`, `.o`, or
  `.mod` build output exists.
* No `manifest.json` was authored and no `runner.py` / `run_simulate.py` code path
  was executed.
* No model output NWB was created.
* No parameter was fitted, tuned, perturbed or re-estimated.
* No `fit.json` byte was modified; both descriptors are stored exactly as served
  and were re-verified against source by an independent download.

The only execution performed was the inspection script, which reads files, computes
SHA-256 digests, parses JSON and SWC text, and prints a report. It contains no
`import neuron` and no simulation call, and it states this in its own output.

---

## 14. What this phase does not license us to say

Stated explicitly so the boundary is not lost between phases.

* ❌ **"The Allen models have been validated."** They have not been compared with
  the recording at all. Nothing here is a reproduction check.
* ❌ **"The models reproduce the cell."** No simulation exists to check.
* ❌ **"The perisomatic model is biologically the more accurate of the two."**
  It is better *controlled* (no free `axon_type`), which is a reproducibility
  property, not an accuracy claim.
* ❌ **"The models capture the cell's firing."** The perisomatic model was fitted to
  the one sweep Phase 1C identified as protocol-dependent (§10.3).
* ❌ **"The model is Allen's exact model."** The fitted geometry is unavailable and
  a published substitute is used (§6.3).
* ❌ **"L2/3 and L5 differ in model requirements."** Only one specimen has been
  examined for model readiness. A single cell per layer cannot establish a layer
  effect, and `471129934` was explicitly out of scope.

---

## 15. Summary

**Verdict: CONDITIONALLY READY.**

The Phase 1C question — *what does the model download actually resolve to?* — is
now answered precisely. It resolves to **one `fit.json` per model**, and to nothing
else. Allen's runner needs a `manifest.json` as well, and that document is not
published. That gap is the whole distance between "the assets exist" and "the model
can be run", and it is closed by authoring a manifest, not by finding one.

Everything on the asset side is in good order: 23 digest-pinned files, no
corruption, no contradiction, exact mechanism coverage (15 required, 16 available,
`NaTa` unused), parameters that are section-class level and therefore transferable
to an available morphology, and a template that is 715 bytes of clearly readable
hoc. Both model classes are reconstructible.

Execution is blocked by environment, not by data. NEURON has **no Windows
distribution on PyPI or conda-forge** — zero artefacts across all 31 PyPI releases,
zero `win-64` builds of 724 conda-forge files — so the models cannot run on this
machine on any supported route. WSL2 or a Linux container resolves this, the
AllenSDK version conflict, and the `nrnivmodl` toolchain question in one move.

Three findings should shape Phase 2B more than the verdict does:

1. **Both models are single-sweep fits.** One trace of evidence each.
2. **Both fitting sweeps (38, 41) are inside the 20 COARSE sweeps.** They are
   in-sample and must be excluded from held-out evaluation, leaving 18 clean
   sweeps of the 20.
3. **The perisomatic model was fitted to sweep 38 — the 14-spike outlier that
   Phase 1C flagged.** Reproducing it would validate the *pipeline*, not the
   *biology*. That distinction has to survive into every subsequent report.

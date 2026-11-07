# Phase 2B — Geometry and Manifest Reproducibility Audit

**Repository:** `Patel-Princy/INCM_project`  **Branch:** `ashish-work`
**Specimen:** `382982932` (mouse VISp, L2/3, `Nr5a1-Cre;Ai14-177333.03.01.01`)
**Models:** perisomatic `473862496`, all-active `497233292`
**Reference stack:** AllenSDK `v2.16.2`, Allen RMA `api/v2`
**Predecessor:** `results/phase2/PHASE2A_MODEL_EXECUTION_READINESS.md`

---

## 1. Executive verdict

| Model | Id | Verdict |
|---|---|---|
| Biophysical — perisomatic | `473862496` | **REPRODUCIBLE WITH DOCUMENTED SUBSTITUTIONS** |
| Biophysical — all active | `497233292` | **UNDER-SPECIFIED** |

Neither model is exactly reproducible from published assets. One blocker is now
retired and three new facts replace it.

**The geometry question is answered, and the answer is better than Phase 2A
expected.** Reconstruction `491771090` has no row anywhere in the Allen database,
not even as a superseded record. But no part of Allen's runtime ever dereferences
`neuronal_model.neuron_reconstruction_id`. Both code paths that load a morphology
— `BiophysicalApi.cache_data` and `BiophysicalModuleReader.morphology_path` —
resolve it through `specimen → neuron_reconstructions`. The SWC that Allen's own
tooling would load for model `473862496` today is therefore the specimen's
currently published reconstruction, `674389884`. Using that file is not an
invention of ours; it is the documented resolution rule applied to this specimen.

**That substitution is auditable, not merely plausible.** Of the eleven geometric
summaries Allen publishes for reconstruction `674389884`, eight reproduce
exactly from the downloaded SWC — `number_nodes` (2417), `total_length`
(2875.15684072065 µm), `overall_depth` (145.5314 µm), `number_stems` (9),
`number_tips` (33), `number_bifurcations` (24), `number_branches` (57) and
`max_branch_order` (6.0). `total_length` agrees to the last digit the API prints.
The three that do not reproduce (`overall_height`, `overall_width`,
`soma_surface`) are computation-convention differences, identified in §4.4.

**The manifest question is also answered, and Phase 2A had it wrong in two
places.** `axon_type` is *not* a manifest field: `runner.load_description`
appends `{"axon_type": ...}` to `description.data["biophys"]` and `create_utils`
then reads `biophys[1]`. Authoring it in the manifest would shift that appended
entry to index 2 and misdispatch the model. The value arrives on the command line
as `--axon_type`, `choices=['stub','truncated']`, default `truncated`.

**What remains genuinely unresolved is narrower and sharper.** For the all-active
model, *which* of the two validated axon configurations was used cannot be
established from any Allen record — not the model row, not the template row, not
the descriptor, not any well-known file. The database stores 104 all-active
models against a single template id and a three-column template table in which
the strings `stub`, `truncat` and `axon` appear zero times. That is why the
all-active configuration is classified **UNDER-SPECIFIED** rather than
reproducible.

Two further defects were found in AllenSDK `v2.16.2` itself, both of which shape
the drafts:

1. **`sweeps_by_type` is required but not emitted.** `runner.run_sync` reads
   `run_params['sweeps_by_type']` unconditionally at line 119, while
   `BiophysicalApi.create_manifest` writes only `sweeps`. A manifest produced by
   Allen's own public downloader therefore cannot be run by `run_sync` without
   editing. We derive the missing key from the documented
   `sweep_numbers_by_type()` rule.
2. **The all-active fixture test does not run.** `test_biophysical_all_active.py`
   calls `AllActiveUtils(description)` with one argument against a signature that
   requires two, so Allen's all-active reference fixture is not an executable
   reference.

No simulation was executed. No NEURON import, no `.mod` compilation, no voltage
trace, no parameter change, no environment change, no additional NWB download.

---

## 2. What Phase 2A left open, and what Phase 2B settles

| Phase 2A statement | Status | Phase 2B finding |
|---|---|---|
| "Reconstruction `491771090` does not resolve." | **Confirmed** | No row, live or superseded, and no well-known file attached to that id. |
| "The specimen's published reconstruction is a substitute." | **Revised** | It is the result of Allen's own resolution rule. `neuron_reconstruction_id` is never read at run time. |
| "`axon_type` has no published value; must be recovered." | **Retired** | Not a manifest field. It is a CLI option with a documented default. |
| "`manifest.json` is not published; must be authored." | **Confirmed** | `fit.json` is complete as published. Allen's own fixture `fit.json` has the same four sections. |
| "`neuron[0].hoc` list is not identified." | **Resolved** | `["stdgui.hoc","import3d.hoc"]`, a constant in `create_manifest` and in both fixtures. |
| "`runs` and sweep selection needed." | **Confirmed, plus defect** | `sweeps` is recoverable; `sweeps_by_type` must be derived because the generator omits it. |
| "`MARKER` is required in the manifest." | **Revised** | Written by the manifest generator, read by nothing at run time. Allen's own fixture ships the reference without the file. |

The decisive Phase 2A worry — that the published download might be a truncated
artefact — is disproved. Allen's own `allensdk/test/model/peri_model/
468193142_fit.json` (2891 B, sha256 `721220dcd3c06e59…`) has top-level keys
`conditions`, `fitting`, `genome`, `passive` and nothing else. That is exactly
what our two descriptors contain. `biophys`, `neuron`, `runs` and `manifest` were
never in `fit.json`; the split is by design, not truncation.

---

## 3. The reconstruction investigation

### 3.1 The reference under audit

| Property | Value |
|---|---|
| `NeuronalModel` id | `473862496` (perisomatic), `497233292` (all-active) |
| `neuron_reconstruction_id` | `491771090` for both |
| `neuronal_model_template_id` | `329230710` (perisomatic), `491455321` (all-active) |
| `specimen_id` | `382982932` |
| Parameter document | WKF `497235792` → `prod312/neuronal_model_473862496/382982932_fit.json` |
| Parameter document | WKF `568156386` → `prod583/neuronal_model_497233292/497233292_fit.json` |

The model's own `name` carries the cell identity:
`Biophysical - perisomatic_Nr5a1-Cre;Ai14-177333.03.01.01`. The downloaded SWC is
served as `Nr5a1-Cre_Ai14-177333.03.01.01_674389884_m.swc`. The cell name in the
filename is the cell name in the model record, which is independent evidence that
`674389884` is a reconstruction of *this* cell rather than of another specimen.

### 3.2 What the database returns for the reference

Query route (all RMA calls take this shape):

```
http://api.brain-map.org/api/v2/data/<Model>/query.json?criteria=[<predicate>]&num_rows=all
```

| Query | Result |
|---|---|
| `NeuronReconstruction` where `id$eq491771090` | **0 rows** |
| `WellKnownFile` where `attachable_id$eq491771090` | **0 rows** |
| `NeuronReconstruction` where `specimen_id$eq382982932` | **1 row**: `674389884` |
| `Reconstruction 674389884` | type `full`, `superseded = false`, 2417 nodes |
| `WellKnownFile` on that reconstruction | `674389901` (SWC), `674389910` (marker), `487661131` (thumbnail) |

Three possibilities were considered: deleted, never published, or referenced
incorrectly.

**Not "referenced incorrectly".** Across all 201 specimens that carry a
biophysical model, no model ever points at a reconstruction belonging to a
different specimen. Where the reference resolves, `recon.specimen_id` matches
`model.specimen_id` in **256 of 256** cases. The foreign key is semantically
sound; only its referent is missing.

**Not a soft supersede.** `NeuronReconstruction.superseded` is a live mechanism:
33 of 701 sampled rows are `true`. `491771090` appears in neither the live set nor
the superseded set. It was hard-deleted or re-created, not retired.

**A systematic re-registration, not a one-off.** Of 201 distinct
reconstructions referenced by the 293 biophysical models in the Phase 0
inventory, **177 resolve and 24 do not**. For every one of the 24 affected
specimens:

| Outcome | Specimens |
|---|---|
| Still publishes at least one reconstruction | 22 / 24 |
| Publishes exactly one reconstruction | 19 / 24 |
| Publishes nothing | 2 / 24 |

The 24 dangling ids span `491119336`–`514342545`; the reconstructions those
specimens publish today span `650160511`–`760239945`. The dangling ids are
*interleaved* with 145 resolving ids in the same numeric range, so this is not a
clean whole-batch deletion. It is consistent with individual specimens having
their morphology re-registered under a new id while the model row kept the old
one.

The strongest single piece of supporting evidence is that three of the affected
specimens now hold **two** reconstructions of the same cell with near-identical
geometry:

| Specimen | Reconstruction | Nodes | `total_length` (µm) |
|---|---|---|---|
| `321708130` | `657210204` | 1971 | 2336.9303 |
| `321708130` | `759896998` | 1970 | 2335.8309 |
| `473540161` | `657256518` | 1938 | 2263.6627 |
| `473540161` | `760239945` | 1934 | 2262.9536 |
| `478110866` | `650160511` | 3606 | 4063.6816 |
| `478110866` | `759946058` | 3599 | 4052.7984 |

Allen demonstrably holds duplicate registrations of one morphology whose node
counts differ by less than 0.2%. Re-registration of the kind that would strand
`491771090` is a normal event in this database, not an anomaly.

### 3.3 Why `neuron_reconstruction_id` cannot be the retrieval key

This is the pivot of the whole phase, so the code is quoted.

`allensdk/api/queries/biophysical_api.py`, `read_json`, line 194:

```python
if 'specimen' in neuronal_model:
    specimen = neuronal_model['specimen']
    if 'neuron_reconstructions' in specimen:
        for neuron_reconstruction in specimen['neuron_reconstructions']:
```

`allensdk/internal/api/queries/biophysical_module_reader.py`,
`morphology_file_entries`, line 166:

```python
neuronal_model = self.lims_data['neuronal_model']
specimen = neuronal_model['specimen']
reconstructions = specimen['neuron_reconstructions']

for reconstruction in reconstructions:
    superseded = reconstruction['superseded']
    manual = reconstruction['manual']
    if manual == True and superseded == False:
```

Both descend from the **model** to the **specimen**, then enumerate the
specimen's reconstructions and filter on `superseded`. Neither reads
`neuronal_model.neuron_reconstruction_id`. That column is provenance metadata for
the fitting run; it is not a retrieval key, and its dangling value cannot break a
download.

The practical consequence: the morphology Allen's own tooling resolves for model
`473862496` today is the specimen's non-superseded reconstruction, whose SWC is
`674389901` — the file audited in §4.

### 3.4 Verdict on the missing reconstruction

> `491771090` cannot be recovered. It has no row, no attached file, and no
> superseded record. No alternative reconstruction id can be established as its
> exact equivalent, because the deleted row retains no geometry to compare
> against.

What *can* be established, and is the stronger practical statement:

> The morphology that Allen's own documented resolution rule returns for this
> model is reconstruction `674389884`, file `674389901`. Its geometry is fully
> audited in §4. Whether `491771090` described the same cell is unprovable; that
> it was *the same specimen's* morphology at fit time is the only reading
> consistent with the cohort pattern, but it remains an inference and is labelled
> as one throughout.

---

## 4. Morphology comparison

### 4.1 The file

| Property | Value |
|---|---|
| Well-known file | `674389901` (type `3DNeuronReconstruction`, `303941301`) |
| Served name | `Nr5a1-Cre_Ai14-177333.03.01.01_674389884_m.swc` |
| Local path | `tmp/model_cache/morphology/674389901_382982932_m.swc` |
| Size | 335 924 B |
| SHA-256 | `71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c` |
| Data rows | 7587 across 4 comment lines |

### 4.2 Node census

| SWC type | Class | Nodes | Share |
|---|---|---|---|
| 1 | soma | 1 | 0.01 % |
| 2 | axon | 5169 | 68.13 % |
| 3 | basal dendrite | 1533 | 20.21 % |
| 4 | apical dendrite | 884 | 11.65 % |

No type outside 1–4 occurs, and there are no dangling parents. The soma is a
single node (r = 7.1424 µm), which is Allen's standard `_m` convention rather than
a defect.

Note that `number_nodes = 2417` counts **only** types 3 and 4. The axon's 5169
nodes are excluded from the published count and from `total_length`, even though
the file contains them.

### 4.3 Metric-by-metric reproduction

| Field | Published | Recomputed from the SWC | Match |
|---|---|---|---|
| `number_nodes` | 2417 | 2417 (types 3 + 4) | exact |
| `total_length` | 2875.15684072065 | 2875.1568407206 | exact |
| `overall_depth` | 145.5314 | 145.5314 (z extent) | exact |
| `number_stems` | 9 | 9 | exact |
| `number_tips` | 33 | 33 | exact |
| `number_bifurcations` | 24 | 24 | exact |
| `number_branches` | 57 | 57 | exact |
| `max_branch_order` | 6.0 | 6.0 | exact |
| `overall_height` | 533.3783 | 557.2047 (raw y extent) | no |
| `overall_width` | 218.0993 | 444.7174 (raw x extent) | no |
| `soma_surface` | 557.6743 | 641.0593 (4·π·r²) | no |

Three of these agreements required identifying a convention rather than assuming
one, and the conventions are the point:

- **`total_length` excludes the stem connectors.** A naive sum over all dendritic
  segments gives 2951.6526 µm, which is 2.66 % high. Excluding the nine segments
  that bridge the soma to a dendritic stem gives 2875.1568406 µm — matching to
  the last digit the API prints. This is why the 2.66 % gap is evidence of a
  convention, not of a different cell.
- **`number_bifurcations` counts a trifurcation as two.** The tree contains 22
  nodes with two children and 1 with three. `Σ(children − 1)` = 24.
- **`number_branches` = `number_tips` + `number_bifurcations`** = 33 + 24 = 57.

> **This proves the downloaded SWC is the file that record `674389884`
> summarises.** It does **not** prove `674389884` and `491771090` are the same
> geometry. Equal node counts alone were explicitly not treated as proof; the
> ten-digit agreement on `total_length`, together with seven independent
> topological identities, is what raises the claim above the level of a
> plausibility argument — about a different proposition.

### 4.4 What cannot be reproduced, and why it does not undermine the identity

| Field | Published | Reason |
|---|---|---|
| `overall_height` | 533.3783 | Neither the raw y extent (557.2047) nor the dendrite-only y extent (526.2401). Computed in an aligned frame Allen does not document. |
| `overall_width` | 218.0993 | Raw x extent is 444.7174, i.e. a factor of 2.04 larger. Same cause. |
| `soma_surface` | 557.6743 | Implies r = 6.6617 µm; the single soma node has r = 7.1424 µm (ratio 0.870). Allen's surface convention for a one-point soma is not documented. |
| `total_surface`, `total_volume` | — | Require Allen's frustum/surface algorithm; not testable from the SWC alone. |

`overall_depth` *is* the raw z extent (145.5314 exactly), so the published metrics
and the SWC share a coordinate frame. The three mismatches are limited to
quantities that depend on Allen's own measurement code, and they are recorded as
a documented limitation rather than explained away.

### 4.5 Section-class mapping after Import3d

`Utils.generate_morphology` calls `Import3d_SWC_read()` → `Import3d_GUI(swc, 0)`
→ `imprt.instantiate(h.this)`. NEURON creates a `SectionList` per SWC type, so
`h.soma`, `h.axon`, `h.dend` and `h.apic` all exist. `nseg` is then fixed by the
deterministic rule `nseg = 1 + 2*int(L/40.0)`.

Both descriptors address exactly the classes the file provides:

| Descriptor surface | Classes referenced |
|---|---|
| `genome[*].section` | `soma`, `axon`, `dend`, `apic` |
| `passive[0].cm[*].section` (perisomatic) | `soma`, `axon`, `dend`, `apic` |
| `conditions[0].erev[*].section` (all-active) | `soma`, `axon`, `dend`, `apic` |

Every class a descriptor names is present in the SWC, so no parameter silently
fails to apply. With `cell.hoc` omitted from the manifest — as both Allen fixtures
and `create_manifest` do — no placeholder sections pre-exist, so the four
SectionLists map one-to-one onto the four SWC types without index ambiguity.

### 4.6 Axon handling

The reconstructed axon is 5169 nodes and 6116.008 µm of the file's 9067.661 µm
total neurite length. It is mostly discarded:

| Class / option | Axon treatment | Does the SWC axon reach the simulator? |
|---|---|---|
| Perisomatic (`Utils`) | All `axon*` sections deleted; `axon[2]` created, L = 30 µm each, diam = 1 µm; attached at `soma(0.5)` | **No** |
| All-active, `stub` | Identical to perisomatic (delegates to `super()`) | **No** |
| All-active, `truncated` | Two diameters read from the SWC, then all axon sections deleted; `axon[2]` at those diameters, L = 30 µm each; attached at `soma(1.0)` | **Two scalars only** |

The SWC's axon radii span 0.1144–0.2819 µm (diameters 0.229–0.564 µm) across 42
distinct values. Under `truncated` exactly two of them survive: the proximal axon
diameter and the diameter of the first axon section beyond 60 µm from the soma.
Under `stub` none survive.

So the substitution is behaviourally inert for the perisomatic model and for the
all-active model run with `stub`. Under `truncated` it is not inert, but its
influence is confined to two diameter scalars on a 60 µm stump — roughly a
fourfold thinner axon than the 1 µm stub.

---

## 5. Manifest schema and field provenance

### 5.1 Where the schema comes from

`BiophysicalApi.create_manifest` is Allen's own programmatic generator. It is the
authoritative description of a model download, and both shipped fixtures
(`allensdk/test/model/peri_model/manifest.json`,
`allensdk/test/model/aa_model/manifest.json`) match it exactly. It emits four
top-level sections:

| Section | Shape |
|---|---|
| `biophys` | `[{model_file: [manifest, fit], model_type}]` — exactly **one** entry |
| `runs` | `[{sweeps: [...]}]` |
| `neuron` | `[{hoc: ["stdgui.hoc", "import3d.hoc"]}]` |
| `manifest` | 7 path entries: `BASEDIR`, `WORKDIR`, `MORPHOLOGY`, `MARKER`, `MODFILE_DIR`, `stimulus_path`, `output_path` |

### 5.2 Three manifest variants exist in Allen's own tree

| Variant | Where | `hoc` list | `sweeps_by_type` |
|---|---|---|---|
| Public download | `BiophysicalApi.create_manifest` | 2 files | **absent** |
| Fixtures | `test/model/{peri,aa}_model/` | 2 files | absent |
| Internal pipeline | `biophysical_module_reader.to_manifest` | 3 files (+`cell.hoc`) | present, plus `neuronal_model_run_id`, `CODE_DIR`, `MOD_FILE_*` |

The drafts follow the **public download** variant, because that is what Allen
ships for a model record and what the SDK's own fixture tests exercise. The only
addition is `sweeps_by_type`, which the runtime requires (§5.4).

`cell.hoc` is omitted deliberately. In `v2.16.2` nothing reads the `axon_morph`
section, and `axon_morph` is the only consumer of the `all` and `axonal`
SectionLists that `cell.hoc` creates. The legacy template-driven axon replacement
was superseded by `--axon_type`. Note also that `runner.py` lists
`'axon_morph,'` — with a trailing comma — in `fix_sections`, so even that
reference never matches. `cell.hoc` is vestigial in this version.

### 5.3 Field-by-field provenance for the drafts

`R` = recovered from an Allen record · `C` = constant in Allen's generator ·
`D` = derived by an Allen rule · `S` = substituted · `X` = deliberately absent

| Field | Perisomatic value | All-active value | Src | Basis |
|---|---|---|---|---|
| `biophys[0].model_file[0]` | `manifest.json` | `manifest.json` | C | `create_manifest`: self-reference so `Config.read_model_description` pre-loads the manifest |
| `biophys[0].model_file[1]` | `382982932_fit.json` | `497233292_fit.json` | R | Basename of the `NeuronalModelParameters` well-known file |
| `biophys[0].model_type` | `Biophysical - perisomatic` | `Biophysical - all active` | R | `NeuronalModelTemplate` name; compared against `PERISOMATIC_TYPE` / `ALL_ACTIVE_TYPE` |
| `runs[0].sweeps` | sweeps 24–43 | sweeps 24–43 | D, restricted | Allen emits every non-`Test` sweep (73). Restricted to the `C1LSCOARSE` block so protocols are never pooled |
| `runs[0].sweeps_by_type` | 9 stimulus types, 80 sweeps | same | D | `sweep_numbers_by_type()` groups `ephys_sweeps` by stimulus-type name; not emitted by `create_manifest` |
| `neuron[0].hoc` | `stdgui.hoc`, `import3d.hoc` | same | C | `create_manifest` line 287; NEURON-shipped files |
| `manifest[BASEDIR]` | `.` | `.` | C | `create_manifest` |
| `manifest[WORKDIR]` | `work` (parent `BASEDIR`) | same | C | `create_manifest` |
| `manifest[MORPHOLOGY]` | `674389901_382982932_m.swc` | same | **S** | Reconstruction `491771090` has no file; `674389884` is what Allen's specimen-scoped rule returns |
| `manifest[MARKER]` | `674389910_382982932_m.marker` | same | **S** | Allen's spec convention is `<cell>_<recon>_marker_m.swc`; the published asset is `<cell>_<recon>_m.marker`. Renamed to the actual file; never read |
| `manifest[MODFILE_DIR]` | `modfiles` | same | C | `create_manifest` |
| `manifest[stimulus_path]` | `382982932.nwb` | same | R | The specimen's stimulus NWB; Allen names it `<ephys_result_id>.nwb` |
| `manifest[output_path]` | `382982932.nwb` under `work/` | same | C | `create_manifest` reuses the stimulus name under `WORKDIR` |
| `axon_type` | — | — | **X** | Not a manifest field; see §6 |
| `fitting[0].junction_potential` | `-14.0` | `-14.0` | R | From the descriptor |
| `fitting[0].sweeps` | `[38]` | `[41]` | R | From the descriptor |

The drafts are written to
`tmp/model_cache/manifest_drafts/{perisomatic,all_active}/` with a
`provenance.json` sidecar carrying the same table. `tmp/` is ignored at
`.gitignore:72`, so neither the manifests nor any staged asset can be committed.

### 5.4 `sweeps_by_type`: a real defect in AllenSDK

`allensdk/model/biophysical/runner.py`, `run_sync` line 119:

```python
run_params = description.data['runs'][0]
if sweeps is None:
    sweeps = run_params['sweeps']
sweeps_by_type = run_params['sweeps_by_type']
```

`BiophysicalApi.create_manifest` writes `runs[0] = {"sweeps": sweeps}` and
nothing else. A manifest produced by Allen's own downloader therefore raises
`KeyError` in `run_sync` on the first sweep. The internal pipeline does emit the
key — `biophysical_module_reader.py` line 405 — so the inconsistency is between
the public generator and the shared runner, not a misunderstanding on our part.

It is recoverable exactly, from the documented rule:

```python
d = {s['ephys_stimulus']['ephys_stimulus_type']['name']: [] for s in sweeps}
for s in sweeps:
    d[s['ephys_stimulus']['ephys_stimulus_type']['name']].append(s['sweep_number'])
```

The Phase 1C inventory already extracted that same stimulus-type name from the
NWB, so the key is regenerable offline with no new download. The drafts carry the
full 80-sweep census across 9 types. It is a lookup table; `save_nwb` consults
only the entries for the sweep being written.

### 5.5 A note on `biophys` arity

`create_utils` reads `description.data["biophys"][1]["axon_type"]`
unconditionally, for **both** model classes. Because `load_description` appends
that dict, `biophys` must have exactly one entry when the manifest is loaded. If a
manifest authored `biophys[1]`, the runner's append would land at index 2 and
`biophys[1]` would be the authored dict — a silent misdispatch when that dict
lacks `axon_type`. Both drafts therefore carry one entry, and the audit asserts
it.

`Utils` itself never reads `axon_type`, so constructing a perisomatic `Utils`
directly from a one-entry description is safe. The arity constraint applies to the
`runner` path, which is the path the manifest serves.

---

## 6. Axon configuration

### 6.1 What `axon_type` controls

`AllActiveUtils.generate_morphology`, `v2.16.2`:

```python
if self.axon_type == "stub":
    self._log.info("Replacing axon with a stub : length 60 micron, diameter 1 micron")
    super(AllActiveUtils, self).generate_morphology(morph_filename)
    return

self._log.info("Legacy model - Truncating reconstructed axon after 60 micron")
...
axon_diams = [self.h.axon[0].diam, self.h.axon[0].diam]
self.h.distance(sec=self.h.soma[0])
for sec in self.h.allsec():
    if sec.name()[:4] == "axon":
        if self.h.distance(0.5, sec=sec) > 60:
            axon_diams[1] = sec.diam
            break
...
self.h.axon[0].connect(self.h.soma[0], 1.0, 0.0)
```

Both branches discard the reconstructed axon and build a two-compartment 60 µm
stump. They differ in exactly three respects:

| Respect | `stub` | `truncated` |
|---|---|---|
| Axon diameters | 1 µm (both) | read from the SWC (0.229–0.564 µm) |
| Soma attachment | `soma(0.5)` | `soma(1.0)` |
| Code path | delegates to `Utils.generate_morphology` | its own inline implementation |

### 6.2 Valid values and defaults

| Property | Evidence |
|---|---|
| Legal values | `choices=['stub','truncated']` in `runner.sim_parser` |
| Default | `default='truncated'`, restated in the `AllActiveUtils` docstring as "*(default)*" |
| Injection point | `load_description`: `description.update_data({'axon_type': args_dict.get('axon_type','truncated')}, 'biophys')` |
| Consumption | `create_utils`: `axon_type = description.data["biophys"][1]["axon_type"]` |
| Applies to | All-active only; `Utils` ignores the value |

Two caveats. First, `AllActiveUtils.__init__` does not validate the string — any
value other than `"stub"` falls through to the truncating branch, so a typo
silently selects `truncated`. Second, Allen's documentation distinguishes model
generations: `doc_template/biophysical_models.rst` line 105 runs "legacy
all-active models" with no flag (= `truncated`) and line 106-107 runs "new
all-active models" with `--axon_type stub`. `test_runner.py` encodes the same
split, asserting that the legacy call carries no `stub` and labelling the
`--axon_type stub` call "Current all-active simulation call pattern".

### 6.3 Is the value recoverable for model `497233292`?

**No.** Every place it could plausibly be recorded was checked:

| Candidate source | Result |
|---|---|
| `NeuronalModel` row | 5 columns only: `id`, `name`, `neuron_reconstruction_id`, `neuronal_model_template_id`, `specimen_id`. No axon field |
| `NeuronalModelTemplate` row | 3 columns only: `description`, `id`, `name`. `491455321` = "Biophysical - all active" |
| Whole template table (7 rows) | occurrences of `stub` 0, `truncat` 0, `axon` 0 |
| Template separation | all 104 all-active models share template `491455321`; all 189 perisomatic models share `329230710`. No variant template exists to distinguish generations |
| `fit.json` | `fitting` has only `junction_potential` and `sweeps`. No `axon_morph`, no `axon_type` |
| Well-known files | one parameter document per model; nothing else attached to the model or its template |
| `axon_morph` presence | vestigial in `v2.16.2`; never read, and listed in `fix_sections` with a trailing-comma typo. Not a usable discriminator |

The descriptor is *invariant* to the choice: both branches apply the same
section-class parameters to the same two sections, differing only in geometry. So
no amount of descriptor analysis can recover which geometry was present when the
parameters were fitted.

### 6.4 Consequence of the ambiguity

| Aspect | Impact |
|---|---|
| Perisomatic model | **None.** `Utils` ignores `axon_type` entirely |
| All-active, `stub` vs `truncated` | Axon diameter changes ~4×; soma attachment moves 0.5 → 1.0 |
| Held-out comparison | Any all-active voltage trace carries this free parameter and must be reported with the value used |

Hence: the all-active configuration is **under-specified** in this one respect,
and the drafts record `truncated` as the assumed value — the argparse default and
the documented behaviour for legacy models — flagged as an assumption rather than
a recovered fact. Every future all-active result must state which value produced
it.

---

## 7. Static validation results

`scripts/audit_model_geometry_and_manifests.py` emits the drafts and validates
them without importing NEURON.

```
checks: 88   passed: 87   failed: 0   skipped: 1          (emitting mode)
checks: 89   passed: 88   failed: 0   skipped: 1          (--no-emit mode)
```

| Group | Checks | Result |
|---|---|---|
| Draft directory presence | 2 | pass |
| A. Reconstruction provenance and morphology identity | 23 | all pass (1 skipped: the `height`/`width`/`soma_surface` limitation) |
| B. Manifest schema and per-class dispatch | 57 | all pass, across the perisomatic and all-active blocks |
| C. Sweep-block integrity against the Phase 1C inventory | 7 | all pass |
| D. Execution readiness | 0 checks, 5 blockers | reported, never raised as failures |
| **Total (`--no-emit`)** | **89** | **88 passed, 0 failed, 1 skipped** |

Group C's 7 checks compare the selected sweeps against `data/metadata/sweep_inventory.csv`,
so the sweep block is validated against the Phase 1C extraction rather than against
the manifest itself.

Specific assertions worth naming:

| Assertion | Outcome |
|---|---|
| Manifest is valid JSON with exactly Allen's four sections | pass, both classes |
| `biophys` has exactly one entry; no `axon_type` authored | pass |
| `model_type` matches the loader constant | pass |
| `model_file[1]` names an existing descriptor in the draft directory | pass |
| Perisomatic `passive` keys are `{ra, cm, e_pas}`; all 16 genes are floats | pass |
| All-active `passive` keys are `{ra}`; all 42 genes are strings, all `float()`-coercible | pass |
| Every genome mechanism has a `.mod` source (11 mechanisms, `pas` built in) | pass |
| `junction_potential` = `-14.0` in both | pass |
| `MORPHOLOGY`, `MARKER`, `stimulus_path`, `MODFILE_DIR` all resolve | pass |
| `output_path` is written under `WORKDIR` | pass |
| `runs` carries `sweeps_by_type` | pass |
| The 20 selected sweeps are `C1LSCOARSE150216[0..19]`, index `k` ↔ sweep `24+k` | pass |
| Every selected sweep appears in exactly one `sweeps_by_type` entry | pass |
| Fitting sweeps 38 and 41 are selected and lie inside the COARSE block | pass |
| No FINEST sweep is selected | pass |
| 170 pA exists in both the COARSE and FINEST blocks | pass, recorded |

Exit behaviour: `0` all pass; `1` on any failure; `2` with
`--require-execution-ready` because five blockers remain (§8).

### 7.1 Fitting-sweep provenance

| Model | Fitting sweep | Protocol | Amplitude | Spikes |
|---|---|---|---|---|
| Perisomatic `473862496` | 38 | `C1LSCOARSE150216[14]` | +170.000 pA | 14 |
| All-active `497233292` | 41 | `C1LSCOARSE150216[17]` | +230.000 pA | 25 |

Both sweeps are inside the 20-sweep COARSE block and both are listed in the
drafts' `runs[0].sweeps`. **Neither is a held-out evaluation sweep.** Of the 20
COARSE sweeps, 18 remain independent of the fit; sweeps 38 and 41 must be
excluded from any held-out claim, and the drafts cannot express that distinction
because Allen's schema has no field for it.

Two further cautions carry forward from Phase 1C. FINEST sweeps 49–52 hold four
nominally identical 170 pA trials that differ from one another, and COARSE[14] is
also 170 pA with a very different spike count. The COARSE and FINEST blocks are
not interchangeable and are not pooled anywhere in these drafts.

---

## 8. Distinct classes of claim

Three different things are commonly conflated. Only the first is "the Allen
model".

1. **Reproducing Allen's original fitted model.** Requires the exact morphology
   present at fit time, the exact mechanism set, the exact NEURON version, and the
   exact axon configuration. The morphology is gone (`491771090` has no row); the
   axon configuration was never recorded. **This is not achievable.**
2. **Reconstructing an Allen-compatible model using substitute geometry.**
   The fitted parameters are exact, the mechanism set is exact, the schema is
   Allen's, and the morphology is the one Allen's own resolution rule returns.
   The axon configuration is an assumption. This is what the drafts describe, and
   it is what the perisomatic verdict names. **It is not the original Allen
   model**; it is a faithful re-execution of Allen's documented pipeline against
   the geometry Allen currently publishes for this cell.
3. **Building a new model inspired by Allen's parameters.** Changing geometry,
   mechanism set, or fitted values to suit a different question. Legitimate, but
   any comparison with the Allen recording would then measure our own choices as
   much as Allen's model. Not attempted in this phase.

Nothing in this report describes (2) or (3) as the original Allen model.

---

## 9. Remaining blockers

| # | Blocker | Scope | Consequence |
|---|---|---|---|
| B1 | NEURON is unavailable: no importable package, no `nrnivmodl`, no `cl`/`make`. PyPI ships **0 Windows artefacts across all 31 releases**; conda-forge has **0 `win-64` of 724 files** | both models | No simulation can run in this environment |
| B2 | `axon_type` for all-active is not recorded by Allen anywhere (§6.3) | all-active | Value must be declared as an assumption; results are conditional on it |
| B3 | `sweeps_by_type` is required by `run_sync` but not emitted by `create_manifest` (§5.4) | both | Authored value; derived exactly from a documented rule |
| B4 | `manifest.json` is not published (Phase 2A) | both | Authored value; schema is Allen's |
| B5 | Fit-time morphology identity cannot be confirmed: `491771090` has no row and no retained metrics (§3.4) | both | Geometry is the specimen's current publication, not a verified fit-time identity |
| B6 | AllenSDK `v2.16.2` pins `numpy<1.24`, `pandas==1.5.3`, `scipy<1.11`; the host has NumPy 2.3.4, pandas 2.3.3, scipy 1.16.3 on Python 3.14 | both | Running AllenSDK's own runner requires an isolated environment |
| B7 | Allen's all-active fixture test is broken: it calls `AllActiveUtils(description)` with one argument against a two-argument signature | all-active | The SDK cannot be used as an executable reference for the all-active class |

B1, B6 and B7 are environment and tooling problems. B2, B3, B4 and B5 are
property-of-the-record problems: they cannot be resolved by more work on our side,
only by declaration.

B1 and B6 are jointly resolved by the same move — a Linux or WSL2 container
providing both a NEURON build and a compatible scientific stack — which is why it
is the recommended next step.

---

## 10. Recommended next step

**Phase 2C:** create an isolated Linux/WSL2 environment, compile the 16 `.mod`
files, and run the perisomatic draft against **sweep 38 only**, comparing the
simulated trace with the recorded trace under the −14 mV convention
(`V_written = V_sim + 14 mV`, applied at output only, identically for both
classes).

That single run is the highest-information test available:

- Sweep 38 is the perisomatic fitting sweep, so agreement is a *pipeline*
  validation — it tests geometry loading, mechanism compilation, unit handling,
  sampling-rate handling and the junction convention end to end.
- It uses the model class with **no** unresolved configuration: perisomatic
  ignores `axon_type` entirely and discards the reconstructed axon, so the only
  substitution in play is the morphology itself, which §4 shows to be the file
  Allen's own rule returns.
- Sweep 38 is also the Phase 1C anomaly: COARSE[14] shows 14 spikes at 170 pA
  while the four FINEST 170 pA trials show 1 spike each. Agreement here confirms
  the pipeline; disagreement is informative rather than evidence of a pipeline
  fault.

The all-active model should not be run before B2 is declared, and when it is run
the axon configuration must be reported alongside the result.

**Explicitly out of scope for Phase 2C:** held-out evaluation on COARSE sweeps
other than 38, any use of the FINEST block, any refitting, any change to the
fitted parameters, and any claim about layer differences between specimens
`382982932` and `471129934`.

---

## 11. What was not done

Confirmed by construction, not by assertion:

| Constraint | Status |
|---|---|
| Only specimen `382982932` | Held |
| No additional NWB downloads | Held; the existing `data/nwb_cache/382982932.nwb` was hard-linked, not re-fetched |
| No NEURON installation, no package installation, no environment change | Held; the audit reports NEURON as unimportable rather than attempting to fix it |
| No NEURON simulation, no voltage trace generation | Held; no model was instantiated |
| No FHN work | Held |
| No parameter fitting or modification | Held; both descriptors are byte-identical to the published files and were hard-linked, never edited |
| Phase 0 inventories and rankings unchanged | Held; no file under `data/metadata/` was written |
| Model assets and manifest drafts ignored and outside Git | Held; all under `tmp/`, ignored at `.gitignore:72` |
| `main` untouched | Held |

One capability was added that Phase 2A did not use: the AllenSDK `v2.16.2` tag
tarball (49 584 417 B) was saved and extracted under `tmp/model_cache/2b/src/` so
that `axon_type`, `sweeps_by_type` and the two manifest variants could be read
from primary source rather than inferred. It is ignored scratch, not an
installation.

The one artifact of that source that changed a conclusion: Allen's own fixture
`fit.json` proves the four-section split is by design (§2), which retires the
Phase 2A hypothesis that the published descriptor might be incomplete.

---

## 12. Reproducing this audit

```bash
# 1. assets must already be in the ignored cache (Phase 2A)
python scripts/inspect_model_assets.py --verify-remote

# 2. emit both drafts and run every static check
python scripts/audit_model_geometry_and_manifests.py

# 3. re-validate without rewriting the drafts
python scripts/audit_model_geometry_and_manifests.py --no-emit

# 4. assert that no model can actually run yet
python scripts/audit_model_geometry_and_manifests.py --no-emit --require-execution-ready
```

The API evidence behind §3 was gathered with these calls. Each is a plain
`GET`; `num_rows=all` is the default for the cohort query.

```
NeuronReconstruction/query.json?criteria=[id$eq491771090]
NeuronReconstruction/query.json?criteria=[id$eq674389884]
NeuronReconstruction/query.json?criteria=[specimen_id$eq382982932]
WellKnownFile/query.json?criteria=[attachable_id$eq491771090]
NeuronReconstruction/query.json?criteria=[id$in<40 ids>]
NeuronalModelTemplate/query.json?num_rows=all
NeuronalModel/query.json?criteria=[id$eq497233292]
```

Two query forms do **not** work on this endpoint and are recorded so the next
phase does not retry them. A `$like` predicate is rejected by the parser
(`extraneous input ... expecting RBRACKET`), so substring searches on
`WellKnownFile.path` are impossible and the `attachable_id` query — the
authoritative linkage — has to stand alone. The `?q=model::X[rma::criteria,...]`
form returns the error text in `msg` with `success: true`, so a caller that
indexes `msg` without checking its type reads characters of an error string.

Result digests, so a re-run can be compared directly:

| Artifact | Size | SHA-256 (prefix) |
|---|---|---|
| `assets_2a.json` descriptor count | 31 | — |
| Perisomatic `fit.json` | 2891 B | `d24d00aaed5a2a0e…` |
| All-active `fit.json` | 5738 B | `bcffd56bbcec001b…` |
| SWC `674389901` | 335 924 B | `71bb551b6ed6ce2f…` |
| Marker `674389910` | 373 B | `3cc83ad85e7caebd…` |
| Perisomatic draft `manifest.json` | 2983 B | emitted deterministically |
| All-active draft `manifest.json` | 2982 B | emitted deterministically |

---

## 13. Provenance and licensing

| Asset | Source | Licence |
|---|---|---|
| `fit.json` (both) | RMA well-known files `497235792`, `568156386` | Allen Institute Terms of Use |
| SWC `674389901` | RMA well-known file, reconstruction `674389884` | Allen Institute Terms of Use |
| Marker `674389910` | RMA well-known file `3DNeuronMarker` | Allen Institute Terms of Use |
| 16 `.mod` files | AllenSDK `v2.16.2` `model/biophysical/modfiles/` | Allen Institute Software License |
| `cell.hoc`, `stdgui.hoc`, `import3d.hoc` | AllenSDK `v2.16.2`; the latter two ship with NEURON | Allen Institute Software License / NEURON |
| `manifest.json` schema | `BiophysicalApi.create_manifest` | Allen Institute Software License |
| `sweeps_by_type` rule | `BiophysicalModuleReader.sweep_numbers_by_type` | Allen Institute Software License |

The Allen Institute Software License is BSD-2-Clause plus a third clause
prohibiting commercial redistribution without written permission. None of these
assets may be redistributed commercially, and none is redistributable as a bundle
without reviewing that clause. Every asset and every draft therefore remains in
the ignored cache and out of version control. What is committed is the audit
script and this report — analysis, not data.

---

**End of Phase 2B.** No simulation was executed, no model was instantiated, and
no published parameter, descriptor, fixture or Phase 0 inventory was modified.

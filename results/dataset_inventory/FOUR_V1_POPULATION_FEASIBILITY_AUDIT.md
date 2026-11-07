# Four V1 Neuronal Population Feasibility Audit

**Phase:** 0B — population feasibility, not model implementation
**Repository:** `Patel-Princy/INCM_project` · **Branch:** `ashish-work`
**Date:** 2026-11-07
**Scope:** VISp (primary visual cortex), *Mus musculus*, Allen Cell Types Database
**Status:** complete; **four layer-defined populations are feasible, four
projection-defined populations are not**

This audit does not train, fit, execute, download or modify any model. It reads
only the Phase 0 inventory that is already committed, plus one recorded
identity-schema probe. Every count below is reproducible with:

```
python src/data_audit/four_population_audit.py --print-tables
```

Evidence labels used throughout:

| Label | Meaning |
|---|---|
| **OBSERVED** | read directly from a committed inventory column or a validated report |
| **DERIVED** | computed from those values by a named, scripted rule |
| **ASSUMED** | a convention the inventory cannot prove (e.g. a Cre line as an indirect class marker) |
| **UNAVAILABLE** | the database does not carry the information at all |

---

## 1. Executive verdict

1. **Recording capacity is not the constraint.** All 1,588 VISp mouse
   specimens have long-square current-clamp data (1,585 after three failed
   recordings), and every non-failed specimen has at least two distinct
   depolarising amplitudes and a resolved NWB reference. **OBSERVED/DERIVED**
2. **The constraint is model + morphology + identity.** Only 194 of the 1,546
   four-layer specimens carry a biophysical model, and only 192 of those also
   have a usable morphology asset (the two missing cells are the only
   model-bearing specimens without a usable reconstruction). **DERIVED**
3. **Four *layer-defined* populations are feasible.** Layer-level eligibility
   is A 63, B 30, C 79, D 20. Restricting to spiny (putative excitatory)
   dendrite type gives A 54, B 7, C 41, D 8, with perisomatic models in 54, 6,
   39 and 8 specimens respectively. All four groups clear a 3–4 neuron
   planning target. **DERIVED**
4. **Four *projection-defined* populations are not feasible on this database.**
   There is no projection, cell-class or transcriptomic-type field in
   `model::Specimen` (probe evidence in §6). Using the strongest indirect
   evidence available (layer + spiny dendrite + a class-compatible Cre line),
   the identity-compatible counts are A 47, B 2, C 15, D 5. Group B fails the
   3–4 target and has zero specimens with both model classes. **DERIVED**
5. **No specimen can be labelled CONFIRMED.** The strongest honest label is
   PROBABLE, and only where three independent indirect features converge.
   Layer alone never establishes a projection class. **DERIVED**
6. **Recommendation to the supervisor:** say yes to *four layer-defined V1
   excitatory populations*, no to *four projection-defined populations*, and no
   to calling the L2/3 group "IT". Details in §8–§10.

Consistency block (DERIVED; every value is also asserted by
`tests/test_four_population_audit.py`):

- final eligible: A=63, B=30, C=79, D=20
- both model classes: A=27, B=23, C=32, D=6
- identity-compatible final: A=47, B=2, C=15, D=5
- identity confidence: A=PROBABLE, B=LAYER-ONLY, C=PROBABLE, D=PROBABLE

---

## 2. Biological rationale for the four candidates

The four candidates follow canonical V1 feed-forward and feedback streams. They
are *hypotheses for selection*, not labels the database can assign.

| Group | Layer | Proposed identity | Biological reason to expect a distinct phenotype |
|---|---|---|---|
| A | 4 | excitatory spiny stellate / IT-like | thalamorecipient layer; strong, fast feed-forward drive; distinctive input integration and firing onset |
| B | 2/3 | IT pyramidal | first cortico-cortical output stage; strong recurrent excitation; rate/adaptation profile differs from L5 |
| C | 5 | ET/PT pyramidal | thick-tufted output to subcortical targets; prominent adaptation and burst behaviour; largest dendritic tree |
| D | 6 | corticothalamic | feedback to thalamus; distinctive membrane time constant and spindle/adaptation behaviour |

The scientific rationale is biological, but the *evidence* available to
distinguish these classes is thin:

- **UNAVAILABLE:** projection target, projection class (IT/ET/PT/CT), cell
  class, transcriptomic type, and any axonal projection annotation. The
  `model::Specimen` payload carries 27 fields and none of them are a projection
  field (§6.2).
- **OBSERVED:** cortical layer (`cortical_layer`), coarse dendrite type
  (`spiny` / `aspiny` / `sparsely spiny`), apical-dendrite reconstruction
  status, driver/reporter line, genotype, layer-resolved structure id.
- **ASSUMED:** that a Cre line historically used to target a layer or class is
  an indirect marker of that class. This is an assumption, not a measurement,
  and it is why the ceiling is PROBABLE.

Consequently the audit tests a *layered* biological question (do these four
laminae contain enough well-recorded, well-modelled excitatory neurons?) and a
*weaker* class question (does converging indirect evidence support the proposed
identity?). It never converts the first into the second.

---

## 3. Exact specimen counts and filtering stages

Denominator: **1,588** VISp mouse specimens (**OBSERVED**, `cell_inventory.csv`).
Four layers contain **1,546** specimens; the 42 L1 specimens are outside all
four candidates and are never counted in a group. Group totals are
458 / 311 / 505 / 272 (**OBSERVED**).

Stage definitions are in `src/data_audit/four_population_audit.py::STAGES`.
Stages 2–6 are sequential; stages 7–11 are facets computed over stage 6; stage
12 is the final intersection.

### 3.1 Twelve-stage funnel

Percentages are of the group's own stage-1 total. `n` is specimens, not
recordings or models, and each specimen appears once.

| # | Stage | A n | A % | B n | B % | C n | C % | D n | D % |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Total mouse V1 specimens | 458 | 100.0 | 311 | 100.0 | 505 | 100.0 | 272 | 100.0 |
| 2 | Long-square current clamp | 457 | 99.8 | 311 | 100.0 | 503 | 99.6 | 272 | 100.0 |
| 3 | Depolarising long square | 457 | 99.8 | 311 | 100.0 | 503 | 99.6 | 272 | 100.0 |
| 4 | ≥ 2 distinct amplitudes | 457 | 99.8 | 311 | 100.0 | 503 | 99.6 | 272 | 100.0 |
| 5 | Sufficient conditions | 457 | 99.8 | 311 | 100.0 | 503 | 99.6 | 272 | 100.0 |
| 6 | Downloadable NWB | 457 | 99.8 | 311 | 100.0 | 503 | 99.6 | 272 | 100.0 |
| 7 | Perisomatic model | 63 | 13.8 | 28 | 9.0 | 71 | 14.1 | 21 | 7.7 |
| 8 | All-active model | 28 | 6.1 | 25 | 8.0 | 40 | 7.9 | 6 | 2.2 |
| 9 | Both model classes | 27 | 5.9 | 23 | 7.4 | 32 | 6.3 | 6 | 2.2 |
| 10 | Morphology asset | 109 | 23.8 | 91 | 29.3 | 148 | 29.3 | 84 | 30.9 |
| 11 | Fit descriptor | 64 | 14.0 | 30 | 9.6 | 79 | 15.6 | 21 | 7.7 |
| 12 | **Final eligible** | **63** | **13.8** | **30** | **9.6** | **79** | **15.6** | **20** | **7.4** |

Stage 12 = stage 6 **and** ≥ 1 biophysical model with a resolved fit-descriptor
reference **and** a usable morphology asset. It does not require both model
classes and does not require a projection identity.

Stage 5 counts: ≥ 6 long-square current-clamp sweeps, ≥ 3 depolarising sweeps,
≥ 2 distinct depolarising amplitudes (1e-3 pA rounding). Phase 0's PASS rule
(≥ 6 LS, ≥ 3 depolarising, biophysical model, model download reference, NWB
reference) is retained unchanged; group PASS counts are 64 / 30 / 79 / 21 = 194,
two more than stage 12, and the difference is exactly the morphology
requirement (**DERIVED**, `quality_checks`).

### 3.2 Additional eligibility variants (DERIVED)

| Variant | A | B | C | D |
|---|---:|---:|---:|---:|
| Final, any biophysical model (stage 12) | 63 | 30 | 79 | 20 |
| Final, both model classes | 27 | 23 | 32 | 6 |
| Final, spiny dendrite only | 54 | 7 | 41 | 8 |
| Final, spiny + perisomatic | 54 | 6 | 39 | 8 |
| Final, spiny + both classes | 21 | 3 | 13 | 2 |
| Final, identity-compatible (PROBABLE) | 47 | 2 | 15 | 5 |
| Final, identity-compatible + perisomatic | 47 | 1 | 14 | 5 |
| Final, identity-compatible + both | 18 | 0 | 2 | 1 |
| Final, full morphology | 3 | 15 | 11 | 7 |
| Final, identity-compatible + full morphology | 0 | 1 | 0 | 0 |

### 3.3 Why specimens were excluded

1,354 specimens fail at least one requirement. The first failing requirement,
in the audit's fixed order, is (**DERIVED**, `four_population_exclusions.csv`):

| First failing requirement | A | B | C | D | Total |
|---|---:|---:|---:|---:|---:|
| No biophysical model | 393 | 281 | 424 | 251 | 1,349 |
| EphysResult failed | 1 | 0 | 2 | 0 | 3 |
| No usable morphology (model present) | 1 | 0 | 0 | 1 | 2 |
| **Total excluded** | **395** | **281** | **426** | **252** | **1,354** |

Excluded + final = 1,546 for every group. A specimen is never excluded twice and
is never counted in two groups. The audit re-derives the per-specimen
perisomatic / all-active / GLIF counts from `model_inventory.csv` and stops with
an error if they disagree with `cell_inventory.csv` (**DERIVED**, enforced in
`build_records`).

Note that 736 four-layer specimens have **GLIF-only** models (234 / 150 / 223 /
129). A GLIF model is not a biophysical model and never satisfies stage 7–12.
**OBSERVED**

---

## 4. Recording feasibility

All values **OBSERVED** in `sweep_inventory.csv` / `cell_inventory.csv` or
**DERIVED** by the audit. One EphysResult per specimen and one NWB file per
specimen: session counts equal specimen counts and NWB reference counts equal
non-failed specimen counts.

| Quantity | A | B | C | D |
|---|---:|---:|---:|---:|
| Specimens | 458 | 311 | 505 | 272 |
| Recording sessions (unique `ephys_result_id`) | 458 | 311 | 505 | 272 |
| NWB references resolved | 458 | 311 | 505 | 272 |
| Sampling 50 kHz | 163 | 182 | 231 | 205 |
| Sampling 200 kHz | 295 | 129 | 274 | 67 |
| Long-square CC sweeps | 11,170 | 8,342 | 12,362 | 6,730 |
| LS sweeps per specimen, median (min–max) | 23 (7–66) | 25 (7–63) | 23 (7–64) | 25 (6–50) |
| Depolarising sweeps | 8,626 | 6,564 | 9,495 | 5,301 |
| Distinct depolarising amplitudes, median (min–max) | 13 (3–45) | 14 (4–51) | 13 (2–42) | 13 (3–32) |
| Specimens with ≥ 5 distinct amplitudes | 454 | 309 | 499 | 269 |
| Specimens with a repeated amplitude | 422 | 291 | 461 | 255 |
| Failed EphysResult | 1 | 0 | 2 | 0 |
| Implicit clamp-mode specimens | 15 | 49 | 51 | 45 |
| Depolarising amplitude range (pA) | 10–850 | 10–950 | 10–810 | 10–610 |
| Unit labels (`Amps` / `pA`) | 443 / 15 | 262 / 49 | 454 / 51 | 227 / 45 |

### 4.1 Unit convention

The inventory's `stimulus_units` label is a **campaign marker, not a unit
label**. Phase 1B validated 236/236 long-square sweeps against raw NWB arrays
and found that every inventory amplitude is in picoamperes, whatever the label
says, and that the `pA` label is perfectly confounded with a null `clamp_mode`
(**OBSERVED**, `results/phase1/CROSS_SPECIMEN_UNIT_VALIDATION.md`). The audit
therefore applies the validated units-aware rule:

```
current_clamp  OR  (clamp_mode is null AND stimulus_units == 'pA')
```

This recovers 160 implicit-clamp specimens inside the four groups (164
database-wide). It does **not** inflate the final counts: every implicit-clamp
specimen has zero biophysical models, so all 160 fail at stage 7.
**DERIVED**

### 4.2 Calibration and held-out capacity

Per-specimen capacity is adequate: every non-failed specimen has ≥ 2 distinct
depolarising amplitudes, the group medians are 13–14, and repeated amplitudes
exist in 1,429 of 1,546 specimens. One L5 specimen has only 2 distinct
depolarising amplitudes; it meets the ≥ 2 rule but supports only a minimal
one-level split. **DERIVED**

Within-specimen sweeps are *not* statistically independent conditions in the
sense a held-out evaluation usually assumes. The audit establishes only that
there are enough distinct amplitudes and repeats to *construct* a split. It does
**not** verify which sweeps were used to fit each model; that requires opening
the fit descriptor (§5.4). **UNAVAILABLE in this phase**

### 4.3 Protocol consistency

All four groups use the same long-square protocol families, dominated by
`C1LSCOARSE150216` and `C1LSFINEST150112`. Specimens with both families / coarse
only: A 427 / 31, B 294 / 17, C 471 / 34, D 258 / 14 (**DERIVED**). The 96
coarse-only specimens are a minor protocol inconsistency and should be either
excluded or analysed as a covariate in a later phase.

Sampling rate is the larger comparability issue: each group mixes 50 kHz and
200 kHz recordings, and L6 is predominantly 50 kHz (205 of 272). Membrane
potential and f–I metrics are usable across both rates; spike-waveform metrics
should be restricted to a 200 kHz subset or resampled. **DERIVED**

No data gaps were found in NWB references, sampling rate, or long-square
amplitudes. **OBSERVED**

---

## 5. Biophysical model feasibility

Five evidence levels are kept strictly separate. A model that is *listed* is not
a model that is *reproducible*.

| Level | Meaning | Status in this phase |
|---|---|---|
| Listed | `model_inventory.csv` row with a biophysical template | 194 specimens in the four groups |
| Descriptor available | `availability_status = metadata_present_download_reference_resolved` and a non-null fit-file id | 194 specimens (100% of listed) |
| Assets available | fit JSON, morphology and mechanisms present in the repository | 1 specimen (382982932) |
| Executable | the model has actually been run in this repository | 1 specimen (382982932, both classes) |
| Validated against its recording | simulated output compared with the recorded response | **0** |

These levels are **OBSERVED/DERIVED**; "executable" and "validated" reflect the
Phases 2C, 2G-B and 2G-C results already on `ashish-work`.

### 5.1 Availability by group

| Quantity | A | B | C | D |
|---|---:|---:|---:|---:|
| Any biophysical model (listed) | 64 | 30 | 79 | 21 |
| Perisomatic | 63 | 28 | 71 | 21 |
| All-active | 28 | 25 | 40 | 6 |
| Both classes | 27 | 23 | 32 | 6 |
| GLIF only | 234 | 150 | 223 | 129 |
| Fit-descriptor reference resolved | 64 | 30 | 79 | 21 |
| Usable morphology asset | 109 | 91 | 148 | 84 |
| Final eligible (any model) | 63 | 30 | 79 | 20 |
| Final perisomatic | 62 | 28 | 71 | 20 |
| Final all-active | 28 | 25 | 40 | 6 |
| Final both | 27 | 23 | 32 | 6 |
| Model reconstruction ≠ specimen reconstruction | 3 | 13 | 7 | 2 |
| Assets in repository | 0 | 1 | 0 | 0 |
| Executed in repository | 0 | 1 | 0 | 0 |
| Validated against recording | 0 | 0 | 0 | 0 |

Templates: perisomatic `329230710`, all-active `491455321`. Class is assigned by
template id and never by `well_known_file_type_id`, because the biophysical fit
JSON and the GLIF neuron configuration share a file type. **OBSERVED**

### 5.2 Strongest candidates (model ids)

Ranked by identity confidence, then both-class availability, then full
morphology, then distinct amplitudes, then sampling rate. Full machine-readable
ranking in `four_population_candidates.csv`.

**A — L4** (all top candidates have dendrite-only reconstructions):

| Rank | Specimen | Driver line | Perisomatic (template) | Fit file | All-active (template) |
|---:|---|---|---|---|---|
| 1 | 485931158 | Rorb-IRES2-Cre | 486509958 (329230710) | 539256354 | 515175291 (491455321) |
| 2 | 468193142 | Scnn1a-Tg3-Cre | 482934212 (329230710) | 497236041 | 497233125 (491455321) |
| 3 | 320207387 | Scnn1a-Tg3-Cre | 329321704 (329230710) | 497237599 | 497229082 (491455321) |

**B — L2/3** (only two identity-compatible cells exist; each has one model class):

| Rank | Specimen | Driver line | Perisomatic (template) | Fit file | All-active (template) | Note |
|---:|---|---|---|---|---|---|
| 1 | 487661754 | Cux2-CreERT2 | 488462783 (329230710) | 496540225 | — | full morphology; model reconstruction ≠ specimen |
| 2 | 486262299 | Cux2-CreERT2 | — | — | 515175253 (491455321) | dendrite-only; reconstruction matches |

**C — L5**:

| Rank | Specimen | Driver line | Perisomatic (template) | Fit file | All-active (template) |
|---:|---|---|---|---|---|
| 1 | 471129934 | Rbp4-Cre_KL100 | 480624414 (329230710) | 497236153 | 497233049 (491455321) |
| 2 | 485574832 | Rbp4-Cre_KL100 | 486052412 (329230710) | 497237159 | 497232312 (491455321) |
| 3 | 471767045 | Rbp4-Cre_KL100 | 478513443 (329230710) | 497236218 | — |

**D — L6** (all five identity-compatible cells are Ntsr1-Cre_GN220):

| Rank | Specimen | Driver line | Perisomatic (template) | Fit file | All-active (template) |
|---:|---|---|---|---|---|
| 1 | 471819401 | Ntsr1-Cre_GN220 | 478513398 (329230710) | 497236261 | 497232999 (491455321) |
| 2 | 471786879 | Ntsr1-Cre_GN220 | 480632594 (329230710) | 497236229 | — |
| 3 | 471789504 | Ntsr1-Cre_GN220 | 472430904 (329230710) | 497236247 | — |

### 5.3 Asset and execution limitations

- **Mechanisms UNAVAILABLE** for every model except 382982932: no model archive
  for the other 193 specimens exists in the repository, and none was downloaded
  in this phase.
- **Reconstruction mismatch:** in 25 of 192 final specimens the model's
  `neuron_reconstruction_id` differs from the specimen's own reconstruction.
  This is worst in B (13 of 30, 43%) and small in A (3 of 63) and D (2 of 20).
  A model built on a different reconstruction is not a morphology-constrained
  model of that cell. **DERIVED**
- **Executable ≠ validated:** the one executed specimen (382982932, L2/3) has
  never been compared against its own recorded response. No model in this
  repository is validated against its recording. **OBSERVED**
- **Model class coverage is asymmetric:** every group has more perisomatic than
  all-active models, and D has only six all-active models in total.

### 5.4 What was not opened

The fit descriptor is resolved at the metadata level only. The audit did not
open the fit JSON, so it cannot say which sweeps were used for fitting. For the
same reason the audit cannot guarantee that the sweeps available for held-out
testing were excluded from the fit. **UNAVAILABLE in this phase**; this is the
first item in §11.

---

## 6. Identity confidence and evidence limitations

### 6.1 Identity-evidence table

| Group | Proposed identity | Evidence available | Class label | Confidence | Final PROBABLE | Final LAYER-ONLY | Final UNRESOLVED | Final not a candidate |
|---|---|---|---|---|---:|---:|---:|---:|
| A | L4 excitatory spiny stellate / IT-like | layer 4 + spiny dendrite + L4 class-compatible lines (Rorb, Scnn1a Tg2/Tg3, Nr5a1, Cux2); apical status intact for all 47 | A | **PROBABLE** | 47 | 1 | 7 | 8 |
| B | L2/3 IT pyramidal | Cux2-CreERT2 + spiny dendrite, but only 2 such cells survive all requirements | B | **LAYER-ONLY** | 2 | 1 | 5 | 22 |
| C | L5 ET/PT pyramidal | layer 5 + spiny dendrite + Rbp4-Cre_KL100; ET vs PT not separable | C | **PROBABLE** | 15 | 0 | 29 | 35 |
| D | L6 corticothalamic | Ntsr1-Cre_GN220 + spiny dendrite, L6a only (all 20 final specimens are 6a) | D | **PROBABLE** | 5 | 0 | 6 | 9 |

All-group confidence distributions (specimens): A 241 PROBABLE / 17 LAYER-ONLY /
48 UNRESOLVED / 152 not a candidate; B 25 / 7 / 42 / 237; C 54 / 72 / 123 / 256;
D 50 / 60 / 38 / 124. **DERIVED**

Rules used (**DERIVED**, `classify_identity`):

- **PROBABLE** — spiny dendrite **and** a class-compatible line **and** the
  matching layer. Three independent indirect features must converge.
- **LAYER-ONLY** — spiny dendrite, layer known, line uninformative.
- **UNRESOLVED** — line/layer conflict, line/morphology conflict, or missing
  dendrite type.
- **NOT-CANDIDATE** — aspiny or sparsely spiny dendrite, i.e. not one of the
  four proposed excitatory classes.
- **CONFIRMED** — never assigned.

### 6.2 Why nothing can be CONFIRMED

Probe of `http://api.brain-map.org/api/v2/data/query.json`, run once on
2026-11-07 (**OBSERVED**, embedded in the audit as `IDENTITY_SCHEMA_PROBE`):

| Probe | Result |
|---|---|
| `model::Specimen` payload fields | 27 fields; no projection, cell-class or transcriptomic field |
| columns `projection`, `projection_class`, `cell_type`, `cell_class`, `projection_target`, `target_structure_id`, `cre_line`, `line_name` | HTTP 200, `success=false`, "Data Access error" (column does not exist) |
| models `model::Projection`, `model::ProjectionTarget`, `model::CellType`, `model::TranscriptomicType` | HTTP 200, `success=false`, "uninitialized constant" |
| control: `structure_id$eq721` (VISp L4) | HTTP 200, `success=true`, 458 rows |

The control proves the query pattern works when a column exists, so the
negative results are evidence of absence, not a malformed request. The database
therefore **cannot** distinguish IT / ET / PT / CT, cannot distinguish spiny
stellate from star pyramidal, and cannot distinguish L6 CT from L6 corticocortical
cells.

### 6.3 Specific biological cautions

- **A: spiny stellate is not supported.** All 47 identity-compatible L4 cells
  carry `apical_dendrite_status = intact` and a dendrite-only reconstruction.
  An intact apical dendrite argues for a star-pyramidal / IT-like morphology and
  against a classical spiny stellate morphology. The honest label is "L4 spiny
  excitatory, stellate vs star pyramidal unresolved". **OBSERVED/DERIVED**
- **A: five Rbp4-Cre cells appear in L4.** Rbp4 is an L5 class marker, so these
  cells are layer/line conflicts (UNRESOLVED), not L4 candidates, even though
  they pass the layer-level count.
- **B: four Nr5a1-Cre spiny cells appear in L2/3.** Nr5a1 is an L4 marker; these
  are layer/line conflicts and are UNRESOLVED, not IT. Only the two Cux2 cells
  are IT-compatible.
- **B: the L2/3 layer-level count is dominated by interneurons.** Of the 30
  final specimens, 22 are not candidates (mainly Pvalb, Sst, Htr3a). Any claim
  about "L2/3 pyramidal" based on the raw layer count would be wrong.
- **C: ET and PT cannot be separated.** Rbp4-Cre_KL100 targets L5 thick-tufted
  cells but does not distinguish ET from PT. 41 of 79 final cells are spiny; 35
  are interneurons.
- **D: "L6" is effectively L6a.** All 48 L6b specimens have zero biophysical
  models, so none can enter the audit. All 20 final L6 cells are L6a, and only
  five are Ntsr1-compatible.
- **Dendrite type is coarse.** `spiny` is not proof of excitatory identity, and
  `aspiny` is not proof of inhibitory identity. The audit uses it only as one
  indirect feature and flags GABAergic-line conflicts explicitly.

---

## 7. Population balance and comparability

| Criterion | A | B | C | D | Verdict |
|---|---|---|---|---|---|
| Layer-defined final specimens | 63 | 30 | 79 | 20 | all ≥ 20; B and D smallest |
| Spiny (putative excitatory) final | 54 | 7 | 41 | 8 | all ≥ 7; B and D near the floor |
| Identity-compatible final | 47 | 2 | 15 | 5 | B fails a 3–4 target |
| Perisomatic available | 62 | 28 | 71 | 20 | all groups comfortably covered |
| All-active available | 28 | 25 | 40 | 6 | D thin |
| Both classes | 27 | 23 | 32 | 6 | D at the 6-cell margin |
| Same long-square protocol family | yes | yes | yes | yes | comparable |
| Mixed 50/200 kHz | yes | yes | yes | yes (mostly 50) | Vm/f–I comparable; spike shape needs care |
| Same evaluation metrics possible | yes | yes | yes | yes | for Vm, f–I, adaptation, threshold |
| Full morphology | 3 | 15 | 11 | 7 | A and C mostly dendrite-only |
| Model reconstruction matches specimen | 60/64 | 17/30 | 72/79 | 18/21 | B weakest |

**Balance assessment (DERIVED).** On the layer-defined perisomatic criterion the
four groups are usable but not equal: A and C are strong, B is adequate (6
spiny perisomatic cells), D is adequate (8) but has only two spiny specimens
with both model classes. On the identity-compatible criterion the design
collapses: B has 2 cells and 0 with both model classes, so a four-group
projection-defined comparison is not supportable. Full-morphology coverage is
the weakest asset: only one identity-compatible cell in the whole four-group
set (a B cell) has a full reconstruction, so morphology-constrained claims
cannot be balanced across groups.

**Evaluation metrics.** Membrane-potential statistics, f–I curves, adaptation
indices and spike threshold are computable in all four groups with the existing
long-square data. Spike-shape metrics (half-width, afterhyperpolarisation) are
rate-sensitive and should be restricted to the 200 kHz subset; that subset is
still 295 / 129 / 274 / 67 specimens, so no group is lost. **DERIVED**

---

## 8. Recommended four populations

**Recommendation: adopt four *layer-defined* V1 excitatory populations and keep
the projection hypothesis as an annotation, not a selection criterion.**

| New group | Definition | Eligible (spiny final) | Perisomatic | Both classes | Permissible claim |
|---|---|---:|---:|---:|---|
| A′ | VISp L4, spiny, perisomatic model | 54 | 54 | 21 | L4 excitatory electrophysiology; **not** "spiny stellate" |
| B′ | VISp L2/3, spiny, perisomatic model | 7 | 6 | 3 | L2/3 excitatory electrophysiology; **not** "IT" |
| C′ | VISp L5, spiny, perisomatic model | 41 | 39 | 13 | L5 excitatory, thick-tufted-compatible; **not** "ET" or "PT" |
| D′ | VISp L6a, spiny, perisomatic model | 8 | 8 | 2 | L6a excitatory, CT-compatible; **not** "CT" |

A practical minimum target of 3–4 eligible neurons per population is met by all
four groups on the perisomatic criterion (54 / 6 / 39 / 8). The all-active
criterion is met by A, B and C but only marginally by D (2 spiny cells with both
classes). A defensible plan is therefore:

1. **Primary comparison:** four layer-defined excitatory populations, 4 neurons
   per group, perisomatic models only. Balanced and fully supported.
2. **Secondary comparison:** all-active models in A and C (21 and 13 spiny
   cells) as a descriptive extension; B (3) and D (2) are too thin to carry a
   four-group claim and should be reported separately.
3. **Annotation layer:** report the identity-compatible subset (47 / 2 / 15 / 5)
   per neuron so the supervisor can see which cells carry the strongest
   indirect class evidence, without letting that subset define the groups.

What would *not* be permissible: describing the four groups as IT / ET / PT / CT,
describing A as spiny stellate, or pooling the four groups into a "projection
class" comparison. Those claims are not supported by any field in the database.

---

## 9. Alternative populations if a candidate fails

B is the candidate that fails. Three honest alternatives, in order of preference:

1. **Redefine B as "L2/3 excitatory" instead of "L2/3 IT".** 7 spiny final
   cells, 6 perisomatic, 3 both. This preserves the L2/3→L4 feed-forward
   comparison and keeps four groups. It removes any projection claim for B.
2. **Replace B with a layer-defined L2/3 inhibitory population.** Pvalb+,
   Sst+ and Htr3a+ interneurons dominate the L2/3 final set (22 of 30
   non-candidates; 9 Htr3a, 7 Sst, 5 Pvalb). An interneuron group would be
   scientifically interesting and numerically stronger, but it changes the
   biological question from "excitatory projection classes" to "excitatory vs
   inhibitory integration" and should be a supervisor decision, not an audit
   decision.
3. **Drop to three projection-compatible populations.** A 47, C 15, D 5, using
   the identity-compatible subset with perisomatic models (47 / 14 / 5). This is
   the only version in which all groups carry indirect projection evidence, and
   D is at the 3–4 floor. All-active coverage in this subset is 18 / 2 / 1,
   which is too thin for a balanced secondary analysis.

The audit does not recommend forcing B into a projection-defined group by
relaxing eligibility. That would make the group look populated while removing
the very evidence the supervisor is asking about.

---

## 10. Is the proposed project feasible with the available data?

**Yes, with a redefinition of the four populations; no, as originally framed.**

| Question | Answer | Basis |
|---|---|---|
| Can four biologically distinct V1 populations be studied? | Yes, if "distinct" means layer-defined excitatory populations | 54 / 7 / 41 / 8 spiny cells; perisomatic 54 / 6 / 39 / 8 |
| Can four *projection-defined* populations be studied? | No | no projection field; identity-compatible 47 / 2 / 15 / 5 |
| Are detailed and reduced models available? | Perisomatic yes; all-active unevenly | perisomatic 63 / 28 / 71 / 21; all-active 28 / 25 / 40 / 6 |
| Can the same evaluation be run in all groups? | Yes for Vm/f–I/adaptation; spike shape needs 200 kHz subset | §7 |
| Is 3–4 neurons per group achievable? | Yes on the perisomatic criterion; D only marginally on both-class | §8 |
| Is the data sufficient to execute models now? | No | assets for 1 of 194 model-bearing specimens; 0 validated |

Feasible today: population selection, recording audit, model-asset audit,
per-neuron identity annotation, and a balanced 4×4 perisomatic modelling plan.
Not feasible today: any claim about IT/ET/PT/CT identity, any
morphology-constrained comparison, and any model-execution claim beyond the one
reference specimen.

---

## 11. Validation still required before model implementation

1. **Open the fit descriptors** for the 194 model-bearing specimens and record
   the fitted sweep numbers, so fit and held-out sweeps can be proven disjoint.
   This is the largest unverified assumption in the audit.
2. **Download and checksum the model archives** for the selected cells, confirm
   the NEURON mechanisms compile, and record which models are executable.
   Currently only 382982932 is known executable.
3. **Inspect a small NWB sample from each population** (not all files) to
   confirm the units-aware rule on the selected cells and to record the actual
   stimulus start/duration. Phase 1B already covers five files; the selected
   cells are not among them.
4. **Resolve the reconstruction mismatch** for the 25 final specimens whose
   model reconstruction differs from the specimen's own, and decide whether they
   remain eligible.
5. **Assign the held-out split** per cell and verify it is not the fitted set;
   the audit only shows that enough amplitudes and repeats exist.
6. **Decide the B question** (redefine as L2/3 excitatory, replace with
   interneurons, or drop to three groups) before any population is frozen.
7. **Confirm spike-shape metrics are rate-comparable** or restrict them to the
   200 kHz subset.
8. **Do not create four projection-defined groups** unless an external
   projection/transcriptomic source is added; the Allen metadata cannot supply
   one.

---

## Appendix A — Reproducibility and quality checks

```
python src/data_audit/four_population_audit.py --print-tables
python -m pytest tests/test_four_population_audit.py -q
```

The script verifies `cell_inventory.csv`, `sweep_inventory.csv` and
`model_inventory.csv` against the Phase 0 SHA-256 manifest before reading them,
and refuses to run on changed inputs. All 14 internal quality checks pass:

| Check | Result |
|---|---|
| Specimen ids unique | 1,546 / 1,546 |
| Groups disjoint and cover the four layers | 1,546 = 1,588 − 42 L1 |
| No specimen in two populations | pass |
| Every model maps to a group specimen | pass |
| Model ids unique and class-disjoint | 183 perisomatic, 99 all-active, 0 overlap |
| Final is a subset of every required facet | pass |
| Stage counts monotonic against base | pass |
| Every non-final specimen has a reason | pass |
| Every final specimen has morphology and a model | pass |
| Identity never CONFIRMED | pass |
| Phase 0 PASS ≥ final, per group | 64/63, 30/30, 79/79, 21/20 |

Outputs:

| File | Rows | Content |
|---|---:|---|
| `results/dataset_inventory/four_population_counts.csv` | 48 | 12 stages × 4 groups, n and % |
| `results/dataset_inventory/four_population_candidates.csv` | 192 | final-eligible specimens, model ids, identity evidence |
| `results/dataset_inventory/four_population_exclusions.csv` | 1,354 | every non-final specimen and its failing requirements |
| `results/dataset_inventory/four_population_model_availability.csv` | 4 | model evidence levels per group |
| `results/dataset_inventory/four_population_audit_summary.json` | — | machine-readable summary, probe evidence, quality checks |

## Appendix B — Source documents reused

| Document | Used for |
|---|---|
| `results/dataset_inventory/DATASET_INVENTORY_REPORT.md` | Phase 0 denominators, model and morphology counts |
| `results/dataset_inventory/LONG_SQUARE_FEASIBILITY_NOTE.md` | long-square coverage, PASS/FAIL structure, interneuron warning |
| `results/phase1/CROSS_SPECIMEN_UNIT_VALIDATION.md` | units-aware rule and the `Amps`/`pA` finding |
| `results/phase1/NWB_VALIDATION_341442651.md` | independent NWB schema check |
| `docs/DATASET_SELECTION_DECISION.md` | VISp choice and scope constraints |
| `data/metadata/cell_inventory.csv` | 1,588 VISp mouse specimens |
| `data/metadata/sweep_inventory.csv` | 38,604 four-group long-square sweeps |
| `data/metadata/model_inventory.csv` | 3,262 model rows, 194 group biophysical cells |

No previous report, model parameter, or Phase 0 artifact was modified. No NWB
file, model archive or FHN model was downloaded or executed in this phase.

# Dataset Selection Decision Record

| | |
|---|---|
| **Project** | INCM — *How much biological detail does a neuron model need?* |
| **Phase** | 0 — Allen Cell Types Database inventory |
| **Status** | 🔴 **PENDING APPROVAL — NO POPULATION SELECTED** |
| **Prepared by** | Research software engineering (Phase 0 audit) |
| **Evidence base** | `results/dataset_inventory/DATASET_INVENTORY_REPORT.md`, `inventory_summary.json`, `database_structure_coverage.json`, `data/metadata/*.csv` |
| **Decision required from** | Project supervisor / both team members |

> **This document records a decision that has NOT been made.** Per the Phase 0 brief:
> *"Do not select the final populations automatically… Stop after producing the inventory
> and report. Present the findings and wait for approval."*
>
> Nothing below is a selection. Every option is presented with its metadata evidence and
> its open risks so that an approver can choose.

---

## 1. The decision that was supposed to be made

The proposal assigns:

* **Member 1** → a **sensory** neuronal population
* **Member 2** → a **motor** neuronal population

with candidate regions `VISp`, `VISl`, `VISal` (sensory) and `MOp`, `ALM` (motor),
explicitly described as *"candidates to investigate, not confirmed available populations."*

The proposal's qualification rule (§3) is:

> *"A population qualifies only with at least four recorded cells with suitable long-square
> sweeps and downloadable models of the same class."*

---

## 2. What the audit found (confirmed metadata, not validated eligibility)

### 2.1 The motor arm cannot be populated — confirmed absence

This is the central finding and it is a **confirmed absence**, not missing information.
Every count below came from an HTTP 200 / `success=true` RMA response, and **zero API
errors** were recorded across the whole run.

| Structure | ID | Level checked | Cell specimens |
|---|---|---|---|
| `MOp` (Primary motor area) | 985 | region (parent) | **0** |
| `MOp1` | 320 | layer | **0** |
| `MOp2/3` | 943 | layer | **0** |
| `MOp5` | 648 | layer | **0** |
| `MOp6a` | 844 | layer | **0** |
| `MOp6b` | 882 | layer | **0** |
| `MOs` (Secondary motor area) | 993 | region | **0** |
| `FRP` (Frontal pole) | 184 | region | **0** |
| `SSs`, `SSp`, `PT`, `SC`, `AN` | — | controls | **0** |
| `ALM` | — | ontology lookup | **acronym absent from the Allen structure ontology** |

**Query-pattern control.** The sensory parents `VISp` (385), `VISl` (409) and `VISal` (402)
*also* return 0 cells at the parent level, while their layer sub-structures return 505,
458, 311, 224, 48, 42 … cells. Cells in this database are therefore attached at **layer**
level, which proves the zero `MOp` layer counts are real and not a level-of-attachment
artefact.

**Whole-database scan.** All **2 336** Cell Types Database cells (`is_cell_specimen=true`,
1 923 mouse + 413 human) across **79** structures were enumerated, together with all
**345** biophysical models (238 perisomatic + 107 all-active) and **3 753** GLIF models.
Results:

* **No mouse motor-cortex cell exists anywhere in the database.**
* Structures whose official name matches a motor/frontal filter and that *do* hold cells —
  `MTG`, `FroL`, `MFG`, `ITG`, `TemL`, `AnG`, `IFG`, `SFG` — have **zero mouse cells**
  (human tissue only), outside this project's mouse scope.
* The mouse structures matched by that filter (`RSPagl1/2/3/5/6a`, retrosplenial agranular
  cortex, 19 cells) are **not motor areas** and carry **zero biophysical models**.
* Only **5** structures database-wide hold ≥4 *mouse* biophysical models: `VISp5` (111),
  `VISp4` (91), `VISp2/3` (53), `VISp6a` (27), `VISl4` (5). **All are visual.**

**Consequence.** No choice of motor region — `MOp`, `ALM`, `MOs`, `FRP`, or anything else
— can satisfy the ≥4-cell rule. A sensory-versus-motor comparison is **not feasible with
the Allen Cell Types Database.** This is a property of the dataset, not of the query
design, and it cannot be resolved by downloading more data.

### 2.2 The sensory arm is well supported

Candidate-region inventory: **1 694 specimens**, all *Mus musculus*, across **3** regions.

| Region | Mouse cells | CC Long Square | Perisomatic | All-active | ≥1 biophysical | PASS | COND | FAIL |
|---|---|---|---|---|---|---|---|---|
| `VISp` | 1 588 | 1 424 | 184 | 100 | 195 | **195** | 1 226 | 167 |
| `VISl` | 89 | 76 | 4 | 2 | 4 | **4** | 72 | 13 |
| `VISal` | 17 | 13 | 1 | 2 | 2 | **2** | 11 | 4 |

Database-wide (all mouse, all layers): 1 513 cells with current-clamp Long Square sweeps
(all ≥6), 189 with a perisomatic model, 104 with an all-active model, 201 with ≥1
biophysical model, 810 GLIF-only, 468 with a morphology SWC reference.

Eligibility across the candidate inventory: **PASS 201, CONDITIONAL 1 309, FAIL 184,
UNKNOWN 0.**

### 2.3 Reference specimen 485909730

Returned by the current API and present in the candidate inventory.

| Field | Value |
|---|---|
| Region / layer | `VISp` (Primary visual area), layer **5** (`VISp5`, id 778) |
| Species | *Mus musculus* |
| Transgenic line | `Cux2-CreERT2` driver / `Ai14(RCL-tdT)` reporter |
| Dendrite type / apical | `spiny` / `intact` |
| Electrophysiology | `ephys_result` 485909728, `failed = false`, 200 kHz |
| Sweeps | 35 total — 12 current-clamp Long Square, 13 current-clamp Short Square, 3 current-clamp Ramp, 1 other current-clamp (remainder are non-current-clamp/test sweeps) |
| NWB | well-known-file 491316386 (download reference resolved) |
| Biophysical model | **486509232** — *Biophysical – perisomatic* (template 329230710), reconstruction 500961528 ("dendrite-only"), fit JSON wkf 501606122 |
| Morphology | SWC well-known-file 500961530 |
| **Audit eligibility** | **PASS** — *metadata level only* |

This is consistent with the previous project's use of the cell, and it satisfies every
Phase 0 metadata criterion. **It has not been re-validated**: the NWB was not opened and
the model archive was not downloaded or run. It must not be assumed to qualify for the new
experiment without that validation.

---

## 3. Options for approval

### Option A — Adopt the proposal's own fallback: `VISp` layer 2/3 vs `VISp` layer 5 ⭐ *best supported*

The proposal (§3) already anticipates this: *"V1 layer 2/3 vs layer 5, or V1 vs a higher
visual area."*

| | `VISp2/3` | `VISp5` |
|---|---|---|
| Mouse cells | 311 | 505 |
| Cells with CC Long Square | 262 | 454 |
| Median CC Long Square sweeps | 23 | 22 |
| Mouse biophysical models | 53 | 111 |
| — perisomatic | 28 | 71 |
| — all-active | 25 | 40 |
| Cells with ≥1 biophysical model | 30 | 79 |
| Audit `PASS` cells | 30 | 79 |
| Clears ≥4-cell rule? | **yes** | **yes** |
| Shared model class available? | **yes — perisomatic (28 vs 71)** | |

* **Strengths.** Both arms clear the rule with a large margin; a **single shared model
  class** (*Biophysical – perisomatic*) is available in both, satisfying the proposal's
  "one model class for all cells unless justified"; layer is a genuine biological contrast
  relevant to the research question; the reference specimen 485909730 is in the L5 arm, so
  prior work is directly reusable; 30 + 79 PASS cells give ample room for the 3–4 cells
  per population the protocol needs.
* **Risks.** It is a **layer** contrast within one area, not a **region** contrast, so the
  "two populations" framing changes. Both members would work in `VISp`, which reduces the
  independence of the two work packages.
* **Needs approval because** it abandons the sensory/motor design.

### Option B — `VISp` vs a higher visual area (`VISl`)

| | `VISp` | `VISl` |
|---|---|---|
| Mouse cells | 1 588 | 89 |
| Cells with CC Long Square | 1 424 | 76 |
| Cells with a **perisomatic** model | 184 | **4** |
| Cells with an **all-active** model | 100 | 2 |
| Cells with ≥1 biophysical model | 195 | 4 |
| Audit `PASS` cells | 195 | **4** |

* **Strengths.** Preserves a genuine **area-to-area** contrast, closest in spirit to the
  original sensory/motor design. `VISl` does technically reach the ≥4-cell bar on a single
  shared class (*Biophysical – perisomatic*, 4 cells).
* **Risks — this is the weak point.** The margin is **exactly zero**: 4 perisomatic cells
  against a rule that requires 4. Those 4 cells are also split across layers (`VISl4` = 3,
  `VISl5` = 1), so the "population" is not a single coherent layer group. If **any one** of
  the 4 fails NWB or model validation, `VISl` drops below the bar and the arm collapses.
  `VISal` is worse still — 2 cells with a biophysical model (`VISal2/3` all-active, `VISal4`
  perisomatic), 2 `PASS`, so it does **not** clear the rule on any class.
* **Verdict.** Technically admissible but **fragile**. Only viable if the approver accepts a
  zero-margin population, or if validation shows extra `VISl` cells can be recovered from
  the 72 `CONDITIONAL` rows (those lack a biophysical model in metadata, so recovery is
  unlikely).

### Option C — Keep the sensory/motor design and source motor data elsewhere

* **What it would take.** A different dataset with mouse motor-cortex cells that have both
  current-clamp long-square recordings *and* downloadable conductance-based models.
* **Risks.** Outside the Allen Cell Types Database, so outside the proposal's stated data
  source; introduces a second data format, a second modelling pipeline and a second set of
  provenance concerns; high schedule risk against an 18–22 October inventory milestone that
  has already been met only for the sensory arm.
* **Verdict.** Feasible in principle, but a substantial scope change requiring explicit
  supervisor direction. **No such dataset was audited in Phase 0** — its availability is
  therefore **UNKNOWN**, not confirmed absent.

### Option D — Whisker/barrel-field somatosensory (`SSp-bfd`) as the second population

Checked because it is the other classic mouse sensory system in this database.

* `SSp-bfd4` = 2 cells, `SSp-bfd5` = 2 cells, `SSp-bfd2/3` = 1 cell — **5 mouse cells
  total, zero biophysical models.**
* **Verdict.** Does not clear the ≥4-cell rule and has **no** biophysical models at all.
  **Not viable.**

### Comparison

| Option | Clears ≥4-cell rule | Shared model class | Preserves sensory/motor design | Schedule risk | Metadata support |
|---|---|---|---|---|---|
| **A — VISp L2/3 vs L5** | ✅ both arms, large margin | ✅ perisomatic (28 / 71 cells) | ❌ | Low | **Strong** |
| **B — VISp vs VISl** | ⚠️ VISl = exactly 4, zero margin | ⚠️ perisomatic, but split across layers | ⚠️ partially | Medium | Weak / fragile |
| **C — external motor data** | UNKNOWN | UNKNOWN | ✅ | High | **Not audited** |
| **D — SSp-bfd** | ❌ 5 cells, 0 models | ❌ | ⚠️ partially | Low | Confirmed not viable |

**On metadata evidence, Option A is the only option that satisfies the proposal's own
qualification rule with a usable margin.** That is a recommendation, **not a selection**.

---

## 4. What "PASS" does and does not mean

Every number above is **confirmed metadata**. None of it is experimentally validated
eligibility.

| Confirmed by Phase 0 | NOT confirmed by Phase 0 |
|---|---|
| The specimen exists and is *Mus musculus* | That the NWB file parses |
| Region and layer, from the CCF structure hierarchy | That the long-square sweep amplitudes span a usable range |
| `EphysResult` present and `failed = false` | That the recording is artefact-free |
| Number of current-clamp Long Square sweeps | That the actual sampling rate matches the metadata |
| A biophysical model exists, with template class and a resolved download reference | That the model archive downloads, loads and **runs unmodified in NEURON** |
| A morphology reconstruction exists with an SWC reference | That a single conductance can be perturbed |
| Dendrite type / apical status / transgenic line, from `specimen_tags` | That the Allen model reproduces the cell's own recording |

Every `PASS` and `CONDITIONAL` row therefore carries `needs_nwb_validation` and
`needs_model_validation` flags. The proposal's own go/no-go gate — *"one real model
downloaded, run unmodified, single conductance change"* — has **not** been attempted.

---

## 5. Environment decisions also pending approval

Phase 0 required no installs. Phase 1 does. Nothing below was installed, upgraded or
downgraded.

| Need | Current state | Blocker | Decision needed |
|---|---|---|---|
| **NEURON** (to run Allen biophysical models) | **not installed** | Required by the proposal's methodology | Approve an installation route (native Windows wheel vs WSL2 vs conda) |
| **AllenSDK** | **not installed**; latest release **2.16.2** pins **`numpy < 1.24`** | This environment has **numpy 2.3.4**; installing AllenSDK forces a numpy **downgrade**, forbidden without approval. The proposal itself notes AllenSDK "fails on Windows/Python 3.12" and recommends Python 3.9/3.10 under WSL2/conda. | Approve either (a) a separate Python 3.9/3.10 conda or WSL2 environment for Phase 1, or (b) continuing without AllenSDK, reading NWB directly via `h5py`/`pynwb` |
| **NWB reading** (`h5py` / `pynwb`) | not audited for install status | Needed for targeted recording validation | Approve installation |
| **Python interpreter** | **3.14.0** on Windows | AllenSDK and possibly NEURON lack support at this version | Approve the Phase 1 environment strategy |

Recommended install command for AllenSDK, **reported but not executed**:

```powershell
python -m pip install allensdk
```

---

## 6. Exact recommended next step (awaiting approval)

**Do not begin model implementation.** The next step is still audit-grade:

> **Targeted NWB and model validation of a shortlist drawn from `VISp` layer 5 and `VISp`
> layer 2/3 — the proposal's own go/no-go gate — performed only after the population
> decision in §3 is approved.**

Concretely, once an option is approved:

1. Shortlist ~6 candidate cells per arm from `cell_inventory.csv` (`eligibility == PASS`,
   `n_long_square_cc` high, `biophysical_classes == biophysical_perisomatic`), including
   reference specimen **485909730** in the L5 arm.
2. Download **one** NWB file and **one** *Biophysical – perisomatic* model archive.
3. Verify the NWB's long-square sweep amplitudes, sampling rate and artefact status.
4. Run the Allen model **unmodified** in NEURON and reproduce the cell's own recording.
5. Perturb a **single conductance** and confirm the model responds sensibly.
6. Only if all five succeed, expand to the full shortlist.

If any of steps 3–5 fails, the go/no-go gate fails and the population choice must be
revisited before any further work.

---

## 7. Approval block

| Decision | Chosen option | Approved by | Date |
|---|---|---|---|
| Sensory population (Member 1) | ☐ A ☐ B ☐ C ☐ D ☐ other: ______ | | |
| Motor population (Member 2) | ☐ A ☐ B ☐ C ☐ D ☐ other: ______ | | |
| Shared model class | ☐ perisomatic ☐ all-active ☐ other: ______ | | |
| Phase 1 environment (NEURON / AllenSDK / numpy) | ☐ WSL2 ☐ conda py3.9/3.10 ☐ native ☐ no-AllenSDK | | |
| Proceed to targeted NWB/model validation | ☐ yes ☐ no | | |

*Until this block is completed, Phase 0 remains the final state of the project and no
population has been selected.*

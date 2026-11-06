# VISp Layer 2/3 vs Layer 5 — Long-Square Current-Clamp Feasibility

**Scope.** A read-only follow-up to Phase 0. Question: *do VISp layer 2/3 and VISp layer 5
have comparable long-square current-clamp sweep availability for the planned experiments?*

**Status: informational only.** No population is selected, no cell is frozen, no sweep is
claimed to be scientifically usable, and no Phase 1 work is begun. Everything below is
derived from metadata already committed in Phase 0.

---

## 1. Methods and files inspected

### 1.1 Files read (none modified)

| File | Rows | Used for |
|---|---|---|
| `data/metadata/cell_inventory.csv` | 1,694 | specimen attributes, per-specimen sweep counts, model counts, `eligibility` |
| `data/metadata/sweep_inventory.csv` | 128,869 | `stimulus_category`, `clamp_mode`, `stimulus_units`, `stimulus_absolute_amplitude`, `stimulus_name` |
| `data/metadata/model_inventory.csv` | 3,262 | `model_class`, `template_name`, per-model identity |
| `results/dataset_inventory/DATASET_INVENTORY_REPORT.md` | 472 | Phase 0 `PASS`/`CONDITIONAL`/`FAIL` definitions (§3.2) and region table |

No Allen API call was made. No NWB file and no model archive was downloaded. No CSV was
written. The only file created by this analysis is this note.

### 1.2 Population definition

A specimen belongs to a population if `region_acronym == "VISp"` **and**
`cortical_layer` equals `"2/3"` or `"5"`. `cortical_layer` is stored as a **string**, so
`"2/3"` is a single level, not two. Layer identity comes from the structure acronym
(`VISp2/3` = 311 cells, `VISp5` = 505 cells), not from `cortex_layer_id`, which is null
throughout the database.

- **VISp layer 2/3: 311 specimens**
- **VISp layer 5: 505 specimens**

### 1.3 Two defensible definitions of "current-clamp long square"

The sweep table contains **two** encodings of current clamp, and the choice changes the
answer materially:

| Encoding | `clamp_mode` | `stimulus_units` | Long-square rows |
|---|---|---|---|
| Explicit | `current_clamp` | `Amps` | 37,459 |
| **Implicit** | **null** | **`pA`** | **4,772** |

The implicit rows are unmistakably current clamp (units `pA`, names `Long Square`,
`Short Square`, `Ramp`, `Noise`). They belong to **181 specimens that have no
`current_clamp` row at all** — the two sets are disjoint (0 overlap). Of those 181, **51
are VISp 2/3 and 57 are VISp 5**.

> **Consequence for Phase 0 numbers.** The committed `n_long_square_cc` column counts only
> the explicit encoding, so the Phase 0 report §3.2 figures of **262** (L2/3) and **454**
> (L5) long-square cells are **lower bounds**. The units-aware counts are **311** and
> **505**. Both figures are reported below; the underlying CSVs were **not** altered, and
> Phase 0's `PASS` classification (which required the explicit encoding) is unchanged.

Definitions used here:

- **Long square** — `stimulus_category == "long_square"`; the only `stimulus_name` in this
  category is `Long Square`.
- **Units-aware current clamp** — `clamp_mode == "current_clamp"` **or**
  (`clamp_mode` null **and** `stimulus_units == "pA"`).
- **Depolarising** — `stimulus_absolute_amplitude > 0`.

---

## 2. VISp layer 2/3 findings

### 2.1 Long-square availability

| Measure | Value |
|---|---|
| Specimens | 311 |
| Specimens with ≥1 long-square sweep | **311 (100%)** |
| Long-square sweeps in total | **8,342** |
| … counted by the explicit encoding only | 262 specimens / 7,009 sweeps |
| Long-square sweeps per specimen | min **7**, p25 20, **median 25**, p75 32, max **63**, mean 26.8 |

Distribution of long-square sweeps per specimen:

| Sweeps | 0–5 | 6–9 | 10–14 | 15–19 | 20–29 | 30+ |
|---|---|---|---|---|---|---|
| Specimens | 0 | 3 | 14 | 53 | **137** | **104** |

Every specimen clears the Phase 0 audit threshold (≥6 long-square sweeps, ≥3 depolarising).

### 2.2 Amplitude metadata

| Measure | Value |
|---|---|
| Long-square rows with `stimulus_absolute_amplitude` populated | **8,342 / 8,342 (100%)** |
| Specimens with ≥2 distinct depolarising amplitudes | **311 (100%)** |
| Distinct depolarising amplitudes per specimen | min **4**, median **14**, max **51** |
| Distinct amplitudes per specimen, any sign | median **20** |
| Per-specimen amplitude span | most-negative component median **−110**, most-positive median **270** |

Stimulus units are **not uniform within the population**: 7,009 rows are labelled `Amps`
and 1,333 rows `pA`. Observed magnitudes (−270 … 950) are only physically sensible as
picoamperes, so the label and the magnitude disagree. See §6.

### 2.3 Metadata completeness

| Field | Present | Note |
|---|---|---|
| `ephys_sampling_rate` | 311 / 311 | **50 kHz: 182**, 200 kHz: 129 |
| `nwb_file_id` | 311 / 311 | download reference resolved |
| `ephys_failed == false` | 311 / 311 | no failed results in this layer |
| `metadata_complete` | 311 / 311 | Phase 0 flag |
| `has_morphology` | 91 / 311 (29.3%) | |
| `nwb_download_url` / model download URL | 311 / 311 | reference only, nothing fetched |

`needs_nwb_validation = 262`, `needs_model_validation = 30`.

### 2.4 Stimulus categories represented (current-clamp, per specimen)

| Category | L2/3 | L5 (for comparison) |
|---|---|---|
| long_square | 100.0% | 100.0% |
| short_square | 100.0% | 100.0% |
| ramp | 100.0% | 99.6% |
| noise | 89.7% | 87.7% |
| other | 98.4% | 97.4% |

### 2.5 Model availability

| Measure | Value |
|---|---|
| Specimens with ≥1 biophysical model | **30** |
| — Biophysical **perisomatic** | 28 |
| — Biophysical **all-active** | 25 |
| — **Both** classes | **23** |
| GLIF-only (not biophysical) | 175 |
| Phase 0 eligibility | **PASS 30**, CONDITIONAL 232, FAIL 49 |

---

## 3. VISp layer 5 findings

### 3.1 Long-square availability

| Measure | Value |
|---|---|
| Specimens | 505 |
| Specimens with ≥1 long-square sweep | **505 (100%)** |
| Long-square sweeps in total | **12,362** |
| … counted by the explicit encoding only | 454 specimens / 11,022 sweeps |
| Long-square sweeps per specimen | min **7**, p25 19, **median 23**, p75 29, max **64**, mean 24.5 |

Distribution of long-square sweeps per specimen:

| Sweeps | 0–5 | 6–9 | 10–14 | 15–19 | 20–29 | 30+ |
|---|---|---|---|---|---|---|
| Specimens | 0 | 6 | 36 | 96 | **259** | **108** |

### 3.2 Amplitude metadata

| Measure | Value |
|---|---|
| Long-square rows with `stimulus_absolute_amplitude` populated | **12,362 / 12,362 (100%)** |
| Specimens with ≥2 distinct depolarising amplitudes | **505 (100%)** |
| Distinct depolarising amplitudes per specimen | min **2**, median **13**, max **42** |
| Distinct amplitudes per specimen, any sign | median **19** |
| Per-specimen amplitude span | most-negative component median **−110**, most-positive median **250** |

Units: 11,022 rows `Amps`, 1,340 rows `pA` — same inconsistency as §2.2.

### 3.3 Metadata completeness

| Field | Present | Note |
|---|---|---|
| `ephys_sampling_rate` | 505 / 505 | **200 kHz: 274**, 50 kHz: 231 |
| `nwb_file_id` | 505 / 505 | download reference resolved |
| `ephys_failed == false` | 503 / 505 | **2 flagged failed** |
| `metadata_complete` | 505 / 505 | Phase 0 flag |
| `has_morphology` | 148 / 505 (29.3%) | |
| `needs_nwb_validation` / `needs_model_validation` | 452 / 79 | |

### 3.4 Model availability

| Measure | Value |
|---|---|
| Specimens with ≥1 biophysical model | **79** |
| — Biophysical **perisomatic** | 71 |
| — Biophysical **all-active** | 40 |
| — **Both** classes | **32** |
| GLIF-only (not biophysical) | 266 |
| Phase 0 eligibility | **PASS 79**, CONDITIONAL 373, FAIL 53 |

---

## 4. Comparison

| Dimension | VISp 2/3 | VISp 5 | Verdict |
|---|---|---|---|
| Specimens | 311 | 505 | L5 larger |
| With ≥1 long-square sweep (units-aware) | **311 (100%)** | **505 (100%)** | **identical** |
| With ≥1 long-square sweep (explicit `clamp_mode`) | 262 (84.2%) | 454 (89.9%) | L5 slightly better; both artifacts of §1.3 |
| Long-square sweeps, total | 8,342 | 12,362 | scales with population |
| Median long-square sweeps/specimen | **25** | **23** | comparable (L2/3 +2) |
| ≥20 sweeps per specimen | 241 (77.5%) | 367 (72.7%) | L2/3 marginally denser |
| Minimum long-square sweeps | 7 | 7 | identical floor |
| Amplitude field populated | 100% | 100% | **identical** |
| ≥2 distinct depolarising amplitudes | 311 (100%) | 505 (100%) | **identical** |
| Median distinct depolarising amplitudes | **14** | **13** | comparable |
| Median per-specimen amplitude span | −110 … 270 | −110 … 250 | **comparable** |
| Same stimulus categories available | LS/SS/Ramp 100%, noise 89.7% | LS/SS 100%, Ramp 99.6%, noise 87.7% | **equivalent** |
| Sampling rate recorded | 100% (50 kHz 59% / 200 kHz 41%) | 100% (200 kHz 54% / 50 kHz 46%) | L5 marginally faster-leaning |
| Failed ephys results | 0 | 2 | negligible |
| `has_morphology` | 29.3% | 29.3% | **identical** |
| PASS (Phase 0) | 30 | 79 | L5 2.6× |
| Biophysical perisomatic | 28 | 71 | L5 2.5× |
| Biophysical all-active | 25 | 40 | L5 1.6× |
| **Both** model classes | 23 | 32 | L5 1.4× — both usable for class comparison |
| Spiny (pyramidal-like) PASS cells | **7** | **41** | **L5 5.9× — the decisive gap** |

### 4.1 Direct answers

1. **Are stimulus categories represented similarly?** Yes — effectively identically.
   Long square, short square and ramp are present in ~100% of both populations; noise in
   ~88–90%.
2. **Are current amplitudes available and comparable?** Yes — 100% populated in both, with
   comparable spans (−110 … ~250–270) and comparable step counts (13–14 distinct
   depolarising steps). **However the declared unit is inconsistent** (§6), so the
   amplitudes are *comparable to each other* but their absolute scale is unverified.
3. **Are sweep counts sufficient?** Yes, on both counts. Every specimen in both layers has
   ≥7 long-square sweeps (median 23–25), which comfortably supports the ≥6 threshold and a
   train/held-out amplitude split.
4. **Obvious metadata completeness differences?** Only one, and it is not in the sweeps:
   **cell-class composition.** Long-square, amplitude and stimulus metadata are equally
   complete. But layer 2/3 is 72.7% aspiny (Pvalb+/Gad2+ interneurons) while layer 5 is
   47.1% spiny, and among PASS cells L2/3 offers only **7 spiny** candidates versus **41**
   in L5.

---

## 5. Five provisional candidates per layer

### 5.1 Ranking criteria (documented fields only)

Hard filter: `eligibility == "PASS"`, which already requires mouse, identified region and
layer, a non-failed `EphysResult`, ≥6 long-square sweeps with ≥3 depolarising, ≥1
biophysical model with a resolved download reference, and a resolved NWB reference.

Tie-break order, applied lexicographically:

1. `has_morphology` — descending (a reconstruction exists for morphology-aware analysis)
2. **both** model classes present (`n_biophysical_perisomatic > 0` **and**
   `n_biophysical_all_active > 0`) — enables the perisomatic-vs-all-active contrast
   *within the same cell*
3. distinct depolarising amplitudes — descending (capacity for held-out amplitude
   generalisation)
4. long-square sweep count — descending (train/validation split capacity)
5. `ephys_sampling_rate` — 200 kHz before 50 kHz
6. `specimen_id` ascending — a deterministic, arbitrary final tie-break

**These are provisional candidates for validation, not a selection.**

### 5.2 VISp layer 2/3 — top 5

All 30 PASS cells in this layer have `has_morphology`, are 200 kHz, and 23 of 30 carry both
model classes; the ranking discriminates mainly on criteria 3 and 4.

| Rank | Specimen | Genotype (driver) | Long-square sweeps | Distinct dep. amplitudes | Perisomatic | All-active | Morphology |
|---|---|---|---|---|---|---|---|
| 1 | **341442651** | Pvalb-IRES-Cre | 48 | 28 | 1 | 1 | yes |
| 2 | **488501071** | Pvalb-IRES-Cre | 38 | 28 | 1 | 1 | yes |
| 3 | **484635029** | Pvalb-IRES-Cre | 40 | 24 | 1 | 1 | yes |
| 4 | **485184849** | Pvalb-IRES-Cre | 40 | 24 | 1 | 1 | yes |
| 5 | **333604946** | Pvalb-IRES-Cre | 36 | 19 | 1 | 1 | yes |

### 5.3 VISp layer 5 — top 5

| Rank | Specimen | Genotype (driver) | Long-square sweeps | Distinct dep. amplitudes | Perisomatic | All-active | Morphology |
|---|---|---|---|---|---|---|---|
| 1 | **482516713** | Pvalb-IRES-Cre | 47 | 30 | 1 | 1 | yes |
| 2 | **323540736** | Gad2-IRES-Cre | 34 | 28 | 1 | 1 | yes |
| 3 | **471077857** | Pvalb-IRES-Cre | 40 | 24 | 1 | 1 | yes |
| 4 | **471129934** | Rbp4-Cre_KL100 *(spiny/intact)* | 35 | 24 | 1 | 1 | yes |
| 5 | **469610831** | Pvalb-IRES-Cre | 40 | 23 | 1 | 1 | yes |

### 5.4 Ties

- **L2/3 ranks 3 and 4 are a genuine tie.** Specimens 484635029 and 485184849 agree on every
  criterion (both classes, 24 distinct depolarising amplitudes, 40 long-square sweeps,
  200 kHz). They are ordered only by the arbitrary `specimen_id` tie-break and should be
  treated as **equal rank**.
- L2/3 rank 1 and rank 2 also share 28 distinct amplitudes and are separated only by sweep
  count (48 vs 38).
- No ties occur in the L5 top 5.

### 5.5 Critical caveat — these criteria select interneurons

Ranking by "most complete metadata" is **not** a neutral criterion in this database. Allen
reconstructed and modelled a biased subset, and Pvalb+ aspiny cells dominate it. The result
is that **9 of the 10 candidates above are aspiny interneurons** (8 Pvalb+, 1 Gad2+).

If the planned experiments target **pyramidal / excitatory** cells, the main ranking is the
wrong list. Restricting to `dendrite_type == "spiny"` PASS cells gives:

| Rank | VISp 2/3 (only **7** spiny PASS cells exist) | VISp 5 (**41** exist) |
|---|---|---|
| 1 | 382982932 — Nr5a1-Cre, 29 LS, 17 dep. amp, both classes | 471129934 — Rbp4-Cre, 35 LS, 24 dep. amp, both classes |
| 2 | 318808427 — Nr5a1-Cre, 19 LS, 14, both | 476048909 — Rorb-IRES2-Cre-D, 33 LS, 20, both |
| 3 | 477127614 — Slc17a6-IRES-Cre, 19 LS, 11, both | 468120757 — Scnn1a-Tg3-Cre, 29 LS, 19, both |
| 4 | 486262299 — Cux2-CreERT2, 38 LS, 31, **all-active only** | 485574832 — Rbp4-Cre, 28 LS, 18, both |
| 5 | 476087653 — Nr5a1-Cre, 22 LS, 13, **perisomatic only** | 314822529 — Rorb-IRES2-Cre-D, 24 LS, 17, both |

Under a pyramidal-cell requirement, **layer 2/3 is thin: 7 cells in total, and only 3 of
them carry both model classes** (3 perisomatic-only, 1 all-active-only), against **41 spiny
PASS cells in layer 5, 13 of which carry both classes**. This is the single most
decision-relevant asymmetry in this note, and it is a property of the cell-class
composition, **not** of long-square availability — which is equal.

### 5.6 Continuity with the previous project

Specimen **485909730** (VISp layer 5, `Cux2-CreERT2;Ai14`) remains `PASS` with 12
long-square sweeps, 6 distinct depolarising amplitudes, a perisomatic model and morphology —
but it is **below every candidate listed above** on sweep count and amplitude coverage. It
remains a valid reference cell, not the richest one available.

---

## 6. What this inventory cannot establish

Everything below requires opening files, and Phase 0 downloaded nothing.

1. **Exact stimulus amplitudes.** The `Amps`/`pA` label conflict means the numeric field
   cannot be converted to a physical unit from metadata alone. No NWB stimulus trace has
   been read, so neither the offset nor the scale is confirmed. **No amplitude in this note
   should be treated as a calibrated current.**
2. **Whether a sweep is usable at all.** Metadata proves a sweep *exists*, not that it has a
   stable baseline, correct bridge balance, no seal degradation, or a valid holding current.
3. **Calibration state** — bridge balance, series resistance, pipette offset, liquid-junction
   potential, amplifier filtering: none of these appear in any committed field.
4. **Holding potential and resting membrane potential** per sweep, and whether they are
   consistent across a cell's sweep series.
5. **Sweep-level quality and spike-detection validity** — the committed `num_spikes` is
   metadata, not a verified electrophysiological measurement.
6. **Which sweeps are truly "held out" in a scientific sense** — a distinct amplitude value
   is not proof of an independent, usable protocol step.
7. **Model archive contents.** The inventory records a resolved download reference and a
   template name; it does not show parameter values, the fit configuration, or whether the
   model reproduces the cell's recordings.
8. **Whether the two layers need different model classes.** The counts show which classes
   *exist*, not which class is *appropriate*; that is an empirical question for Phase 1.
9. **Reason for the 181 missing `clamp_mode` values**, and whether those cells would pass a
   re-derived eligibility test — Phase 0 classification was not recomputed here.

---

## 7. Recommendation for targeted NWB validation

Long-square availability is **not** the discriminating factor: both layers are at 100%
coverage with comparable sweep counts (median 25 vs 23) and comparable amplitude structure.
The decision should therefore be driven by **cell class** and **model class**, and validated
on a small, deliberate sample:

1. **Resolve the unit question first.** Download **one** NWB file for one candidate and
   compare `stimulus_absolute_amplitude` against the actual current trace. Until this is
   settled, no amplitude-based protocol can be trusted.
2. **Validate 2–3 cells per layer per cell class**, not 5. Suggested starting set:
   - L2/3 interneuron: 341442651; L5 interneuron: 482516713
   - L2/3 pyramidal: 382982932; L5 pyramidal: 471129934
   This also tests, cheaply, whether layer 2/3 pyramidal coverage is genuinely thin.
3. **For each validated cell, confirm before any modelling:** sweep amplitudes and units,
   sampling rate, holding current and membrane potential, long-square sweep count actually
   present in the file, and absence of seal/QC failures.
4. **Confirm the model class exists and loads** — one *Biophysical–perisomatic* archive and
   one *Biophysical–all-active* archive, checking that a single class can be used for both
   populations (23 L2/3 and 32 L5 cells carry both classes, so this is testable within a
   cell).
5. **Do not extend to the full shortlist** until steps 1–4 agree between the two layers.
   If they diverge, the divergence itself is the finding.
6. **Re-derive the 181 no-`clamp_mode` specimens' long-square counts** only if a decision
   depends on them; it does not, under the equal-coverage result above.

**Provisional answer to the question asked:** long-square current-clamp availability is
**comparable** between VISp layer 2/3 and layer 5, at 100% specimen coverage in both, with
layer 2/3 marginally higher on median sweep count (25 vs 23). The populations are **not**
equivalent in pyramidal-cell model coverage (7 vs 41 PASS cells), and that difference — not
sweep availability — should determine which layer the planned experiments use.

---

*Read-only analysis. No CSV, report or scientific result was modified; no population was
selected and no cell frozen.*

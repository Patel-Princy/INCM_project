# Cross-specimen validation of NWB stimulus units

**Phase:** 1B — unit and sweep validation across specimens
**Scope:** four new Allen NWB recordings, one per (unit-label × cortical-layer) stratum,
plus the Phase 1A recording as the `Amps` / L2-3 reference
**Date:** 2026-11-06
**Status:** complete; **all five recordings PASS**
**Branch:** `ashish-work`

This report answers one question: *are the stimulus amplitudes in the committed
inventory numerically compatible with the raw stimulus samples in the NWB files,
and under what unit convention?* It does not fit any model, extract any feature,
or select any population.

---

## 1. Headline result

| | |
|---|---|
| Recordings validated | **5** (4 new + the Phase 1A reference) |
| Long-square sweeps validated | **236 / 236 matched** |
| Largest \|measured − inventory\| | **5.116 × 10⁻¹³ pA** |
| Largest \|measured − `aibs_stimulus_amplitude_pa`\| | **1.497 × 10⁻⁵ pA** |
| Specimens with a scale (1e±3n) discrepancy | **0** |
| New NWB downloads | **4** (exactly the four pre-registered) |

**The `Amps` and `pA` labels are neither reliable nor inverted — they are
inconsistent, and they describe the wrong object.** In every one of the five
files the raw stimulus array is in **amperes** and every `stimulus_absolute_amplitude`
value is in **picoamperes**. The label `pA` happens to describe the *inventory
column* correctly; the label `Amps` does not. Neither label describes the *NWB
array*, for which `Amps` would be the correct token. Full argument in §8.

---

## 2. What was and was not done

Performed:

* read `results/phase1/NWB_VALIDATION_341442651.md`,
  `results/dataset_inventory/LONG_SQUARE_FEASIBILITY_NOTE.md`,
  `data/metadata/cell_inventory.csv`, `data/metadata/sweep_inventory.csv`;
* selected the four specimens from the committed inventory and recorded the
  selection criteria and IDs **before** downloading anything (§3);
* downloaded **four** NWB files into the existing ignored cache
  `data/nwb_cache/` (no other downloads of any kind);
* wrote `scripts/validate_nwb_stimulus_units.py` and validated all five files
  with it, independently inspecting each file's structure first;
* added `scripts/requirements-nwb-validation.txt` (see §12.3 for why this was
  judged necessary).

Deliberately **not** done: no model archives were downloaded; no FHN or other
neuron model was run or fitted; no Phase 0 CSV, manifest, or candidate ranking
was modified; no population or cell was frozen; `main` was not touched; no raw
NWB file or intermediate table was staged for commit.

`h5py==3.16.0` was already installed and was reused; nothing new was installed.

---

## 3. Specimen selection

### 3.1 Pre-registered criteria

Recorded to console at **18:20:21 on 2026-11-06, before any download**:

| id | criterion |
|---|---|
| C1 | all long-square inventory rows for the specimen carry a **single** `stimulus_units` value |
| C2 | rows are `current_clamp`, **or** `clamp_mode` is null **and** `stimulus_units == 'pA'` (the Phase 0 units-aware rule) |
| C3 | `eligibility == PASS` — **applied to strata A and B only** (§3.3) |
| C4 | resolved `nwb_download_url` |
| C5 | ≥ 6 long-square sweeps |
| C6 | preference order: has a biophysical model → has morphology → more long-square sweeps → lower `specimen_id` |
| C7 | no specimen reused across strata; must differ from `341442651` |

### 3.2 The label is a campaign marker, not a per-sweep property

Across the whole inventory, **1,694 of 1,694** specimens carry a single
long-square label — **zero** specimens are mixed:

| `stimulus_units` | specimens | `clamp_mode` on those rows | Phase 0 eligibility |
|---|---|---|---|
| `Amps` | 1,513 | `current_clamp` (1,513 / 1,513) | 201 PASS, 1,309 CONDITIONAL, 3 FAIL |
| `pA` | 181 | **null** (181 / 181) | **181 FAIL, 0 PASS, 0 CONDITIONAL** |

The `pA` label and a null `clamp_mode` are **perfectly confounded**. This is the
single most important selection finding of this phase.

### 3.3 Blocker: strata C and D could not be filled strictly

**Under the stated criteria, strata C (`pA` / L2-3) and D (`pA` / L5) have zero
candidates — not zero *good* candidates, but zero candidates of any quality.**

The reason is structural, not statistical: PASS requires ≥6 long-square
*current-clamp* sweeps, and every `pA`-labelled specimen has `clamp_mode = null`,
so the Phase 0 rule classified all 181 as FAIL. Requiring PASS of a `pA`
specimen is therefore unsatisfiable **by construction**, and eligibility was
itself computed from the very field under test — so applying C3 would not have
made strata C and D better, only untestable.

This is reported here rather than resolved silently. One criterion was relaxed
and nothing else:

> **C3 (`eligibility == PASS`) was dropped for strata C and D only.**
> C1, C2, C4, C5, C6 and C7 were retained unchanged. The model preference in C6
> is inapplicable to these strata: **all 181** `pA`-labelled specimens have
> `n_biophysical_models = 0`, so preferring a model was not possible for any of
> them, and no criterion was traded away to obtain a labelled specimen.

Consequently the C and D verdicts in §5 come from Phase 0 `FAIL` specimens. They
are sound as *unit* evidence (the unit question does not depend on eligibility),
but they must not be read as an endorsement of those specimens for later phases.

### 3.4 Selected specimens

| stratum | specimen_id | species line | layer | depth class | rate | eligibility | label | LS sweeps |
|---|---|---|---|---|---|---|---|---|
| **A1** (1A reference) | `341442651` | Pvalb-IRES-Cre;Ai14-178310.02.01.01 | VISp 2/3 | aspiny | 200 kHz | PASS | `Amps` | 48 |
| **A2** | `484635029` | Pvalb-IRES-Cre;Ai14-201791.05.01.01 | VISp 2/3 | aspiny | 200 kHz | PASS | `Amps` | 40 |
| **B** | `482516713` | Pvalb-IRES-Cre;Ai14-199001.04.02.01 | VISp 5 | aspiny | 200 kHz | PASS | `Amps` | 47 |
| **C** | `614777438` | Vipr2-IRES2-Cre;Pvalb-T2A-FlpO;Ai65-344474.02.02.01 | VISp 2/3 | aspiny | 50 kHz | FAIL (relaxed) | `pA` | 55 |
| **D** | `583434059` | Chrna2-Cre_OE25;Pvalb-T2A-Dre;Ai66-312583.02.02.01 | VISp 5 | aspiny | 50 kHz | FAIL (relaxed) | `pA` | 46 |

`A2` was chosen over `485184849` (also 40 sweeps, 2 biophysical models, morphology)
by the C6 tie-break on `specimen_id`; `A2` additionally carries 7 models in total
against 4. `B`, `C` and `D` are the top C6 candidates of their strata.

A1 is not a fifth stratum, only the reference case already published in Phase 1A;
it is re-run here so that the new script can be shown to reproduce the earlier
hand-derived result exactly (§12.2).

---

## 4. File identities and checksums

All four were fetched from
`http://api.brain-map.org/api/v2/well_known_file_download/<nwb_file_id>`
over HTTP through `requests`, with resumable `Range` requests (the server reset
several connections mid-stream; one file needed 12 attempts and was completed by
byte-range resumption — see §15.1).

| stratum | specimen | `nwb_file_id` | bytes | SHA-256 |
|---|---|---|---|---|
| A1 | 341442651 | 491200479 | 87,791,928 | `02604560436c649a91efdbc962fb08eec66372c152ba99c1b22590ef9d43262a` |
| A2 | 484635029 | 491317612 | 140,035,946 | `9cbc1b4d7a95c9f434c2aaa0cb7b20431640c3347241e90eb0ca394056c33981` |
| B | 482516713 | 491316028 | 61,787,818 | `19eb9155820fd9ce357c981e567d6af0f358e9dec4a87f1fa48fe4f8db321557` |
| C | 614777438 | 646445395 | 43,850,605 | `38e7eca23a1a14ec91f571e5001ca0e1bb1e8c221c5cc17ab6ceeff2f6685754` |
| D | 583434059 | 659441472 | 24,089,968 | `94e9061ac571ac54ea71b25cf997a328d1bca1e506ebe66af038c27a4ffadcb1` |

Sizes equal the server `Content-Length` in every case, so no file is truncated.
Allen publishes **no upstream checksum**, so these locally computed SHA-256
values are the only identity anchor and are reproducible from the URLs above.

Cache location `data/nwb_cache/`; covered by `.gitignore:59` (`*.nwb`).
**Zero `.nwb` files are tracked by Git.**

### 4.1 Identity chain

The file must name the specimen it claims to be. Verified for all five:

| specimen | `/general/aibs_specimen_id` | `/general/session_id` | inventory `ephys_result_id` | agrees |
|---|---|---|---|---|
| 341442651 | 341442651 | 341442649 | 341442649 | yes |
| 484635029 | 484635029 | 484635027 | 484635027 | yes |
| 482516713 | 482516713 | 482516705 | 482516705 | yes |
| 614777438 | 614777438 | 614777322 | 614777322 | yes |
| 583434059 | 583434059 | 583434044 | 583434044 | yes |

`/stimulus/presentation` and `/acquisition/timeseries` contain the **same number**
of series in every file (77, 116, 67, 109, 78), and `/epochs` contains exactly
**3 ×** that count in all five. No series is orphaned.

**The root `identifier` field is not a reliable identity anchor** (see §10.3): only
the three 200 kHz files contain the human-readable
`"Allen Institute for Brain Science, Ephys Result <id>"` form. Identity above is
therefore established from `aibs_specimen_id` + `session_id` + the download id,
all of which agree.

---

## 5. Per-specimen verdict

| stratum | specimen | long-square rows (inv / NWB / matched) | unit in NWB | resolution | verdict |
|---|---|---|---|---|---|
| A1 | 341442651 | 48 / 48 / 48 | `Amps` | 0.0 | **MATCH** |
| A2 | 484635029 | 40 / 40 / 40 | `Amps` | 0.0 | **MATCH** |
| B | 482516713 | 47 / 47 / 47 | `Amps` | 0.0 | **MATCH** |
| C | 614777438 | 55 / 55 / 55 | **`A`** | **absent** | **MATCH** |
| D | 583434059 | 46 / 46 / 46 | `Amps` | 0.0 | **MATCH** |

"Inventory-only" sweeps (inventory long-square rows with no NWB counterpart) are
**empty for all five**. Every long-square sweep number present in the inventory is
also present in the NWB file, and vice versa.

`conversion = 1.0` and `offset` absent in all five; `resolution = 0.0` in four and
absent in `614777438`. Neither `conversion` nor `resolution` changes any value
here — `resolution = 0.0` is a placeholder, not a quantisation step.

---

## 6. How sweeps were matched

Phase 1A matched on the stimulus template (`data_link` → `C1LSCOARSE…[i]x<mult>`)
and *verified* the sweep number as a check. **That route does not exist in the
newer campaign**, so the two were swapped and the check inverted:

1. select presentation series whose `aibs_stimulus_name` is `Long Square`;
2. parse the sweep number from the series name;
3. join to the inventory on `sweep_number` with a **one-to-one** assertion —
   so a duplicate would raise rather than silently produce a cartesian product
   (the Phase 1A bug that generated a spurious 50 pA error);
4. *then* check the template/description where one exists, and report the check
   as a separate column instead of using it as a key.

Result of step 4: the template base name equals the inventory
`stimulus_description` for 48/48, 40/40 and 47/47 sweeps in the 200 kHz files, and
for **0/55 and 0/46** in the newer files. That is not a matching failure — those
files contain **no templates and no description** (§10.2), so there is nothing to
compare. The matched amplitudes are exact in both cases, which is why the
description check is advisory and the amplitude comparison is decisive.

---

## 7. Measured versus inventory amplitudes

Plateau current is extracted as the **dominant non-baseline constant level** (the
longest run of identical samples that is not the baseline). The naive
maximum-excursion detector used in early Phase 1A work is not used anywhere,
because it latches onto the embedded pre-step pulse (§9).

Measured pA = `raw` × `conversion` + `offset`, then × 10¹² when the declared unit
is amperes. No other arithmetic is applied to any value.

| stratum | specimen | n | inv min | inv max | n ≥ 0 | max \|Δ vs inventory\| | max \|Δ vs `aibs_pA`\| | verdict |
|---|---|---|---|---|---|---|---|---|
| A1 | 341442651 | 48 | −270 | +530 | 34 | 5.116e−13 | 1.497e−05 | MATCH |
| A2 | 484635029 | 40 | −270 | +490 | 28 | 5.116e−13 | 1.497e−05 | MATCH |
| B | 482516713 | 47 | −270 | +590 | 33 | 5.116e−13 | 1.497e−05 | MATCH |
| C | 614777438 | 55 | −110 | +670 | 50 | 5.116e−13 | 5.116e−13 | MATCH |
| D | 583434059 | 46 | −110 | +590 | 40 | 5.116e−13 | 5.116e−13 | MATCH |

All values in pA. Full per-sweep tables are reproduced by the script (§12).

Representative rows, including both extremes of the amplitude grid:

| specimen | sweep | inventory | measured | aibs_pA | onset | duration |
|---|---|---|---|---|---|---|
| 341442651 | 24 | −270 | −270 | −270 | 1.02 s | 1000.00 ms |
| 341442651 | 64 | +530 | +530 | +530 | 1.02 s | 1000.00 ms |
| 484635029 | 30 | −270 | −270 | −270 | 1.02 s | 1000.00 ms |
| 482516713 | 20 | −270 | −270 | −270 | 1.02 s | 1000.00 ms |
| 614777438 | 41 | −110 | −110 | −110 | 1.02 s | 1000.00 ms |
| 614777438 | 96 | +630 | +630 | +630 | 1.02 s | 1000.00 ms |
| 583434059 | 34 | −110 | −110 | −110 | 1.02 s | 1000.00 ms |

**236 / 236 sweeps agree.** The largest residual (5.116 × 10⁻¹³ pA, occurring at a
670 pA step) is 7.6 × 10⁻¹⁶ of that step — i.e. the float32 representation error
of the commanded level and nothing else. The `aibs_stimulus_amplitude_pa` residual is
larger in the 200 kHz files (1.5 × 10⁻⁵ pA) purely because that field stores the
pA value as float32 directly, whereas the newer files evidently derive it from the
same array.

---

## 8. Are the `Amps` and `pA` labels reliable, inverted, or inconsistent?

**Inconsistent — and, more precisely, ambiguous about what they label.** They are
not inverted: no specimen shows a 10¹² discrepancy in either direction, which is
what inversion would produce and what the validator would have reported as
`MISMATCH_SCALE`.

The token `stimulus_units` is being read by different consumers as describing two
different objects, and it is right about one of them:

| consumer | what the numbers are | what `Amps` claims | what `pA` claims | who is right |
|---|---|---|---|---|
| **NWB raw array** (`data` + `@unit`) | amperes (magnitude ≈ n × 10⁻¹⁰) | A | pA | **`Amps`** |
| **inventory `stimulus_absolute_amplitude`** | picoamperes (magnitude ≈ n) | A | pA | **`pA`** |

Evidence:

| # | observation | specimens |
|---|---|---|
| E1 | raw plateau values are of order 10⁻¹⁰, and measured × 10¹² reproduces the inventory exactly | 5 / 5 |
| E2 | `aibs_stimulus_amplitude_pa` — a field that names its unit in pA — equals measured × 10¹² to ≤1.5e−05 pA | 5 / 5 |
| E3 | the declared NWB unit, normalised, is amperes in every file (`Amps` ×4, `A` ×1) | 5 / 5 |
| E4 | `conversion = 1.0` and no `offset` anywhere, so the stored numbers are already in the declared unit | 5 / 5 |
| E5 | specimens labelled `pA` show the *same* ampere-valued arrays as specimens labelled `Amps` | 2 / 2 `pA` |
| E6 | an inverted scale would have produced a 10¹² ratio; the observed ratio is 1.000000000000 | 0 / 5 |
| E7 | the `Amps` label co-occurs with `clamp_mode = current_clamp`; the `pA` label co-occurs with `clamp_mode = null` | 1,694 / 1,694 |
| E8 | Phase 1A established, from a cached Allen API response, that the API itself pairs `stimulus_units = "Amps"` with pA-scale amplitudes | 1 |

Reading of E1–E8: `stimulus_units` is a **campaign/API artifact**, not a scaling
instruction for either column. In the newer campaign it happens to read `pA`,
which correctly describes the amplitude column; in the older campaign it reads
`Amps`, which correctly describes the NWB array. Both campaigns store the same
physical quantity in the same way in NWB; they differ only in a metadata token.

**Practical consequence:** `stimulus_units` must not be used to scale anything.
The NWB `@unit` attribute *is* trustworthy once `A` and `Amps` are treated as the
same unit — but only after case/plural normalisation. An exact-match test against
`'Amps'` silently breaks on `614777438`.

---

## 9. The embedded pre-step pulse: common, not variable

Every long-square sweep of every specimen carries a short constant-current pulse
*before* the step, in addition to the step itself. Measured directly:

| specimen | rate | plateau samples | plateau duration | pulse samples | pulse duration | pulse amplitude | sweeps with exactly 1 such run |
|---|---|---|---|---|---|---|---|
| 341442651 | 200 kHz | 200,000 | 1000.000 ms | 2,001 | 10.005 ms | +50.000 pA | 48 / 48 |
| 484635029 | 200 kHz | 200,000 | 1000.000 ms | 2,001 | 10.005 ms | +50.000 pA | 40 / 40 |
| 482516713 | 200 kHz | 200,000 | 1000.000 ms | 2,001 | 10.005 ms | +50.000 pA | 47 / 47 |
| 614777438 | 50 kHz | 50,000 | 1000.000 ms | 501 | 10.020 ms | +50.000 pA | 55 / 55 |
| 583434059 | 50 kHz | 50,000 | 1000.000 ms | 501 | 10.020 ms | +50.000 pA | 46 / 46 |

* timing: constant at **0.0050 – 0.0150 s** in all 236 sweeps;
* amplitude: **+50.000 pA** in all 236 sweeps;
* duration: **10 ms + one sample** in both campaigns (2,001 samples at 200 kHz,
  501 at 50 kHz) — the identical protocol event expressed at two sample rates;
* it is the **only** non-step constant run in any sweep: the count of extra runs
  is exactly 1 for every one of the 236 sweeps.

**Verdict: common and invariant.** It does not vary with specimen, layer, unit
label, campaign, or sampling rate. It is a fixed 50 pA / 10 ms probe delivered
before the step, not a per-file artifact.

Two consequences for downstream work:

1. It **must not** be excluded by a fixed early-time blanking rule that happens to
   sit outside it. Phase 1A recommended dropping 0–0.1 s, which does work here
   (the pulse ends at 15 ms), but that is a coincidence of this protocol, not a
   property the validator assumes. The script instead classifies runs by *duration
   relative to the step* and reports every one of them.
2. It explains the step onset of 1.02 s: the response and stimulus both carry a
   fixed prefix, so no downstream code should hardcode 1.02 s either. The script
   infers onset and reports it per sweep (1.0200 s in all 236, which is a finding,
   not an assumption).

Note where a step of exactly ±50 pA occurs, it carries the same value as the pulse.
Because the step and the pulse are separate runs of that value, the dominant-level
rule still separates them correctly (200,000 vs 2,001 samples); a "largest absolute
value" rule would not.

---

## 10. NWB version and layout differences

### 10.1 Version

All five files are **`NWB-1.0.5`**, stored as a root HDF5 *dataset* `nwb_version`
(not a root attribute, and not under `/general`). Every file has the same root
members: `acquisition`, `analysis`, `epochs`, `file_create_date`, `general`,
`identifier`, `nwb_version`, `processing`, `session_description`,
`session_start_time`, `stimulus`; `/general/generated_by` reads
`pipeline / IVSCC / version / 1.0` in all five. **No structural version change.**

### 10.2 Layout: the newer campaign is a reduced variant

| property | 200 kHz files (A1, A2, B) | 50 kHz files (C, D) |
|---|---|---|
| `nwb_version` | NWB-1.0.5 | NWB-1.0.5 (unchanged) |
| `/stimulus/templates` | 63, 67, 56 children | **0 children** |
| `data_link` attribute | present, `…/templates/C1LSCOARSE…[i]x<mult>` | **absent** |
| `aibs_stimulus_description` | `C1LSCOARSE150217` (truncated `S16`) | literal **`None`** |
| relative-amplitude multiplier | recoverable (`x1`, `x3.4`, …) | **not recoverable** |
| inventory `stimulus_relative_amplitude` | 1.0 – 4.0 | uniformly **10.0** |
| `resolution` attribute | `0.0` | **absent** on `614777438` |
| `gain` | 0.01 | **absent** (NaN) on C and D |
| `electrode_name` | `/general/intracellular_ephys/Electrode 1` | C: `"[u'electrode_0']"`, D: path form |
| `num_samples` per sweep | 1,204,001 – 1,604,001 | 301,000 – 401,000 |
| trace duration | 6.02 – 8.02 s | 6.02 – 8.02 s |

The series *shape* is identical (`Sweep_<n>` group containing `data`,
`starting_time`, and the `aibs_*` datasets), so a reader keyed on that shape works
for both. What is missing in the newer files is the **template indirection layer**
and two electrode fields. A reader keyed on `data_link` fails outright there.

**The inventory `stimulus_relative_amplitude` cannot be cross-checked for C and D**:
it is uniformly 10.0 while there is no multiplier to compare it with. This does
not affect amplitude validation (the absolute amplitude is present and exact) but
it does mean the relative-amplitude column is unverified for those two specimens.

### 10.3 `identifier` is unreliable in the newer campaign

| specimen | root `identifier` |
|---|---|
| 341442651 / 484635029 / 482516713 | `Allen Institute for Brain Science, Ephys Result <ephys_result_id>` |
| 614777438 | `063831c098fe4f0e61973035d7b122215c03a4176b0f1e33e914abf16080332f.edit` |
| 583434059 | **`P.edit`** |

`583434059` carries a 6-character identifier that encodes nothing. Any pipeline
that trusts `identifier` for provenance will accept a meaningless string here.
Provenance must instead be taken from `aibs_specimen_id` + `session_id` (§4.1).

### 10.4 Sampling rate

200 kHz for A1/A2/B, **50 kHz for C/D**, matching `ephys_sampling_rate` in the
inventory in all five. Both rates resolve the 1 s step to exactly 200,000 and
50,000 samples respectively, and the pulse to 2,001 and 501 — i.e. the timings are
rate-independent and the counts scale exactly as they should. This is evidence
that `starting_time @rate` is the correct rate for these series and that no
resampling has occurred.

---

## 11. Sweep coverage

| specimen | inventory sweeps | NWB series | missing from NWB | long-square (inv / NWB) |
|---|---|---|---|---|
| 341442651 | 83 | 77 | 0, 1, 2, 3, 83, 84 | 48 / 48 |
| 484635029 | 122 | 116 | 0, 1, 2, 3, 128, 129 | 40 / 40 |
| 482516713 | 73 | 67 | 0, 1, 2, 3, 94, 95 | 47 / 47 |
| 614777438 | 119 | 109 | 0–5, 105, 116, 117, 118 | 55 / 55 |
| 583434059 | 87 | 78 | 0–4, 90, 101, 102, 103 | 46 / 46 |

The missing sweeps are always a leading run (the first 4–6) and a trailing run
(the last 2–4); no sweep is missing from the middle of a long-square block. This
matches the Phase 1A explanation — NWB 1.0.5 omits the leading voltage-clamp and
the final failed/acquisition sweeps — but the reason is **not re-established here**
for each file; only the count and position pattern is.

**Long-square coverage is complete in all five files** (236 rows, 236 series,
236 matched). For these specimens, "the sweep exists" and "the sweep is usable"
coincide, because the amplitude in each is now independently verified.

---

## 12. The validation script

`scripts/validate_nwb_stimulus_units.py` — scope: stimulus units and sweep
coverage only; no FHN fit, no feature extraction.

```
python scripts/validate_nwb_stimulus_units.py --specimen 341442651
python scripts/validate_nwb_stimulus_units.py --all
python scripts/validate_nwb_stimulus_units.py --all --json-out <path>   # keep out of Git
```

Exit code 0 when every requested specimen reaches a definite verdict
(`MATCH`, `MATCH_SCALE`-free `MISMATCH`), 2 when any is `AMBIGUOUS` or `UNRESOLVED`.

### 12.1 Design decisions that matter

* **No naive maximum-excursion detector.** The plateau is the longest constant
  non-baseline run; all other constant runs are reported. This is what makes it
  immune to the 50 pA pulse at small step amplitudes.
* **No hardcoded onset and no fixed exclusion window.** Onset, offset and duration
  are measured per sweep; nothing assumes 1.02 s or blanks 0–0.1 s.
* **Units are preserved and every conversion is named.** The declared unit string,
  `conversion`, `resolution` and `offset` are printed verbatim. pA is reached by a
  single documented factor from a table in `UNIT_TO_PA`; nothing is inferred from
  magnitude.
* **Unmatched is reported, not forced.** A missing cache file, an absent inventory
  row, a duplicate inventory row, a trace with no non-baseline level, a
  non-baseline run under 100 ms, or an unrecognised unit all yield
  `UNRESOLVED`/`AMBIGUOUS` with a reason, never a guess.
* **Robust to the layout split.** Series are found as groups under
  `/stimulus/presentation` with an `/acquisition/timeseries` fallback; the
  template/description is used only as an advisory check; `A` and `Amps` are
  normalised.
* **The scale verdict is principled.** A ratio within half a decade of an exact
  power of 1000 is `MISMATCH_SCALE`, because that is the only signature a
  unit-prefix error can produce.

### 12.2 Regression against Phase 1A

Run on `341442651`, the script reproduces the hand-derived Phase 1A result exactly:
48/48 MATCH, onset 1.0200 s, plateau 1000.00 ms, embedded run at 0.0050–0.0150 s
at 50.0000 pA in 48/48 sweeps, and the same SHA-256. Behaviour was also exercised
against the negative paths: an unknown specimen → `UNRESOLVED`, exit 2; a missing
cache file → `UNRESOLVED`, exit 2; and `classify()` returns `MISMATCH_SCALE` at
ratios of 10⁶, 10⁹ and 10¹² while leaving a genuine 7× error as `MISMATCH`.

### 12.3 Dependency declaration

The repository had **no** dependency file of any kind (`requirements*.txt`,
`pyproject.toml`, `environment*.yml`, `Pipfile` — none exist); the only environment
information anywhere was prose in `docs/DATASET_INVENTORY_README.md` and
`docs/DATASET_SELECTION_DECISION.md` discussing AllenSDK. A narrow declaration was
therefore added:

`scripts/requirements-nwb-validation.txt` — **`h5py==3.16.0` and nothing else**,
with a header stating that it covers only this validation path and is deliberately
not a full environment. No attempt was made to snapshot the machine's installed
packages.

---

## 13. What is justified, and what is not

### 13.1 Justified by this sample

1. For these five specimens and 236 long-square sweeps, spanning two layers, two
   campaigns and two sampling rates, `stimulus_absolute_amplitude` is in **pA**
   and equals the NWB plateau × 10¹² (with `conversion = 1.0`, no `offset`) to
   within 5.1 × 10⁻¹³ pA.
2. `stimulus_units` is **not** a scaling instruction and must not be used as one.
   The label `Amps` is wrong about the amplitude column; the label `pA` is right
   about it; both are silent about the NWB array, which is in amperes in all five.
3. The NWB `@unit` attribute is correct in all five and is trustworthy **after
   normalising `A` / `Amps`**. Failing to normalise breaks one specimen.
4. The pre-step pulse is a fixed protocol constant — +50 pA, 10 ms + 1 sample,
   5 ms after the recording starts — not a per-file artifact, and it must
   be removed by run-detection rather than by a fixed blanking window.
5. A single unit-handling rule (§14) is safe to adopt **as a rule plus a runtime
   assertion**. Adopting it as an assumption, with no assertion, would have hidden
   the `pA`-labelled specimens' different unit spelling.

### 13.2 Not established

1. **Coverage.** 236 of the 42,231 long-square current-clamp rows in the inventory
   (**0.56 %**), and 5 of 1,694 specimens (**0.30 %**). 4,772 rows (11.3 %) carry
   the `pA` label; 2 of those specimens were tested.
2. **No other census group, layer, or species line** was tested: only VISp L2/3 and
   L5, only aspiny Pvalb/Vipr2/Chrna2 lines. Nothing here licenses a statement about
   L1, L4, L6, spiny cells, or other areas.
3. **Whether every `Amps`-labelled specimen really is pA-valued.** All five tested
   are. The remaining 1,509 `Amps`-labelled specimens are untested; a genuinely
   ampere-valued `Amps` specimen would still validate correctly under §14, but has
   not been observed.
4. **No zero-amplitude case.** The inventory contains **0** long-square rows with
   zero amplitude, so the pA comparison is always defined. That is a fact about
   the data, not a robustness result; a zero-step sweep would have to be reported as
   `UNRESOLVED` because it has no non-baseline plateau to measure.
5. **Whether `stimulus_units` ever disagrees between sweeps of one specimen.** Zero
   mixed specimens exist in this inventory snapshot (1,694/1,694 single-labelled)
   — but that is one snapshot of one table, not a guarantee.
6. **The pulse's purpose.** +50 pA for 10 ms is consistent with a probe/QC or
   bridge-balance check, but Allen does not document it and this task did not
   investigate it. What is measured is its amplitude, timing and universality.
7. **Why the newer campaign omits templates, `gain`, `clamp_mode` and the
   description.** The effect is documented; the cause is not.
8. **Whether the 181 `pA`-labelled specimens' FAIL status is a metadata artifact or
   a genuine data-quality signal.** This was not investigated and **blocks any
   defensible population freeze** (see §15.2).

---

## 14. Recommendation: adopt a common unit-handling policy

**Yes — Phase 1 can adopt a common policy now**, provided it is implemented as a
rule with an assertion rather than as a silent assumption. Recommended rule:

1. **Ignore `stimulus_units` for scaling.** Treat `stimulus_absolute_amplitude`
   (and `stimulus_relative_amplitude` where needed) as picoamperes
   unconditionally.
2. **Derive pA from the NWB array, not from metadata:** read `data`, then
   `unit` (normalise case and plural: `A`, `a`, `amp`, `amps` → amperes;
   `pA` → picoamperes), then apply `physical = raw × conversion + offset`, then a
   single explicit factor to pA.
3. **Assert agreement** between the two on every sweep, at 0.5 pA absolute or
   1e−6 relative, and **fail loudly** rather than continuing. Both figures are
   far above the observed residual (5 × 10⁻¹³ pA) and far below any meaningful
   physiological difference.
4. **Key the sweep match on `sweep_number`** with a one-to-one assertion. Do not
   key on the template or description — they are absent in one of the two
   campaigns.
5. **Locate the plateau by dominant non-baseline run** and drop every other
   constant run (the 50 pA pulse) instead of blanking a fixed time window.
6. **Do not hardcode 1.02 s.** Measure onset per sweep and store it; record it as
   a per-sweep output.
7. **Treat an unrecognised unit, an unmatched sweep, or an absent amplitude as an
   error, not a default.**

Two follow-ups this report recommends but does not perform:

* re-run the eligibility rule with the units-aware clamp-mode inference **before**
  any population is frozen, because the current PASS rule mechanically excludes
  all 181 `pA`-labelled specimens (§3.3);
* extend the validation to a handful of `pA`-labelled and `Amps`-labelled
  specimens in layers other than 2/3 and 5 before the policy is treated as
  population-wide.

---

## 15. Blockers and open issues

1. **Transfer reliability.** The Allen download endpoint reset connections
   repeatedly; one 61.8 MB file needed 12 attempts and was completed only by
   byte-range resumption, and one 24 MB file stalled at 0 bytes and had to be
   re-launched after killing the stalled socket. The four files took ≈77 min of
   transfer time in total, almost all of it lost to resets and retries — the same
   endpoint returned 43.9 MB without interruption in 10 s once a clean connection
   was established. Future phases should download with `Range` resumption and
   short read timeouts from the start.
2. **Population selection is still blocked** by §3.3 / §13.2(8): 181 of 1,694
   specimens are marked FAIL purely because `clamp_mode` is null, which is a
   metadata absence rather than demonstrated bad data. No population may be frozen
   until that is resolved.
3. **`identifier` cannot be trusted** in the newer campaign (§10.3), including one
   file whose identifier is literally `P.edit`.
4. **Two fields are missing in the newer campaign** — `gain` and `resolution` — and
   `stimulus_relative_amplitude` (uniformly 10.0) cannot be cross-checked there.
5. **Only 0.56 % of long-square rows** have been validated (§13.2).
6. `h5py` is now a real, pinned dependency (§12.3); it remains the only third-party
   package this path requires beyond numpy/pandas.

---

## Artefacts and reproduction

Tracked by this phase:

| path | role |
|---|---|
| `scripts/validate_nwb_stimulus_units.py` | reusable validator |
| `scripts/requirements-nwb-validation.txt` | `h5py==3.16.0` only |
| `results/phase1/CROSS_SPECIMEN_UNIT_VALIDATION.md` | this report |

Not tracked, intentionally: `data/nwb_cache/*.nwb` (5 files, 357,556,265 bytes,
covered by `.gitignore:59`), and any JSON/CSV the validator can emit.

Reproduce:

```
python scripts/validate_nwb_stimulus_units.py --all
```

Re-derive the selection from the committed inventory:

```
python - <<'PY'
import pandas as pd
c = pd.read_csv("data/metadata/cell_inventory.csv")
s = pd.read_csv("data/metadata/sweep_inventory.csv")
s["is_cc"] = (s.clamp_mode=="current_clamp") | (s.clamp_mode.isna() & (s.stimulus_units=="pA"))
ls = s[(s.stimulus_category=="long_square") & s.is_cc]
print(ls.groupby("specimen_id").stimulus_units.agg(lambda x: "|".join(sorted(set(x)))).value_counts())
PY
```

Prior phase for comparison:
`results/phase1/NWB_VALIDATION_341442651.md` (specimen `341442651`, verdict
CONDITIONAL). This report supersedes its units conclusion with a five-specimen
basis and leaves its usability caveats intact.

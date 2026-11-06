# Validation of the two provisional pyramidal candidates

**Phase:** 1C — metadata revalidation, NWB validation and model readiness for
specimens `382982932` (VISp L2/3) and `471129934` (VISp L5)

**Status:** both candidates validated; **both are admissible to Phase 2, with
conditions on the L5 cell.** No population was frozen and no model was executed.

**Branch:** `ashish-work`

**Question answered here:** *do these two provisional candidates survive contact
with their own recordings and with their own model references well enough to
carry the layer 2/3 versus layer 5 comparison into Phase 2?*

---

## 1. Headline result

| | 382982932 (L2/3) | 471129934 (L5) |
|---|---|---|
| Metadata revalidated against committed CSVs | **unchanged** | **unchanged** |
| Long-square sweeps matched | **29 / 29** | **35 / 35** |
| Verdict | **MATCH** | **MATCH_CONVERSION_CONFLICT** |
| Largest abs(measured − inventory) | ≤ 5.2 × 10⁻¹³ pA (float64 round-off) | ≤ 5.2 × 10⁻¹³ pA (float64 round-off) |
| Largest abs(measured − `aibs_stimulus_amplitude_pa`) | 7.07 × 10⁻⁶ pA | 5.12 × 10⁻¹³ pA |
| Embedded pre-step pulse | +50.000 pA, 29/29 | +50.000 pA, 35/35 |
| Metadata integrity | clean | **4 corrupted string fields** |
| Both biophysical model classes | yes | yes |
| Model references resolve | yes, as `fit.json` | yes, as `fit.json` |
| Admissible to Phase 2 | **yes** | **yes, conditional** |

The L5 verdict is not a failure of the recording. The stimulus samples in
`471129934` match the inventory exactly; what fails is the file's
`conversion` attribute, which is wrong by 10¹² on the stimulus channel and by
10³ on the acquisition channel. Section 6 establishes this from two independent
witnesses inside the same file. Reporting it as `MATCH` would have hidden a
defect that will corrupt any downstream consumer that obeys NWB 1.x literally;
reporting it as `MISMATCH_SCALE` would have wrongly condemned usable data.

---

## 2. What was and was not done

Performed:

* revalidated every field of §3 against the committed `cell_inventory.csv`,
  `sweep_inventory.csv` and `model_inventory.csv` — the feasibility note was
  **not** taken on trust;
* downloaded **exactly two** NWB files into the ignored cache `data/nwb_cache/`
  (no other NWB file, no model archive, no morphology file);
* ran `scripts/validate_nwb_stimulus_units.py` on both, independently probing
  each file's structure before trusting the script's reading of it;
* improved the validator once, for two defects that this batch actually
  exposed (§6.4);
* inspected the four biophysical `fit.json` descriptors and the two morphology
  references by HTTP range/descriptor read only.

Deliberately **not** done: no model archive was downloaded; no morphology file
was downloaded (references probed for resolvability only); NEURON, FHN or any
other model was not run or fitted; no Phase 0 CSV, manifest or candidate ranking
was modified; no cell or population was frozen; `main` was not touched; no raw
NWB file or scratch table was staged.

`h5py==3.16.0` was already installed and reused. Nothing new was installed.

---

## 3. Metadata revalidated (objective 1)

Both specimens were re-derived from the committed CSVs. **Every value used in
`LONG_SQUARE_FEASIBILITY_NOTE.md` §5.5 still holds**; the note is accurate.

### 3.1 382982932 — VISp layer 2/3

| field | value |
|---|---|
| `specimen_name` | `Nr5a1-Cre;Ai14-177333.03.01.01` |
| `donor_full_genotype` | `Nr5a1-Cre/wt;Ai14(RCL-tdT)/wt` |
| `transgenic_driver_line` | `Nr5a1-Cre` |
| `region_acronym` / `structure_acronym` | `VISp` / `VISp2/3` (structure_id 821) |
| `cortical_layer` | `2/3` |
| `dendrite_type` / `apical_dendrite_status` | `spiny` / `intact` |
| species, donor, sex, age | *Mus musculus*, donor 339692340, M, P51 |
| `ephys_result_id` / `ephys_failed` | 382982929 / false |
| `ephys_sampling_rate` | 200,000 Hz |
| `nwb_file_id` / `nwb_download_url` | 491199232 / resolved |
| `n_sweeps_total` / `_current_clamp` | 80 / 74 |
| `n_long_square` / `_cc` | **29 / 29** |
| depolarising / hyperpolarising rows | 23 / 6 |
| **distinct** depolarising amplitudes | **17** |
| distinct amplitudes, any sign | 23 |
| amplitude span | −110 … +270 pA |
| `long_square_sweep_numbers` | 24–52, contiguous, no gaps |
| `has_morphology` / `reconstruction_id` / type | true / 674389884 / `full` |
| `n_models_total` | 4 = 1 perisomatic + 1 all-active + 2 GLIF |
| `eligibility` | **PASS** |

### 3.2 471129934 — VISp layer 5

| field | value |
|---|---|
| `specimen_name` | `Rbp4-Cre_KL100;Ai14-180747.06.01.01` |
| `donor_full_genotype` | `Rbp4-Cre_KL100/wt;Ai14(RCL-tdT)/wt` |
| `transgenic_driver_line` | `Rbp4-Cre_KL100` |
| `region_acronym` / `structure_acronym` | `VISp` / `VISp5` (structure_id 778) |
| `cortical_layer` | `5` |
| `dendrite_type` / `apical_dendrite_status` | `spiny` / `intact` |
| species, donor, sex, age | *Mus musculus*, donor 469953288, M, P55 |
| `ephys_result_id` / `ephys_failed` | 471129929 / false |
| `ephys_sampling_rate` | 200,000 Hz |
| `nwb_file_id` / `nwb_download_url` | 491202812 / resolved |
| `n_sweeps_total` / `_current_clamp` | 147 / 141 |
| `n_long_square` / `_cc` | **35 / 35** |
| depolarising / hyperpolarising rows | 30 / 5 |
| **distinct** depolarising amplitudes | **24** |
| distinct amplitudes, any sign | 29 |
| amplitude span | −110 … +430 pA |
| `long_square_sweep_numbers` | 25–60 with **28 absent** |
| `has_morphology` / `reconstruction_id` / type | true / 495335491 / `dendrite-only` |
| `n_models_total` | 7 = 1 perisomatic + 1 all-active + 5 GLIF |
| `eligibility` | **PASS** |

### 3.3 Two inventory-level observations

1. **`cell_reporter_id` takes only two distinct values across all 1,694
   specimens** (491913822 for 1,598 of them, 491913824 for 96) and is identical
   for both candidates. It is a near-constant, not a per-cell identifier, and
   must not be used as one.
2. **Sweep 28 of `471129934` exists in neither the inventory nor the NWB file.**
   The inventory is therefore complete with respect to the recording, not
   missing a row. Had it existed, `C1LSCOARSE150216[3]` would have been the
   −50 pA step; the cell's hyperpolarising series is consequently
   −110/−90/−70/−30/−10 with **−50 absent**, whereas `382982932` has the full
   six-point hyperpolarising set.

---

## 4. File identities and checksums

Fetched from `http://api.brain-map.org/api/v2/well_known_file_download/<id>`
with resumable `Range` requests; both completed on the **first attempt**
(94 MB in 25.7 s, 117 MB in 29.8 s — materially easier than the Phase 1B batch).

| specimen | `nwb_file_id` | bytes | SHA-256 |
|---|---|---|---|
| 382982932 | 491199232 | 94,207,824 | `d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63` |
| 471129934 | 491202812 | 117,131,886 | `ecab60d2424d27d50f773ada32f669b8a88caa31469d552bf046c1511b59e085` |

Allen publishes no upstream checksum, so these locally computed values are the
only identity anchor. Cache `data/nwb_cache/`; covered by `.gitignore:59`
(`*.nwb`). **Zero `.nwb` files are tracked.**

### 4.1 Identity chain

| specimen | `/general/aibs_specimen_id` | `/general/session_id` | inventory `ephys_result_id` | root `identifier` | agrees |
|---|---|---|---|---|---|
| 382982932 | 382982932 | 382982929 | 382982929 | `Allen Institute for Brain Science, Ephys Result 382982929` | **yes** |
| 471129934 | 471129934 | 471129929 | 471129929 | **`P.edit`** | yes on ids; `identifier` unusable |

Identity is established from `aibs_specimen_id` + `session_id` + the download id,
all three of which agree for both files. The root `identifier` of `471129934`
is one of four corrupted strings in that file (§5.3) and is not an identity
anchor.

---

## 5. NWB structure — the two files differ from each other

Neither file is a copy of the Phase 1A/1B layout, and they are not copies of
each other. This was checked per file before running the validator.

### 5.1 Common to both

* NWB **1.0.5**, stored as a **root dataset** `nwb_version` (`b'NWB-1.0.5'`);
  root attributes are empty.
* Series are **groups**: `/stimulus/presentation/Sweep_<n>` and
  `/acquisition/timeseries/Sweep_<n>` contain `data`, `starting_time`
  and the `aibs_*` datasets.
* `unit`, `conversion` and `resolution` live on the **`data` dataset**.
* `/analysis/spike_times/Sweep_<n>` present for **every** series
  (74/74 and 141/141).
* `/general/generated_by` = `pipeline / IVSCC / version / 1.0`.
* Electrode metadata is a constant block (`Bessel filter at 10KHz`); it contains
  **no holding-potential and no holding-current field** in either file.
* `/epochs` holds exactly **3 ×** the series count (222 and 423).

### 5.2 382982932 — full layout, 2017

* `/stimulus/templates` holds **48** template datasets;
  `data_link` present on every sweep (group attribute, e.g.
  `['/stimulus/presentation/Sweep_24', '/stimulus/templates/C1LSCOARSE150216[0]x1']`).
* Per-series metadata: `aibs_stimulus_description` (truncated `|S16`, e.g.
  `C1LSCOARSE150216`), `aibs_stimulus_amplitude_pa`, `aibs_stimulus_interval`,
  `gain`, `seal`, `initial_access_resistance`, `electrode_name`.
* `identifier` and `session_start_time`/`session_description` are intact.
* `file_create_date` = Mon Feb 6 2017.

### 5.3 471129934 — reduced layout, 2018

This is a **third** structural combination, not previously seen in Phase 1:

* `/stimulus/templates` holds **0** datasets; **`data_link` is absent** from all
  141 series.
* `aibs_stimulus_description` and `gain` **do not exist**; `aibs_stimulus_name`,
  `aibs_stimulus_amplitude_pa` and `aibs_stimulus_interval` do.
* Four corrupted string fields: root `identifier` = **`P.edit`**,
  `session_start_time` = **`T`**, `session_description` = **`P`**
  (per-series `description`/`comments`/`source` are empty strings). The same
  `P.edit` string also appears in `583434059` from Phase 1B, so it is an export
  signature rather than a one-off (§6.2).
* `file_create_date` = Mon Apr 2 2018.

So the reduced layout is **not** tied to 50 kHz or to the 6××××××× id block, as
Phase 1B could have suggested: this is a 200 kHz file in the 4××××××× id block
with a reduced layout. **Layout must be detected per file, not inferred from
rate or id.**

### 5.4 Consequence for matching

Phase 1B already had to match on `sweep_number` for the reduced layout. This
batch strengthens the reason:

> In the fine-search block, **all** sweeps share the same template index.
> `382982932` sweeps 44–52 all carry `C1LSFINEST150112[0]`, and
> `471129934` sweeps 53–60 all carry `C1LSFINEST150112[0]`, although their
> amplitudes differ. A template-keyed join would have merged 9 and 8 distinct
> amplitudes into a single key and produced a cartesian product — the exact
> Phase 1A bug.

Sweep-number matching, with a one-to-one assertion, is the only safe key here.
The script's description cross-check therefore reports 48/48-style agreement
only for full-layout files; for `471129934` it has nothing to compare against,
and that is reported rather than treated as a failure.

---

## 6. Stimulus units and conversion

### 6.1 Measured plateau amplitudes

The script locates the dominant non-baseline constant run (no time window, no
maximum-excursion detector) and multiplies the raw sample by the declared
`unit` factor. Results:

| | 382982932 | 471129934 |
|---|---|---|
| `unit` on `data` | `Amps` | `Amps` |
| `conversion` on `data` | **1.0** | **1e-12** |
| `resolution` on `data` | 0.0 (placeholder) | 0.0 (placeholder) |
| `offset` | absent | absent |
| raw sample magnitudes | ≈ 1 × 10⁻¹¹ … 2.7 × 10⁻¹⁰ | ≈ 1 × 10⁻¹¹ … 4.3 × 10⁻¹⁰ |
| raw × 10¹² vs inventory | exact | exact |
| verdict | **MATCH** | **MATCH_CONVERSION_CONFLICT** |

Every raw long-square sample in both files is an **ampere** magnitude; no
inventory value is consistent with the arrays being in pA. This extends the
Phase 1B conclusion to two more specimens and adds a seventh file in which the
raw array is amperes.

### 6.2 The `conversion = 1e-12` defect in `471129934`

NWB 1.x defines `physical = raw × conversion + offset`. Applied literally to
this file, a commanded 90 pA step becomes

```
raw (-9e-11) x conversion (1e-12) = -9e-23 A = -9e-11 pA
```

which is 9 orders of magnitude below the amplifier noise floor and 10¹² times
smaller than the value the file itself declares. **Two witnesses inside the same
file contradict the attribute:**

1. **The file's own `aibs_stimulus_amplitude_pa`.** For all 35 sweeps,
   `raw × 10¹²` equals `aibs_stimulus_amplitude_pa` to **3.3 × 10⁻¹⁵ relative**
   (worst absolute 5.12 × 10⁻¹³ pA). For sweep 26: raw `-9.0000000508e-11`,
   declared `-90.0000005077`. The two agree only if the raw sample is amperes.
2. **The embedded pulse.** Every sweep of every file in this project carries a
   +50 pA pre-step pulse. In `471129934` the pulse sample is `5.0000001e-11`,
   which is 50 pA in amperes — the identical value the attribute would make
   5 × 10⁻²³ A.

The same defect is present on the **acquisition** channel: `unit = Volts` with
`conversion = 0.001`, while the raw response samples are already volts
(≈ −0.068 V ⇒ −68 mV, a plausible resting potential; applying 0.001 would give
−0.068 mV). So this is a **systematic writer defect in this file**, not an
isolated stimulus-channel slip.

For reference, across the **seven** files examined in Phases 1A–1C:

| file | rate | stimulus `unit` | stimulus `conversion` | acquisition `conversion` | `identifier` |
|---|---|---|---|---|---|
| 341442651 | 200 kHz | `Amps` | 1.0 | 1.0 | normal |
| 484635029 | 200 kHz | `Amps` | 1.0 | 1.0 | normal |
| 482516713 | 200 kHz | `Amps` | 1.0 | 1.0 | normal |
| 614777438 | 50 kHz | `A` | 1.0 | 1.0 | hash + `.edit` |
| 583434059 | 50 kHz | `Amps` | 1.0 | 1.0 | **`P.edit`** |
| **382982932** | 200 kHz | `Amps` | **1.0** | **1.0** | normal |
| **471129934** | 200 kHz | `Amps` | **1e-12** | **0.001** | **`P.edit`** |

All seven acquisition channels declare `Volts`, and six of seven declare unity
on **both** channels. `471129934` is the only file in the set where either
channel departs from 1.0 — by 10¹² on the stimulus and 10³ on the voltage.

One thing this table rules out is worth stating. `583434059` shares
`471129934`'s corrupted `identifier` (`P.edit`), so the two most plausibly
passed through the same export step — yet `583434059` declares unity on both
channels. The string corruption and the conversion corruption are therefore
**not** one writer-wide defect predictable from provenance: `471129934` is the
only file here with the conversion problem, and its sibling from the same
export step does not have it. Each file must be checked on its own, which is
precisely why the validator now scores both readings instead of inferring
either from the other attributes.

### 6.3 What is adopted, and why

The adjudication is to **read the samples as being in the declared unit**
(`conversion = 1`), because that is the only reading consistent with the file's
own declared amplitude field and with a protocol constant verified in 236
sweeps of Phase 1B. The alternative — obeying `conversion` — produces a number
that is arithmetically defined but physically impossible.

This is recorded as a **conflict**, not silently resolved: the verdict name is
`MATCH_CONVERSION_CONFLICT`, the specimen exits with status 2, and the report
prints both readings. A Phase 2 consumer that reads this file must use
`conversion = 1` for both channels; one that reads it through a standard NWB
reader will get values 10¹² too small on the stimulus and 10³ too small on the
voltage.

### 6.4 The validator change (the two defects this batch exposed)

`scripts/validate_nwb_stimulus_units.py` was modified once, narrowly, for two
real defects:

1. **Inconsistent conversion rules within one report.** The step was converted
   with `raw × conversion + offset`; the embedded pulse was converted with
   `raw × factor` only. In a file with a non-unity conversion the two numbers in
   the same output used different definitions of "pA". Both now use the same
   rule.
2. **A non-unity `conversion` was silently converted into a data verdict.**
   The script had no way to express "the amplitudes agree but the conversion
   attribute is contradicted". It now scores **both** readings and returns
   `MATCH_CONVERSION_CONFLICT` when only the second agrees, printing the
   spec-rule ratio alongside. It does not fall back silently, and it does not
   report `MATCH` for a file whose conversion attribute is unsafe.

Regression: all five previously validated specimens reproduce their Phase 1B
verdicts exactly — 48, 47, 40, 46 and 55 sweeps, all `MATCH`, exit 0 for those
files. The pulse and step figures for `341442651` are unchanged
(onset 1.0200 s, 1000.00 ms, +50.000 pA at 0.0050–0.0150 s in 48/48).

---

## 7. Step timing, sampling rate, pulse

| | 382982932 | 471129934 |
|---|---|---|
| sampling rate | 200,000 Hz | 200,000 Hz |
| step onset (all sweeps) | 1.0200 s | 1.0200 s |
| step duration | 1000.00 ms | 1000.00 ms |
| plateau samples | 200,000 | 200,000 |
| embedded pulse | **+50.000 pA**, 0.0050–0.0150 s, **29/29** | **+50.000 pA**, 0.0050–0.0150 s, **35/35** |
| pulse samples | 2,001 (10.005 ms) | 2,001 (10.005 ms) |
| extra constant runs per sweep | exactly 1 | exactly 1 |

The pulse is the same protocol constant seen in all seven files: +50 pA,
≈10 ms, starting 5 ms after the trace begins. Nothing about it varies between
the two candidates or against the earlier batch.

The onset was **measured, not assumed**. Both files happen to use 1.02 s, which
is also what the inventory's `stimulus_start_time` says; the script never
hardcodes it.

### 7.1 Sweep trace lengths differ between protocol blocks

| | COARSE sweeps | FINEST sweeps |
|---|---|---|
| trace length | 1,604,001 samples = **8.020 s** | 1,204,001 samples = **6.020 s** |
| step | 1.02 s, 1 s | 1.02 s, 1 s |

The step is identical; only the post-step tail differs. This matters because it
is the fingerprint of two different protocol blocks, which §9.2 shows is not
cosmetic.

---

## 8. Holding potential, spike availability, missing sweeps

### 8.1 Holding potential (derived — no such field exists)

Neither file stores a holding potential or holding current. The only defensible
measure is the **baseline membrane potential**, mean over the pre-step window
(0–1.0 s) of the acquisition trace:

| | 382982932 | 471129934 |
|---|---|---|
| median over long-square sweeps | **−80.55 mV** | **−68.35 mV** |
| range | −81.53 … −79.39 mV | −69.56 … −67.91 mV |
| per-sweep SD of the baseline | 0.44 … 0.52 mV | 0.22 … 0.26 mV |
| drift across the LS block | none visible | none visible |

Both cells are held stably; the **L5 cell sits 12.2 mV more depolarised than
the L2/3 cell**. This is the single largest between-cell difference in the whole
dataset and is developed in §11.

### 8.2 Spike-time availability

| | 382982932 | 471129934 |
|---|---|---|
| `/analysis/spike_times` entries | 74 (every series) | 141 (every series) |
| long-square sweeps with ≥1 spike | **12 of 29** | **12 of 35** |
| total spikes in the LS block | 151 | 42 |
| first spiking amplitude | 130 pA | 290 pA |
| largest response | 32 spikes at 270 pA | 11 spikes at 430 pA |

Spike times are **sweep-referenced**: each dataset runs from 0 to the trace
duration, e.g. `382982932` sweep 38 spans 1.059–5.521 s inside an 8.020 s trace,
and its 28.020 s noise sweep 57 spans 10.150–20.938 s. A consumer must **add the
sweep's own `starting_time`** (768.0 s and 1280.0 s respectively) to place them
on the session timeline; they are not session times and are not comparable
across sweeps without that offset. Both files are internally consistent with
the inventory's `num_spikes` column.

### 8.3 Coverage and missing sweeps

| | 382982932 | 471129934 |
|---|---|---|
| inventory long-square rows | 29 | 35 |
| NWB long-square series | 29 | 35 |
| matched one-to-one on `sweep_number` | **29** | **35** |
| inventory-only (no NWB counterpart) | **none** | **none** |
| NWB-only (no inventory row) | **none** | **none** |

Both are complete. The only inventory/NWB discrepancy in either file is
structural and shared by both: the inventory carries **6 voltage-clamp `Test`
sweeps** (sweep numbers 0–4 plus two late numbers) that have no
`stimulus/presentation` series. All six are 70 ms voltage-clamp test pulses,
not long squares, and do not affect this analysis.

---

## 9. Per-specimen verdict and the one quality finding

### 9.1 382982932 — MATCH

Stimulus units, conversion, offsets, resolution, sampling rate, step timing,
pulse, sweep coverage and identity all verify. The file is internally coherent,
carries the full 2017 layout (48 templates, intact strings), and every
amplitude matches both the inventory and the file's own pA field. No caveat
beyond the usual `resolution = 0.0` placeholder.

### 9.2 471129934 — MATCH_CONVERSION_CONFLICT

Everything above also verifies except the `conversion` attributes (§6.2) and
four corrupted strings (§5.3). Amplitude agreement is stronger than in any
previous file — 5.12 × 10⁻¹³ pA worst case, i.e. float64 round-off — because
the raw samples and the declared pA values are literally the same number
rescaled by 10¹².

### 9.3 A quality finding that affects both, and that neither metadata set reveals

Both cells contain **two protocol blocks with overlapping amplitudes that do not
agree with each other.**

| | 382982932 | 471129934 |
|---|---|---|
| overlapping amplitudes | 130, 150, 170 pA | 290, 310, 330 pA |
| COARSE spikes at overlap | 1, 6, 14 | 1, 1, 2 |
| FINEST spikes at overlap | 0, 0, **1** | 0, 0, **1** |
| FINEST repeats of the top amplitude | 4 × at 170 pA → 1 spike each | 4 × at 330 pA → 1 spike each |

In `382982932`, 170 pA produces **14 spikes** in the coarse sweep (38) and
**1 spike** in each of four fine sweeps (49–52). The commanded current is
identical (`1.7e-10` in both), the step is identical (1.02 s, 1 s), the baseline
Vm is identical (−80.80 vs −80.92 mV) and the steady state is within 0.7 mV
(mean over the last 200 ms of the step: −46.32 mV in sweep 38, −45.90 …
−46.96 mV across sweeps 49–52). Exactly one of the two can be right for the
same cell.

The L5 cell's version is weaker and is deliberately **not** presented as the
same finding. At 330 pA its coarse sweep (47) sits at −43.83 mV over that same
late window against −46.01 … −46.73 mV in the four fine sweeps (57–60), i.e.
**2.3 mV more depolarised**. That can contribute to 2 spikes against 1; it
cannot account for a 14-fold difference. Only the L2/3 case is a genuine
anomaly at matched command and matched Vm.

`access_resistance` and `seal` cannot explain it: both are file-level constants
repeated identically on all 29 and 35 sweeps (12.23 MΩ / 2.34 GΩ and
11.10 MΩ / 2.07 GΩ) and are not per-sweep measurements.

What follows, and what does not:

* The FINEST block is a **separate protocol** (6.020 s traces, one template
  index for every amplitude, repeated sweeps at a single amplitude). It is
  consistent with a threshold-search block appended at the end of the session.
* **It must not be pooled with COARSE to build an F-I curve.** Doing so would
  insert apparent non-monotonicity at three amplitudes in both cells.
* The **cause is not established** by this analysis and is not claimed. A 14-fold
  difference at equal command and equal Vm is a real observation that Phase 2
  must either explain or work around by using the COARSE block alone.

Practical consequence: usable held-out amplitudes are **20 COARSE steps**
(14 depolarising, 6 hyperpolarising) for `382982932` and **27 COARSE steps**
(22 depolarising, 5 hyperpolarising) for `471129934` — still comfortably above
the ≥6 threshold, but 9 and 8 sweeps fewer than the inventory counts imply. The
remaining depolarising amplitudes (3 for L2/3, 2 for L5) exist **only** in the
FINEST block.

---

## 10. The two candidates compared (objective 3)

| dimension | 382982932 (L2/3) | 471129934 (L5) | confound risk |
|---|---|---|---|
| driver line | `Nr5a1-Cre` | `Rbp4-Cre_KL100` | **high** — different pyramidal subpopulations |
| reporter | Ai14 (tdTomato) | Ai14 (tdTomato) | none |
| donor / age / sex | 339692340 / P51 / M | 469953288 / P55 / M | moderate (different animals) |
| dendrite / apical | spiny / intact | spiny / intact | none |
| layer | VISp 2/3 | VISp 5 | intended variable |
| long-square sweeps | 29 (20 COARSE + 9 FINEST) | 35 (27 COARSE + 8 FINEST) | low |
| distinct amplitudes | 23 (17 dep / 6 hyper) | 29 (24 dep / 5 hyper) | low |
| amplitude span | −110 … +270 pA | −110 … +430 pA | moderate |
| missing hyperpolarising step | none (−110 … −10) | **−50 absent** | low |
| sampling rate | 200 kHz | 200 kHz | none |
| trace length | 8.020 s / 6.020 s | 8.020 s / 6.020 s | none |
| **holding Vm (baseline)** | **−80.55 mV** | **−68.35 mV** | **high** |
| spiking sweeps (both blocks) | 12 / 29 | 12 / 35 | — |
| spiking sweeps in COARSE only | 8 / 20 | 8 / 27 | — |
| first spike | 130 pA | 290 pA | high — see below |
| max spikes | 32 (at 270 pA) | 11 (at 430 pA) | high |
| total spikes | 151 | 42 | high |
| session length | 80 sweeps | 147 sweeps | moderate (drift exposure) |
| perisomatic model | 473862496 | 480624414 | — |
| all-active model | 497233292 | 497233049 | — |
| GLIF models | 2 | 5 | irrelevant to this comparison |
| reconstruction | full, 674389884 | dendrite-only, 495335491 | low (the norm, §12.3) |
| NWB layout | full 2017 | reduced 2018 | moderate |
| metadata integrity | clean | 4 corrupted strings + bad conversions | **high** |
| verdict | MATCH | MATCH_CONVERSION_CONFLICT | — |

### 10.1 Interpretation limits

The two cells fire differently by a wide margin: a 2.2× higher rheobase, 3×
fewer spikes in the maximal response and 3.6× fewer spikes overall. **This is not
evidence of a layer effect and must not be reported as one.** At least four
differences co-vary:

1. **Holding potential differs by 12.2 mV.** The L5 cell starts 12 mV closer to
   threshold, which is the wrong direction if anything strengthens the L2/3
   contrast, and a 12 mV shift is easily worth tens of pA of rheobase. Neither
   cell's protocol was normalised to a common Vm.
2. **Genotype differs.** `Nr5a1-Cre` and `Rbp4-Cre_KL100` label different
   excitatory populations; L5 thick-tufted pyramidal cells and L2/3 pyramidal
   cells differ in intrinsic excitability for reasons that have nothing to do
   with being in a layer.
3. **Amplitude ranges differ.** The L5 series reaches 430 pA, the L2/3 series
   stops at 270 pA — and the L2/3 cell is already at 32 spikes there. The two
   F-I curves are sampled over different parts of their own range.
4. **Recording provenance differs.** Different file vintages (created Feb 2017
   and Apr 2018 — the L5 file's own `session_start_time` is corrupted to `T`,
   so its session date cannot be recovered), different layouts, different
   session lengths (80 vs 147 sweeps), and one file with corrupted metadata.

A defensible Phase 2 design must therefore compare **the two models of the same
cell** (perisomatic vs all-active) *within* each specimen, and treat any
L2/3-versus-L5 statement as a two-cell anecdote. The layer comparison is not
identifiable from one cell per layer.

---

## 11. Model readiness (objective 4)

### 11.1 Are the model classes the same?

**Yes, for the two classes that matter.** Both specimens carry exactly one
`Biophysical - perisomatic` and one `Biophysical - all active` model. They also
differ in GLIF coverage (2 vs 5), which is irrelevant to the planned comparison.

Across the whole inventory, all **293** biophysical model rows share
`well_known_file_type_id = 329230374` and exactly two `template_name` values
(`Biophysical - perisomatic`, 189; `Biophysical - all active`, 104). The class
naming and file type are uniform database-wide.

### 11.2 Do the references resolve?

Yes — but they are **not archives.** Each `download_url` returns a
`fit.json` parameter document directly:

| | 382982932 | 471129934 |
|---|---|---|
| perisomatic `model_id` | 473862496 | 480624414 |
| perisomatic descriptor | HTTP 206, **2,891 B**, `application/json` | HTTP 206, **2,892 B**, `application/json` |
| all-active `model_id` | 497233292 | 497233049 |
| all-active descriptor | HTTP 206, **5,738 B**, `application/json` | HTTP 206, **5,736 B**, `application/json` |
| morphology reference | HTTP 206, **335,924 B**, `octet-stream` | HTTP 206, **185,694 B**, `octet-stream` |

`file_path` confirms this: `/external/mousecelltypes/prod312/neuronal_model_473862496/382982932_fit.json`.
The three references that would be needed to actually run a model are therefore
**three separate objects** — fit parameters, morphology, and (not referenced at
all in the inventory) the NEURON template and mechanism library.

### 11.3 Are the templates compatible?

Structurally yes; the fit documents differ in schema between the two classes,
which is expected rather than a problem:

| field | `Biophysical - perisomatic` | `Biophysical - all active` |
|---|---|---|
| top-level keys | `passive`, `fitting`, `conditions`, `genome` | identical |
| `passive` | per-section `cm` list; fitted `ra` (95.89 / 58.05) | `[{"ra": 100}]`, no `cm` |
| `v_init` | = `e_pas` (−94.87 / −83.24) | −90 (both) |
| `genome` values | floats | **strings** |
| `genome` sections | mostly `soma` | `soma`, `axon`, `apic`, `dend` |
| `celsius` | 34.0 | 34 |
| `fitting.junction_potential` | **−14.0 mV** | **−14.0 mV** |

The perisomatic fit is a simplified single-compartment-ish parameterisation
(soma-dominant `genome`, fitted `ra`, per-section `cm`); the all-active fit
distributes passive conductances across `axon`/`apic`/`dend` and stores numbers
as strings. Both are Allen's standard schemas and both reference the same
`well_known_file_type_id`, so one loader with two branches covers them.

### 11.4 Three findings that matter before execution

**(a) The models were fitted to a single suprathreshold sweep, not to the F-I
curve.** `fitting.sweeps` names one sweep per model:

| | perisomatic | all-active |
|---|---|---|
| 382982932 | sweep 38 → **170 pA** | sweep 41 → **230 pA** |
| 471129934 | sweep 51 → **410 pA** | sweep 50 → **390 pA** |
| 341442651 (reference) | sweep 59 | sweep 57 |

All named sweeps fall inside the long-square block of their cell, so they are
among the sweeps validated here. This is good for Phase 2 — the F-I curve is
**held-out data** relative to the fit — but it means the models were never
trained on the full amplitude range and should not be assumed to reproduce the
sub- and supra-threshold extremes equally well.

**(b) A −14.0 mV junction potential is baked into every fit.** All four of these
`fit.json` files, and both of `341442651`'s, declare
`junction_potential = -14.0`. The recorded traces carry no such correction.
Consequently `e_pas` sits 14 mV below the recorded baseline:

| | recorded baseline (median) | minus 14 mV | fitted `e_pas` | residual |
|---|---|---|---|---|
| 382982932 | −80.55 mV | −94.55 mV | −94.87 mV | 0.32 mV |
| 471129934 | −68.35 mV | −82.35 mV | −83.24 mV | 0.89 mV |

The agreement to under 1 mV in both cells shows this is a consistent convention
and not a coincidence. **Any model-versus-data voltage comparison must apply the
same 14 mV offset on one side**, or it will report a systematic 14 mV error that
looks like a model failure.

**(c) NEURON is not available and the mechanism library is not referenced.**
Executing either model requires the NEURON simulator, Allen's biophysical
template and `mod` mechanism files, the morphology and the `fit.json`. The
inventory supplies only the last of these. NEURON is not installed, and
`docs/DATASET_SELECTION_DECISION.md` already records that AllenSDK is unusable in
this environment (it pins `numpy < 1.24`; this environment runs numpy 2.3.x).

### 11.5 Reconstruction-id relationship is normal, not a red flag

`382982932`'s models reference `neuron_reconstruction_id = 491771090` while the
cell record carries `reconstruction_id = 674389884`. This looks alarming but is
**the normal pattern**: across the 201 modelled specimens, the model's
reconstruction id differs from the inventory's in **30 (14.9%)**, including the
Phase 1A reference `341442651` (513557093 vs 657253247). It is not a specific
defect of this candidate.

Likewise, `dendrite-only` is **not** a limitation for modelling: it is the
majority reconstruction type among modelled specimens (160 of 201, against 39
`full`). `471129934`'s morphology is therefore typical, and its reference
resolves to a 185,694 B file.

### 11.6 Model readiness verdict

| question | answer |
|---|---|
| Same model classes? | **Yes** — one perisomatic + one all-active each |
| References resolvable? | **Yes** (HTTP 206/200, exact byte counts) |
| References sufficient to execute? | **No** — they are `fit.json` only |
| Templates compatible enough? | **Yes**, one loader with two schema branches |
| Obvious obstacle before execution? | **Yes, three**: NEURON + mechanism library absent; −14 mV junction potential must be applied consistently; models are single-sweep fits |

**Neither model is claimed executable.** No archive, morphology or simulator was
downloaded or run, so executability is unverified by construction.

---

## 12. What this validates, and what it does not

Justified by this batch:

* The two candidates exist in the database exactly as the feasibility note says,
  and their metadata is internally consistent.
* Both recordings are the cells they claim to be, are complete against the
  inventory, use 200 kHz, and use amperes in the raw stimulus array.
* All 64 long-square sweeps match the inventory exactly in both files.
* The +50 pA, ≈10 ms pre-step pulse is common to both and identical to the five
  earlier files.
* Both carry both biophysical model classes with resolvable parameter
  references, fitted to a single long-square sweep each with a −14 mV junction
  potential.
* `471129934` contains a systematic `conversion`-attribute defect on both the
  stimulus and the acquisition channel.

**Not** justified, and explicitly not claimed:

* Any layer 2/3 versus layer 5 difference in excitability. One cell per layer,
  different genotypes, a 12.2 mV holding difference and different amplitude
  ranges make the comparison unidentifiable (§10.1).
* Any generalisation to the population. These are **two** specimens out of 1,694;
  the `conversion` defect is now known to affect 1 of 7 examined files, and its
  prevalence is unknown. Its existence means every future NWB read must be
  checked, not assumed.
* That either model reproduces the cell. The fits are single-sweep, the
  junction potential has not been applied anywhere yet, and no simulation has
  run.
* Any claim about recording quality beyond what is measured here: no series
  resistance compensation, bridge balance, liquid-junction correction state or
  seal stability over time is recorded per sweep.
* The cause of the COARSE-versus-FINEST discrepancy in §9.3.
* That the FINEST sweeps are unusable in general — only that they are a
  different protocol and must not be pooled with COARSE without explanation.

---

## 13. Recommendation

**`382982932` (VISp L2/3): proceed to Phase 2.** Unconditional from a
validation standpoint. Use the 20 COARSE long-square sweeps (14 depolarising,
−110 … +270 pA); exclude the 9 FINEST sweeps from any F-I construction unless
the block is separately justified.

**`471129934` (VISp L5): proceed to Phase 2, with four mandated conditions.**

1. Read the stimulus channel as amperes with **`conversion = 1`**, not with the
   declared `1e-12`, and the acquisition channel as volts with
   **`conversion = 1`**, not `0.001`. Any standard NWB reader will otherwise be
   wrong by 10¹² and 10³ respectively.
2. Do **not** use `identifier`, `session_start_time` or `session_description`
   from this file; identity comes from `aibs_specimen_id` / `session_id`.
3. Use the 27 COARSE sweeps (22 depolarising, −110 … +430 pA); the hyperpolarising
   series lacks −50 pA. Drop the 8 FINEST sweeps for two reasons of unequal
   weight: they are a separate threshold-search protocol (6.020 s traces, one
   template index for every amplitude) and they duplicate three COARSE
   amplitudes, which is enough on its own to exclude them; the L2/3 cell's
   spike discrepancy is **not** replicated strongly here (§9.3).
4. Record the `conversion` defect in the Phase 2 provenance so it is not
   rediscovered as a bug in the analysis.

Both:

* **Apply the −14 mV junction potential explicitly and identically** to both
  cells before comparing model to data, or the comparison is off by 14 mV.
* **Do not present the two cells as a layer comparison.** Present them as two
  independent specimens, each with its own perisomatic-versus-all-active
  contrast. That contrast is the one this dataset can support.
* Treat `471129934`'s suitability as **conditional**: a single file with four
  corrupted strings and two bad conversion attributes is weaker provenance than
  `382982932`'s clean 2017 file, even though its amplitudes verify more tightly.

Seven NWB files have now been validated across Phases 1A–1C. Reckoned against
the feasibility note, **four** of its ten main-ranking candidates (§5.2 + §5.3)
are among them — `341442651`, `484635029`, `482516713` and `471129934` — joined
by `614777438` and `583434059` from the Phase 1B stratified check. `382982932`
is **not** on the main list at all: it is the §5.5 L2/3 rank 1 candidate from
the spiny-restricted table, which is the list that matters here.

The layer contrast therefore still rests on **one spiny pyramidal cell per
layer**. If Phase 2 needs a genuine second L2/3 cell, that is cheaper than
further model work: only **7** spiny PASS cells exist in L2/3, and only **3**
carry both model classes. The next by coverage after `382982932` is `318808427`
(Nr5a1-Cre, 19 long-square sweeps, 14 distinct depolarising amplitudes, both
classes), then `477127614` (Slc17a6-IRES-Cre, 19 sweeps, 11 amplitudes, both).

---

## 14. Artefacts and reproduction

| artefact | status |
|---|---|
| `scripts/validate_nwb_stimulus_units.py` | modified (§6.4), committed |
| `results/phase1/PYRAMIDAL_CANDIDATE_VALIDATION.md` | this report |
| `data/nwb_cache/382982932.nwb`, `471129934.nwb` | downloaded, **ignored**, untracked |
| scratch downloader, probe, JSON dump | under `tmp/`, ignored, untracked |

Reproduce:

```
python scripts/validate_nwb_stimulus_units.py --specimen 382982932 --specimen 471129934
```

`382982932` exits 0. `471129934` exits **2** by design: its amplitudes agree, but
its `conversion` attribute is contradicted by its own data and requires
adjudication before use.

*No model was downloaded or executed. No Phase 0 file was modified. No cell was
frozen.*

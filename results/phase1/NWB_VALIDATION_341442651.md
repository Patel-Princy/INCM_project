# NWB Validation — Specimen 341442651 (VISp L2/3, Pvalb-IRES-Cre)

**Phase 1A — validate one real NWB recording and resolve the `Amps` / `pA`
stimulus-unit inconsistency.**

| | |
|---|---|
| Specimen | **341442651** |
| Parent instrument | Allen Institute for Brain Science, Cell Types Database |
| NWB file downloaded | `nwb_file_id = 491200479` (one file only) |
| Validation date | Phase 1A |
| Phase 0 reference documents | `results/dataset_inventory/LONG_SQUARE_FEASIBILITY_NOTE.md`, `results/dataset_inventory/DATASET_INVENTORY_REPORT.md` |
| Verdict | **CONDITIONAL — suitable for subsequent analysis, subject to three conditions (§13)** |
| Units question | **Resolved: a labelling defect, not a scaling defect (§9)** |

---

## 1. Scope, and what was deliberately not done

This note reports the validation of **one** recording. Specimen 341442651 is a
provisional test candidate named for this task; it is **not** a frozen project
selection, and nothing here selects or excludes any population.

Deliberately not done, per the task constraints:

* No Allen API inventory run — every metadata number below comes from the
  already-committed Phase 0 CSVs or from the NWB file itself.
* No Phase 0 CSV, manifest, ranking, or report was modified. The manifest
  SHA-256 digests were left untouched (see §12).
* No other recording was downloaded, and no neuronal-model archive was
  downloaded.
* No FitzHugh–Nagumo fit and no neuron model was run.
* No population or cell selection was frozen.

**One environment change was approved by the user during this task:** `h5py`
was not installed, so the NWB file (an HDF5 container) could not be read at
all. With explicit approval, `h5py==3.16.0` (HDF5 2.0.0) was installed. `pynwb`
and `allensdk` were **not** installed; all NWB access below is raw HDF5 via
`h5py`, which matters for §5 (this file is NWB **1.0.5**, which `pynwb` 2.x
cannot open anyway).

---

## 2. Specimen and recording provenance

From `data/metadata/cell_inventory.csv`, row `specimen_id = 341442651`:

| Field | Value |
|---|---|
| `specimen_name` | `Pvalb-IRES-Cre;Ai14-178310.02.01.01` |
| `transgenic_driver_line` | Pvalb-IRES-Cre |
| `transgenic_reporter_line` | Ai14(RCL-tdT) |
| `donor_full_genotype` | `Pvalb-IRES-Cre/wt;Ai14(RCL-tdT)/wt` |
| `donor_id` / `donor_sex` | 329549869 / F |
| `species` | *Mus musculus* |
| `structure_acronym` | VISp2/3 (`cortical_layer = "2/3"`) |
| `dendrite_type` | aspiny |
| `cell_reporter_id` | 491913822 |
| `ephys_result_id` | **341442649** |
| `ephys_sampling_rate` | 200000 |
| `nwb_file_id` | **491200479** |
| `eligibility` (Phase 0) | PASS |
| `n_sweeps_total` / `n_sweeps_current_clamp` | 83 / 77 |
| `n_long_square_cc` / `n_long_square_depolarizing_cc` | 48 / **34** |
| `has_morphology` / `metadata_complete` / `needs_nwb_validation` | True / True / True |
| `n_models_total` | 4 → 2 GLIF, 1 perisomatic biophysical, 1 all-active biophysical |
| `biophysical_model_id` | 480633479 |

(48 long-square current-clamp sweeps of which 34 are depolarising: 27 coarse
positive steps + 7 fine steps. `clamp_mode = current_clamp` and
`stimulus_units = Amps` for all 48 — this specimen is **not** one of the 181
specimens with a null `clamp_mode` discussed in the Phase 0 note.)

Cross-check against the NWB file itself — the identity chain closes exactly:

| NWB field | Value | Matches |
|---|---|---|
| `identifier` | `Allen Institute for Brain Science, Ephys Result 341442649` | `ephys_result_id` |
| `general/session_id` | `341442649` | `ephys_result_id` |
| `general/aibs_specimen_id` | `341442651` | `specimen_id` |
| `general/aibs_specimen_name` | `Pvalb-IRES-Cre;Ai14-178310.02.01.01` | `specimen_name` |
| `general/aibs_cre_line` | `Pvalb-IRES-Cre` | driver line |
| `general/aibs_dendrite_type` | `aspiny` | `dendrite_type` |
| `general/subject/genotype` | `Pvalb-IRES-Cre; Ai14(RCL-tdT)` | genotype |
| `general/subject/sex`, `age` | `F`, `P48` | donor sex |
| `general/institution` | `Allen Institute for Brain Science` | — |
| `general/generated_by` | `pipeline / IVSCC / version 1.0` | — |
| `session_start_time` | `Fri, 20 Feb 2015 15:32:16 GMT` | — |
| `file_create_date` | `Mon Feb 6 17:09:09 2017` | — |

Electrode metadata (`/general/intracellular_ephys/Electrode 1`), identical
across the validated sweeps:

| Field | Value | Unit in file |
|---|---|---|
| `gain` | 0.01 | `Volt/Volt` |
| `seal` | 2.1301894 | **no unit attribute** |
| `initial_access_resistance` | 11.761073 | **no unit attribute** (nominally MΩ) |
| `bias_current` | −2.22 × 10⁻²⁵ (Sweep_24); range −4.97 × 10⁻¹² … +2.01 × 10⁻¹² A over all 77 series | `Amps` |
| `bridge_balance` | 1.2820513 × 10⁷ | `Ohms` |
| `capacitance_compensation` | 2.5002643 × 10⁻¹² | `Farads` |

Note the `bias_current` unit is `Amps` with values at the 10⁻¹² scale — direct
evidence that this file's ampere convention is real and that 10⁻¹²-scale
numbers are picoampere-scale currents (§9).

---

## 3. NWB file identity

| | |
|---|---|
| Download URL | `http://api.brain-map.org/api/v2/well_known_file_download/491200479` |
| HTTP status | 200 |
| `Content-Type` | `application/octet-stream` |
| `Content-Length` / bytes received | **87 791 928** |
| `Last-Modified` (server) | `Tue, 07 Feb 2017 01:24:48 GMT` |
| **SHA-256 (computed locally)** | `02604560436c649a91efdbc962fb08eec66372c152ba99c1b22590ef9d43262a` |
| First 8 bytes | `89 48 44 46 0D 0A 1A 0A` — valid HDF5 signature |
| `nwb_version` | **`NWB-1.0.5`** |
| Published upstream checksum | **none available** — the Allen API does not publish a
checksum or ETag for `well_known_file_download`; the SHA-256 above is the only
identity anchor and any future re-download should be compared against it |

The file is **NWB 1.0.5**, not NWB 2.x. This is decision-relevant: the
`/processing` and `/intervals` groups that NWB 2.x tooling expects are absent,
there is no `units` module, and `nwb_version` is a root dataset. Any downstream
loader must handle the NWB 1.x layout described in §5.

---

## 4. Download method and local cache

Phase 0 **never downloaded** an NWB file — `src/data_audit/allen_inventory.py`
only *resolves* download references (`well_known_files` →
`nwb_download_url`) and records them. There was therefore no existing download
path to reuse, so the project's existing `requests`-based conventions were
reused instead: direct streaming GET, 3 attempts with linear backoff,
incremental SHA-256, and an idempotent skip if the file is already present.

Local cache location, which is **already Git-ignored** and was verified as such
(`git check-ignore -v` → `.gitignore:59:*.nwb`):

```
data/nwb_cache/341442651.nwb        87 791 928 bytes   (raw NWB — never committed)
```

Intermediate per-sweep tables were written into the same directory during the
analysis and deleted afterwards (§14), so `data/nwb_cache/` contains only the
ignored raw file and `git status` stays clean.

No `.gitignore` change was needed: the `*.nwb` rule from the Phase 0
publication already covers this path, and `git status` stayed clean throughout
the download.

---

## 5. NWB structure — where the stimulus actually lives

```
/
├── acquisition/timeseries/Sweep_<n>            (77)  CurrentClampSeries   → response voltage
├── stimulus/
│   ├── presentation/Sweep_<n>                  (77)  CurrentClampStimulusSeries → injected current
│   └── templates/<desc>x<mult>                 (63)  group { data, electrode_name, gain, num_samples }
├── epochs/Experiment_<n>                       (231 objects) links response + stimulus, start/stop
├── analysis/spike_times/Sweep_<n>              (77)  spike times
├── general/                                          subject, electrode, aiBS provenance
└── (no /processing, no /intervals — NWB 1.0.5)
```

Key structural facts, all measured:

* The **acquisition** series holds the response in `Volts`; the **stimulus**
  series holds the injected current in `Amps`. The two are linked by the epoch
  group's attributes: `'response' is '/acquisition/timeseries/Sweep_<n>'` and
  `'stimulus' is '/stimulus/presentation/Sweep_<n>'`.
* Each stimulus series carries
  `@data_link = ['/stimulus/presentation/Sweep_<n>',
  '/stimulus/templates/<desc>x<mult>']`. The **template name is the only place
  the relative-amplitude multiplier survives** — `aibs_stimulus_description`
  is a fixed-width `S16` field and is truncated to e.g. `C1LSCOARSE150217`,
  losing both the index `[i]` and the `x<mult>` suffix.
* **All 77 presentation `data` arrays are byte-identical to their template
  `data` arrays.** The template is a duplicate copy of the waveform, not a
  normalised unit kernel.
* `starting_time` is a scalar in `Seconds` with `@rate = 200000.0`. For the 48
  long-square sweeps it takes only **5 distinct values**
  (768, 1024, 1280, 1536, 1792; counts 2/25/13/5/3). It is therefore **not a
  per-sweep identifier** and must not be used as a sweep key.
* `epochs/Experiment_<n>/stimulus/idx_start = 150000` (= 0.750000 s) and
  `count = 1454001` or `1054001`. `epoch.start_time − starting_time = 0.750000`
  s in **all 48** long-square sweeps. But `count` spans the whole sweep tail
  (5.27 s or 7.27 s), **not** the 1 s step — so the epoch window cannot be used
  directly as the stimulus plateau window.

---

## 6. Relevant series and metadata fields

Uniform across all 77 `stimulus/presentation` series (no exceptions):

| Attribute | Value |
|---|---|
| `data @unit` | `Amps` |
| `data @conversion` | `1.0` |
| `data @resolution` | `0.0` (placeholder — see §11) |
| `data @offset` | **absent** — no offset attribute exists on any series |
| `data dtype` | `float32` |
| `starting_time @rate` | `200000.0` |
| `starting_time @unit` | `Seconds` |
| template `data @unit` / `@conversion` / `@resolution` | `Amps` / `1.0` / `0.0` |
| response `data @unit` / `@conversion` / `@resolution` | `Volts` / `1.0` / `0.0` |
| `num_samples` | 404601 … 6804001 → 2.023 … 34.020 s |

Custom Allen fields on every stimulus series:

| Field | Meaning | Example (Sweep_24) |
|---|---|---|
| **`aibs_stimulus_amplitude_pa`** | nominal step amplitude, **explicitly labelled pA** | `-270.0` |
| `aibs_stimulus_description` | protocol token, truncated `S16` | `C1LSCOARSE150217` |
| `aibs_stimulus_name` | human-readable category | `Long Square` |
| `aibs_stimulus_interval` | inter-stimulus interval (s) | `8.0` / `0.2005` / absent |
| `gain`, `seal`, `initial_access_resistance` | electrode state | §2 |

---

## 7. Sweep-matching methodology

The mapping was established by an **objective key**, then cross-checked three
ways, rather than assumed from the `Sweep_<n>` numbering:

1. Read `/stimulus/presentation/Sweep_<n>@data_link[1]`, take the template
   basename, strip the `x<mult>` suffix → `C1LSCOARSE150217[0]`.
2. Compare that string to `sweep_inventory.csv:stimulus_description` for the
   row with `sweep_number = n`.
3. Compare the stripped `x<mult>` multiplier to
   `sweep_inventory.csv:stimulus_relative_amplitude`.

Results (long-square only):

| Check | Result |
|---|---|
| Inventory long-square rows | 48 |
| NWB `Long Square` series | 48 |
| Same set of sweep numbers (24–71) | **yes, identical** |
| `template base == stimulus_description` | **48 / 48** |
| `x-multiplier == stimulus_relative_amplitude` | **48 / 48** |

The sweep numbering is therefore consistent between the inventory and the NWB
file, *and that consistency was verified rather than presumed*. Note that
`sweep_inventory.csv:sweep_id` (e.g. `396426265`) is the Allen **database**
identifier and has no counterpart in the NWB object names (`Sweep_24`); the
two namespaces must not be conflated.

Coverage reconciliation — the NWB file contains **77** of the **83** inventory
sweep rows:

| Category | Inventory rows | In NWB |
|---|---|---|
| long_square (current clamp) | 48 | 48 |
| short_square (current clamp) | 17 | 17 |
| noise (current clamp) | 6 | 6 |
| ramp (current clamp) | 3 | 3 |
| other (current clamp) | 3 | 3 (`Test` ×1, `Square - 0.5ms Subthreshold` ×2) |
| **other (voltage clamp)** | **6** | **0 — absent** |
| **Total** | **83** | **77** |

The 6 missing sweeps are sweep numbers **0, 1, 2, 3, 83, 84**, all
`clamp_mode = voltage_clamp`. NWB 1.0.5 embeds no voltage-clamp series at all,
so those rows cannot be validated from this file — they are irrelevant to
long-square current-clamp work but the gap should be recorded.

---

## 8. Actual versus inventory stimulus amplitude

Method: for each of the 48 long-square stimulus series, take the raw `float32`
amperes, identify the **dominant non-baseline level** (the 1 s plateau), and
multiply by 10¹² to express it in pA. The three quantities compared are the
measured plateau, the NWB `aibs_stimulus_amplitude_pa` field, and the inventory
`stimulus_absolute_amplitude`.

Representative rows (all 48 agree; the complete 48-row comparison was
recomputed per sweep during validation and the aggregate statistics follow the
table):

| sweep | `stimulus_description` | inventory `stimulus_units` | inventory `stimulus_absolute_amplitude` | measured plateau (pA) | measured plateau (A, raw) | Δ vs inventory (pA) | `aibs_stimulus_amplitude_pa` |
|---|---|---|---|---|---|---|---|
| 24 | `C1LSCOARSE150217[0]` | `Amps` | −269.999995 | −269.999995 | −2.700000 × 10⁻¹⁰ | **4.5 × 10⁻¹³** | −270.000000 |
| 32 | `C1LSCOARSE150217[8]` | `Amps` | −110.000002 | −110.000002 | −1.100000 × 10⁻¹⁰ | 9.9 × 10⁻¹⁴ | −110.000000 |
| 37 | `C1LSCOARSE150217[13]` | `Amps` | −10.000000 | −10.000000 | −1.000000 × 10⁻¹¹ | −1.8 × 10⁻¹⁵ | −10.000000 |
| 38 | `C1LSCOARSE150217[14]` | `Amps` | 10.000000 | 10.000000 | 1.000000 × 10⁻¹¹ | 1.8 × 10⁻¹⁵ | 10.000000 |
| 51 | `C1LSCOARSE150217[27]` | `Amps` | 269.999995 | 269.999995 | 2.700000 × 10⁻¹⁰ | −4.5 × 10⁻¹³ | 270.000000 |
| 64 | `C1LSCOARSE150217[40]` | `Amps` | 529.999988 | 529.999988 | 5.300000 × 10⁻¹⁰ | 4.5 × 10⁻¹³ | 530.000000 |
| 68 | `C1LSFINEST150112[0]` ×3.4 | `Amps` | 340.000000 | 340.000000 | 3.400000 × 10⁻¹⁰ | −4.5 × 10⁻¹³ | 340.000000 |
| 71 | `C1LSFINEST150112[0]` ×3.5 | `Amps` | 350.000001 | 350.000001 | 3.500000 × 10⁻¹⁰ | 2.3 × 10⁻¹³ | 350.000000 |

Aggregate statistics over all 48 sweeps:

| Comparison | Max absolute difference | Notes |
|---|---|---|
| measured plateau vs inventory `stimulus_absolute_amplitude` | **5.12 × 10⁻¹³ pA** | 48/48 agree within 10⁻³ pA; the residual is float64 round-off |
| measured plateau vs NWB `aibs_stimulus_amplitude_pa` | **1.5 × 10⁻⁵ pA** | residual is `float32` rounding of a 10⁻¹⁰-scale number |
| inventory vs NWB `aibs_stimulus_amplitude_pa` | **1.5 × 10⁻⁵ pA** | same cause |

Both independent NWB quantities — the raw array and the explicitly-pA field —
therefore reproduce the inventory number **when the array is expressed in
picoamperes**. There is no multiplicative factor between them.

---

## 9. Unit and scaling conclusion, with evidence

### 9.1 Evidence

| # | Observation | Source |
|---|---|---|
| E1 | The stimulus array is declared `unit = 'Amps'` with `conversion = 1.0`; no `offset` attribute exists. Stored values are therefore **amperes, unscaled and un-offset**. | `/stimulus/presentation/*/data` attrs |
| E2 | The stored `float32` values are of order **10⁻¹⁰** (e.g. `-2.700000e-10` for the −270 step). | measured |
| E3 | The same file carries `aibs_stimulus_amplitude_pa`, explicitly a **picoampere** field, whose values are `-270.0`, `-110.0`, `10.0`, `530.0`, … | `/stimulus/presentation/*/aibs_stimulus_amplitude_pa` |
| E4 | The measured ampere plateau × 10¹² equals `aibs_stimulus_amplitude_pa` to ≤ 1.5 × 10⁻⁵ pA — E2 and E3 are two encodings of one physical current. | measured |
| E5 | The inventory `stimulus_absolute_amplitude` equals the **pA-expressed** value to ≤ 5.12 × 10⁻¹³ pA, i.e. it was populated from a pA quantity, while `stimulus_units` says `Amps`. | measured |
| E6 | The Allen API itself returns the contradictory pair. `data/metadata/api_cache/p2_ephys_sweeps_ref.json` (35 cached sweep records from other specimens) contains **29 rows with `stimulus_units = "Amps"` whose `stimulus_absolute_amplitude` is also pA-scale** (median \|amp\| 500, max 800), alongside 6 `Volts` rows. | Phase 0 API cache |
| E7 | Elsewhere in the same file, `bias_current` is declared `Amps` and holds values such as `2.01 × 10⁻¹² A` — the file's ampere convention is internally consistent, which is what allows E2 to be read as "270 pA" rather than "270 A". | electrode metadata |

`sweep_inventory.csv` column names (`stimulus_units`,
`stimulus_absolute_amplitude`, `stimulus_relative_amplitude`) mirror the Allen
`EphysSweep` field names exactly, so the `Amps` string in the inventory was
copied from E6 and not invented by Phase 0.

### 9.2 Hypothesis test

| Hypothesis | Verdict | Reason |
|---|---|---|
| **Labelling problem** — the values are correct pA numbers under a wrong unit string | **CONFIRMED** | E5 and E6 show the number is a pA value while the label is `Amps`; E1/E4 show the NWB data itself needs no correction |
| **Scaling / conversion problem** — values are amperes and must be multiplied by 10¹² | **REJECTED** | the array is already amperes with `conversion = 1.0`; `measured_A × 10¹² = inventory` exactly (E4). Applying 10¹² *to the inventory number* would make −270 → −2.7 × 10¹⁴ A, absurd and unsupported by any field |
| **Unresolved** | **REJECTED** | the file provides a redundant, explicit pA field and a measurable array; both agree |

### 9.3 Consequence for the project

> **`sweep_inventory.csv:stimulus_absolute_amplitude` is in picoamperes for
> every one of this specimen's 48 long-square sweeps. The accompanying
> `stimulus_units = "Amps"` string is wrong. Do not apply a 10¹² factor, and do
> not trust `stimulus_units` as a unit assertion.**

This is a **labelling defect inherited from Allen metadata**, not an error in
Phase 0's extraction and not a property of the NWB data. The scope established
here is **one specimen, 48 sweeps, plus 29 corroborating API rows from other
specimens**; whether the label is never once *correct* across the 195
`Amps`-labelled specimens listed in the Phase 0 note remains to be shown (§14).

This conclusion does **not** rest on magnitudes looking plausible. It rests on
an explicit unit attribute, an explicit `_pa` field, a measurement of the raw
array, exact numerical agreement with the inventory, and the upstream API
record.

---

## 10. Sampling rate and long-square sweep findings

**Sampling rate.** `200000.0` Hz for all 77 series (`starting_time @rate`),
matching `cell_inventory.csv:ephys_sampling_rate = 200000`. Verified
independently by geometry: the 1 s step contains exactly **200 000** samples,
and `num_samples / rate` reproduces the declared sweep durations
(1 204 001 → 6.020005 s; 1 604 001 → 8.020005 s).

**Long-square sweeps actually present: 48 of 48 inventory rows** (sweep numbers
24–71), no more and no fewer.

| Property | Value |
|---|---|
| Stimulus category (`aibs_stimulus_name`) | `Long Square` |
| Step onset | **1.02 s** after sweep origin — matches `stimulus_start_time = 1.02` exactly |
| Step offset | **2.02 s** |
| Step length | **200 000 samples = 1.000000 s** in all 48 |
| Inventory `stimulus_duration` | `0.999995 s` → 199 999 samples; **1 sample shorter** than measured (5 µs). Trivial, but it is a real 1-sample mismatch, not a rounding of my analysis |
| Baseline between steps | **0.000000 pA** in all 48 — no holding current in the command |
| Protocol families | **41** × `C1LSCOARSE150217[i]` (`i` = 0…40), and **7** × `C1LSFINEST150112[0]` |
| Coarse amplitudes | −270 → +530 pA in 20 pA steps, `x1` multiplier, `relative_amplitude = 1.0` |
| Fine amplitudes | 340, 350, 350, 350, 350, 370, 390 pA with multipliers `x3.4`, `x3.5`, `x3.7`, `x3.9` |
| `relative_amplitude` meaning | for the fine family `absolute_pA = 100 × multiplier` exactly (3.4 → 340). For the coarse family the multiplier is `1` and the amplitude comes from the indexed list. **`relative_amplitude` is not a universal multiplier** and must not be used alone to reconstruct amplitudes |

**Respiratory/usability state of the response channel** (not just "the sweep
exists"):

| Measure | Result |
|---|---|
| Holding potential (median of pre-step 0.5 s) | −82.91 … −81.09 mV (median −82.16 mV) — stable |
| Response range over the 48 sweeps | −97.53 … +10.09 mV |
| Sweeps containing ≥ 1 spike | **14 / 48**, sweeps **57–71** (+390 pA to +530 pA) |
| Spike counts per spiking sweep | 12, 34, 44, 61, 72, 82, 96, 107 (sweeps 57–64); 31, 16, 4, 4, 4, 1 (sweeps 65–67, 69–71) |
| `analysis/spike_times/Sweep_<n>` present | 48 / 48 |
| Sweep 68 (+340 pA) | present but **0 spikes** — an excitability boundary case, not a defect |

**Independent cross-check on the response side.** The inventory's `num_spikes`
column agrees with the NWB spike counts in every single case: it is populated
for exactly the 14 spiking sweeps with exactly matching counts (12, 34, 44, 61,
72, 82, 96, 107, 31, 16, 4, 4, 4, 1), and it is `null` for exactly the 34
zero-spike sweeps. The inventory↔NWB correspondence is therefore confirmed on
two independent axes — stimulus amplitude (§8) and spike count — not just one.

So the file supports a full F–I characterisation from −270 pA to +530 pA with
14 spiking sweeps, a stable ~−82 mV holding potential, and no sweep missing a
spike-time dataset.

---

## 11. Issues that affect scientific usability

1. **Embedded 50 pA / 10 ms test pulse in every sweep.** All 48 long-square
   sweeps contain an additional square pulse of **+50.000001 pA** lasting
   **2001 samples (10.005 ms) at t = 5.000 … 15.005 ms**, i.e. at the very
   start of the sweep, well before the 1.02 s step. Consequence: any
   amplitude detector that simply takes the largest excursion will return
   **50 pA instead of the true step** whenever |step| ≲ 100 pA. This is exactly
   what happened on my first pass — sweeps 33–38, 41 and 42 appeared to
   disagree with the inventory by up to 90 pA until the plateau extraction was
   fixed. Any pipeline must exclude 0–0.1 s from both baseline estimation and
   amplitude detection. (On Sweep_40 the step is also +50 pA, so the pulse and
   step are indistinguishable by value and the two runs merge into 202 001
   samples — a genuine ambiguity resolved only by timing.)
2. **`resolution = 0.0` on every dataset** is a placeholder, not a quantisation
   step. The real precision is `float32`: residuals of ≤ 1.5 × 10⁻⁵ pA are
   consistent with `float32` representation of 10⁻¹⁰-scale amperes. Do not
   interpret `0.0` as "infinitely precise" or as an error.
3. **No `offset` attribute anywhere.** The offset is implicitly zero; this is
   consistent with the measured 0.000000 pA inter-step baseline, but it is an
   absence of metadata rather than an explicit zero.
4. **NWB 1.0.5 legacy layout.** No `/processing`, no `/intervals`, no units
   module, no sweep table. A sweep cannot be located by a standard NWB 2.x
   accessor; it must be found by object name and epoch link.
5. **`aibs_stimulus_description` is truncated to 16 bytes**, dropping the
   `[i]` index and `x<mult>` suffix. The only surviving copy of both is the
   **template object name** in `data_link`. Any loader that reads only the
   description field will silently lose the amplitude identity of all 7 fine
   sweeps.
6. **6 voltage-clamp sweeps (0–3, 83, 84) are absent** from this file. Not a
   problem for long-square work, but it means the file is not a complete mirror
   of the inventory row set.
7. **`starting_time` is not a sweep key** (§5). It has only 5 distinct values
   across the 48 long-square sweeps.
8. **`seal` and `initial_access_resistance` carry no unit attribute.** Values
   (2.13, 11.76) are presumed GΩ/MΩ by Allen convention but that is not
   asserted in the file.
9. **`aibs_stimulus_interval` is inconsistently populated** — `8.0` on some
   series, `0.2005` on others, absent on the long-square sweeps entirely. It is
   not usable as a timing source; use `epoch.start_time` instead.
10. **`bias_current` records the amplifier's compensating current, not the
    biological holding current.** Its magnitude varies per sweep
    (−4.97 × 10⁻¹² … +2.01 × 10⁻¹² A) while the measured holding potential
    stays at ~−82 mV. It must not be subtracted from the command amplitude.

---

## 12. What this file cannot establish

* **Whether the `Amps` label is wrong for *all* 195 `Amps`-labelled specimens.**
  Verified here for 1 specimen / 48 sweeps. The 29 corroborating API rows are
  metadata, not measurements.
* **Whether the 1,333 `pA`-labelled rows are also pA** — those were not
  exercised by this specimen (all 48 of its rows are `Amps`-labelled).
* **Semantics of `stimulus_relative_amplitude` in general.** The rule
  `absolute = 100 × mult` holds for this specimen's fine family and not for its
  coarse family; a second protocol family would be needed to generalise it.
* **The purpose of the 50 pA/10 ms pulse.** It is measured precisely but its
  protocol role (seal/capacitance check) is inferred from context only.
* **Anything about voltage-clamp sweeps** — none present.
* **Model behaviour.** The specimen *does* carry models in Phase 0
  (`n_models_total = 4`: 2 GLIF, `n_biophysical_perisomatic = 1`,
  `n_biophysical_all_active = 1`, `biophysical_model_id = 480633479`), but this
  NWB file contains **no model data whatsoever** — models are distributed in
  separate archives that this task deliberately did not download. The file can
  therefore validate recording usability only; it says nothing about whether
  either model reproduces these sweeps.

No Phase 0 artefact was modified in producing this note: all seven
`.generated_manifest.json` SHA-256 digests still match (0 mismatches), and
`sweep_inventory.csv` / `cell_inventory.csv` were only ever read.

---

## 13. Verdict

> ### CONDITIONAL — this recording is scientifically usable, subject to three conditions.

The specific validation questions of Phase 1A all **pass**:

| Question | Outcome |
|---|---|
| Is the NWB reference resolvable and the file obtainable? | **PASS** — HTTP 200, 87 791 928 bytes, valid HDF5, SHA-256 recorded |
| Do the inventory's long-square rows correspond to real sweeps? | **PASS** — 48/48, matched by verified key, not by numbering assumption |
| Are the actual stimulus amplitudes what the inventory says? | **PASS** — agreement ≤ 5.12 × 10⁻¹³ pA |
| Is the `Amps` / `pA` discrepancy resolved? | **PASS** — a labelling defect, confirmed with measurement (§9) |
| Is the sampling rate as recorded? | **PASS** — 200 kHz, confirmed by sample geometry |
| Is the response channel usable? | **PASS** — stable −82 mV holding, 14/48 spiking, spike times for all 48 |

Status is **CONDITIONAL rather than unconditional PASS** because three
conditions must be met before this file — or any file validated on the same
pattern — is used in analysis:

1. **Treat `stimulus_absolute_amplitude` as picoamperes and ignore
   `stimulus_units`.** The project must adopt this as a written rule (and
   ideally add a derived `stimulus_absolute_amplitude_pA` column in a *new*
   file, never by editing the Phase 0 CSV).
2. **Exclude 0–0.1 s of every sweep** from baseline estimation and from any
   amplitude detector, because of the embedded +50 pA / 10.005 ms pulse.
3. **Keep the validation single-specimen until extended.** One verified
   specimen is not evidence that the label defect, the embedded pulse, or the
   NWB 1.0.5 layout is uniform across the 311 L2/3 and 505 L5 specimens.

It is **not FAIL**: nothing about this recording prevents the planned analysis.
It is **not an unconditional PASS**: the unit label must be overridden
downstream by policy, and a naive loader will misreport amplitudes.

---

## 14. Recommendation for the next validation step

**Next step — targeted NWB validation of amplitude-label coverage across
specimens, not of more sweeps within this specimen.**

The unit question is closed *for this file*, so additional sweeps here add
little. The open risk is that the `Amps` label is not uniformly wrong. Concretely:

1. **Select 4–6 specimens from the Phase 0 `pA`-labelled group** (the 1,333
   rows not exercised here) **plus 4–6 more from the `Amps` group**, spanning
   both layers, and download only their NWB files into `data/nwb_cache/`.
2. For each, repeat §7 (template-keyed matching) and §8 (dominant-level
   plateau) and record the sign and magnitude of
   `measured_pA − stimulus_absolute_amplitude`. The two competing policies to
   discriminate are *"`Amps` rows are pA"* versus *"`pA`-labelled rows are
   pA"*; a 50/50 split in the Phase 0 note makes it possible that the label is
   simply inverted or unreliable in both directions.
3. Explicitly test whether the **embedded pre-sweep pulse** (§11.1) and the
   **`x<mult>` template suffix** are present in other specimens' files. If the
   pulse amplitude or timing varies, the "skip 0–0.1 s" rule must be replaced
   by pulse detection.
4. Only after the label rule is settled should any Phase 1 feature extraction
   (rheobase, F–I slope, sag, adaptation) be written — every one of those
   measures depends on the stimulus being in the correct units.

Two smaller follow-ups worth folding into the same pass: confirm whether the
1-sample mismatch between `stimulus_duration = 0.999995 s` and the measured
200 000-sample step is systematic, and record that the 6 voltage-clamp sweeps
per specimen are never present in NWB 1.0.5 so Phase 1 must not expect them.

---

### Reproduction artefacts

| Artefact | Location | Committed? |
|---|---|---|
| This note | `results/phase1/NWB_VALIDATION_341442651.md` | **yes** |
| Raw NWB, 87 791 928 bytes | `data/nwb_cache/341442651.nwb` | **no** — ignored by `.gitignore:59` (`*.nwb`) |

Per-sweep and per-series intermediate tables were generated in
`data/nwb_cache/` during the validation and then **deleted**, so that no derived
data is committed and the working tree stays clean. They are fully regenerable
from the single NWB file with the method of §7–§8, which needs no Allen API
call:

1. **Sweep identity** — the `Sweep_<n>` object name in
   `/stimulus/presentation/` and `/acquisition/timeseries/`.
2. **Amplitude identity** — `/stimulus/presentation/Sweep_<n>@data_link[1]` →
   template basename (`C1LSCOARSE150217[i]`, `C1LSFINEST150112[0]`) plus the
   `x<mult>` suffix.
3. **Plateau** — the **dominant non-zero level** of the `float32` array, not the
   maximum excursion (a naive maximum fails on any sweep with |step| ≲ 100 pA;
   see §11.1).

Environment used for measurement: Python 3.14.0, `h5py` 3.16.0 (HDF5 2.0.0),
`numpy` 2.3.4, `pandas` 2.3.3, `requests` 2.32.5. `h5py` installed with the
user's explicit approval during this task; `pynwb` and `allensdk` were never
installed.

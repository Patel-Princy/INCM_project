# Phase 2D — Electrophysiology Anomaly and Protocol Consistency Audit

**Repository:** `Patel-Princy/INCM_project`  **Branch:** `ashish-work`
**Specimen:** `382982932` (mouse VISp, L2/3, `Nr5a1-Cre;Ai14-177333.03.01.01`)
**Session:** `382982929`  **NWB:** NWB-1.0.5
**Audit script:** `scripts/audit_electrophysiology_protocols.py`
**Predecessors:** `results/phase1/PYRAMIDAL_CANDIDATE_VALIDATION.md`,
`results/phase1/CROSS_SPECIMEN_UNIT_VALIDATION.md`,
`results/phase2/PHASE2B_GEOMETRY_AND_MANIFEST_AUDIT.md`,
`results/phase2/PHASE2C_PERISOMATIC_EXECUTION_VALIDATION.md`

**Scope statement.** This is a recording and protocol audit. No model was run: no
NEURON, no Allen SDK runner, no FHN, no held-out evaluation, no threshold fitting
and no sweep deselection. No NWB file was downloaded or modified. Every number
below is read out of one already-cached file or measured from its arrays.

**Evidence classes.** The brief requires observed facts to be separated from
interpretation, so every claim below carries one of four labels:

| Label | Meaning |
|---|---|
| **OBSERVED** | Measured directly from the NWB arrays. Reproducible by re-running the script. |
| **SUPPORTED** | A mechanism that the NWB/Allen metadata explicitly records. |
| **HYPOTHESIS** | A plausible explanation that the data neither confirms nor excludes. |
| **UNRESOLVED** | A question the available metadata cannot answer. |

Only OBSERVED and SUPPORTED may drive an eligibility decision. HYPOTHESIS entries
are recorded so they are not silently promoted to facts later.

---

## 1. Executive verdict

**THE COARSE BLOCK IS INTERNALLY CLEAN AND EXTERNALLY CONTRADICTED. IT IS NOT
ELIGIBLE AS A HELD-OUT EVALUATION TARGET, AND THE COARSE AND FINEST BLOCKS MUST
NOT BE POOLED.**

Three findings carry the verdict.

**(a) The discrepancy is a block-level offset, not a sweep-38 anomaly.**
**OBSERVED.** COARSE fires more than any rival block at *every one of the six
command amplitudes it shares with another block* (130, 150, 170, 190, 210,
250 pA) — 6 of 6. At +170 pA the block delivers 12 spikes in a 1 s step against
1 spike in each of four FINEST repeats and 1 spike in a 2000 ms step in a third
block. Sweep 38 is therefore the *most visible symptom* of a systematic offset,
not an isolated bad sweep.

**(b) None of the obvious explanations survives measurement.**
**OBSERVED.** At +170 pA the four FINEST commands are **bit-identical** to sweep
38's: 0 differing samples and `max|Δ| = 0.000e+00 pA` over 1,204,001 samples. The
step onset (1.020000 s), step end (2.020000 s) and duration (1000.000 ms) are
identical. `gain`, `initial_access_resistance` and `seal` are **file-level
constants** across all 74 series (one distinct value each), so they carry no
between-block information. The steady-state depolarisation agrees within
**1.281 mV** on the spike-robust median, and sweep 38 sits at the *most
hyperpolarised* end of that range while firing twelve times as often. The passive
membrane time constant at step offset is **18.56 ms in sweep 38 and 18.66 ms in
sweep 49** (R² 0.9988 / 0.9973) — identical to within 0.5 %. Neither stimulus
delivery, nor steady-state voltage, nor gross passive properties separates the
blocks.

**(c) The two post-stimulus events in sweep 38 are genuine action potentials by
every morphological test applied, and their *origin* is unexplained.**
**OBSERVED.** Allen's own `/analysis/spike_times` contains both events
(5.514020 s and 5.521270 s), and an independent detector finds the same two
excursions. The command current is **exactly 0.000 pA** over 5.400–5.600 s. Each
event has full action-potential morphology: amplitude 108.063 / 109.281 mV, width
at half-max 0.975 / 1.220 ms, a 10–90 % upstroke spanning 97 and 98 samples, and
a maximum slew of 1.625 mV/sample that lies *inside* the 1.7188 mV/sample
envelope of 212 other spikes in the file. They repolarise to a −59.719 mV trough,
far below the −26.531 mV half-max, with a 7.155 ms inter-spike interval. They are
**not** artefacts of the recording, and they are **not** explained by it either.

**Decisions.** Sweep 38 → **ELIGIBLE WITH CAVEATS**. FINEST 49–52 →
**ELIGIBLE**. Remaining COARSE sweeps → **ELIGIBLE WITH CAVEATS**. COARSE block
as a whole → **UNRESOLVED**.

The distinction matters: the twenty COARSE traces pass every sample-integrity
test and form a smooth, monotone F–I curve. What fails is not their quality but
their *adjudicability* — a block that contradicts two other blocks at an
identical command cannot serve as ground truth for a cross-protocol rate
comparison, however clean its individual traces are.

---

## 2. Data and metadata provenance

**OBSERVED.** Every number in this report comes from a single cached file.

| Property | Value |
|---|---|
| Path | `tmp/model_cache/manifest_drafts/perisomatic/382982932.nwb` (git-ignored) |
| Size | 94,207,824 bytes — matches the Phase 1C record |
| SHA-256 | `d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63` |
| NWB version | 1.0.5 (`nwb_version` stored as a root dataset, not an attribute) |
| Session id | `382982929` |
| Specimen id | `382982932` |
| Stimulus / acquisition / spike-time series | 74 / 74 / 74 |

The script re-checks both the byte count and the digest before it measures
anything, and both match the Phase 1C inventory. Nothing was downloaded.

**OBSERVED.** The 74 stimulus series resolve into **11 protocol blocks**. Sweeps
carrying a step of at least 200 ms ("long square") number **44**; sweeps carrying
a 3 ms pulse ("short square") number **16**; the remaining **14** carry metadata
only and are not analysed as traces.

```
block                     n   amp_lo   amp_hi   trace_s   step_ms    start_s
C1LSCOARSE150216         20   -110.0    270.0      8.02      1000 512.0,768.0
C1LSFINEST150112          9    120.0    170.0      6.02      1000 768.0,1024.0
C1NSSEED_1150216          4    394.0    394.0     28.02           1024.0,1280.0
C1NSSEED_2150216          4    400.8    400.8     28.02           1024.0,1280.0
C1RP25PR1S141203          3    800.0    800.0     34.02                512.0
C1SQCAPCHK141203          1   -200.0   -200.0      8.24               1536.0
C1SSCOARSE150112          7    100.0    700.0      2.023               512.0
C1SSFINEST150112          9    650.0    670.0      2.023               512.0
C2NSRMPRH2150216          1    711.8    711.8     42.02               1792.0
C2SQRHELNG150216         15    170.0    290.0     10.02      2000 1536.0,1792.0
EXTPBLWOUT141203          1      0.0      0.0      4.02               2048.0
```

**OBSERVED.** Sampling is 200 kHz throughout (`DT` = 0.005 ms). Every long-square
sweep additionally carries one invariant embedded probe pulse: **+50.000 pA from
5.000 to 15.005 ms**, 2,001 samples. The script identifies that probe *by
identity* rather than by width, because the 3 ms threshold pulses are *shorter*
than the 10 ms probe and a width-based rule misidentifies them as the stimulus.

**OBSERVED — a metadata limitation that shapes the whole audit.** Every
`starting_time_s` is a multiple of 256 s, taking only the values
`512, 768, 1024, 1280, 1536, 1792, 2048` for 74 timed sweeps — **7 distinct
values, with the largest group holding 23 sweeps**. `epochs/*/start_time` carries
the same quantisation, and the resulting epoch windows overlap (consecutive
FINEST epochs 49–52 all overlap). Therefore:

- `starting_time_s` is **not** a per-sweep timestamp and cannot be used to
  recover an inter-sweep interval or a recovery time. **UNRESOLVED**: the
  inter-sweep interval is not in this file.
- `starting_time_s` *is* monotone in sweep number — **0 inversions over 73
  consecutive pairs** — so it does encode acquisition *order* even though it
  does not encode acquisition *time*. This is used in §3 as the only available
  statement about ordering, and it is used only qualitatively.

---

## 3. COARSE versus FINEST comparison

### 3.1 The stimulus is identical, sample for sample

**OBSERVED.** Sweep 38's command was compared with each of sweeps 49–52, sample
by sample, over the full overlap:

```
command 38 vs 49   differing=0   max|diff|=0.000e+00 pA    1,204,001 samples
command 38 vs 50   differing=0   max|diff|=0.000e+00 pA    1,204,001 samples
command 38 vs 51   differing=0   max|diff|=0.000e+00 pA    1,204,001 samples
command 38 vs 52   differing=0   max|diff|=0.000e+00 pA    1,204,001 samples
```

The commands are **bit-identical**, not merely equal in nominal amplitude. The
brief's warning — that identical nominal amplitudes need not mean identical
protocols — was the right thing to test, and for this pair it is discharged: the
current waveforms agree to the last bit.

**OBSERVED.** Everything else that a stimulus generator could vary is also equal:

| field | sweep 38 | sweeps 49–52 | equal? |
|---|---|---|---|
| command level | 170.000000188 pA | 170.000000188 pA | yes |
| step onset | 1.020000 s | 1.020000 s | yes |
| step end | 2.020000 s | 2.020000 s | yes |
| step duration | 1000.000 ms | 1000.000 ms | yes |
| embedded probe | +50.000 pA, 5.000–15.005 ms | identical | yes |
| sampling rate | 200 kHz | 200 kHz | yes |
| `gain` | 0.01 | 0.01 | yes (file constant) |
| `initial_access_resistance` | 12.234692 MΩ | same | yes (file constant) |
| `seal` | 2.33597064 GΩ | same | yes (file constant) |
| `starting_time_s` | 768 | 1024 | **no** |
| trace length | 8.020 s | 6.020 s | **no** |

Two differences remain, and neither is a stimulus difference: a **2 s longer
recording** in sweep 38, and a **different `starting_time` block**.

### 3.2 The steady state is the same, and the difference is not voltage

**OBSERVED.** Level over the final 200 ms of the step. The median is reported
alongside the mean because sweep 38 holds 2 of its 12 spikes inside that window,
which biases the mean upward by roughly 0.2 mV per spike.

| sweep | command | plateau mean mV | plateau **median** mV | spikes in step |
|---|---|---|---|---|
| 38 | 170.000000 | −45.992 | **−47.094** | 12 |
| 49 | 170.000000 | −45.754 | **−45.813** | 1 |
| 50 | 170.000000 | −46.356 | **−46.312** | 1 |
| 51 | 170.000000 | −46.158 | **−45.938** | 1 |
| 52 | 170.000000 | −47.012 | **−47.000** | 1 |

Mean range 1.258 mV; **median range 1.281 mV**. Sweep 38 is at the *most
hyperpolarised* end of that range on the median and fires twelve times as often.
The comparison is therefore conservative: the spike bias pushes sweep 38 up, and
it still does not separate from the others. **"COARSE ended up at a more
excitable potential" is excluded**, at least at the level of the recorded somatic
voltage.

### 3.3 The passive membrane is the same

**OBSERVED.** Single-exponential fit to the decay immediately after the 1 s step
ends at 2.020 s, with the asymptote fixed at the pre-step baseline
(−80.906 mV) and goodness of fit reported:

| sweep | fit window | τ | R² |
|---|---|---|---|
| 38 (COARSE) | 2.0215–2.045 s | **18.56 ms** | 0.9988 |
| 49 (FINEST) | 2.0215–2.045 s | **18.66 ms** | 0.9973 |

A 0.5 % difference. This is the most direct available probe of input
resistance × capacitance at the soma, and it is unchanged between the blocks.
**"COARSE is a leakier/less leaky cell" is excluded.** It also rules out a gross
change in series resistance or capacitance compensation between the blocks.

### 3.4 Latency to the first spike agrees to 64 ms while the rate differs 12-fold

**OBSERVED.** First in-step spike: sweep 38 at **1.060 s**; sweeps 49–52 at
1.124, 1.097, 1.113 and 1.113 s. Spread 64.3 ms, i.e. all five fire within
104 ms of step onset. But the *subsequent* behaviour diverges completely: 38
continues to fire 11 more times at a mean interval of ~81 ms, while 49–52 fall
silent.

This combination is informative. It says the blocks share an *activation*
threshold — the same current, applied to the same resting potential, evokes a
spike at about the same latency — and disagree only about whether firing is
*sustained*. A difference in resting excitability would move the latency too; a
difference in a slow process that accumulates during repetitive firing would not.

### 3.5 The offset is systematic across every shared amplitude

**OBSERVED.** Amplitudes driven by more than one block — six of them — with the
stronger rate first:

| amp pA | block | step s | spikes | rate Hz | sweeps |
|---|---|---|---|---|---|
| 130 | C1LSCOARSE150216 | 1.00 | **1** | 1.00 | [36] |
| 130 | C1LSFINEST150112 | 1.00 | 0 | 0.00 | [45] |
| 150 | C1LSCOARSE150216 | 1.00 | **6** | 6.00 | [37] |
| 150 | C1LSFINEST150112 | 1.00 | 0 | 0.00 | [47] |
| 170 | C1LSCOARSE150216 | 1.00 | **12** | 12.00 | [38] |
| 170 | C1LSFINEST150112 | 1.00 | 1/1/1/1 | 1.00 ×4 | [49, 50, 51, 52] |
| 170 | C2SQRHELNG150216 | 2.00 | 1 | 0.50 | [64] |
| 190 | C1LSCOARSE150216 | 1.00 | **18** | 18.00 | [39] |
| 190 | C2SQRHELNG150216 | 2.00 | 0 | 0.00 | [66] |
| 210 | C1LSCOARSE150216 | 1.00 | **22** | 22.00 | [40] |
| 210 | C2SQRHELNG150216 | 2.00 | 1/1/1/1 | 0.50 ×4 | [68, 69, 70, 71] |
| 250 | C1LSCOARSE150216 | 1.00 | **29** | 29.00 | [42] |
| 250 | C2SQRHELNG150216 | 2.00 | 4/3/2/4 | 2.00/1.50/1.00/2.00 | [72, 73, 74, 75] |

**COARSE is faster at 6 of 6.** The offset is not an artefact of one sweep, and
it is not confined to 170 pA.

Note also that the COARSE F–I curve is **internally smooth and monotone**:
1, 6, 12, 18, 22, 25, 29, 32 for 130 → 270 pA, with 0 spikes at every amplitude
from −110 to +110 pA. There is no erratic step. A single anomalous sweep would
not produce that; a shifted activation curve would.

### 3.6 A third block disagrees with both, and is itself poorly reproducible

**OBSERVED.** `C2SQRHELNG150216` delivers the same +170.000000188 pA level, at
the same 1.020 s onset, but for **2000 ms** instead of 1000 ms, on a 10.020 s
trace. Its F–I curve at 170 pA gives 1 spike (0.5 Hz over the 2 s step), matching
FINEST — but it is **non-monotone**: 170 pA → 1, 190 pA → 0, 200 pA → 0,
210 pA → 1. And its repeats at a single command disagree wildly
(250 pA → 4, 3, 2, 4 spikes; 290 pA → 12, 14, 11, 8).

So the third block agrees with FINEST at 170 pA, which strengthens the case that
COARSE is the outlier — but its own non-monotonicity and 2-fold repeat scatter
mean it cannot arbitrate finely either. It is a useful *corroborating* block and
a weak *quantitative* reference.

### 3.7 A short-pulse control, and the limit of what it proves

**OBSERVED.** The file contains a natural control: a matched pair of **3 ms**
threshold protocols, `C1SSCOARSE150112` (sweeps 8–14) and `C1SSFINEST150112`
(sweeps 15–23). Each is a 2.023 s trace with one 3 ms current pulse.

| block | 3 ms pulse levels and outcome |
|---|---|
| C1SSCOARSE150112 | silent at 100, 200, 300, 400, 500, 600 pA; **fires at 700 pA** |
| C1SSFINEST150112 | silent at 650 pA; **mixed at 660 pA** (1 of 2 repeats fires); **fires at 670 pA** (6 of 6) |

The brackets are 30 pA apart, inside the 100 pA command increment of the COARSE
block. No 3 ms pulse evokes more than one spike in either block. The COARSE
long-steps fire 12 spikes where FINEST fires 1.

**SUPPORTED interpretation, stated narrowly.** The COARSE/FINEST distinction is
not intrinsic to the protocol *families*: when the same two families were used to
measure spike threshold with a brief pulse, they agreed. The 12-versus-1
difference is specific to *sustained* depolarisation.

**The limit of this control, stated explicitly.** These sweeps are numbers 8–23;
the long-square blocks are 24–52. The control therefore characterises
COARSE-versus-FINEST agreement *before* the long steps were acquired, not during
them. It does **not** exclude a state change occurring between sweep 23 and sweep
38. That is why §8 lists run-down as a live hypothesis rather than a dismissed
one.

**OBSERVED.** The 660 pA level is genuinely ambiguous: of two repeats at the same
command, one fires and one does not. The audit records it as `mixed` rather than
folding it into either bracket, because a mixed level bounds a threshold without
resolving it.

### 3.8 What the metadata records about ordering, and what it cannot

**SUPPORTED.** Sweep number and acquisition order coincide: `starting_time_s` is
monotone non-decreasing in sweep number (0 inversions over 73 pairs). The
acquisition sequence is therefore **short-square pair (8–23) → long-square COARSE
(24–43) → long-square FINEST (44–52) → noise protocols → C2 (64–79)**.

**UNRESOLVED.** Nothing in the file records the wall-clock time between sweeps,
the holding current between sweeps, or which amplifier compensation settings were
active in which block. `gain`, `Ra` and `seal` are constants stamped on all 74
series, so they cannot reveal a mid-session change even if one occurred. The file
is silent on the two quantities most likely to explain a state shift — elapsed
time and holding current — and this audit does not invent them.

---

## 4. Sweep 38 late-doublet investigation

### 4.1 Both events are in Allen's own annotation

**OBSERVED.** `/analysis/spike_times/Sweep_38` contains 14 times. Twelve fall
inside the step; two fall after it:

```
annotated post-step times   5.514020 s, 5.521270 s
independent excursion detector (threshold -20 mV)   5.515 s, 5.522 s
```

Two independent paths agree. An independent upward-crossing detector (0 mV
threshold, 1.5 ms refractory) also reproduces Allen's annotated count on **all 44**
long-square sweeps with a worst discrepancy of **0 spikes**, so the detector is
not mis-splitting or merging events elsewhere in the file. The "14 versus 12"
discrepancy that Phase 2C reported is entirely these two events.

### 4.2 The command current is exactly zero, and the baseline is stable

**OBSERVED.**

```
max|I| over 5.400-5.600 s       0.000e+00 pA   (exactly zero, not small)
baseline immediately before      -80.563 mV
median level over the final 0.5 s -80.719 mV
last sample                       -80.688 mV
sweep-38 pre-step baseline        -80.906 mV (sd 0.093)
```

There is **no current command whatsoever** at the time of the events, and no
baseline instability: the trace sits within 0.35 mV of the pre-step baseline
before the first event and returns to within 0.19 mV of it by the end of the
trace, 2.5 s later. **"An unexplained voltage event accompanied by a current
command" is excluded** — there is no command at all. That is the *problem*, not
the explanation.

There is also no pre-event ramp. Sampled every 50 ms from 5.400 s, the trace
reads −80.500, −80.469, −80.594, −80.656, −80.469, −80.563, −80.594 mV, and then
the upstroke begins. The events start abruptly from a flat resting potential
rather than growing out of a slow depolarisation.

### 4.3 Morphology is a full action potential

**OBSERVED.** The correct control for an event that fires from rest is the *first*
spike of every firing sweep in the file, which also fires from rest — 25 spikes
across all three long-square blocks, spanning a 39 mV range of starting
potential. The first three in-step spikes of sweep 38 are a weaker control,
because only the first of them rises from rest; the others start on the preceding
AHP tail, which inflates their measured 10–90 % rise to as much as 2.7 ms without
any change in the spike itself.

| metric | first 3 driven (38) | **late events (38)** |
|---|---|---|
| peak (mV) | 29.125 / 30.656 / 32.000 | **27.500 / 28.750** |
| amplitude above local baseline (mV) | 70.938 / 74.703 / 85.500 | **108.063 / 109.281** |
| width at half-max (ms) | 0.880 / 0.938 / 0.965 | **0.975 / 1.220** |
| rise 10–90 % (ms) | 0.405 / 0.480 / 2.715 | **0.485 / 0.490** |
| max dV/dt (V/s) | 231.250 / 250.000 / 306.250 | **325.000 / 325.000** |
| min dV/dt (V/s) | −118.750 / −100.000 / −93.750 | **−118.750 / −118.750** |
| AHP minimum (mV) | −51.688 / −51.313 / −50.250 | **−75.625 / −77.219** |

Against the 25-spike from-rest population, and again against the six of those
that also started below −70 mV (sweeps 42, 43, 76, 77, 78, 79 — the only genuinely
matched comparators, since a spike launched from −80 mV has a larger Na⁺ driving
force than one launched from −46 mV):

| metric | from-rest population (n=25) | baseline ≤ −70 mV (n=6) | late events | inside? |
|---|---|---|---|---|
| peak (mV) | 28.594 / 30.781 / 33.219 | 30.219 / 30.703 / 31.500 | 27.500 / 28.750 | **NO** (1.1 / 2.7 mV low) |
| amplitude (mV) | 72.156 / 88.563 / 111.719 | 103.344 / 105.016 / 111.719 | 108.063 / 109.281 | **yes** |
| width (ms) | 0.840 / 0.930 / 1.080 | 0.985 / 1.062 / 1.080 | 0.975 / 1.220 | **NO** (one 0.14 ms wide) |
| max dV/dt (V/s) | 206.250 / 287.500 / 343.750 | 287.500 / 296.875 / 325.000 | 325.000 | **at the edge** |

Reading this honestly: the late events' **amplitude is squarely inside** the
matched population, their **slew reaches but does not exceed** the maximum of it,
and their **peak sits 1.09 mV below the population minimum and 2.72 mV below the
matched subgroup's minimum**, while one of the two **widths is 0.14 ms wider**
than any spike in it. These are small deviations, not categorical ones.

The **AHP difference is not a deviation at all** — it is fully explained by the
absence of the command. During a step the membrane repolarises toward the
−46 mV plateau; with no command it repolarises toward the −80.6 mV rest. An AHP
of −76 mV is the *expected* result of a spike fired from rest and must not be
scored against it.

### 4.4 The upstroke is many samples wide, not a discontinuity

**OBSERVED.** For each event the time from 10 % to 90 % of the rising phase spans
**97 and 98 samples** (0.485 and 0.490 ms), and the largest single-sample jump
inside the events is **1.625 mV**. The largest single-sample jump during the step
is 1.531 mV. The largest jump among **212** genuine spikes in the file, with the
two events under test excluded from the pool, corresponds to an envelope of
**1.7188 mV/sample**; the late events sit inside it.

```
reference population (late events excluded)  212 spikes; dV/dt 125.0 / 237.5 / 343.8 V/s
late-event max slew                          1.6250 mV/sample
envelope                                     1.7188 mV/sample   -> PASS
```

A recording discontinuity, an ADC glitch or a dropped-sample interpolation would
produce a *one-sample* stair-step. These events are sampled smoothly across ~100
samples of upstroke, exactly like the genuine spikes they sit between.

### 4.5 Nothing is clipped or saturated

**OBSERVED.**

```
sweep-38 voltage range                    -81.156 .. +32.000 mV
samples above +200 mV                     0
samples below  -95 mV                     0
longest constant run anywhere in the trace  0.095 ms
```

No rail is reached, no flat run of any length appears, and the ADC is
demonstrably not stuck (§5). The peak of +32.000 mV is the file's largest single
value and it occurs during the *step*, at 1.099 s — not during the late events,
whose peaks are 27.500 and 28.750 mV. **"Saturation or clipping" is excluded.**

### 4.6 They are a doublet, not one broadened event

**OBSERVED.**

```
inter-peak trough      -59.719 mV at 5521.170 ms
inter-spike interval    7.155 ms
half-max level         -26.531 mV
```

The membrane repolarises to −59.719 mV — **33.2 mV below the half-maximum level**
— between the two peaks, so these are two distinct action potentials with a
complete repolarisation between them, not one event with a notched peak. The
second spike is triggered from a depolarised level (−59.7 mV) left by the first
spike's afterdepolarisation, which is the signature of a brief burst rather than
of two independent spontaneous spikes.

### 4.7 The recovery after the doublet is slower than the passive membrane

**OBSERVED.** After the second event, the membrane returns to baseline more slowly
than a passive RC decay would predict. A single exponential fitted to
5.526–5.700 s with the asymptote fixed at −80.688 mV gives τ ≈ 38.6 ms with
**R² 0.64** — a poor fit, and a τ that shifts between 38 and 63 ms depending on
the window. Compare the step-off decay of the *same trace*, which is a clean
exponential at τ = 18.56 ms with R² 0.9988.

So the post-doublet recovery is (i) roughly two to three times slower than the
membrane's passive time constant and (ii) not a clean single exponential.

**HYPOTHESIS.** A slow afterburst conductance — a genuine slow AHP, or a decaying
plateau conductance — would produce exactly this: a recovery slower than passive
and not strictly exponential. This is consistent with the events being
physiological.

**HYPOTHESIS (not excluded).** The same slowness could be produced by an
instrumental baseline shift that the recording never resolves back to. The data
cannot distinguish these two, and this audit does not claim it can.

### 4.8 Only sweep 38 shows any post-step event — and that is a real constraint

**OBSERVED.** Across all 44 long-square sweeps, sweep 38 is the **only** one with
any post-step excursion. This is not an artefact of thin coverage: every one of
the 44 sweeps was observed for at least **4.000 s** after its step ended (the
shortest, sweep 44, still has 4.000 s; sweep 38 has **6.000 s**). The
20-sweep post-step overlay of the COARSE block shows 19 smooth passive
relaxations and one doublet.

**Consequence for interpretation.** If these were unrelated spontaneous events,
they would be expected to appear occasionally in *any* sweep with a long
post-step window. They appear in one of 44. Either sweep 38 was in a uniquely
excitable state, or the probability is simply low. **UNRESOLVED**, and the
distinction matters because the first alternative would link the doublet to the
12-versus-1 discrepancy and the second would not.

---

## 5. Recording-quality analysis

**OBSERVED.** Screening across all 44 long-square sweeps (72,976,044 samples).

| test | result |
|---|---|
| NaN / infinite samples | **0** across 44 sweeps |
| repeated consecutive samples | 19,585,784 of 72,976,044 (26.84 %) |
| ADC quantum | **0.031248 mV**, one value for all 44 sweeps |
| smallest noise/quantum ratio | **9.45** |
| distinct sample values per sweep | 165 … 3,591 |
| longest constant run (worst sweep) | **0.325 ms** |
| current-command anomalies | **0** |
| worst baseline sd | 0.295 mV (sweep 79) |
| worst \|baseline drift\| | 0.6044 mV/s (sweep 51) |
| worst baseline span | 2.156 mV (sweep 68) |
| baseline median range | −79.500 … −81.625 mV |
| amplifier rail | none (no sample > +200 mV or < −95 mV anywhere) |

**The 26.84 % "duplicate" rate is quantisation, not data loss.** The ADC resolves
0.031248 mV while the pre-step noise is ~0.09–0.30 mV, giving a smallest
noise-to-quantum ratio of 9.45. Under those conditions roughly a quarter of
consecutive samples land on the same code in a perfectly healthy recording. The
test that distinguishes a *stall* is a long **continuous** run of one code, and
the worst such run anywhere in the file is **0.325 ms** — 15× shorter than the
5 ms that would be needed to fake an action potential. The audit therefore
reports the repeat count without a verdict and asserts the quantisation
relationship explicitly, so the 26.84 % figure cannot be misread as missing data.

**OBSERVED.** No sweep has an abnormal resting potential: the baseline median
spans 2.13 mV across 44 sweeps (−79.500 to −81.625 mV), with per-sweep sd between
0.085 and 0.295 mV, \|drift\| ≤ 0.6044 mV/s, and a worst within-sweep span of
2.156 mV. There is no drift trend with sweep number in either long-square block.

**OBSERVED.** Spike amplitudes and widths are uniform within each block (all 25
from-rest spikes: peak 28.594–33.219 mV, width 0.840–1.080 ms, dV/dt
206.250–343.750 V/s) except for the two sweep-38 late events quantified in §4.3.
No sweep shows an isolated outlier spike *within* its step.

**HYPOTHESIS.** The one quality metric that cannot be checked from this file is
the inter-sweep recovery: with 256 s-quantised timestamps and overlapping epochs,
there is no way to ask whether the COARSE sweeps were acquired with less recovery
than the FINEST ones. This is not a defect of the recording, it is a limitation
of the metadata, and it is carried forward to §8.

---

## 6. Sweep-level eligibility decisions

The rule is applied mechanically so that no sweep can be excused or condemned by
preference. For a single sweep: **EXCLUDE** on a sample-integrity fault
(non-finite samples, a stalled converter run, an amplifier rail); **ELIGIBLE WITH
CAVEATS** when the trace is usable but carries a documented abnormality that
restricts which analyses it can support; **ELIGIBLE** when nothing abnormal was
found. For a block, **cross-block disagreement at the contested amplitude
outranks every other consideration**, because a block that contradicts another
block at an identical command cannot serve as ground truth regardless of how
clean its individual traces are.

### 6.1 Per-sweep verdicts

All 44 long-square sweeps were screened. **No sweep is EXCLUDE**: there is no
sample-integrity fault anywhere in the file.

| sweep | block | amp pA | in-step | post-step | total | verdict |
|---|---|---|---|---|---|---|
| 24–35 | C1LSCOARSE150216 | −110 … 110 | 0 | 0 | 0 | ELIGIBLE |
| 36 | C1LSCOARSE150216 | 130 | 1 | 0 | 1 | ELIGIBLE |
| 37 | C1LSCOARSE150216 | 150 | 6 | 0 | 6 | ELIGIBLE |
| **38** | **C1LSCOARSE150216** | **170** | **12** | **2** | **14** | **ELIGIBLE WITH CAVEATS** |
| 39–43 | C1LSCOARSE150216 | 190 … 270 | 18 … 32 | 0 | 18 … 32 | ELIGIBLE |
| 44–48 | C1LSFINEST150112 | 120 … 160 | 0 | 0 | 0 | ELIGIBLE |
| 49–52 | C1LSFINEST150112 | 170 | 1/1/1/1 | 0 | 1 | ELIGIBLE |
| 64–79 | C2SQRHELNG150216 | 170 … 290 | see §3.6 | 0 | same | ELIGIBLE |

The only per-sweep caveat in the entire file is sweep 38's: *2 spike(s) after the
step ended*.

### 6.2 Block verdicts

| block | n | verdict | reason |
|---|---|---|---|
| `C1LSCOARSE150216` | 20 | **UNRESOLVED** | at +170 pA gives [12] while `C1LSFINEST150112`, `C2SQRHELNG150216` gives [1] |
| `C1LSFINEST150112` | 9 | **ELIGIBLE** | repeats agree (1 repeated amplitude) and +170 pA agrees with `C2SQRHELNG150216` |
| `C2SQRHELNG150216` | 15 | **ELIGIBLE WITH CAVEATS** | repeats at one command disagree: 250 pA → [4, 3, 2, 4]; 290 pA → [12, 14, 11, 8] |

### 6.3 The four decisions the brief asks for

**1. Sweep 38 — ELIGIBLE WITH CAVEATS.**
*2 spike(s) after the step ended.* The trace itself is sound: zero non-finite
samples, no flat run, no rail, baseline sd 0.093 mV, drift 0.0873 mV/s, and 12
in-step spikes that both detectors and Allen's own annotation agree on. The
caveat is specific and bounded: two action potentials occur 3.49 s after the
command ended with the command at exactly 0.000 pA, so any analysis of the
stimulus-free interval must treat them as unexplained. The in-step count of 12 is
*not* itself a per-sweep defect — it is the block-level question in decision 4.
Excluding sweep 38 would not remove the discrepancy; sweeps 36, 37 and 39–43 show
the same offset against FINEST at their shared amplitudes.

**2. FINEST sweeps 49–52 — ELIGIBLE.**
Repeats agree: four independent 1 s steps at an identical command give 1, 1, 1, 1
spikes, and their +170 pA count agrees with the third block. Every trace test
passes (§5). The one thing the block cannot offer is a rate *curve* — it has a
single firing amplitude (170 pA) and is silent at 120–160 pA — so it can support
a threshold and a single rate point, not an F–I slope.

**3. The remaining COARSE sweeps (19 sweeps, 24–43) — ELIGIBLE WITH CAVEATS.**
No per-sweep integrity fault was found in any of them; each is individually
usable. The caveat is not per-trace but per-comparison: this block fires faster
than every rival at every shared amplitude (6 of 6), so these sweeps may be used
*within* the block — for its internal F–I curve, for spike morphology, for
resting properties — but must be set aside from any **cross-protocol** comparison.
That distinction is the substantive point: the sweeps are set aside for one
purpose, not discarded.

**4. The COARSE block as a whole — UNRESOLVED.**
At +170 pA the block gives 12 spikes where `C1LSFINEST150112` and
`C2SQRHELNG150216` both give 1, on bit-identical commands. Nothing in §3–§5
explains it, and the audit does not manufacture an explanation (§8). A block in
this state is **not** a valid held-out evaluation target: a model scored against
it would be scored against a protocol whose own expected output is unknown.

### 6.4 What was deliberately *not* done

Sweep 38 was not discarded, and no sweep was moved or reweighted to improve
agreement with any model. The two post-step spikes are reported as a caveat on
one sweep, not as grounds for removal — precisely because removing them would
erase the clearest evidence that something about this block's state is unusual,
which is the audit's most important finding.

---

## 7. Implications for the F–I curve and held-out evaluation

### 7.1 Three F–I curves, not one

The file supports three mutually inconsistent rate-amplitude relations:

```
C1LSCOARSE150216 (1 s)  -110:0 ... +110:0  130:1  150:6  170:12  190:18
                        210:22  230:25  250:29  270:32          [smooth, monotone]
C1LSFINEST150112 (1 s)  120:0  130:0  140:0  150:0  160:0  170:1/1/1/1
                                                                 [rheobase > 160 pA]
C2SQRHELNG150216 (2 s)  170:1  190:0  200:0  210:1/1/1/1  250:4/3/2/4  290:12/14/11/8
                                                                 [non-monotone, 2x scatter]
```

COARSE's rheobase lies at or below 130 pA; FINEST's is above 160 pA. Because the
COARSE bracket is (110, 130] and the FINEST bracket is (160, 170], the rheobase
shift is bounded at **30 to 60 pA** without either bracket being tightened. On a
1 s step COARSE reaches 32 Hz at 270 pA, while FINEST reaches 1 Hz at 170 pA and
`C2` reaches a 2 Hz-equivalent at 250 pA over its 2 s step.

**Pooling COARSE and FINEST is not scientifically justified, and this audit
declines to do it.** The audit found no property shared by the two blocks that
would license treating them as repeated measurements of one relation: they differ
by a factor of 12 in rate at an identical command, and the three blocks that
agree with each other (FINEST ×4, C2) disagree with COARSE at every amplitude
they share. Pooling would produce an F–I curve whose scatter reflects the
protocol offset rather than the cell.

### 7.2 The choice of block determines the model verdict

**OBSERVED.** In Phase 2C the perisomatic model `473862496` was executed against
sweep 38 and produced **12 spikes, matching the recording's 12**.

**Deduction from that observation.** Because commands 38 and 49 are **bit-identical**
(0 differing samples, §3.1), and NEURON is deterministic given identical input and
identical parameters, the model's output for sweep 49 must equal its output for
sweep 38 — 12 spikes — where the recording contains **1**. The same simulation
that Phase 2C scored as a success on sweep 38 would therefore be a catastrophic
failure on sweep 49, with no change to the model.

This is the single most consequential finding of the audit. The Phase 2C
agreement on sweep 38 is **not evidence that the model is correct**; it is
evidence that the model and the COARSE block happen to sit in the same excitable
regime. Held-out evaluation performed against COARSE sweeps would report success;
the same evaluation performed against FINEST sweeps would report failure. The
protocol must be adjudicated before the model is scored at all.

### 7.3 Consequences for held-out evaluation

1. **Do not use the COARSE block as the held-out target.** Verdict UNRESOLVED
   (§6.3). Scoring against it measures the model's agreement with a protocol
   whose expected output is unknown.
2. **FINEST 49–52 is the defensible held-out reference**, with the caveat that it
   supports four repeats at one amplitude and a threshold, not a rate curve. Its
   four-way agreement (1, 1, 1, 1) is the strongest reproducibility in the file.
3. **`C2SQRHELNG150216` is a corroborating block, not a reference.** It agrees
   with FINEST at 170 pA but is non-monotone between 170 and 210 pA and scatters
   2-fold at 250 and 290 pA.
4. **No held-out evaluation was run in this phase**, as required. Nothing here
   changes any fitted model parameter or any sweep selection used for fitting.
5. **The F–I comparison in future phases must be within-block.** A
   COARSE-versus-model F–I and a FINEST-versus-model F–I are different
   experiments with different expected answers, and must be reported separately.

---

## 8. Remaining uncertainties

**UNRESOLVED — why the COARSE block is more excitable at 170 pA.**
Excluded by measurement: command waveform, onset, duration, sampling rate,
steady-state depolarisation, passive membrane time constant, data integrity,
threshold (short pulses), and the file-level gain/Ra/seal constants. Not excluded
and not decidable from this file:

- **Run-down / state drift between sweeps 23 and 38.** The blocks were acquired in
  sweep order (COARSE 24–43, then FINEST 44–52), and excitability declines along
  that order. **HYPOTHESIS.** It cannot be tested here, because the file records
  neither acquisition time nor holding current, and the short-pulse control that
  could have tested it was acquired *before* the long steps (§3.7).
- **A change in amplifier compensation not captured in the metadata.** `gain`,
  `Ra` and `seal` are constants stamped on all 74 series; they cannot reveal a
  mid-session change. **HYPOTHESIS.** Untestable from this file.
- **A genuinely different ion-channel state** (e.g. neuromodulatory or
  phosphorylation state) that is not a recording artefact at all. **HYPOTHESIS.**
  Indistinguishable here from run-down.
- **Different inter-sweep recovery.** **UNRESOLVED.** Not recoverable: timestamps
  are 256 s-quantised placeholders with 7 distinct values for 74 sweeps, and
  epoch windows overlap.

**UNRESOLVED — the origin of sweep 38's two post-step spikes.**
Established: they are in Allen's annotation; the command is exactly 0.000 pA;
they have full action-potential morphology (amplitude 108–109 mV, width
0.975–1.220 ms, 97–98-sample upstroke); their slew is inside the envelope of 212
other spikes; there is no rail, no flat run, and no baseline instability; they
are a doublet 7.155 ms apart with a −59.719 mV trough between them. Not
established: what depolarised the membrane. **HYPOTHESIS.** A slow intrinsic or
synaptic conductance, supported by a post-doublet recovery that is slower than
the passive τ and not a single exponential. **HYPOTHESIS.** A slow baseline shift
that never resolves; not excluded. No evidence for an acquisition artefact was
found, but "no evidence found" is not the same as "excluded".

**UNRESOLVED — whether the doublet and the 12-versus-1 offset share a cause.**
They coincide in one sweep. Only 1 of 44 sweeps has a post-step event, so the
sample is a single observation and cannot support either a link or its absence.

**UNRESOLVED — the identity and role of `C2SQRHELNG150216`.**
Its prefix differs from the `C1…` blocks and it uses 2000 ms steps. It is treated
as an independent third measurement because it delivers the same command level at
the same onset, but its non-monotone F–I and 2-fold repeat scatter mean it cannot
arbitrate finely.

**Not a limitation, recorded for completeness.** All 74 series carry the identical
embedded +50 pA / 10 ms probe at 5–15 ms, so no sweep is usable for absolute
resting-potential comparison before 15 ms. This affects nothing in this audit,
which uses windows far from the probe.

---

## 9. Reproduction instructions

### 9.1 Requirements

The audit runs in the existing environment; no dependency was added and nothing
outside it was installed. Python 3 with `numpy` (required) and `matplotlib`
(optional — only for figures; the script degrades gracefully without it). The
cached NWB must be present at the path below. Nothing else is downloaded.

### 9.2 Commands

```
# from the repository root
python scripts/audit_electrophysiology_protocols.py \
    --nwb tmp/model_cache/manifest_drafts/perisomatic/382982932.nwb \
    --plots-dir tmp/phase2d_plots \
    --json tmp/phase2d_summary.json
```

Exit status 0 means every check passed. The run prints 60 checks (60 passed,
0 failed) and 37 observations, and writes the figure and JSON outputs below. The
script re-verifies the file size and SHA-256 before measuring, so a substituted or
truncated NWB fails at the first check rather than silently producing different
numbers.

### 9.3 Outputs (all outside Git — `tmp/` is in `.gitignore`)

| Path | Contents |
|---|---|
| `tmp/phase2d_summary.json` | full machine-readable measurements for every section |
| `tmp/phase2d_plots/fi_by_block.png` | F–I for the three long-square blocks |
| `tmp/phase2d_plots/sweep38_vs_finest.png` | sweep 38 versus FINEST 49–52, voltage and command |
| `tmp/phase2d_plots/doublet_zoom.png` | 5.400–5.600 s: voltage and command current |
| `tmp/phase2d_plots/late_vs_driven_shape.png` | late events versus driven spikes, peak-aligned |
| `tmp/phase2d_plots/post_step_all_coarse.png` | post-step window of all 20 COARSE sweeps |

The figures are diagnostic and are not committed; they are regenerated by the
command above. `tmp/phase2d_run.log` holds a captured console transcript when the
run is redirected.

### 9.4 Script structure

| Section | Contents |
|---|---|
| A | provenance, file identity, series counts |
| B | protocol block inventory, block discovery |
| C | COARSE 38 versus FINEST 49–52: commands, onset, plateau, latency, ordering |
| D | the second long-square block at the contested amplitude |
| E | per-sweep spike counts, the implied F–I, shared-amplitude comparison |
| F | short-square control: the 3 ms threshold pair |
| G | sweep 38 late doublet: annotation, morphology, artefact screening |
| H | recording quality across the 44 long-square sweeps |
| I | eligibility: per-sweep, per-block, and the four named decisions |

`--nwb` is required. `--plots-dir` and `--json` are optional; omit `--plots-dir`
to run headless. The script never writes to the NWB.

### 9.5 Test suite

`python -m pytest tests -q` → **96 passed**. The suite covers Phase 0 inventory
and unit checks; it does not cover this audit, which is verified by its own 60
internal checks and 37 observations.

---

## Summary of decisions

| Item | Decision |
|---|---|
| Sweep 38 | **ELIGIBLE WITH CAVEATS** — 2 unexplained post-step spikes at 5.514/5.521 s with the command at exactly 0 pA |
| FINEST sweeps 49–52 | **ELIGIBLE** — four repeats at one command all give 1 spike; every integrity test passes |
| Remaining COARSE sweeps (24–43, 19 sweeps) | **ELIGIBLE WITH CAVEATS** — individually sound, set aside from cross-protocol comparison because the block fires faster at 6 of 6 shared amplitudes |
| COARSE block as a whole | **UNRESOLVED** — 12 spikes versus 1 at a bit-identical +170 pA command, unexplained |
| Pooling COARSE and FINEST | **NOT JUSTIFIED** |
| Held-out evaluation target | FINEST 49–52 only; COARSE excluded until resolved |

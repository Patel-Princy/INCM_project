# Phase 2E — Held-Out FINEST Evaluation of the Perisomatic Model

**Repository:** `Patel-Princy/INCM_project`  **Branch:** `ashish-work`
**Specimen:** `382982932` (mouse VISp, L2/3, `Nr5a1-Cre;Ai14-177333.03.01.01`)
**Model:** perisomatic `473862496`, executed unmodified
**Fitting sweep:** `38` (`C1LSCOARSE150216`)  **Held-out block:** `C1LSFINEST150112`, sweeps `49, 50, 51, 52`
**Command:** +170 pA, 1000 ms, onset 1020 ms, 200 kHz
**Reference stack:** AllenSDK `v2.16.2` (from source), NEURON `8.2.7`
**Predecessors:** `PHASE1_CANDIDATE_VALIDATION.md`, `PHASE2B_GEOMETRY_AND_MANIFEST_AUDIT.md`,
`PHASE2C_PERISOMATIC_EXECUTION_VALIDATION.md`, `PHASE2D_ELECTROPHYSIOLOGY_PROTOCOL_AUDIT.md`
**Evaluation script:** `scripts/evaluate_finest_held_out.py`

---

## 1. Executive verdict

**HELD-OUT PREDICTION MISMATCH.**

The published perisomatic model was executed unchanged against the four held-out
FINEST sweeps and compared with the recordings. **The pipeline is correct and the
prediction is wrong.** Those two findings are reported separately throughout this
document and must not be conflated.

**Pipeline correctness — 107 of 107 checks passed.** Held-out independence was
established from the descriptor, the manifest and the asset digests before
anything was executed. Four independent processes each integrated 1,204,001
samples of a 6.020 s trace, wrote an NWB through AllenSDK's own `runner`, and the
result was read back out of that file. Sixteen of sixteen mechanisms compiled with
zero warnings and zero errors; the −14 mV junction convention was applied at
output only (`written = raw + 14.000 mV` exactly); the sampled data round-tripped
the NWB write path to `3.7e-09 V` (float32 precision); the stimulus array was
unchanged; and every input digest — NWB, descriptor, morphology, marker, manifest,
16 mechanisms — matched its recorded value before and after the run. Nothing was
refitted, recalibrated, or optimised.

**Predictive performance — a categorical mismatch on the quantity that matters
most.** Every held-out recording contains **exactly one** action potential in the
step. The model predicts **twelve**. The mismatch is present in all four sweeps
and is not marginal: the model's first spike arrives at **40.10 ms** after step
onset against observed latencies of **77.0–104.0 ms** (mean 91.7 ms), and the
model continues firing at ~11 Hz for the rest of the step while the recorded cell
sits depolarised at −46 mV in silence. Correlation inside the step is **0.241**
(mean over the four sweeps) and **92.4 %** of the in-step squared error lies within
±10 ms of a spike the model produced.

**What does agree.** The subthreshold and single-spike descriptors are close. The
resting baseline matches to **≤ 0.37 mV** (pre-step RMSE 0.29–0.47 mV); the
depolarised plateau in the last 200 ms of the step matches within **0.86 mV**
(0.41 mV on the mean); and the single action potential that does exist in each
recording is reproduced to within a few millivolts in amplitude and ~0.05 ms in
width
(§6.3). The failure is therefore **not** a DC error, a baseline drift, a units
error, or a rendering artefact of the recording. It is a failure to reproduce
repetitive firing — accommodation — in a cell that is demonstrably depolarised to
the same level the model reaches.

**The one apparent success does not survive scrutiny.** Sweep 38 is the fitting
sweep, and there the spike counts agree at 12 versus 12. That agreement is
count-only and in-sample: on that same sweep the in-step correlation is **0.1422**,
the in-step RMSE is **11.126 mV** (worse than any held-out sweep), and the spike
times are off by a median of **25.7 ms**. Because the FINEST command is
bit-identical to the COARSE command over the 1,204,001-sample common window, the
model emits **bit-identical output for all four held-out sweeps and for sweep 38**
(verified, `0.000e+00 mV`). The "agreement" on sweep 38 and the "mismatch" on
49–52 are therefore **the same single prediction scored against five different
recordings**, two of which happen to contain twelve spikes and four of which
contain one.

**Scope limit that is not resolved here.** Phase 2D established that the COARSE
block has an unresolved excitability offset, and this evaluation does not explain
it. It is possible that the FINEST recordings represent a different physiological
state and that the model is being asked a question outside its fitting
distribution. That possibility is real, it is stated plainly in §9.5, and it
does not upgrade the verdict: a model that returns twelve spikes where the held-out
recording has one is a predictive mismatch, not a successful prediction with
caveats.

---

## 2. Inputs, provenance and hashes

Every input was read from the existing repository cache and the existing Phase 2C
model workspace. **No file was downloaded in this phase.** Each asset's SHA-256 was
recomputed before the run and again after it; all six values are unchanged.

| Asset | SHA-256 | Size |
|---|---|---|
| `382982932_fit.json` (descriptor) | `d24d00aaed5a2a0ecf9752735b62254bba7ab3dc0d3627e61466f95b00a8e38f` | 2 891 B |
| `382982932.nwb` (stimulus + recording) | `d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63` | 94 207 824 B |
| `674389901_382982932_m.swc` (morphology) | `71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c` | 335 924 B |
| `674389910_382982932_m.marker` | `3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925` | 373 B |
| `manifest.json` (Phase 2B draft) | `93ef8ca022cea0b109f536e28da97d7661aaf72c9b54dba71f09db8b761692b0` | 2 983 B |
| 16 `.mod` files | per-file digests matched `tmp/model_cache/assets_2a.json` (§2.2) | — |

The descriptor, morphology, marker and manifest digests are **exactly** the ones
recorded in Phase 2B and Phase 2C. The descriptor digest is asserted against the
Phase 2C constant `d24d00aa…` inside the script rather than merely printed, and the
staged copy is additionally required to be byte-identical to
`tmp/model_cache/models/perisomatic_473862496/382982932_fit.json`.

Because AllenSDK's `prepare_nwb_output` overwrites `model/work/382982932.nwb` on
every execution, the run was performed in a **separate workspace**
(`~/incm_phase2e/model`) staged from the Phase 2C assets. Phase 2C's
`model/work/382982932.nwb` and `results/traces_sweep38.npz` (19 361 729 B) are
untouched and were reused read-only for the sweep-38 comparison in §8.

### 2.1 Sweep metadata as read from the NWB

| Sweep | Block | Template | Multiplier | Rate | Samples | Duration | Amplitude | Onset | Step |
|---|---|---|---|---|---|---|---|---|---|
| 38 | `C1LSCOARSE150216` | `C1LSCOARSE150216[14]` | 1.0 | 200 kHz | 1 604 001 | 8.020 s | 170.000000 pA | 1020 ms | 1000 ms |
| 49 | `C1LSFINEST150112` | `C1LSFINEST150112[0]` | 1.7 | 200 kHz | 1 204 001 | 6.020 s | 170.000000 pA | 1020 ms | 1000 ms |
| 50 | `C1LSFINEST150112` | `C1LSFINEST150112[0]` | 1.7 | 200 kHz | 1 204 001 | 6.020 s | 170.000000 pA | 1020 ms | 1000 ms |
| 51 | `C1LSFINEST150112` | `C1LSFINEST150112[0]` | 1.7 | 200 kHz | 1 204 001 | 6.020 s | 170.000000 pA | 1020 ms | 1000 ms |
| 52 | `C1LSFINEST150112` | `C1LSFINEST150112[0]` | 1.7 | 200 kHz | 1 204 001 | 6.020 s | 170.000000 pA | 1020 ms | 1000 ms |

The COARSE sweep applies a 1.0× multiplier and the FINEST sweeps a 1.7× multiplier,
but the **resulting command is bit-identical**: 0 differing samples and
`max |Δ| = 0.0 pA` across the 1,204,001-sample common window (confirmed again here,
matching Phase 2D §3). Trace length is the one genuine difference — 8.020 s versus
6.020 s — so all cross-sweep work is done over the common window, and the sweep-38
comparison is done over its full 8.020 s.

### 2.2 Mechanisms

Sixteen `.mod` files were digested and matched against `assets_2a.json`, then
recompiled from source in the run workspace: `nrnivmodl` finished in 0.63 s with
0 warnings and 0 errors and produced `libnrnmech.so` at **149 016 B** — the same
size as the Phase 2C build. All 16 mechanisms loaded at run time and the cell
resolved to **59 sections**.

| Mechanism | SHA-256 (first 16 hex) | Mechanism | SHA-256 (first 16 hex) |
|---|---|---|---|
| `CaDynamics` | `f012def9758f7d02` | `Kd` | `1cac92486bf77c29` |
| `Ca_HVA` | `021d34cf9ef3e76b` | `Kv2like` | `9244b0eb301dacee` |
| `Ca_LVA` | `a7a9ef262541dc96` | `Kv3_1` | `e636c3437a9d9ccb` |
| `Ih` | `8616325d83add9a1` | `NaTa` | `fd6af6564b365f5e` |
| `Im` | `e1c3bfb2186439bd` | `NaTs` | `d75ed63d6367fe27` |
| `Im_v2` | `bc378428d3b4da76` | `NaV` | `635605ba861c070f` |
| `K_P` | `2254697617c8da16` | `Nap` | `979d21508f5b089e` |
| `K_T` | `1cb9d72f985ef028` | `SK` | `079f1e3cac744469` |

Recorded at 16 hex digits for legibility; the script compares the full 64-character
digests against `assets_2a.json` and reports a mismatch on any of the sixteen.

The mechanism set is byte-identical to the one Phase 2C compiled and ran.

### 2.3 Descriptor content

The descriptor was parsed and asserted rather than trusted: 4 sections;
`junction_potential = -14.0`; `fitting_sweeps = [38]`; **11 unique fitted
mechanisms in 12 genome entries** on the soma (CaDynamics contributes two,
`gamma_CaDynamics` and `decay_CaDynamics`); and a `sweeps_by_type` family of
`Long Square`. The all-active descriptor for the same specimen carries
`fitting_sweeps = [41]`.

---

## 3. Held-out independence verification

The six claims required before execution were each converted into a check. All
passed. Section A of the run holds **56 checks**, covering all six claims below plus
the per-sweep stimulus and quality assertions.

### 3.1 The fitting descriptor references sweep 38 only

`fitting_sweeps = [38]`, length 1, and the single entry is 38. The descriptor
contains no reference to 49, 50, 51 or 52 — asserted by set intersection rather
than by inspection: `{38} ∩ {49,50,51,52} = ∅`.

### 3.2 Sweeps 49–52 were not used to fit either model

Two independent statements, both checked:

- **Perisomatic `473862496`** — the descriptor's `fitting_sweeps` is `[38]`, so
  none of 49–52 appears in the fitting set.
- **All-active `497233292`** — its descriptor's `fitting_sweeps` is `[41]`, which
  is also disjoint from `{49,50,51,52}`. The all-active model was **not executed**
  in this phase; its descriptor was read only to establish this disjointness.

Noise models and any other model in the specimen were outside scope; the two
named models are the two the brief asks about, and neither saw 49–52.

### 3.3 All four FINEST recordings are eligible per Phase 2D

Eligibility was re-derived from the NWB rather than quoted from the Phase 2D
report, and the re-derivation agrees with Phase 2D §6.1:

| Criterion | Sweep 49 | 50 | 51 | 52 |
|---|---|---|---|---|
| Block is `C1LSFINEST150112` | yes | yes | yes | yes |
| No non-finite samples | 0 | 0 | 0 | 0 |
| Longest flat run ≤ 5 ms | 0.085 ms | 0.085 ms | 0.080 ms | 0.075 ms |
| No rail clipping (±200/−95 mV) | yes | yes | yes | yes |
| Exactly one step, +170 pA | yes | yes | yes | yes |
| Onset 1020 ms, duration 1000 ms | yes | yes | yes | yes |
| Phase 2D decision | ELIGIBLE | ELIGIBLE | ELIGIBLE | ELIGIBLE |

Recording quality metrics, recomputed: 1 204 001 samples each, 1 611–1 724 distinct
values, ADC quantum 0.03125 mV, longest flat run ≤ 0.085 ms, no jumps larger than
1.375 mV, baseline SD 0.104–0.185 mV. These are clean traces by the Phase 2D
criteria.

The COARSE sweep 38 is carried into §8 as context only. Phase 2D classifies it
**ELIGIBLE WITH CAVEATS** because of the post-step doublet at 5514.8/5522.0 ms;
that caveat is honoured — the 12-versus-12 count in §8 is in-step, and the
post-step doublet is reported separately and never pooled with FINEST.

### 3.4 Command waveforms and sampling rates

Sampling rate is 200 000 Hz for all five sweeps (requested and actual), giving
`dt = 0.005 ms`. The four FINEST commands are compared sample-by-sample against
sweep 38 over the common window: **0 differing samples, `max |Δ| = 0.0 pA`**. The
four FINEST commands are additionally identical to each other. Amplitudes agree to
`170.00000018807526 pA` in all five sweeps.

### 3.5 NWB hash and model asset hashes

The initial NWB digest is `d38b43fc…37b63` and the asset digests are as tabulated
in §2. They were recomputed after the run and unchanged, which is a stronger
statement here than usual because the runner writes an NWB: the reason the
digests can be unchanged is that execution happened in a staged copy, and that is
verified rather than assumed.

### 3.6 The model and descriptor are unchanged

The descriptor staged into the run workspace is byte-identical to the cached
published copy, and to the copy Phase 2C used. The morphology, marker, manifest
and 16 mechanisms are likewise byte-identical. **No parameter, morphology,
mechanism, manifest, descriptor or convention was modified at any point in this
phase.**

### 3.7 What could not be established

Nothing. Every independence and provenance claim in the brief was established from
the assets themselves, so the "stop and report" condition was not triggered.

Two honest qualifications, neither of which is an independence failure:

1. **Sweep 38 is a poor fitting target.** Phase 1C flagged it as a recording
   anomaly and Phase 2D gave it a caveat for the post-step doublet. The model is
   therefore fit to a sweep that is not clean, which limits how much its in-sample
   agreement can mean (§8).
2. **Independence of sweeps is not independence of predictions.** Because all four
   held-out commands are bit-identical, the model produces one unique prediction,
   not four (§5.2). The held-out block supplies four *recordings* to compare
   against, but only one *test* of the model.

---

## 4. Execution environment

The isolated Linux environment built for Phase 2C was reused unchanged. AllenSDK
is imported from the repository source tree, so no reinstallation was needed and
no package was downloaded.

| Component | Version | Note |
|---|---|---|
| Python | 3.11.18 | forced by `numpy<1.24`, `pandas==1.5.3`, `scipy<1.11` |
| NEURON | 8.2.7 | substitution, controlled in Phase 2C §3.5 |
| AllenSDK | 2.16.2 | release source tree at `tmp/model_cache/2b/src/AllenSDK-2.16.2` |
| numpy | 1.23.5 | pinned |
| scipy | 1.10.1 | |
| h5py | 3.10.0 | |
| pandas | 1.5.3 | |
| scikit-image | 0.21.0 | |
| matplotlib | 3.7.5 | `Agg` backend; figures only, not used in any metric |
| `libnrnmech.so` | 149 016 B | built from the 16 `.mod` files |

**Environment drift was detected and reverted.** matplotlib is not part of the
Phase 2C environment and the Phase 2C virtual environment has no `pip`, so it was
installed with `uv pip install`. That silently upgraded numpy from 1.23.5 to
1.26.4 — which would have made this phase's numbers non-comparable with Phase 2C
while still producing plausible output. The install was redone with both versions
pinned (`numpy==1.23.5`, `matplotlib==3.7.5`), numpy was confirmed back at 1.23.5,
and the whole evaluation was re-run from scratch. Results were identical and the
identity check against the Phase 2C trace still returned `0.0 mV` (§5.3). The
recorded environment above is the one that produced every number in this report.

---

## 5. Execution and the identity of the four outputs

### 5.1 What was run

The perisomatic model was executed **once per sweep, in four separate processes**,
each starting from a clean interpreter:

```
python scripts/evaluate_finest_held_out.py --child --sweep N \
    --model-dir ~/incm_phase2e/model \
    --allensdk-src <repo>/tmp/model_cache/2b/src/AllenSDK-2.16.2 \
    --child-out ~/incm_phase2e/results/sweep_N
```

Each child calls AllenSDK's own `runner.run({"manifest_file": "manifest.json",
"axon_type": "truncated"}, sweeps=[N], procs=1)` with instrumentation wrapped
around `Utils.setup_iclamp` and `Utils.get_recorded_data`. The wrapper records the
sweep number the runner actually requested, the raw simulator vector, the written
vector, the junction potential in force, both sampling rates, `dt`, `tstop`, and
the IClamp count during the run. Nothing else is modified: no fitted parameter, no
morphology, no mechanism, no junction convention, no optimisation, no FHN, and no
all-active execution.

One process per sweep was chosen because it reproduces the validated Phase 2C code
path exactly, isolates failures to a single sweep, and makes §5.2 a statement about
*independent processes* rather than about one reused object graph. It is not a
claim that a single process would have failed: a separate two-sweep probe was run
and its traces matched single-sweep traces exactly, because `setup_iclamp` rebinds
its own `IClamp` and leaves exactly one in the graph (measured: `iclamp_before_run
= 0`, `iclamp_during_run = 1`).

Per-sweep execution facts:

| Sweep | Elapsed | Sections | Mechanisms | IClamp during run | Samples written | NWB written | Round-trip error |
|---|---|---|---|---|---|---|---|
| 49 | 9.00 s | 59 | 16 | 1 | 1 204 001 | 95 170 041 B | 3.7e-09 V |
| 50 | 9.04 s | 59 | 16 | 1 | 1 204 001 | 95 169 981 B | 3.7e-09 V |
| 51 | 8.92 s | 59 | 16 | 1 | 1 204 001 | 95 170 026 B | 3.7e-09 V |
| 52 | 9.24 s | 59 | 16 | 1 | 1 204 001 | 95 170 007 B | 3.7e-09 V |

The four output NWB files differ in length by up to 60 bytes because HDF5 metadata
is not byte-reproducible. **The sampled data inside them is not affected by that**,
as §5.2 shows.

### 5.2 The script does not assume identity — it measures it

The brief requires the identity of the four outputs to be checked rather than
assumed. It was measured on the sample vectors read back out of the four written
NWB files:

| Comparison | Samples | Max absolute difference |
|---|---|---|
| sweep 50 vs 49 | 1 204 001 | **0.000e+00 mV** |
| sweep 51 vs 49 | 1 204 001 | **0.000e+00 mV** |
| sweep 52 vs 49 | 1 204 001 | **0.000e+00 mV** |
| stored spike times, 49 vs 50/51/52 | 12 events each | identical to the last bit |

The 12 spike times AllenSDK itself detects and stores in the NWB are `1.059535,
1.101485, 1.160330, 1.238395, 1.331265, 1.428975, 1.526490, 1.622595, 1.717210,
1.810505, 1.902685, 1.993935` s — identical in all four files.

**So the four comparisons in §6 are not four independent tests.** They are one
prediction scored against four recordings. This matters for how the result is
read, and it is the reason §7 reports both the per-sweep spread and the fact that
the model-side spread is exactly zero by construction.

That the model is deterministic given a bit-identical command, a fixed initial
condition and no stochastic mechanism is expected; the point of checking was that
it holds here through the full write-and-read-back path, and it does.

### 5.3 The Phase 2C trace is reproduced exactly

The strongest available control on the execution path is Phase 2C's sweep-38 trace,
produced by a different script in a different workspace on an earlier day. Because
the FINEST command equals sweep 38's command over the first 1,204,001 samples, the
sweep-49 output must equal the first 1,204,001 samples of Phase 2C's `v_sim`:

| Comparison | Samples | Max absolute difference |
|---|---|---|
| sweep 49 vs Phase 2C sweep-38 prefix | 1 204 001 of 1 604 001 | **0.000e+00 mV** |

Exact agreement. The Phase 2E execution path is numerically identical to the
validated Phase 2C path.

### 5.4 Conventions verified at run time

| Convention | Expected | Observed |
|---|---|---|
| Junction potential | −14.0 mV, applied at output only | `junction_mv = -14.0` |
| Raw simulator first sample | unshifted | −94.868774 mV |
| Written first sample | raw + 14 mV | −80.868774 mV |
| Shift applied to input? | never | stimulus array unchanged |
| `dt` / `tstop` | 0.005 ms / 6020.0 ms | 0.005 ms / 6020.0 ms |
| Stimulus rate vs simulation rate | both 200 kHz | 200000.0 / 200000.0 |

`written − raw = +14.000000 mV` exactly on the first sample, and
`max |written − captured| = 3.7e-09 V` over the whole trace, which is float32
round-off in the NWB payload rather than a numerical difference.

---

## 6. Predicted versus observed, per held-out sweep

All metrics use the Phase 2C and Phase 2D conventions unchanged: the 0 mV-crossing
detector with a 1.5 ms refractory window, the step defined as 1020–2020 ms, latency
measured from step onset, baseline taken from the pre-step interval, and the
plateau measured over the last 200 ms of the step. The same functions from
`scripts/audit_electrophysiology_protocols.py` are imported rather than
reimplemented, so the detector is literally the Phase 2D detector.

### 6.1 Summary table

| Sweep | In-step spikes (pred/obs) | First latency pred/obs (ms) | Baseline pred/obs (mV) | Pre-step RMSE (mV) | In-step RMSE (mV) | In-step RMSE away from spikes (mV) | Error within ±10 ms of a spike | Whole RMSE (mV) | Corr whole | Corr in-step |
|---|---|---|---|---|---|---|---|---|---|---|
| 49 | **12 / 1** | 40.10 / 104.05 | −80.69 / −80.95 | 0.372 | 8.672 | 2.979 | 91.3 % | 3.629 | 0.9647 | 0.2254 |
| 50 | **12 / 1** | 40.10 / 77.02 | −80.69 / −80.58 | 0.292 | 8.558 | 2.679 | 92.6 % | 3.617 | 0.9660 | 0.2561 |
| 51 | **12 / 1** | 40.10 / 93.18 | −80.69 / −80.51 | 0.313 | 8.648 | 2.709 | 92.7 % | 3.646 | 0.9653 | 0.2451 |
| 52 | **12 / 1** | 40.10 / 92.54 | −80.69 / −81.06 | 0.465 | 8.810 | 2.693 | 93.0 % | 3.675 | 0.9653 | 0.2391 |

Read the whole-trace column with care. It is deceptively good — 3.6 mV and a
correlation of 0.965 — because 5 of the 6.02 s of every trace is a flat baseline
the model gets right. **The whole-trace RMSE conceals the spike-count
disagreement**, which is exactly the failure mode the brief warns about. The
columns that describe the disagreement are the in-step RMSE (8.6–8.8 mV), the
in-step correlation (0.24), and the spike count (12 versus 1).

### 6.2 Per-sweep detail

**Sweep 49.** Predicted 12 spikes in the step, 0 afterwards; observed 1 spike in the
step at **1124.045 ms**, 0 afterwards. First spike 63.95 ms early. Predicted spike
times: 1060.10, 1102.06, 1160.91, 1238.98, 1331.85, 1429.56, 1527.08, 1623.18,
1717.79, 1811.09, 1903.27, 1994.52 ms. Predicted ISIs: 41.96, 58.85, 78.07, 92.88,
97.71, 97.52, 96.11, 94.61, 93.30, 92.18, 91.25 ms (mean 84.95 ms). No observed
ISIs — a single spike has none. Baseline −80.69 predicted against −80.95 observed;
plateau −46.67 against −45.81; minimum −84.16 against −81.34; maximum +37.80
against +30.31.

**Sweep 50.** Same 12 predicted spikes, same times, same ISIs. Observed single spike
at **1097.020 ms** — the earliest of the four — so the latency error is the
smallest, 36.93 ms. Baseline −80.69 vs −80.58; plateau −46.67 vs −46.31; maximum
+37.80 vs +32.31.

**Sweep 51.** Same prediction. Observed single spike at **1113.180 ms**; latency
error 53.09 ms. Baseline −80.69 vs −80.51; plateau −46.67 vs −45.94; maximum
+37.80 vs +31.72.

**Sweep 52.** Same prediction. Observed single spike at **1112.535 ms**; latency
error 52.44 ms. Baseline −80.69 vs −81.06 (the largest baseline offset of the four,
+0.37 mV); plateau −46.67 vs −47.00 (the best plateau agreement); pre-step RMSE
0.465 mV is the largest of the four and still below half a millivolt.

### 6.3 Spike morphology, predicted versus observed

The recorded single spikes:

| Sweep | Time (ms) | Peak (mV) | Amplitude (mV) | Width (ms) | Rise 10–90 % (ms) | Max upstroke (V/s) | AHP (mV) |
|---|---|---|---|---|---|---|---|
| 49 | 1124.045 | 30.31 | 72.94 | 0.875 | 0.410 | 243.75 | −51.91 |
| 50 | 1097.020 | 32.31 | 77.59 | 0.880 | 0.370 | 275.00 | −51.72 |
| 51 | 1113.180 | 31.72 | 75.16 | 0.875 | 0.410 | 262.50 | −51.94 |
| 52 | 1112.535 | 31.75 | 76.78 | 0.870 | 0.415 | 268.75 | −52.47 |

The model's twelve spikes are identical across the four sweeps (as they must be):

| Descriptor | Model, min–max (median) | Recorded range |
|---|---|---|
| Peak | 32.16–37.80 (**32.34**) | 30.31–32.31 |
| Amplitude | 75.61–88.95 (**75.89**) | 72.94–77.59 |
| Width at half-max | 0.915–0.950 (**0.925**) | 0.870–0.880 |
| Rise 10–90 % | 0.810–3.400 (**0.815**) | 0.370–0.415 |
| Maximum upstroke | 323.29–409.16 (**325.12**) | 243.75–268.75 |
| Afterhyperpolarisation | −65.83 to −49.87 (**−50.91**) | −51.72 to −52.47 |

**The single-spike waveform is well matched; the firing pattern is not.** Median
peak differs by 0.03–2.03 mV, median amplitude by 0.7–2.9 mV, width by
0.045–0.055 ms (the model is ~5 % wider), and the AHP by 0.8–1.6 mV (the model's is
shallower). The upstroke is the one clear morphological outlier: the model's median
`dV/dt` is 325 V/s against 244–275 V/s recorded, i.e. 18–33 % faster, which is
consistent with a spike generated by a slightly different conductance mix rather
than a sampling or filtering difference.

The first-spike error *is* visible in the model's own train: the first ISI is
41.96 ms, far shorter than any plausible steady state, and the train then slows to a
~92 ms plateau. That accelerating-then-slowing structure is a genuine model
property, not a detector artefact.

---

## 7. Cross-sweep summary

Before aggregating, one asymmetry has to be stated because it governs how the
summary should be read. **The model's spread across the four repeats is exactly
zero by construction** (§5.2), while the recordings genuinely differ. A "mean over
four" on the model side is therefore an average of four identical numbers; a "mean
over four" on the recording side is an average over four real measurements.

### 7.1 Aggregate over the four held-out sweeps

| Quantity | Mean | SD | Min | Max |
|---|---|---|---|---|
| In-step spikes, recorded | 1 | 0 | 1 | 1 |
| In-step spikes, predicted | 12 | 0 | 12 | 12 |
| First in-step latency, recorded (ms) | 91.695 | 11.117 | 77.020 | 104.045 |
| First in-step latency, predicted (ms) | 40.095 | 0 | 40.095 | 40.095 |
| Baseline offset, predicted − recorded (mV) | +0.085 | 0.268 | −0.178 | +0.366 |
| Pre-step RMSE (mV) | 0.361 | 0.077 | 0.292 | 0.465 |
| In-step RMSE (mV) | 8.672 | 0.104 | 8.558 | 8.810 |
| In-step RMSE away from spikes (mV) | 2.765 | 0.143 | 2.679 | 2.979 |
| Error share within ±10 ms of a spike | 0.9238 | 0.0076 | 0.9127 | 0.9300 |
| Whole-trace RMSE (mV) | 3.642 | 0.025 | 3.617 | 3.675 |
| Whole-trace correlation | 0.9653 | 0.0005 | 0.9647 | 0.9660 |
| In-step correlation | 0.2414 | 0.0128 | 0.2254 | 0.2561 |

### 7.2 How repeatable are the four recordings?

| Quantity | Value |
|---|---|
| RMS difference of each recording from the four-recording mean | 0.893, 0.934, 0.698, 0.830 mV |
| Largest recording-to-recording RMS difference (pairwise) | 1.532 mV |
| Spread of the single spike's time | 27.0 ms (1097.02–1124.05 ms) |
| Spread of the single spike's amplitude | 4.65 mV (72.94–77.59 mV) |
| Baseline SD within a single recording | 0.104–0.185 mV |

The four FINEST recordings are **consistent with each other**. They agree to within
0.93 mV RMS about their common mean at every sample of 1,204,001 samples, and each
contains exactly one full-amplitude spike within a 27 ms window. This is the same
conclusion Phase 2D reached, and it is what makes the block usable as a held-out
target.

### 7.3 How large is the mismatch relative to that repeatability?

Two comparisons, in the two regimes that matter:

- **Away from spikes**, where a smooth disagreement can be measured without
  confounding by spike timing, the model differs from the recordings by
  **2.765 mV RMS** — about **3×** the worst recording-to-recording difference
  (0.934 mV). This is a real model-versus-data discrepancy, not noise.
- **At spikes**, the disagreement is categorical rather than quantitative: 12
  events against 1. No amount of averaging over four repeats can reduce it,
  because all four repeats receive the same prediction.

The four repeats therefore do not act as four votes. They act as one prediction
measured four times against a stable reference, and the measurement is negative
each time. Reporting "3 of 4 sweeps failed" would be misleading in the opposite
direction from the one the brief warns about: the correct statement is that the
single prediction fails against the block.

---

## 8. Sweep 38 beside the FINEST results

### 8.1 The two results side by side

| Quantity | Sweep 38 (fitting, COARSE) | FINEST 49–52 (held out) |
|---|---|---|
| In-step spikes, recorded | **12** | **1, 1, 1, 1** |
| In-step spikes, predicted | **12** | **12, 12, 12, 12** |
| Spike-count delta | 0 | **+11** |
| Post-step spikes, recorded | 2 (5514.81, 5521.96 ms) | 0, 0, 0, 0 |
| Post-step spikes, predicted | 0 | 0 |
| First in-step latency, recorded | 39.75 ms | 77.02–104.05 ms (mean 91.70) |
| First in-step latency, predicted | 40.10 ms | 40.10 ms |
| Latency error | **+0.35 ms** | **−36.9 to −64.0 ms** |
| Whole-trace RMSE | 4.456 mV | 3.642 mV |
| In-step RMSE | **11.126 mV** | 8.672 mV |
| In-step RMSE away from spikes | 3.726 mV | 2.765 mV |
| In-step correlation | **0.1422** | 0.2414 |
| Whole-trace correlation | 0.9314 | 0.9653 |
| Error share within ±10 ms of a spike | 0.9332 | 0.9238 |
| Spike-time offset, median (max) | **25.69 ms (38.08 ms)** | 52.44–63.95 ms (all 12 unmatched) |
| MAE, whole sweep | 1.213 mV | — |
| Baseline offset | +0.137 mV | +0.085 mV mean |
| Plateau, predicted vs recorded | −46.67 vs −47.09 mV | −46.67 vs −46.27 mV mean |
| Share of whole-trace squared error inside the step | 77.8 % | 93.0–95.5 % |

### 8.2 Why sweep 38 produced apparent spike-count agreement

Three reasons, in order of importance.

**1. Sweep 38 is the fitting sweep.** The parameters of `473862496` were fitted on
sweep 38, so reproducing its coarse features is in-sample behaviour by definition.
Spike count over a 1 s step is precisely the kind of aggregate a fitting objective
can lock in. The 12-versus-12 agreement was therefore the expected outcome, and it
carries no information about generalisation.

**2. Even in-sample, the agreement is count-only.** On the fitting sweep itself:
in-step correlation is **0.1422**, in-step RMSE is **11.126 mV** — worse than any of
the four held-out sweeps — spike times are off by a median of **25.69 ms** and up to
**38.08 ms**, and 93.3 % of the in-step squared error sits within ±10 ms of a
spike. The model matched the number of spikes and not their timing, their
waveform, or the intervals between them. The ISI sequence makes this visible:

| ISI index | Recorded (ms) | Model (ms) | Difference |
|---|---|---|---|
| 1 | 39.250 | 41.960 | +2.71 |
| 2 | 59.030 | 58.850 | −0.18 |
| 3 | 79.515 | 78.070 | −1.45 |
| 4 | 75.685 | 92.875 | +17.19 |
| 5 | 80.845 | 97.710 | +16.87 |
| 6 | 114.705 | 97.515 | −17.19 |
| 7 | 79.750 | 96.105 | +16.36 |
| 8 | 92.245 | 94.610 | +2.37 |
| 9 | 95.080 | 93.300 | −1.78 |
| 10 | 94.655 | 92.180 | −2.48 |
| 11 | 85.935 | 91.250 | +5.32 |
| **Mean** | **81.518** | **84.948** | **+3.43** |

The first three intervals agree to within 2.7 ms, and the means agree to within
3.4 ms — the fit captured the early structure of the train. From the fourth
interval onwards the model settles onto a steady ~92–98 ms rhythm while the
recording continues to fluctuate between 75.7 and 114.7 ms. Mean-ISI agreement
(81.5 vs 84.9 ms, reported in Phase 2C) is therefore an average of a partly-right
and partly-wrong sequence, and it hid a 17 ms systematic band error in the middle
of the step.

**3. The model, not the sweep, decides the prediction.** The FINEST command is
bit-identical to sweep 38's command over the common window, so the model's output
for sweeps 49–52 **is** the first 6.02 s of its sweep-38 output — verified as
`0.000e+00 mV` over 1,204,001 samples. "Agreement on 38" and "mismatch on 49–52"
are not two results. They are one prediction, scored against recordings that differ
in how many spikes they contain.

### 8.3 Does the model predict the same response for all four FINEST sweeps?

**Yes, exactly.** All four outputs are bit-identical (§5.2): 1,204,001 samples,
`0.000e+00 mV` maximum difference pairwise, and identical stored spike times in all
four NWB files. The four comparisons in §6 rest on one simulated trace.

### 8.4 Does the model reproduce the FINEST block's one-spike response?

**No.** It predicts twelve spikes in every held-out sweep. The first predicted spike
arrives 36.9–64.0 ms earlier than the recorded one, and the eleven that follow have
no counterpart in any recording.

### 8.5 Where the discrepancy comes from

Ordered by how much of the error each accounts for, with the evidence behind the
ordering:

| Component | Evidence | Weight |
|---|---|---|
| **Spike count** | 12 vs 1; in-step RMSE 8.67 mV against 2.77 mV away from spikes; 92.4 % of in-step squared error within ±10 ms of a spike | **dominant** |
| **Firing pattern / adaptation** | the model holds a ~92 ms ISI plateau; the recorded cell fires once and then stays silent for ~900 ms at −46 mV | large, and it is the same phenomenon as the count error |
| **Spike timing** | latency 40.10 ms against 77.0–104.0 ms; no predicted spike is matched to a recorded one | large, but it is a consequence of the count error |
| **Waveform shape** | amplitude within 2.95 mV, width within 0.055 ms, peak within 2.03 mV; upstroke 18–33 % too fast | modest |
| **Baseline** | pre-step RMSE 0.29–0.47 mV; offset within 0.37 mV; baseline SD of the recordings themselves is 0.10–0.19 mV | negligible |

The baseline and plateau columns are worth dwelling on because they exclude the
easy explanations. The predicted plateau is −46.67 mV and the recorded plateaus are
−45.81, −46.31, −45.94 and −47.00 mV — mean −46.27 mV. **The model sits 0.41 mV
more hyperpolarised than the mean recording and yet fires twelve times as often.**
A DC-offset or input-resistance error would move both quantities together; it
cannot produce "same voltage, twelve times the firing". The disagreement is in the
spike-generating dynamics and in whatever terminates the recorded cell's firing,
not in how far the membrane is driven.

---

## 9. Scientific interpretation

### 9.1 Pipeline reproducibility — established

107 of 107 checks passed, and the checks are of the kind that would fail loudly if
something were wrong: asset digests asserted rather than printed, junction
convention verified as an exact 14.000 mV shift on the first sample and to 3.7e-09 V
over the whole trace, stimulus array verified unmodified, mechanism set recompiled
(0 warnings, 0 errors) and all 16 loaded, four independent processes each writing and
reading back an NWB, and output identity measured rather than assumed.

The strongest single piece of evidence is that the sweep-49 output reproduces Phase
2C's sweep-38 prefix **exactly** — `0.000e+00 mV` over 1,204,001 samples — from a
different script, a different workspace, a different day, and a matplotlib/numpy
installation event that had to be reverted (§4). Two independently written scripts
that agree to the last bit on the same model and command are not agreeing by luck.

**Conclusion: the execution pipeline is reproducible, and every number in this
report is a faithful reading of what the model actually computed.**

### 9.2 Prediction on the held-out FINEST recordings — failed

The model predicts **12** action potentials where each of the four held-out
recordings contains **1**, places its first spike **51.6 ms** too early on average,
and produces a train that correlates with the recording at **0.241** inside the
step. 92.4 % of its in-step squared error is concentrated within ±10 ms of spikes it
invented.

This is a **predictive mismatch**, and the brief's phrasing is the correct
description of it: the model executed correctly and predicts 12 spikes where the
held-out recording has one.

What the same run shows the model getting right is worth stating precisely, because
it constrains any interpretation: resting baseline to ≤ 0.37 mV, plateau to ≤
0.86 mV, single-spike peak to ≤ 2.03 mV, amplitude to ≤ 2.95 mV, width to ≤
0.055 ms, and AHP to ≤ 1.6 mV. The passive and steady-state properties and the
shape of an individual action potential are largely correct. Repetitive firing is
not.

### 9.3 Cross-protocol generalisation — not demonstrated

The model does not generalise from the COARSE fitting sweep to the FINEST block. It
has exactly one behaviour for this command, and it produces that behaviour
identically in all four held-out trials because the command is identical.

Stated carefully: **the evaluation cannot separate "the model is generically wrong
about this cell" from "the model is right about the COARSE state and the FINEST
block is a different state".** What it can say is that in the form in which the
model is published, and for the command the brief specifies, its prediction for the
FINEST block is wrong in a way that no re-analysis of the comparison removes. There
is no threshold, alignment, smoothing or metric choice that converts 12 spikes into
1.

One observation is worth recording because it constrains future explanations, and
it is presented as an observation, not a mechanism:

> The FINEST recordings reach a **more depolarised** plateau (−46.27 mV mean) than
> the COARSE fitting sweep (−47.09 mV) and fire **twelve times less**. Across the
> two blocks the resting baseline is essentially unchanged (−80.5 to −81.1 mV).
> Whatever differs between the blocks therefore does not appear as a shift in
> resting potential or in steady-state depolarisation; it appears as a change in
> the cell's ability to sustain repetitive firing.

**This is not an explanation, and no mechanism is claimed.** Phase 2D left the
COARSE block's excitability offset unresolved, and nothing in this phase resolves
it. The observation above only tells us which *class* of hypothesis the data are
compatible with — adaptation or spike-threshold changes rather than DC gains — and
identifying which one would require evidence this NWB does not contain.

### 9.4 Biological validity — not established

The model is not a validated predictor for this specimen's FINEST sweeps. Two
things follow, and they point in opposite directions from each other, so both are
recorded:

- **In its favour**, the steady-state voltage levels and single-spike morphology are
  close enough that the reconstruction is not obviously wrong about passive
  properties, leak, or spike shape.
- **Against it**, the model reproduces none of the accommodation that allows the
  recorded cell to sit at −46 mV without firing. Since the model was fitted on a
  sweep that fires twelve times, and never saw a FINEST sweep, this is a genuine
  extrapolation failure rather than a fitting artefact.

The model was **not** modified to improve this result, and no parameter was
re-estimated. Any statement that the model "would do better if" something were
tuned is out of scope here by instruction and is not made.

### 9.5 The limits imposed by the unresolved physiological state difference

These limits are real and they bound the claims of this report.

1. **The fitting target is itself compromised.** Sweep 38 is flagged by Phase 1C as
   a recording anomaly and by Phase 2D as ELIGIBLE WITH CAVEATS, for a post-step
   doublet at 5514.81/5521.96 ms that no model without a spontaneous-event
   mechanism would produce. This phase's model produces 0 post-step spikes, so if
   the doublet is included the count on sweep 38 is 14 versus 12, not 12 versus 12.
   The in-step-only convention used throughout §8 is the favourable reading.
2. **The block difference is unresolved.** If the FINEST block represents a
   different physiological state — drift, injury, recording order, or a state the
   experiment did not document — then part of the 12-versus-1 mismatch is
   out-of-domain error rather than model error. This evaluation cannot quantify
   that fraction, and does not try.
3. **One amplitude, one cell, one fitting sweep.** No generalisation claim about
   the model, the cell class, or the reconstruction pipeline is supportable from
   this design, in either direction.
4. **The prediction is singular.** With bit-identical commands the four held-out
   sweeps yield one prediction. The effective sample size for the prediction is 1,
   so no confidence interval, no fraction-of-sweeps-agreeing, and no significance
   test is meaningful on the model side.
5. **COARSE and FINEST are never pooled.** Every number in §6 and §7 is FINEST-only;
   every number in §8's first column is sweep-38-only. Phase 2D's instruction is
   followed literally.

None of these limits changes the verdict. They change what the verdict means: the
model fails as a *predictor for this block*, and the report does not claim it fails
as a *description of the COARSE state*.

---

## 10. Figures

All four figures are saved **outside Git tracking**, in `~/incm_phase2e/figures`
inside the Linux environment, with working copies under the repository's ignored
`tmp/phase2e_figures/`. None is staged or committed.

| Figure | What it shows |
|---|---|
| `step_window.png` | 1000–2150 ms. The one model trace (black) overlaid on the four recordings, which coincide. The model's spike train runs through a recording that contains a single spike. |
| `first_spike_shape.png` | A 24 ms window around the first action potential, aligned on peak. Recorded sweep 49 against the model's first spike — the closest agreement in the whole comparison, and the reason the failure is localised to count rather than shape. |
| `full_window.png` | The whole 6.020 s common window, including the post-step interval. Shows that the disagreement is confined to the step: outside it the model and all four recordings lie on top of each other. |
| `error_budget.png` | In-step RMS error split into "within 10 ms of a spike" and "away from every spike", for sweeps 49, 50, 51, 52 and, for reference, sweep 38. Makes the geometric dominance of the spike-related term visible. |

Reproduce them with the same script; omit them with `--no-plots` or redirect them
with `--plots-dir`.

---

## 11. Limitations and next steps

**Limitations.** Beyond §9.5: the spike detector has a defined convention and both
recorded and simulated traces are measured with the *same* detector, so no
detector-induced bias enters the comparison — but the two detectors in use disagree
by 0.56 ms on the same events (AllenSDK's `detect_putative_spikes` reports the
model's first spike at 1059.535 ms on the dV/dt criterion, the Phase 2D 0 mV-crossing
detector at 1060.095 ms). That is immaterial at a 40–64 ms error scale, and it is
recorded so that no one later attributes the latency discrepancy to a detector.
Additionally, the model contains no trial-to-trial variability, so the four repeats
cannot probe it; and the plateau is measured over the last 200 ms of the step, a
window that is available in both blocks but is not the same absolute time in the
experiment.

**Next steps that this phase's evidence supports**, none of which involves
modifying or refitting the model:

1. **Characterise the block difference from the recordings alone.** The observation
   in §9.3 — same resting potential, more depolarised plateau, twelve times fewer
   spikes — can be turned into a testable statement about adaptation with the
   metadata already held, without touching the model. This is the highest-value
   follow-up because it decides how much of the mismatch is out-of-domain.
2. **Resolve the sweep-38 anomaly.** The post-step doublet at 5514.81/5521.96 ms is
   either a real spontaneous event or a recording artefact, and Phase 1C and Phase
   2D each treat it as unresolved. Until it is settled, sweep 38 is a poor fitting
   target and an even poorer validation target.
3. **Evaluate the all-active model `497233292` on the same sweeps** as a separate,
   pre-registered phase. It was explicitly out of scope here, and it is the natural
   test of whether the missing accommodation lives in the perisomatic compartment.
4. **Only then consider a protocol for parameter estimation against the FINEST
   block**, if at all — and only with a held-out split that does not reuse the same
   four sweeps.

The wrong next step is to adjust the current model until the FINEST sweeps agree.
That would convert an honest negative result into an in-sample fit with no
predictive value, and it is excluded by the brief.

---

## 12. Reproduction and artefact inventory

```bash
# 1. reuse the Phase 2C environment; nothing is downloaded
#    uv -> CPython 3.11.18 -> ~/incm_phase2c/venv
#    numpy 1.23.5  scipy 1.10.1  h5py 3.10.0  pandas 1.5.3
#    scikit-image 0.21.0  matplotlib 3.7.5 (Agg)  neuron 8.2.7

# 2. stage a private workspace from the Phase 2C assets
#    ~/incm_phase2e/model    manifest.json  382982932_fit.json
#                            674389901_382982932_m.swc  674389910_382982932_m.marker
#                            modfiles/ (16)  382982932.nwb  empty work/
#    ~/incm_phase2e/results  empty

# 3. run the evaluation (parent spawns one child process per sweep)
PYTHONDONTWRITEBYTECODE=1 ~/incm_phase2c/venv/bin/python \
  scripts/evaluate_finest_held_out.py \
    --model-dir       ~/incm_phase2e/model \
    --allensdk-src    <repo>/tmp/model_cache/2b/src/AllenSDK-2.16.2 \
    --repo-cache      <repo>/tmp/model_cache \
    --phase2c-traces  ~/incm_phase2c/results/traces_sweep38.npz \
    --out-dir         ~/incm_phase2e/results \
    --plots-dir       ~/incm_phase2e/figures
```

The script exits `0` when every pipeline check passes and `1` when one fails.
**The biological verdict never changes the exit code** — that separation is
deliberate and is the mechanical form of the distinction this report insists on
between pipeline correctness and predictive performance.

Result tally for the canonical run:

```
checks: 107   passed: 107   failed: 0   skipped: 0   metrics: 77
  A. Provenance and held-out independence      56
  B. Mechanism compilation                      4
  C. Execution                                 32
  D. Output identity                            6
  E. Predicted versus observed                  4
  F. Cross-sweep summary                        1
  G. Sweep 38 beside the held-out repeats       4
verdict: HELD-OUT PREDICTION MISMATCH
```

Artefacts, all outside the repository and outside Git tracking:

| Artefact | Size | Note |
|---|---|---|
| `results/phase2e_summary.json` | 66 005 B | 107 checks, 77 metrics, all facts |
| `results/sweep_49..52/traces.npz` | — | `v_sim`, `t_ms`, `v_raw_mv` per sweep |
| `results/sweep_49..52/child_summary.json` | — | per-process execution facts |
| `results/nrnivmodl.log` | 753 B | verbatim compiler output |
| `model/work/382982932.nwb` | 95 170 007 B | last sweep written (52); overwritten per sweep |
| `model/x86_64/libnrnmech.so` | 149 016 B | compiled mechanisms |
| `figures/*.png` | 29 547–92 041 B | the four figures in §10 |

---

## 13. Constraints honoured

| Constraint | Status |
|---|---|
| No new NWB downloads | No download; every input read from the existing cache |
| No fitting or parameter modification | Descriptor byte-identical to the published copy; no optimiser run |
| No morphology or mechanism change | SWC, marker and 16 `.mod` files byte-identical |
| −14 mV junction convention preserved | Verified as an exact +14.000 mV output-only shift |
| Original NWB not modified | Digests unchanged before and after; execution in a staged copy |
| No all-active simulation | `497233292` not executed; descriptor read only to prove disjointness |
| No FHN | Not run |
| No optimisation | Not run |
| No changes to Phase 0 or Phase 1 inventories | No inventory file touched |
| No pooling of COARSE and FINEST | Enforced throughout; sweep 38 appears only in its own comparison |
| No claim that the cross-protocol difference is explained | §9.3 states the opposite explicitly |

---

## 14. Final verdict

**HELD-OUT PREDICTION MISMATCH.**

**Pipeline: correct.** 107 of 107 provenance, execution and numerical checks passed.
The model ran unmodified in the validated environment, wrote through AllenSDK's own
runner, and its output was read back and compared using the Phase 2C and Phase 2D
detectors and conventions. Its sweep-49 output reproduces the Phase 2C sweep-38
trace to `0.000e+00 mV` over 1,204,001 samples.

**Prediction: wrong.** Twelve spikes predicted; one observed, in every one of the
four held-out sweeps. First spike 51.6 ms early on average. In-step correlation
0.241. 92.4 % of the in-step squared error within ±10 ms of a spike the model
produced.

**The one apparent success was in-sample and count-only.** Sweep 38's 12-versus-12
agreement came with a 0.1422 in-step correlation and a 25.7 ms median spike-timing
error, on the sweep the model was fitted to, with a prediction that is bit-identical
to the one that fails on the held-out block.

The model was not modified to improve the result, and the unresolved COARSE/FINEST
physiological difference is neither invoked as an excuse nor claimed as an
explanation.

---

**End of Phase 2E.** Four held-out sweeps were executed, compared and reported. No
fitted parameter, descriptor, morphology, mechanism, manifest or convention was
modified. No NWB was downloaded. The all-active model, FHN, parameter fitting and
every COARSE sweep other than the sweep-38 comparison were not run. The simulation
genuinely executed, its output was read back out of the NWB it wrote, and the
result is a negative predictive result with a correct pipeline behind it.

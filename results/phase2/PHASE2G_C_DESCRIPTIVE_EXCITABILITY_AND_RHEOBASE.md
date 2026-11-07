# Phase 2G-C — Descriptive Excitability and Rheobase Mapping of the All-Active Model

    All-active model 497233292 using published parameters, substitute
    morphology 674389901, and project-declared axon treatment stub.
    All-active model 497233292 using published parameters, substitute
    morphology 674389901, and project-declared axon treatment truncated.

These are **substitute-morphology reconstructions, not reproductions of
Allen's original fitted model**: the reconstruction the parameters were fitted
with is unavailable (Phase 2G-A), and the axon treatment under which the fit
was run was never published.  Nothing in this phase fits, refits, optimises or
modifies any model parameter.  It measures.

---

## 1. Executive verdict

**MEASURED AND REPRODUCIBLE; BRANCH-DIVERGENT AT THE SPIKE LEVEL.**

Twenty-eight runs — two declared axon treatments times fourteen stimulus
conditions of the validated COARSE long-square block — all executed
successfully with zero failed pipeline checks, byte-identical inputs, one
compiled mechanism library, and a +170 pA condition that reproduces the Phase
2G-B output NWBs byte-for-byte.  The descriptive results:

| quantity | stub axon | truncated axon | recorded neuron (COARSE, 1 s steps) |
| --- | --- | --- | --- |
| first in-step spike | none up to +270 pA | between +170 and +190 pA | between +110 and +130 pA (Phase 2F) |
| descriptive rheobase | **above the tested range** (> 270 pA) | **interval (170, 190] pA** | interval (110, 130] pA |
| slope input resistance (ohmic region, 7 points) | 44.9 MΩ (r² = 0.9992) | 84.5 MΩ (r² = 0.9950) | not measured in this phase |
| apparent R_in at +170 pA | 41.9 MΩ | 72.2 MΩ | — |
| spike count at +270 pA | 0 | 26 | 32 |
| settled baseline (written frame) | −61.895 mV | −63.325 mV | −80.869 mV (recorded sweep-38 settled baseline) |

The unpublished axon configuration is **consequential at the spike level, not
only in the subthreshold margin**: the two reconstructions of the *same*
published parameter set differ by 1.72× in apparent input resistance at
+170 pA (1.88× in ohmic slope), and they disagree qualitatively on whether the
model fires at all inside the tested range.  The stub reconstruction is silent
at every depolarizing amplitude the recording offers; the truncated
reconstruction crosses threshold between +170 and +190 pA and reaches 26 Hz at
+270 pA.

Neither reconstruction's rheobase is the biological cell's rheobase; both are
properties of a reconstruction built on a substitute morphology.  The
recording's own excitability is stated separately in §8.  No branch is
selected, and no branch-level agreement is used to argue that either
configuration is the one Allen fitted.

---

## 2. Stimulus conditions and exclusions

### 2.1 Where the amplitudes come from

**OBSERVED.** All stimulus conditions are the recorded waveforms of block
`C1LSCOARSE150216` (sweeps 24–43) in the validated NWB
(`data/nwb_cache/382982932.nwb`, SHA-256 `d38b43fc…87b63`, 94 207 824 B).
No waveform was constructed, edited or substituted.  The command levels were
re-measured from the stimulus arrays before the run plan was frozen, with the
Phase 2D stimulus classifier (`analyse_stimulus`, which removes the invariant
embedded +50 pA probe by identity and is sign-agnostic); every run re-checks
its own level against the frozen table (tolerance 0.01 pA; the DAC writes
levels like 170.000000188 pA):

| sweep | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | **38** | 39 | 40 | **41** | 42 | 43 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| level (pA) | −110 | −90 | −70 | −50 | −30 | −10 | +10 | +30 | +50 | +70 | +90 | +110 | +130 | +150 | **+170** | +190 | +210 | **+230** | +250 | +270 |

All steps are 1000.0 ms at a 1020.0 ms onset, 200 kHz, in 8.02 s traces.

### 2.2 The frozen condition list

Fourteen conditions were executed per branch (28 runs total):

| run | sweep | condition label | level (pA) | role |
| --- | --- | --- | --- | --- |
| M01 | 24 | `coarse_n110` | −110 | hyperpolarizing control (input-resistance cross-check) |
| M02 | 30 | `coarse_p010` | +10 | lowest positive COARSE amplitude |
| M03 | 31 | `coarse_p030` | +30 | |
| M04 | 32 | `coarse_p050` | +50 | |
| M05 | 33 | `coarse_p070` | +70 | |
| M06 | 34 | `coarse_p090` | +90 | |
| M07 | 35 | `coarse_p110` | +110 | highest amplitude below the recorded first spike |
| M08 | 36 | `coarse_p130` | +130 | |
| M09 | 37 | `coarse_p150` | +150 | |
| **M10** | **38** | `coarse_p170` | **+170** | the Phase 2G-B condition; doubles as the baseline reproduction check |
| M11 | 39 | `coarse_p190` | +190 | |
| M12 | 40 | `coarse_p210` | +210 | |
| M13 | 42 | `coarse_p250` | +250 | |
| M14 | 43 | `coarse_p270` | +270 | highest valid depolarizing amplitude in the block |

This satisfies the brief's minimum: +170 itself, amplitudes below it (+10 …
+150), amplitudes above it (+190 … +270), and the highest valid depolarizing
amplitude (+270).  **Excluded:** sweep 41 (+230 pA) — it fitted this model and
is refused by the executor under every invocation; sweeps 25–29 (−90 … −10
pA) — additional hyperpolarizing levels beyond the single control; all FINEST
and C2 sweeps — see §8.  The +230 pA exclusion leaves a 20 pA gap in the
tested ladder (+210 → +250); every rheobase statement below is bounded by the
amplitudes that were actually run, never extrapolated across that gap.

---

## 3. Model and asset provenance

**OBSERVED.** Identical to Phase 2G-B, and re-verified in every one of the 28
runs (section A of each run's check tally: 31 asset checks, 0 failures):

| asset | value |
| --- | --- |
| specimen | 382982932 |
| model | 497233292, `Biophysical - all active`, template 491455321 |
| descriptor | `497233292_fit.json`, SHA-256 `bcffd56b…b5963`, 5 738 B — unchanged, never edited |
| substitute morphology | reconstruction 674389884 / SWC `674389901_382982932_m.swc`, SHA-256 `71bb551b…f36c`, 335 924 B |
| marker | `674389910_382982932_m.marker`, SHA-256 `3cc83ad8…0925`, 373 B |
| stimulus NWB | `382982932.nwb`, SHA-256 `d38b43fc…7b63`, 94 207 824 B — read-only, never modified |
| fitting sweep | 41 (+230 pA) — excluded from every evaluation |
| junction potential | −14 mV; output stage writes V_sim + 14 mV, verified `max_abs_delta_v = 0.0` in every run |

The staged cell (identical to 2G-B): 59 sections — soma 1 / 641.059 µm²,
dend 38 / 758.504 µm², apic 18 / 494.622 µm², axon 2.  The axon is the only
difference between the branches: **stub** 2 × 30 µm, diameter 1.0 µm,
188.496 µm², attached at `soma[0](0.5)`; **truncated** 2 sections, diameters
0.403667/0.2288 µm, 59.609 µm², attached at `soma[0](1.0)`.  All 42 genome
entries were applied and read back matching in every run (0 dropped; the
`AllActiveUtils` silent-drop hazard is checked, not assumed away).

All 31 entries of the Phase 2A asset cache (`assets_2a.json`) were re-digested
in place after the runs: **0 missing, 0 mismatched**.  The repository copy of
the recording and every cached original is byte-identical to what Phase 1C/2B
validated.

---

## 4. Environment and execution reproducibility

**OBSERVED.** Isolated WSL2 staging under `~/incm_phase2gc/` (a fresh tree, so
the Phase 2G-B tree and its outputs stay pristine), Python 3.11.18 in the
Phase 2C venv, NEURON 8.2.7, AllenSDK 2.16.2 from the pinned source tree
(`utils.py` `fbd5c75f…`, `hoc_utils.py` `c29daeaf…`, `runner.py`
`7acc5793…`).  Mechanisms compiled once into
`~/incm_phase2gc/model/x86_64/libnrnmech.so` (149 016 B, SHA-256
`aa4f3257…612b`) and reused by every run — the analysis verifies all 28 runs
record the same library digest.

The executor extension for this phase is deliberately minimal: a `--condition`
label that marks a run as a Phase 2G-C measurement of a COARSE sweep, with the
2G-B identities A–D and all existing checks unchanged.  The generalised
amplitude check replaces the hardcoded +170 pA plateau assertion: each run now
measures its own command level and compares it to the validated table, so a
run staged against the wrong sweep fails loudly.

### 4.1 Exact command (one per run; each run its own process)

```
~/incm_phase2c/venv/bin/python ~/proj/scripts/validate_all_active_execution.py \
    --model-dir    ~/incm_phase2gc/model \
    --allensdk-src ~/proj/tmp/model_cache/2b/src/AllenSDK-2.16.2 \
    --repo-cache   ~/proj/tmp/model_cache \
    --run-id M07 --condition coarse_p110 \
    --axon-type    truncated \
    --sweep        35 \
    --out-dir      ~/incm_phase2gc/results/M07_truncated_sweep35
```

`--axon-type` is explicit in all 28 invocations (never the runner default);
runs M02–M14 additionally carry `--skip-compile` after the first run compiled
the shared library.  Every run directory contains `command.txt`, the literal
recorded command line, `stdout.txt`, `stderr.txt`, `execution.log`,
`traces_<branch>_sweep<id>.npz` and `run_summary.json`.

### 4.2 Consistency: 15 PASS, 0 FAIL

1. both branches executed all 14 conditions (28 runs)
2. no run executed the fitting sweep 41
3. all 28 runs report status success (0 failed checks; tallies 73 or 68 checks
   per run, differences are the compile section and recorded-spike metrics)
4. every run is recorded as a Phase 2G-C measurement with a `--condition` label
5. every recorded command line names `--axon-type` and `--condition`
6. every measured command level matches the validated table
7. all runs consumed byte-identical inputs
8. all runs executed the same compiled mechanism library
9. the crossing detector and the Allen NWB detector agree on every run
10. stub branch: one settled baseline (−61.895351 mV) across all 14 conditions
11. truncated branch: one settled baseline (−63.324701 mV) across all 14
    conditions — the lead-in is the same 0 pA segment in every sweep, so any
    drift here would signal a broken determinism assumption
12. **stub +170 pA reproduces the Phase 2G-B run A output NWB byte-for-byte**
    (`3bff27469e75e6c9…c33`)
13. **truncated +170 pA reproduces the Phase 2G-B run C output NWB
    byte-for-byte** (`20ca3a9ec4a9da75…b10b`)
14. every run wrote a distinct trace file (28 distinct trace digests)
15. the two spike detectors agree (repeat of 9 by construction of the report)

The fresh `nrnivmodl` compile produces a different library digest than 2G-B's
(`aa4f3257…` vs `d40eb5fd…`) — object files are not reproducible — but checks
12 and 13 show the simulation outputs are byte-identical anyway, exactly as
the 2G-B determinism replicate established.  Per-run wall time: 226–313 s
(stub), 284–329 s (truncated).

---

## 5. Results — stub axon treatment

**OBSERVED/DERIVED.** Model-only measurements, written-output frame (junction
correction applied), Phase 2E conventions (baseline = last 100 ms before the
step; plateau = median of the last 200 ms of the step; spikes by the validated
0 mV-crossing detector with 1.5 ms refractory).

| run | sweep | pA | in-step spikes | first latency (ms) | mean rate (Hz) | plateau (mV) | response (mV) | apparent R_in (MΩ) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | 24 | −110 | 0 | — | — | −67.035 | −5.140 | 46.7 |
| M02 | 30 | +10 | 0 | — | — | −61.436 | +0.460 | 46.0 |
| M03 | 31 | +30 | 0 | — | — | −60.555 | +1.340 | 44.7 |
| M04 | 32 | +50 | 0 | — | — | −59.690 | +2.206 | 44.1 |
| M05 | 33 | +70 | 0 | — | — | −58.839 | +3.057 | 43.7 |
| M06 | 34 | +90 | 0 | — | — | −58.002 | +3.894 | 43.3 |
| M07 | 35 | +110 | 0 | — | — | −57.178 | +4.718 | 42.9 |
| M08 | 36 | +130 | 0 | — | — | −56.366 | +5.530 | 42.5 |
| M09 | 37 | +150 | 0 | — | — | −55.564 | +6.332 | 42.2 |
| M10 | 38 | +170 | 0 | — | — | −54.770 | +7.125 | 41.9 |
| M11 | 39 | +190 | 0 | — | — | −53.983 | +7.912 | 41.6 |
| M12 | 40 | +210 | 0 | — | — | −53.199 | +8.697 | 41.4 |
| M13 | 42 | +250 | 0 | — | — | −51.625 | +10.271 | 41.1 |
| M14 | 43 | +270 | 0 | — | — | −50.825 | +11.071 | 41.0 |

- Settled baseline: **−61.895 mV**, identical across all conditions; settles
  before the step in every run (drift over the last 20 ms of lead-in
  ≤ 0.0004 mV).
- **Descriptive rheobase: above the tested range** — no tested amplitude up to
  +270 pA elicicted a spike.  At +270 pA the subthreshold peak is −50.279 mV
  (11.617 mV of excursion above baseline); no numerical rheobase is
  extrapolated.
- Slope input resistance over the ohmic region (|I| ≤ 110 pA, 7 subthreshold
  points −110…+110): **44.9 MΩ**, r² = 0.9992, intercept −0.100 mV.
- The I–V relation is nearly linear over the whole tested range: apparent
  R_in falls only from 46.7 MΩ (−110 pA) to 41.0 MΩ (+270 pA).

## 6. Results — truncated axon treatment

| run | sweep | pA | in-step spikes | first latency (ms) | mean rate (Hz) | plateau (mV) | response (mV) | apparent R_in (MΩ) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | 24 | −110 | 0 | — | — | −73.622 | −10.297 | 93.6 |
| M02 | 30 | +10 | 0 | — | — | −62.494 | +0.831 | 83.1 |
| M03 | 31 | +30 | 0 | — | — | −60.899 | +2.426 | 80.9 |
| M04 | 32 | +50 | 0 | — | — | −59.375 | +3.950 | 79.0 |
| M05 | 33 | +70 | 0 | — | — | −57.915 | +5.410 | 77.3 |
| M06 | 34 | +90 | 0 | — | — | −56.508 | +6.816 | 75.7 |
| M07 | 35 | +110 | 0 | — | — | −55.142 | +8.183 | 74.4 |
| M08 | 36 | +130 | 0 | — | — | −53.797 | +9.528 | 73.3 |
| M09 | 37 | +150 | 0 | — | — | −52.448 | +10.877 | 72.5 |
| M10 | 38 | +170 | 0 | — | — | −51.055 | +12.270 | 72.2 |
| M11 | 39 | +190 | **1** | **34.57** | 1.0 | −49.561 | +13.764 | 72.4 |
| M12 | 40 | +210 | **4** | **18.54** | 4.0 | −47.850 | +15.475 | 73.7 |
| M13 | 42 | +250 | **23** | **11.43** | 23.0 | −49.500 | +13.825 | 55.3 |
| M14 | 43 | +270 | **26** | **9.61** | 26.0 | −50.619 | +12.706 | 47.1 |

- Settled baseline: **−63.325 mV**, identical across all conditions; settles
  before the step in every run (drift ≤ 0.0002 mV).
- **Descriptive rheobase: interval (170, 190] pA** — silent at +170 pA, one
  spike at +190 pA (first-spike latency 34.57 ms, absolute peak +18.885 mV
  in the written frame — 82.210 mV above the settled baseline).
- Slope input resistance over the same ohmic region: **84.5 MΩ**,
  r² = 0.9950, intercept −0.544 mV.
- Firing behaviour, once spiking: at +210 pA, 4 spikes with ISIs
  45.965 / 54.140 / 68.910 ms (mean 56.338 ms); at +250 pA, 23 spikes, 22
  ISIs spanning 22.565–55.380 ms (mean 44.600 ms) — a train that lengthens
  its intervals early and then stabilises near 54–55 ms before the step ends;
  at +270 pA, 26 spikes, 25 ISIs spanning 18.225–48.390 ms (mean 38.940 ms)
  with the same stabilise-at-the-end pattern (final ISIs ≈ 47.6 ms).
- The plateau and apparent-R_in columns of the three spiking rows are no
  longer passive measurements: the median over the last 200 ms of a spiking
  trace mixes inter-spike troughs with depolarised epochs, which is why
  "response" appears to fall from +15.475 mV (+210) to +12.706 mV (+270).
  The subthreshold rows (up to +170 pA) are unaffected by this caveat.

---

## 7. Branch sensitivity (model-only, never pooled)

Each entry is a pairwise comparison of the two answers to the *same* recorded
condition; no averaging across branches exists anywhere in the pipeline (the
analysis refuses to build a branch table from mixed-branch runs).

| run | pA | response stub (mV) | response truncated (mV) | Δresponse (mV) | apparent-R_in ratio (trunc/stub) | in-step RMS ΔV (mV) | in-step max abs ΔV (mV) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | −110 | −5.140 | −10.297 | −5.157 | 2.00 | 6.518 | 6.591 |
| M02 | +10 | +0.460 | +0.831 | +0.372 | 1.81 | 1.059 | 1.430 |
| M03 | +30 | +1.340 | +2.426 | +1.086 | 1.81 | 0.360 | 1.430 |
| M04 | +50 | +2.206 | +3.950 | +1.744 | 1.79 | 0.327 | 1.430 |
| M05 | +70 | +3.057 | +5.410 | +2.353 | 1.77 | 0.923 | 1.430 |
| M06 | +90 | +3.894 | +6.816 | +2.922 | 1.75 | 1.489 | 1.583 |
| M07 | +110 | +4.718 | +8.183 | +3.465 | 1.73 | 2.032 | 2.200 |
| M08 | +130 | +5.530 | +9.528 | +3.998 | 1.72 | 2.566 | 2.858 |
| M09 | +150 | +6.332 | +10.877 | +4.545 | 1.72 | 3.117 | 3.629 |
| M10 | +170 | +7.125 | +12.270 | +5.145 | 1.72 | 3.724 | 4.708 |
| M11 | +190 | +7.912 | +13.764 | +5.851 | 1.74 | 4.636 | **72.786** |
| M12 | +210 | +8.697 | +15.475 | +6.779 | 1.78 | 5.829 | **73.748** |
| M13 | +250 | +10.271 | +13.825 | +3.554 | 1.35 | 7.662 | **73.482** |
| M14 | +270 | +11.071 | +12.706 | +1.635 | 1.15 | 7.851 | **73.270** |

- **Subthreshold branch difference.** The truncated reconstruction is 1.72×
  more responsive at +170 pA (apparent R_in ratio 1.72; slope ratio 84.5 /
  44.9 = 1.88 over the ohmic region).  The Δresponse grows monotonically with
  amplitude while both branches are subthreshold (up to +6.779 mV at +210
  pA).  At −110 pA the ratio is 2.00 — the hyperpolarizing control separates
  the branches even more than the depolarizing range does.
- **Spike-level branch difference.** From +190 pA upward the maximum voltage
  difference is ≈ 73 mV: one branch spikes, the other does not.  This is not
  an exaggeration of scale — it is the difference between a spike train and
  its absence, produced by the *only* free configuration choice in the
  reconstruction.
- **First-spike-producing amplitude.** Not measurable as a single number of
  pA: the truncated branch first spikes in (170, 190] pA and the stub branch
  does not spike within the tested range at all.  Quantified as: the stub
  rheobase exceeds the truncated rheobase by at least 270 − 190 = **80 pA**
  (lower bound, since the stub value is only bounded below by +270 pA).
- The shrinking Δresponse and R_in ratio at +250/+270 pA are consequences of
  the truncated trace spiking (see the caveat in §6), not a convergence of
  the branches: the in-step RMS difference keeps growing (7.662 → 7.851 mV).

---

## 8. Comparison with the recorded neuron — carefully separated

Model-only excitability and the recorded neuron's observed excitability are
different kinds of statement.  The tables above describe reconstructions built
on a substitute morphology; nothing in them is the biological cell's
rheobase.  The recording columns below come from the same run summaries
(recorded spike counts of the executed sweeps) and Phase 2F.

### 8.1 Recorded spike counts at the shared COARSE conditions

| pA | recorded in-step spikes | stub spikes | truncated spikes | recorded first latency (ms) | truncated first latency (ms) |
| --- | --- | --- | --- | --- | --- |
| −110…+110 | 0 | 0 | 0 | — | — |
| +130 | 1 | 0 | 0 | 148.185 | — |
| +150 | 6 | 0 | 0 | 58.755 | — |
| **+170** | **12** | 0 | 0 | 39.750 | — |
| +190 | 18 | 0 | **1** | 30.990 | 34.570 |
| +210 | 22 | 0 | **4** | 25.405 | 18.540 |
| +250 | 29 | 0 | **23** | 18.175 | 11.430 |
| +270 | 32 | 0 | **26** | 15.415 | 9.610 |

Observations, stated without mechanism inference:

1. **The recorded neuron is more excitable than either reconstruction.**  Its
   COARSE rheobase interval is (110, 130] pA (Phase 2F); the truncated
   reconstruction's is (170, 190] pA — at least 40 pA and at most 80 pA
   higher; the stub reconstruction's is above +270 pA — at least 140 pA
   higher.
2. **The stub reconstruction misses the recording qualitatively** — 0 spikes
   where the recording shows up to 32.
3. **The truncated reconstruction crosses threshold in the right region of
   the ladder but fires less than the recording at every shared amplitude**
   (1 vs 18 at +190 pA; 26 vs 32 at +270 pA), and its first-spike latencies
   are shorter than the recorded ones once it fires (34.57 vs 30.99 ms at
   +190 pA is close; 9.61 vs 15.42 ms at +270 pA is not).
4. At the highest amplitudes the truncated spike counts approach the recorded
   ones (23/29 and 26/32), but "approaching at high drive" is a statement
   about this ladder only, and the +230 pA fitting sweep was never tested.

### 8.2 Protocol labels, preserved

- Sweep 38 (+170 pA, 12 recorded spikes) remains the **anomalous COARSE
  plausibility bracket**: the COARSE block is the anomalous one (Phase 2D/2F),
  and its spike counts are not interchangeable with FINEST's.
- FINEST sweeps 49–52 are **one repeated condition** (+170 pA, one spike in
  each repeat, latencies 104.045 / 77.020 / 93.180 / 92.535 ms — ±27 ms of
  recording variability), not four conditions.  Phase 2G-B already compared
  the models to sweep 49 as the primary held-out test: both branches produced
  0 spikes against the single recorded one.  No FINEST or C2 sweep was
  executed in this phase, and none was pooled with COARSE.
- The COARSE/FINEST discrepancy is a property of the recording, and no
  specific biological mechanism is inferred from it here.

---

## 9. Figures

Under `tmp/phase2g_c_figures/` (gitignored), every figure titled with the
model identity, morphology substitution, axon treatment and stimulus protocol:

1. `fig1_stub_spikecount.png` — stub: amplitude vs in-step spike count (0 at
   every tested amplitude).
2. `fig2_truncated_spikecount.png` — truncated: amplitude vs in-step spike
   count (0 → 1 → 4 → 23 → 26).
3. `fig3_depolarisation.png` — both branches: amplitude vs steady-state
   response (two labelled series, never pooled; the truncated curve bends over
   where it starts spiking).
4. `fig4_firing_rate.png` — both branches: amplitude vs mean in-step firing
   rate; the stub series is labelled as absent rather than silently dropped.
5. `fig5_branch_difference.png` — per shared condition: in-step RMS and
   maximum absolute voltage difference between the branches (the ≈ 73 mV
   maximum from +190 pA upward is the spike/no-spike difference).

---

## 10. Limitations and unresolved assumptions

- **Substitute morphology.** Reconstruction 674389884 / SWC 674389901 is not
  the geometry the parameters were fitted with (unavailable, Phase 2G-A).
  Every number above is a property of a reconstruction.
- **Unpublished axon treatment.** Neither branch can be shown to be Allen's
  original configuration; a branch that matches the recording more closely is
  not thereby the fitted one, and no branch is selected here.
- **Ladder resolution.** The COARSE spacing is 20 pA and the +230 pA fitting
  sweep is excluded, so the truncated rheobase interval (170, 190] is 20 pA
  wide with a 40 pA untested gap above +210; the stub rheobase is bounded
  only below (above +270 pA).  No numerical rheobase is extrapolated.
- **Spiking-row plateau measurements.** For the three truncated conditions
  that fire, "steady-state response" and apparent R_in are medians over a
  spiking trace (§6) — reported for completeness, not as passive properties.
- **One cell, one recording file, one substitute morphology.** Nothing here
  generalises to other specimens or models.
- **ASSUMED.** That `axon_type` ∈ {stub, truncated} enumerates the relevant
  configuration space (it enumerates the two documented treatments).
- **UNAVAILABLE.** The fitted reconstruction and the fitted axon
  configuration; the recording's true rheobase at finer resolution than the
  protocol brackets.

Per the instruction for this task, no FHN work and no Phase 3 work was
started.

---

## 11. Deliverables and reproduction

| artefact | location |
| --- | --- |
| this report | `results/phase2/PHASE2G_C_DESCRIPTIVE_EXCITABILITY_AND_RHEOBASE.md` |
| executor (extended with the `--condition` measurement mode) | `scripts/validate_all_active_execution.py` |
| excitability/rheobase analysis | `scripts/analyse_all_active_excitability.py` |
| tests (25 new; suite: 251 passed) | `tests/test_all_active_excitability.py` |
| run outputs (28 dirs, outside the repo) | `~/incm_phase2gc/results/M<nn>_<branch>_sweep<id>/` |
| machine-readable copies (gitignored) | `tmp/phase2g_c_results/` (28 summaries + commands + `phase2g_c_summary.json`) |
| figures (gitignored) | `tmp/phase2g_c_figures/` |

Reproduction, in order:

```bash
bash tmp/gc_stage.sh                      # stage ~/incm_phase2gc/model, verify digests
bash tmp/gc_run.sh stub      1 14         # 14 runs, one process each
bash tmp/gc_run.sh truncated 1 14         # 14 runs, one process each
~/incm_phase2c/venv/bin/python scripts/analyse_all_active_excitability.py \
    --results-root  ~/incm_phase2gc/results \
    --baseline-root ~/incm_phase2g_b/results \
    --figures-dir   ~/proj/tmp/phase2g_c_figures \
    --out-dir       ~/incm_phase2gc/results
python -m pytest tests -q                 # 251 passed
```

The staging and chunk driver scripts live under gitignored `tmp/` as working
instructions; the versioned deliverables are the executor, the analysis, the
tests and this report.

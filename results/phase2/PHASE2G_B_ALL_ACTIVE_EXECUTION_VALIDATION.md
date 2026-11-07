# Phase 2G-B — All-Active Model Isolated Execution Validation

**Repository:** `Patel-Princy/INCM_project`  **Branch:** `ashish-work`
**Specimen:** `382982932` (mouse VISp, L2/3, `Nr5a1-Cre;Ai14-177333.03.01.01`)
**Model class:** `Biophysical - all active`  **Model ID:** `497233292`  **Template ID:** `491455321`
**Fit descriptor:** `497233292_fit.json`, 5 738 B, `sha256 bcffd56bbcec001b…`
**Fitting sweep:** `41` (`C1LSCOARSE150216`) — **excluded from every evaluation in this phase**
**Published fitted reconstruction:** `491771090` — does not exist in the API
**Substitute morphology:** reconstruction `674389884`, SWC `674389901`, marker `674389910`
**Executor:** `scripts/validate_all_active_execution.py` (one run per process; 73/68 checks, 0 failures)
**Branch analysis:** `scripts/analyse_all_active_branches.py` (10 consistency checks, 0 failures)
**Tests:** `tests/test_all_active_execution_validation.py` (25 tests; 221 in the suite)
**Figures:** `tmp/phase2g_b_figures/` (ignored)  **Summaries:** `tmp/phase2g_b_results/` (ignored)
**Predecessors:** `PHASE2G_A_ALL_ACTIVE_READINESS_AUDIT.md` and, before it, the Phase 2A–2F reports

**Evidence vocabulary**

| Tag | Meaning |
|---|---|
| **OBSERVED** | measured in a file, reproducible from a digest |
| **DERIVED** | a consequence of OBSERVED facts plus AllenSDK source, with no unknowns |
| **ASSUMED** | true only if an unrecorded choice is made |
| **UNAVAILABLE** | not derivable from any published artefact |

---

**Model identity used by every run, figure and table in this report**

> All-active model 497233292 using published parameters, substitute
> morphology 674389901, and project-declared axon treatment stub
> *or* truncated.

Nothing in this report is a reproduction of Allen's originally fitted model.
The fitted reconstruction (`491771090`) is gone and `axon_type` was never
published, so each branch is a separate reconstruction and the two are never
pooled, averaged, or ranked.

---

## 1. Executive verdict

**EXECUTED AND REPRODUCIBLE; PREDICTIVELY DIVERGENT.**

| Dimension | Finding | Basis |
|---|---|---|
| **Pipeline execution** | All four runs completed. 73 + 68 + 68 + 68 checks, **0 failures**. | **OBSERVED** |
| **Numerical reproducibility** | A second process reproduced run A **bit-for-bit**: identical trace (max \|ΔV\| = 0.000e+00 mV) and identical output NWB digest. | **OBSERVED** |
| **Sweep 38 response** | Not reproduced. Recorded: 12 in-step spikes. Simulated: **0** in both branches. | **OBSERVED** |
| **Sweep 49 held-out response** | Not reproduced. Recorded: 1 spike at 1124.045 ms. Simulated: **0** in both branches. | **OBSERVED** |
| **Branch sensitivity** | Material at the sub-threshold level: step response 7.125 mV (`stub`) vs 12.270 mV (`truncated`), R_in 41.9 vs 72.2 MΩ, in-step branch difference 3.724 mV RMS / 4.708 mV max. The qualitative outcome — no spikes at +170 pA — is branch-invariant for these two stimuli. | **OBSERVED** |
| **Fidelity to the originally fitted model** | Unknowable; the fitted geometry and the fitted axon treatment are both unavailable. | **UNAVAILABLE** |

**The one sentence form:** *the model runs perfectly and does not predict
either recording, and the unpublished axon configuration changes the
sub-threshold prediction by a factor of 1.7 while leaving the spike outcome
unchanged in these two tests.*

Both axon branches are inexcitable at +170 pA. The entire depolarisation the
stimulus produces is 7.23 mV (`stub`) or 13.36 mV (`truncated`) above the
settled baseline — the model never approaches a firing threshold, whereas the
recording fires 12 times (sweep 38) and once (sweep 49) under the same
command. At the same time the model's resting potential is *more* depolarised
than the recording's by 17.5–19.2 mV in the comparison frame. Both facts are
reported as measurements of these two reconstructions. No biological
mechanism is inferred from either.

---

## 2. Asset and environment provenance

Every check below ran **before** any simulation, inside each of the four run
processes, and is recorded in that run's `run_summary.json`. The executor
stops (exit code 2) rather than warning on any failure.

### 2.1 Input digests — staged copies and originals

| Asset | Size (B) | SHA-256 | Staged | Original in cache |
|---|---:|---|---|---|
| `497233292_fit.json` | 5 738 | `bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963` | matches | matches |
| `674389901_382982932_m.swc` | 335 924 | `71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c` | matches | matches |
| `674389910_382982932_m.marker` | 373 | `3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925` | matches | matches |
| `382982932.nwb` | 94 207 824 | `d38b43fcbdf1c88dfa6741a565ac689289aef931d66e9eb6b64ca5598f237b63` | matches | matches |
| `manifest.json` | 2 982 | `66470dc220a00fb5ebab01968312d393c1581e97ee9274b62b437c9a33e253cd` | matches | matches |

All four runs consumed byte-identical inputs (`tmp/gb_report_numbers.py`
cross-check; the analysis script asserts it). **OBSERVED.**

### 2.2 No cached asset was modified

All **31 entries** of `tmp/model_cache/assets_2a.json` were re-digested in
place after the executions: **0 missing, 0 mismatched**, including the 16
canonical `.mod` files, both reference manifests, the AllenSDK reference
sources and both fit descriptors. The draft originals under
`tmp/model_cache/manifest_drafts/all_active/` (manifest, SWC, marker, 16
modfiles) were separately re-digested and match the staged copies. **OBSERVED.**

### 2.3 AllenSDK source identity

AllenSDK is used **from the cached source tree, never installed**:
`tmp/model_cache/2b/src/AllenSDK-2.16.2`. Each run verified the tree name and
recorded the digests of the three loader-critical files:

| File | SHA-256 |
|---|---|
| `allensdk/model/biophysical/utils.py` | `fbd5c75fdd66a0ed…91910405` |
| `allensdk/model/biophys_sim/neuron/hoc_utils.py` | `c29daeaf4870bfd4…9548115e` |
| `allensdk/model/biophysical/runner.py` | `7acc5793cca57fba…683ca52b6` |

Identity is additionally proven structurally (`axon_type` read from
`description.data["biophys"][1]`, the commented-out perisomatic
`passive["cm"]` loops, the CLI default string). **OBSERVED.**

### 2.4 Environment

| Component | Value |
|---|---|
| Runtime | WSL2, the existing Phase 2C tree `~/incm_phase2g_b/` (outside the repository) |
| Interpreter | Python 3.11.18, `~/incm_phase2c/venv` (no package added, removed, upgraded or downgraded) |
| NEURON | 8.2.7 (recorded inside each run by `h.nrnversion()`) |
| Key packages | numpy 1.23.5, scipy 1.10.1, h5py 3.10.0, matplotlib 3.7.5 |
| Compiled mechanisms | `~/incm_phase2g_b/model/x86_64/libnrnmech.so`, 149 016 B, `sha256 d40eb5fde88c0628…93dd73` — **one library shared by all four runs** |

Run A compiled the mechanisms with `nrnivmodl modfiles/` (return code 0, zero
warnings, zero errors); B, C and D re-used the identical library via
`--skip-compile`, and the analysis script asserts all four runs loaded the
same digest. **OBSERVED.**

### 2.5 Junction-potential convention

The descriptor still carries `junction_potential = −14 mV` and the executor
verified, on the raw captured vectors, that

```
V_written = (V_sim − junction_potential) · 1e-3   →  max |delta| = 0.0 V
```

and that the written peak exceeds the simulated peak by **exactly
+14.000 mV** in every run. The shift is applied at the output stage only: the
simulator's own vector (raw `−90.0 … −68.67` mV stub / `−90.0 … −63.97` mV
truncated) is unshifted, and no model parameter was altered. **OBSERVED.**

### 2.6 Sweep exclusions

* Sweep **41** fitted this model. The executor refuses it (`--sweep 41` exits
  with code 2) and every summary records `fitting_sweep_excluded: 41`.
  Verified by a unit test.
* Exactly two evaluation sweeps were executed: 38 and 49. Sweeps 50–52 were
  **not executed** and appear only as recording-repeatability context
  (§8.3). No other sweep was run.

---

## 3. Manifest and loader configuration

The manifest is the all-active draft (`model_type: "Biophysical - all active"`,
`model_file: ["manifest.json", "497233292_fit.json"]`, runs over sweeps 24–43,
`neuron[0].hoc = ["stdgui.hoc", "import3d.hoc"]`). The perisomatic manifest and
the perisomatic parameter-loading path were **not** used: each run asserts
`isinstance(utils, AllActiveUtils)` and records `utils_class: AllActiveUtils`.
`axon_type_in_manifest` is `False` in every run — the branch comes from the
command line and nowhere else. **OBSERVED.**

The descriptor holds only the four parameter sections
(`conditions/fitting/genome/passive`) and no wiring, run list or `axon_type`;
that absence is itself the loader contract the executor asserts. **OBSERVED.**

### 3.1 The cell each branch actually built

| Section class | Sections | Area (µm²) | Notes |
|---|---:|---:|---|
| soma | 1 | 641.059 | diam 14.285 µm |
| dend | 38 | 758.504 | diam 0.229–0.714 µm |
| apic | 18 | 494.622 | diam 0.236–0.778 µm |
| axon (**stub**) | 2 | **188.496** | 2 × 30 µm, diam 1.0 / 1.0, attached `soma[0](0.5)` |
| axon (**truncated**) | 2 | **59.609** | 2 × 30 µm, diam 0.4037 / 0.2288, attached `soma[0](1.0)` |

59 sections in both branches; only the axon differs. The stub axon is **3.16×**
the truncated axon's membrane area and is attached at the soma midpoint rather
than its distal end. **OBSERVED** (read back from the live cell).

### 3.2 All 42 genome entries applied

`AllActiveUtils.load_cell_parameters` applies genome entries through a
`hasattr(h, section_array)` gate with **no `else` branch** — a missing section
array would drop an entry silently. The executor therefore reads every value
back off the configured cell:

* 42 entries targeted, **42 read back matching, 0 dropped, 0 mismatched**,
  in every one of the four runs (including the replicate).

This is the load-bearing check for the whole phase: without it, "the published
parameters were applied" would be an assumption rather than a measurement.
**OBSERVED.**

---

## 4. Exact commands for both axon branches

Every invocation passes `--axon-type` explicitly; the executor makes the flag
mandatory (`required=True`, choices `stub`/`truncated`) so the runner default
(`truncated`) can never be relied upon silently. Each command line below is
copied verbatim from that run's `command.txt` / `run_summary.json["facts"]["command"]`.

**Run A — stub, sweep 38 (compiles the mechanisms):**

```
/home/ashish/incm_phase2c/venv/bin/python /home/ashish/proj/scripts/validate_all_active_execution.py \
    --model-dir    /home/ashish/incm_phase2g_b/model \
    --allensdk-src /home/ashish/proj/tmp/model_cache/2b/src/AllenSDK-2.16.2 \
    --repo-cache   /home/ashish/proj/tmp/model_cache \
    --run-id A --axon-type stub --sweep 38 \
    --out-dir      /home/ashish/incm_phase2g_b/results/A_stub_sweep38
```

**Run B — stub, sweep 49:** as run A with
`--run-id B --axon-type stub --sweep 49 --out-dir …/B_stub_sweep49 --skip-compile`.

**Run C — truncated, sweep 38:** as run A with
`--run-id C --axon-type truncated --sweep 38 --out-dir …/C_truncated_sweep38 --skip-compile`.

**Run D — truncated, sweep 49:** as run A with
`--run-id D --axon-type truncated --sweep 49 --out-dir …/D_truncated_sweep49 --skip-compile`.

**Determinism replicate (not a fifth evaluation):** run A's exact
configuration re-executed as a second independent process into
`~/incm_phase2g_b/repro/A2_stub_sweep38` with `--skip-compile --skip-compare`.
Its numbers are never pooled with A's.

Four separate processes, four separate output directories, four separate
stdout/stderr logs, four separate output NWB files. **OBSERVED.**

---

## 5. Results for all four runs

| Run | Axon treatment | Sweep | Elapsed | Checks (pass/fail) | Status | Output NWB SHA-256 | Bytes |
|---|---|---|---:|---|---|---|---:|
| A | stub | 38 | 260.9 s | 73 / 0 | success | `3bff27469e75e6c9…ba9aadc33` | 94 330 761 |
| B | stub | 49 | 180.3 s | 68 / 0 | success | `be87179c89de3d45…62e9d35` | 94 329 672 |
| C | truncated | 38 | 240.0 s | 68 / 0 | success | `20ca3a9ec4a9da75…14cb10b` | 94 337 308 |
| D | truncated | 49 | 180.2 s | 68 / 0 | success | `b835824dc763f226…00e6da1` | 94 337 386 |

The four output NWB files are four distinct artefacts (four distinct digests),
all produced from byte-identical inputs and one shared mechanism library.
Identical inputs did **not** produce identical outputs across branches — the
stub and truncated outputs differ, as §7 quantifies. **OBSERVED.**

Two structural facts the analysis script asserts:

1. **A ≡ B and C ≡ D** over their common window (max \|ΔV\| = 0.000e+00 mV,
   1 204 001 samples). Sweeps 38 and 49 deliver the *same* +170 pA command
   (`stimulus_roundtrip_identical: True`), so a deterministic model must
   answer both identically — only the recordings differ (12 spikes vs 1).
   This is a property of the model, not a pipeline fault.
2. **A ≢ C and B ≢ D**: the two branches give genuinely different answers to
   the same question.

### 5.1 Reproducibility

The replicate reproduced run A exactly: identical trace
(max \|ΔV\| = 0.000e+00 mV over the common window) and an **identical output
NWB digest** (`3bff2746…`). Run A's digest was in fact identical across three
separate executions — the initial build, the replicate, and the re-run after a
reporting fix — so execution is deterministic end-to-end, not merely
similar. **OBSERVED.**

---

## 6. Numerical validation against the recordings

All metrics use the validated Phase 2C/2E conventions verbatim
(`evaluate_finest_held_out.describe_trace` / `compare_traces`, 10 ms spike
windows, 1.5 ms refractory). NWB responses are stored in volts and are
converted to millivolts — the same conversion Phase 2C/2E apply; a unit test
now pins it, because a first pass of this phase compared in volts and was
caught and re-run.

Voltages below are in the **comparison frame** (junction-corrected, mV).
"Whole" spans the entire sweep; "in step" spans 1020–2020 ms.

### 6.1 The four comparisons

| Metric | A: stub / 38 | B: stub / 49 | C: trunc / 38 | D: trunc / 49 |
|---|---:|---:|---:|---:|
| Recorded in-step spikes | 12 | 1 | 12 | 1 |
| Simulated in-step spikes | **0** | **0** | **0** | **0** |
| Recorded first-spike latency (ms) | 39.75 | 104.045 | 39.75 | 104.045 |
| Simulated first-spike latency (ms) | — (no spike) | — | — | — |
| Recorded mean in-step ISI (ms) | 81.52 | — (single spike) | 81.52 | — |
| Recorded settled baseline (mV) | −80.87 | −81.05 | −80.87 | −81.05 |
| Simulated settled baseline (mV) | −61.90 | −61.90 | −63.32 | −63.32 |
| Baseline difference (mV) | **+18.97** | **+19.15** | **+17.54** | **+17.72** |
| Recorded plateau (mV) | −47.09 | −45.81 | −47.09 | −45.81 |
| Simulated plateau (mV) | −54.77 | −54.77 | −51.05 | −51.05 |
| Step RMSE (mV) | 11.797 | 8.884 | 9.474 | 5.700 |
| Whole-trace RMSE (mV) | 17.953 | 17.555 | 16.464 | 16.028 |
| In-step RMSE away from spikes (mV) | 7.610 | 8.540 | 4.661 | 5.220 |
| RMSE ±5 ms around recorded first spike (mV) | 23.379 | 25.488 | 21.029 | 23.054 |
| Correlation, whole trace | 0.950 | 0.987 | 0.952 | 0.990 |
| Correlation, in step | 0.274 | 0.564 | 0.277 | 0.530 |
| Share of in-step error near spikes | 0.684 | 0.095 | 0.816 | 0.178 |

Three reading notes that the table alone does not make obvious:

* **Whole-trace RMSE is dominated by the baseline offset, not the step.**
  Pre-step RMSE is 17.42–18.98 mV and post-step 17.20–18.77 mV in all four
  runs: the constant ≈18 mV rest mismatch contributes almost everywhere. The
  whole-trace number must never be quoted as "trajectory error" without this
  caveat — hence the explicit in-step column.
* **The correlations are inflated by the step silhouette.** A sub-threshold
  plateau correlates strongly with a spiking plateau's coarse shape
  (0.95–0.99 whole-trace) while missing every spike; the in-step correlations
  (0.27–0.56) are the honest size of the agreement.
* **Spike waveform metrics are undefined for the simulations, not zero.**
  With 0 simulated spikes there is no simulated amplitude, width, AHP or
  post-spike trajectory to compare. The recorded values are still reported:
  sweep 38 amplitude median 75.53 mV (n=14), half-max width 0.943 ms,
  AHP −51.37 mV, 10–90 % rise 0.485 ms; sweep 49 amplitude 72.94 mV,
  width 0.875 ms, AHP −51.91 mV, rise 0.410 ms, max dV/dt ≈ 244 V/s. None of
  these has a simulated counterpart in any branch.

### 6.2 Sweep 38 — plausibility bracket, not biological validation

Sweep 38 is **out-of-sample for the all-active model** (it fitted sweep 41) but
it is a COARSE response that Phase 2F identified as biologically anomalous for
this specimen, and it is the sweep the *perisomatic* model was fitted on. Two
statements must be kept separate:

1. **Numerical reproduction:** not achieved. 0 vs 12 in-step spikes; the first
   recorded spike (1059.75 ms, latency 39.75 ms) has no simulated event
   anywhere near it (simulated peak in the ±5 ms window: −54.71 mV stub /
   −50.15 mV truncated, vs recorded +31.66 mV).
2. **Bracket value:** sweep 38 shows what a strongly driven COARSE recording
   looks like — 12 in-step spikes, first ISI 39.25 ms (25.5 Hz) adapting to
   ~86–95 ms (10–12 Hz), mean in-step ISI 81.52 ms, mean rate 12 Hz, plus two
   post-step spikes at 5514.8 / 5522.0 ms. The all-active reconstructions sit
   7–13 mV above their own rest under the same command. The bracket confirms
   the direction of the mismatch under strong drive; it is not a
   representative physiological validation.

### 6.3 Sweep 49 — the primary held-out test

Sweep 49 was used to fit neither model. The recording contains exactly **one**
in-step spike at 1124.045 ms (latency 104.045 ms, amplitude 72.94 mV,
half-max width 0.875 ms, AHP −51.91 mV). The all-active prediction under both
branches contains **zero** spikes over the entire sweep, so the comparison
against the single observed spike is unambiguous: the model predicts no event
where the cell produces one, and its sub-threshold plateau (−54.77 mV stub /
−51.05 mV truncated) never enters the spike's voltage range. The ±5 ms window
around the observed spike has RMSE 25.49 mV (stub) / 23.05 mV (truncated)
against a simulated peak of −54.82 / −51.09 mV versus the recorded +30.31 mV.
**OBSERVED.**

The four FINEST repeats are **not** treated as four model predictions. They
are recording-repeatability context only: sweeps 49–52 each contain one
in-step spike with first latencies 104.0, 77.0, 93.2 and 92.5 ms — the
recording itself varies by ±27 ms in latency, which bounds how precisely any
model could be expected to place a single spike. **OBSERVED** (Phase 2E data).

### 6.4 Settling — the baseline difference is real, not a transient

The descriptor's `v_init` is −90 mV and every trace starts there. The settling
diagnostic shows the model completes its approach long before the step:

| Quantity | stub | truncated | recorded (38 / 49) |
|---|---:|---:|---:|
| Drift over last 20 ms of lead-in (mV) | 0.00037 | 0.00015 | −0.06 / −0.03 |
| Drift over full lead-in (mV) | +14.11 | +12.68 | −0.03 / −0.06 |
| Settled baseline, last 100 ms (mV) | −61.90 | −63.32 | −80.87 / −81.05 |

The ≈18 mV baseline difference is therefore a steady-state property of these
reconstructions (raw simulator rest: −75.90 mV stub, −77.33 mV truncated; the
written frame adds the +14 mV junction correction), not an artefact of
insufficient lead-in. **DERIVED.**

---

## 7. Branch sensitivity — stub versus truncated

A separate comparison, never pooled with the recording comparison and never
used to select a branch.

| Quantity | stub | truncated | Ratio / difference |
|---|---:|---:|---|
| Axon membrane area (µm²) | 188.496 | 59.609 | **3.16×** |
| Axon diameters (µm) | 1.0, 1.0 | 0.4037, 0.2288 | — |
| Axon attachment | `soma[0](0.5)` | `soma[0](1.0)` | — |
| Settled baseline, raw (mV) | −75.895 | −77.325 | 1.43 mV |
| Step response at +170 pA (mV) | 7.125 | **12.270** | **1.72×** |
| Input resistance (MΩ) | 41.9 | **72.2** | **1.72×** |
| Depolarisation above rest (mV) | 7.23 | 13.36 | 1.85× |
| In-step spikes (both sweeps) | 0 | 0 | identical |
| Step RMSE vs sweep 38 (mV) | 11.797 | 9.474 | −2.32 mV |
| Step RMSE vs sweep 49 (mV) | 8.884 | 5.700 | −3.18 mV |
| Correlation in step (38 / 49) | 0.274 / 0.564 | 0.277 / 0.530 | ≈ equal |
| Execution status | success, 0 failures | success, 0 failures | identical |
| Numerical stability | settled (0.0004 mV drift) | settled (0.0001 mV drift) | identical |

### 7.1 How far apart the two branches are

Measured on the pair of traces for the same stimulus (1 604 001 samples,
sweep 38; identical values for sweep 49 over the common window):

| Branch difference | Value |
|---|---:|
| RMS difference, in step (mV) | **3.724** |
| Max \|difference\|, in step (mV) | **4.708** |
| Mean difference, in step (mV) | −3.709 (stub below truncated) |
| RMS difference, pre-step (mV) | 1.462 |
| RMS difference, whole trace (mV) | 1.889 (sweep 38) / 2.014 (sweep 49) |
| In-step samples with \|difference\| ≥ 1 mV | 198 975 of 200 000 (99.5 %) |

The difference is a steady, stimulus-dependent offset, not a transient: the
branches differ by ~1.4 mV at rest and ~3.7–4.7 mV throughout the step, with
99.5 % of in-step samples more than 1 mV apart. **OBSERVED.**

### 7.2 Conclusion the brief asks for

The branch choice changes the sub-threshold prediction **materially**: a
1.72× change in input resistance and step response, and a 3.7 mV RMS / 4.7 mV
maximum change in the trajectory, from a section class that is 3–9 % of total
membrane area. Because `axon_type` was never published, **the unpublished axon
configuration is consequential for reproducibility**: two defensible readings
of the same published parameter set give measurably different models.

The one thing the branches agree on — zero spikes at +170 pA — is reported
**only for these two stimuli**. It is not evidence that the axon choice is
generally irrelevant: at a different stimulus amplitude, near the two
branches' differing rheobases, the spike-level predictions would be expected
to diverge as well. Neither branch is selected, ranked or preferred here; the
lower RMSE of the truncated branch against both recordings is a property of
its higher input resistance under this substitution morphology, and carries no
information about which branch Allen fitted.

---

## 8. Comparison with prior perisomatic results

The perisomatic model `473862496` was executed in Phase 2C (sweep 38) and
Phase 2E (sweeps 49–52) on the same specimen and recordings.

| Condition | Model | Spikes (rec / sim) | First latency rec / sim (ms) | RMSE whole / in step (mV) | Corr whole |
|---|---|---|---|---|---|
| Sweep 38 — **in-sample for perisomatic**, out-of-sample for all-active | perisomatic | 12 / 12 | 39.75 / 40.14 (Δ 0.385) | 4.456 / 11.126 | 0.931 |
| | all-active stub | 12 / 0 | 39.75 / — | 17.953 / 11.797 | 0.950 |
| | all-active truncated | 12 / 0 | 39.75 / — | 16.464 / 9.474 | 0.952 |
| Sweep 49 — **held out for both models** | perisomatic | 1 / 12 | 104.045 / 40.095 | 3.629 / 8.672 | 0.965 |
| | all-active stub | 1 / 0 | 104.045 / — | 17.555 / 8.884 | 0.987 |
| | all-active truncated | 1 / 0 | 104.045 / — | 16.028 / 5.700 | 0.990 |

**Does the all-active model improve on the perisomatic held-out mismatch?
No.** The two model classes miss sweep 49 in **opposite directions**: the
perisomatic model fires 12 spikes where the recording has one (and places its
first spike 64 ms early), while both all-active branches fire none where the
recording has one. On the whole-trace RMSE the all-active reconstructions are
**worse by roughly 4–5×** (16.0–17.6 mV vs 3.6 mV), though that gap is mostly
the ≈18 mV baseline offset; on the in-step RMSE the truncated branch is
modestly better (5.70 vs 8.67 mV) and the stub branch essentially equal
(8.88 vs 8.67 mV), while failing the actual prediction — the spike — that
both models were being asked to make.

Caveats that bound this comparison, all of them binding:

* **Different model classes and different parameter sets.** The perisomatic
  model was fitted on sweep 38 of this specimen; the all-active model was
  fitted on sweep 41. Sweep 49 is the only condition genuinely held out for
  both, and it is the only row above that is a like-for-like test.
* **Different execution assumptions.** The all-active runs use a substitute
  morphology (`674389901`) and a project-declared axon treatment; the
  perisomatic Phase 2C/2E runs used their own staged tree and the
  `truncated`-defaulted loader path of that phase. Neither execution
  reproduces the originally fitted model of its class.
* **Correlation and whole-trace RMSE reward a matching baseline**, which the
  perisomatic model happens to have and the all-active reconstructions do
  not; spike-count agreement is the metric that actually discriminates here,
  and on it both classes fail in different ways.

No conclusion about the relative biological fidelity of the two model classes
follows from this table. **OBSERVED**, interpretation bounded as stated.

---

## 9. Scientific interpretation

**1. Does either branch execute successfully and reproducibly?**
Yes, both. All four runs completed with zero failed checks (73/68/68/68), one
shared compiled mechanism library, and byte-identical inputs. Reproducibility
is exact: a second independent process reproduced run A's trace and output NWB
digest bit-for-bit, and run A's digest was stable across three separate
executions. The pipeline is deterministic; the predictions are not ambiguous
between runs, only between branches.

**2. Does either branch reproduce the sweep 38 response?**
No. The recording fires 12 in-step spikes (first at 39.75 ms, adapting from
25.5 Hz to ~10–12 Hz) plus two post-step spikes; both branches produce a flat
sub-threshold plateau 7–13 mV above rest and zero events. Numerical
reproduction was not achieved, and — given sweep 38's anomalous-COARSE
provenance — was never the right test of biological validity; its value was
as a plausibility bracket under strong drive, which the model also fails.

**3. Does either branch reproduce the sweep 49 held-out response?**
No. The recording contains a single spike at 1124.045 ms; both branches
contain none, and their plateaus never enter the spike's voltage range. The
primary held-out test therefore returns a clear negative for both
reconstructions.

**4. How sensitive are predictions to the unpublished axon configuration?**
Materially, at the sub-threshold level, and not at all at the spike level for
these two stimuli. The axon choice — a 3.16× difference in axonal membrane
area and a different attachment site — changes whole-cell input resistance by
1.72× (41.9 → 72.2 MΩ), the step response by 1.72× (7.13 → 12.27 mV), and the
trajectory by 3.7 mV RMS / 4.7 mV maximum, with 99.5 % of in-step samples more
than 1 mV apart. The unpublished `axon_type` is therefore consequential for
reproducibility, exactly as Phase 2G-A predicted. The shared failure (no
spikes) is reported only for these two stimuli and is not a general claim.

**5. Does the all-active model improve on the perisomatic held-out mismatch?**
No (§8). The perisomatic model over-predicted sweep 49 (12 spikes, first spike
64 ms early); the all-active reconstructions under-predict it (zero spikes).
Whole-trace error is 4–5× larger, driven by an ≈18 mV resting-potential
offset; in-step error is comparable or slightly smaller; the prediction that
matters — the single held-out spike — is missed by both classes, in opposite
directions. Given the different fitting sweeps, substitute morphology and
declared axon treatments, this is a comparison of two reconstructions, not of
two biological hypotheses.

**6. What can we conclude about biological detail from this experiment?**
Very little, and the little is negative. A model with 42 distributed genome
entries, 16 active mechanisms and a full dendritic tree, run with its
published parameters, is *less* excitable at +170 pA than the cell it was
fitted to — while resting 17–19 mV *more* depolarised. More compartments and
more conductances did not produce greater predictive accuracy on the held-out
condition. What the experiment does establish is narrow and useful: the
published parameter set is executable as issued (nothing needed repair, no
entry silently dropped), and the substitution morphology plus a declared axon
treatment yields a deterministic, well-behaved but non-firing reconstruction
at this stimulus. No biological mechanism is inferred from any of these
mismatches; a mismatch under a substituted morphology and a declared axon
treatment cannot support a mechanistic claim.

**7. What remains unidentifiable?**
The fitted reconstruction (`491771090`) — gone from the API, so the geometry
the 42 parameters were fitted against is unavailable and the
geometry–parameter pairing cannot be checked. The original `axon_type` —
never published, and now shown to matter at the 1.72× level. Consequently:
the originally fitted model's true resting potential and input resistance;
its true rheobase and the stimulus range over which the branch choice would
flip spike-level predictions; and any statement about which branch's numbers
are "the" Allen numbers. All **UNAVAILABLE**, as in Phase 2G-A.

---

## 10. Figures

All five figures live in the ignored directory `tmp/phase2g_b_figures/`. Every
title and legend names the stimulus and the axon branch; no figure plots a
pooled or averaged branch.

| File | Content |
|---|---|
| `fig1_sweep38_recorded_and_branches.png` | Sweep 38: recorded trace (12 spikes) with the stub and truncated predictions plotted separately, full sweep plus a 250 ms zoom on the step onset |
| `fig2_sweep49_recorded_and_branches.png` | Sweep 49: recorded trace (1 spike) with both branches separately, same two-panel layout |
| `fig3_branch_difference.png` | V_stub − V_truncated for each stimulus, one panel each, with the in-step RMS and maximum annotated |
| `fig4_sweep49_spike_window.png` | The single observed sweep 49 spike (1100–1160 ms) against both branches' trajectories at the same time, with each branch's spike count in the title |
| `fig5_metric_comparison.png` | Four separate panels (in-step RMSE, step response, settled baseline, input resistance), four individual bars per panel — never averaged |

---

## 11. Deliverables and reproducibility

* **Executor:** `scripts/validate_all_active_execution.py` — one (branch,
  sweep) pair per process; verifies provenance, manifest, loader, mechanisms,
  junction convention and the 42-entry genome readback before, during and
  after execution; writes `run_summary.json`, the trace npz, and per-run logs.
* **Branch analysis:** `scripts/analyse_all_active_branches.py` — loads the
  four run directories, asserts the quartet's consistency (including the
  determinism replicate), builds the recording, branch and difference tables,
  writes `phase2g_b_summary.json` and the five figures.
* **Tests:** `tests/test_all_active_execution_validation.py` — 25 tests
  covering the frozen run plan, the excluded fitting sweep, the mandated
  model-claim sentence, the checker arithmetic, the settling diagnostic, the
  step-response / input-resistance arithmetic (including the mV and MΩ unit
  conversions this phase once got wrong), branch-difference antisymmetry, and
  the quartet consistency checks (a failed run, a duplicate output or two
  indistinguishable branches are all reported as failures). Full suite:
  **221 passed**.
* **Machine-readable summaries:** `tmp/phase2g_b_results/` (ignored) — the
  four `run_summary.json` files, their `command.txt` lines, the replicate's
  summary, and the aggregated `phase2g_b_summary.json`.
* **Figures:** `tmp/phase2g_b_figures/` (ignored).
* Nothing generated — no NWB, no compiled object, no DLL, no raw Allen asset —
  is tracked by git; `tmp/` and `*.nwb` are ignored, and the executed tree
  lives under `~/incm_phase2g_b/` outside the repository entirely.

---

## 12. Limitations and next steps

**Limitations.**

1. Two stimuli, one amplitude. Everything in §6–§8 describes +170 pA only;
   the branch agreement on "no spikes" cannot be extrapolated to other
   amplitudes.
2. Substitute morphology and declared axon treatment. Every number is a
   property of the reconstruction named in the header sentence, not of
   Allen's fitted model.
3. Sweep 38's anomalous COARSE provenance bounds its evidential value to a
   plausibility bracket.
4. The recorded FINEST repeats vary by ±27 ms in first-spike latency, so
   single-spike timing agreement could not have been assessed more precisely
   than that even with a firing model.
5. Spike waveform metrics (amplitude, width, AHP, post-spike trajectory) have
   no simulated counterparts in any branch; they are reported for the
   recordings only.

**Next steps.** These are proposals, not actions taken in this phase.

1. Map each branch's rheobase descriptively (a *measurement* of the two
   reconstructions, never a refit) to locate where the branch choice begins
   to change spike-level predictions. Requires a separate instruction; no
   additional sweeps were executed here.
2. Report the ≈18 mV resting-potential offset as a standing discrepancy of
   the substitute-morphology reconstruction, to be carried into any future
   comparison rather than silently normalised away.
3. Keep both branches in every future table that quotes this model; the
   1.72× input-resistance gap is the reproducibility cost of the unpublished
   `axon_type` and should not be collapsed to a single number.

Per the instruction for this task, no FHN work and no Phase 3 work was
started.

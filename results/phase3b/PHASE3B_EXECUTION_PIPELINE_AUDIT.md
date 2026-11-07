# PHASE 3B — EXECUTION PIPELINE AUDIT

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3B — Out-of-Sample Held-Out Evaluation  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  
**Execution Runner:** [`scripts/run_representative_perisomatic.py`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/scripts/run_representative_perisomatic.py)  
**Test Suite:** [`tests/test_heldout_pipeline.py`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/tests/test_heldout_pipeline.py)  

---

## 1. Executive Summary

To prepare for genuine out-of-sample held-out evaluation across 109 sweeps in the four representative perisomatic models, the execution runner [`scripts/run_representative_perisomatic.py`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/scripts/run_representative_perisomatic.py) was enhanced and hardened against experimental edge cases and scientific boundary violations.

All 346 unit and regression tests pass (100% pass rate), including 6 new tests explicitly enforcing calibration sweep rejection, held-out provenance disjointness, condition grouping, and stimulus step segmentation.

---

## 2. Hardening and Validation Details

### 2.1 Calibration Sweep Rejection Guard (Audit Gate 3 Enforcement)
- **Scientific Rule:** Calibration fitting sweeps must never be evaluated as held-out sweeps.
- **Implementation:**
  ```python
  if condition_type == "held_out" and sweep == meta["calibration_sweep"]:
      raise ValueError(
          f"REJECTED: Sweep {sweep} is the published calibration fitting sweep "
          f"for specimen {specimen_id}. It cannot be executed under condition_type='held_out'."
      )
  ```
- **Validation:** Tested across all four specimens in `test_runner_calibration_rejection_in_heldout_mode`. Any attempt to execute the fitting sweep under held-out evaluation immediately halts execution with an explicit error.

### 2.2 Stimulus Pulse Segmentation Hardening
- **Discovered Nuance:** In subthreshold depolarizing sweeps (e.g., $+10\text{ pA}$ or $+30\text{ pA}$), an initial hyperpolarizing test pulse (typically $-100\text{ pA}$, $20\text{ ms}$) is present at $t \approx 100\text{ ms}$ before the main $1000\text{ ms}$ step at $t \approx 1020\text{ ms}$. Sorting pulses purely by absolute amplitude mistakenly identified the test pulse as the stimulus.
- **Solution:** Segments are filtered by duration (`duration_ms > 100.0`), isolating the primary long step regardless of step amplitude:
  ```python
  segments = _stimulus_segments(stim_rec_a, dt_ms)
  long_segments = [s for s in segments if s["duration_ms"] > 100.0]
  step = long_segments[0] if long_segments else (segments[0] if segments else None)
  ```
- **Validation:** Tested with synthetic subthreshold pulse trains in `test_stimulus_segmentation_filters_test_pulse`, confirming exact selection of the $1000\text{ ms}$ step ($+20.0\text{ pA}$, onset $1020\text{ ms}$).

### 2.3 Batch Execution and Provenance Architecture
- **Command Line Interface:**
  - `--specimen-id <int>`: Required specimen ID.
  - `--sweeps all_heldout`: Automatically loads all 109 held-out sweeps from [`results/phase3b/heldout_sweeps.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_sweeps.csv) for that specimen.
  - `--sweeps <int,int,...>`: Accepts arbitrary comma-separated sweep lists.
  - `--condition-type auto|calibration|held_out`: Enforces mode.
  - `--save-traces`: Flag to save compressed `.npz` files (default disabled to prevent disk bloat; git-ignored).
- **Directory Hierarchy:**
  ```
  results/phase3b/heldout/<specimen_id>/
  ├── sweep_<sweep_id>/
  │   ├── summary.json
  │   ├── overlay.png
  │   └── runner.log
  ├── aggregated_metrics.csv
  └── failures.json (if any failures occur)
  ```
- **Summary Schema:**
  Each `summary.json` records:
  - Specimen ID, Model ID, Fit File ID, NWB File ID, Morphology SWC.
  - Sweep number, sweep ID, protocol family, condition type.
  - Stimulus metrics: amplitude (pA), onset (ms), duration (ms), sampling rate (kHz).
  - Waveform metrics: RMSE overall (mV), RMSE baseline, RMSE step, RMSE post-stimulus, MAE (mV), Pearson correlation $r$.
  - Spike metrics: recorded spike count, simulated spike count, spike count delta, mean firing rate (Hz), first-spike latency (ms), latency delta, mean ISI (ms), ISI adaptation ratio.
  - Resting potential: baseline recorded (mV), baseline simulated (mV), baseline delta (mV).

---

## 3. Test Suite Status

| Test Suite | Tests Passed | Status |
|---|---:|---|
| `tests/test_all_active_excitability.py` | 30 | PASS |
| `tests/test_all_active_execution_validation.py` | 25 | PASS |
| `tests/test_allen_inventory_units.py` | 50 | PASS |
| `tests/test_audit_all_active_readiness.py` | 33 | PASS |
| `tests/test_excitability_accommodation.py` | 67 | PASS |
| `tests/test_four_population_audit.py` | 53 | PASS |
| `tests/test_four_representative_pipeline.py` | 5 | PASS |
| `tests/test_heldout_pipeline.py` | 6 | PASS |
| `tests/test_inventory_outputs.py` | 46 | PASS |
| `tests/test_phase0c_selected_readiness.py` | 31 | PASS |
| **Total Suite** | **346** | **100% PASS** |

---

## 4. Audit Gate 3 Verdict

> **AUDIT GATE 3: PASSED**
>
> 1. The execution runner supports batch execution across all 109 held-out sweeps.
> 2. Calibration sweeps are strictly protected from held-out evaluation via hard programmatic assertions.
> 3. Stimulus pulse segmentation robustly isolates long depolarizing steps across the entire dynamic range (-110 pA to +470 pA).
> 4. Full test suite (346 tests) passes cleanly without regressions.
> 5. Ready to proceed to Phase 4 (Controlled Batch Held-Out Simulations).


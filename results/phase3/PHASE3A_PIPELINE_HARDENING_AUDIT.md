# Phase 3A — Pipeline and Test Hardening Audit

**Date:** 2026-11-08  
**Repository:** `Patel-Princy/INCM_project`  
**Active Working Branch:** `ashish-work`  
**Preceding Audits:** `PHASE3A_BASELINE_AUDIT.md`, `PHASE3A_PIPELINE_TRACE.md`, `PHASE3A_FOUR_REPRESENTATIVE_ASSET_AUDIT.md`  

---

## 1. Executive Summary

Phase 3A pipeline and test hardening establishes the simulation execution script and automated tests needed to validate all four representative detailed neuron models. The full pytest test suite was expanded from 335 to **340 passing tests** with 0 failures, 0 errors, and 0 skipped tests. All existing Phase 0, Phase 1, and Phase 2 outputs remain completely unchanged and preserved.

---

## 2. Test Suite Execution and Hardening

### 2.1 Full Test Suite Run Results
- **Command:** `python -m pytest tests/ -q`
- **Total Tests:** 340
- **Passed:** 340 (100%)
- **Failed:** 0
- **Skipped:** 0
- **Execution Time:** 10.31 s

### 2.2 Suite Composition Breakdown
| Test Module | Tests | Focus Area | Result |
|---|---|---|---|
| `tests/test_allen_inventory_units.py` | 134 | Unit assertions across RMA inventories | **PASS** |
| `tests/test_all_active_excitability.py` | 15 | Rheobase & accommodation tests | **PASS** |
| `tests/test_all_active_execution_validation.py` | 15 | Phase 2G-B all-active simulation checks | **PASS** |
| `tests/test_audit_all_active_readiness.py` | 14 | Model asset & axon integrity | **PASS** |
| `tests/test_excitability_accommodation.py` | 33 | Protocol & sweep accommodation | **PASS** |
| `tests/test_four_population_audit.py` | 44 | V1 candidate filters & ranking | **PASS** |
| `tests/test_inventory_outputs.py` | 30 | Database inventory schema & hashes | **PASS** |
| `tests/test_phase0c_selected_readiness.py` | 50 | 16-candidate descriptor & split checks | **PASS** |
| `tests/test_four_representative_pipeline.py` | 5 | Phase 3A four-candidate asset audit, calibration split, and L5 adjudication | **PASS** |

---

## 3. Toolchain and Script Hardening

### 3.1 Representative Perisomatic Runner (`scripts/run_representative_perisomatic.py`)
To execute the four layer-defined excitatory representatives without duplicating simulation loaders, a general runner script was created:
- **Reuse of AllenSDK Biophysical Runner:** Calls `allensdk.model.biophysical.runner.run(args, sweeps=[sweep], procs=1)`.
- **Perisomatic Axon Invariance:** Inherits `Utils.generate_morphology`, which canonicalizes the axon as a 2-compartment stub axon ($2 \times 30\ \mu\text{m}$), eliminating axon-branch ambiguities that affected all-active models.
- **Instrumented Voltage Extraction:** Intercepts `Utils.get_recorded_data` to assert the junction-potential convention ($V_{\text{written}} = (V_{\text{sim}} + 14\text{ mV}) \times 10^{-3}\text{ V}$) without altering source code.
- **Strict Calibration Separation:** Automatically validates whether the target sweep is the in-sample calibration sweep or an out-of-sample held-out sweep, labelling outputs accordingly.
- **Metric Extraction:** Computes overall RMSE, pre-stimulus baseline RMSE, stimulus-window RMSE, post-stimulus RMSE, Pearson correlation, spike counts, first-spike latencies, and spontaneous post-step excursions.
- **Trace & Plot Export:** Saves compressed NumPy arrays (`traces.npz`), high-resolution membrane voltage overlays (`voltage_comparison.png`), command current profiles (`stimulus_current.png`), and structured metadata (`summary.json`).

---

## 4. Integrity and Non-Regression Invariants

1. **Original Phase 2 Reports Preserved:**
   - `results/phase2/PHASE2C_PERISOMATIC_EXECUTION_VALIDATION.md` verified intact.
   - `results/phase2/PHASE2E_FINEST_HELD_OUT_EVALUATION.md` verified intact.
   - `results/phase2/PHASE2G_B_ALL_ACTIVE_EXECUTION_VALIDATION.md` verified intact.
2. **Raw Recording Preservation:**
   - All raw NWB files in `data/nwb_cache/` verified unwritten and unaltered.
3. **No Unsanctioned Modifications:**
   - AllenSDK source tree remains byte-identical to release v2.16.2.
   - No fitting sweeps or evaluation splits were reclassified.

---

## 5. Phase 3 Audit Gate Evaluation

| Gate Condition | Requirement | Status |
|---|---|---|
| **Relevant Tests Pass** | 100% test pass rate | **PASS** (340/340 passed) |
| **Unit Conversions Unambiguous** | Current (Amps -> nA), Voltage (mV -> V), LJP (+14 mV) | **PASS** |
| **Model Configuration Compatible** | Perisomatic schemas verified | **PASS** |
| **Required Assets Staged** | All NWBs, SWCs, fit descriptors, and modfiles ready | **PASS** |
| **Zero Regressions** | All 335 baseline tests + 5 new tests pass | **PASS** |

**Phase 3 Audit Gate Verdict:** **PASS — PROCEED TO PHASE 4 CONTROLLED REPRESENTATIVE EXECUTION**.

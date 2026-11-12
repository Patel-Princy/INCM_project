# Phase 5F — Final Research QA and Provenance Report

**Date:** November 10, 2026  
**Author:** Ashish (INCM Project)  
**Branch:** `ashish-work`  
**Base Commit:** `5509ddd`  
**Repository:** `Patel-Princy/INCM_project`  

---

## 1. Scope and Objective

This report formally documents the quality assurance, provenance reconciliations, and scientific integrity verifications performed during Phase 5F for:
- `results/phase5/FINAL_RESEARCH_REPORT.md`
- `results/phase5/PHASE5F_L5_L6A_LITERATURE_REVIEW.md`
- `results/phase5/PHASE5F_LITERATURE_EVIDENCE_MATRIX.md`
- `results/phase5/PHASE5F_REFERENCE_VERIFICATION.md`

This document satisfies the explicit cross-reference in Section 13 (Methodological Caveats, Item 15) of the final research manuscript.

---

## 2. Inventory of Scientific Provenance Corrections

In Phase 5F, six specific empirical and bibliographic corrections were reconciled against the frozen project artifacts. None of these corrections altered any frozen data, fitted parameters, simulation outputs, or test assertions.

### 2.1 Resting Potential Baseline Reconciliation (Table 1)
- **Population B (L2/3):** Table 1 previously reported $-78.96\text{ mV}$ (taken from the external Allen `v_rest` feature API). This was corrected to **$-75.90\text{ mV}$**, matching the pre-stimulus baseline of the calibrated experimental sweep (`fhn_calibration_metrics.csv` and `fhn_fitted_parameters.csv`).
- **Population C (L5):** Table 1 previously reported $-68.62\text{ mV}$ (Allen `v_rest`). This was corrected to **$-69.34\text{ mV}$**, matching the pre-stimulus baseline of calibration sweep 51.
- **Scientific Impact:** Ensures complete consistency between the biological characterization table and the zero-current equilibrium $V_{\mathrm{rest}}$ parameter in the calibrated dynamical models.

### 2.2 Population D First-Spike Latency Reconciliation
- **Prior Statement:** Earlier working notes suggested Population D exhibited latency "$> 1000\text{ ms}$ near threshold".
- **Empirical Audit:** Inspection of the frozen spike timestamps from held-out sweep evaluations revealed that for the near-threshold sweep (+210 pA, Sweep 40, COARSE protocol), the biological neuron fired **5 spikes**, with the first action potential occurring at **$113.82\text{ ms}$** after stimulus onset ($t = 1133.82\text{ ms}$ absolute timestamp in the $[1020, 2020]\text{ ms}$ pulse window). Subsequent sweeps exhibit monotonically shortening latency:
  - $+230\text{ pA}$: $72.88\text{ ms}$ (10 spikes)
  - $+250\text{ pA}$: $57.95\text{ ms}$ (13 spikes, calibration sweep)
  - $+270\text{ pA}$: $47.06\text{ ms}$ (17 spikes)
  - $+290\text{ pA}$: $41.74\text{ ms}$ (19 spikes)
  - $+310\text{ pA}$: $37.35\text{ ms}$ (21 spikes)
  - $+330\text{ pA}$: $30.59\text{ ms}$ (24 spikes)
  - $+350\text{ pA}$: $27.37\text{ ms}$ (27 spikes)
- **Corrected Statement:** Pop D displays a graded first-spike latency from $113.82\text{ ms}$ down to $27.37\text{ ms}$. In FINEST sweeps at $+240\text{ pA}$ (Sweeps 52–54), single spikes occurred at $119.67$, $109.81$, and $180.02\text{ ms}$. The claim of "$> 1000\text{ ms}$" was an artifact of confusing the stimulus pulse window with latency and has been eliminated.

### 2.3 Input-Resistance Calibration Target Qualification
- **Observation:** FHN subthreshold charging tracks the exponential time course ($r^2 \ge 0.996$ on hyperpolarizing steps) but under-predicts steady-state voltage deflections by approximately threefold.
- **Root-Cause Analysis:** The calibration pipeline targeted an apparent $R_{\mathrm{in}}$ estimated across an initial 10 ms test pulse (apparent $R_{\mathrm{in}} \in [31.3, 80.3]\text{ M}\Omega$). Because membrane time constants $\tau_m$ are $14\text{--}21\text{ ms}$, the 10 ms pulse measures the pre-steady-state charging transient. On full 1000 ms hyperpolarizing steps, steady-state $R_{\mathrm{in}}$ is $90.6\text{--}217.5\text{ M}\Omega$ (matching Allen steady-state metrics).
- **Documentation:** Caveat 13 and Section 8 were updated to clarify this definition, explaining the distinction between dynamic charging fidelity ($r^2$) and steady-state gain ($R^2$).

### 2.4 Hyperpolarization-Activated Inward Sag
- **Observation:** Biological neurons exhibit $0.63\text{--}1.86\text{ mV}$ sag at $-110\text{ pA}$ (largest in Population D).
- **Model Fact:** FHN is a two-variable planar polynomial system without an $I_h$ pacemaker conductance.
- **Documentation:** The manuscript explicitly documents that the absence of sag in FHN is a structural consequence of dimensionality reduction.

### 2.5 Reclassification of Delay Mechanism to Hypothesis
- **Prior Claim:** Delayed spike firing in Layer 6a was previously noted as being driven by "Kv4/Kv1.4 per literature".
- **Literature Reconciliation:** Exhaustive search across primary mouse V1 literature did not identify empirical pharmacological or biophysical demonstration linking Ntsr1-Cre L6a CT neurons specifically to Kv4/Kv1.4 currents.
- **Correction:** The mechanism is strictly labeled as an unverified hypothesis (`[H]`).

### 2.6 Reference Verification and Metadata Fixes
- Crossref REST API verification identified that Teeter et al. (2018) was incorrectly titled with the insertion "mouse and human cortical". This was restored to the exact published title: *"Generalized leaky integrate-and-fire models classify multiple neuron types"*.
- Ambiguous Allen Institute white-paper citations were resolved to explicit URLs and dated `n.d.`.

---

## 3. Table 3 Parameter Integrity Check

All 32 FHN parameters in Table 3 of `FINAL_RESEARCH_REPORT.md` were audited against `results/phase4b/fhn_fitted_parameters.csv`:

| Pop | Layer | Parameter | Markdown Value | Authoritative CSV Value | Absolute Difference | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| A | L4 | $C_m$ | 133.6293 | 133.6293 | 0.0000 | **MATCH** |
| A | L4 | $g_L$ | 3.2394 | 3.2394 | 0.0000 | **MATCH** |
| A | L4 | $V_{\mathrm{rest}}$ | -73.7340 | -73.7340 | 0.0000 | **MATCH** |
| A | L4 | $V_{\mathrm{th}}$ | -69.4172 | -69.4172 | 0.0000 | **MATCH** |
| A | L4 | $V_{\mathrm{peak}}$ | 52.0920 | 52.0920 | 0.0000 | **MATCH** |
| A | L4 | $k_v$ | 0.003983 | 0.003983 | 0.0000 | **MATCH** |
| A | L4 | $\tau_w$ | 18.1072 | 18.1072 | 0.0000 | **MATCH** |
| A | L4 | $a_w$ | 17.1751 | 17.1751 | 0.0000 | **MATCH** |
| B | L2/3 | $C_m$ | 38.2489 | 38.2489 | 0.0000 | **MATCH** |
| B | L2/3 | $g_L$ | 0.8571 | 0.8571 | 0.0000 | **MATCH** |
| B | L2/3 | $V_{\mathrm{rest}}$ | -75.9007 | -75.9007 | 0.0000 | **MATCH** |
| B | L2/3 | $V_{\mathrm{th}}$ | -67.6462 | -67.6462 | 0.0000 | **MATCH** |
| B | L2/3 | $V_{\mathrm{peak}}$ | 64.9531 | 64.9531 | 0.0000 | **MATCH** |
| B | L2/3 | $k_v$ | 0.001790 | 0.001790 | 0.0000 | **MATCH** |
| B | L2/3 | $\tau_w$ | 6.8893 | 6.8893 | 0.0000 | **MATCH** |
| B | L2/3 | $a_w$ | 9.7725 | 9.7725 | 0.0000 | **MATCH** |
| C | L5 | $C_m$ | 138.9047 | 138.9047 | 0.0000 | **MATCH** |
| C | L5 | $g_L$ | 0.7416 | 0.7416 | 0.0000 | **MATCH** |
| C | L5 | $V_{\mathrm{rest}}$ | -69.3360 | -69.3360 | 0.0000 | **MATCH** |
| C | L5 | $V_{\mathrm{th}}$ | -48.2778 | -48.2778 | 0.0000 | **MATCH** |
| C | L5 | $V_{\mathrm{peak}}$ | 53.7525 | 53.7525 | 0.0000 | **MATCH** |
| C | L5 | $k_v$ | 0.004763 | 0.004763 | 0.0000 | **MATCH** |
| C | L5 | $\tau_w$ | 18.8946 | 18.8946 | 0.0000 | **MATCH** |
| C | L5 | $a_w$ | 18.8666 | 18.8666 | 0.0000 | **MATCH** |
| D | L6a | $C_m$ | 206.5891 | 206.5891 | 0.0000 | **MATCH** |
| D | L6a | $g_L$ | 0.9128 | 0.9128 | 0.0000 | **MATCH** |
| D | L6a | $V_{\mathrm{rest}}$ | -75.7102 | -75.7102 | 0.0000 | **MATCH** |
| D | L6a | $V_{\mathrm{th}}$ | -57.4868 | -57.4868 | 0.0000 | **MATCH** |
| D | L6a | $V_{\mathrm{peak}}$ | 64.9985 | 64.9985 | 0.0000 | **MATCH** |
| D | L6a | $k_v$ | 0.002577 | 0.002577 | 0.0000 | **MATCH** |
| D | L6a | $\tau_w$ | 38.8553 | 38.8553 | 0.0000 | **MATCH** |
| D | L6a | $a_w$ | 11.7242 | 11.7242 | 0.0000 | **MATCH** |

**Result:** 32 / 32 parameters match authoritative records with 0.0000 error.

---

## 4. Test Suite Execution Summary

- **Test Target:** `tests/test_fhn_calibration_audit.py`
- **Execution Command:** `python -m pytest tests/test_fhn_calibration_audit.py -v`
- **Output:**
  ```text
  collected 28 items
  28 passed in 47.45s (100% pass rate)
  ```
- **Assertions Verified:**
  - Exact spike count reproduction across all 4 populations.
  - Latency matching within numerical tolerances.
  - Calibration loss parity against frozen records.
  - Low loss vs. high RMSE mathematical mechanism verification.
  - Population D Pareto frontier trade-offs.
  - Jacobian stability and resting conductance physics.

---

## 5. Conclusion

All provenance corrections, Table 3 parameters, scientific claims, and regression tests have been audited and verified. The manuscript and its companion literature documents are fully synchronized, scientifically defensible, and ready for publication-grade export.


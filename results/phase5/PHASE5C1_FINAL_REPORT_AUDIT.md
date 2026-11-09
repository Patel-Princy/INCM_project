# INCM Phase 5C.1 — Final Research Report Factual and Scientific Audit

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Authoritative Milestone:** Phase 5C.1 Final Report Scientific Audit  
**Date:** November 2026  
**Audited Artifacts:**
- [`results/phase5/FINAL_RESEARCH_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/FINAL_RESEARCH_REPORT.md)
- [`results/phase5/PHASE5C_REPORT_VERIFICATION.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C_REPORT_VERIFICATION.md)

---

## 1. Executive Audit Overview

This document reports the independent factual, numerical, and scientific audit of the authoritative final research report (`results/phase5/FINAL_RESEARCH_REPORT.md`) and its accompanying verification record (`results/phase5/PHASE5C_REPORT_VERIFICATION.md`).

The audit cross-referenced every empirical claim, mathematical formula, parameter count, reconstruction assignment, and bifurcation interval against the original serialized evidence files from Phases 0 through 4C.3.1. 

### Key Audit Outcomes
1. **Population A Late-Step Firing Counts & Cessation:** Identified and resolved a conflation in the draft report that merged +410 pA and +430 pA data. Established the exact per-sweep recorded versus detailed spike counts, cessation timings, and step boundaries across Sweeps 49 (calibration), 50, 51, and 52.
2. **Morphology Reconstruction Provenance:** Replaced the erroneous statement that detailed models for Populations A, C, and D used substitute morphologies. Confirmed via `cell_inventory.csv`, `model_inventory.csv`, and SWC header inspection that all four frozen representative perisomatic models utilize morphological reconstructions derived directly from their respective recorded donor specimens. Traced the root cause of the substitute morphology confusion to exploratory candidate `382982932` in Phase 2.
3. **FHN Parameter Count Reconciled:** Reconciled conflicting text references (7 vs. 8 parameters). Confirmed that the dimensional FHN model has 2 dynamical state variables ($V, w$), 1 time-dependent input ($I_{\mathrm{inj}}$), and **8 dimensional biophysical parameters** ($C_m, g_L, V_{\mathrm{rest}}, V_{\mathrm{th}}, V_{\mathrm{peak}}, k_v, \tau_w, a_w$). Corrected all text occurrences to reflect 8 parameters.
4. **Model-Reduction Hierarchy Qualified:** Removed overgeneralized claims asserting that 2D models cannot mathematically represent adaptation or delayed onset. Qualified all statements to apply specifically to the tested autonomous two-variable cubic FHN formulation with linear recovery and its calibrated parameter subspace.
5. **F–I Rate Scaling and Saturation Characterized:** Clarified the exact per-sweep F–I mappings. Detailed models reproduce monotonic firing rate increases once suprathreshold; biological cells exhibit plateaus (e.g., Pop A at +370 and +390 pA both firing 9 spikes) and cessation/depolarization block at high currents; FHN models do not exhibit continuous monotonic F–I rate expansion, but instead rapidly saturate in limit cycle frequency (e.g., Pop A is flat at 9 spikes from +270 to +410 pA; Pop B saturates at 17 spikes before collapsing).
6. **Factual Baseline Consistency Confirmed:** Verified that all baseline metrics (109 held-out sweeps, confusion matrices, open bistability intervals, biological sag, 23 qualifying adaptation sweeps, and provisional AP upstroke velocities) remain 100% consistent with prior audited phases.
7. **Zero Violations of Frozen Boundaries:** No new simulations or calibrations were run, historical precursor files remain untouched bit-for-bit, and all working tree changes remain strictly uncommitted on branch `ashish-work`.

---

## 2. Issue 1: Population A High-Current Spike Counts and Cessation

### 2.1 Audit Findings and Conflation Diagnosis
In the initial draft of `FINAL_RESEARCH_REPORT.md` (§9.1 and §13 item 5), the text stated:
> *"At high currents (+410 pA), it severely overcounts spikes (48 spikes vs. 12 recorded) due to the absence of late-step spike cessation."*

An inspection of `results/phase3b/heldout/484564503/aggregated_metrics.csv` and `results/phase4c/fhn_detailed_comparison.csv` revealed that this statement conflated two separate high-current sweeps:
- **Sweep 51 (+410 pA, COARSE):** Biological cell fired **13 spikes**, while the detailed model fired **39 spikes**.
- **Sweep 52 (+430 pA, COARSE):** Biological cell fired **12 spikes**, while the detailed model fired **48 spikes**.

### 2.2 Authoritative High-Current Per-Sweep Evidence
The table below documents the exact per-sweep stimulus amplitudes, recorded versus detailed spike counts, onset latencies, and cessation timings for Population A (Specimen `484564503`, Layer 4 spiny neuron). 

In all sweeps, current-clamp steps have a duration of $1000.0\text{ ms}$, starting at $t_{\mathrm{onset}} = 1020.0\text{ ms}$ and terminating at $t_{\mathrm{offset}} = 2020.0\text{ ms}$:

| Sweep ID | Protocol | Amplitude (pA) | Spikes Rec | Spikes Det | Spikes FHN | Rec First Spike (ms) | Rec Last Spike (ms) | Rec Firing Duration (ms) | Rec Late-Step Silence (ms) | Det Last Spike (ms) | Firing Pattern / Cessation Dynamics |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **49** | COARSE | $+370.0$ | **9** | **9** | **9** | $1040.24$ | $1348.65$ | $328.65$ | $671.35$ | $1978.20$ | **Primary Calibration Sweep:** All 3 models match 9 spikes. |
| **50** | COARSE | $+390.0$ | **9** | **27** | **9** | $1039.43$ | $1335.27$ | $315.27$ | $684.73$ | $1971.36$ | **Early Cessation:** Rec cell silent for final $68.5\%$ of step. |
| **51** | COARSE | $+410.0$ | **13** | **39** | **9** | $1034.54$ | $1522.03$ | $502.03$ | $497.97$ | $1992.51$ | **Mid-Step Cessation:** Rec cell silent for final $49.8\%$ of step. |
| **52** | COARSE | $+430.0$ | **12** | **48** | **8** | $1036.79$ | $1498.34$ | $478.34$ | $521.66$ | $2003.26$ | **Depolarization Block / Cessation:** Rec count drops to 12. |

### 2.3 Key Scientific Takeaways
1. **Premature Cessation in Biology:** Across all strong depolarizing steps (+370 to +430 pA), the biological neuron ceased firing approximately one-third to one-half of the way through the 1000 ms pulse (firing duration $315.27\text{--}502.03\text{ ms}$; silent for the final $497.97\text{--}684.73\text{ ms}$).
2. **Failure of Detailed Model to Replicate Cessation:** The detailed multi-compartment model continued firing repetitively throughout the entire 1000 ms step across all sweeps (last spike at $1971.36\text{--}2003.26\text{ ms}$). This explains why the detailed model's spike count progressively diverged from the biological recording at high currents (27 vs. 9 at +390 pA, 39 vs. 13 at +410 pA, and 48 vs. 12 at +430 pA).
3. **In-Place Report Corrections:** Both §9.1 and §13 (Caveat 5) of `FINAL_RESEARCH_REPORT.md` were corrected to present the exact per-sweep counts (Sweep 51: 13 vs. 39; Sweep 52: 12 vs. 48) and explicit cessation timings.

---

## 3. Issue 2: Morphology Reconstruction Assignments and Provenance

### 3.1 Audit Findings and Source Verification
The initial draft of `FINAL_RESEARCH_REPORT.md` (§5.2 and §13 item 3) stated:
> *"specimens 484564503 (Pop A), 471129934 (Pop C), and 471786879 (Pop D) utilized substitute 3D morphological reconstructions... Specimen 318808427 (Pop B) possessed an original reconstructed morphology."*

To audit this claim, we cross-referenced:
- `data/metadata/cell_inventory.csv` (specimen metadata, `reconstruction_id`, and `specimen_name`)
- `data/metadata/model_inventory.csv` (model metadata, `neuron_reconstruction_id`)
- Local cached SWC reconstruction files in `tmp/morphology_cache/`
- ASCII header comments inside each SWC file.

### 3.2 Verified Morphological Provenance Table
The audit revealed that **all four representative perisomatic models utilize morphological reconstructions from their own histological donor experiments**:

| Population | Layer | Specimen ID | Model ID | Specimen Reconstruction ID (`cell_inventory.csv`) | Model Reconstruction ID (`model_inventory.csv`) | SWC File Name | SWC Header Donor Experiment | Matching Specimen Name in Inventory | Reconstruction Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **L4** | `484564503` | `485591776` | `491459182.0` | `491459182.0` | `484564503.swc` | `Rorb-IRES2-Cre-D_Ai14-201965.05.01.01_RD_DS_final.swc...` | `Rorb-IRES2-Cre-D;Ai14-201965.05.01.01` | **Original Specimen Donor** |
| **B** | **L2/3** | `318808427` | `473863035` | `491119754.0` | `491119754.0` | `318808427.swc` | `Nr5a1-Cre_Ai14_IVSCC_-169250.03.02.01_471087815_p...` | `Nr5a1-Cre;Ai14-169250.03.02.01` | **Original Specimen Donor** |
| **C** | **L5** | `471129934` | `480624414` | `495335491.0` | `495335491.0` | `471129934.swc` | `Rbp4-Cre_KL100_Ai14_IVSCC_-180747.06.01.01_485996858_p...` | `Rbp4-Cre_KL100;Ai14-180747.06.01.01` | **Original Specimen Donor** |
| **D** | **L6a** | `471786879` | `480632594` | `491392868.0` | `491392868.0` | `471786879.swc` | `Ntsr1-Cre_Ai14_GSL_-181184.05.02.01_ApicalBasalFix...` | `Ntsr1-Cre;Ai14-181184.05.02.01` | **Original Specimen Donor** |

*(Note on Population D: `PHASE3A_FOUR_REPRESENTATIVE_ASSET_AUDIT.md` noted `495335607` as an associated reconstruction file ID, but the underlying donor experiment and histology in the SWC file match specimen `471786879`).*

### 3.3 Root Cause of the Substitute Morphology Misconception
The audit established why substitute reconstructions were previously mentioned in earlier notes:
- During exploratory candidate screening in Phase 2A and Phase 2G, a different Layer 2/3 candidate, **specimen `382982932` (biophysical model `473862496`)**, was evaluated.
- That model's fitted reconstruction (`491771090`) was missing from the Allen API endpoints. To enable execution testing, the pipeline downloaded a published substitute reconstruction (`674389901`, reconstruction ID `674389884`).
- This exploratory substitute reconstruction was erroneously generalized in draft notes across all perisomatic models.
- **In-Place Report Corrections:** §5.2 and §13 (Caveat 3) were corrected to present the verified table, confirm specimen donor matching, and explain the true historical context.

---

## 4. Issue 3: Reconciling 7 vs. 8 Dimensional FHN Parameters

### 4.1 Audit Findings
The report draft contained inconsistent references to "7-parameter" and "seven biophysical quantities" while simultaneously listing 8 parameters in equations and tables.

### 4.2 Exact Formulation Decomposition
The dimensional FitzHugh–Nagumo model formulated for this project is:

$$\begin{aligned}
C_m \frac{\mathrm{d}V}{\mathrm{d}t} &= -g_L (V - V_{\mathrm{rest}}) + k_v (V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V)(V - V_{\mathrm{rest}}) - w + I_{\mathrm{inj}}(t) \\
\tau_w \frac{\mathrm{d}w}{\mathrm{d}t} &= a_w (V - V_{\mathrm{rest}}) - w
\end{aligned}$$

This system strictly consists of:
- **Two Dynamical State Variables:** $V(t)$ [$\text{mV}$] and $w(t)$ [$\text{pA}$].
- **One Time-Dependent Input:** $I_{\mathrm{inj}}(t)$ [$\text{pA}$].
- **Exactly Eight Calibrated Dimensional Parameters:**
  1. $C_m$ [$\text{pF}$]: Total somatic membrane capacitance.
  2. $g_L$ [$\text{nS}$]: Passive leak conductance near rest.
  3. $V_{\mathrm{rest}}$ [$\text{mV}$]: Resting membrane potential (zero-current equilibrium).
  4. $V_{\mathrm{th}}$ [$\text{mV}$]: Apparent instantaneous spike threshold.
  5. $V_{\mathrm{peak}}$ [$\text{mV}$]: Peak action-potential voltage ceiling.
  6. $k_v$ [$\text{nS/mV}^2$]: Non-linear cubic voltage scaling coefficient for active inward current.
  7. $\tau_w$ [$\text{ms}$]: Slow outward recovery deactivation timescale.
  8. $a_w$ [$\text{nS}$]: Steady-state feedback coupling conductance.

### 4.3 Frozen Calibrated Parameter Values (`results/phase4b/fhn_fitted_parameters.csv`)
| Population | Layer | $C_m$ (pF) | $g_L$ (nS) | $V_{\mathrm{rest}}$ (mV) | $V_{\mathrm{th}}$ (mV) | $V_{\mathrm{peak}}$ (mV) | $k_v$ ($\text{nS/mV}^2$) | $\tau_w$ (ms) | $a_w$ (nS) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **L4** | $133.6293$ | $1.0000$ | $-73.73$ | $-57.8105$ | $50.0$ | $0.001662$ | $18.1072$ | $17.1751$ |
| **B** | **L2/3** | $38.2489$ | $0.7788$ | $-78.96$ | $-57.4422$ | $50.0$ | $0.001391$ | $6.8893$ | $9.7725$ |
| **C** | **L5** | $138.9047$ | $0.9859$ | $-77.34$ | $-53.5136$ | $50.0$ | $0.001673$ | $18.8946$ | $18.8666$ |
| **D** | **L6a** | $206.5891$ | $0.9128$ | $-75.71$ | $-57.4877$ | $65.0$ | $0.002577$ | $38.8553$ | $11.7242$ |

### 4.4 In-Place Report Corrections
All references in the Abstract, §6.1, §6.2, §12.1, and §15 were harmonized to **8 parameters** / **8-parameter** / **eight biophysical quantities**.

---

## 5. Issue 4: Model-Reduction Hierarchy Qualification

### 5.1 Audit Findings
Certain phrases in the initial draft implied an unproven universal mathematical theorem:
> *"two-variable planar models cannot sustain adaptation or delayed onset."*

In non-linear dynamical systems theory, non-polynomial planar models with subthreshold-activated recovery, non-monotonic $w$-nullclines, or state-dependent reset mechanisms can exhibit transient slowing or delayed onset. 

### 5.2 Evidence-Bounded Qualification
The audit revised the hierarchy narrative in §10 (Tier 4), §12.1, and §12.2 to state:
1. The inability to sustain continuous multi-second spike-frequency adaptation is an **empirical and structural property of the tested autonomous two-variable cubic FHN formulation with linear recovery** ($w$).
2. In this polynomial planar system, the absence of a secondary slow degree of freedom causes limit cycle trajectories to rapidly settle into stationary periodic orbits ($\le 2$ cycles; $\Delta \mathrm{ISI} < 0.01\%$).
3. Capturing continuous multi-second SFA ($1.97\times\text{--}11.3\times$ ISI expansion) and decoupling onset latency from repetitive firing rate across experimental current-clamp steps provides strong scientific motivation for exploring model extensions that incorporate secondary slow processes (such as a second recovery variable $w_2$ or intracellular calcium accumulation $[\mathrm{Ca}^{2+}]_i$), rather than establishing a universal mathematical impossibility for all two-dimensional models.

---

## 6. Issue 5: Monotonic F–I Scaling and Rate Saturation Verification

### 6.1 Audit Findings
The claim of "monotonic F–I scaling" required precise empirical qualification to prevent misinterpretation.

### 6.2 Empirical Regimes and Model-Specific Differences
Cross-referencing `results/phase4c/fhn_detailed_comparison.csv`, `results/phase3/detailed_model/484564503/summary.json`, and `results/phase3b/heldout/484564503/` confirmed distinct F–I behaviours across the three model tiers:
- **Detailed Multi-Compartment Models:** Once suprathreshold, detailed models display monotonic firing rate increases across moderate current ranges in Populations A (+350 to +430 pA: 1, 9, 27, 39, 48 spikes), B (+150 to +270 pA: 11, 16, 19, 23, 26, 29, 33 spikes), C (+350 to +430 pA: 2, 4, 5, 8, 21 spikes), and D (+210 to +350 pA: 1, 9, 14, 18, 21, 24, 26, 29 spikes). However, they overestimate rheobase by +60 pA in Populations A and C, and severely overcount spikes at strong depolarizations (+390 to +430 pA in Pop A) due to the absence of late-step biological cessation.
- **Biological Recordings:** Biological neurons exhibit monotonic or non-decreasing firing across moderate suprathreshold ranges, but display plateaus (e.g., Pop A firing 9 spikes at both +370 and +390 pA) and non-monotonic decreases at high currents due to late-step cessation or depolarization block (Pop A dropping to 12 spikes at +430 pA). Furthermore, within-cell non-stationarity between COARSE and FINEST protocols disrupts simple monotonic scaling (e.g., Pop A firing 3 spikes at 310 pA in COARSE vs. 1 spike at 310 pA in FINEST).
- **FitzHugh–Nagumo Models:** FHN models do **not** capture continuous monotonic F–I rate expansion. Due to planar cubic nullcline geometry and strong recovery feedback, FHN limit cycles rapidly saturate in frequency: in Population A, FHN fires exactly 9 spikes across the entire 140 pA span from +270 to +410 pA (dropping to 8 at +430 pA); in Population B, FHN firing rate scales only from +150 to +170 pA (15 to 17 spikes) before plateauing and then collapsing to 1–2 spikes at +250 to +270 pA; and in Population D, FHN firing is heavily suppressed to 1–4 spikes.
- **In-Place Report Corrections:** The scope was explicitly qualified in Tier 2 of §10 and §12.1.

---

## 7. Issue 6: Comprehensive Baseline Metric Audit

All quantitative baseline metrics reported in `FINAL_RESEARCH_REPORT.md` and `PHASE5C_REPORT_VERIFICATION.md` were re-verified against frozen precursor records:

| Metric Category | Audited Report Value | Authoritative Source File | Source Row / Field | Audit Status |
| :--- | :--- | :--- | :--- | :---: |
| **Held-Out Sweeps** | 109 sweeps (A: 31, B: 18, C: 34, D: 26) | `results/phase4c/population_summary.csv` | Total sweeps | **VERIFIED** |
| **Biological Spiking / Silent** | 40 Spiking / 69 Silent | `results/phase4c1/phase4c1_spike_detection_audit.csv` | Ground truth row | **VERIFIED** |
| **Detailed Contingency** | 24 TP, 0 FP, 16 FN, 69 TN (Sens 60.0%) | `results/phase4c1/phase4c1_spike_detection_audit.csv` | Det totals | **VERIFIED** |
| **FHN Contingency** | 37 TP, 7 FP, 3 FN, 62 TN (Sens 92.5%) | `results/phase4c1/phase4c1_spike_detection_audit.csv` | FHN totals | **VERIFIED** |
| **Open Bistability Pop A** | $(214.16, 234.34)\text{ pA}$ ($\Delta I = 20.18\text{ pA}$) | `results/phase4c3/phase4c3_bistability_verification.csv` | Row A | **VERIFIED** |
| **Open Bistability Pop B** | $(146.72, 161.28)\text{ pA}$ ($\Delta I = 14.55\text{ pA}$) | `results/phase4c3/phase4c3_bistability_verification.csv` | Row B | **VERIFIED** |
| **Open Bistability Pop C** | $(360.03, 385.33)\text{ pA}$ ($\Delta I = 25.29\text{ pA}$) | `results/phase4c3/phase4c3_bistability_verification.csv` | Row C | **VERIFIED** |
| **Open Bistability Pop D** | $(215.92, 236.27)\text{ pA}$ ($\Delta I = 20.36\text{ pA}$) | `results/phase4c3/phase4c3_bistability_verification.csv` | Row D | **VERIFIED** |
| **Biological Sag at -110 pA** | A: 0.80, B: 1.13, C: 0.63, D: 1.86 mV | `results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md` | Section 7.3 | **VERIFIED** |
| **Detailed Model Sag** | Not quantified | `results/phase3b/heldout_metrics.csv` | Metric omitted | **VERIFIED** |
| **FHN Sag at -110 pA** | $0.00\text{ mV}$ (tested condition) | `results/phase4c1/phase4c1_claim_evidence_matrix.csv` | C5 Sag row | **VERIFIED** |
| **Qualifying SFA Sweeps** | 23 sweeps (A: 6, B: 6, C: 4, D: 7) | `results/phase4c3/phase4c3_biological_adaptation_scope.csv` | Scope census | **VERIFIED** |
| **AP Upstroke Velocities** | Det $397\text{--}466\text{ V/s}$ vs FHN $5.7\text{--}6.2\text{ V/s}$ | `results/phase4c/` / `PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md` | Provisional check | **VERIFIED** |

---

## 8. Regression Test Suite and Working Tree Verification

The automated test suite was executed to verify that no functional regressions were introduced:
```
python -m pytest tests -q
============================= 451 passed in 58.86s =============================
```

### Git Isolation Check
- Working branch: `ashish-work`
- The `main` branch was not accessed or modified.
- No git commits or push commands were executed.
- All working tree changes remain strictly uncommitted.

---

## 9. Conclusion and Sign-Off

The Phase 5C.1 factual and scientific audit is complete. All six audited issues have been reconciled against serialized historical data and updated in place in `FINAL_RESEARCH_REPORT.md` and `PHASE5C_REPORT_VERIFICATION.md`. The final research report is now empirically verified and scientifically robust.


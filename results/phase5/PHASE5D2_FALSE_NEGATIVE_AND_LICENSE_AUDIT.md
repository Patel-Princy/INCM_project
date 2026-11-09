# INCM Phase 5D.2 — False-Negative Reconciliation and Release Licensing Audit

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `INCM-Project`  
**Active Branch:** `ashish-work`  
**Evaluation Target:** Independent reconstruction of detailed-model false negatives, complete metric recomputation, and legal licensing reassessment  
**Date of Audit:** 2026-11-09  
**Audit Status:** Complete, Authoritative, and Fully Reconciled  

---

## 1. Executive Summary & Audit Mandate

This Phase 5D.2 audit was commissioned to independently reconstruct and resolve the remaining scientific and licensing uncertainties in the release documentation. Rather than relying on high-level narrative summaries or aggregate rheobase comparisons, this audit reconstructs every metric directly from frozen sweep-level data, verifies individual sweep traces against original JSON files, and performs an unvarnished assessment of intellectual property and distribution rights.

### Summary of Authoritative Determinations:
1. **Contingency Reconciliation:** Exactly **16 detailed-model false negatives** exist across the 109 held-out sweeps (Pop A: 7; Pop B: 2; Pop C: 7; Pop D: 0). Every single sweep strictly satisfies the definition: $\text{Biological Spikes} > 0$ and $\text{Detailed Model Spikes} = 0$.
2. **Population C FINEST Resolution:** Sweeps 57, 58, 59, and 60 (+330 pA, FINEST) are **confirmed genuine false negatives** ($\text{Rec} = 1$, $\text{Det} = 0$). In contrast, earlier FINEST Sweeps 53 (+280 pA), 54 (+290 pA), 55 (+310 pA), and 56 (+320 pA) were **biologically silent** ($\text{Rec} = 0$, $\text{Det} = 0$) and represent True Negatives ($TN$). The threshold gap in the FINEST block is strictly $+20\text{ pA}$ ($350 - 330\text{ pA}$), directly reflecting biological threshold elevation between COARSE and FINEST blocks.
3. **Population A FINEST Attribution:** The failure of the detailed model to fire in FINEST Sweeps 55 (+300 pA) and 58, 60, 61 (+310 pA) is directly supported by its invariant somatic activation threshold of $+350\text{ pA}$. Crucially, biology fired only 1 spike at $+310\text{ pA}$ across FINEST repeats compared to 3 spikes in COARSE Sweep 46, demonstrating within-cell excitability run-down that should not be conflated with a static $+60\text{ pA}$ staircase offset.
4. **Spike Detection Metrics Recomputed:** Global sensitivity is $60.00\%$ ($24/40$) for detailed models and $92.50\%$ ($37/40$) for FHN models. Global specificity is $100.00\%$ ($69/69$) for detailed models and $89.86\%$ ($62/69$) for FHN models. All 109 sweep classifications and population denominators are 100% reconciled across comparison datasets.
5. **Licensing & Redistribution Legal Audit:** No repository `LICENSE` file currently exists. Fair use cannot be legally assumed as established. Permissive open-source licenses (MIT, BSD, CC0, CC-BY) cannot be claimed without an explicit decision and committed license file by the repository owner. Furthermore, standalone public redistribution of derived CSVs and figure images under Allen Institute Terms of Use remains legally unverified outside standard academic manuscript publication.
6. **Revised Release Verdict:** **CONDITIONALLY READY (Empirically Reconciled; Pending Owner License Commitment, Derived Data Distribution Review, and Manuscript Export Formatting).**

---

## 2. Independent Reconstruction of the 16 Detailed-Model False Negatives

A false negative is defined strictly as:
$$\text{Biological Spike Count} > 0 \quad \text{AND} \quad \text{Detailed-Model Spike Count} = 0$$

Every held-out sweep across all 109 records in `results/phase4c/fhn_detailed_comparison.csv` and `results/phase4c/fhn_heldout_metrics.csv` was audited. Exactly **16 sweeps** satisfy this condition:

### Table 1: Authoritative False-Negative Sweep Census

| Index | Pop (Layer) | Specimen ID | Sweep ID | Protocol Family | Stimulus Amp ($I_{\mathrm{inj}}$) | Bio Spk | Det Spk | FHN Spk | Bio Spike Times (ms) | Det Max Depol ($V_{\max}$) | Authoritative Source File |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| **FN-01** | **A (L4)** | `484564503` | **45** | COARSE | $+290.0\text{ pA}$ | **1** | **0** | 9 | `[1063.32]` | $-49.75\text{ mV}$ | `results/phase3b/heldout/484564503/sweep_45/summary.json` |
| **FN-02** | **A (L4)** | `484564503` | **55** | FINEST | $+300.0\text{ pA}$ | **1** | **0** | 9 | `[1084.995]` | $-49.21\text{ mV}$ | `results/phase3b/heldout/484564503/sweep_55/summary.json` |
| **FN-03** | **A (L4)** | `484564503` | **46** | COARSE | $+310.0\text{ pA}$ | **3** | **0** | 9 | `[1053.45, 1104.12, 1163.25]` | $-48.62\text{ mV}$ | `results/phase3b/heldout/484564503/sweep_46/summary.json` |
| **FN-04** | **A (L4)** | `484564503` | **58** | FINEST | $+310.0\text{ pA}$ | **1** | **0** | 9 | `[1067.18]` | $-48.62\text{ mV}$ | `results/phase3b/heldout/484564503/sweep_58/summary.json` |
| **FN-05** | **A (L4)** | `484564503` | **60** | FINEST | $+310.0\text{ pA}$ | **1** | **0** | 9 | `[1063.495]` | $-48.62\text{ mV}$ | `results/phase3b/heldout/484564503/sweep_60/summary.json` |
| **FN-06** | **A (L4)** | `484564503` | **61** | FINEST | $+310.0\text{ pA}$ | **1** | **0** | 9 | `[1075.31]` | $-48.62\text{ mV}$ | `results/phase3b/heldout/484564503/sweep_61/summary.json` |
| **FN-07** | **A (L4)** | `484564503` | **47** | COARSE | $+330.0\text{ pA}$ | **6** | **0** | 9 | `[1051.30, 1082.74, ...]` (6 spk) | $-47.16\text{ mV}$ | `results/phase3b/heldout/484564503/sweep_47/summary.json` |
| **FN-08** | **B (L2/3)** | `318808427` | **37** | COARSE | $+130.0\text{ pA}$ | **1** | **0** | 0 | `[1074.155]` | $-47.80\text{ mV}$ | `results/phase3b/heldout/318808427/sweep_37/summary.json` |
| **FN-09** | **B (L2/3)** | `318808427` | **46** | FINEST | $+130.0\text{ pA}$ | **1** | **0** | 0 | `[1081.03]` | $-47.80\text{ mV}$ | `results/phase3b/heldout/318808427/sweep_46/summary.json` |
| **FN-10** | **C (L5)** | `471129934` | **45** | COARSE | $+290.0\text{ pA}$ | **1** | **0** | 0 | `[1095.03]` | $-48.71\text{ mV}$ | `results/phase3b/heldout/471129934/sweep_45/summary.json` |
| **FN-11** | **C (L5)** | `471129934` | **46** | COARSE | $+310.0\text{ pA}$ | **1** | **0** | 1 | `[1075.82]` | $-47.15\text{ mV}$ | `results/phase3b/heldout/471129934/sweep_46/summary.json` |
| **FN-12** | **C (L5)** | `471129934` | **47** | COARSE | $+330.0\text{ pA}$ | **2** | **0** | 1 | `[1063.77, 1128.755]` | $-44.83\text{ mV}$ | `results/phase3b/heldout/471129934/sweep_47/summary.json` |
| **FN-13** | **C (L5)** | `471129934` | **57** | FINEST | $+330.0\text{ pA}$ | **1** | **0** | 1 | `[1111.44]` | $-44.83\text{ mV}$ | `results/phase3b/heldout/471129934/sweep_57/summary.json` |
| **FN-14** | **C (L5)** | `471129934` | **58** | FINEST | $+330.0\text{ pA}$ | **1** | **0** | 1 | `[1105.15]` | $-44.83\text{ mV}$ | `results/phase3b/heldout/471129934/sweep_58/summary.json` |
| **FN-15** | **C (L5)** | `471129934` | **59** | FINEST | $+330.0\text{ pA}$ | **1** | **0** | 1 | `[1106.44]` | $-44.83\text{ mV}$ | `results/phase3b/heldout/471129934/sweep_59/summary.json` |
| **FN-16** | **C (L5)** | `471129934` | **60** | FINEST | $+330.0\text{ pA}$ | **1** | **0** | 1 | `[1136.59]` | $-44.83\text{ mV}$ | `results/phase3b/heldout/471129934/sweep_60/summary.json` |

---

## 3. Recomputed Confusion Matrices and Spike Detection Metrics

Using ground truth $\text{Biological Spikes} > 0$ ($P = 40$) and $\text{Biological Spikes} = 0$ ($N = 69$):

### 3.1 Global Comparison Across All 109 Held-Out Sweeps

| Metric | Detailed Biophysical Model | Reduced FitzHugh–Nagumo Model | Mathematical Definition & Derivation |
| :--- | :---: | :---: | :--- |
| **True Positives ($TP$)** | **24** | **37** | $\text{Bio} > 0 \land \text{Model} > 0$ |
| **False Positives ($FP$)** | **0** | **7** | $\text{Bio} = 0 \land \text{Model} > 0$ |
| **False Negatives ($FN$)** | **16** | **3** | $\text{Bio} > 0 \land \text{Model} = 0$ |
| **True Negatives ($TN$)** | **69** | **62** | $\text{Bio} = 0 \land \text{Model} = 0$ |
| **Total Sweeps ($N_{\mathrm{total}}$)** | **109** | **109** | $TP + FP + FN + TN$ |
| **Sensitivity (Recall / TPR)** | **60.00%** | **92.50%** | $TP / (TP + FN) = 24/40$ vs. $37/40$ |
| **Specificity (TNR)** | **100.00%** | **89.86%** | $TN / (TN + FP) = 69/69$ vs. $62/69$ |
| **Balanced Accuracy** | **80.00%** | **91.18%** | $(\text{Sensitivity} + \text{Specificity}) / 2$ |
| **Overall Accuracy** | **85.32%** | **90.83%** | $(TP + TN) / N_{\mathrm{total}} = 93/109$ vs. $99/109$ |
| **Positive Predictive Value (Precision)** | **100.00%** | **84.09%** | $TP / (TP + FP) = 24/24$ vs. $37/44$ |
| **Negative Predictive Value (NPV)** | **81.18%** | **95.38%** | $TN / (TN + FN) = 69/85$ vs. $62/65$ |

### 3.2 Population-Wise Confusion Counts

```
+----------------------------------------------------------------------------------------------------+
|                             POPULATION-WISE SPIKE DETECTION METRICS                                |
+----------------------------------------------------------------------------------------------------+
| POPULATION A (Layer 4, Specimen 484564503, Total Sweeps = 31: 11 Spiking, 20 Silent)               |
|   - Detailed Model: TP =  4, FP = 0, FN = 7, TN = 20 | Sens =  36.4%, Spec = 100.0%, BalAcc = 68.2%|
|   - FHN Model:      TP = 11, FP = 4, FN = 0, TN = 16 | Sens = 100.0%, Spec =  80.0%, BalAcc = 90.0%|
|   * FHN False Positives: Sweeps 41, 42, 43, 44 (+210, +230, +250, +270 pA; near-threshold gating) |
|   * FHN False Negatives: None (0 FN)                                                               |
+----------------------------------------------------------------------------------------------------+
| POPULATION B (Layer 2/3, Specimen 318808427, Total Sweeps = 18: 8 Spiking, 10 Silent)              |
|   - Detailed Model: TP =  6, FP = 0, FN = 2, TN = 10 | Sens =  75.0%, Spec = 100.0%, BalAcc = 87.5%|
|   - FHN Model:      TP =  6, FP = 0, FN = 2, TN = 10 | Sens =  75.0%, Spec = 100.0%, BalAcc = 87.5%|
|   * Both models miss Sweep 37 (COARSE, +130 pA) and Sweep 46 (FINEST, +130 pA)                     |
|   * False Positives: Zero (0 FP across both models)                                                |
+----------------------------------------------------------------------------------------------------+
| POPULATION C (Layer 5, Specimen 471129934, Total Sweeps = 34: 11 Spiking, 23 Silent)               |
|   - Detailed Model: TP =  4, FP = 0, FN = 7, TN = 23 | Sens =  36.4%, Spec = 100.0%, BalAcc = 68.2%|
|   - FHN Model:      TP = 10, FP = 2, FN = 1, TN = 21 | Sens =  90.9%, Spec =  91.3%, BalAcc = 91.1%|
|   * FHN False Positives: Sweeps 55, 56 (FINEST, +310, +320 pA; biological cell silent)             |
|   * FHN False Negative: Sweep 45 (COARSE, +290 pA; biological cell fired 1 spike)                  |
+----------------------------------------------------------------------------------------------------+
| POPULATION D (Layer 6a, Specimen 471786879, Total Sweeps = 26: 10 Spiking, 16 Silent)              |
|   - Detailed Model: TP = 10, FP = 0, FN = 0, TN = 16 | Sens = 100.0%, Spec = 100.0%, BalAcc = 100.0%|
|   - FHN Model:      TP = 10, FP = 1, FN = 0, TN = 15 | Sens = 100.0%, Spec =  93.8%, BalAcc = 96.9%|
|   * FHN False Positive: Sweep 39 (COARSE, +190 pA; biological cell silent until +210 pA)           |
|   * Detailed Model: Zero False Negatives (10/10 biological spiking sweeps detected)                 |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Population-Wise Attribution with Distinguishable Confidence Levels

To prevent over-generalizing aggregate rheobase differences, the causes of detailed-model false negatives are divided into three formal tiers:

### 4.1 Population A (7 False Negatives: Sweeps 45, 46, 47, 55, 58, 60, 61)
- **Directly Supported Explanation (High Confidence):**
  Across all held-out sweeps, the detailed model's first action potential occurs at $+350.0\text{ pA}$ (Sweep 48: 1 spike). In the COARSE protocol, biology fires at $+290\text{ pA}$ (Sweep 45: 1 spike), $+310\text{ pA}$ (Sweep 46: 3 spikes), and $+330\text{ pA}$ (Sweep 47: 6 spikes). All 7 false negative sweeps occur at stimulus amplitudes between $+290\text{ pA}$ and $+330\text{ pA}$, strictly below the detailed model's somatic threshold. The $+60\text{ pA}$ coarse rheobase shift is an empirically verified fact of the COARSE staircase.
- **Plausible Contributing Factors (Moderate Confidence):**
  1. *Biological Run-Down in FINEST:* In COARSE Sweep 46 (+310 pA), biology fired 3 spikes. However, in FINEST Sweeps 58, 60, and 61 (+310 pA), biology fired only 1 solitary spike. This within-cell rate reduction indicates that biological excitability decreased across repeated hunting sweeps, yet remained suprathreshold for the biological cell while the detailed model remained subthreshold.
  2. *Depolarization-Activated Inactivation:* Despite a $+13.6\text{ mV}$ depolarized resting baseline, the detailed model fails to spike below $+350\text{ pA}$, suggesting that steady-state sodium channel inactivation ($h_{\infty}$) or higher leak conductance raised the effective threshold.
- **Unresolved Cause (Low Confidence):**
  The specific ionic current densities (e.g., balance of $\bar{g}_{\mathrm{Na}}$ vs. $\bar{g}_{\mathrm{Kv3.1}}$ or $\bar{g}_{\mathrm{leak}}$) that caused the automated calibration pipeline to select a $+350\text{ pA}$ threshold cannot be causally deduced without parameter perturbation simulations.

### 4.2 Population B (2 False Negatives: Sweeps 37, 46)
- **Directly Supported Explanation (High Confidence):**
  In both COARSE Sweep 37 (+130 pA) and FINEST Sweep 46 (+130 pA), biology fired exactly 1 spike. In both sweeps, the detailed model remained subthreshold ($V_{\max} = -47.80\text{ mV}$), but at the very next current step (+150 pA, Sweep 38), the detailed model fired 11 spikes. FHN also fired 0 spikes at $+130\text{ pA}$ and 15 spikes at $+150\text{ pA}$. This is a mild $+20\text{ pA}$ near-threshold sensitivity mismatch, not a $+60\text{ pA}$ shift.
- **Plausible Contributing Factors (Moderate Confidence):**
  Solitary spikes at threshold in experimental patch-clamp recordings can be facilitated by stochastic microscopic channel fluctuations that are absent in deterministic cable equations.
- **Unresolved Cause (Low Confidence):**
  Whether this threshold offset represents biological stochasticity or an uncalibrated deterministic slope conductance cannot be resolved from two sweeps.

### 4.3 Population C (7 False Negatives: Sweeps 45, 46, 47, 57, 58, 59, 60)
- **Directly Supported Explanation (High Confidence):**
  The detailed model's first held-out spike occurs at $+350.0\text{ pA}$ (Sweep 48: 2 spikes). In COARSE sweeps, biology fires at $+290\text{ pA}$ (Sweep 45: 1 spike), $+310\text{ pA}$ (Sweep 46: 1 spike), and $+330\text{ pA}$ (Sweep 47: 2 spikes). This directly demonstrates a $+60\text{ pA}$ rheobase overestimation in COARSE sweeps.
- **Explicit Resolution of FINEST Sweeps 57–60:**
  *Discrepancy Clarification:* Earlier protocol audits noted that FINEST Sweeps 53 (+280 pA), 54 (+290 pA), 55 (+310 pA), and 56 (+320 pA) were **biologically silent**. They are True Negatives ($TN$), NOT false negatives.
  In contrast, repeated FINEST Sweeps 57, 58, 59, and 60 (+330 pA) **all fired 1 biological spike** ($Rec = 1$, latencies 85.2–116.6 ms). The detailed model remained subthreshold across all four ($V_{\max} = -44.83\text{ mV}$).
  *Crucial Finding:* Because biology was silent at $+290$ and $+310\text{ pA}$ in FINEST, the biological threshold within the FINEST block had shifted upward to $+330\text{ pA}$. Therefore, for Sweeps 57–60, the detailed model's threshold overestimation was strictly $+20\text{ pA}$ ($350 - 330\text{ pA}$), NOT $+60\text{ pA}$. Conflating FINEST sweeps with the COARSE $+60\text{ pA}$ rheobase shift is empirically incorrect.

---

## 5. Licensing and Provenance Legal Audit

Every proposed public release component was evaluated against strict legal standards:
- **Fair Use Disclaimer:** Fair use is an affirmative defense under US copyright law evaluated on a case-by-case basis; it cannot be declared as legally established by project contributors.
- **License Existence Check:** A filesystem search confirmed that **no repository `LICENSE` file exists** in `INCM-Project`.
- **No Inferred Rights:** Open-source licenses (MIT, BSD, CC0, CC-BY) cannot be assigned without an explicit owner decision. Public accessibility of the Allen database does not equal redistribution permission.

### Table 2: Public Release Licensing and Provenance Matrix

| Component | Source / Origin | Classification Category | Applicable Legal Framework | Exact Redistribution Rights & Known Restrictions | Clearance Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Research Report Manuscript** (`FINAL_RESEARCH_REPORT.md`) | Authored by project team. | **Category 1: Original Project Work** | Unspecified / Unlicensed | No `LICENSE` file exists. Requires repository owner to formally select and commit an open license (e.g., CC-BY 4.0). Must cite Allen Institute data. | **REQUIRES OWNER LICENSE SELECTION** |
| **Compiled Research PDF** (`FINAL_RESEARCH_REPORT.pdf`) | Compiled from manuscript. | **Category 1: Original Project Work** | Unspecified / Unlicensed | Identical to Markdown manuscript. Requires owner license decision. | **REQUIRES OWNER LICENSE SELECTION** |
| **Derived Summary CSVs** (`population_summary.csv`, `fhn_detailed_comparison.csv`, `subthreshold_iv_data.csv`, `fi_curve_data.csv`) | Derived from Allen Cell Types Database recordings via computational feature extraction. | **Category 2: Derived from Allen Data** | Allen Institute Terms of Use (`alleninstitute.org/terms-of-use/`) | Terms permit research and academic publication of results with citation. **Terms do NOT explicitly grant an open redistribution license for standalone third-party CSV hosting.** Fair use is unestablished. Requires attribution: *"Data derived from the Allen Cell Types Database (© 2015 Allen Institute for Brain Science)"*. | **UNRESOLVED / REQUIRES REVIEW (Exclude from standalone redistribution until reviewed)** |
| **Calibrated FHN Parameters & Bifurcation CSVs** (`calibrated_fhn_parameters.csv`, `phase4c3_*.csv`) | Numerical parameter estimates and Lyapunov coefficients computed by project algorithms. | **Category 1: Original Project Work** | Unspecified / Unlicensed | 100% project-generated numerical data. Unlicensed. Requires repository owner to attach an explicit public license (e.g., CC0 or CC-BY 4.0). | **REQUIRES OWNER LICENSE SELECTION** |
| **Publication Figures** (`results/phase4b/figures/*.png`, `results/phase4c/figures/*.png`) | Rendered by project scripts; displays model traces overlaid on biological experimental voltage recordings. | **Category 2: Derived Analytical Visualizations** | Allen Institute Terms of Use | Depicts raw biological recording traces. Redistribution permission as standalone image assets is unverified. Captions must cite donor specimen IDs. Fair use is unestablished. | **UNRESOLVED / REQUIRES REVIEW (Exclude from standalone redistribution until reviewed)** |
| **Core Reproduction Codebase** (`src/*.py`, `tests/*.py`) | Original simulation and bifurcation algorithms authored by project. | **Category 1 & 3: Original Code interfacing with 3rd-Party APIs** | Unspecified / Unlicensed | Owner must select and commit an open-source license (e.g., MIT or BSD 3-Clause). Third-party licenses (AllenSDK: BSD 2-Clause + non-commercial restriction; NEURON: BSD/GPL) must be acknowledged. | **REQUIRES OWNER LICENSE SELECTION** |
| **Morphology SWC Reconstructions** (`data/metadata/*.swc`) | Histological reconstructions from Allen Institute. | **Category 3: Externally Sourced Material** | Allen Institute Terms of Use | Multi-megabyte external scientific assets. Bundling in git repository is prohibited. Must be fetched via AllenSDK. | **STRICTLY EXCLUDED (TIER C)** |
| **Raw Patch-Clamp NWB Traces** (`data/nwb_cache/*.nwb`) | Primary experimental patch-clamp recordings from Allen Institute. | **Category 3: External Primary Data** | Allen Institute Terms of Use | >700 MB binary archives. Re-hosting prohibited by bandwidth and unverified licensing. Fetched via AllenSDK. | **STRICTLY EXCLUDED (TIER C)** |

---

## 6. Corrections Made to Phase 5D Release-Readiness Audit

In `results/phase5/PHASE5D_RELEASE_READINESS_AUDIT.md`, the following authoritative corrections were applied in-place:
1. **Section 1 (Executive Verdict):** Refined the release packaging verdict to **"CONDITIONALLY READY / REQUIRES OWNER ACTION"**, explicitly documenting that no `LICENSE` file currently exists in the repository, and noting that standalone derived dataset redistribution rights under Allen Institute Terms of Use remain subject to review.
2. **Section 3.7 (Contingency Matrix Narrative):** Replaced aggregate rheobase statements with the full sweep-by-sweep breakdown:
   - Explicitly resolved that Population C FINEST Sweeps 53–56 were biologically silent ($TN$), whereas Sweeps 57–60 genuinely fired 1 spike ($FN$).
   - Documented that the threshold gap in Pop C FINEST was strictly $+20\text{ pA}$ ($350 - 330\text{ pA}$), reflecting biological threshold elevation.
   - Documented that in Pop A, biological spike counts dropped from 3 spikes in COARSE (+310 pA) to 1 spike in FINEST (+310 pA), demonstrating within-cell non-stationarity.
   - Characterized Population B false negatives (Sweeps 37, 46 at +130 pA) as a $+20\text{ pA}$ near-threshold sensitivity mismatch.
3. **Section 7.1 (Licensing Table):** Replaced premature "CLEARED CC-BY/MIT" and "Fair use established" declarations with legally sound classifications:
   - Original work marked as **"REQUIRES OWNER LICENSE SELECTION"**.
   - Derived CSVs and figures marked as **"UNRESOLVED / REQUIRES REVIEW (Exclude from open redistribution until reviewed)"**.
   - Primary SWC and NWB files marked as **"STRICTLY EXCLUDED (TIER C)"**.
4. **Section 8 (Issue Classification Matrix):** Added **ISS-09 (Major)** formally tracking the absence of a repository `LICENSE` file and unverified standalone derived data redistribution rights.

---

## 7. Remaining Legal and Scientific Uncertainties

1. **Standalone Data Redistribution:** While scholarly publication of derived summary tables in an academic research article is standard scientific practice, public hosting of standalone extracted CSV datasets and figure images on GitHub or public portals without explicit Allen Institute data redistribution approval remains legally unreviewed.
2. **License Selection:** The repository owner has not yet chosen or committed an official open-source license (`LICENSE` file) or dataset attribution statement (`DATASET_NOTICE.md`).
3. **Biophysical Cause of Pop B Threshold Mismatch:** Whether the 1-spike biological firing at $+130\text{ pA}$ in Population B represents channel stochasticity near threshold or a deterministic conductance bias cannot be definitively resolved without multi-trial patch-clamp recordings.

---

## 8. Revised Release Verdict

### **Revised Verdict: CONDITIONALLY READY**

- **Scientific Integrity:** **RECONCILED AGAINST FROZEN EVIDENCE.** The empirical evaluation metrics and spike-detection classifications across all 109 held-out sweeps have been independently reconciled against the frozen evaluation data, and the 16 detailed-model false negatives were independently checked. Population-specific Hopf and bistability findings are supported by analytical local calculations and numerical dynamical evidence, subject to the documented limitations of the numerical fold estimates (which represent forward-integration extinction estimates rather than rigorous periodic-orbit continuation-derived folds; no full periodic-orbit BVP/Floquet continuation analysis was performed).
- **Export & Layout:** **CONDITIONALLY READY.** Pre-export adjustments (handling the 15-column Table 4 width and optional figure embedding) must be finalized before PDF compilation.
- **Licensing & Release Clearance:** **PENDING OWNER DECISION.** The repository owner must commit an official `LICENSE` file (e.g., MIT for code, CC-BY 4.0 for text) and a `DATASET_NOTICE.md` acknowledging Allen Institute data attribution before public distribution. Standalone derived datasets should be restricted to manuscript distribution until legal review is complete.

---

## 9. Phase 5D.3 Scientific Integrity Wording Correction Note

This note records the Phase 5D.3 documentation correction to prevent overclaiming verification:
1. **Scope of Empirical Reconciliation:** All 109 held-out sweep metrics, spike-detection classifications, and 16 detailed-model false negatives were independently reconciled against frozen Phase 3 and Phase 4 comparison datasets.
2. **Local Hopf vs. Global Fold Distinctions:**
   - Population-specific Hopf calculations support local subcritical Hopf classifications under the documented normal-form convention ($l_1 > 0$).
   - Bistability intervals are supported by numerical dynamical evidence.
   - The reported fold thresholds ($I_{\mathrm{fold}}$) are forward-integration extinction estimates, not rigorous periodic-orbit continuation-derived folds. No full periodic-orbit BVP or Floquet multiplier continuation analysis was conducted.
3. **Removal of Absolute Verification Claims:** Blanket assertions describing findings as "100% verified" or "mathematically verified" across all dynamical regimes have been excised and replaced with bounded, defensible phrasing.
4. **Release Gate Status:** The project remains conditionally ready, and cannot be declared ready for public release while licensing commitments and manuscript export layout issues remain unresolved.


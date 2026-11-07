# PHASE 3C — METRIC RECOMPUTATION AUDIT

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3C — Independent Scientific Consistency Audit and Phase 3B Results Correction  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  
**Output CSV:** [`results/phase3c/recomputed_population_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3c/recomputed_population_metrics.csv)  
**Audit Script:** [`scripts/audit_phase3b_metrics.py`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/scripts/audit_phase3b_metrics.py)  

---

## 1. Executive Summary

An independent computational audit was conducted across all 109 simulation runs generated during Phase 3B. Every row in [`results/phase3b/heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv) was verified directly against its corresponding on-disk `summary.json` file in `results/phase3b/heldout/<specimen_id>/sweep_<id>/`.

**Integrity Verification Result:**
- Total per-sweep summary JSON files checked: **109 / 109 (100%)**
- Discrepancies between JSON summaries and `heldout_metrics.csv`: **0 (Zero mismatches)**
- Numerical accuracy: Verified to within $< 10^{-4}$ for correlation and $< 10^{-3}\text{ mV}$ for RMSE and MAE.

---

## 2. Comparison: Original Phase 3B Reported Metrics vs Independently Recomputed Metrics

Below is the side-by-side verification table comparing what was reported in Phase 3B against the independent recomputation from the underlying per-sweep simulation records:

```
==================================================================================================================================
Metric / Field                           Pop A (L4)          Pop B (L2/3)        Pop C (L5)          Pop D (L6a)         Status
==================================================================================================================================
Held-Out Sweeps Count:
  - Phase 3B Reported                    31                  18                  34                  26                  CONFIRMED
  - Recomputed                           31                  18                  34                  26                  CONFIRMED
Unique Current Amplitudes:
  - Phase 3B Reported                    29 (ambiguous)      18 (ambiguous)      29 (ambiguous)      24 (ambiguous)      CLARIFIED
  - Recomputed (Amplitudes alone)        28                  17                  28                  24                  RECOMPUTED
  - Recomputed (Protocol × Amplitude)    29                  18                  31                  24                  RECOMPUTED
Overall RMSE (mV):
  - Phase 3B Reported                    12.73 ± 0.80        4.04 ± 2.64         4.73 ± 0.58         2.23 ± 1.80         CONFIRMED
  - Recomputed (Sample std, ddof=1)      12.727 ± 0.799      4.040 ± 2.636       4.735 ± 0.580       2.228 ± 1.801       CONFIRMED
Overall MAE (mV):
  - Phase 3B Reported                    12.23 ± 0.80        2.17 ± 1.01         4.51 ± 0.41         0.85 ± 0.44         CONFIRMED
  - Recomputed (Sample std, ddof=1)      12.227 ± 0.803      2.170 ± 1.007       4.515 ± 0.410       0.849 ± 0.443       CONFIRMED
Overall Pearson Correlation (r):
  - Phase 3B Reported                    0.8036 ± 0.2000     0.9570 ± 0.0594     0.9610 ± 0.0692     0.9699 ± 0.0354     CONFIRMED
  - Recomputed (Sample std, ddof=1)      0.8036 ± 0.2000     0.9570 ± 0.0594     0.9610 ± 0.0692     0.9699 ± 0.0354     CONFIRMED
Subthreshold Correlation (r):
  - Phase 3B Reported                    0.7402              0.9965              0.9579              0.9894              CONFIRMED
  - Recomputed                           0.7402              0.9965              0.9579              0.9893              CONFIRMED
Suprathreshold Correlation (r):
  - Phase 3B Reported                    0.9189              0.9076              0.9673              0.9388              CONFIRMED
  - Recomputed                           0.9189              0.9076              0.9673              0.9388              CONFIRMED
Mean Spike Count Delta:
  - Phase 3B Reported                    +1.94               +0.83               -0.03               +1.35               CONFIRMED
  - Recomputed                           +1.935              +0.833              -0.029              +1.346              CONFIRMED
Maximum Spike Count Delta (abs):
  - Phase 3B Reported                    +36                 +4                  +10                 +10                 CONFIRMED
  - Recomputed                           +36                 +4                  +10                 +10                 CONFIRMED
Baseline Resting Potential (mV):
  - Recorded Mean                        -74.17              -75.40              -68.58              -75.90              CONFIRMED
  - Simulated                            -61.07              -75.93              -63.65              -75.96              CONFIRMED
  - Baseline Delta                       +13.10              -0.53               +4.93               -0.06               CONFIRMED
Rheobase Interval Midpoint (COARSE):
  - Recorded                             280.0 pA            120.0 pA            280.0 pA            200.0 pA            CONFIRMED
  - Simulated                            340.0 pA            140.0 pA            340.0 pA            200.0 pA            CONFIRMED
  - Rheobase Shift                       +60.0 pA            +20.0 pA            +60.0 pA            0.0 pA              CONFIRMED
==================================================================================================================================
```

---

## 3. Discrepancy Findings and Clarifications

1. **Condition Count Nomenclature:**
   - Previous reports used "Unique Conditions" interchangeably between unique stimulus amplitudes and unique protocol-condition groups.
   - Specifically, Specimen 471129934 (L5) tested 28 unique amplitudes across 31 protocol-amplitude condition groups (due to overlap at 290, 310, and 330 pA across COARSE and FINEST). The previous table mistakenly listed 29 for L5. The total across the 4 populations is exactly **97 unique amplitudes** and **102 protocol-amplitude condition groups**.
2. **Mean vs. Extremes in Spike Delta (Pop A):**
   - The reported mean spike delta of $+1.94$ in Pop A is mathematically exact as an unweighted average over all 31 sweeps. However, presenting it without emphasizing the $+36$ spike over-prediction at high currents ($+430\text{ pA}$) concealed severe firing rate saturation failure.
3. **Subthreshold Correlation Prose Error:**
   - The reported table values ($0.7402, 0.9965, 0.9579, 0.9894$) are computationally exact. The prose assertion in the report claiming "$r > 0.98$ across models" was a narrative overgeneralization contradicted by the table itself.

# PHASE 3C — CORRECTION LOG

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3C — Independent Scientific Consistency Audit and Phase 3B Results Correction  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  
**Target Files Corrected:**
- [`results/phase3b/PHASE3B_FINAL_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_FINAL_REPORT.md)
- [`results/phase3b/PHASE3B_CROSS_POPULATION_ANALYSIS.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_CROSS_POPULATION_ANALYSIS.md)

---

## 1. Summary of Identified Discrepancies and Errors

| ID | Issue Category | Affected File(s) | Description | Root Cause | Correction Applied |
|:---:|:---|:---|:---|:---|:---|
| **C1** | Prose/Table Contradiction | `PHASE3B_FINAL_REPORT.md`, `PHASE3B_CROSS_POPULATION_ANALYSIS.md` | Prose claimed subthreshold correlation "$r > 0.98$ across models" and "$r > 0.98$ for Pops B, C, D", but table reported Pop C at 0.9579 and Pop A at 0.7402. | Generalization in prose contradicted the actual recomputed numbers. | Corrected prose to accurately state that only Pop B ($0.9965$) and Pop D ($0.9894$) exceed 0.98, while Pop C is 0.9579 and Pop A is 0.7402. |
| **C2** | Unsupported Mechanistic Claims | `PHASE3B_FINAL_REPORT.md`, `PHASE3B_CROSS_POPULATION_ANALYSIS.md` | Attributing high subthreshold correlation as "confirming passive multicompartmental cable theory and morphology reconstruction accuracy". | Pearson correlation is invariant to constant shifts and linear scaling; high correlation does not validate input resistance or absolute voltage response. | Replaced with scientifically precise language; noted that correlation reflects waveform trajectory shape rather than parameter accuracy. |
| **C3** | Concealment by Aggregate Statistics | `PHASE3B_FINAL_REPORT.md`, `PHASE3B_CROSS_POPULATION_ANALYSIS.md` | Pop A was characterized primarily by its baseline offset and a modest mean spike delta of $+1.94$, omitting the severe non-monotonic firing mismatch and mid-step cessation. | Averaging under-prediction at threshold ($-1$ to $-6$ spikes) with massive over-prediction at high currents ($+18$ to $+36$ spikes) produced a misleadingly low mean. | Added explicit analysis of the F-I curve failure in L4: late-step biological cessation at $\ge 390\text{ pA}$ vs continuous $48\text{ Hz}$ model firing ($+36$ spikes delta), independent of baseline offset. |
| **C4** | Condition Count Discrepancy | `PHASE3B_FINAL_REPORT.md` | Pop C unique conditions reported as 29 in the table, but `condition_groups.csv` and `heldout_fi_curves.csv` contain 31 groups. | Ambiguity between unique current amplitudes (28 for Pop C) and protocol-amplitude groups (31 for Pop C). | Standardized and clarified definitions: 97 unique amplitudes, 102 protocol-amplitude condition groups across the 4 populations. |
| **C5** | Temporal Variability Terminology | `PHASE3B_FINAL_REPORT.md`, `PHASE3B_CROSS_POPULATION_ANALYSIS.md` | Speculating on biological mechanisms (e.g. metabolic exhaustion, wash-out) for L5 and L6a FINEST firing drops. | Current-clamp somatic recordings cannot isolate the cellular cause of temporal non-stationarity without independent measurements. | Reframed strictly as phenomenological temporal non-stationarity / between-protocol threshold drift. |
| **C6** | Representative vs Population Scope | `PHASE3B_FINAL_REPORT.md`, `PHASE3B_CROSS_POPULATION_ANALYSIS.md` | Phrasing sometimes implied conclusions applied to the entire cortical layer population rather than the single representative specimen model. | Scope overstatement. | Added explicit scoping caveat: findings reflect the specific layer-representative specimen and model fit, not full cortical population variance. |

---

## 2. Detailed Change Log

### Correction C1 & C2: Subthreshold Correlation & Cable Claims
- **Location:** `PHASE3B_FINAL_REPORT.md` (Sections 1 & 4.3), `PHASE3B_CROSS_POPULATION_ANALYSIS.md` (Sections 1 & 5).
- **Previous Text:**
  > "Across all four populations, models achieve exceptional correlation on hyperpolarizing and subthreshold sweeps ($r > 0.98$ for Pops B, C, D)."
  > "Conversely, subthreshold and hyperpolarizing waveforms maintain correlations exceeding 0.98, confirming the accuracy of passive multicompartmental cable properties."
- **Corrected Text:**
  > "Subthreshold correlation varies substantially across populations: while Population B ($r = 0.9965$) and Population D ($r = 0.9894$) exhibit near-perfect trajectory alignment, Population C achieves $r = 0.9579$, and Population A achieves only $r = 0.7402$ due to small signal-to-noise ratio on low-amplitude deflections ($\le 30\text{ pA}$) combined with resting potential offset."
  > "High correlation on subthreshold sweeps reflects shape similarity during capacitive charging, but does not independently validate input resistance or absolute voltage calibration, which are compromised in Population A."

### Correction C3: Pop A (L4) Excitability Breakdown
- **Location:** `PHASE3B_FINAL_REPORT.md` (Section 4.1), `PHASE3B_CROSS_POPULATION_ANALYSIS.md` (Section 3.4).
- **Correction Detail:**
  - Added table of L4 firing at high current steps ($+290\text{ pA}$: $1$ vs $0$; $+390\text{ pA}$: $9$ vs $27$; $+410\text{ pA}$: $13$ vs $39$; $+430\text{ pA}$: $12$ vs $48$).
  - Documented that the biological neuron fires an initial burst and then enters late-step spike cessation (completely silent for the final $500\text{ ms}$ of the step at $430\text{ pA}$), whereas the model fires continuously at up to $48\text{ Hz}$.
  - Clarified that reporting an average spike delta of $+1.94$ conceals a $+36$ spike over-prediction at high currents canceled out by under-prediction near threshold.
  - Documented that this excitability breakdown is completely independent of the $+13.1\text{ mV}$ baseline offset.

### Correction C4: Standardized Condition Counts
- **Location:** `PHASE3B_FINAL_REPORT.md` (Table in Section 3), `PHASE3B_CROSS_POPULATION_ANALYSIS.md` (Table in Section 2).
- **Correction Detail:**
  - Explicitly differentiated:
    - Unique stimulus amplitudes: Pop A = 28, Pop B = 17, Pop C = 28, Pop D = 24 (Total = 97).
    - Unique protocol-amplitude condition groups: Pop A = 29, Pop B = 18, Pop C = 31, Pop D = 24 (Total = 102).
  - Corrected Pop C table entry from 29 to 31 protocol-amplitude condition groups (matching `condition_groups.csv` and `heldout_fi_curves.csv`).

### Correction C5 & C6: Scoping and Non-Stationarity Language
- **Location:** Throughout reports.
- **Correction Detail:**
  - Qualified all layer labels to indicate "individual representative specimen model".
  - Reframed all L5 and L6a protocol discussions around phenomenological temporal non-stationarity without speculative mechanistic assertions.

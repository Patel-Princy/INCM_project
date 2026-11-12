# Phase 5F.2 — Resting Potential Provenance Correction and Final Export Report

**Repository:** `Patel-Princy/INCM_project`  
**Working Branch:** `ashish-work`  
**Base Commit:** `5509ddd`  
**Date:** November 10, 2026  
**Auditor / Engineer:** Independent Antigravity Scientific Integrity & Verification Agent  
**Scope:** Dual-Reporting Table 1 Correction, Dependent Claim Review, Export Recompilation, and Comprehensive Scientific QA  

---

## 1. Executive Summary & Verification Outcome

Following the independent scientific audit in `results/phase5/PHASE5F1_INDEPENDENT_SCIENTIFIC_AUDIT.md`, Phase 5F.2 resolved the methodological conflation between whole-cell session biological resting potentials and single-sweep pre-stimulus baselines.

### Summary of Actions Taken:
1. **Table 1 Dual-Reporting Structure:** Replaced the single resting potential column with two distinct, explicitly labeled columns:
   - `Whole-Cell Biological V_rest (mV)` (session-level Allen Cell Types Database ephys feature)
   - `Calibration-Sweep Baseline V_baseline (mV)` (local pre-stimulus baseline of the designated calibration sweep)
2. **Explanatory Table Note:** Added an explicit note explaining that the dimensional FHN model's $V_{\mathrm{rest}}$ parameter in Table 3 anchors directly to the calibration-sweep baseline rather than the session-wide biological resting feature.
3. **Dependent Claim Review & Harmonization:** Audited and updated dependent wording in Section 9.2 (Population B detailed model behavior), Table 7 (Cross-Laminar Synthesis), and Section 13 (Caveat 15).
4. **Preservation of Scientific Assets:** All 32 parameters in Table 3, all 109 held-out evaluation metrics, all 16 false negatives, all 52 references, and all Phase 5F literature review documents were preserved without modification.
5. **Manuscript Export Recompilation:** Regenerated `FINAL_RESEARCH_REPORT.html` and `FINAL_RESEARCH_REPORT.pdf` using the validated headless print pipeline (`build_manuscript.py`, KaTeX v0.16.27, Headless Chrome).
6. **Scientific Verification:** Confirmed that **451 of 451 tests pass** and **541 of 541 frozen files** match the baseline cryptographic manifest (including the authoritative FHN parameter CSV hash).

---

## 2. Table 1 Correction (Before and After)

### 2.1 Original Table 1 (at Phase 5C / Commit `5509ddd`)
*Single column conflating unverified values and draft parameters:*

| Population | Cortical Layer | Specimen ID | Transgenic Cre Line | Dendritic Morphology | Input Resistance ($R_{\mathrm{in}}$) | Resting Potential ($V_{\mathrm{rest}}$) | Primary Calibration Sweep |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **Layer 4** | `484564503` | Rorb-IRES2-Cre | Spiny (Pyramidal) | $44.3\text{ M}\Omega$ | $-73.73\text{ mV}$ | Sweep 49 (+370 pA, COARSE) |
| **B** | **Layer 2/3** | `318808427` | Nr5a1-Cre | Spiny (Pyramidal) | $80.3\text{ M}\Omega$ | $-78.96\text{ mV}$ | Sweep 40 (+190 pA, COARSE) |
| **C** | **Layer 5** | `471129934` | Rbp4-Cre_KL100 | Spiny (Pyramidal) | $31.3\text{ M}\Omega$ | $-77.34\text{ mV}$ | Sweep 51 (+410 pA, COARSE) |
| **D** | **Layer 6a** | `471786879` | Ntsr1-Cre_GN220 | Spiny (Pyramidal) | $52.6\text{ M}\Omega$ | $-75.71\text{ mV}$ | Sweep 42 (+250 pA, COARSE) |

*Issues identified in audit:* Pop B ($-78.96\text{ mV}$) was the session feature, whereas Pop A ($-73.73\text{ mV}$) and Pop D ($-75.71\text{ mV}$) were single-sweep baselines. Pop C ($-77.34\text{ mV}$) was an untraceable typo from an unverified draft.

---

### 2.2 Corrected Table 1 (Authoritative Dual-Reporting Structure)
*Separate reporting of whole-cell session biological resting potential and single-sweep calibration baseline:*

| Population | Cortical Layer | Specimen ID | Transgenic Cre Line | Dendritic Morphology | Apparent Input Resistance ($R_{\mathrm{in}}$, test pulse) | Whole-Cell Biological $V_{\mathrm{rest}}$ | Calibration-Sweep Baseline $V_{\mathrm{baseline}}$ | Primary Calibration Sweep |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **Layer 4** | `484564503` | Rorb-IRES2-Cre | Spiny (Pyramidal) | $44.3\text{ M}\Omega$ | $-73.70\text{ mV}$ | $-73.73\text{ mV}$ | Sweep 49 (+370 pA, COARSE) |
| **B** | **Layer 2/3** | `318808427` | Nr5a1-Cre | Spiny (Pyramidal) | $80.3\text{ M}\Omega$ | $-78.96\text{ mV}$ | $-75.90\text{ mV}$ | Sweep 40 (+190 pA, COARSE) |
| **C** | **Layer 5** | `471129934` | Rbp4-Cre_KL100 | Spiny (Pyramidal) | $31.3\text{ M}\Omega$ | $-68.62\text{ mV}$ | $-69.34\text{ mV}$ | Sweep 51 (+410 pA, COARSE) |
| **D** | **Layer 6a** | `471786879` | Ntsr1-Cre_GN220 | Spiny (Pyramidal) | $52.6\text{ M}\Omega$ | $-75.92\text{ mV}$ | $-75.71\text{ mV}$ | Sweep 42 (+250 pA, COARSE) |

*Accompanying Table Note:*
> **Electrophysiological baseline and provenance note:** (i) Table 1 dual-reports both the whole-cell session biological resting potential ($V_{\mathrm{rest}}$) from the Allen Cell Types Database ephys feature pipeline (`data/metadata/cell_inventory.csv`) and the local pre-stimulus baseline of the designated calibration sweep ($V_{\mathrm{baseline}}$; `results/phase4b/fhn_calibration_metrics.csv`). The single-sweep pre-stimulus baseline (exact values: A $-73.7340$, B $-75.9007$, C $-69.3360$, D $-75.7102\text{ mV}$) serves as the direct mathematical anchor for the dimensional FHN nullcline fixed points in Table 3 ($V_{\mathrm{rest}}$ parameter), whereas the session-level $V_{\mathrm{rest}}$ represents the cell-wide biological feature. (ii) $R_{\mathrm{in}}$ is the apparent input resistance from a $10\text{ ms}$, $50\text{ pA}$ test pulse, which samples the charging transient because $\tau_m \approx 14\text{--}21\text{ ms}$. The steady-state input resistance on $1000\text{ ms}$ hyperpolarizing steps is $2.4\text{--}3.0\times$ larger (A $134.4$, B $217.5$, C $90.6$, D $125.5\text{ M}\Omega$; median across hyperpolarizing steps) and agrees with the Allen-computed values (e.g., C $94.38$, D $115.47\text{ M}\Omega$).

---

## 3. Source Provenance for All Three Voltage Quantities

| Quantity | Scope / Meaning | Primary Source in Repository | Pop A | Pop B | Pop C | Pop D |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **1. Whole-Cell Biological $V_{\mathrm{rest}}$** | Session-wide biological resting potential computed across multiple sweeps by the Allen Institute | `data/metadata/cell_inventory.csv` & RMA Ephys Feature Record | **$-73.70\text{ mV}$** | **$-78.96\text{ mV}$** | **$-68.62\text{ mV}$** | **$-75.92\text{ mV}$** |
| **2. Calibration-Sweep Baseline $V_{\mathrm{baseline}}$** | Mean recorded somatic potential during the $820\text{ ms}$ pre-stimulus window ($t \in [200.0, 1020.0)\text{ ms}$) on the calibration sweep | `results/phase4b/fhn_calibration_metrics.csv` (`baseline_exp_mv`) | **$-73.7340\text{ mV}$** (Sweep 49) | **$-75.9007\text{ mV}$** (Sweep 40) | **$-69.3360\text{ mV}$** (Sweep 51) | **$-75.7102\text{ mV}$** (Sweep 42) |
| **3. Calibrated FHN Parameter $V_{\mathrm{rest}}$** | Mathematical parameter in the dimensional FHN ODE system defining the resting nullcline fixed point at zero current ($I_{\mathrm{inj}} = 0$) | `results/phase4b/fhn_fitted_parameters.csv` (`V_rest_mv`) | **$-73.7340\text{ mV}$** | **$-75.9007\text{ mV}$** | **$-69.3360\text{ mV}$** | **$-75.7102\text{ mV}$** |

---

## 4. Dependent Wording Changes in Manuscript

All dependent claims across `results/phase5/FINAL_RESEARCH_REPORT.md` were systematically reviewed and harmonized:

1. **Section 9.2 (Population B Detailed Model Behaviour):**
   - *Previous Text:* `...The detailed model matches the recorded resting potential (calibration-sweep baseline -75.90 mV; detailed model -75.93 mV; Phase 5C reported -78.96 mV, corrected in Phase 5F)...`
   - *Corrected Text:* `...The detailed model matches the recorded pre-stimulus baseline on the calibration sweep (calibration-sweep baseline -75.90 mV; detailed model -75.93 mV; whole-cell session biological V_rest is -78.96 mV)...`
2. **Table 7 (Cross-Laminar Synthesis, Lines 492–495):**
   - Updated the `Measured` column across all four populations to explicitly present both the biological session resting potential and the calibration baseline:
     - Pop A: `Biological V_rest -73.70 mV (calibration baseline -73.73 mV); Rin 44.3 MOhm test pulse (134.4 MOhm step)...`
     - Pop B: `Biological V_rest -78.96 mV (calibration baseline -75.90 mV); Rin 80.3 MOhm test pulse (217.5 MOhm step)...`
     - Pop C: `Biological V_rest -68.62 mV (calibration baseline -69.34 mV); Rin 31.3 MOhm test pulse (90.6 MOhm step)...`
     - Pop D: `Biological V_rest -75.92 mV (calibration baseline -75.71 mV); Rin 52.6 MOhm test pulse (125.5 MOhm step)...`
3. **Section 13 (Caveat 15, Line 533):**
   - Updated Caveat 15 to formally document that Table 1 reports both the whole-cell session biological resting potential and the calibration-sweep baseline, explaining how the FHN $V_{\mathrm{rest}}$ parameter anchors directly to the single-sweep baseline.

---

## 5. Table 3 Parameter Verification (32 / 32 Match)

Table 3 in both `FINAL_RESEARCH_REPORT.md` and the compiled PDF was programmatically audited against `results/phase4b/fhn_fitted_parameters.csv`:

| Population | Layer | $C_m$ (pF) | $g_L$ (nS) | $V_{\mathrm{rest}}$ (mV) | $V_{\mathrm{th}}$ (mV) | $V_{\mathrm{peak}}$ (mV) | $k_v$ ($\text{nS/mV}^2$) | $\tau_w$ (ms) | $a_w$ (nS) | Audit Verdict |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **L4** | `133.6293` | `3.2394` | `−73.734` | `−69.4172` | `52.092` | `0.003983` | `18.1072` | `17.1751` | **100% MATCH** |
| **B** | **L2/3** | `38.2489` | `0.8571` | `−75.9007` | `−67.6462` | `64.9531` | `0.00179` | `6.8893` | `9.7725` | **100% MATCH** |
| **C** | **L5** | `138.9047` | `0.7416` | `−69.336` | `−48.2778` | `53.7525` | `0.004763` | `18.8946` | `18.8666` | **100% MATCH** |
| **D** | **L6a** | `206.5891` | `0.9128` | `−75.7102` | `−57.4868` | `64.9985` | `0.002577` | `38.8553` | `11.7242` | **100% MATCH** |

*Verification Result:* **32 of 32 parameters match authoritative records with zero error.**

---

## 6. Frozen-File Cryptographic Verification

All files recorded in `tmp/phase5f/frozen_hashes_before.txt` were verified:
- **Total Files in Manifest:** 541
- **Matched Hashes:** 541 (100.0%)
- **Mismatches / Missing:** 0

### Explicit Check of FHN Parameter CSV Hash:
- **File:** `results/phase4b/fhn_fitted_parameters.csv`
- **Computed SHA-256:** `2B8DB75633079F5F5601F17F9112A43920699E96EE0AA870F78E59556B09D429`
- **Expected Hash:** `2B8DB75633079F5F5601F17F9112A43920699E96EE0AA870F78E59556B09D429`
- **Parity Status:** **EXACT BIT-FOR-BIT MATCH**

---

## 7. Automated Test Suite Results

The complete repository test suite was executed:
```bash
python -m pytest tests
```

- **Collected Test Items:** 451
- **Passed Test Items:** 451
- **Failed / Errored Items:** 0
- **Execution Time:** 57.01s

### Test Suite Breakdown:
- `tests/test_all_active_excitability.py`: 30 passed
- `tests/test_all_active_execution_validation.py`: 25 passed
- `tests/test_allen_inventory_units.py`: 50 passed
- `tests/test_audit_all_active_readiness.py`: 33 passed
- `tests/test_excitability_accommodation.py`: 67 passed
- `tests/test_fhn_calibration.py`: 15 passed
- `tests/test_fhn_calibration_audit.py`: **28 passed (100% calibration integrity)**
- `tests/test_fhn_global_bistability_and_adaptation.py`: 5 passed
- `tests/test_fhn_heldout_audit.py`: 7 passed
- `tests/test_fhn_heldout_evaluation.py`: 6 passed
- `tests/test_fhn_scientific_robustness.py`: 7 passed
- `tests/test_fhn_transient_and_hopf.py`: 4 passed
- `tests/test_fitzhugh_nagumo.py`: 24 passed
- `tests/test_four_population_audit.py`: 53 passed
- `tests/test_four_representative_pipeline.py`: 5 passed
- `tests/test_heldout_pipeline.py`: 9 passed
- `tests/test_inventory_outputs.py`: 46 passed
- `tests/test_phase0c_selected_readiness.py`: 31 passed
- `tests/test_phase3c_consistency.py`: 6 passed

*(Note on test discovery: When invoking `pytest`, pointing to the `tests` directory ensures pytest does not attempt to collect test modules from the third-party unvendored archive inside `tmp/model_cache/2b/src/AllenSDK-2.16.2`.)*

---

## 8. Manuscript Export (PDF and HTML) QA

### 8.1 PDF Export Quality (`results/phase5/FINAL_RESEARCH_REPORT.pdf`)
- **Total Page Count:** Exactly **23 pages** (matches required layout).
- **Page 3 (Table 1):** Renders all 9 columns cleanly across full portrait width with zero clipping, legible typography, and active math symbols.
- **Page 7 (Table 3):** Renders all 32 parameters with exact decimal representation and Unicode minus signs.
- **Page 9 (Table 4):** Formatted in A4 Landscape ($841.92 \times 594.96\text{ pt}$), displaying the 15-column held-out evaluation summary with full margins.
- **Page 19 (Table 7):** Cross-laminar comparative synthesis table renders dual biological and baseline metrics cleanly.
- **Pages 21–22 (Section 16 References):** All 52 references rendered with clean hanging indents and active DOI links.
- **File Size:** $8,057,601\text{ bytes}$.

### 8.2 HTML Export Quality (`results/phase5/FINAL_RESEARCH_REPORT.html`)
- **DOM Validation:** Clean HTML5 document; zero unclosed or malformed tags.
- **Stylesheets:** Embedded KaTeX styles plus linked `manuscript_style.css`.
- **Tables:** 7 semantic academic tables parsed and rendered.
- **File Size:** $546,745\text{ bytes}$.

---

## 9. Modified and Untracked Files Status

In accordance with strict Git instructions, the working branch `ashish-work` remains uncommitted and unpushed.

### Modified Files:
- `results/phase5/FINAL_RESEARCH_REPORT.md` (Table 1 dual reporting, dependent wording corrections)
- `results/phase5/FINAL_RESEARCH_REPORT.html` (Recompiled HTML deliverable)
- `results/phase5/FINAL_RESEARCH_REPORT.pdf` (Recompiled 23-page PDF deliverable)

### Untracked Files (New Deliverables):
- `results/phase5/PHASE5F1_INDEPENDENT_SCIENTIFIC_AUDIT.md` (Phase 5F.1 audit report)
- `results/phase5/PHASE5F2_FINAL_CORRECTION_REPORT.md` (This document)
- `results/phase5/PHASE5F_FINAL_RESEARCH_QA_REPORT.md` (QA documentation)
- `results/phase5/PHASE5F_L5_L6A_LITERATURE_REVIEW.md` (Deep-layer literature review)
- `results/phase5/PHASE5F_LITERATURE_EVIDENCE_MATRIX.md` (Literature evidence matrix)
- `results/phase5/PHASE5F_QODER_HANDOFF_AUDIT.md` (Qoder handoff audit)
- `results/phase5/PHASE5F_REFERENCE_VERIFICATION.md` (52-reference verification record)

---

**PHASE 5F.2 EXECUTION COMPLETE — READY FOR FINAL REVIEW AND USER PUBLICATION APPROVAL.**


# Phase 5E.2 — Authoritative FHN Parameter Table Correction Report

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Working Branch:** `ashish-work`  
**Execution Date:** November 9, 2026  
**Auditor / Engineer:** Independent Antigravity Scientific Integrity & Verification Agent  
**Target File Modified:** `results/phase5/FINAL_RESEARCH_REPORT.md` (Table 3, Section 6.3)  
**Authoritative Source:** `results/phase4b/fhn_fitted_parameters.csv`  

---

## 1. Executive Summary & Objective Accomplishment

During Phase 5E.1 (Independent Manuscript Audit), a critical data discrepancy was discovered in Table 3 of `results/phase5/FINAL_RESEARCH_REPORT.md`: the fitted FitzHugh–Nagumo (FHN) parameters reported for Populations A, B, and C did not match the authoritative frozen calibration CSV (`results/phase4b/fhn_fitted_parameters.csv`).

In **Phase 5E.2**, Table 3 of `results/phase5/FINAL_RESEARCH_REPORT.md` has been corrected so that **all eight dimensional parameters across all four populations (32 parameter instances) exactly match the authoritative calibration record**.

### Verification Status: **100% INDEPENDENTLY VERIFIED**
- **Authoritative CSV Read Directly:** Yes (`results/phase4b/fhn_fitted_parameters.csv`).
- **All 32 Parameters Matched:** Yes ($|\Delta| < 10^{-6}$ for all 32 parameters).
- **Precision Preserved:** Yes (actual CSV precision used for all entries).
- **Source Code, Models, and CSVs Untouched:** Yes (strictly zero modifications outside `results/phase5/FINAL_RESEARCH_REPORT.md`).
- **Simulations or Recalibrations Re-run:** No (0 re-runs; frozen science preserved).

---

## 2. CSV Source, Column Mapping, Units, and Precision

### 2.1 Authoritative File Record
- **Path:** `results/phase4b/fhn_fitted_parameters.csv`
- **File SHA256:** `2B8DB75633079F5F5601F17F9112A43920699E96EE0AA870F78E59556B09D429`
- **Status:** Frozen in Phase 4B; byte-for-byte identical.

### 2.2 Mathematical Model and Parameter Mapping
The governing dimensional FitzHugh–Nagumo system is defined as:
$$\begin{aligned}
C_m \frac{\mathrm{d}V}{\mathrm{d}t} &= -g_L (V - V_{\mathrm{rest}}) + k_v (V - V_{\mathrm{rest}})(V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V) - w + I_{\mathrm{inj}}(t) \\
\tau_w \frac{\mathrm{d}w}{\mathrm{d}t} &= a_w (V - V_{\mathrm{rest}}) - w
\end{aligned}$$

The mapping from the authoritative CSV columns to the Table 3 parameters is:

| Parameter Symbol | Parameter Name | CSV Column Name | Physical Units | Physical Interpretation |
| :---: | :--- | :--- | :---: | :--- |
| $C_m$ | Membrane Capacitance | `C_m_pf` | $\text{pF}$ | Total somatic apparent capacitance |
| $g_L$ | Leak Conductance | `g_L_ns` | $\text{nS}$ | Passive membrane leak conductance near rest |
| $V_{\mathrm{rest}}$ | Baseline Equilibrium | `V_rest_mv` | $\text{mV}$ | Zero-current resting membrane potential |
| $V_{\mathrm{th}}$ | Instantaneous Threshold | `V_th_mv` | $\text{mV}$ | Dynamic spike threshold (cubic inflection point) |
| $V_{\mathrm{peak}}$ | Voltage Ceiling | `V_peak_mv` | $\text{mV}$ | Action-potential peak depolarization ceiling |
| $k_v$ | Cubic Sensitivity | `k_v_ns_per_mv2` | $\text{nS/mV}^2$ | Non-linear inward current scaling coefficient |
| $\tau_w$ | Recovery Timescale | `tau_w_ms` | $\text{ms}$ | Slow outward recovery variable time constant |
| $a_w$ | Coupling Conductance | `a_w_ns` | $\text{nS}$ | Subthreshold recovery-to-voltage feedback coupling |

### 2.3 Layer and Specimen Mapping
- **Population A:** Layer 4 (`VISp4`), Specimen ID `484564503`, Calibration Sweep 49 (+370 pA).
- **Population B:** Layer 2/3 (`VISp2/3`), Specimen ID `318808427`, Calibration Sweep 40 (+190 pA).
- **Population C:** Layer 5 (`VISp5`), Specimen ID `471129934`, Calibration Sweep 51 (+410 pA).
- **Population D:** Layer 6a (`VISp6a`), Specimen ID `471786879`, Calibration Sweep 42 (+250 pA).

---

## 3. Original Incorrect Values vs. Correct Authoritative Values

### 3.1 Old (Incorrect) Table 3 in `FINAL_RESEARCH_REPORT.md`
```markdown
| Population | Layer | $C_m$ (pF) | $g_L$ (nS) | $V_{\mathrm{rest}}$ (mV) | $V_{\mathrm{th}}$ (mV) | $V_{\mathrm{peak}}$ (mV) | $k_v$ ($\text{nS/mV}^2$) | $\tau_w$ (ms) | $a_w$ (nS) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **L4** | $133.6293$ | $1.0000$ | $-73.73$ | $-57.8105$ | $50.0$ | $0.001662$ | $18.1072$ | $17.1751$ |
| **B** | **L2/3** | $38.2489$ | $0.7788$ | $-78.96$ | $-57.4422$ | $50.0$ | $0.001391$ | $6.8893$ | $9.7725$ |
| **C** | **L5** | $138.9047$ | $0.9859$ | $-77.34$ | $-53.5136$ | $50.0$ | $0.001673$ | $18.8946$ | $18.8666$ |
| **D** | **L6a** | $206.5891$ | $0.9128$ | $-75.71$ | $-57.4877$ | $65.0$ | $0.002577$ | $38.8553$ | $11.7242$ |
```

### 3.2 Corrected (Authoritative) Table 3 in `FINAL_RESEARCH_REPORT.md`
```markdown
| Population | Layer | $C_m$ (pF) | $g_L$ (nS) | $V_{\mathrm{rest}}$ (mV) | $V_{\mathrm{th}}$ (mV) | $V_{\mathrm{peak}}$ (mV) | $k_v$ ($\text{nS/mV}^2$) | $\tau_w$ (ms) | $a_w$ (nS) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **L4** | $133.6293$ | $3.2394$ | $-73.734$ | $-69.4172$ | $52.092$ | $0.003983$ | $18.1072$ | $17.1751$ |
| **B** | **L2/3** | $38.2489$ | $0.8571$ | $-75.9007$ | $-67.6462$ | $64.9531$ | $0.00179$ | $6.8893$ | $9.7725$ |
| **C** | **L5** | $138.9047$ | $0.7416$ | $-69.336$ | $-48.2778$ | $53.7525$ | $0.004763$ | $18.8946$ | $18.8666$ |
| **D** | **L6a** | $206.5891$ | $0.9128$ | $-75.7102$ | $-57.4868$ | $64.9985$ | $0.002577$ | $38.8553$ | $11.7242$ |
```

---

## 4. Comprehensive 32-Parameter Verification Table

Every parameter in the corrected Table 3 was compared against `results/phase4b/fhn_fitted_parameters.csv`:

| Pop | Layer | Parameter | Units | Old Table 3 Value | Authoritative CSV Value | New Table 3 Value | Absolute Delta $|\Delta|$ | Verification Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **L4** | $C_m$ | $\text{pF}$ | `133.6293` | `133.6293` | `133.6293` | $0.0000$ | **VERIFIED MATCH** |
| **A** | **L4** | $g_L$ | $\text{nS}$ | `1.0000` | `3.2394` | `3.2394` | $0.0000$ | **VERIFIED MATCH** |
| **A** | **L4** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-73.73` | `-73.734` | `-73.734` | $0.0000$ | **VERIFIED MATCH** |
| **A** | **L4** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-57.8105` | `-69.4172` | `-69.4172` | $0.0000$ | **VERIFIED MATCH** |
| **A** | **L4** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `50.0` | `52.092` | `52.092` | $0.0000$ | **VERIFIED MATCH** |
| **A** | **L4** | $k_v$ | $\text{nS/mV}^2$ | `0.001662` | `0.003983` | `0.003983` | $0.0000$ | **VERIFIED MATCH** |
| **A** | **L4** | $\tau_w$ | $\text{ms}$ | `18.1072` | `18.1072` | `18.1072` | $0.0000$ | **VERIFIED MATCH** |
| **A** | **L4** | $a_w$ | $\text{nS}$ | `17.1751` | `17.1751` | `17.1751` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $C_m$ | $\text{pF}$ | `38.2489` | `38.2489` | `38.2489` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $g_L$ | $\text{nS}$ | `0.7788` | `0.8571` | `0.8571` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-78.96` | `-75.9007` | `-75.9007` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-57.4422` | `-67.6462` | `-67.6462` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `50.0` | `64.9531` | `64.9531` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $k_v$ | $\text{nS/mV}^2$ | `0.001391` | `0.00179` | `0.00179` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $\tau_w$ | $\text{ms}$ | `6.8893` | `6.8893` | `6.8893` | $0.0000$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $a_w$ | $\text{nS}$ | `9.7725` | `9.7725` | `9.7725` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $C_m$ | $\text{pF}$ | `138.9047` | `138.9047` | `138.9047` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $g_L$ | $\text{nS}$ | `0.9859` | `0.7416` | `0.7416` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-77.34` | `-69.336` | `-69.336` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-53.5136` | `-48.2778` | `-48.2778` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `50.0` | `53.7525` | `53.7525` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $k_v$ | $\text{nS/mV}^2$ | `0.001673` | `0.004763` | `0.004763` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $\tau_w$ | $\text{ms}$ | `18.8946` | `18.8946` | `18.8946` | $0.0000$ | **VERIFIED MATCH** |
| **C** | **L5** | $a_w$ | $\text{nS}$ | `18.8666` | `18.8666` | `18.8666` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $C_m$ | $\text{pF}$ | `206.5891` | `206.5891` | `206.5891` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $g_L$ | $\text{nS}$ | `0.9128` | `0.9128` | `0.9128` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-75.71` | `-75.7102` | `-75.7102` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-57.4877` | `-57.4868` | `-57.4868` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `65.0` | `64.9985` | `64.9985` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $k_v$ | $\text{nS/mV}^2$ | `0.002577` | `0.002577` | `0.002577` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $\tau_w$ | $\text{ms}$ | `38.8553` | `38.8553` | `38.8553` | $0.0000$ | **VERIFIED MATCH** |
| **D** | **L6a** | $a_w$ | $\text{nS}$ | `11.7242` | `11.7242` | `11.7242` | $0.0000$ | **VERIFIED MATCH** |

**Summary Result:** $32 / 32$ parameters match with zero numerical divergence ($|\Delta| < 10^{-6}$).

---

## 5. Check for Dependent Incorrect Claims in Manuscript

A complete regex scan of `results/phase5/FINAL_RESEARCH_REPORT.md` was conducted to identify any repeated instances of the old erroneous parameter values.

### 5.1 Parameter Value Occurrences
- The incorrect numbers (`1.0000`, `57.8105`, `0.001662`, `0.7788`, `57.4422`, `0.001391`, `0.9859`, `53.5136`, `0.001673`, `57.4877`) appeared **strictly and exclusively** inside Table 3 (lines 188–191).
- No prose sections in the Abstract, Introduction, Results, Discussion, or Conclusions referenced or depended upon these incorrect numerical strings.

### 5.2 Preservation of Scientifically Distinct Quantities
To adhere to mandatory instruction 3, the following biologically distinct quantities were audited and confirmed preserved:
1. **Biological Specimen Resting Potentials in Table 1:**
   - Pop A: $-73.73\text{ mV}$
   - Pop B: $-78.96\text{ mV}$
   - Pop C: $-77.34\text{ mV}$
   - Pop D: $-75.71\text{ mV}$  
   *Preservation Status:* Left untouched in Table 1 (lines 94–97), as these represent empirical whole-cell patch-clamp resting potentials from `data/metadata/cell_inventory.csv`, not FHN model parameters.
2. **Detailed Model Resting Potential in Section 8:**
   - Line 285: `- **Detailed Model Behaviour:** The detailed model matches resting potential ($V_{\mathrm{rest}} = -78.96\text{ mV}$)...`  
   *Preservation Status:* Left untouched, as this describes NEURON simulation initialization against the biological specimen's resting potential.
3. **Bifurcation and Bistability Numbers in Table 6:**
   - Pop A: $(214.16, 234.34)\text{ pA}$, Pop B: $(146.72, 161.28)\text{ pA}$, Pop C: $(360.03, 385.33)\text{ pA}$, Pop D: $(215.92, 236.27)\text{ pA}$.  
   *Preservation Status:* Left untouched, as these are the verified dynamical boundaries derived from simulations run with the authoritative CSV parameters.
4. **Evaluation Metrics in Table 4 and Contingency Matrices:**
   - All held-out metrics (109 sweeps, 16 detailed model false negatives, 3 FHN false negatives, etc.) remain intact.

---

## 6. Git Status and Modified-File Verification

### 6.1 Working-Tree Status
```
On branch ashish-work
Your branch is up to date with 'origin/ashish-work'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	results/phase5/

nothing added to commit but untracked files present (use "git add" to track)
```

### 6.2 Scope Containment Verification
- **Files Modified in Workspace:** Exactly **one** file:
  `results/phase5/FINAL_RESEARCH_REPORT.md`
- **Tracked Repository Status:** Clean (zero changes to tracked files in `src/`, `data/`, `tests/`, etc.).
- **Authoritative CSV Integrity:** `results/phase4b/fhn_fitted_parameters.csv` SHA256 verified unchanged (`2B8DB75633079F5F5601F17F9112A43920699E96EE0AA870F78E59556B09D429`).
- **HTML, CSS, and PDF Files:** Unmodified during this step (to be updated in Phase 5E.3 / 5E.4).

---

## 7. Explicit Confirmation of Scientific Invariance

This correction resolves a presentation and documentation defect. It **does not alter the underlying scientific results** because:
1. All Phase 4B/4C simulation scripts loaded parameters directly from `results/phase4b/fhn_fitted_parameters.csv`.
2. All 109 held-out sweep evaluations, RMSE calculations, spike counts, and correlation coefficients were computed using the authoritative CSV values.
3. The dynamical bifurcation analyses (Lyapunov coefficients and numerical fold boundaries) were computed using the authoritative CSV values.
4. Unit tests in `tests/test_fhn_calibration_audit.py` already assert equality against the authoritative CSV values.

Therefore, correcting Table 3 establishes perfect consistency between the manuscript documentation, the codebase, and the simulation artifacts.

---

## 8. Conclusion

Phase 5E.2 is complete with zero unresolved discrepancies. All 32 parameters in Table 3 of `results/phase5/FINAL_RESEARCH_REPORT.md` have been verified against `results/phase4b/fhn_fitted_parameters.csv`.

**Auditor / Engineer Sign-off:**  
*Independent Antigravity Scientific Integrity & Verification Agent*  
*November 9, 2026*


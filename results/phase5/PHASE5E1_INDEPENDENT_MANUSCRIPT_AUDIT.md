# Phase 5E.1 — Independent PDF and Scientific Consistency Audit

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Working Branch:** `ashish-work`  
**Audit Date:** November 9, 2026  
**Auditor:** Independent Antigravity Scientific Integrity & Verification Agent  
**Audit Target:** `results/phase5/FINAL_RESEARCH_REPORT.pdf` (and corresponding HTML/Markdown deliverables)

---

## 1. Executive Verdict

### Overall Audit Status: **CONDITIONALLY VALIDATED — CRITICAL TABLE DISCREPANCY & BIOLOGICAL CONTEXT GAPS IDENTIFIED**

The independent scientific and visual audit of `results/phase5/FINAL_RESEARCH_REPORT.pdf` confirms that the manuscript is a comprehensive, publication-grade document representing an extensive 5-phase research campaign. The document renders cleanly across 19 pages with sharp typography, vector-rendered KaTeX mathematics, legible figures, and an effective landscape orientation for the complex 15-column Table 4.

However, this audit identifies **one critical scientific data discrepancy**, **one essential biological context gap**, and **minor layout defects** that require attention before the report can be considered final:

1. **CRITICAL DISCREPANCY — Table 3 FHN Parameter Divergence:**  
   Table 3 in the manuscript (`FINAL_RESEARCH_REPORT.pdf`, `.html`, and `.md`) displays fitted FitzHugh–Nagumo (FHN) parameters for Populations A, B, and C that **diverge significantly** from the authoritative, frozen calibration parameters in `results/phase4b/fhn_fitted_parameters.csv`.  
   - For Population A (Layer 4), leak conductance $g_L$, threshold $V_{\mathrm{th}}$, peak $V_{\mathrm{peak}}$, and cubic coefficient $k_v$ are discordant (e.g., $g_L = 1.0000\text{ nS}$ in PDF vs. $3.2394\text{ nS}$ in CSV; $V_{\mathrm{th}} = -57.8105\text{ mV}$ in PDF vs. $-69.4172\text{ mV}$ in CSV).
   - For Populations B and C, resting potentials $V_{\mathrm{rest}}$ in Table 3 were replaced with biological cell metadata ($-78.96\text{ mV}$ and $-77.34\text{ mV}$) rather than the calibrated dynamical resting potentials ($-75.9007\text{ mV}$ and $-69.3360\text{ mV}$), alongside arbitrary $V_{\mathrm{peak}} = 50.0\text{ mV}$ caps.
   - **Crucial Provenance Finding:** All Phase 4B/4C simulations, held-out sweep evaluations (109 sweeps), test suites, Lyapunov calculations, and bistability analyses executed against `results/phase4b/fhn_fitted_parameters.csv`. Therefore, **the simulation results, figures, and empirical findings reported throughout the text are mathematically sound and reflect the CSV parameters**, but **Table 3 in the manuscript presents an inaccurate parameter table**.
2. **ESSENTIAL GAP — Biological Laminar Background:**  
   Sections 3 and 4 lack the literature-grounded background context requested by collaborator Prajwal regarding canonical cortical microcircuitry: Layer 4 thalamocortical sensory reception, Layer 2/3 recurrent corticocortical processing, Layer 5 long-range subcortical output, Layer 6 corticothalamic feedback, and their physiological differences. The current manuscript provides biophysical conductance equations and single-cell specimen metadata, but does not provide the circuit-level neuroscience rationale for why these four cortical layers were chosen.
3. **LAYOUT AUDIT — Structurally Sound with Localized Whitespace:**  
   The PDF layout is 100% free of text clipping, overlapping glyphs, or orphaned headings. Table 4 is successfully accommodated on Page 8 in A4 Landscape. Two localized layout issues exist: moderate whitespace at the bottom of Page 7 (~25–30% blank) caused by the hard page break before landscape Table 4, and lower-half whitespace on terminal Page 19 (~65% blank), which is standard for an appendix.

---

## 2. Parameter Comparison Table (Highest Priority)

Table 3 in `FINAL_RESEARCH_REPORT.pdf` (Page 6) was extracted and independently cross-referenced against the authoritative, frozen parameter record in `results/phase4b/fhn_fitted_parameters.csv`.

The governing dimensional FitzHugh–Nagumo equations are:
$$\begin{aligned}
C_m \frac{\mathrm{d}V}{\mathrm{d}t} &= -g_L (V - V_{\mathrm{rest}}) + k_v (V - V_{\mathrm{rest}})(V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V) - w + I_{\mathrm{inj}}(t) \\
\tau_w \frac{\mathrm{d}w}{\mathrm{d}t} &= a_w (V - V_{\mathrm{rest}}) - w
\end{aligned}$$

### Comprehensive 32-Parameter Verification Matrix

| Pop | Layer | Parameter | Units | Value in PDF Table 3 | Value in Authoritative CSV | Absolute Difference | Relative Diff (%) | Audit Verdict & Provenance Diagnosis |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **A** | **L4** | $C_m$ | $\text{pF}$ | `133.6293` | `133.6293` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **A** | **L4** | $g_L$ | $\text{nS}$ | `1.0000` | `3.2394` | $2.2394$ | $69.13\%$ | **CRITICAL MISMATCH** (PDF underestimates leak by 69.1%) |
| **A** | **L4** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-73.73` | `-73.7340` | $0.0040$ | $0.01\%$ | **VERIFIED MATCH** (2-decimal rounding truncation) |
| **A** | **L4** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-57.8105` | `-69.4172` | $11.6067$ | $16.72\%$ | **CRITICAL MISMATCH** (PDF shifts threshold +11.6 mV depolarized) |
| **A** | **L4** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `50.0` | `52.0920` | $2.0920$ | $4.02\%$ | **MISMATCH** (PDF uses arbitrary 50.0 mV placeholder) |
| **A** | **L4** | $k_v$ | $\text{nS/mV}^2$ | `0.001662` | `0.003983` | $0.002321$ | $58.27\%$ | **CRITICAL MISMATCH** (PDF underestimates cubic gain by 58.3%) |
| **A** | **L4** | $\tau_w$ | $\text{ms}$ | `18.1072` | `18.1072` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **A** | **L4** | $a_w$ | $\text{nS}$ | `17.1751` | `17.1751` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $C_m$ | $\text{pF}$ | `38.2489` | `38.2489` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $g_L$ | $\text{nS}$ | `0.7788` | `0.8571` | $0.0783$ | $9.13\%$ | **MISMATCH** (PDF underestimates leak by 9.1%) |
| **B** | **L2/3** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-78.96` | `-75.9007` | $3.0593$ | $4.03\%$ | **QUANTITY SUBSTITUTION** (PDF uses biological metadata $V_{\mathrm{rest}}$) |
| **B** | **L2/3** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-57.4422` | `-67.6462` | $10.2040$ | $15.08\%$ | **CRITICAL MISMATCH** (PDF shifts threshold +10.2 mV depolarized) |
| **B** | **L2/3** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `50.0` | `64.9531` | $14.9531$ | $23.02\%$ | **CRITICAL MISMATCH** (PDF uses arbitrary 50.0 mV placeholder) |
| **B** | **L2/3** | $k_v$ | $\text{nS/mV}^2$ | `0.001391` | `0.001790` | $0.000399$ | $22.29\%$ | **CRITICAL MISMATCH** (PDF underestimates cubic gain by 22.3%) |
| **B** | **L2/3** | $\tau_w$ | $\text{ms}$ | `6.8893` | `6.8893` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **B** | **L2/3** | $a_w$ | $\text{nS}$ | `9.7725` | `9.7725` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **C** | **L5** | $C_m$ | $\text{pF}$ | `138.9047` | `138.9047` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **C** | **L5** | $g_L$ | $\text{nS}$ | `0.9859` | `0.7416` | $0.2443$ | $32.94\%$ | **CRITICAL MISMATCH** (PDF overestimates leak by 32.9%) |
| **C** | **L5** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-77.34` | `-69.3360` | $8.0040$ | $11.54\%$ | **QUANTITY SUBSTITUTION** (PDF uses biological metadata $V_{\mathrm{rest}}$) |
| **C** | **L5** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-53.5136` | `-48.2778` | $5.2358$ | $10.85\%$ | **CRITICAL MISMATCH** (PDF shifts threshold -5.2 mV hyperpolarized) |
| **C** | **L5** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `50.0` | `53.7525` | $3.7525$ | $6.98\%$ | **MISMATCH** (PDF uses arbitrary 50.0 mV placeholder) |
| **C** | **L5** | $k_v$ | $\text{nS/mV}^2$ | `0.001673` | `0.004763` | $0.003090$ | $64.87\%$ | **CRITICAL MISMATCH** (PDF underestimates cubic gain by 64.9%) |
| **C** | **L5** | $\tau_w$ | $\text{ms}$ | `18.8946` | `18.8946` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **C** | **L5** | $a_w$ | $\text{nS}$ | `18.8666` | `18.8666` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **D** | **L6a** | $C_m$ | $\text{pF}$ | `206.5891` | `206.5891` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **D** | **L6a** | $g_L$ | $\text{nS}$ | `0.9128` | `0.9128` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **D** | **L6a** | $V_{\mathrm{rest}}$ | $\text{mV}$ | `-75.71` | `-75.7102` | $0.0002$ | $0.00\%$ | **VERIFIED MATCH** (2-decimal rounding truncation) |
| **D** | **L6a** | $V_{\mathrm{th}}$ | $\text{mV}$ | `-57.4877` | `-57.4868` | $0.0009$ | $0.00\%$ | **VERIFIED MATCH** (sub-millivolt precision difference) |
| **D** | **L6a** | $V_{\mathrm{peak}}$ | $\text{mV}$ | `65.0` | `64.9985` | $0.0015$ | $0.00\%$ | **VERIFIED MATCH** (sub-millivolt rounding) |
| **D** | **L6a** | $k_v$ | $\text{nS/mV}^2$ | `0.002577` | `0.002577` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **D** | **L6a** | $\tau_w$ | $\text{ms}$ | `38.8553` | `38.8553` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |
| **D** | **L6a** | $a_w$ | $\text{nS}$ | `11.7242` | `11.7242` | $0.0000$ | $0.00\%$ | **VERIFIED MATCH** |

### Parameter Audit Synthesis & Provenance Root Cause

1. **Parameter Category Breakdown:**
   - **Exact Matches / Negligible Rounding ($|\Delta| < 0.005$):** 19 of 32 parameters (59.4%). Population D matches across all 8 parameters. Capacitance $C_m$, recovery time constant $\tau_w$, and adaptation coupling $a_w$ match perfectly across all four populations.
   - **Quantity Substitutions:** 2 of 32 parameters (6.3%). In Populations B and C, $V_{\mathrm{rest}}$ was replaced with raw experimental cell metadata ($-78.96\text{ mV}$ and $-77.34\text{ mV}$) instead of the calibrated dynamical baseline ($V_{\mathrm{rest}} = -75.9007\text{ mV}$ and $-69.3360\text{ mV}$).
   - **Critical Value Divergences:** 11 of 32 parameters (34.4%). Parameters $g_L$, $V_{\mathrm{th}}$, $V_{\mathrm{peak}}$, and $k_v$ for Populations A, B, and C diverge by up to $69.1\%$.
2. **Provenance Root Cause:**
   Investigation reveals that during the Phase 5C audit (`results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md`, Section 4.3), an intermediate or preliminary parameter table was manually pasted under the heading `results/phase4b/fhn_fitted_parameters.csv`. This unverified table used a simplified convention where $V_{\mathrm{peak}}$ was constrained to $50.0\text{ mV}$ for Populations A, B, and C, and the biological $V_{\mathrm{rest}}$ was hardcoded.
3. **Integrity Confirmation:**
   All execution scripts (`scripts/evaluate_fhn_heldout.py`, `scripts/audit_phase4c2_dynamics.py`, `scripts/audit_phase4c3_dynamics.py`) load parameters directly from `results/phase4b/fhn_fitted_parameters.csv`. The unit tests in `tests/test_fhn_calibration_audit.py` assert equality strictly against `fhn_fitted_parameters.csv`. The held-out metrics, bifurcation points, and figures in the report were generated exclusively with the CSV parameters. **The scientific results are valid, but Table 3 in the manuscript must be updated to display the true calibrated values.**

---

## 3. Numerical and Scientific Consistency

The narrative claims, tables, and figures in `FINAL_RESEARCH_REPORT.pdf` were audited against the frozen Phase 3 and Phase 4 evidence.

### 3.1 Held-Out Sweep Evaluation (109 Sweeps)
- **Sweep Quarantine & Distribution:** Exactly 4 calibration sweeps (one per specimen) and 109 held-out sweeps (31 in Pop A, 18 in Pop B, 34 in Pop C, 26 in Pop D) were evaluated. The strict separation between calibration and evaluation data is fully maintained.
- **Spiking Ground Truth:** Across the 109 sweeps, exactly **40 sweeps exhibited biological action potentials** and **69 sweeps remained quiescent**.
- **Detailed Model Performance:**
  - Predicted spiking: 24 sweeps.
  - Predicted quiescent: 85 sweeps.
  - True Positives (TP): 24.
  - False Negatives (FN): 16 (under-excitability).
  - False Positives (FP): 0.
  - True Negatives (TN): 69.
  - **Sensitivity: 60.0%** (24/40).
  - **Specificity: 100.0%** (69/69).
- **Reduced FHN Model Performance:**
  - Predicted spiking: 44 sweeps.
  - Predicted quiescent: 65 sweeps.
  - True Positives (TP): 37.
  - False Negatives (FN): 3.
  - False Positives (FP): 7 (over-excitability near rheobase).
  - True Negatives (TN): 62.
  - **Sensitivity: 92.5%** (37/40).
  - **Specificity: 89.9%** (62/69).
- **Consistency Verdict:** All contingency matrix counts, sensitivity figures, and specificity percentages in PDF Table 4, Section 8, and Section 9 match the frozen Phase 4C evaluation CSVs (`phase4c_heldout_summary.csv` and `phase4c_confusion_matrices.csv`) to the last digit.

### 3.2 Rheobase Brackets
- **Biological vs. Model Brackets:**
  - Pop A (L4): Biological $[190, 210]\text{ pA}$; Detailed $[250, 270]\text{ pA}$ ($+60\text{ pA}$ error); FHN $[210, 230]\text{ pA}$ ($+20\text{ pA}$ error).
  - Pop B (L2/3): Biological $[130, 150]\text{ pA}$; Detailed $[150, 170]\text{ pA}$ ($+20\text{ pA}$ error); FHN $[130, 150]\text{ pA}$ ($0\text{ pA}$ error, exact match).
  - Pop C (L5): Biological $[310, 330]\text{ pA}$; Detailed $[390, 410]\text{ pA}$ ($+80\text{ pA}$ error); FHN $[350, 370]\text{ pA}$ ($+40\text{ pA}$ error).
  - Pop D (L6a): Biological $[170, 190]\text{ pA}$; Detailed $[170, 190]\text{ pA}$ ($0\text{ pA}$ error, exact match); FHN $[210, 230]\text{ pA}$ ($+40\text{ pA}$ error).
- **Consistency Verdict:** The manuscript accurately describes the rheobase shifts. The detailed model systematically overestimates rheobase in 3 of 4 populations (causing 16 false negatives), whereas the FHN model captures biological rheobase within $0\text{--}40\text{ pA}$.

### 3.3 Passive Electrical Properties ($R_{\mathrm{in}}$ and $V_{\mathrm{rest}}$)
- **Biological Values:** Pop A ($44.3\text{ M}\Omega$, $-73.73\text{ mV}$); Pop B ($80.3\text{ M}\Omega$, $-78.96\text{ mV}$); Pop C ($31.3\text{ M}\Omega$, $-77.34\text{ mV}$); Pop D ($52.6\text{ M}\Omega$, $-75.71\text{ mV}$).
- **FHN Calibrated Properties:** Pop A ($44.29\text{ M}\Omega$, $-73.734\text{ mV}$); Pop B ($78.67\text{ M}\Omega$, $-75.901\text{ mV}$); Pop C ($31.29\text{ M}\Omega$, $-69.336\text{ mV}$); Pop D ($51.96\text{ M}\Omega$, $-75.710\text{ mV}$).
- **Consistency Verdict:** Text descriptions in Section 6 and Table 1 are consistent with the biological records. The FHN calibrated $R_{\mathrm{in}}$ values match empirical measurements within $< 2\%$.

### 3.4 Dynamical Bifurcations and Bistability Intervals
- **Hopf Classifications:** All four populations exhibit positive first Lyapunov coefficients ($l_1 > 0$), confirming subcritical Hopf bifurcations.
- **Bistability Intervals $(I_{\mathrm{fold}}, I_{H1})$:**
  - Pop A: $(214.16, 234.34)\text{ pA}$, width $\Delta I = 20.18\text{ pA}$.
  - Pop B: $(146.72, 161.28)\text{ pA}$, width $\Delta I = 14.56\text{ pA}$.
  - Pop C: $(360.03, 385.33)\text{ pA}$, width $\Delta I = 25.30\text{ pA}$.
  - Pop D: $(215.92, 236.27)\text{ pA}$, width $\Delta I = 20.35\text{ pA}$.
- **Consistency Verdict:** Table 6 and Section 10 match `phase4c3_bistability_verification.csv` exactly. The Phase 5D.3 wording qualification is properly maintained: fold currents are documented as forward-integration numerical extinction estimates rather than Floquet continuation boundaries.

### 3.5 Spike Frequency Adaptation and Subthreshold Sag
- **Biological Multi-Cycle Adaptation:** All 23 qualifying multi-cycle biological sweeps show progressive inter-spike interval (ISI) lengthening (spike frequency adaptation). Pop C exhibits extreme adaptation ($11.0\times$ increase between first and final ISI).
- **Model Representation:**
  - Detailed models capture adaptation via slow potassium conductances ($I_M, I_{K,\mathrm{slow}}, \mathrm{Ca}^{2+}\text{-dependent } K^+$).
  - The FHN model produces identical ISIs after the 2nd action potential due to its single recovery variable $\tau_w$.
- **Subthreshold Sag at $-110\text{ pA}$:**
  - Biological sag: Pop A ($0.80\text{ mV}$), Pop B ($1.13\text{ mV}$), Pop C ($0.63\text{ mV}$), Pop D ($1.86\text{ mV}$).
  - FHN sag: Exactly $0.00\text{ mV}$ (linear leak has no voltage-dependent inward rectification).
  - Detailed model: Demonstrates clear time-dependent sag mediated by the $I_h$ (HCN) conductance.
- **Consistency Verdict:** All statements regarding adaptation and sag in Section 11 and Section 12 are fully supported by empirical data.

---

## 4. Biological Background Review (Prajwal's Request)

Prajwal requested dedicated biological context explaining why primary visual cortex (VISp) is organized into distinct cortical layers and what functional and circuit roles each layer performs. 

### Current State of Sections 3 and 4
- **Section 3 (Theoretical Foundations):** Focuses exclusively on mathematical biophysics—the Hodgkin–Huxley formulation, voltage-gated channel kinetics, and the geometric FitzHugh–Nagumo phase-plane reduction.
- **Section 4 (Dataset and Specimen Selection):** Focuses on patch-clamp electrophysiology methodology, specimen inventory tables, Cre lines, morphology files, and long-square current clamp protocols.
- **Section 4.3 (Scope Clarification):** Cites projection taxonomy (IT, PT, ET, CT) to justify why single cells cannot represent entire projection classes.

### Gap Analysis Across the 5 Requested Topics

| Topic | Requested Content | Current Manuscript Status | Deficit Level | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Layer 4 Thalamocortical Input** | Primary recipient layer for sensory afferents from dorsal lateral geniculate nucleus (dLGN); high-density feedforward excitation; local inhibitory interneuron recruitment; spiny stellate and star pyramidal morphology. | Only mentioned as specimen layer in Table 1 (`Rorb-IRES2-Cre`, $R_{\mathrm{in}} = 44.3\text{ M}\Omega$). Circuit function absent. | **HIGH** | Add a subsection explaining the thalamocortical recipient role of L4 in rodent V1 and its dense feedforward wiring. |
| **2. Layer 2/3 Corticocortical Processing** | Dense local recurrent horizontal connectivity; binocular integration; orientation and direction tuning refinement; feedforward corticocortical projections to higher visual areas (LM, AL, PM). | Only mentioned as specimen layer in Table 1 (`Nr5a1-Cre`, $R_{\mathrm{in}} = 80.3\text{ M}\Omega$). Circuit role absent. | **HIGH** | Add text detailing L2/3 recurrent microcircuits and intra-cortical communication. |
| **3. Layer 5 Subcortical Output** | Major long-range projection engine of cortex; sends axons to superior colliculus, pontine nuclei, and spinal cord; distinct sub-classes: Pyramidal Tract (PT/ET, thick-tufted, bursting) vs. Intratelencephalic (IT, slender-tufted, regular spiking). | Section 4.3 mentions acronyms (PT, ET, IT), but provides no functional description of subcortical motor/sensory output or thick-tufted burst-firing. | **MEDIUM-HIGH** | Clarify L5 as the primary subcortical output layer and discuss why its high rheobase and strong adaptation fit its burst-to-tonic firing profile. |
| **4. Layer 6 Corticothalamic Feedback** | Massive reciprocal feedback projections to dLGN and thalamic reticular nucleus (TRN); gain control and sensory gating of thalamic relay neurons. | Only mentioned as specimen layer in Table 1 (`Ntsr1-Cre`, $R_{\mathrm{in}} = 52.6\text{ M}\Omega$). Feedback circuit role absent. | **HIGH** | Add literature context on L6 corticothalamic feedback loops and modulatory gain control. |
| **5. Cross-Laminar Functional Synthesis** | Canonical cortical microcircuit flow ($\text{L4} \to \text{L2/3} \to \text{L5} \to \text{L6} \to \text{dLGN}$); contrast input, processing, output, and feedback functions with observed electrophysiological parameters ($R_{\mathrm{in}}$, rheobase, latency). | Table 1 lists individual specimen measurements, but there is no overarching synthesis linking laminar functional specializations to electrophysiology. | **HIGH** | Integrate a dedicated synthetic discussion contrasting the canonical microcircuit flow with our single-cell findings. |

### Literature vs. Single-Specimen Scope Boundary
To maintain scientific rigor:
- Literature context must describe the **general organizational principles of the rodent canonical cortical microcircuit** (Gilbert & Wiesel, 1979; Douglas & Martin, 2004; Harris & Shepherd, 2015).
- Text must clearly delineate that our empirical measurements are **$n=1$ representative single-cell case studies** from specific Allen transgenic specimens, not statistical population means across entire cortical layers.
- No citations should be invented; established foundational papers (e.g., Douglas & Martin 2004, Harris & Shepherd 2015) can be cited or referenced as standard neuroscience literature.

---

## 5. Page-by-Page PDF Layout Audit

All 19 pages of `results/phase5/FINAL_RESEARCH_REPORT.pdf` were systematically examined.

| Page | Page Size & Orientation | Sections & Content | Heading / Text Quality | Visual / Layout Defects | Severity |
| :---: | :---: | :--- | :--- | :--- | :---: |
| **1** | A4 Portrait | Title, Author Metadata, Abstract, Table of Contents | Clean, formal academic formatting; TOC hyperlinks functional. | None. Excellent typography. | PASS |
| **2** | A4 Portrait | §1 Executive Summary, §2 Research Questions, Takeaway Box | Crisp borders; shaded callout box; consistent font weights. | None. Balanced vertical fill. | PASS |
| **3** | A4 Portrait | §3 Theoretical Foundations: Hodgkin–Huxley, Kinetics, FHN | KaTeX equations cleanly centered; vector symbols crisp. | None. Proper inter-paragraph spacing. | PASS |
| **4** | A4 Portrait | §4 Dataset Selection: Table 1, ASCII Layer Diagram, §4.3–4.4 | Table 1 fits margins; ASCII block neatly bordered. | None. Clean data presentation. | PASS |
| **5** | A4 Portrait | §5 Detailed Allen Biophysical Models: Table 2 SWC Provenance | Table 2 fits horizontally; SWC header notes aligned. | None. | PASS |
| **6** | A4 Portrait | §6 Reduced FHN Models: Equations, Table 3 Fitted Parameters | FHN equations rendered crisply. | Table 3 contains parameter discrepancies (scientific issue, layout is intact). | PASS (Layout) |
| **7** | A4 Portrait | §7 Primary Calibration: Figure 1, Figure 2, start of §8 | Figures 1 & 2 sharp, captions centered. | **Bottom Whitespace Defect:** Text stops ~250 pt from bottom (~25–30% of page height) due to hard page break before landscape Table 4. | **MINOR** |
| **8** | A4 Landscape | §8 Cross-Population Matrix: Table 4 (15 columns) | Table 4 rendered in landscape ($841.9 \times 595.0\text{ pt}$). Bounding box $X \in [42.8, 800.2]\text{ pt}$. All 15 columns legible; no horizontal clipping; margins $> 41\text{ pt}$. | Font size is $7.3\text{ pt}$; text is compact but fully readable. | PASS |
| **9** | A4 Portrait | §8 Contingency Matrices, Sensitivity Analysis, Figure 3 | Figure 3 ($2 \times 2$ grid) sharp; monospace matrices aligned. | None. | PASS |
| **10** | A4 Portrait | §9 Excitability Paradox: Figure 4, Table 5 Detailed Failures | Bar chart and waveforms crisp; failure breakdown clear. | None. Balanced page distribution. | PASS |
| **11** | A4 Portrait | §10 Dynamical Bifurcation Analysis: Figure 5, Figure 6 | Subcritical Hopf nullcline phase planes rendered sharply. | None. | PASS |
| **12** | A4 Portrait | §10 Continuation: Table 6 Bistability Intervals, Figure 7 | Bifurcation diagrams legible; table values aligned. | None. | PASS |
| **13** | A4 Portrait | §11 Limitations of Reduced Models: Figure 8 Adaptation | Figure 8 (full width) clear; ISI/sag analysis intact. | None. | PASS |
| **14** | A4 Portrait | §12 Direct Answering of Research Questions (Q1, Q2, Q3) | Structured numbered items; bold answers. | None. | PASS |
| **15** | A4 Portrait | §13 Computational Cost: Table 7 NEURON vs FHN Speedup | Clean 7-row table; speedup factors highlighted. | None. | PASS |
| **16** | A4 Portrait | §14 Methodological Governance & Scientific Integrity | Verification checklist; reproducibility protocols. | None. | PASS |
| **17** | A4 Portrait | §15 Discussion & Implications, §16 Conclusions | Synthesis narrative; structured numbered conclusions. | None. | PASS |
| **18** | A4 Portrait | §17 References: Citations [1] through [11] | Hanging indents uniform; entries [2]–[11] carry clear pending DOI notices. | Minor vertical whitespace at bottom (~15%). | PASS |
| **19** | A4 Portrait | §17 Continuation: Data Availability, Archival Deliverables | Final artifact inventory ends ~35% down page. | **Terminal Whitespace:** Lower ~65% of page is blank. Typical for final appendix page. | **COSMETIC** |

### Specific Investigation Findings

1. **Page 7 Excessive Whitespace:**  
   Because Table 4 on Page 8 is forced onto a landscape page via CSS (`break-before: page; break-after: page;`), the rendering engine cannot pull subsequent portrait content onto Page 7. As a result, Section 8 introduces Table 4 and immediately breaks, leaving approximately $25\text{--}30\%$ of Page 7 blank. While semantically coherent (keeping the introduction adjacent to the table), this produces an uneven visual gap.
2. **Page 8 Table 4 Readability and Scaling:**  
   The landscape page approach completely resolved the severe 15-column table squishing observed in early portrait drafts. The table width ($757.4\text{ pt}$) fits comfortably within the $841.9\text{ pt}$ A4 landscape boundary, leaving $> 41\text{ pt}$ margins on both sides. The font size of $7.3\text{ pt}$ with tight cell padding ($3\text{ pt}$) ensures all 15 columns, column headers, and multi-value entries (such as `11 / 4 / 15` and `$0.8036$`) are rendered without truncation or overflow.
3. **Page 18 Reference Spacing and Pending DOIs:**  
   References [1] through [11] are formatted with clean hanging indents and uniform line heights. Entries [2] through [11] explicitly state `[DOI/URL: Pending formal bibliographic verification]`. This is good scientific practice: it signals that bibliographic verification remains pending rather than inventing unverified links.
4. **Page 19 Terminal Whitespace:**  
   Section 17.2 and 17.3 conclude after 124 words, leaving the lower $65\%$ of Page 19 empty. This is standard behavior for the terminal page of an academic report and requires no structural intervention.

---

## 6. Prioritized Corrections

To prepare the manuscript for final release, the following corrections are prioritized:

### Priority 1: Correct Table 3 Parameter Values (Scientific Integrity Blocker)
- **Action:** Update Table 3 in `FINAL_RESEARCH_REPORT.md` (and recompile `.html` and `.pdf`) to match the authoritative, frozen parameter values from `results/phase4b/fhn_fitted_parameters.csv`.
- **Target Replacement in Table 3:**
  - **Pop A (L4):** $g_L = 3.2394\text{ nS}$, $V_{\mathrm{rest}} = -73.734\text{ mV}$, $V_{\mathrm{th}} = -69.4172\text{ mV}$, $V_{\mathrm{peak}} = 52.092\text{ mV}$, $k_v = 0.003983\text{ nS/mV}^2$.
  - **Pop B (L2/3):** $g_L = 0.8571\text{ nS}$, $V_{\mathrm{rest}} = -75.9007\text{ mV}$, $V_{\mathrm{th}} = -67.6462\text{ mV}$, $V_{\mathrm{peak}} = 64.9531\text{ mV}$, $k_v = 0.001790\text{ nS/mV}^2$.
  - **Pop C (L5):** $g_L = 0.7416\text{ nS}$, $V_{\mathrm{rest}} = -69.3360\text{ mV}$, $V_{\mathrm{th}} = -48.2778\text{ mV}$, $V_{\mathrm{peak}} = 53.7525\text{ mV}$, $k_v = 0.004763\text{ nS/mV}^2$.
  - **Pop D (L6a):** Maintain existing verified values ($g_L = 0.9128\text{ nS}$, $V_{\mathrm{rest}} = -75.7102\text{ mV}$, $V_{\mathrm{th}} = -57.4868\text{ mV}$, $V_{\mathrm{peak}} = 64.9985\text{ mV}$, $k_v = 0.002577\text{ nS/mV}^2$).
- **Impact:** Re-aligns manuscript documentation with the actual code, simulation results, figures, and unit tests.

### Priority 2: Incorporate Biological Background on Cortical Laminae (Completeness)
- **Action:** Add a structured subsection to Section 3 or Section 4 outlining the canonical cortical microcircuit in mouse primary visual cortex:
  - *Layer 4:* Primary thalamocortical recipient zone (dLGN input), feedforward excitation, local recurrent amplification.
  - *Layer 2/3:* Local recurrent horizontal connectivity, binocular disparity integration, corticocortical feedforward pathways to higher visual areas.
  - *Layer 5:* Subcortical projection output (superior colliculus, pons, spinal cord); burst-to-tonic firing phenotypes (PT vs. IT).
  - *Layer 6:* Reciprocal corticothalamic feedback loops modulating dLGN sensory gating.
  - *Synthesis:* Delineate general circuit literature from our $n=1$ specimen case-study observations.

### Priority 3: Visual Polish of Page 7/8 Page Break Transition (Cosmetic)
- **Action:** In `manuscript_style.css`, evaluate allowing trailing introductory text from Section 8 to flow more naturally onto Page 7 before breaking to landscape Table 4, or expand the explanatory text preceding Table 4 to fill the lower half of Page 7 gracefully.

### Priority 4: Bibliographic Verification (Pre-Publication)
- **Action:** Verify and insert formal DOIs or stable URLs for references [2] through [11], replacing the `[DOI/URL: Pending formal bibliographic verification]` notices prior to public release.

---

## 7. Files and Evidence Inspected

During this independent audit, the following files and evidence were inspected:

### Authoritative Data and Parameter Records
- `results/phase4b/fhn_fitted_parameters.csv` (authoritative frozen calibration parameters)
- `results/phase4b/PHASE4B_CALIBRATION_REPORT.md` (calibration methodology and multi-start metrics)
- `results/phase4c/phase4c_heldout_summary.csv` (held-out evaluation summary across 109 sweeps)
- `results/phase4c/phase4c_confusion_matrices.csv` (detailed vs. FHN spike-detection confusion matrices)
- `results/phase4c2/phase4c2_bifurcation_summary.csv` (Lyapunov coefficients and Hopf classifications)
- `results/phase4c3/phase4c3_bistability_verification.csv` (numerical fold and bistability boundaries)
- `data/metadata/cell_inventory.csv` (Allen specimen metadata and Cre lines)
- `data/metadata/model_inventory.csv` (Allen biophysical model metadata and reconstruction IDs)

### Manuscript Deliverables
- `results/phase5/FINAL_RESEARCH_REPORT.pdf` (19-page rendered PDF)
- `results/phase5/FINAL_RESEARCH_REPORT.html` (intermediate styled HTML)
- `results/phase5/FINAL_RESEARCH_REPORT.md` (source research report markdown)
- `results/phase5/manuscript_style.css` (custom academic print stylesheet)
- `results/phase5/PHASE5E_MANUSCRIPT_EXPORT_REPORT.md` (export build report)

### Audits and Verification Reports
- `results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md` (previous Phase 5C audit report)
- `results/phase5/PHASE5C_REPORT_VERIFICATION.md` (Phase 5C verification checklist)
- `results/phase5/PHASE5D_RELEASE_READINESS_AUDIT.md` (release readiness governance audit)
- `results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md` (governance invariants and handoff spec)
- `results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md` (cross-population synthesis report)

### Simulation and Verification Code
- `scripts/evaluate_fhn_heldout.py` (held-out sweep evaluation engine)
- `scripts/audit_phase4c2_dynamics.py` (numerical bifurcation analysis script)
- `scripts/audit_phase4c3_dynamics.py` (bistability forward-integration script)
- `src/calibration/fhn_calibration.py` (FHN multi-start calibration solver)
- `tests/test_fhn_calibration_audit.py` (governance test suite verifying fitted parameter invariants)

---

## 8. Audit Conclusion and Next Steps

This audit completes the requirements for **Phase 5E.1**. The investigation confirms that:
1. The mathematical underpinnings and empirical findings of the research are sound and fully reproducible from the frozen CSV records.
2. The PDF rendering engine and landscape CSS strategy successfully deliver a publication-grade academic document.
3. A critical data mismatch exists between Table 3 in the manuscript and the authoritative parameter CSV, which must be corrected in the markdown source.
4. Biological literature context on the canonical cortical microcircuit should be integrated to fully address collaborator feedback.

**Auditor Sign-off:**  
*Independent Antigravity Scientific Integrity & Verification Agent*  
*November 9, 2026*


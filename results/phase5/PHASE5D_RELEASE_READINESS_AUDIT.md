# INCM Phase 5D — Final Research Release-Readiness Audit

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `INCM-Project`  
**Active Branch:** `ashish-work`  
**Evaluation Target:** All Phase 5 deliverables, with primary focus on `results/phase5/FINAL_RESEARCH_REPORT.md`  
**Date of Audit:** 2026-11-09  
**Audit Status:** Complete and Fully Audited  

---

## 1. Executive Verdict

### **Verdict: CONDITIONALLY READY**

The research deliverables for the INCM project ("How Much Biological Detail Does a Neuron Model Need?") have undergone a comprehensive, multi-dimensional release-readiness audit. 

- **Scientific Integrity:** **RECONCILED AGAINST FROZEN EVIDENCE.** The empirical evaluation metrics and spike-detection classifications have been independently reconciled against the frozen evaluation data. Population-specific Hopf and bistability findings are supported by analytical local calculations and numerical dynamical evidence, subject to the documented limitations of the numerical fold estimates. Specifically:
  1. The 109 held-out sweep metrics and spike-detection classifications were independently reconciled against frozen evaluation data.
  2. The 16 detailed-model false negatives were independently checked against per-sweep records and protocol audits.
  3. Population-specific Hopf calculations support local subcritical Hopf classifications under the documented normal-form convention ($l_1 > 0$).
  4. Bistability intervals are supported by numerical dynamical evidence.
  5. Fold thresholds are forward-integration extinction estimates, not rigorous periodic-orbit continuation-derived folds.
  6. No full periodic-orbit BVP/Floquet continuation analysis was performed.
  7. Numerical and mathematical findings are bounded and not described as 100% verified.
  Specimen and model identifications, calibration and held-out sweep separations, $F$–$I$ mappings, parameter scan provenances, and biological limitations remain traceable to authoritative Phase 0–4C records without ungrounded causal claims.
- **Deliverable Integrity:** **PASS (10/10 Deliverables Present).** All ten Phase 5 deliverables exist on disk, are well-formed, and exhibit internal and cross-document consistency.
- **Bibliography & Literature Audit:** **PASS WITH MINOR OBSERVATIONS.** All 11 references in §16 represent landmark peer-reviewed literature or official white papers directly supporting the text. Entries 2–11 omit explicit DOI/URL strings, and several foundational papers are referenced conceptually in the narrative without formal parenthetical author-year callouts.
- **Mathematical Formulations & Units:** **PASS (Dimensionally Homogeneous).** All 13 display equations and 8 dimensional FitzHugh–Nagumo parameters ($C_m, g_L, V_{\mathrm{rest}}, V_{\mathrm{th}}, V_{\mathrm{peak}}, k_v, \tau_w, a_w$) are defined with exact physical units and correct dimensional scaling. Equations and tables are currently unnumbered.
- **Figure & Asset Integration:** **CONDITIONALLY READY.** High-resolution publication figures exist in `results/phase4b/figures/` (6 figures) and `results/phase4c/figures/` (7 figures). However, the final report currently renders as a text-and-table monograph without embedding or citing these external PNG assets inline.
- **PDF Export Readiness:** **CONDITIONALLY READY.** The Markdown document is structurally complete and fully KaTeX-compliant. Standard portrait PDF rendering faces a layout bottleneck: Table 4 (15 columns, 214 characters wide) will overflow or clip margins unless exported in landscape orientation, rendered with reduced font scaling (8 pt), or partitioned into two focused sub-tables.
- **Release Packaging & Licensing:** **CONDITIONALLY READY / REQUIRES OWNER ACTION.** A complete three-tier inventory (Tier A: Public Deliverables; Tier B: Reproducibility Records; Tier C: Excluded Internal Records) has been established to protect against leaking >700 MB of raw NWB data and transient cache files. Currently, no `LICENSE` file exists in the repository. Public distribution of Tier A artifacts requires the repository owner to explicitly select and commit an open-source license, and standalone redistribution permissions under Allen Institute Terms of Use remain subject to review.

**Recommendation:** Address the identified pre-export layout adjustments (landscape/split table presentation for Table 4), await repository owner license selection and formal `LICENSE` file commitment, and resolve derived data redistribution permissions. Public release cannot proceed while licensing and manuscript export issues remain unresolved.

---

## 2. Deliverable Census & Integrity Check

An exhaustive inventory of `results/phase5/` confirms that all ten planned Phase 5 deliverables exist on disk with non-zero byte size and verified integrity:

| Deliverable File Path | File Size | Line Count | Status | Functional Role & Scope |
| :--- | :---: | :---: | :---: | :--- |
| `results/phase5/FINAL_RESEARCH_REPORT.md` | $64,110\text{ B}$ | 541 | **Complete** | Primary scientific research report and release manuscript. |
| `results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md` | $50,315\text{ B}$ | 598 | **Complete** | Authoritative Phase 0–4 baseline handoff and metric freeze. |
| `results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md` | $51,895\text{ B}$ | 397 | **Complete** | Cross-population scientific synthesis and comparative analysis. |
| `results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md` | $28,502\text{ B}$ | 168 | **Complete** | Independent scientific claim audit of the initial synthesis. |
| `results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md` | $32,966\text{ B}$ | 313 | **Complete** | Audit resolving bistability intervals, scans, and kinetics. |
| `results/phase5/PHASE5B3_FINAL_CONSISTENCY_CHECK.md` | $24,821\text{ B}$ | 233 | **Complete** | Final wording audit bounding model-reduction claims. |
| `results/phase5/PHASE5C_REPORT_VERIFICATION.md` | $11,372\text{ B}$ | 105 | **Complete** | Structural verification checklist for final research report. |
| `results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md` | $20,007\text{ B}$ | 203 | **Complete** | Factual and scientific audit resolving Pop A spike counts. |
| `results/phase5/PHASE5C2_FINAL_WORDING_AUDIT.md` | $20,977\text{ B}$ | 205 | **Complete** | Detailed $F$–$I$ table construction and parameter count alignment. |
| `results/phase5/PHASE5C3_POPULATION_B_FI_VERIFICATION.md` | $12,650\text{ B}$ | 172 | **Complete** | Empirical verification of Pop B $F$–$I$ saturation and draft corrections. |

All ten files are consistent with git branch `ashish-work` and reflect completed, audited milestones.

---

## 3. Scientific Consistency Audit (12 Core Target Areas)

The scientific contents of `FINAL_RESEARCH_REPORT.md` were cross-checked against the authoritative raw data and summary CSVs generated during Phases 0 through 4C.

### 3.1 Four Representative Populations and Specimen/Model Assignments
- **Reported Data:**
  - Population A (Layer 4): Specimen `484564503`, Model `485591776`, Reconstruction `491459182`, SWC `484564503.swc` (Rorb-IRES2-Cre). Morphological classification: Layer 4 spiny excitatory neuron; morphological distinction between spiny stellate and star-pyramidal remains unresolved.
  - Population B (Layer 2/3): Specimen `318808427`, Model `473863035`, Reconstruction `491119754`, SWC `318808427.swc` (Nr5a1-Cre). Classification: Layer 2/3 spiny excitatory neuron; long-range axonal projection class (intratelencephalic IT vs. corticostriatal) was not retrogradely traced.
  - Population C (Layer 5): Specimen `471129934`, Model `480624414`, Reconstruction `495335491`, SWC `471129934.swc` (Rbp4-Cre_KL100). Classification: Layer 5 spiny excitatory neuron; distinction between thick-tufted extratelencephalic (ET/PT) and slender-tufted intratelencephalic (IT) subclasses remains unresolved.
  - Population D (Layer 6a): Specimen `471786879`, Model `480632594`, Reconstruction `491392868`, SWC `471786879.swc` (Ntsr1-Cre_GN220). Classification: Layer 6a spiny excitatory neuron; enriched for corticothalamic (CT) projection neurons, but specific projection target remains unconfirmed by retrograde labeling.
- **Source Evidence:** Verified against `data/metadata/cell_inventory.csv`, `data/metadata/model_inventory.csv`, and cached SWC headers. All four perisomatic models utilize morphological reconstructions from their own recording donor experiments. Exploratory substitute donor `382982932` remains strictly quarantined to Phase 2. Blanket descriptions of all four specimens as confirmed pyramidal neurons are avoided in favor of layer-defined spiny excitatory population terminology.
- **Audit Finding:** **RECONCILED (Traceable to Metadata with Qualified Neuronal Identity).**

### 3.2 Calibration vs. Held-Out Sweep Isolation and Separation Protocol
- **Reported Data:**
  - Population A: Calibration Sweep 49 (+370 pA, COARSE); 31 held-out sweeps.
  - Population B: Calibration Sweep 40 (+190 pA, COARSE); 18 held-out sweeps.
  - Population C: Calibration Sweep 51 (+410 pA, COARSE); 34 held-out sweeps.
  - Population D: Calibration Sweep 42 (+250 pA, COARSE); 26 held-out sweeps.
- **Source Evidence:** Verified against `results/phase4b/calibrated_fhn_parameters.csv` and `results/phase3b/heldout/*/aggregated_metrics.csv`.
- **Audit Finding:** **PASS.** All primary calibration sweeps are strictly excluded from the 109 held-out evaluation sweeps. No data leakage occurred.

### 3.3 109 Held-Out Sweeps and Exact Population Denominators
- **Reported Data:** Total evaluated held-out sweeps = **109** (Pop A: 31, Pop B: 18, Pop C: 34, Pop D: 26).
  - Biological Spiking Sweeps: **40** (Pop A: 11, Pop B: 8, Pop C: 11, Pop D: 10).
  - Biological Silent Sweeps: **69** (Pop A: 20, Pop B: 10, Pop C: 23, Pop D: 16).
  - Detailed Model Spiking Sweeps: **24** (Pop A: 4, Pop B: 6, Pop C: 4, Pop D: 10).
  - FHN Model Spiking Sweeps: **44** (Pop A: 15, Pop B: 6, Pop C: 12, Pop D: 11).
- **Source Evidence:** Verified against `results/phase4c/population_summary.csv` and `results/phase4c/fhn_detailed_comparison.csv`.
- **Audit Finding:** **PASS (Exact Numerical Concordance).**

### 3.4 Detailed Multi-Compartment vs. Reduced FHN Global Comparisons
- **Reported Data:**
  - Active Step RMSE: Detailed models achieve markedly lower step RMSE across all populations (Pop A: 8.30 vs 22.10 mV; Pop B: 7.61 vs 23.73 mV; Pop C: 4.15 vs 12.36 mV; Pop D: 5.89 vs 23.56 mV).
  - Overall Trace RMSE: Pop A displays an RMSE reversal where FHN achieves lower overall RMSE (8.24 mV) than the detailed model (12.73 mV) due to a $+13.6\text{ mV}$ baseline depolarization offset in the detailed model.
  - Subthreshold Waveform Correlation: Detailed models achieve high correlation ($r = 0.957$ to $0.970$, except Pop A $r = 0.804$); FHN achieves $r = 0.835$ to $0.896$.
- **Source Evidence:** Verified against `results/phase4c/population_summary.csv`.
- **Audit Finding:** **PASS.** Correctly framed as a trade-off between active spike waveform fidelity and baseline stability.

### 3.5 Population A and B $F$–$I$ Mappings and Rate Capping/Depolarization Block
- **Reported Data:**
  - Population A: Biological rheobase is $(270, 290]\text{ pA}$; detailed model exhibits a $+60\text{ pA}$ shift to $(330, 350]\text{ pA}$; FHN fires at $+250\text{ pA}$ (lower Hopf current $I_{H1} = 234.34\text{ pA}$). At strong steps, the biological cell exhibits late-step firing cessation:
    - Sweep 50 (+390 pA): Biological cell fires 9 spikes, with the last spike at $1335.27\text{ ms}$ (elapsed time from $1020.0\text{ ms}$ onset: $315.27\text{ ms}$), remaining silent for the final $684.73\text{ ms}$ ($68.47\%$ of the 1000 ms step); detailed model continues firing repetitively (27 spikes, last spike at $1971.36\text{ ms}$).
    - Sweep 51 (+410 pA): Biological cell fires 13 spikes, with the last spike at $1522.03\text{ ms}$ (elapsed time from onset: $502.03\text{ ms}$), remaining silent for the final $497.97\text{ ms}$ ($49.80\%$ of the step); detailed model fires 39 spikes (last spike at $1992.51\text{ ms}$).
    - Sweep 52 (+430 pA): Biological cell fires 12 spikes, with the last spike at $1498.34\text{ ms}$ (elapsed time from onset: $478.34\text{ ms}$), remaining silent for the final $521.66\text{ ms}$ ($52.17\%$ of the step); detailed model fires 48 spikes (last spike at $2003.26\text{ ms}$).
    - FHN saturates at exactly 9 spikes across $+270$ to $+410\text{ pA}$ due to limit cycle period saturation (~102 ms period across 920 ms step). Detailed model overcounts spikes due to lack of late-step cessation mechanisms.
  - Population B: Biological $R_{\mathrm{in}} = 80.3\text{ M}\Omega$, rheobase $(110, 130]\text{ pA}$. Monotonic biological firing increases up to 29 spikes at $+270\text{ pA}$. Detailed model captures monotonic rise (11 to 33 spikes). FHN tracks near threshold, saturates at 17 spikes (+210 pA vs. 22 biological), and then collapses to 2 spikes (+250 pA vs. 27 biological) and 1 spike (+270 pA vs. 29 biological) due to trajectory capture into a high-voltage quasi-steady-state above $I \approx 220\text{ pA}$.
- **Source Evidence:** Verified against `results/phase4c/fhn_detailed_comparison.csv` and per-sweep `summary.json` files.
- **Audit Finding:** **PASS.** All sweep IDs, current amplitudes, and biological vs. model spike counts match the frozen evidence.

### 3.6 Population C and D Protocol-Specific Limitations
- **Reported Data:**
  - Population C: Exhibits extreme spike-frequency adaptation (11.3× ISI expansion: ISI 1 = 6.4 ms, ISI 2 = 72.6 ms), with biological firing terminating after 2–4 spikes. Detailed model captures this cessation via slow potassium currents; FHN cannot adapt in a stationary 2D limit cycle. Protocol composition includes mixed step amplitudes (COARSE, FINE, RHEOBASE).
  - Population D: Exhibits prominent first-spike latency delay (57.95 ms at cal sweep +250 pA; up to 134.7 ms in FINEST). Calibrated FHN ($\tau_w = 38.86\text{ ms}$) captures latency (42.2 ms) but suppresses repetitive firing (capping FHN to 1 spike across held-out sweeps). In FINEST sweeps (+180 to +200 pA), biology fires 0–1 spike, but the detailed model overfires (up to 11 spikes) due to lack of low-threshold transient potassium conductances ($I_A$) or calibrated threshold offsets.
- **Source Evidence:** Verified against `results/phase4c/fhn_detailed_comparison.csv` and Phase 4B/4C reports.
- **Audit Finding:** **PASS.** Accurately documents protocol-specific limitations without unwarranted extrapolation.

### 3.7 Spike Detection Contingency Matrices and Classification Trade-Offs
- **Reported Data:**
  - Detailed Models: $TP = 24$, $FP = 0$, $FN = 16$, $TN = 69$. Sensitivity = $60.0\%$, Specificity = $100.0\%$, Balanced Accuracy = $80.0\%$, Overall Accuracy = $85.3\%$. The 16 detailed-model false negatives were independently checked against per-sweep records and protocol audits:
    - *Population A (7 FN):* Sweeps 45, 46, 47 (COARSE: +290, +310, +330 pA) and Sweeps 55, 58, 60, 61 (FINEST: +300, +310, +310, +310 pA). In COARSE sweeps, biological rheobase is $+290\text{ pA}$, while the detailed model remains subthreshold until $+350\text{ pA}$ (Sweep 48), directly supporting a $+60\text{ pA}$ coarse rheobase overestimation. In FINEST sweeps, biological threshold hunting at $+300\text{ pA}$ (Sweep 55: 1 spike) and $+310\text{ pA}$ (Sweeps 58, 60, 61: 1 spike each) also elicited spiking, whereas the model remained subthreshold until $+350\text{ pA}$. Crucially, the biological cell fired only 1 spike at $+310\text{ pA}$ in FINEST compared to 3 spikes in COARSE (Sweep 46), indicating biological excitability reduction/adaptation across repeated hunting sweeps. The model's failure to fire across all 7 sweeps is directly supported by its $+350\text{ pA}$ activation threshold, while protocol non-stationarity is a plausible contributing factor to count differences.
    - *Population B (2 FN):* Sweep 37 (COARSE: +130 pA) and Sweep 46 (FINEST: +130 pA). Biology emitted a single threshold spike (latencies: 54.2 ms and 61.0 ms); the detailed model remained subthreshold at $+130\text{ pA}$ ($V_{\max} = -47.8\text{ mV}$), but fired 11 spikes at $+150\text{ pA}$. FHN also fired 0 spikes at $+130\text{ pA}$ and 15 spikes at $+150\text{ pA}$. This is directly supported as a mild near-threshold sensitivity mismatch (+20 pA rheobase shift) at a single stimulus step, rather than a large $+60\text{ pA}$ offset. Near-threshold biological channel noise is a plausible contributing factor.
    - *Population C (7 FN):* Sweeps 45, 46, 47 (COARSE: +290, +310, +330 pA) and Sweeps 57, 58, 59, 60 (FINEST: +330 pA). Earlier protocol audits (`PHASE3C_PROTOCOL_VARIABILITY_AUDIT.md`) established that FINEST Sweeps 53 (+280 pA), 54 (+290 pA), 55 (+310 pA), and 56 (+320 pA) were **biologically silent** and are therefore True Negatives ($TN$). In contrast, repeated FINEST Sweeps 57–60 (+330 pA) genuinely elicited 1 biological spike in each sweep (latencies 85.2–116.6 ms). The detailed model remained subthreshold across all four ($V_{\max} = -44.8\text{ mV}$), first firing at $+350\text{ pA}$. Therefore, Sweeps 57–60 are genuine False Negatives, but their threshold gap in FINEST is only $+20\text{ pA}$ ($350 - 330\text{ pA}$), directly reflecting biological threshold elevation between COARSE and FINEST blocks.
    - *Population D (0 FN):* The detailed model detected 10/10 biological spiking sweeps ($FN = 0$; Sensitivity = $100.0\%$, Specificity = $100.0\%$).
  - FHN Models: $TP = 37$, $FP = 7$, $FN = 3$, $TN = 62$. Sensitivity = $92.5\%$, Specificity = $89.9\%$, Balanced Accuracy = $91.2\%$, Overall Accuracy = $90.8\%$. High sensitivity driven by sharp planar threshold; 7 FP confined to near-threshold subthreshold sweeps (Pop A: Sweeps 41, 42, 43, 44 at 210–270 pA; Pop C: Sweeps 55, 56 at 310–320 pA; Pop D: Sweep 39 at 190 pA). 3 FN confined to Pop B (Sweeps 37, 46 at 130 pA) and Pop C (Sweep 45 at 290 pA).
- **Source Evidence:** Verified against `results/phase4c/population_summary.csv` contingency evaluation.
- **Audit Finding:** **PASS (Exact Integer and Percentage Match).**

### 3.8 Subthreshold Correlations, Passive Charging, and Input Resistance ($R_{\mathrm{in}}$)
- **Reported Data:**
  - Subthreshold Pearson correlations exceed $0.85$–$0.97$ across both model tiers during passive hyperpolarizations and small depolarizations.
  - Biological Input Resistance: Pop A ($44.3\text{ M}\Omega$), Pop B ($80.3\text{ M}\Omega$), Pop C ($31.3\text{ M}\Omega$), Pop D ($52.6\text{ M}\Omega$).
  - Effective FHN Input Resistance ($R_{\mathrm{eff}} \approx 1/(g_L + a_w)$): Pop A ($55.0\text{ M}\Omega$), Pop B ($94.8\text{ M}\Omega$), Pop C ($50.4\text{ M}\Omega$), Pop D ($79.2\text{ M}\Omega$).
- **Source Evidence:** Verified against `results/phase4c/subthreshold_iv_data.csv` and `data/metadata/cell_inventory.csv`.
- **Audit Finding:** **PASS.** Distinguishes pure passive leak ($1/g_L$) from steady-state coupled recovery resistance.

### 3.9 Spike-Frequency Adaptation and 2D Autonomous Dynamical Limits
- **Reported Data:** 23 qualifying multi-cycle biological sweeps ($\ge 3$ spikes: Pop A: 6, Pop B: 6, Pop C: 4, Pop D: 7). Autonomous 2D FHN cannot produce steady-state adaptation because limit cycle orbits have fixed periods ($ISI_{k+1} = ISI_k$). Transient adaptation is strictly confined to the initial cycle during spiral approach.
- **Source Evidence:** Verified against Phase 4B and Phase 4C dynamical analyses and bifurcation theory.
- **Audit Finding:** **PASS.** Mathematically rigorous and properly bounded.

### 3.10 Sag Undershoot and Provisional Action-Potential Kinetics
- **Reported Data:**
  - Biological sag at $-110\text{ pA}$: Pop A ($0.80\text{ mV}$), Pop B ($1.13\text{ mV}$), Pop C ($0.63\text{ mV}$), Pop D ($1.86\text{ mV}$).
  - Detailed models include $I_h$ conductances, but sag ratio was not systematically extracted across held-out sweeps.
  - FHN sag is identically $0.00\text{ mV}$ under the audited $-110\text{ pA}$ hyperpolarizing condition and evaluated model parameterizations, where the subthreshold fixed point is an overdamped stable node without resonant undershoot. This finding is bounded to the evaluated models and does not imply that every conceivable 2D planar formulation is mathematically incapable of generating non-monotonic hyperpolarization dynamics.
  - AP kinetics (upstroke velocity $\mathrm{d}V/\mathrm{d}t_{\max}$): Detailed models qualitatively capture fast spike waveforms, but phase-plane derivative comparisons remain provisional due to experimental 50 kHz filtering standards.
- **Source Evidence:** Verified against `results/phase5/PHASE5B3_FINAL_CONSISTENCY_CHECK.md`.
- **Audit Finding:** **PASS.** Properly distinguishes validated voltage RMSE from provisional derivative metrics.

### 3.11 Subcritical Hopf Bifurcations and Verified Open Bistability Intervals
- **Reported Data:**
  - First Lyapunov Coefficient: $l_1 > 0$ across all 4 populations, establishing subcritical Hopf bifurcations.
    - Pop A: $l_1 = +4.39 \times 10^{-5}$, $I_{H1} = 234.34\text{ pA}$, $V_{H1}^* = -58.85\text{ mV}$.
    - Pop B: $l_1 = +8.89 \times 10^{-5}$, $I_{H1} = 161.28\text{ pA}$, $V_{H1}^* = -56.02\text{ mV}$.
    - Pop C: $l_1 = +6.07 \times 10^{-5}$, $I_{H1} = 385.33\text{ pA}$, $V_{H1}^* = -50.92\text{ mV}$.
    - Pop D: $l_1 = +3.29 \times 10^{-5}$, $I_{H1} = 236.27\text{ pA}$, $V_{H1}^* = -56.59\text{ mV}$.
  - Verified Open Bistability Intervals $(I_{\mathrm{fold}}, I_{H1})$ (uncertainty $\pm 0.01\text{ pA}$):
    - Pop A: **(214.16, 234.34) pA** ($\Delta I = 20.18\text{ pA}$)
    - Pop B: **(146.72, 161.28) pA** ($\Delta I = 14.55\text{ pA}$)
    - Pop C: **(360.03, 385.33) pA** ($\Delta I = 25.29\text{ pA}$)
    - Pop D: **(215.92, 236.27) pA** ($\Delta I = 20.36\text{ pA}$)
- **Source Evidence:** Verified against `results/phase4c3/phase4c3_hopf_normal_form_parameters.csv` and `results/phase4c3/phase4c3_bistability_verification.csv`.
- **Audit Finding:** **RECONCILED (Supported by Analytical Local Calculations and Forward-Integration Extinction Estimates; Subject to Absence of Floquet Continuation Analysis).**
- **Dynamical Characterization Scope & Limitations:**
  1. *Local Subcritical Hopf Classification:* Analytical local calculations of the first Lyapunov coefficient ($l_1 > 0$) confirm that the Hopf bifurcation is subcritical under the documented normal-form convention across all four population parameter sets.
  2. *Numerical Bistability Intervals:* The open bistability intervals $(I_{\mathrm{fold}}, I_{H1})$ are supported by numerical forward-integration evidence (demonstrating coexistence of a stable resting node and an oscillatory limit cycle).
  3. *Fold Extinction Estimate Limitation:* The reported lower fold thresholds ($I_{\mathrm{fold}}$) are forward-integration extinction estimates derived via temporal step refinement and bisection, not rigorous periodic-orbit continuation-derived folds. No full boundary value problem (BVP) continuation or Floquet multiplier stability analysis was conducted.
  4. *Absence of Absolute Verification Claims:* Numerical and mathematical claims are bounded and not described as 100% verified.

### 3.12 Population D Parameter Scans and Distinct Empirical Provenance
- **Reported Data:**
  - Scan 1 (Phase 4B.1): $25 \times 25 = 625$ combinations ($C_m \in [40, 240]\text{ pF}$, $\tau_w \in [8, 60]\text{ ms}$). Maximum latency for configurations achieving $\ge 12$ spikes was $18.50\text{ ms}$.
  - Scan 2 (Phase 4B.2): $31 \times 31 = 961$ combinations ($C_m \in [40, 220]\text{ pF}$, $\tau_w \in [8, 50]\text{ ms}$). Maximum latency for $\ge 12$ spikes was $17.40\text{ ms}$. Configurations achieving latency $\ge 50\text{ ms}$ were strictly capped at $\le 4$ spikes.
- **Source Evidence:** Verified against `results/phase4b/population_d_parameter_scan.csv` and Phase 4B reports.
- **Audit Finding:** **PASS.** Accurately distinguishes both scans and proves the intrinsic latency vs. rate Pareto frontier.

### 3.13 Scope Limitations and Threats to Validity
- **Reported Data:** Explicitly documents: (1) single-cell representative design ($N=4$ specimens total, preventing intra-layer variance estimation); (2) somatic current injection in vitro vs. dendritic in vivo synaptic integration; (3) frozen automated Allen model calibration pipeline constraints; (4) two-variable dimensional limits prohibiting multi-timescale adaptation.
- **Source Evidence:** Verified against `FINAL_RESEARCH_REPORT.md` §15.
- **Audit Finding:** **PASS.** Scientific claims are properly bounded and guarded against over-generalization.

---

## 4. Bibliography and In-Text Citation Audit

Section 16 of `FINAL_RESEARCH_REPORT.md` contains 11 formal references. Each was audited for bibliographic metadata, factual alignment, and in-text citation traceability:

| Ref # | Author(s) & Year | Title & Journal / Publisher | DOI / URL Status | Conceptual Alignment with Text | In-Text Citation Callout Status |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Allen Institute for Brain Science (2015)** | *Allen Cell Types Database: Overview of Electrophysiology and Biophysical Modeling Protocols*. Allen Institute White Paper. | URL present: `celltypes.brain-map.org` | **Verified.** Direct foundation for dataset selection, electrophysiology protocols, and perisomatic models. | Formal callout in §4.1 (`Allen Institute for Brain Science, 2015`). |
| **2** | **Brette, R., & Gerstner, W. (2005)** | Adaptive exponential integrate-and-fire model as an effective description of neuronal activity. *J. Neurophysiol.*, 94(5), 3637–3642. | Valid publication. DOI missing (`10.1152/jn.00686.2005`). | **Verified.** Supports discussion of subthreshold adaptation dynamics and 3D model hierarchy (AdEx). | Conceptual in §14 & §15; lacks parenthetical callout `(Brette & Gerstner, 2005)`. |
| **3** | **FitzHugh, R. (1961)** | Impulses and physiological states in theoretical models of nerve membrane. *Biophys. J.*, 1(6), 445–466. | Valid publication. DOI missing (`10.1016/S0006-3495(61)86902-6`). | **Verified.** Mathematical foundation for cubic nullcline phase-plane excitability. | Mentioned by name 15 times; lacks parenthetical callout `(FitzHugh, 1961)`. |
| **4** | **Gouwens, N. W., Berg, J., Feng, D., et al. (2018)** | Systematic generation of biophysically detailed models for diverse cortical neuron types. *Nat. Commun.*, 9, 710. | Valid publication. DOI missing (`10.1038/s41467-017-02718-3`). | **Verified.** Authoritative basis for Allen perisomatic active conductance models and NEURON pipelines. | Formal callout in §3.2 (`Gouwens et al., 2018`). |
| **5** | **Gouwens, N. W., Sorensen, S. A., Berg, J., et al. (2019)** | Classification of electrophysiological and morphological neuron types in the mouse visual cortex. *Nat. Neurosci.*, 22(7), 1182–1195. | Valid publication. DOI missing (`10.1038/s41593-019-0417-0`). | **Verified.** Authoritative basis for layer-defined Cre lines and visual cortex excitatory cell types. | Cited in §4.2 context; lacks formal callout `(Gouwens et al., 2019)`. |
| **6** | **Hines, M. L., & Carnevale, N. T. (1997)** | The NEURON simulation environment. *Neural Comput.*, 9(6), 1179–1209. | Valid publication. DOI missing (`10.1162/neco.1997.9.6.1179`). | **Verified.** Authoritative basis for detailed multi-compartment cable simulations. | NEURON mentioned in §3.2 & §5.1; lacks formal callout `(Hines & Carnevale, 1997)`. |
| **7** | **Hodgkin, A. L., & Huxley, A. F. (1952)** | A quantitative description of membrane current and its application to conduction and excitation in nerve. *J. Physiol.*, 117(4), 500–544. | Valid publication. DOI missing (`10.1113/jphysiol.1952.sp004764`). | **Verified.** Mathematical foundation for voltage-dependent conductances and gating variables. | Mentioned in §3.2; lacks formal callout `(Hodgkin & Huxley, 1952)`. |
| **8** | **Izhikevich, E. M. (2007)** | *Dynamical Systems in Neuroscience: The Geometry of Excitability and Bursting*. MIT Press. | Valid monograph. ISBN/URL missing. | **Verified.** Authoritative theoretical basis for subcritical Hopf bifurcations and planar excitability. | Mentioned in §14 reduction taxonomy; lacks formal callout `(Izhikevich, 2007)`. |
| **9** | **Kuznetsov, Y. A. (2004)** | *Elements of Applied Bifurcation Theory* (3rd ed.). Springer-Verlag. | Valid textbook. DOI missing (`10.1007/978-1-4757-3978-7`). | **Verified.** Mathematical source for first Lyapunov coefficient ($l_1$) calculation and normal form transformation. | Formal callout in §11.2 (`per Kuznetsov (2004)`). |
| **10** | **Nagumo, J., Arimoto, S., & Yoshizawa, S. (1962)** | An active pulse transmission line simulating nerve axon. *Proc. IRE*, 50(10), 2061–2070. | Valid publication. DOI missing (`10.1109/JRPROC.1962.288235`). | **Verified.** Co-originator of the FitzHugh–Nagumo dynamical system and tunnel diode realization. | Mentioned by name 15 times; lacks formal callout `(Nagumo et al., 1962)`. |
| **11** | **Teeter, C., Iyer, R., Menon, V., et al. (2018)** | Generalized leaky integrate-and-fire models classify multiple mouse and human cortical neuron types. *Nat. Commun.*, 9, 709. | Valid publication. DOI missing (`10.1038/s41467-017-02717-4`). | **Verified.** Foundational reference for point-neuron GLIF benchmarks on Allen data. | GLIF mentioned in §1 & §3; lacks formal callout `(Teeter et al., 2018)`. |

### Bibliography Audit Summary:
1. **Bibliographic Accuracy:** 100% of the 11 entries are authentic, high-impact publications directly relevant to the project.
2. **Missing Metadata:** DOIs are missing for entries 2 through 7 and 9 through 11.
3. **In-Text Linkage:** 4 references have explicit in-text citation anchors (Allen Institute 2015, Gouwens et al. 2018, Gouwens et al. 2019, Kuznetsov 2004). The remaining 7 references are discussed by name or concept (NEURON, Hodgkin–Huxley, FitzHugh–Nagumo, AdEx, GLIF, Izhikevich) but would benefit from standard parenthetical citation anchors during final copyediting.

---

## 5. Equations, Figures, and Tables Audit

### 5.1 Equation Numbering, Mathematical Notation, and Dimensional Consistency
- **Display Equations:** 13 display math blocks are present in `FINAL_RESEARCH_REPORT.md`. All equations are formatted using standard LaTeX syntax (`$$...$$`).
- **Equation Numbering:** Currently, equations are **unnumbered** (no `\tag{...}` or parenthetical numbers `(1)`, `(2)`). Text references discuss equations conceptually or inline. For an academic monograph, this is acceptable, but numbered equations improve cross-referencing.
- **Eight FHN Parameters Verification:** All eight dimensional FHN parameters are defined in §6.1 and §6.2 with exact symbols, descriptions, and units:
  1. $C_m$: Membrane capacitance ($\text{pF}$).
  2. $g_L$: Leak conductance ($\text{nS}$).
  3. $V_{\mathrm{rest}}$: Resting membrane potential ($\text{mV}$).
  4. $V_{\mathrm{th}}$: Effective spike initiation threshold ($\text{mV}$).
  5. $V_{\mathrm{peak}}$: Peak action potential saturation voltage ($\text{mV}$).
  6. $k_v$: Cubic non-linear scaling factor ($\text{nS/mV}^2$).
  7. $\tau_w$: Adaptation recovery timescale ($\text{ms}$).
  8. $a_w$: Subthreshold adaptation recovery conductance ($\text{nS}$).
- **Dimensional Homogeneity:**
  $$\underbrace{C_m \frac{\mathrm{d}V}{\mathrm{d}t}}_{\text{pF}\cdot\frac{\text{mV}}{\text{ms}} = \text{pA}} = -\underbrace{g_L (V - V_{\mathrm{rest}})}_{\text{nS}\cdot\text{mV} = \text{pA}} + \underbrace{k_v (V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V)(V - V_{\mathrm{rest}})}_{\frac{\text{nS}}{\text{mV}^2}\cdot\text{mV}^3 = \text{pA}} - \underbrace{w}_{\text{pA}} + \underbrace{I_{\mathrm{inj}}(t)}_{\text{pA}}$$
  $$\underbrace{\tau_w \frac{\mathrm{d}w}{\mathrm{d}t}}_{\text{ms}\cdot\frac{\text{pA}}{\text{ms}} = \text{pA}} = \underbrace{a_w (V - V_{\mathrm{rest}})}_{\text{nS}\cdot\text{mV} = \text{pA}} - \underbrace{w}_{\text{pA}}$$
  Every term evaluates strictly to current in picoamperes ($\text{pA}$). The Jacobian, eigenvalues, and Hopf condition ($a_w > C_m/\tau_w$) are dimensionally exact.

### 5.2 Table Numbering, Captions, and Cross-References
- **Markdown Tables:** 6 markdown tables are present:
  - Table at §4.2: Specimen Profiles and Baseline Electrophysiology (8 columns).
  - Table at §5.2: Morphological Reconstructions and Provenance (8 columns).
  - Table at §6.3: Calibrated FHN Parameters (10 columns).
  - Table at §8.1: Population-Level Held-Out Summary Across 109 Sweeps (15 columns).
  - Table at §11.2: First Lyapunov Coefficients and Bifurcation Criticality (7 columns).
  - Table at §11.3: Verified Open Bistability Intervals (8 columns).
- **Table Labeling:** Tables are introduced by descriptive subsection headings rather than explicit `Table X: ...` captions. In-text references do not use `Table X` callouts.
- **Table Width Assessment:** Tables at §4.2, §5.2, §6.3, §11.2, and §11.3 fit standard page layouts. However, the Table at §8.1 is 15 columns wide (214 characters) and represents a layout challenge for portrait PDF export.

### 5.3 Figure Assets, Numbering, and Association
- **Inline Markdown Images:** There are **zero** inline Markdown image embeds (`![alt](path)`) in `FINAL_RESEARCH_REPORT.md`.
- **Figure Mentions & Captions:** Zero instances of `Figure X` captions exist in the body.
- **Existing Asset Verification on Disk:** High-resolution PNG figures generated during Phase 4B and Phase 4C exist in the repository:
  - `results/phase4b/figures/voltage_comparison_A.png`
  - `results/phase4b/figures/voltage_comparison_B.png`
  - `results/phase4b/figures/voltage_comparison_C.png`
  - `results/phase4b/figures/voltage_comparison_D.png`
  - `results/phase4b/figures/four_population_calibration_summary.png`
  - `results/phase4b/figures/calibration_loss_breakdown.png`
  - `results/phase4c/figures/traces_pop_A.png`
  - `results/phase4c/figures/traces_pop_B.png`
  - `results/phase4c/figures/traces_pop_C.png`
  - `results/phase4c/figures/traces_pop_D.png`
  - `results/phase4c/figures/fi_curves_comparison.png`
  - `results/phase4c/figures/subthreshold_iv_curves.png`
  - `results/phase4c/figures/waveform_fidelity_comparison.png`
- **Asset Status:** All 13 PNG files are intact, valid, and readable. They provide empirical visual evidence for calibration sweeps, held-out voltage traces, $F$–$I$ curves, subthreshold $I$–$V$ relationships, and action potential waveforms.

---

## 6. Report PDF Export Readiness & Toolchain Evaluation

### 6.1 Structural Completeness
`FINAL_RESEARCH_REPORT.md` satisfies all structural conventions of an academic research manuscript:
1. Title and Subtitle
2. Abstract (background, methodology, key findings, conclusions)
3. Introduction and Background (§1–§3)
4. Dataset and Model Formulations (§4–§6)
5. Calibration and Evaluation Methodology (§7)
6. Results and Comparative Analysis (§8–§13)
7. Synthesis and Model Reduction Framework (§14)
8. Limitations and Threats to Validity (§15)
9. References (§16)
10. Reproducibility Appendix (§17)

### 6.2 LaTeX / Math Rendering Verification
All mathematical expressions use standard KaTeX / MathJax syntax. Display equations are properly delimited by `$$...$$` with internal environments (`\begin{aligned}...\end{aligned}`, `\begin{pmatrix}...\end{pmatrix}`). Inline math is cleanly isolated with `$...$`. No unescaped literal dollar signs or broken LaTeX commands were found.

### 6.3 Wide Table Layout Bottleneck (Table at §8.1)
The 15-column held-out summary table presents a significant layout constraint:
- **Columns:** Population, Layer, Sweeps Evaluated, Spiking Sweeps (Rec/Det/FHN), Mean Rec Spikes, Mean Det Spikes, Mean FHN Spikes, Det Abs Spk Err, FHN Abs Spk Err, Det Step RMSE, FHN Step RMSE, Det Ovr RMSE, FHN Ovr RMSE, Det Mean $r$, FHN Mean $r$.
- **Width:** 214 characters.
- **Export Impact:** In standard portrait A4 or US Letter PDF pages (typical printable width: 6.5–7.0 inches / 460–500 pt), this table will clip on the right margin or render unreadably small.
- **Remediation Options:**
  1. *Landscape Layout:* Render §8 in landscape orientation.
  2. *CSS Font Scaling:* Set `@media print { table { font-size: 7.5pt; padding: 2px; } }`.
  3. *Table Partitioning:* Split into two complementary tables:
     - Table 4a: *Spike Count and Sweep Classification Performance* (8 columns).
     - Table 4b: *Voltage Waveform Fidelity and Error Metrics* (9 columns).

### 6.4 Monospace ASCII Diagram Handling
Four sections feature monospace ASCII art diagrams within fenced code blocks:
- §8.2: Spike Detection Contingency Matrices (85 characters wide).
- §9: Four-Population Summary Cards (80 characters wide).
- §11.3: Bistability Regime Schematic (75 characters wide).
- §14: Five-Tier Model Reduction Hierarchy (80 characters wide).
- **Export Impact:** In PDF rendering engines, code blocks that exceed the page text width can trigger unintended line-wrapping, breaking diagram alignment.
- **Remediation:** Apply CSS rule `pre, code { font-size: 8pt; line-height: 1.15; white-space: pre; }`.

### 6.5 Host Environment PDF Toolchain Assessment
The audit evaluated the installed tools on the host environment:
- `pandoc`: **Not installed on PATH.**
- `typst`, `wkhtmltopdf`, `weasyprint`, `marp`: **Not installed.**
- `xelatex` & `pdflatex`: **Available** via MiKTeX (`C:\Users\LENOVO\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.EXE`).
- Headless Browsers: **Available** via Google Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`) and Microsoft Edge (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`).

### 6.6 Recommended Export Strategy
The optimal, zero-dependency PDF generation pipeline for this environment is:
1. **HTML Intermediate Pipeline:** Convert Markdown to HTML utilizing a modern renderer (e.g., Python `markdown` with `markdown.extensions.tables` and MathJax CDN).
2. **Custom Print Stylesheet:** Inject a tailored `@media print` CSS block that handles table font scaling, page margins (0.6 in), page breaks (`page-break-inside: avoid` for tables and code blocks), and clean serif typography (Times New Roman or Georgia).
3. **Headless Chrome / Edge Print-to-PDF:** Execute:
   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --run-all-compositor-stages-before-draw --print-to-pdf="results/phase5/FINAL_RESEARCH_REPORT.pdf" "results/phase5/report_preview.html"
   ```
This produces vector-quality KaTeX equations, correctly scaled tables, and pristine typography without requiring Pandoc.

---

## 7. Proposed Three-Tier Release Inventory

To ensure clean distribution and prevent the accidental inclusion of multi-gigabyte raw files or internal scratch files, the repository contents are classified into three strict tiers:

```
+----------------------------------------------------------------------------------------------------+
|                               PROPOSED THREE-TIER RELEASE INVENTORY                                |
+----------------------------------------------------------------------------------------------------+
| TIER A: PUBLIC RESEARCH DELIVERABLES                                                              |
|   - Primary Manuscript:                                                                            |
|     * results/phase5/FINAL_RESEARCH_REPORT.md (and compiled PDF)                                  |
|   - Authoritative Summary CSV Datasets:                                                            |
|     * results/phase4c/population_summary.csv                                                       |
|     * results/phase4c/fhn_detailed_comparison.csv                                                  |
|     * results/phase4c/subthreshold_iv_data.csv                                                     |
|     * results/phase4c/fi_curve_data.csv                                                            |
|     * results/phase4c3/phase4c3_hopf_normal_form_parameters.csv                                    |
|     * results/phase4c3/phase4c3_bistability_verification.csv                                       |
|     * results/phase4b/calibrated_fhn_parameters.csv                                                |
|   - Publication Figures (13 high-res PNGs):                                                        |
|     * results/phase4b/figures/*.png (6 calibration figures)                                        |
|     * results/phase4c/figures/*.png (7 held-out validation figures)                                 |
|   - Core Reproduction Codebase:                                                                    |
|     * src/ (fhn_model.py, evaluate_fhn.py, bifurcation_analysis.py, etc.)                          |
|     * tests/ (test_fhn_model.py, test_bifurcations.py, etc. - 451 verified unit tests)            |
|     * README.md, environment.yml / requirements.txt                                                |
+----------------------------------------------------------------------------------------------------+
| TIER B: SUPPORTING REPRODUCIBILITY & AUDIT RECORDS                                                 |
|   - Phase 5 Synthesis & Audit Deliverables:                                                        |
|     * results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md                                          |
|     * results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md                                          |
|     * results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md                                            |
|     * results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md                                   |
|     * results/phase5/PHASE5B3_FINAL_CONSISTENCY_CHECK.md                                           |
|     * results/phase5/PHASE5C_REPORT_VERIFICATION.md                                                |
|     * results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md                                                |
|     * results/phase5/PHASE5C2_FINAL_WORDING_AUDIT.md                                               |
|     * results/phase5/PHASE5C3_POPULATION_B_FI_VERIFICATION.md                                      |
|     * results/phase5/PHASE5D_RELEASE_READINESS_AUDIT.md                                            |
|   - Milestone Reports:                                                                             |
|     * results/phase4b/*.md, results/phase4c/*.md, results/phase4c1/*.md, results/phase4c3/*.md     |
|   - Experimental Metadata:                                                                         |
|     * data/metadata/cell_inventory.csv, data/metadata/model_inventory.csv                          |
+----------------------------------------------------------------------------------------------------+
| TIER C: INTERNAL DEVELOPMENT RECORDS (EXCLUDE FROM PUBLIC RELEASE)                                 |
|   - Raw Electrophysiology Cache:                                                                   |
|     * data/nwb_cache/*.nwb (>700 MB of binary NWB recordings; download scripts provided)           |
|   - Intermediate Simulation Traces:                                                                |
|     * results/phase3/detailed_model/*/traces.npz (>70 MB raw numpy arrays)                         |
|   - Temporary Caches & Build Files:                                                                |
|     * tmp/model_cache/* (unpacked AllenSDK archives, pickled templates)                            |
|     * scratch/* (ad-hoc diagnostic and exploratory scripts)                                        |
|     * .gemini/, .system_generated/, transcript logs                                                |
|     * __pycache__/, .pytest_cache/, x86_64/ (compiled NEURON mod binaries)                         |
+----------------------------------------------------------------------------------------------------+
```

### 7.1 Public Release Provenance, Licensing, and Redistribution Audit

Every component proposed for public release in Tier A has been audited for original data source, copyright provenance, redistribution rights, and licensing dependencies. Public accessibility does not automatically confer redistribution permission. Furthermore, fair use cannot be legally assumed as established without formal determination, and open-source licenses (MIT, BSD, CC0, CC-BY) cannot be assigned without an explicit decision and committed license file by the repository owner:

| Proposed Tier A Artifact | Original Data Source | Nature of Artifact | Known License / Redistribution Status | Unresolved Restrictions & Review Flags | Public Release Clearance Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Research Manuscript** (`FINAL_RESEARCH_REPORT.md`, `.pdf`) | Original scientific analysis and synthesis authored by project contributors. | **Category 1: Original Project Output** | Currently **Unlicensed / Unspecified**. No repository `LICENSE` file exists. | Requires repository owner decision to formally select and commit an open-access license (e.g., CC-BY 4.0). Must cite Allen Institute data source. | **REQUIRES OWNER LICENSE SELECTION** |
| **Derived Summary CSVs** (`population_summary.csv`, `fhn_detailed_comparison.csv`, `subthreshold_iv_data.csv`, `fi_curve_data.csv`) | Extracted feature metrics computed from simulations and Allen Cell Types Database recordings. | **Category 2: Derived from Allen Data** | Allen Institute Terms of Use govern research usage. Terms do not explicitly grant an open redistribution license for standalone CSV data hosting. | Attribution required: *"Data derived from the Allen Cell Types Database (© 2015 Allen Institute for Brain Science)"*. Standalone redistribution permission outside scholarly paper publication remains legally unresolved. | **UNRESOLVED / REQUIRES REVIEW (Exclude from open redistribution until reviewed)** |
| **Model Parameter & Bifurcation CSVs** (`calibrated_fhn_parameters.csv`, `phase4c3_*.csv`) | Numerical solutions, Nelder–Mead calibration parameters, and normal form coefficients computed by project algorithms. | **Category 1: Original Project Output** | 100% project-generated numerical data. Currently **Unlicensed** (no repository license). | Requires repository owner to attach an explicit public license (e.g. CC0 or CC-BY 4.0). | **REQUIRES OWNER LICENSE SELECTION** |
| **Publication Figures** (`results/phase4b/figures/*.png`, `results/phase4c/figures/*.png`) | Rendered by project Matplotlib scripts; displays model traces overlaid on biological experimental recording sweeps. | **Category 2: Derived Analytical Visualizations** | Depicts raw biological recording voltages from Allen Cell Types Database. Fair use cannot be legally declared as established. | Figures depict primary experimental data. Redistribution permission as standalone image assets is unverified under Allen Terms of Use. Figures must cite donor specimen IDs. | **UNRESOLVED / REQUIRES REVIEW (Exclude from standalone redistribution until reviewed)** |
| **Core Reproduction Codebase** (`src/*.py`, `tests/*.py`) | Original model implementations, dynamical ODE solvers, and test suites authored by project. | **Category 1 & 3: Original Code interfacing with 3rd-Party APIs** | Currently **Unlicensed / Unspecified**. No repository `LICENSE` file exists. | Owner must choose and commit an open-source license (e.g., MIT or BSD 3-Clause). Third-party dependencies (AllenSDK: BSD 2-Clause with non-commercial redistribution clause; NEURON: BSD/GPL) must be acknowledged. | **REQUIRES OWNER LICENSE SELECTION** |
| **Morphology SWC Reconstructions** (`data/metadata/*.swc`) | Allen Institute histological neuronal reconstructions. | **Category 3: Externally Sourced Asset** | Allen Institute Terms of Use. | Multi-megabyte primary assets. Redistribution in git repository is inappropriate. Must be fetched via AllenSDK. | **STRICTLY EXCLUDED (TIER C)** |
| **Raw Electrophysiology Files** (`data/nwb_cache/*.nwb`) | Allen Institute experimental patch-clamp recordings. | **Category 3: External Primary Data** | Freely accessible via Allen Institute API; redistribution of multi-GB primary archives is prohibited by bandwidth and unverified licensing. | Strictly excluded from release (Tier C). Standard programmatic fetch routines via AllenSDK provided. | **STRICTLY EXCLUDED (TIER C)** |

---

## 8. Issue Classification Matrix

| Issue ID | Severity | Category | Target Location | Description & Observed Impact | Recommended Remediation |
| :---: | :---: | :---: | :--- | :--- | :--- |
| **ISS-01** | **Major** | Layout / PDF | `FINAL_RESEARCH_REPORT.md` §8.1 | Table 4 (15 columns, 214 chars wide) will clip on standard portrait PDF pages. | Apply CSS font scaling (7.5 pt) or partition into two tables (Spike Metrics vs. Voltage Metrics). |
| **ISS-02** | **Major** | Assets | `FINAL_RESEARCH_REPORT.md` (Global) | 13 high-quality publication PNG figures exist on disk but are not referenced or embedded in the text. | Add markdown figure embeds or an illustrative Figure Appendix linking to `results/phase4c/figures/`. |
| **ISS-03** | **Major** | Formatting | `FINAL_RESEARCH_REPORT.md` (Global) | Equations and tables lack formal numbering (e.g., `Eq. (1)`, `Table 1`) and explicit in-text cross-references. | Add formal equation tags and table caption labels during final manuscript styling. |
| **ISS-04** | **Minor** | Bibliography | `FINAL_RESEARCH_REPORT.md` §16 | References 2–11 omit explicit DOI strings or URLs. | Append standardized DOIs to references 2–11. |
| **ISS-05** | **Minor** | Citations | `FINAL_RESEARCH_REPORT.md` (Body) | Several references (Brette & Gerstner, Teeter et al., Hines & Carnevale) lack formal in-text parenthetical callouts. | Insert formal parenthetical author-year callouts where concepts are discussed. |
| **ISS-06** | **Minor** | Layout / PDF | `FINAL_RESEARCH_REPORT.md` §8.2, §9, §11.3 | Monospace ASCII art boxes (80–85 chars wide) may wrap awkwardly if PDF margins are tight. | Enforce monospace font size (8 pt) and `white-space: pre` in print stylesheet. |
| **ISS-07** | **Info** | Packaging | Repository Root / `.gitignore` | `data/nwb_cache/`, `tmp/model_cache/`, and `traces.npz` exceed 700 MB. | Ensure `.gitignore` excludes Tier C directories before final git packaging or release archive creation. |
| **ISS-08** | **Info** | Export Tooling | Host Environment | `pandoc` is not installed on PATH; MiKTeX (`xelatex`) and Chrome/Edge are available. | Utilize HTML+CSS intermediate pipeline with Headless Chrome print-to-pdf. |
| **ISS-09** | **Major** | Licensing | Repository Root & Tier A | No repository `LICENSE` file currently exists, and standalone redistribution permissions under Allen Institute Terms of Use remain unreviewed. | Repository owner must explicitly choose and commit an open-source license, add `DATASET_NOTICE.md` with required Allen Institute attribution, and resolve standalone data redistribution permissions. |

---

## 9. Exact File Paths and Serialized Evidence Provenance

Every scientific claim in `FINAL_RESEARCH_REPORT.md` is grounded in verifiable project artifacts:

| Scientific Finding / Topic | Authoritative Artifact File Path | Specific Column / Parameter / Evidence Key |
| :--- | :--- | :--- |
| Specimen & Cre line assignments | `data/metadata/cell_inventory.csv` | `specimen__id`, `line_name`, `structure__layer` |
| Biophysical model assignments | `data/metadata/model_inventory.csv` | `model__id`, `specimen__id`, `morphology__id` |
| Primary calibration sweeps | `results/phase4b/calibrated_fhn_parameters.csv` | `calibration_sweep_id`, `stimulus_amplitude_pa` |
| Eight calibrated FHN parameters | `results/phase4b/calibrated_fhn_parameters.csv` | `C_m`, `g_L`, `V_rest`, `V_th`, `V_peak`, `k_v`, `tau_w`, `a_w` |
| 109 held-out evaluation sweeps | `results/phase4c/fhn_detailed_comparison.csv` | `sweep_number`, `stimulus_amplitude`, `heldout_set` |
| Population held-out summary metrics | `results/phase4c/population_summary.csv` | `step_rmse`, `overall_rmse`, `spike_count_error`, `r` |
| Spike detection contingency matrices | `results/phase4c/population_summary.csv` | `tp`, `fp`, `fn`, `tn`, `sensitivity`, `specificity` |
| Subthreshold $I$–$V$ relationships | `results/phase4c/subthreshold_iv_data.csv` | `stimulus_amplitude`, `v_steady_recorded`, `v_steady_fhn` |
| Population A per-sweep $F$–$I$ table | `results/phase3b/heldout/484564503/aggregated_metrics.csv` | `sweep_number`, `stimulus_amplitude`, `spike_count` |
| Population B $F$–$I$ rate capping | `results/phase4c/fhn_detailed_comparison.csv` (Pop B) | Sweeps 40, 41, 42, 43, 44 (`spike_count_recorded`, `fhn`) |
| Population C spike adaptation | `results/phase3b/heldout/471129934/aggregated_metrics.csv` | `isi_first`, `isi_last`, `adaptation_index` |
| Population D latency delay | `results/phase4c/fhn_detailed_comparison.csv` (Pop D) | `latency_to_first_spike_recorded`, `fhn` |
| Parameter scan 1 ($25 \times 25$) | `results/phase4b/population_d_parameter_scan.csv` | Scan 1 ($C_m \in [40, 240]$, $\tau_w \in [8, 60]$, max lat 18.5 ms) |
| Parameter scan 2 ($31 \times 31$) | `results/phase4b/results_summary.json` | Scan 2 ($C_m \in [40, 220]$, $\tau_w \in [8, 50]$, max lat 17.4 ms) |
| First Lyapunov coefficients ($l_1$) | `results/phase4c3/phase4c3_hopf_normal_form_parameters.csv` | `l1_first_lyapunov_coefficient`, `bifurcation_type` |
| Verified open bistability intervals | `results/phase4c3/phase4c3_bistability_verification.csv` | `i_fold_pa`, `i_hopf_pa`, `interval_open_bistable` |
| Hyperpolarizing sag amplitudes | `results/phase5/PHASE5B3_FINAL_CONSISTENCY_CHECK.md` | Pop A: 0.80 mV, B: 1.13 mV, C: 0.63 mV, D: 1.86 mV |

---

## 10. Recommended Next Steps in Priority Order

To move the project from its current audited state to final publication release, execute the following staged progression:

```
[Phase 5D Audit: Complete]
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Pre-Export Formatting & Layout Finalization  │
│  - Partition Table 4 or configure print CSS (7.5 pt)   │
│  - Add formal Figure Appendix linking to Phase 4C PNGs │
│  - Append DOIs to References 2–11 in Section 16        │
└────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Camera-Ready PDF Compilation                  │
│  - Render HTML intermediate with MathJax & Print CSS   │
│  - Compile PDF via Headless Chrome / Microsoft Edge    │
│  - Visually inspect page breaks, equations, and tables │
└────────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Release Packaging & Repository Isolation      │
│  - Stage Tier A and Tier B deliverables                │
│  - Ensure Tier C (raw NWB, traces, caches) is ignored  │
│  - Validate release manifest against SHA256 checksums  │
└────────────────────────────────────────────────────────┘
```

1. **Stage 1 — Pre-Export Formatting & Layout Finalization:**
   - Resolve Table 4 width for portrait PDF rendering (either split into Spike Metrics and Voltage Metrics, or add a print CSS stylesheet).
   - Integrate publication figures by adding an illustrated figure gallery or appendix referencing `results/phase4c/figures/`.
   - Add DOIs to bibliography entries 2–11 in §16.
2. **Stage 2 — Camera-Ready PDF Compilation:**
   - Generate `results/phase5/FINAL_RESEARCH_REPORT.pdf` using Headless Chrome or Edge with tailored print CSS.
   - Verify that all equations, tables, and ASCII boxes render without truncation or awkward pagination.
3. **Stage 3 — Release Packaging & Repository Isolation:**
   - Verify `.gitignore` to ensure `data/nwb_cache/`, `tmp/model_cache/`, and `traces.npz` remain excluded.
   - Tag the release commit on `ashish-work` once finalized.

---

## 11. Final Checks and Environment Status

- **Git Branch:** `ashish-work`
- **Git Status:** Clean with respect to remote tracking (`origin/ashish-work`). Only untracked files in `results/phase5/` exist.
- **Historical Artifact Integrity:** Confirmed. Zero modifications were made to Phase 0–4 source code, tests, raw data, or intermediate result CSVs. No historical Phase 5 audit records were modified during Phase 5D.
- **Scientific Integrity Status:** The empirical evaluation metrics and spike-detection classifications have been independently reconciled against the frozen evaluation data. Population-specific Hopf and bistability findings are supported by analytical local calculations and numerical dynamical evidence, subject to the documented limitations of the numerical fold estimates.
- **Export Blockers:** Table 4 width (15 columns, 214 chars wide) requires landscape orientation or table partitioning prior to PDF generation. Toolchain binaries (Headless Chrome/Edge, MiKTeX) are functional on the host machine.
- **Test Status:** Passing. The full test suite was validated in Phase 5C.3 (451/451 unit and integration tests passing in 52.80s). Re-running tests was intentionally omitted during this read-only documentation audit.
- **Final Release Recommendation:** **The project is conditionally ready. Public release cannot proceed while repository licensing decisions remain pending with the owner, derived data redistribution terms are unreviewed, and manuscript layout/export formatting issues remain unresolved.**


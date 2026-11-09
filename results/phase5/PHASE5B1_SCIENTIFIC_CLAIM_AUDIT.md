# INCM Phase 5B.1 — Independent Scientific Claim Audit of Cross-Population Synthesis

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Authoritative Milestone:** Phase 5B.1 Independent Audit Record  
**Date:** 2026-11-09  
**Audited Artifact:** [`results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md)  
**Status:** Audit complete; targeted qualifications and corrections applied in place; working tree left uncommitted.

---

## 1. Executive Audit Overview

Phase 5B.1 conducted an independent scientific claim audit of the cross-population synthesis artifact (`results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md`) generated under Phase 5B. The audit evaluated whether every statement in the synthesis was strictly supported by the empirical and numerical evidence established in Phases 0 through 4C.3.1, ensuring that:
1. Empirical observations are not presented as proven biophysical mechanisms or causal explanations without direct experimental proof.
2. Formulation-specific and parameter-subspace limitations of the 2-variable FitzHugh–Nagumo (FHN) model are not over-generalized into universal mathematical impossibility theorems for all reduced models.
3. Provisional numerical observations (such as action-potential upstroke velocities) are not presented as standardized headline metrics.
4. The five-tier behaviour taxonomy accurately distinguishes between features reproduced reasonably well, behaviours reproduced under restricted conditions, systematically mismatched or subspace-constrained dynamics, and features structurally absent from the current equations.

---

## 2. Authoritative Source Artifacts Inspected

The audit cross-referenced every quantitative claim and narrative conclusion against the following frozen and audited repository artifacts:

| Domain / Phase | Authoritative Source Artifacts Inspected |
| :--- | :--- |
| **Phase 3B / 3C Detailed Models** | [`results/phase3b/heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv)<br>[`results/phase3b/heldout_rheobase.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_rheobase.csv)<br>[`results/phase3b/PHASE3B_FINAL_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_FINAL_REPORT.md)<br>[`results/phase3b/PHASE3B_CROSS_POPULATION_ANALYSIS.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_CROSS_POPULATION_ANALYSIS.md)<br>[`results/phase3c/PHASE3C_FINAL_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3c/PHASE3C_FINAL_REPORT.md) |
| **Phase 4B / 4B.1 / 4B.2 FHN Calibration** | [`results/phase4b/fhn_fitted_parameters.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b/fhn_fitted_parameters.csv)<br>[`results/phase4b/fhn_calibration_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b/fhn_calibration_metrics.csv)<br>[`results/phase4b1/fhn_population_d_pareto_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b1/fhn_population_d_pareto_audit.csv)<br>[`results/phase4b1/PHASE4B1_INDEPENDENT_CALIBRATION_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b1/PHASE4B1_INDEPENDENT_CALIBRATION_AUDIT.md)<br>[`results/phase4b2/fhn_population_d_grid_points.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/fhn_population_d_grid_points.csv)<br>[`results/phase4b2/fhn_population_d_refined_pareto.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/fhn_population_d_refined_pareto.csv)<br>[`results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md) |
| **Phase 4C / 4C.1 Held-Out Evaluations** | [`results/phase4c/population_summary.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c/population_summary.csv)<br>[`results/phase4c/protocol_family_summary.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c/protocol_family_summary.csv)<br>[`results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md)<br>[`results/phase4c1/phase4c1_spike_detection_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_spike_detection_audit.csv)<br>[`results/phase4c1/phase4c1_subthreshold_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_subthreshold_audit.csv)<br>[`results/phase4c1/phase4c1_rmse_decomposition.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_rmse_decomposition.csv)<br>[`results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md) |
| **Phase 4C.2 / 4C.3 Dynamical Audits** | [`results/phase4c2/phase4c2_isi_transient_adaptation.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c2/phase4c2_isi_transient_adaptation.csv)<br>[`results/phase4c2/PHASE4C2_DYNAMICAL_BEHAVIOUR_AND_HOPF_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c2/PHASE4C2_DYNAMICAL_BEHAVIOUR_AND_HOPF_AUDIT.md)<br>[`results/phase4c3/phase4c3_biological_adaptation_scope.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_biological_adaptation_scope.csv)<br>[`results/phase4c3/phase4c3_hopf_independent_checks.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_hopf_independent_checks.csv)<br>[`results/phase4c3/phase4c3_bistability_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_bistability_verification.csv)<br>[`results/phase4c3/phase4c3_fold_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_fold_verification.csv)<br>[`results/phase4c3/PHASE4C3_GLOBAL_DYNAMICS_AND_ADAPTATION_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/PHASE4C3_GLOBAL_DYNAMICS_AND_ADAPTATION_AUDIT.md)<br>[`results/phase4c3/PHASE4C3_CORRECTION_LOG.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/PHASE4C3_CORRECTION_LOG.md) |
| **Phase 5 Baseline Handoff** | [`results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md) |

---

## 3. Audit of the Three High-Priority Concerns

### Concern A: Detailed-Model Rheobase Mismatch (+60 pA in Populations A and C)
- **Claim Under Review:** Statements attributing the $+60\text{ pA}$ rheobase overestimation in Populations A and C causally to calibration on strongly suprathreshold sweeps (+370 pA and +410 pA) or implying that conductance-based models inherently fail near threshold.
- **Empirical Audit:**
  - *Directly Demonstrated Facts:* In the COARSE protocol ([`results/phase3b/heldout_rheobase.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_rheobase.csv)), biological rheobase is $(270, 290]\text{ pA}$ for Pop A and $(270, 290]\text{ pA}$ for Pop C. The detailed models fire their first spike at $(330, 350]\text{ pA}$, resulting in an exact $+60\text{ pA}$ rheobase shift. In COARSE sweeps, the detailed models missed 7 biological spiking sweeps in Pop A (firing in 4/11) and 7 in Pop C (firing in 4/11). In Population D, the detailed model matched rheobase exactly ($(190, 210]\text{ pA}$, shift $0\text{ pA}$), and in Population B the shift was modest ($+20\text{ pA}$).
  - *Speculative Elements:* Neither Phase 3B nor Phase 3C conducted a re-calibration experiment at near-threshold current to prove that calibration sweep amplitude was the causal mechanism. Other plausible factors include the $+13.6\text{ mV}$ resting offset in Pop A, active conductance densities in the published Allen model, or spatial dendritic filtering.
- **Audit Decision & Corrections:** All causal attributions were replaced with neutral empirical observations. Calibration on suprathreshold sweeps is documented strictly as a *plausible methodological consideration / hypothesis*, and the text explicitly clarifies that this does not establish a general limitation of conductance-based modeling.

### Concern B: FHN Structural Limitations and Claim Boundaries
- **Claim Under Review:** Statements characterizing multi-timescale adaptation, latency decoupling, and high-frequency rate scaling as "structurally absent" or "mathematically impossible" for reduced models.
- **Analytical & Empirical Audit:**
  - *Distinction 1: Features lacking explicit mathematical representations in the current equations:*
    - *Hyperpolarization Sag ($I_h$):* The linear recovery equation $\frac{\mathrm{d}w}{\mathrm{d}t} = \frac{a_w(V - V_{\mathrm{rest}}) - w}{\tau_w}$ possesses no hyperpolarization-activated inward conductance term. Under the tested $-110\text{ pA}$ condition, the calibrated FHN models produced zero measured sag ($\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$ across all populations). This characterizes the tested formulation and calibrated parameter sets under this protocol, and must not be conflated with a universal mathematical theorem about all conceivable parameterizations of two-variable planar systems. Intracellular biological recordings at $-110\text{ pA}$ exhibit modest inward sag ($0.63\text{--}1.86\text{ mV}$: Pop A = $0.80\text{ mV}$, Pop B = $1.13\text{ mV}$, Pop C = $0.63\text{ mV}$, Pop D = $1.86\text{ mV}$). In detailed Allen models, sag was not quantified in project evaluation metrics (no $\Delta V_{\mathrm{sag}}$ metric extracted in Phase 3B/4C). The "1.5–5.4 mV" figure previously cited in chat was an erroneous conflation with the 5.4-fold spike-frequency adaptation ratio in Population A.
    - *Multi-Timescale Adaptation:* The autonomous planar system possesses a single recovery variable $w(t)$ on timescale $\tau_w \approx 7\text{--}39\text{ ms}$. Trajectories contract onto the limit cycle within $\le 2$ cycles ($\le 120\text{ ms}$; initial transient ISI adjustment of $-0.5\%\text{ to }+1.2\%$), settling to stationary periodic firing ($\Delta \mathrm{ISI} < 0.01\%$). Sustained multi-second adaptation across 1-second pulses (as measured in the 23 qualifying multi-cycle biological sweeps) was not reproduced because the equations lack a slow second recovery process.
  - *Distinction 2: Empirical limitations poorly reproduced by the calibrated parameter sets:*
    - *High-Frequency Firing:* In Population B and Population D, the calibrated FHN models underfire at high currents due to premature depolarization block or heavy recovery damping ($\tau_w = 38.86\text{ ms}$). This is a parameter-tuning limitation of these specific calibrated models, not an inherent impossibility of the FHN equations (which can cycle rapidly if $C_m$ and $\tau_w$ are small).
  - *Distinction 3: Subspace constraints in the investigated parameter space:*
    - *Population D Latency-Frequency Trade-Off:* Across 961 explicit RK4 simulations in $(C_m, \tau_w) \in [40, 220]\text{ pF} \times [8, 50]\text{ ms}$ for specimen `471786879`, configurations with $N_{\mathrm{spk}} \ge 12$ have latency $\le 17.40\text{ ms}$ ($\le 16.00\text{ ms}$ at 13 spikes), while configurations with $t_{\mathrm{lat}} \ge 50\text{ ms}$ yield $N_{\mathrm{spk}} \le 4$. Per Phase 4B.2 Table 3.1, this is an empirical trade-off within the investigated 2D subspace under the calibration objective, **not** an unproven universal impossibility theorem for all planar systems. In the detailed model, delayed latency ($52.97\text{ ms}$) and repetitive firing (14 spikes) coexist at a single observed calibration operating point (Sweep 42, $+250\text{ pA}$), but this is not an invariant decoupling across all stimulus protocols (e.g., at $+210\text{ pA}$ its first spike is delayed to $978.91\text{ ms}$, firing only 1 spike vs. 5 biological spikes).
- **Audit Decision & Corrections:** Decoupled first-spike latency was moved out of Tier 4 ("Structurally Absent") and reclassified under Tier 3 as an empirical subspace constraint. Adaptation was qualified as "not reproduced over sustained multi-second timescales in the tested two-variable autonomous formulation and parameterization."

### Concern C: Action-Potential Waveform Kinetics and Upstroke Metrics
- **Claim Under Review:** Citing numerical upstroke velocities ($5.7\text{--}6.2\text{ V/s}$ for FHN vs. $397\text{--}466\text{ V/s}$ biological, $60\times\text{--}75\times$ slower) as definitive headline results, or claiming that detailed models "accurately reproduce" fine AP kinetics.
- **Methodological Audit:**
  - In Phase 4C.1 (§6, C6), this numerical comparison was audited and classified as *provisional*.
  - The biological recording sampling rate (200 kHz) and the FHN numerical integration time-step ($\Delta t = 0.025\text{ ms} \implies 40\text{ kHz}$) were not standardized with identical low-pass filtering, digital differentiation stencils (e.g., 5-point stencil vs. simple 2-point difference), or standardized voltage threshold windows across all sweeps.
  - Furthermore, the detailed models' fine phase-plane derivative kinetics ($\mathrm{d}V/\mathrm{d}t$ vs. $V$) were not standardized or benchmarked against recorded spikes under identical stencils; while they capture narrow spikes and lower step RMSE ($4.15\text{--}8.30\text{ mV}$), claiming they "accurately reproduce AP kinetics" without qualification exceeds the evidence.
- **Audit Decision & Corrections:** The $60\times\text{--}75\times$ figure and exact numerical upstroke velocities are retained strictly as *provisional supporting observations* and omitted from headline findings. The synthesis distinguishes observed waveform differences (narrow fast spike vs broad relaxation wave) from provisional numerical upstroke metrics, and explicitly notes that fine standardized kinetics remain unverified.

---

## 4. Audit of the Five-Tier Behaviour Taxonomy

| Taxonomy Tier | Original Classification in Synthesis | Audit Evaluation | Required Action / Qualification Applied |
| :--- | :--- | :--- | :--- |
| **Tier 1: Reproduced Reasonably Well** | Resting potential ($V_{\mathrm{rest}}$); passive charging and input resistance ($R_{\mathrm{in}}$). | **Supported by Data.** $V_{\mathrm{rest}}$ matches biology by construction ($0.00\text{ mV}$ offset). $R_{\mathrm{in}}$ and hyperpolarizing linearity are excellent ($r^2 > 0.996$). | **Qualified:** Clarified that high hyperpolarizing correlation ($r^2 > 0.996$) must not be conflated with general all-subthreshold performance. |
| **Tier 2: Reproduced Under Restrictions** | Mutually subthreshold linearity; macroscopic excitability threshold (spike detection); monotonic rate scaling. | **Supported with Caveats.** Mutually subthreshold $r^2$ is high in Pops B and D ($0.990, 0.995$), but degrades in Pops A and C ($0.925, 0.952$). Spike detection sensitivity is $92.5\%$, but specificity is $89.9\%$ (7 false positives). | **Qualified:** Emphasized that high binary spike-detection sensitivity does **not** establish accurate spike trains or rate coding. Noted that monotonic rate scaling breaks down in FINEST protocols and near depolarization block. |
| **Tier 3: Systematically Mismatched / Subspace-Constrained** | Action potential kinetics; suprathreshold spike counts; latency-frequency trade-off. | **Mixed Provenance.** AP kinetics divergence is directly observed. Spike count underfiring in Pop D is a parameter constraint. Latency decoupling was previously mislabeled as structurally absent. | **Reclassified & Qualified:** Latency-frequency decoupling in Pop D moved here as an empirical 2D subspace constraint across 961 simulations, not a universal impossibility. AP upstroke velocity metrics explicitly labeled provisional. |
| **Tier 4: Structurally Absent from Current Formulation** | Sustained multi-second adaptation; hyperpolarization sag ($I_h$). | **Conceptually Accurate.** Equations contain no explicit $I_h$ conductance or slow secondary recovery variable. | **Refined Phrasing:** Qualified that autonomous planar limit cycles settle to asymptotic stationarity within $\le 2$ cycles in these evaluations; sustained multi-second adaptation is absent in this formulation, but this is distinguished from claims about all possible reduced models. |
| **Tier 5: Not Adequately Identifiable** | Channel-specific attributions ($I_A$, $I_{\mathrm{SK}}/I_M$); projection classes (IT/ET/PT/CT). | **Supported by Data Boundaries.** No pharmacological blockers or projection tracing metadata exist in the Allen dataset. | **Retained as Written.** Confirmed as unverified hypotheses and open research gaps. |

---

## 5. Summary of Corrections Applied to `PHASE5_CROSS_POPULATION_SYNTHESIS.md`

The following exact text updates were executed directly in `results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md`:

```carousel
### Correction 1: Section 1.1 (Adaptation Framing)
**Before:**
> "In contrast, the autonomous two-variable FHN formulation exhibits only brief transient cycle-to-cycle adjustments ($\le 2$ cycles, $\le 120\text{ ms}$; initial ISI change of $-0.5\%\text{ to }+1.2\%$), after which trajectories contract onto the periodic orbit where consecutive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$). Multi-second adaptation is structurally absent from the two-variable formulation."

**After:**
> "In contrast, the autonomous two-variable FHN formulation exhibits only brief transient cycle-to-cycle adjustments ($\le 2$ cycles, $\le 120\text{ ms}$; initial ISI change of $-0.5\%\text{ to }+1.2\%$), after which trajectories contract onto the periodic orbit where consecutive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$). Sustained multi-second adaptation was not reproduced over sustained timescales in the tested two-variable autonomous formulation with a single recovery timescale $\tau_w$."
<!-- slide -->
### Correction 2: Section 5.1 & 5.3 (Detailed Model Rheobase Mismatch)
**Before (Section 5.1):**
> "Consequently, it overestimates rheobase by $+60\text{ pA}$ (spiking only in 4 out of 11 biological spiking sweeps; sensitivity $36.4\%$)."

**After (Section 5.1):**
> "In the COARSE protocol, the detailed model overestimates rheobase by $+60\text{ pA}$ (spiking in only 4 out of 11 biological spiking sweeps; sensitivity $36.4\%$). Whether this shift is causally related to the resting potential offset, to calibration on a strongly suprathreshold sweep (+370 pA), or to active conductances in the published fit remains an unresolved question, rather than a proven failure of conductance-based modeling generally."

**Before (Section 5.3):**
> "overestimating rheobase by $+60\text{ pA}$."

**After (Section 5.3):**
> "overestimating COARSE-protocol rheobase by $+60\text{ pA}$. The underlying cause for this rheobase shift remains unresolved, and calibration on a single suprathreshold sweep (+410 pA) is a possible methodological consideration rather than an established explanation."
<!-- slide -->
### Correction 3: Section 6 (Taxonomy Reclassification & AP Kinetics)
**Before:**
> Latency decoupling placed under "Tier 4: Structurally Absent from the Two-Variable FHN Formulation" as a universal constraint. AP kinetics cited with definitive $60\times\text{--}75\times$ upstroke ratio without methodological status.

**After:**
> - Moved Decoupled First-Spike Latency to **Tier 3** as an empirical constraint mapped across 961 simulations in the tested $(C_m, \tau_w)$ subspace, explicitly stating it is not an unproven universal mathematical theorem.
> - Added explicit **Methodological Status** note labeling numerical upstroke velocity comparisons ($5.7\text{--}6.2\text{ V/s}$ vs. $397\text{--}466\text{ V/s}$) as provisional supporting observations due to unstandardized filtering, sampling rates, and differentiation stencils.
> - Clarified Tier 1 distinction between hyperpolarizing linearity ($r^2 > 0.996$) and all-subthreshold performance.
> - Clarified Tier 2 warning: high binary spike-detection sensitivity ($92.5\%$) does not establish accurate spike trains or rate coding.
<!-- slide -->
### Correction 4: Section 7.1 & Section 11 (Neutral Rheobase Observation)
**Before (Section 7.1):**
> "The detailed models, burdened by complex active conductances, were tuned too far from rheobase in Populations A and C, detecting only **$24 / 40$ biological spiking sweeps** ($60.0\%$)."`

**After (Section 7.1):**
> "The detailed models overestimate COARSE rheobase by approximately $+60\text{ pA}$ in Populations A and C, detecting only **$24 / 40$ biological spiking sweeps** ($60.0\%$). While calibration on a single suprathreshold sweep (+370/+410 pA) is a plausible methodological consideration, the definitive biophysical cause remains unresolved, and this discrepancy should not be construed as an established general failure of conductance-based modeling."

**Before (Section 11, Point 2):**
> "In multi-compartment biophysical models, fitting a single suprathreshold sweep (+370/+410 pA) led to severe rheobase overestimation near threshold (+60 pA shift in Pops A and C). Calibration algorithms must enforce subthreshold impedance and near-threshold rheobase constraints simultaneously."

**After (Section 11, Point 2):**
> "In multi-compartment biophysical models, the detailed models for Populations A and C overestimated COARSE rheobase by approximately $+60\text{ pA}$. While fitting to a single suprathreshold sweep (+370/+410 pA) is a plausible methodological contributor, the definitive cause remains unresolved. This highlights the practical importance of evaluating models across the entire dynamic range rather than assuming suprathreshold parameter fits generalize to threshold activation."
````

---

## 6. Claims Retained with Necessary Qualifications

The audit confirmed that the following key scientific conclusions are fully supported by repository evidence and are retained in the synthesis:

1. **Exact Spike Detection Contingency Table:** Across 109 sweeps, biological ground truth has 40 spiking and 69 non-spiking sweeps. FHN achieved 37 TP, 7 FP, 3 FN, 62 TN (sensitivity $92.5\%$, specificity $89.9\%$, balanced accuracy $91.2\%$), firing in 44 sweeps total. Detailed models achieved 24 TP, 0 FP, 16 FN, 69 TN (sensitivity $60.0\%$, specificity $100.0\%$, balanced accuracy $80.0\%$).
2. **Mathematical Decomposition of Pop A Overall RMSE:** $92.3\%$ of the detailed model's overall MSE is mathematically proven to arise from the $+13.6\text{ mV}$ baseline offset during the non-step intervals ($87.5\%$ of duration), while $89.2\%$ of FHN's MSE arises during the step pulse. FHN's overall RMSE advantage ($8.24\text{ mV}$ vs. $12.73\text{ mV}$) reflects baseline alignment, not superior step waveform reproduction.
3. **Biological Adaptation Census:** 100% of the 23 qualifying multi-cycle sweeps display first-to-last ISI expansion, with medians ranging from $1.97\times$ (Pop D) to $3.45\times$ (Pop A), and extreme adaptation ($\ge 5\times$) confined to only 3 sweeps across the dataset.
4. **Population D Scan Provenance:** The 625-point scan ($[40, 240]\text{ pF} \times [8, 60]\text{ ms}$, max latency $18.50\text{ ms}$ for $\ge 12$ spikes, $12.20\text{ ms}$ at 13 spikes) and the 961-point scan ($[40, 220]\text{ pF} \times [8, 50]\text{ ms}$, max latency $17.40\text{ ms}$ for $\ge 12$ spikes, $16.00\text{ ms}$ at 13 spikes) are retained as distinct, mutually supportive empirical scans.
5. **Open Bistability Semantics and Authoritative Intervals:** Numerical coexistence of a stable resting state and a stable periodic spiking orbit strictly holds on the open interval $(I_{\mathrm{fold}}, I_{H1})$, with non-hyperbolic limit-cycle fold boundaries ($I_{\mathrm{fold}}$) and non-hyperbolic Hopf equilibria ($I_{H1}$). From [`results/phase4c3/phase4c3_bistability_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_bistability_verification.csv), the verified open intervals are:
   - **Population A:** $(214.16, 234.34)\text{ pA}$ ($\Delta I = 20.18\text{ pA}$)
   - **Population B:** $(146.72, 161.28)\text{ pA}$ ($\Delta I = 14.55\text{ pA}$)
   - **Population C:** $(360.03, 385.33)\text{ pA}$ ($\Delta I = 25.29\text{ pA}$)
   - **Population D:** $(215.92, 236.27)\text{ pA}$ ($\Delta I = 20.36\text{ pA}$)
   *(Provenance note: Spurious intervals cited in earlier conversational chat—such as A: (140.23, 140.48) pA, B: (36.00, 37.07) pA, C: (69.87, 72.03) pA, D: (30.31, 31.81) pA—were conversational reporting artifacts resulting from conflating first-spike latency (37.07 ms), action-potential peak voltage (31.81 mV), and metadata IDs. They do not exist in any repository CSV and are completely superseded by the verified Phase 4C.3 intervals above).*
6. **Hyperpolarization Sag Provenance:** At $-110\text{ pA}$ current injection, biological recordings exhibit modest inward sag ($0.63\text{--}1.86\text{ mV}$: Pop A = $0.80\text{ mV}$, Pop B = $1.13\text{ mV}$, Pop C = $0.63\text{ mV}$, Pop D = $1.86\text{ mV}$ per `PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md`). In the FHN model, linear recovery yields monotonic charging with $0.00\text{ mV}$ sag across all four populations. In the detailed Allen models, sag was not extracted or quantified in repository evaluation metrics; the "1.5–5.4 mV" figure previously cited in chat was an erroneous conflation with Population A's 5.4-fold spike-frequency adaptation ratio.

---

## 7. Remaining Unresolved Scientific Questions

The audit confirms that the following five questions remain open scientific gaps that must be treated as discussion points or limitations in Phase 5C:

1. **Biophysical Cause of Detailed Rheobase Overestimation:** Whether the $+60\text{ pA}$ shift in Populations A and C stems from suprathreshold fitting bias, spatial dendritic attenuation, or specific potassium conductance densities cannot be determined without targeted model re-optimization.
2. **Mechanism of Delayed First-Spike Latency in Population D:** Attributing the $58\text{ ms}$ onset delay to transient A-type potassium current ($I_A$) is a plausible hypothesis supported by biophysical literature, but remains unproven in this dataset due to lack of pharmacological channel isolation.
3. **Biological Origin of Within-Cell Protocol Nonstationarity:** Biological firing differences between COARSE and FINEST sweeps within the same specimen (e.g. Pop D firing 1 spike at +240 pA in FINEST vs. multiple spikes in COARSE) remain unresolved (hypotheses include slow cumulative channel inactivation or intracellular ionic shifts).
4. **High-Dimensional Global Pareto Search:** Whether a complex non-polynomial or 7-parameter FHN parameterization can decouple onset latency from cycle period remains unproven.
5. **Generalizability Across Cortical Layers:** Because each population is represented by a single specimen ($n=1$), observed differences cannot establish population-level statistical variance across cortical layers.

---

## 8. Confirmation of Repository and Evidence Integrity

- **Frozen Evidence Untouched:** No files in `results/phase3b/`, `results/phase3c/`, `results/phase4b/`, `results/phase4b1/`, `results/phase4b2/`, `results/phase4c/`, `results/phase4c1/`, `results/phase4c2/`, or `results/phase4c3/` were modified.
- **Baseline Handoff Preserved:** `results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md` was inspected and verified; no modifications were made.
- **No Simulations Run:** Zero new simulations, model fittings, parameter tunings, or data evaluations were executed.
- **Git State:** Working tree remains clean with respect to tracked files; `results/phase5/` contains the updated synthesis document and this audit record. All changes remain **strictly uncommitted** on branch `ashish-work`.
- **Phase 5C Status:** Not started. Ready for subsequent instructions.


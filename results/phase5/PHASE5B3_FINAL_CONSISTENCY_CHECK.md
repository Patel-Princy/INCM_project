# INCM Phase 5B.3 — Final Scientific Wording and Evidence Consistency Check

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Authoritative Milestone:** Phase 5B.3 Final Consistency Check  
**Date:** 2026-11-09  
**Audited Artifacts:**
- [`results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md)
- [`results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md)
- [`results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md)
- [`results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md)

---

## 1. Executive Summary & Freeze Readiness

Phase 5B.3 conducted the final targeted scientific wording and evidence consistency review of the completed Phase 5B cross-population synthesis and audit records prior to freezing Phase 5B.

The review confirmed that:
1. **Detailed-Model Action-Potential Fidelity:** The synthesis strictly separates the detailed models' lower step RMSE ($4.15\text{--}8.30\text{ mV}$) and qualitative waveform profile similarity from directly validated fine action-potential kinetics (rise times, upstroke velocities, repolarization rates, AHP depths), which were not standardized across models. Derivative-based upstroke comparisons remain explicitly designated as provisional supporting observations.
2. **Hyperpolarization Sag ($I_h$) Scope:** Biological sag is preserved at $0.80\text{ mV}$ (A), $1.13\text{ mV}$ (B), $0.63\text{ mV}$ (C), and $1.86\text{ mV}$ (D) at $-110\text{ pA}$. Detailed model sag is preserved as **Not Quantified**. FHN sag is preserved as $0.00\text{ mV}$ under the audited $-110\text{ pA}$ condition, cleanly distinguishing the absence of an explicit $I_h$ inward conductance mechanism and zero measured sag in the tested condition from any universal mathematical claim about all possible planar parameterizations.
3. **Population D Latency Decoupling Scope:** The detailed model's reproduction of delayed first-spike latency ($52.97\text{ ms}$) and repetitive firing (14 spikes) is strictly documented as a **single observed operating point** at the calibration condition (Sweep 42, COARSE, $+250\text{ pA}$), and is not generalized into an invariant decoupling capability across all stimulus protocols. The FHN latency-frequency trade-off is bounded strictly to the investigated 2D parameter subspace ($[40, 220]\text{ pF} \times [8, 50]\text{ ms}$).
4. **Complete Cross-Document Agreement:** All four Phase 5 documents exhibit $100\%$ numerical and semantic agreement across all audited parameters, denominators, contingency tables, bistability intervals, and scan criteria.

**Readiness Determination:** **Phase 5B is fully verified, scientifically qualified, and ready to be frozen.**

---

## 2. Review Item 1: Detailed-Model Action-Potential Fidelity

### 2.1 The Potential Overstatement
In comparative modeling literature, investigators often infer that detailed multi-conductance biophysical models "accurately reproduce action-potential kinetics" solely because their in-step root-mean-square error (step RMSE) is substantially lower than that of reduced planar models (e.g., $4\text{--}8\text{ mV}$ vs. $12\text{--}24\text{ mV}$).

### 2.2 Three-Way Evidentiary Separation Enforced
Phase 5B.3 verifies that the synthesis and audit records rigorously maintain a three-part evidentiary distinction:

1. **Lower Step RMSE Relative to FHN (Demonstrated Metric):**
   - Detailed model step RMSE ranges between $4.15\text{ mV}$ and $8.30\text{ mV}$ across the four populations, compared to $12.36\text{ mV}$ to $23.73\text{ mV}$ for FHN.
   - *Physical Meaning:* This lower error reflects superior alignment with the broad temporal profile of spikes (narrow action-potential duration and rapid return to subthreshold baseline), avoiding the massive area mismatch caused by broad FHN cubic relaxation waves.
   - *Boundary:* Lower step RMSE does **not** prove accurate fine phase-plane derivative kinetics.
2. **Qualitative Similarity of Spike Waveform Profiles (Observed Trajectory):**
   - Somatic biological spikes exhibit narrow durations ($< 1.5\text{ ms}$ half-width), rapid repolarization, and sharp afterhyperpolarization (AHP) troughs.
   - Detailed models generate active $\mathrm{Na}_v / K_v$ spikes with narrow widths and rapid downstrokes that visually resemble recorded spikes.
3. **Directly Validated Kinetic Measurements (Unverified Benchmark):**
   - Directly validated measurements of AP 10%–90% rise times, maximum upstroke velocities ($\mathrm{d}V/\mathrm{d}t_{\mathrm{max}}$), maximum repolarization velocities ($\mathrm{d}V/\mathrm{d}t_{\mathrm{min}}$), and AHP trough depths were **not systematically extracted, filtered, or benchmarked** under identical stencils for either model tier across held-out sweeps.
   - The unstandardized numerical upstroke comparison ($397\text{--}466\text{ V/s}$ recorded vs. $5.7\text{--}6.2\text{ V/s}$ FHN) remains explicitly classified as a **provisional supporting observation** due to differences in analog filtering, sampling rates (200 kHz vs. fixed RK4 steps), and digital differentiation stencils.

---

## 3. Review Item 2: Hyperpolarization Sag ($I_h$) Scope and Wording

### 3.1 Preserved Numerical Metrics
- **Biological Experimental Sag at $-110\text{ pA}$ (1000 ms pulse):**
  - Population A (Specimen `484564503`, Sweep 0): $\Delta V_{\mathrm{sag}} = 0.80\text{ mV}$
  - Population B (Specimen `318808427`, Sweep 31): $\Delta V_{\mathrm{sag}} = 1.13\text{ mV}$
  - Population C (Specimen `471129934`, Sweep 49): $\Delta V_{\mathrm{sag}} = 0.63\text{ mV}$
  - Population D (Specimen `471786879`, Sweep 83): $\Delta V_{\mathrm{sag}} = 1.86\text{ mV}$
  - *Range:* $0.63\text{--}1.86\text{ mV}$ (modest inward rectification, $< 2.0\text{ mV}$).
- **Detailed Biophysical Model Sag:**
  - Formally documented as **Not Quantified** in repository evaluation metrics (no $\Delta V_{\mathrm{sag}}$ column in `heldout_metrics.csv` or summary reports). The spurious "1.5–5.4 mV" figure was an erroneous transposition of Population A's 5.4-fold spike-frequency adaptation ratio.
- **FitzHugh–Nagumo Sag:**
  - $\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$ across all four populations under the tested $-110\text{ pA}$ condition.

### 3.2 Critical Three-Way Formulation Distinction
To prevent over-generalization into unproven mathematical theorems, the wording distinguishes:
1. **Formulation Feature:** The two-variable FHN model uses a linear recovery equation $\frac{\mathrm{d}w}{\mathrm{d}t} = \frac{a_w(V - V_{\mathrm{rest}}) - w}{\tau_w}$, which contains no explicit hyperpolarization-activated inward conductance term ($I_h$).
2. **Empirical Measurement:** Under the audited $-110\text{ pA}$ hyperpolarizing current step with the calibrated parameter sets, the model produced monotonic exponential relaxation with zero measured voltage sag ($\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$).
3. **Avoidance of Universal Mathematical Claims:** This reflects the tested linear-recovery formulation and calibrated parameter sets under this protocol; it is explicitly not asserted as an unproven universal mathematical theorem about all conceivable parameterizations of two-variable planar systems.

---

## 4. Review Item 3: Population D Latency and Firing-Rate Interpretation

### 4.1 Detailed Model Operating Point at Calibration
The statement that detailed models reproduce both delayed onset and repetitive firing was audited against raw held-out and calibration metrics:

- **Calibration Sweep (Sweep 42, COARSE Protocol, $+250\text{ pA}$, $1000\text{ ms}$ Step):**
  - *Biological Ground Truth:* First-spike onset latency $t_{\mathrm{lat}} = 57.95\text{ ms}$; Spike count $N_{\mathrm{spk}} = 13$.
  - *Detailed Model Prediction:* First-spike onset latency $t_{\mathrm{lat}} = 52.97\text{ ms}$; Spike count $N_{\mathrm{spk}} = 14$.
  - *Calibrated FHN Prediction:* First-spike onset latency $t_{\mathrm{lat}} = 59.90\text{ ms}$; Spike count $N_{\mathrm{spk}} = 4$ (suppressed by heavy recovery damping: $\tau_w = 38.86\text{ ms}$).

### 4.2 Why It Is a Single Operating Point, Not an Invariant Decoupling
Across other held-out sweeps on the same biological specimen (`471786879`), this simultaneous alignment is **not** uniformly maintained:
1. **Near-Threshold Sweep (Sweep 40, COARSE, $+210\text{ pA}$):**
   - Biology: Latency = $133.82\text{ ms}$, Spike count = 5.
   - Detailed Model: Latency = $978.91\text{ ms}$, Spike count = 1. The detailed model severely delays its first spike until near the end of the step and misses repetitive firing.
2. **Intermediate Suprathreshold Sweep (Sweep 41, COARSE, $+230\text{ pA}$):**
   - Biology: Latency = $92.89\text{ ms}$, Spike count = 10.
   - Detailed Model: Latency = $117.70\text{ ms}$, Spike count = 9.
3. **Protocol Non-Stationarity (Sweeps 52, 53, 54, FINEST Protocol, $+240\text{ pA}$):**
   - Biology: Firing drops to only 1 spike ($t_{\mathrm{lat}} = 129.81\text{--}200.02\text{ ms}$) due to within-cell biological non-stationarity.
   - Detailed Model: Fires 11 repetitive spikes ($t_{\mathrm{lat}} = 87.30\text{ ms}$), drastically overfiring relative to the biological recording.

**Conclusion:** The detailed model reproducing delayed onset and repetitive firing is strictly documented as a **single observed operating point at $+250\text{ pA}$**, rather than a broad, invariant decoupling capability across all stimulus protocols.

### 4.3 FHN Tested-Subspace Boundaries Retained
The FHN latency-frequency trade-off is strictly bounded to the empirical evidence:
- **Phase 4B.1 Baseline Scan (625 points):** $(C_m, \tau_w) \in [40, 240]\text{ pF} \times [8, 60]\text{ ms}$; for configurations achieving $\ge 12$ spikes, maximum latency is $18.50\text{ ms}$ ($12.20\text{ ms}$ at target 13 spikes).
- **Phase 4B.2 Refined Scan (961 points):** $(C_m, \tau_w) \in [40, 220]\text{ pF} \times [8, 50]\text{ ms}$; for configurations achieving $\ge 12$ spikes, maximum latency is $17.40\text{ ms}$ ($16.00\text{ ms}$ at target 13 spikes); configurations with $t_{\mathrm{lat}} \ge 50\text{ ms} \implies N_{\mathrm{spk}} \le 4$.
- This remains an empirically demonstrated property of the calibrated model within the tested 2D parameter subspace, not an unproven universal theorem across all planar dynamical systems.

---

## 5. Comprehensive Cross-Document Consistency Matrix

The four Phase 5 documents were cross-verified for complete numerical and semantic alignment:

| Evidence Metric / Parameter | Phase 5A Handoff | Phase 5B Synthesis | Phase 5B.1 Audit | Phase 5B.2 Resolution | Phase 5B.3 Consistency Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bistability Interval Pop A** | $(214.16, 234.34)\text{ pA}$ | $(214.16, 234.34)\text{ pA}$ | $(214.16, 234.34)\text{ pA}$ | $(214.16, 234.34)\text{ pA}$ | **$100\%$ Consistent** |
| **Bistability Interval Pop B** | $(146.72, 161.28)\text{ pA}$ | $(146.72, 161.28)\text{ pA}$ | $(146.72, 161.28)\text{ pA}$ | $(146.72, 161.28)\text{ pA}$ | **$100\%$ Consistent** |
| **Bistability Interval Pop C** | $(360.03, 385.33)\text{ pA}$ | $(360.03, 385.33)\text{ pA}$ | $(360.03, 385.33)\text{ pA}$ | $(360.03, 385.33)\text{ pA}$ | **$100\%$ Consistent** |
| **Bistability Interval Pop D** | $(215.92, 236.27)\text{ pA}$ | $(215.92, 236.27)\text{ pA}$ | $(215.92, 236.27)\text{ pA}$ | $(215.92, 236.27)\text{ pA}$ | **$100\%$ Consistent** |
| **Biological Sag at -110 pA** | $0.80, 1.13, 0.63, 1.86\text{ mV}$ | $0.80, 1.13, 0.63, 1.86\text{ mV}$ | $0.80, 1.13, 0.63, 1.86\text{ mV}$ | $0.80, 1.13, 0.63, 1.86\text{ mV}$ | **$100\%$ Consistent** |
| **Detailed Model Sag** | Not quantified | Not quantified | Not quantified | Not quantified | **$100\%$ Consistent** |
| **FHN Sag (-110 pA)** | $0.00\text{ mV}$ (tested condition) | $0.00\text{ mV}$ (tested condition) | $0.00\text{ mV}$ (tested condition) | $0.00\text{ mV}$ (tested condition) | **$100\%$ Consistent** |
| **Held-Out Sweep Total** | 109 sweeps | 109 sweeps | 109 sweeps | 109 sweeps | **$100\%$ Consistent** |
| **Spike Ground Truth** | 40 Spiking / 69 Silent | 40 Spiking / 69 Silent | 40 Spiking / 69 Silent | 40 Spiking / 69 Silent | **$100\%$ Consistent** |
| **Detailed Contingency** | 24 TP, 0 FP, 16 FN, 69 TN | 24 TP, 0 FP, 16 FN, 69 TN | 24 TP, 0 FP, 16 FN, 69 TN | 24 TP, 0 FP, 16 FN, 69 TN | **$100\%$ Consistent** |
| **FHN Contingency** | 37 TP, 7 FP, 3 FN, 62 TN | 37 TP, 7 FP, 3 FN, 62 TN | 37 TP, 7 FP, 3 FN, 62 TN | 37 TP, 7 FP, 3 FN, 62 TN | **$100\%$ Consistent** |
| **Qualifying SFA Sweeps** | 23 sweeps ($\ge 3$ spikes) | 23 sweeps ($\ge 3$ spikes) | 23 sweeps ($\ge 3$ spikes) | 23 sweeps ($\ge 3$ spikes) | **$100\%$ Consistent** |
| **Specimen Count** | 4 single-cell reps ($n=1$) | 4 single-cell reps ($n=1$) | 4 single-cell reps ($n=1$) | 4 single-cell reps ($n=1$) | **$100\%$ Consistent** |
| **Pop D Scan 1 (625 pts)** | $[40, 240]\text{ pF} \times [8, 60]\text{ ms}$ | $[40, 240]\text{ pF} \times [8, 60]\text{ ms}$ | $[40, 240]\text{ pF} \times [8, 60]\text{ ms}$ | $[40, 240]\text{ pF} \times [8, 60]\text{ ms}$ | **$100\%$ Consistent** |
| **Pop D Scan 2 (961 pts)** | $[40, 220]\text{ pF} \times [8, 50]\text{ ms}$ | $[40, 220]\text{ pF} \times [8, 50]\text{ ms}$ | $[40, 220]\text{ pF} \times [8, 50]\text{ ms}$ | $[40, 220]\text{ pF} \times [8, 50]\text{ ms}$ | **$100\%$ Consistent** |

---

## 6. Exact Source File and CSV Column References

| Parameter / Metric | Authoritative File Path | Column Name / Exact Section |
| :--- | :--- | :--- |
| **Bistability Open Intervals** | [`results/phase4c3/phase4c3_bistability_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_bistability_verification.csv) | `bistability_interval_verified`, `bistability_width_verified_pa` |
| **Hopf Points & Lyapunov $l_1$** | [`results/phase4c3/phase4c3_hopf_independent_checks.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_hopf_independent_checks.csv) | `lower_hopf_current_pa`, `first_lyapunov_coefficient` |
| **Biological Sag at -110 pA** | [`results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md) | Section 7.3 ($\Delta V_{\mathrm{sag}} = 0.80, 1.13, 0.63, 1.86\text{ mV}$) |
| **FHN Sag (0.00 mV)** | [`results/phase4c1/phase4c1_claim_evidence_matrix.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_claim_evidence_matrix.csv) | Row `C5_HYPERPOLARIZATION_SAG` |
| **Detailed Model Heldout Metrics** | [`results/phase3b/heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv) | 109 rows; `spike_count_recorded_total`, `spike_count_simulated_total`, `first_spike_recorded_ms`, `first_spike_simulated_ms` |
| **Population D Calibration Sweep** | [`results/phase4b/fhn_calibration_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b/fhn_calibration_metrics.csv) | Row `D`: `sweep_id=42`, `stimulus_amplitude_pa=250.0`, `first_spike_lat_exp_ms=57.95`, `first_spike_lat_detailed_ms=52.97`, `spikes_exp=13`, `spikes_detailed=14` |
| **Biological Adaptation Census** | [`results/phase4c3/phase4c3_biological_adaptation_scope.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_biological_adaptation_scope.csv) | `n_qualifying_sweeps` (23 total: 6 in A, 6 in B, 4 in C, 7 in D) |
| **Pop D Scan 1 (625 pts)** | [`results/phase4b1/fhn_population_d_pareto_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b1/fhn_population_d_pareto_audit.csv) | 625 rows; `cm_pf`, `tau_w_ms`, `latency_ms`, `spike_count` |
| **Pop D Scan 2 (961 pts)** | [`results/phase4b2/fhn_population_d_grid_points.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/fhn_population_d_grid_points.csv) | 961 rows; `cm_pf`, `tau_w_ms`, `latency_ms`, `spike_count` |

---

## 7. Exact Record of Wording Adjustments Executed in Phase 5B.3

````carousel
### Adjustment 1: Section 1.1 in Synthesis (Sag Wording Scope)
**Before:**
```markdown
5. **Structural Absence of Hyperpolarization Sag ($I_h$):**
   - Intracellular recordings display modest hyperpolarization-activated sag ($0.63\text{--}1.86\text{ mV}$) across all specimens. FHN's linear recovery equation produces monotonic charging with zero sag ($0.00\text{ mV}$).
```

**After:**
```markdown
5. **Hyperpolarization Sag ($I_h$) Measurement and Formulation Limitation:**
   - Intracellular recordings display modest hyperpolarization-activated sag at $-110\text{ pA}$ ($0.63\text{--}1.86\text{ mV}$: Pop A = $0.80\text{ mV}$, Pop B = $1.13\text{ mV}$, Pop C = $0.63\text{ mV}$, Pop D = $1.86\text{ mV}$). Detailed-model sag was not quantified in project evaluation metrics.
   - Under the tested $-110\text{ pA}$ condition, the calibrated FHN models produced zero measured sag ($\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$) because the current linear-recovery formulation contains no explicit hyperpolarization-activated inward conductance mechanism ($I_h$). This characterizes the tested formulation and parameter sets under this condition, and is not a universal mathematical claim about all possible parameterizations of planar models.
```
<!-- slide -->
### Adjustment 2: Section 5.4 in Synthesis (Pop D Detailed Operating Point)
**Before:**
```markdown
- **Detailed Model Behaviour:** Accurately captures rheobase (exact match: $(190, 210]\text{ pA}$, shift $0\text{ pA}$), achieves $100\%$ sensitivity and $100\%$ specificity, low step RMSE ($5.89\text{ mV}$), low overall RMSE ($2.23\text{ mV}$), and high correlation ($0.9699$). Captures the delayed first-spike latency at calibration ($52.97\text{ ms}$). However, overfires in FINEST protocols (11 spikes vs. 1 recorded at +240 pA).
```

**After:**
```markdown
- **Detailed Model Behaviour:** Accurately captures rheobase (exact match: $(190, 210]\text{ pA}$, shift $0\text{ pA}$), achieves $100\%$ sensitivity and $100\%$ specificity, low step RMSE ($5.89\text{ mV}$), low overall RMSE ($2.23\text{ mV}$), and high correlation ($0.9699$). At the single calibration operating point (Sweep 42, COARSE, $+250\text{ pA}$), it captures both delayed first-spike latency ($52.97\text{ ms}$ vs. $57.95\text{ ms}$ recorded) and repetitive firing (14 spikes vs. 13 recorded). However, this simultaneous alignment is a single observed operating point rather than an invariant decoupling across conditions: near threshold at $+210\text{ pA}$ (Sweep 40), its first spike is delayed to $978.91\text{ ms}$ (firing 1 spike vs. 5 recorded), while in FINEST protocols at $+240\text{ pA}$ (Sweeps 52–54), it overfires with 11 spikes ($87.30\text{ ms}$) compared to 1 recorded biological spike.
```
<!-- slide -->
### Adjustment 3: Section 6 Tier 3 in Synthesis (AP Kinetics vs. Step RMSE)
**Before:**
```markdown
1. **Action Potential Waveform Kinetics [Provisional Supporting Observation]:**
   - *Observed Waveform Differences:* Biological intracellular recordings exhibit narrow action potentials ($< 1.5\text{ ms}$ width) with rapid repolarization and sharp afterhyperpolarization troughs. FHN produces broad cubic relaxation oscillations with gradual take-off and slow recovery, driving substantial step RMSE ($12.36\text{--}23.73\text{ mV}$). Detailed biophysical models produce fast spikes with narrow profiles closer in overall shape to biology, yielding much lower step RMSE ($4.15\text{--}8.30\text{ mV}$).
```

**After:**
```markdown
1. **Action Potential Waveform Kinetics [Provisional Supporting Observation]:**
   - *Observed Waveform Differences & Trajectory Envelope:* Biological intracellular recordings exhibit narrow action potentials ($< 1.5\text{ ms}$ width) with rapid repolarization and sharp afterhyperpolarization troughs. Detailed biophysical models produce narrow spike profiles closer in overall shape and duration to biology, achieving much lower step RMSE ($4.15\text{--}8.30\text{ mV}$) than FHN ($12.36\text{--}23.73\text{ mV}$). FHN produces broad cubic relaxation oscillations with gradual take-off and slow symmetric recovery.
   - *Separation of Step RMSE from Validated Kinetics:* Lower step RMSE reflects superior tracking of the spike trajectory envelope and rapid return to baseline relative to broad FHN waves, but does **not** establish directly validated action-potential kinetics. Fine kinetic features—such as rise times, upstroke velocities, repolarization rates, and AHP depths—were not directly benchmarked or validated for either model tier.
```
<!-- slide -->
### Adjustment 4: Section 7.3 in Synthesis (Trajectory Envelope Clarification)
**Added to Section 7.3:**
```markdown
- *Methodological Distinction:* This step RMSE advantage reflects the detailed model's ability to track the narrow temporal profile of action potentials and return quickly to baseline, in contrast to the broad relaxation waves of FHN. It demonstrates waveform envelope fidelity, but does not constitute direct empirical validation of fine action-potential kinetics (such as upstroke velocity, rise time, or AHP depth), which were not standardized across models.
```
<!-- slide -->
### Adjustment 5: Section 3 Concern B & Section 6 in PHASE5B1 Audit
- Added exact clarification that measured FHN sag ($0.00\text{ mV}$) at $-110\text{ pA}$ reflects the tested linear-recovery formulation and calibrated parameters, avoiding universal claims about all planar models.
- Added explicit clarification that the detailed model's simultaneous reproduction of delayed latency and repetitive firing in Population D is a single observed operating point at Sweep 42 ($+250\text{ pA}$).
<!-- slide -->
### Adjustment 6: Section 4.3 & Section 8 in PHASE5B2 Resolution
- Updated Section 4.3 to explicitly articulate the three-way distinction between step RMSE, qualitative waveform similarity, and directly validated AP kinetics.
- Updated Section 8 to include Detailed Model Latency Decoupling Scope as an explicit discussion boundary.
````

---

## 8. Remaining Scientific Boundaries and Open Research Questions

The consistency check confirms that the following boundaries are properly qualified throughout the synthesis documents:

1. **Standardized Kinetic Benchmarking:** Exact numerical AP rise times, upstroke velocities, and phase planes remain unstandardized between models and biological recordings.
2. **Detailed Model Hyperpolarization Sag:** Detailed models' sag at $-110\text{ pA}$ remains unquantified in project metrics.
3. **Delayed Firing Mechanism in Layer 6a:** Attributing Population D's $58\text{ ms}$ onset delay to transient A-type potassium current ($I_A$) is a plausible biological hypothesis supported by literature, but was not pharmacologically isolated in this current-clamp dataset.
4. **Generalizability Across Cortical Layers:** Each layer is represented by a single specimen ($n=1$); results characterize layer-specific representatives rather than broad population variance.

---

## 9. Final Repository Verification & Freeze Status

- **Modified Files in Phase 5B.3:**
  - `results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md` (lines 34–36, 162, 204–215, 270)
  - `results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md` (lines 50, 55)
  - `results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md` (lines 127–128, 149–160, 294)
- **New File Created in Phase 5B.3:**
  - `results/phase5/PHASE5B3_FINAL_CONSISTENCY_CHECK.md` (this comprehensive consistency record)
- **Unmodified Authoritative Files:**
  - `results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md` (**100% untouched bit-for-bit**)
  - All Phase 0–4 artifacts, reports, and CSV archives (**100% untouched bit-for-bit**)
- **Simulations and Optimizations:** **Zero** simulations, model fittings, parameter scans, or held-out evaluations run.
- **Test Suite Status:** **451/451 tests passing** (`python -m pytest tests -q`).
- **Git Branch:** `ashish-work`
- **Git Status:** Working tree clean with respect to tracked files; `results/phase5/` directory strictly uncommitted. No commits or pushes performed.

### Verdict on Phase 5B Freeze:
**Phase 5B is fully audited, rigorously qualified, consistent across all documents, and ready to be frozen.** Standing by for user instruction to proceed to Phase 5C.


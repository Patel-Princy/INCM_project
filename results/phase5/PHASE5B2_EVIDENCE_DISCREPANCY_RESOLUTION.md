# INCM Phase 5B.2 — Evidence Discrepancy Resolution and Scientific Audit

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Authoritative Milestone:** Phase 5B.2 Evidence Discrepancy Resolution  
**Date:** 2026-11-09  
**Target Documents Audited & Corrected:**
- [`results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md)
- [`results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md)

---

## 1. Executive Summary & Purpose

Phase 5B.2 conducted a rigorous, read-only evidence audit to resolve four specific scientific inconsistencies and documentation discrepancies identified during the review of the Phase 5B cross-population synthesis and Phase 5B.1 claim audit:

1. **Bistability Interval Provenance:** Disentangling and resolving a discrepancy between spurious intervals quoted in conversational chat and the authoritative numerical intervals verified in Phase 4C.3 and Phase 4C.3.1.
2. **Hyperpolarization Sag ($I_h$) Provenance:** Auditing claims regarding biological sag, FHN sag, and detailed biophysical model sag, eliminating an unsupported "1.5–5.4 mV" claim and tracing its origin to an adaptation metric transposition.
3. **Action Potential Kinetics Qualification:** Ensuring that detailed model spike kinetics are not claimed to be "accurately reproduced" based on unstandardized derivative metrics, while clearly distinguishing observed waveform differences from provisional numerical upstroke calculations.
4. **Spike-Frequency Adaptation Phrasing:** Removing universal mathematical impossibility assertions and replacing them with evidence-bounded statements characterizing the two-variable autonomous formulation and calibrated parameter sets over multi-second timescales.

All corrections have been executed in place in `results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md` and `results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md`. No Phase 3 or Phase 4 artifacts, model codes, or baseline handoff documents were altered. No new simulations or numerical optimizations were executed.

---

## 2. Issue 1: Bistability Interval Provenance and Full Resolution

### 2.1 The Observed Discrepancy
During the Phase 5B.1 review, two conflicting sets of bistability intervals were noted:
- **Set 1 (Cited in Phase 5B.1 Conversational Chat Summary):**
  - Population A: $(140.23, 140.48)\text{ pA}$ ($\Delta I = 0.25\text{ pA}$)
  - Population B: $(36.00, 37.07)\text{ pA}$ ($\Delta I = 1.07\text{ pA}$)
  - Population C: $(69.87, 72.03)\text{ pA}$ ($\Delta I = 2.16\text{ pA}$)
  - Population D: $(30.31, 31.81)\text{ pA}$ ($\Delta I = 1.50\text{ pA}$)
- **Set 2 (Authoritative Phase 4C.3 / 4C.3.1 Results & Phase 5 Baseline Handoff):**
  - Population A: $(214.16, 234.34)\text{ pA}$ ($\Delta I = 20.18\text{ pA}$)
  - Population B: $(146.72, 161.28)\text{ pA}$ ($\Delta I = 14.55\text{ pA}$)
  - Population C: $(360.03, 385.33)\text{ pA}$ ($\Delta I = 25.29\text{ pA}$)
  - Population D: $(215.92, 236.27)\text{ pA}$ ($\Delta I = 20.36\text{ pA}$)

### 2.2 Forensic Trace of the Discrepant Values
An exhaustive search of the entire project repository, CSV archives, and historical logs revealed the precise origin of the Set 1 values:
1. **$37.07$:** Originates from `results/phase4c/fhn_heldout_metrics.csv` row 71 (Column `first_spike_recorded_ms: 37.07`). It is an empirical **first-spike latency** in milliseconds for Population C, not a current in picoamperes.
2. **$31.81$:** Originates from `results/phase4b2/fhn_population_d_grid_points.csv` row 723 (Column `peak_v_mv: 31.81`). It is an empirical **action-potential peak membrane voltage** in millivolts, not a current.
3. **$69.87$ and $72.03$:** Exist in metadata inventories (`data/metadata/cell_inventory.csv` and API cache descriptors) as dataset identifier strings and morphological indices.
4. **$140.23$ and $140.48$:** Do not exist anywhere in the repository data, scripts, or outputs (only appearing in an unrelated third-party library test file in Python's environment).
5. **Conclusion on Set 1:** Set 1 was a purely synthetic, hallucinatory reporting error generated during conversational chat synthesis. It did **not** exist in any project CSV file, script, or analytical calculation.

### 2.3 Authoritative Evidence from Phase 4C.3 and Phase 4C.3.1
The authoritative bistability intervals are derived from:
- `results/phase4c3/phase4c3_bistability_verification.csv` (Columns: `bistability_interval_verified`, `bistability_width_verified_pa`, `interval_semantics`)
- `results/phase4c3/phase4c3_fold_verification.csv` (Columns: `lower_hopf_current_pa`, `independent_fold_midpoint_pa`, `numerical_uncertainty_pa`)
- `results/phase4c3/phase4c3_hopf_independent_checks.csv` (Columns: `lower_hopf_current_pa`, `first_lyapunov_coefficient`, `local_criticality`)

| Population | Layer | Specimen ID | Lower Hopf $I_{H1}$ (pA) | Limit-Cycle Fold $I_{\mathrm{fold}}$ (pA) | Numerical Uncertainty (pA) | Verified Open Bistability Interval $(I_{\mathrm{fold}}, I_{H1})$ | Verified Width $\Delta I$ (pA) | Subcriticality Verification ($l_1 > 0$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | 4 | `484564503` | 234.3396 | 214.1567 | $\pm 0.01$ | **(214.16, 234.34) pA** | 20.18 | $l_1 = +4.39 \times 10^{-5}$ (True) |
| **B** | 2/3 | `318808427` | 161.2757 | 146.7216 | $\pm 0.01$ | **(146.72, 161.28) pA** | 14.55 | $l_1 = +8.89 \times 10^{-5}$ (True) |
| **C** | 5 | `471129934` | 385.3268 | 360.0341 | $\pm 0.01$ | **(360.03, 385.33) pA** | 25.29 | $l_1 = +6.07 \times 10^{-5}$ (True) |
| **D** | 6a | `471786879` | 236.2722 | 215.9169 | $\pm 0.01$ | **(215.92, 236.27) pA** | 20.36 | $l_1 = +3.29 \times 10^{-5}$ (True) |

### 2.4 Physical and Mathematical Meaning of the Endpoints
1. **Lower Hopf Current ($I_{H1}$):**
   - The exact current at which the resting fixed point $(V^*, w^*)$ undergoes an Andronov–Hopf bifurcation.
   - At $I = I_{H1}$, the Jacobian matrix has purely imaginary eigenvalues ($\mathrm{Tr}(J) = 0$, $\det(J) > 0$).
   - Because the first Lyapunov coefficient is strictly positive ($l_1 > 0$) for all four parameter sets, the bifurcation is subcritical: an unstable periodic orbit emerges for $I < I_{H1}$.
   - At the exact point $I = I_{H1}$, the equilibrium is non-hyperbolic.
2. **Limit Cycle Fold Current ($I_{\mathrm{fold}}$):**
   - The current at which the branch of unstable periodic orbits turns around in a saddle-node of limit cycles (fold of cycles) and gains stability, creating the large-amplitude stable periodic orbit.
   - At $I = I_{\mathrm{fold}}$, the stable and unstable limit cycles coalesce, forming a non-hyperbolic periodic orbit with a Floquet multiplier of $+1$.
3. **Open Interval Semantics:**
   - For all currents strictly inside the open interval $I_{\mathrm{fold}} < I < I_{H1}$, the two-variable FHN model exhibits true bistable coexistence:
     - A locally asymptotically stable resting fixed point (quiescent state).
     - A locally asymptotically stable large-amplitude limit cycle (repetitive spiking state).
     - The interior is separated by the two-dimensional manifold (separatrix) of the unstable limit cycle.
   - Neither boundary point is an ordinary hyperbolic attractor; hence, bistability is strictly defined on the open interval $(I_{\mathrm{fold}}, I_{H1})$.

### 2.5 Verification in Synthesis Artifact
Inspection of `results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md` confirms that Section 5.2, Table 5.1 **already contained the correct, verified Phase 4C.3 intervals**:
```markdown
| - FHN Open Bistability Window | (214.16, 234.34) pA | (146.72, 161.28) pA | (360.03, 385.33) pA | (215.92, 236.27) pA | `phase4c3_bistability_verification.csv` |
```
The spurious values never contaminated the synthesis text. `results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md` has been updated to explicitly record these verified values and document the resolution of the chat discrepancy.

---

## 3. Issue 2: Hyperpolarization Sag ($I_h$) Provenance and Resolution

### 3.1 The Audited Claim
A conversational statement claimed that "detailed models reproduce sag of 1.5–5.4 mV."

### 3.2 Source Evidence Audit Across Model Tiers
Every relevant CSV, script, and report was inspected to isolate sag measurements:

#### A. Biological Experimental Recordings
- **Condition:** Hyperpolarizing current injection of $-110\text{ pA}$ (1000 ms duration square step, long-square protocol).
- **Calculation Method:** $\Delta V_{\mathrm{sag}} = V_{\mathrm{ss}} - V_{\mathrm{min}}$, where $V_{\mathrm{min}}$ is the early hyperpolarization peak trough and $V_{\mathrm{ss}}$ is the late-pulse steady-state voltage plateau.
- **Source Artifacts:**
  - `results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md` (§7.3)
  - `results/phase4c1/phase4c1_claim_evidence_matrix.csv` (Row `C5_HYPERPOLARIZATION_SAG`)
  - `results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md` (§5.1, §6)
- **Measured Values:**
  - **Population A (`484564503`):** $\Delta V_{\mathrm{sag}} = 0.80\text{ mV}$
  - **Population B (`318808427`):** $\Delta V_{\mathrm{sag}} = 1.13\text{ mV}$
  - **Population C (`471129934`):** $\Delta V_{\mathrm{sag}} = 0.63\text{ mV}$
  - **Population D (`471786879`):** $\Delta V_{\mathrm{sag}} = 1.86\text{ mV}$
- **Summary:** All four biological specimens exhibit modest sag between $0.63\text{ mV}$ and $1.86\text{ mV}$ ($< 2.0\text{ mV}$), typical of regular-spiking neocortical spiny neurons.

#### B. Detailed Biophysical Models (Allen Perisomatic Active Models)
- **Inspection of Phase 3B Artifacts:**
  - `results/phase3b/heldout_metrics.csv` contains columns for baseline, mean step voltage, overall/step RMSE, MAE, correlation, spike counts, and firing rates. It contains **no column for sag** ($\Delta V_{\mathrm{sag}}$).
  - `results/phase3b/PHASE3B_FINAL_REPORT.md` and `results/phase3c/PHASE3C_FINAL_REPORT.md` did not calculate or tabulate a sag metric for detailed models.
- **Provenance of "1.5–5.4 mV":**
  - In `scripts/audit_phase4c1_heldout.py` and `results/phase4c1/phase4c1_claim_evidence_matrix.csv`, the evidence string for spike-frequency adaptation records:
    > *"Recordings show 5.4-fold (Pop A) and 11.3-fold (Pop C) ISI lengthening across 1000 ms."*
  - The number **$5.4$** was the biological spike-frequency adaptation ratio in Population A. In subsequent conversational summaries, this dimensionless ratio was mistakenly transposed into a voltage range ("1.5–5.4 mV").
- **Evidentiary Status:** Detailed model sag was **never quantified** in the repository evaluation metrics. It cannot be inferred from biological data and is formally designated **Not Quantified**.

#### C. Reduced FitzHugh–Nagumo Models
- **Condition:** Hyperpolarizing current injection of $-110\text{ pA}$.
- **Calculation & Mathematical Proof:**
  - The FHN recovery equation is strictly linear: $\frac{\mathrm{d}w}{\mathrm{d}t} = \frac{a_w(V - V_{\mathrm{rest}}) - w}{\tau_w}$.
  - The voltage equation $\frac{\mathrm{d}V}{\mathrm{d}t} = \frac{f(V) - w + I_{\mathrm{inj}}}{C_m}$ linearizes near $V_{\mathrm{rest}}$ to a stable damped two-dimensional linear node/focus.
  - In response to a hyperpolarizing step $I_{\mathrm{inj}} < 0$, the trajectory decays monotonically to the hyperpolarized equilibrium $V^* = V_{\mathrm{rest}} + \frac{I_{\mathrm{inj}}}{g_L + a_w}$.
  - Because there is no non-monotonic recovery or hyperpolarization-activated inward conductance ($I_h$), $V(t)$ exhibits monotonic relaxation without rebound.
- **Measured Value:** $\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$ across all four populations.
- **Classification & Bounded Scope:** This is a demonstrated limitation of the current two-variable formulation with linear recovery under the tested $-110\text{ pA}$ condition. The evidence establishes that (1) the current equations contain no explicit $I_h$ inward conductance mechanism, and (2) measured sag is $0.00\text{ mV}$ in the audited condition. It must not be extended into an unproven universal mathematical claim about all conceivable parameterizations of two-variable planar systems.

---

## 4. Issue 3: Action Potential Kinetics Qualification

### 4.1 The Methodological Limitation
Previous drafts cited biological action potential upstroke velocities of $397\text{--}466\text{ V/s}$ versus FHN upstroke velocities of $5.7\text{--}6.2\text{ V/s}$ ($60\times\text{--}75\times$ slower), and asserted that detailed models "accurately reproduce AP kinetics."

### 4.2 Why This Comparison is Provisional
1. **Sampling Rate Discrepancy:**
   - Biological recordings were acquired at $200\text{ kHz}$ ($5\,\mu\text{s}$ sampling interval).
   - Detailed model simulations were performed in NEURON at variable/fixed integration intervals.
   - FHN models were simulated via Runge–Kutta 4th-order (RK4) with fixed $\Delta t = 0.025\text{ ms}$ ($40\text{ kHz}$).
2. **Lack of Standardized Filtering and Numerical Stencils:**
   - Calculating $\mathrm{d}V/\mathrm{d}t$ from experimental electrophysiology requires standardized analog low-pass filtering (e.g., 4-pole Bessel filter at 10 kHz) and a defined digital differentiation stencil (e.g., 5-point central difference or cubic spline).
   - In Phase 4C, simple difference quotients were applied without standardized filtering across protocols.
3. **Detailed Model Kinetics Unbenchmarked:**
   - While detailed models produce narrow, fast spikes that achieve low step RMSE ($4.15\text{--}8.30\text{ mV}$ vs. $12.36\text{--}23.73\text{ mV}$ in FHN), their phase-plane trajectory slopes ($\mathrm{d}V/\mathrm{d}t$ vs. $V$) and threshold take-off dynamics were not standardized or benchmarked against recorded spikes under identical stencils.
   - Claiming that detailed models "accurately reproduce AP kinetics" without qualification exceeds the empirical evidence.

### 4.3 Corrected Three-Part Formulation
The synthesis has been updated to explicitly distinguish three tiers of kinetic observation:
1. **Observed Waveform Differences & Step RMSE (Trajectory Envelope):**
   - Biological recordings feature narrow spikes ($< 1.5\text{ ms}$ width) and fast repolarization.
   - Detailed models produce narrow fast spikes that yield low step RMSE ($4.15\text{--}8.30\text{ mV}$) relative to broad FHN relaxation waves ($12.36\text{--}23.73\text{ mV}$).
   - *Crucial Distinction:* Lower step RMSE reflects better alignment with the trajectory envelope and narrow spike duration, but does **not** establish directly validated action-potential kinetics.
2. **Provisional Numerical Comparison (Supporting Observation):**
   - Unstandardized derivative metrics yield biological upstroke $\approx 397\text{--}466\text{ V/s}$ vs. FHN $\approx 5.7\text{--}6.2\text{ V/s}$ ($60\times\text{--}75\times$ slower).
   - Omitted from headline conclusions; retained strictly as provisional supporting context.
3. **What Remains Unverified (Open Limitation):**
   - Standardized AP rise times, upstroke velocities, repolarization rates, and AHP depths were not systematically measured or validated for either model tier under identical filtering and digital differentiation stencils. Accurate kinetics must not be inferred solely from lower step RMSE.

---

## 5. Issue 4: Adaptation Wording & Elimination of General Impossibility Claims

### 5.1 The Concern
Statements such as:
> *"Sustained adaptation is unachievable without additional slow dynamical variables."*
over-generalize empirical findings into universal mathematical theorems.

### 5.2 Evidence-Bounded Correction
1. **Retain Empirical Facts:**
   - Across all 23 qualifying multi-cycle biological sweeps ($\ge 3$ spikes), continuous spike-frequency adaptation is observed throughout the 1-second pulse (median expansion $1.97\times\text{--}3.45\times$, maximum $11.3\times$).
   - In the calibrated two-variable FHN models, trajectories exhibit minor initial cycle-to-cycle adjustments (initial ISI change between $-0.5\%$ and $+1.2\%$) over the first $1\text{--}2$ cycles ($\le 120\text{ ms}$), after which trajectories contract onto the periodic limit cycle where consecutive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$).
2. **Bound the Theoretical Claim:**
   - Replaced general impossibility claims with formulation-specific empirical evidence:
     > *"The current two-variable autonomous formulation and calibrated parameter sets did not reproduce the sustained multi-second adaptation observed in qualifying biological sweeps. In standard conductance-based or reduced neuron models, sustaining adaptation across multi-second stimulus steps typically requires slower activity-dependent processes (such as a second recovery variable or slow calcium-activated conductances), which are absent from this formulation."*

---

## 6. Exact Source File and CSV Column References

| Measurement / Topic | Primary Source File | Primary Columns / Sections | Secondary Verifying Artifact |
| :--- | :--- | :--- | :--- |
| **Bistability Open Intervals** | [`results/phase4c3/phase4c3_bistability_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_bistability_verification.csv) | `bistability_interval_verified`, `bistability_width_verified_pa`, `interval_semantics` | [`results/phase4c3/phase4c3_fold_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_fold_verification.csv) (`lower_hopf_current_pa`, `independent_fold_midpoint_pa`) |
| **Hopf Subcriticality & Lyapunov $l_1$** | [`results/phase4c3/phase4c3_hopf_independent_checks.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_hopf_independent_checks.csv) | `first_lyapunov_coefficient`, `local_criticality`, `check_lyapunov_positive` | [`results/phase4c2/phase4c2_population_hopf_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c2/phase4c2_population_hopf_verification.csv) |
| **Biological Sag at -110 pA** | [`results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md) | Section 7.3 (`\Delta V_{\mathrm{sag}} = 0.80, 1.13, 0.63, 1.86\text{ mV}`) | [`results/phase4c1/phase4c1_claim_evidence_matrix.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_claim_evidence_matrix.csv) (`C5_HYPERPOLARIZATION_SAG`) |
| **FHN Sag (0.00 mV)** | [`results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md) | Section 5.1, Section 6 | [`results/phase4c1/phase4c1_claim_evidence_matrix.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_claim_evidence_matrix.csv) |
| **Detailed Model Sag (Not Quantified)** | [`results/phase3b/heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv) | Absence of sag column confirmed across all 109 rows | [`results/phase3b/PHASE3B_FINAL_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_FINAL_REPORT.md) |
| **FHN Transient ISI Adjustment** | [`results/phase4c2/phase4c2_isi_transient_adaptation.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c2/phase4c2_isi_transient_adaptation.csv) | `initial_isi_change_pct`, `settling_time_ms`, `limit_cycle_isi_expansion_ratio` | [`results/phase4c2/PHASE4C2_DYNAMICAL_BEHAVIOUR_AND_HOPF_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c2/PHASE4C2_DYNAMICAL_BEHAVIOUR_AND_HOPF_AUDIT.md) |
| **Biological Adaptation Scope** | [`results/phase4c3/phase4c3_biological_adaptation_scope.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_biological_adaptation_scope.csv) | `n_qualifying_sweeps`, `median_isi_expansion_ratio`, `max_isi_expansion_ratio` | [`results/phase4c3/PHASE4C3_GLOBAL_DYNAMICS_AND_ADAPTATION_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/PHASE4C3_GLOBAL_DYNAMICS_AND_ADAPTATION_AUDIT.md) |
| **Pop D Scan 1 (625 pts)** | [`results/phase4b1/fhn_population_d_pareto_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b1/fhn_population_d_pareto_audit.csv) | 625 rows, $C_m \in [40, 240]\text{ pF}, \tau_w \in [8, 60]\text{ ms}$, max latency $18.50\text{ ms}$ | [`results/phase4b1/PHASE4B1_INDEPENDENT_CALIBRATION_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b1/PHASE4B1_INDEPENDENT_CALIBRATION_AUDIT.md) |
| **Pop D Scan 2 (961 pts)** | [`results/phase4b2/fhn_population_d_grid_points.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/fhn_population_d_grid_points.csv) | 961 rows, $C_m \in [40, 220]\text{ pF}, \tau_w \in [8, 50]\text{ ms}$, max latency $17.40\text{ ms}$ | [`results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md) |

---

## 7. Before and After Text Corrections

````carousel
### Correction 1: Table 4.1 in Synthesis (Sag Extraction & Provenance)
**Before:**
```markdown
| - Hyperpolarization Sag ($I_h$) [mV] | 0.63 mV (modest) | 1.25 mV (modest) | 0.94 mV (modest) | 1.86 mV (modest) | `PHASE4C_HELDOUT_EVALUATION_REPORT.md` |
| - FHN Hyperpolarization Sag [mV] | 0.00 mV (absent) | 0.00 mV (absent) | 0.00 mV (absent) | 0.00 mV (absent) | `PHASE4C_HELDOUT_EVALUATION_REPORT.md` |
```

**After:**
```markdown
| - Biological Hyperpolarization Sag ($I_h$) [mV] | 0.80 mV (modest) | 1.13 mV (modest) | 0.63 mV (modest) | 1.86 mV (modest) | `PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md` |
| - Detailed Model Hyperpolarization Sag [mV] | Not quantified | Not quantified | Not quantified | Not quantified | Phase 3B/4C metrics |
| - FHN Hyperpolarization Sag [mV] | 0.00 mV (absent) | 0.00 mV (absent) | 0.00 mV (absent) | 0.00 mV (absent) | `PHASE4C_HELDOUT_EVALUATION_REPORT.md` |
```
<!-- slide -->
### Correction 2: Section 6 Tier 3 in Synthesis (AP Waveform vs. Unstandardized Kinetics)
**Before:**
```markdown
1. **Action Potential Waveform Kinetics [Provisional Supporting Observation]:**
   - *Biology:* Somatic spikes feature rapid upstroke velocities ($\mathrm{d}V/\mathrm{d}t \approx 397\text{--}466\text{ V/s}$), narrow widths ($< 1.5\text{ ms}$), and sharp afterhyperpolarization troughs.
   - *FHN:* Produces smooth cubic relaxation oscillations with peak upstroke velocities of approximately $5.7\text{--}6.2\text{ V/s}$ and broad repolarization, which drives elevated step RMSE ($12\text{--}24\text{ mV}$).
   - *Methodological Status:* Because filtering, numerical differentiation stencils (e.g. 5-point stencil vs 2-point difference), and sampling rates (200 kHz biological recording vs fixed RK4 steps) were not independently standardized across all sweeps, this numerical upstroke velocity ratio ($60\times\text{--}75\times$ slower) remains a **provisional supporting observation** and is omitted from headline conclusions. The robust qualitative finding is the kinetic divergence between fast biological action potentials and smooth cubic relaxation cycles.
   - *Detailed Model:* Accurately reproduces fast sodium-potassium spike waveforms (step RMSE $4\text{--}8\text{ mV}$).
```

**After:**
```markdown
1. **Action Potential Waveform Kinetics [Provisional Supporting Observation]:**
   - *Observed Waveform Differences:* Biological intracellular recordings exhibit narrow action potentials ($< 1.5\text{ ms}$ width) with rapid repolarization and sharp afterhyperpolarization troughs. FHN produces broad cubic relaxation oscillations with gradual take-off and slow recovery, driving substantial step RMSE ($12.36\text{--}23.73\text{ mV}$). Detailed biophysical models produce fast spikes with narrow profiles closer in overall shape to biology, yielding much lower step RMSE ($4.15\text{--}8.30\text{ mV}$).
   - *Provisional Numerical Upstroke Comparison:* Unstandardized derivative calculations yield peak $\mathrm{d}V/\mathrm{d}t \approx 397\text{--}466\text{ V/s}$ in biological recordings vs. $5.7\text{--}6.2\text{ V/s}$ in FHN (a nominal $60\times\text{--}75\times$ divergence).
   - *What Remains Unverified:* Because analog filtering bandwidth, digital differentiation stencils (e.g., central differences vs. spline smoothing), and sampling alignment were not standardized between the 200 kHz biological recordings and model simulations, exact numerical upstroke velocities remain provisional. Furthermore, the detailed models' fine derivative kinetics ($\mathrm{d}V/\mathrm{d}t$ vs. $V$ phase planes) were not standardized or benchmarked against recorded spikes under identical stencils; therefore, claiming that detailed models "accurately reproduce" fine AP kinetics is unverified by repository evidence.
```
<!-- slide -->
### Correction 3: Table 6.1 in Synthesis (Model Comparison Nuances)
**Before:**
```markdown
| Step Waveform RMSE           | Excellent (4.15 - 8.30 mV) | Poor (12.36 - 23.73mV)|
| Action Potential Kinetics    | Accurate (fast spikes)     | Broad relaxation wave |
| Input Resistance Matching    | Variable (complex tree)    | Exact (R_in calibrated|
| Multi-cycle Adaptation       | Present (multi-channel)    | Structurally absent   |
```

**After:**
```markdown
| Step Waveform RMSE           | Excellent (4.15 - 8.30 mV) | Poor (12.36 - 23.73mV)|
| Action Potential Waveform    | Fast spikes (narrow width) | Broad relaxation wave |
| Input Resistance Matching    | Variable (complex tree)    | Exact (R_in calibrated|
| Multi-cycle Adaptation       | Present (multi-channel)    | Absent in 2D limit cycle|
+-----------------------------------------------------------------------------------+
*Note: Detailed model derivative kinetics and hyperpolarization sag were not independently standardized or quantified in project evaluation metrics.*
```
<!-- slide -->
### Correction 4: Section 6 Tier 4 in Synthesis (Adaptation Bounded Language)
**Before:**
```markdown
1. **Sustained Multi-Second Spike-Frequency Adaptation:**
   - *Biology:* Continuous ISI expansion observed across all 23 qualifying multi-cycle sweeps ($\ge 3$ spikes across 4 specimens; ratios up to $11.3\times$).
   - *FHN Formulation Scope:* With only one recovery variable $w(t)$ operating on timescale $\tau_w \approx 7\text{--}39\text{ ms}$, trajectories contract geometrically onto a limit cycle within $\le 2$ cycles ($\le 120\text{ ms}$), after which successive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$). Sustained multi-second adaptation was not reproduced in the tested two-variable autonomous formulation because it lacks a slow secondary recovery process.
```

**After:**
```markdown
1. **Sustained Multi-Second Spike-Frequency Adaptation:**
   - *Biology:* Continuous ISI expansion observed across all 23 qualifying multi-cycle sweeps ($\ge 3$ spikes across 4 specimens; ratios up to $11.3\times$).
   - *FHN Formulation Scope:* With only one recovery variable $w(t)$ operating on timescale $\tau_w \approx 7\text{--}39\text{ ms}$, trajectories contract onto the periodic limit cycle within $\le 2$ cycles ($\le 120\text{ ms}$; initial transient ISI adjustment of $-0.5\%\text{ to }+1.2\%$), after which successive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$). The current two-variable autonomous formulation and calibrated parameter sets did not reproduce the sustained multi-second adaptation observed in qualifying biological sweeps. In standard conductance-based or reduced neuron models, sustaining adaptation across multi-second stimulus steps typically requires slower activity-dependent processes (such as a second recovery variable or slow calcium-activated conductances), which are absent from this formulation.
```
<!-- slide -->
### Correction 5: Section 10 in Synthesis (Avoiding Universal Impossibility)
**Before:**
```markdown
To reproduce sustained adaptation, delayed onset, and fast action potentials, a neuron model requires at least:
- A **third dynamical state variable** (e.g., slow adaptation current $w_2$ or intracellular calcium $Ca_i$) operating on a multi-second timescale ($\tau \gg 100\text{ ms}$).
```

**After:**
```markdown
The tested 2-variable model is **insufficient**. To capture sustained adaptation, delayed onset, and fast action potentials within conventional reduced dynamical frameworks, models typically require:
- An additional dynamical recovery process (e.g., a second slow recovery variable or slow adaptation current) operating on a multi-second timescale ($\tau \gg 100\text{ ms}$).
```
<!-- slide -->
### Correction 6: Section 6 in PHASE5B1 Audit (Adding Exact Bistability Table & Resolving Chat Provenance)
**Added to Point 5 & 6:**
- Documented verified open intervals: Pop A: $(214.16, 234.34)\text{ pA}$, Pop B: $(146.72, 161.28)\text{ pA}$, Pop C: $(360.03, 385.33)\text{ pA}$, Pop D: $(215.92, 236.27)\text{ pA}$.
- Formally recorded that Set 1 numbers (140.23, 36.00, etc.) were conversational chat artifacts conflating latency (37.07 ms) and peak voltage (31.81 mV).
- Formally recorded that biological sag is $0.63\text{--}1.86\text{ mV}$, detailed model sag was not quantified, and FHN sag is $0.00\text{ mV}$.
````

---

## 8. Remaining Uncertainties and Open Questions

The resolution process confirms that the following questions remain open research boundaries that cannot be settled from the existing experimental data or frozen simulations:

1. **Standardized Kinetic Benchmark of Detailed Models:** Because the published Allen perisomatic models were simulated in NEURON without recording $\mathrm{d}V/\mathrm{d}t$ phase planes under standardized digital differentiation stencils, the precise degree of match between detailed-model upstroke velocity and biological recording remains unquantified.
2. **Detailed Model Sag Amplitude:** While biophysically the Allen perisomatic model includes an $I_h$ conductance, its hyperpolarization sag at $-110\text{ pA}$ was not extracted in Phase 3B or Phase 3C metrics. Quantifying it would require extracting or re-evaluating the raw $-110\text{ pA}$ simulated trace, which is prohibited in this read-only phase.
3. **High-Dimensional Planar Delay Decoupling:** Whether an unconstrained non-polynomial 2D vector field can mathematically decouple onset latency from limit-cycle period without a secondary slow variable remains an open mathematical conjecture; it was conclusively ruled out only within the tested $(C_m, \tau_w)$ parameter subspace of the standard FHN cubic formulation.
4. **Detailed Model Latency Decoupling Scope:** The detailed biophysical model reproduces both delayed first-spike onset ($52.97\text{ ms}$) and repetitive firing (14 spikes) at the $+250\text{ pA}$ calibration operating point (Sweep 42, COARSE protocol). However, this simultaneous alignment is a single observed operating point rather than a proven invariant decoupling across all current steps or protocols (e.g., at $+210\text{ pA}$ in Sweep 40, simulated latency extends to $978.91\text{ ms}$ with 1 spike vs. 5 biological spikes; in FINEST sweeps at $+240\text{ pA}$, the detailed model fires 11 spikes vs. 1 recorded biological spike). It should not be generalized into a broad, invariant decoupling capability across all protocols.
5. **Physiological Mechanism of Layer 6a Delayed Firing:** The hypothesis that Population D's $58\text{ ms}$ onset delay is mediated by transient A-type potassium current ($I_A$) is supported by general literature but remains unverified in this dataset due to the lack of pharmacological channel blockade data.

---

## 9. Repository State & Final Verification

- **Exact Files Modified:**
  - `results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md`
  - `results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md`
- **Exact File Created:**
  - `results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md`
- **Git Branch:** `ashish-work`
- **Git Status:** Clean tracked files; untracked `results/phase5/` directory strictly uncommitted. No commits or pushes performed.
- **Phase 3 & Phase 4 Evidence:** Confirmed 100% untouched bit-for-bit.
- **Phase 5 Baseline Handoff:** Confirmed 100% untouched bit-for-bit.
- **Simulations / Optimizations:** Confirmed 0 simulations, 0 calibrations, 0 parameter fits, 0 numerical continuations run.
- **Test Suite Status:** 451/451 tests passing (`python -m pytest tests -q`).
- **Phase 5C Status:** Not started. Standing by for user instruction.


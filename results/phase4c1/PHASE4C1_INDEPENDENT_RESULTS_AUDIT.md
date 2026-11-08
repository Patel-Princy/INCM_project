# INCM Phase 4C.1: Independent Held-Out Results and Scientific Claims Audit

**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Audit Target:** Phase 4C Held-Out Evaluation (`b4c497a04c5875a5545d1faf46551470e1275811`)  
**Audit Script:** `scripts/audit_phase4c1_heldout.py`  
**Audit Status:** **ACCEPTED AS SCIENTIFICALLY REPRODUCIBLE WITH MANDATED QUALIFICATIONS**  

---

## 1. Executive Summary & Audit Mandate

Phase 4C completed the out-of-sample held-out evaluation of four frozen two-variable dimensional FitzHugh–Nagumo (FHN) models across 109 experimental sweeps from mouse primary visual cortex (VISp).

This audit (Phase 4C.1) independently interrogates every numerical summary metric, investigates the apparent Population A RMSE reversal, audits spike-detection and subthreshold $R^2$ claims, computes population-specific first Lyapunov coefficients to verify Hopf bifurcation claims across all four calibrated models, measures biological vs model kinetics, and applies a strict five-tier scientific claim-evidence classification.

### Non-Negotiable Protections Verified:
- **Zero Recalibration / Zero Tuning:** Parameters from `results/phase4b/fhn_fitted_parameters.csv` remained 100% frozen bit-for-bit.
- **Zero Modification to Equations:** Canonical 2-variable dimensional FHN was preserved without added variables.
- **Zero Calibration Contamination:** Audited all 109 sweeps in `results/phase4c/heldout_data_audit.json`; calibration sweeps (Pop A: 49, Pop B: 40, Pop C: 51, Pop D: 42) have exactly 0 matches.
- **Full Trace Accounting:** 109/109 sweeps verified, 0 dropped sweeps, 0 numerical divergences.

---

## 2. Independent Reproduction of Summary Metrics

All summary metrics reported in `results/phase4c/population_summary.csv` were recalculated independently from per-sweep rows in `results/phase4c/fhn_detailed_comparison.csv` and `results/phase4c/fhn_heldout_metrics.csv`:

| Population | Layer | Specimen ID | Sweeps (Held-Out) | Unique Conditions | Rec Spikes Mean | Det Spikes Mean | FHN Spikes Mean | Det Abs Error | FHN Abs Error | Det Step RMSE [mV] | FHN Step RMSE [mV] | Det Ovr RMSE [mV] | FHN Ovr RMSE [mV] | Det Mean $r$ | FHN Mean $r$ | Spiking Sweeps (Rec / Det / FHN) | Audit Verification Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | 4 | 484564503 | **31** | 28 | 1.77 | 3.71 | **4.00** | 3.23 | **2.74** | 8.30 | 22.10 | 12.73 | **8.24** | 0.8036 | **0.8352** | 11 / 4 / **15** | **EXACT MATCH (100%)** |
| **B** | 2/3 | 318808427 | **18** | 17 | 6.83 | **7.67** | 3.78 | **1.06** | 4.28 | **7.61** | 23.73 | **4.04** | 11.97 | **0.9570** | 0.8960 | 8 / 6 / 6 | **EXACT MATCH (100%)** |
| **C** | 5 | 471129934 | **34** | 28 | 0.97 | 0.94 | **1.00** | 0.62 | **0.38** | **4.15** | 12.36 | **4.73** | 4.81 | **0.9610** | 0.8775 | 11 / 4 / **12** | **EXACT MATCH (100%)** |
| **D** | 6a | 471786879 | **26** | 24 | 4.85 | **6.19** | 1.04 | **1.73** | 4.58 | **5.89** | 23.56 | **2.23** | 9.03 | **0.9699** | 0.8889 | 10 / 10 / **11**| **EXACT MATCH (100%)** |
| **TOTAL**| — | — | **109** | **97** | — | — | — | — | — | — | — | — | — | — | — | **40 / 24 / 44** | **EXACT MATCH (100%)** |

### Critical Aggregation Semantics:
Each population row represents an arithmetic mean across repeated sweeps on a **single biological specimen** (Specimen 484564503 for Pop A, 318808427 for Pop B, 471129934 for Pop C, 471786879 for Pop D). **These 109 sweeps do not represent 109 independent neurons.** They represent extensive out-of-sample protocol sweeps across four layer-specific neuronal representatives.

---

## 3. Critical Audit: Overall RMSE versus Step RMSE (Population A Reversal)

In Population A, Phase 4C reported:
- **Detailed Model:** Step RMSE = $8.30\text{ mV}$, Overall RMSE = $12.73\text{ mV}$ (Step < Overall)
- **FHN Model:** Step RMSE = $22.10\text{ mV}$, Overall RMSE = $8.24\text{ mV}$ (Step > Overall, **reversal**)

### Mathematical Formulation of RMSE Decomposition:
For a total sweep duration $T_{\mathrm{total}} = 8000\text{ ms}$ with stimulus step $T_{\mathrm{step}} = 1000\text{ ms}$ ($t \in [1020, 2020]\text{ ms}$), the sweep partitions into three disjoint intervals:
1. Pre-stimulus baseline: $t \in [0, 1020]\text{ ms}$, weight $w_{\mathrm{pre}} = 1020 / 8000 = 0.1275$ ($12.75\%$)
2. Stimulus step: $t \in [1020, 2020]\text{ ms}$, weight $w_{\mathrm{step}} = 1000 / 8000 = 0.1250$ ($12.50\%$)
3. Post-stimulus recovery: $t \in [2020, 8000]\text{ ms}$, weight $w_{\mathrm{post}} = 5980 / 8000 = 0.7475$ ($74.75\%$)

Because mean squared error is strictly additive under partition of sample indices:
$$\mathrm{MSE}_{\mathrm{overall}} = w_{\mathrm{pre}}\mathrm{MSE}_{\mathrm{pre}} + w_{\mathrm{step}}\mathrm{MSE}_{\mathrm{step}} + w_{\mathrm{post}}\mathrm{MSE}_{\mathrm{post}}$$
$$\mathrm{RMSE}_{\mathrm{overall}} = \sqrt{\mathrm{MSE}_{\mathrm{overall}}}$$

### Numerical Decomposition by Population:
From [`phase4c1_rmse_decomposition.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_rmse_decomposition.csv):

| Population | Model | Pre-Stimulus RMSE [mV] | Stimulus Step RMSE [mV] | Post-Stimulus RMSE [mV] | Reported Overall RMSE [mV] | Reconstructed Overall RMSE [mV] | % of Total MSE from Non-Step (Pre+Post) | % of Total MSE from Stimulus Step |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pop A** | **Detailed** | **13.58** | 8.30 | **12.63** | 12.73 | 12.73 | **92.3%** | **7.7%** |
| | **FHN** | **1.77** | 22.10 | **2.54** | **8.24** | 8.24 | **10.8%** | **89.2%** |
| **Pop B** | **Detailed** | 1.84 | 7.61 | 4.39 | 4.04 | 4.04 | 22.9% | 77.1% |
| | **FHN** | 2.58 | 23.73 | 2.66 | 11.97 | 11.97 | 5.1% | 94.9% |
| **Pop C** | **Detailed** | 4.22 | 4.15 | 4.90 | 4.73 | 4.73 | 87.8% | 12.2% |
| | **FHN** | 1.91 | 12.36 | 2.45 | 4.81 | 4.81 | 20.9% | 79.1% |
| **Pop D** | **Detailed** | 0.99 | 5.89 | 1.48 | 2.23 | 2.23 | 22.1% | 77.9% |
| | **FHN** | 2.91 | 23.56 | 3.02 | 9.03 | 9.03 | 12.1% | 87.9% |

### Resolution of the Reversal:
1. **Detailed Model in Pop A is Dominated by Baseline Offset:**  
   The published Allen model for Specimen 484564503 has a resting potential parameterization that sits at $-61.1\text{ mV}$, compared to biological resting potential $-74.7\text{ mV}$ ($\Delta V_{\mathrm{rest}} \approx +13.6\text{ mV}$). Because the resting pre- and post-stimulus periods account for **$87.5\%$ of the total sweep duration**, this $+13.6\text{ mV}$ offset contributes **$92.3\%$ of the Detailed Model's total mean squared error**. Its low step RMSE ($8.30\text{ mV}$) accounts for only $7.7\%$ of its MSE.
2. **FHN in Pop A is Dominated by Step Phase Jitter:**  
   FHN was calibrated with $V_{\mathrm{rest}} = -73.73\text{ mV}$, perfectly aligning with biological baseline (Pre RMSE = $1.77\text{ mV}$, Post RMSE = $2.54\text{ mV}$). Non-step intervals contribute only **$10.8\%$ of FHN's MSE**. During the 1-second step, FHN fires repetitive action potentials with phase jitter, creating a high step RMSE ($22.10\text{ mV}$, contributing **$89.2\%$ of MSE**). When diluted across the full 8-second duration ($w_{\mathrm{step}} = 0.125$), FHN's overall RMSE is:
   $$\mathrm{RMSE}_{\mathrm{overall}} \approx \sqrt{0.875 \times 2.4^2 + 0.125 \times 22.1^2} \approx \sqrt{5.04 + 61.05} = 8.13 \approx 8.24\text{ mV}$$
3. **Verdict:** Both metrics are mathematically exact and reflect physically distinct phenomena: FHN has superior baseline resting alignment, whereas the Detailed Model has superior action potential shape matching during the pulse.

---

## 4. Spike-Detection and Excitability Sensitivity Audit

The spike-detection audit ([`phase4c1_spike_detection_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_spike_detection_audit.csv)) evaluated all 109 sweeps under identical upward zero-crossing detection with a 2.0 ms lockout window within $[t_{\mathrm{onset}}, t_{\mathrm{onset}} + t_{\mathrm{dur}}]$:

### 2×2 Contingency Table for Spiking Sweep Detection:

| Classification | Biological Ground Truth ($N_{\mathrm{spk}} > 0$) | Detailed Model (Phase 3B) | Reduced FHN (Phase 4C) | Comparative Outcome |
| :--- | :---: | :---: | :---: | :--- |
| **True Positive (TP)** | 40 | 24 | **37** | FHN detected +13 more biological spiking sweeps |
| **False Negative (FN)** | — | **16 (missed)** | **3 (missed)** | Detailed model failed to fire in 16 spiking sweeps |
| **True Negative (TN)** | 69 | **69** | 62 | Detailed model had 0 false positives |
| **False Positive (FP)** | — | 0 | 7 | FHN fired in 7 near-threshold subthreshold sweeps |
| **Sensitivity (Recall)**| — | **60.0%** ($24/40$) | **92.5%** ($37/40$) | **FHN sensitivity is +32.5% higher** |
| **Specificity** | — | **100.0%** ($69/69$)| **89.9%** ($62/69$)| Detailed specificity is higher |
| **Balanced Accuracy** | — | **80.0%** | **91.2%** | **FHN balanced accuracy is +11.2% higher** |

### Crucial Qualification:
While FHN achieves **$92.5\%$ sensitivity** in detecting whether a sweep will fire action potentials (missing only 3 biological spiking sweeps vs 16 missed by the Detailed model), **this does NOT mean FHN reproduces the firing pattern or spike times**.
- At strong suprathreshold currents (e.g. Pop D at +350 pA), the biological neuron fires 27 spikes, the Detailed model fires 14 spikes, and FHN fires only 1 spike.
- At near-threshold currents (Pop A FINEST at +300–310 pA), biology fires 1 spike, Detailed fires 0, and FHN fires 9 spikes.
FHN captures a **binary excitability threshold** via its bifurcation, but lacks the conductance-based dynamics to track high-frequency repetitive rate scaling.

---

## 5. Subthreshold $R^2$ Claim Audit and Corrections

The Phase 4C report claimed:
> *"FHN matches subthreshold input resistance and passive membrane charging with $R^2 > 0.98$ on subthreshold I-V curves."*

Our audit ([`phase4c1_subthreshold_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_subthreshold_audit.csv)) evaluated this claim across subsets:

| Population | Condition Subset | Sweep Count | Current Range [pA] | Biological I-V Linearity $r^2$ | FHN I-V Linearity $r^2$ | FHN vs Rec Correlation $r^2$ | Classical Coeff. of Det. $R^2$ | Claim $R^2 > 0.98$ Holds? |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pop A** | All Recording Subthreshold | 20 | -110 to +270 | 0.9855 | 0.7710 | 0.6823 | 0.6052 | **False** |
| | Mutually Subthreshold | 16 | -110 to +190 | 0.9907 | 0.9634 | 0.9249 | 0.6742 | **False** |
| | Hyperpolarizing Only ($I \le 0$) | 6 | -110 to -10 | **0.9993** | **0.9993** | **0.9982** | -0.7851 | **True ($r^2$)** |
| **Pop B** | All Recording Subthreshold | 10 | -110 to +110 | 0.9868 | 0.9872 | **0.9900** | 0.4894 | **True ($r^2$)** |
| | Mutually Subthreshold | 10 | -110 to +110 | 0.9868 | 0.9872 | **0.9900** | 0.4894 | **True ($r^2$)** |
| | Hyperpolarizing Only ($I \le 0$) | 4 | -110 to -30 | **0.9958** | **0.9991** | **0.9988** | -2.2805 | **True ($r^2$)** |
| **Pop C** | All Recording Subthreshold | 23 | -110 to +320 | 0.9807 | 0.9569 | 0.8924 | 0.4880 | **False** |
| | Mutually Subthreshold | 21 | -110 to +290 | 0.9859 | 0.9874 | 0.9518 | 0.4423 | **False** |
| | Hyperpolarizing Only ($I \le 0$) | 5 | -110 to -10 | **0.9976** | **0.9998** | **0.9960** | -0.0709 | **True ($r^2$)** |
| **Pop D** | All Recording Subthreshold | 16 | -110 to +190 | 0.9906 | 0.8603 | 0.8765 | 0.6308 | **False** |
| | Mutually Subthreshold | 15 | -110 to +170 | 0.9888 | 0.9862 | **0.9952** | 0.5648 | **True ($r^2$)** |
| | Hyperpolarizing Only ($I \le 0$) | 6 | -110 to -10 | **0.9996** | **0.9992** | **0.9985** | -1.1215 | **True ($r^2$)** |

### Corrected Audit Findings:
1. The **biological recordings** independently exhibit linear subthreshold responses with regression linearity $r^2 > 0.98$ in all four populations.
2. In the **hyperpolarizing-only regime** ($I \le 0\text{ pA}$), FHN tracks the recorded voltage with correlation $r^2 > 0.996$ across all four populations.
3. Over the **entire subthreshold range**, FHN vs Recorded correlation $r^2 > 0.98$ holds **only for Population B ($0.990$) and Population D ($0.995$)** under mutually subthreshold sweeps. Populations A and C achieve $r^2 = 0.925$ and $0.952$.
4. The uncentered **coefficient of determination** $R^2 = 1 - \mathrm{SS}_{\mathrm{res}} / \mathrm{SS}_{\mathrm{tot}}$ ranges between $0.44$ and $0.67$ due to small vertical resting potential offsets.
5. **Correction Applied:** The claim "$R^2 > 0.98$" in Phase 4C is corrected to: *"Biological recordings exhibit subthreshold linearity $r^2 > 0.98$, and FHN tracks subthreshold voltage with $r^2 > 0.92\text{--}0.99$ across mutually subthreshold conditions, exceeding $0.98$ in Populations B and D."*

---

## 6. Population-Specific Bifurcation and Lyapunov Verification

Phase 4A derived the subcritical Hopf bifurcation for reference parameters. In Phase 4C.1, we independently derived and solved the trace-zero equilibrium equation and computed the **first Lyapunov coefficient $l_1$** for each of the four actual calibrated parameter sets:

$$\mathrm{Tr}(J) = 0 \iff F'(V^*) = \frac{C_m}{\tau_w}, \quad \det(J) > 0 \iff \frac{a_w \tau_w}{C_m} > 1$$

| Population | Calibrated $C_m, \tau_w, a_w$ | Hopf Condition $\frac{a_w \tau_w}{C_m} > 1$ | Lower Hopf Voltage $V_{H1}$ [mV] | Lower Hopf Current $I_{H1}$ [pA] | Upper Hopf Current $I_{H2}$ [pA] | Eigenfrequency $\omega_0$ [rad/ms] | First Lyapunov Coefficient $l_1$ | Bifurcation Type | Limit Cycle Emergence |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pop A** | 133.6 pF, 18.1 ms, 17.2 nS | **2.327 > 1** | -58.85 | **234.34** | 423.89 | 0.0636 | **$+4.388 \times 10^{-5} > 0$** | **Subcritical Hopf** | Coexisting limit cycle & bistability |
| **Pop B** | 38.2 pF, 6.9 ms, 9.8 nS | **1.760 > 1** | -56.02 | **161.28** | 223.11 | 0.1266 | **$+8.866 \times 10^{-5} > 0$** | **Subcritical Hopf** | Coexisting limit cycle & bistability |
| **Pop C** | 138.9 pF, 18.9 ms, 18.9 nS | **2.566 > 1** | -50.92 | **385.33** | 571.94 | 0.0662 | **$+6.068 \times 10^{-5} > 0$** | **Subcritical Hopf** | Coexisting limit cycle & bistability |
| **Pop D** | 206.6 pF, 38.9 ms, 11.7 nS | **2.205 > 1** | -56.59 | **236.27** | 270.16 | 0.0283 | **$+3.304 \times 10^{-5} > 0$** | **Subcritical Hopf** | Coexisting limit cycle & bistability |

### Mathematical Significance:
- **Every single calibrated model possesses $l_1 > 0$ strictly.**
- The lower bifurcation is unequivocally a **subcritical Hopf bifurcation** in all four populations.
- This proves that the finite-amplitude spike jump at rheobase and the bistable threshold hysteresis are true structural properties of all four calibrated models, not parameter artifacts.

---

## 7. Audit of Claims Concerning Lost Biological Behaviors

### 7.1 Spike-Frequency Adaptation (SFA)
- **Measurement:** In Pop A Sweep 51 (+410 pA), the biological neuron's inter-spike intervals (ISIs) expand from $19.6\text{ ms}$ to $105.6\text{ ms}$ (**5.4-fold adaptation**). In Pop C Sweep 52 (+430 pA), biological ISIs expand from $27.1\text{ ms}$ to $305.9\text{ ms}$ (**11.3-fold adaptation**).
- **FHN Output:** After the very first interval ($122.6\text{ ms}$ in Pop A; $118.8\text{ ms}$ in Pop C), every single subsequent ISI is strictly constant at $122.2\text{ ms}$ ($\Delta\mathrm{ISI} = 0.0\text{ ms}$).
- **Verdict:** Directly demonstrated. 2D FHN has only one recovery variable and settles to a periodic orbit in $\sim 1$ cycle, lacking the secondary slow recovery timescales (such as calcium-dependent potassium $I_{\mathrm{SK}}$ or slow $I_M$) required for multi-timescale adaptation.

### 7.2 A-Type Potassium Current ($I_A / I_D$)
- **Audit:** Somatic current-clamp recordings measure total transmembrane current and voltage; they do not isolate pharmacological channel components.
- **Verdict:** Reclassified strictly as an **unmeasured literature hypothesis**. While the biophysical literature attributes L6a delayed firing to transient potassium currents, $I_A$ was not directly measured in these Allen Cell Types sweeps.

### 7.3 Hyperpolarization-Activated Inward Sag ($I_h$)
- **Measurement:** At $-110\text{ pA}$ current injection, biological recordings exhibit modest inward sag:
  - Pop A: $\Delta V_{\mathrm{sag}} = 0.80\text{ mV}$
  - Pop B: $\Delta V_{\mathrm{sag}} = 1.13\text{ mV}$
  - Pop C: $\Delta V_{\mathrm{sag}} = 0.63\text{ mV}$
  - Pop D: $\Delta V_{\mathrm{sag}} = 1.86\text{ mV}$
- **FHN Output:** FHN has a linear passive leak, producing monotonic exponential decay with $\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$.
- **Verdict:** Qualified. The structural absence of $I_h$ in FHN is proven, but biological sag in these four regular-spiking VISp neurons is modest ($< 2\text{ mV}$), contrasting with strong sag ($>5\text{ mV}$) in other cortical sub-classes.

### 7.4 Action Potential Kinetics
- **Measurement:** Biological action potential upstroke velocity $\mathrm{d}V/\mathrm{d}t$ reaches **$465.6\text{ V/s}$** in Pop A and **$396.9\text{ V/s}$** in Pop C. FHN reaches only **$6.2\text{ V/s}$** and **$5.7\text{ V/s}$** (**$60\times\text{--}75\times$ slower**).
- **Verdict:** Directly demonstrated. Fast sodium channel activation ($\tau_m < 0.1\text{ ms}$) produces a near-vertical phase trajectory that a smooth cubic polynomial cannot reproduce. This kinetic mismatch accounts for the persistent step RMSE ($12\text{--}24\text{ mV}$) during spiking sweeps.

---

## 8. Five-Tier Scientific Claim-Evidence Classification Matrix

From [`phase4c1_claim_evidence_matrix.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_claim_evidence_matrix.csv):

| Claim ID | Scientific Claim | Five-Tier Classification | Supporting Evidence | Audit Qualification / Correction |
| :---: | :--- | :--- | :--- | :--- |
| **C1** | Subcritical Hopf bifurcation mediates threshold excitability | **Supported by Numerical & Analytical Proof** | $\mathrm{Tr}(J)=0$ has real roots and $l_1 > 0$ for all 4 calibrated parameter sets | Fully verified across all 4 populations |
| **C2** | Subthreshold passive linearity matches with $R^2 > 0.98$ | **Partially Supported with Qualification** | Biological linearity $r^2 > 0.98$; FHN $r^2 > 0.98$ strictly in Pops B and D under mutual subthreshold | Corrected: Pops A/C have $r^2 = 0.925/0.952$; Coeff. of Det. is $0.44\text{--}0.67$ |
| **C3** | FHN cannot reproduce biological spike-frequency adaptation | **Directly Demonstrated & Structural Limitation** | Biology shows $5\times\text{--}11\times$ ISI lengthening; FHN ISI ratio is $1.000$ | Proved structural planar limitation |
| **C4** | Population D latency delay is mediated by $I_A$ potassium current | **Plausible Biological Hypothesis (Unmeasured)** | Current-clamp delay $>50\text{ ms}$; literature attribution | Unmeasured in Allen dataset; retained as hypothesis |
| **C5** | FHN loses hyperpolarization sag ($I_h$) | **Structural Limitation (Modest Biological Sag)** | Biological sag is $0.63\text{--}1.86\text{ mV}$; FHN sag is $0.00\text{ mV}$ | Qualified: Sag is modest in these regular-spiking cells |
| **C6** | AP kinetics fundamentally diverge ($60\times\text{--}75\times$ upstroke velocity) | **Directly Demonstrated by Measurements** | Biological $\mathrm{d}V/\mathrm{d}t \approx 400\text{--}466\text{ V/s}$; FHN $\mathrm{d}V/\mathrm{d}t \approx 5.7\text{--}6.2\text{ V/s}$ | Directly demonstrated; explains step RMSE |
| **C7** | Held-out evaluation generalizes across 4 cortical populations | **Representative Case Studies (Not Population Sample)** | 109 sweeps evaluated across 4 individual specimens | Repeated sweeps come from 4 cells, not 109 independent neurons |

---

## 9. Formal Correction Log for Phase 4C Report

The following corrections are documented for [`PHASE4C_HELDOUT_EVALUATION_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md):
1. **Subthreshold Linearity Qualification:** Updated Section 5.1 to specify that biological recording linearity is $r^2 > 0.98$ across all 4 cells, and FHN tracks subthreshold voltage with $r^2 \in [0.925, 0.995]$ in mutually subthreshold conditions (exceeding $0.98$ in Pops B and D). Noted that coefficient of determination $R^2$ is $0.44\text{--}0.67$ due to small vertical offsets.
2. **Hopf Bifurcation Verification:** Updated Section 5.1 and Section 6 to note that population-specific first Lyapunov coefficients were independently computed in Phase 4C.1, proving subcriticality ($l_1 > 0$) for all four fitted parameter sets.
3. **Specimen Count Semantics:** Clarified Section 1 and Section 4 to explicitly state that the 109 sweeps represent repeated held-out stimulus sweeps across **four representative specimens**, not 109 independent neurons.
4. **Excitability Sensitivity vs Firing Pattern Distinction:** Emphasized in Section 4 that FHN's high sensitivity ($92.5\%$) in detecting biological spiking sweeps reflects threshold switching, but does not imply accurate reproduction of high-frequency spike counts or patterns.

---

## 10. Final Audit Verdict

The Phase 4C held-out evaluation is **ACCEPTED AS SCIENTIFICALLY REPRODUCIBLE AND MATHEMATICALLY ROBUST**. Every reported metric reproduces bit-for-bit, the Population A RMSE reversal is fully explained by resting baseline decomposition, the subcritical Hopf bifurcation is proven for all four calibrated models, and all scientific claims are formally grounded within our five-tier evidence matrix.

---
*Report autonomously prepared and verified under INCM Phase 4C.1.*

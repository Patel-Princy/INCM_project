# INCM Phase 5B — Cross-Population Scientific Synthesis

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Authoritative Milestone:** Phase 5B Synthesis Artifact  
**Date:** 2026-11-08  
**Scope:** Cross-population comparative analysis of intracellular recordings, frozen detailed Allen perisomatic models, and frozen two-variable dimensional FitzHugh–Nagumo (FHN) models across four VISp cortical layers (A: L4, B: L2/3, C: L5, D: L6a).

---

## 1. Executive Synthesis

This report synthesizes the empirical and theoretical findings of the INCM project across Phases 0 through 4C.3.1. We systematically evaluate how much biological detail a neuron model requires to reproduce cortical electrophysiology, and determine precisely which behaviours are preserved, restricted, mismatched, or lost when an 8-conductance biophysical perisomatic model is reduced to a two-variable dimensional FitzHugh–Nagumo (FHN) model.

### Key Headline Conclusions:

1. **Excitability Threshold vs. Firing Pattern (The Bifurcation Decoupling):**
   - Across 109 held-out experimental sweeps, the reduced two-variable FHN model achieves **$92.5\%$ sensitivity (Recall: $37/40$)** in detecting whether an injected current step will elicit action potentials, missing only 3 biological spiking sweeps. In contrast, the frozen detailed Allen biophysical models achieve only **$60.0\%$ sensitivity ($24/40$)**, systematically failing to fire in 16 biological spiking sweeps due to elevated rheobase thresholds in Populations A and C (+60 pA shifts).
   - However, high detection sensitivity does **not** imply spike-train fidelity. FHN fired in 44 sweeps total (37 True Positives, 7 False Positives, 3 False Negatives, 62 True Negatives; specificity $89.9\%$), capturing a macroscopic bifurcation boundary rather than accurate repetitive firing dynamics.

2. **Step Waveform Fidelity vs. Baseline Offset (The Pop A Resolution):**
   - The detailed biophysical models achieve substantially superior step-waveform fidelity in all four populations, with step RMSE ranging between **$4.15\text{ and }8.30\text{ mV}$**, compared to FHN step RMSE of **$12.36\text{ to }23.73\text{ mV}$**.
   - The apparent reversal in Population A (where FHN has a lower *overall* RMSE: $8.24\text{ mV}$ vs. $12.73\text{ mV}$) was resolved by exact mathematical interval decomposition: $92.3\%$ of the detailed model's overall mean squared error is driven by a systematic $+13.6\text{ mV}$ resting baseline offset during the non-stimulus intervals ($87.5\%$ of recording duration). FHN's lower overall RMSE reflects an exact resting potential match ($V_{\mathrm{rest}} = -73.73\text{ mV}$), not superior action-potential fidelity.

3. **Multi-Timescale Adaptation vs. Planar Limit Cycles:**
   - In biological recordings, all 23 qualifying multi-cycle sweeps ($\ge 3$ spikes across 4 specimens) exhibit continuous spike-frequency adaptation (**100% expansion**, median ratios $1.97\times\text{--}3.45\times$, maximum $11.27\times$).
   - In contrast, the autonomous two-variable FHN formulation exhibits only brief transient cycle-to-cycle adjustments ($\le 2$ cycles, $\le 120\text{ ms}$; initial ISI change of $-0.5\%\text{ to }+1.2\%$), after which trajectories contract onto the periodic orbit where consecutive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$). Sustained multi-second adaptation was not reproduced over sustained timescales in the tested two-variable autonomous formulation with a single recovery timescale $\tau_w$.

4. **Population D First-Spike Latency Trade-Off:**
   - In Layer 6a (specimen `471786879`), experimental calibration fires 13 spikes with a delayed onset latency of $57.95\text{ ms}$.
   - High-resolution grid scans (961 combinations across $(C_m, \tau_w) \in [40, 220]\text{ pF} \times [8, 50]\text{ ms}$) prove that within the investigated parameter subspace under the calibrated baseline, parameter sets achieving biological repetitive rates ($N_{\mathrm{spk}} \ge 12$) collapse onset latency to $\le 17.40\text{ ms}$ ($\le 16.00\text{ ms}$ at target 13 spikes), whereas achieving biological latency ($t_{\mathrm{lat}} \ge 50\text{ ms}$) strictly restricts firing to $N_{\mathrm{spk}} \le 4$. This empirical trade-off explains the calibrated FHN model's underfiring (mean 1.04 spikes vs. 4.85 recorded).

5. **Hyperpolarization Sag ($I_h$) Measurement and Formulation Limitation:**
   - Intracellular recordings display modest hyperpolarization-activated sag at $-110\text{ pA}$ ($0.63\text{--}1.86\text{ mV}$: Pop A = $0.80\text{ mV}$, Pop B = $1.13\text{ mV}$, Pop C = $0.63\text{ mV}$, Pop D = $1.86\text{ mV}$). Detailed-model sag was not quantified in project evaluation metrics.
   - Under the tested $-110\text{ pA}$ condition, the calibrated FHN models produced zero measured sag ($\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$) because the current linear-recovery formulation contains no explicit hyperpolarization-activated inward conductance mechanism ($I_h$). This characterizes the tested formulation and parameter sets under this condition, and is not a universal mathematical claim about all possible parameterizations of planar models.

---

## 2. Research Question and Final Empirical Scope

### Central Question:
> *"How much biological detail does a neuron model need to reproduce a real neuron's electrophysiological behaviour, and which behaviours are preserved or lost when a detailed conductance-based model is reduced to a FitzHugh–Nagumo model?"*

### Exact Empirical Scope:
- **Biological Dataset:** Primary visual cortex (VISp) spiny excitatory neurons from the Allen Cell Types Database.
- **Specimens:** Four representative single specimens, one per cortical layer:
  - **Population A (Layer 4):** Specimen `484564503` (Rorb-IRES2-Cre, 200 kHz).
  - **Population B (Layer 2/3):** Specimen `318808427` (Nr5a1-Cre, 200 kHz).
  - **Population C (Layer 5):** Specimen `471129934` (Rbp4-Cre_KL100, 200 kHz).
  - **Population D (Layer 6a):** Specimen `471786879` (Ntsr1-Cre_GN220, 200 kHz).
- **Model Tiers Compared:**
  1. *Biological Ground Truth:* Intracellular whole-cell current-clamp recordings.
  2. *Detailed Biophysical Models:* Multi-compartment, perisomatic active conductance models (NEURON 8.2.7 + AllenSDK 2.16.2), containing passive leak plus 7 active conductances ($\mathrm{Na}_v$, $K_v$, $K_v3$, $K_{\mathrm{slow}}$, $I_A$, $I_h$, $\mathrm{Ca}$).
  3. *Reduced Phenomenological Models:* Two-variable dimensional FitzHugh–Nagumo models calibrated via dual-objective Nelder–Mead optimization on a single calibration sweep per population.
- **Evaluation Dataset:** 109 held-out sweeps (COARSE + FINEST long-square 1000 ms current pulses), strictly isolated from model calibration.

### Crucial Boundaries of the Evidence:
- **Single Representatives:** Results characterize four individual specimens and their respective published model fits; they do not establish statistical population distributions across all neurons in a cortical layer.
- **Layer ≠ Projection Class:** The Allen metadata provides anatomical layer and spiny morphology, but does not identify projection targets (IT, ET, PT, CT are unconfirmed).
- **Provisional AP Kinetics:** Numerical upstroke comparisons remain provisional due to unstandardized filtering and numerical differentiation across protocols.
- **Hypothetical Channel Attributions:** Proposed channel-level explanations (e.g., $I_A$ mediating Pop D latency; $I_{\mathrm{SK}}/I_M$ mediating adaptation) are literature-consistent hypotheses, not experimentally isolated currents in this current-clamp dataset.

---

## 3. Evidence and Comparison Methodology

### 3.1 Model Formulations

#### A. Detailed Biophysical Perisomatic Models
Multi-compartmental models with dendritic trees and an active perisomatic compartment governed by:
$$C_m \frac{\mathrm{d}V}{\mathrm{d}t} = -I_{\mathrm{leak}} - \sum_{k} \bar{g}_k m_k^p h_k^q (V - E_k) + I_{\mathrm{inj}}(t)$$
Active conductances include fast transient $\mathrm{Na}_v$, persistent $\mathrm{Na}$, delayed rectifier $K_v3$, slow non-inactivating $K$, transient $I_A$, hyperpolarization-activated $I_h$, and high-threshold $\mathrm{Ca}^{2+}$ with intracellular calcium pump dynamics.

#### B. Dimensional Two-Variable FitzHugh–Nagumo (FHN) Models
Planar dynamical system formulated directly in physiological units:
$$C_m \frac{\mathrm{d}V}{\mathrm{d}t} = -g_L (V - V_{\mathrm{rest}}) + k_v (V - V_{\mathrm{th}})(V - V_{\mathrm{peak}})(V_{\mathrm{rest}} - V) - w + I_{\mathrm{inj}}(t)$$
$$\frac{\mathrm{d}w}{\mathrm{d}t} = \frac{a_w (V - V_{\mathrm{rest}}) - w}{\tau_w}$$
- State variables: Membrane potential $V(t)$ [mV], recovery current $w(t)$ [pA].
- Parameters (7 physiological parameters): Capacitance $C_m$ [pF], leak conductance $g_L$ [nS], resting potential $V_{\mathrm{rest}}$ [mV], dynamic threshold $V_{\mathrm{th}}$ [mV], spike peak parameter $V_{\mathrm{peak}}$ [mV], cubic scaling coefficient $k_v$ [nS/mV$^2$], recovery timescale $\tau_w$ [ms], recovery coupling conductance $a_w$ [nS].
- Effective input resistance: $R_{\mathrm{in,eff}} = \frac{1}{g_L + a_w}$ [M$\Omega$].

### 3.2 Evaluation Metrics
- **Spike Detection:** Upward zero-crossings ($0.0\text{ mV}$) with a $2.0\text{ ms}$ refractory lockout window during the $1000\text{ ms}$ current step.
- **Waveform RMSE:** Evaluated separately during the stimulus step ($[t_{\mathrm{onset}}, t_{\mathrm{onset}} + t_{\mathrm{dur}}]$) and across the entire sweep duration ($[0, t_{\mathrm{stop}}]$).
- **Subthreshold Linearity:** Pearson correlation coefficient ($r$), coefficient of determination ($r^2$ from linear regression), and classical coefficient of determination ($R^2 = 1 - \mathrm{SS}_{\mathrm{res}}/\mathrm{SS}_{\mathrm{tot}}$) across subthreshold steps.
- **Dynamical Bifurcations:** Analytical Jacobian derivation, trace-zero condition, transversality derivative $\mu'(I_{H1})$, first Lyapunov coefficient $l_1$ (Kuznetsov–Poincaré–Andronov convention), and bisection-refined limit-cycle fold thresholds ($I_{\mathrm{fold}}$).

---

## 4. Comprehensive Four-Population Comparison Table

The following synthesis table compiles the authoritative metrics across all four populations. Every numerical value is derived from frozen Phase 3B, Phase 4B, Phase 4C, and Phase 4C.1–4C.3 artifacts:

| Dimension / Metric | Population A (L4) | Population B (L2/3) | Population C (L5) | Population D (L6a) | Authoritative Source Artifact |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Specimen ID** | `484564503` | `318808427` | `471129934` | `471786879` | `fhn_fitted_parameters.csv` |
| **Detailed Model ID** | `485591776` | `473863035` | `480624414` | `480632594` | `heldout_rheobase.csv` |
| **Total Held-Out Sweeps** | 31 (27 COARSE, 4 FINEST) | 18 (17 COARSE, 1 FINEST) | 34 (26 COARSE, 8 FINEST) | 26 (23 COARSE, 3 FINEST) | `population_summary.csv` |
| **Calibration Sweep ID / Stimulus** | Sweep 49 / +370 pA | Sweep 40 / +190 pA | Sweep 51 / +410 pA | Sweep 42 / +250 pA | `fhn_fitted_parameters.csv` |
| **FHN Parameters:** | | | | | |
| - $C_m$ [pF] / $g_L$ [nS] | 133.63 / 3.2394 | 38.25 / 0.8571 | 138.90 / 0.7416 | 206.59 / 0.9128 | `fhn_fitted_parameters.csv` |
| - $V_{\mathrm{rest}}$ [mV] / $V_{\mathrm{th}}$ [mV] | −73.73 / −69.42 | −75.90 / −67.65 | −69.34 / −48.28 | −75.71 / −57.49 | `fhn_fitted_parameters.csv` |
| - $\tau_w$ [ms] / $a_w$ [nS] | 18.11 / 17.18 | 6.89 / 9.77 | 18.89 / 18.87 | 38.86 / 11.72 | `fhn_fitted_parameters.csv` |
| - $R_{\mathrm{in,eff}}$ [M$\Omega$] (FHN / Exp) | 44.29 / 44.29 | 78.67 / 80.30 | 31.29 / 31.29 | 51.96 / 52.60 | `fhn_calibration_metrics.csv` |
| **Resting Potential Offset:** | | | | | |
| - Detailed Model $\Delta V_{\mathrm{baseline}}$ [mV] | **+13.6 mV** (systematic offset) | ≤ +0.5 mV | ≤ +0.6 mV | ≤ +0.4 mV | `heldout_metrics.csv` |
| - FHN Model $\Delta V_{\mathrm{baseline}}$ [mV] | **0.00 mV** (exact match) | 0.00 mV | 0.00 mV | 0.00 mV | `population_summary.csv` |
| **Subthreshold Correlation ($r^2$):** | | | | | |
| - Mutually Subthreshold Steps | 0.9249 ($R^2 = 0.674$) | **0.9900** ($R^2 = 0.489$) | 0.9518 ($R^2 = 0.442$) | **0.9952** ($R^2 = 0.565$) | `phase4c1_subthreshold_audit.csv` |
| - Hyperpolarizing Steps Only | **0.9982** | **0.9988** | **0.9960** | **0.9985** | `phase4c1_subthreshold_audit.csv` |
| - Biological I-V Linearity ($r^2$) | 0.9907 | 0.9868 | 0.9859 | 0.9888 | `phase4c1_subthreshold_audit.csv` |
| **Rheobase Interval [pA]:** | | | | | |
| - Biological Recording | (270, 290] | (110, 130] | (270, 290] | (190, 210] | `heldout_rheobase.csv` |
| - Detailed Model Prediction | (330, 350] (**+60 pA shift**) | (130, 150] (+20 pA shift) | (330, 350] (**+60 pA shift**) | (190, 210] (**0 pA shift**) | `heldout_rheobase.csv` |
| - FHN Hopf Current $I_{H1}$ | 234.34 pA | 161.28 pA | 385.33 pA | 236.27 pA | `phase4c3_hopf_independent_checks.csv` |
| - FHN Open Bistability Window | (214.16, 234.34) pA | (146.72, 161.28) pA | (360.03, 385.33) pA | (215.92, 236.27) pA | `phase4c3_bistability_verification.csv` |
| **Spike Detection Classification:** | | | | | |
| - Biological Ground Truth (Spk / Non) | 11 / 20 | 8 / 10 | 11 / 23 | 10 / 16 | `phase4c1_spike_detection_audit.csv` |
| - Detailed Model (TP / FP / FN / TN) | 4 / 0 / 7 / 20 | 6 / 0 / 2 / 10 | 4 / 0 / 7 / 23 | 10 / 0 / 0 / 16 | `phase4c1_spike_detection_audit.csv` |
| - Detailed Model Sensitivity / Specificity | 36.4% / 100.0% | 75.0% / 100.0% | 36.4% / 100.0% | 100.0% / 100.0% | `phase4c1_spike_detection_audit.csv` |
| - FHN Model (TP / FP / FN / TN) | 11 / 4 / 0 / 16 | 6 / 0 / 2 / 10 | 10 / 2 / 1 / 21 | 10 / 1 / 0 / 15 | `phase4c1_spike_detection_audit.csv` |
| - FHN Model Sensitivity / Specificity | 100.0% / 80.0% | 75.0% / 100.0% | 90.9% / 91.3% | 100.0% / 93.8% | `phase4c1_spike_detection_audit.csv` |
| **Mean Spike Count per Step:** | | | | | |
| - Biological Recording | 1.77 | 6.83 | 0.97 | 4.85 | `population_summary.csv` |
| - Detailed Model Prediction | 3.71 | 7.67 | 0.94 | 6.19 | `population_summary.csv` |
| - FHN Model Prediction | 4.00 | 3.78 | 1.00 | 1.04 (**underfires**) | `population_summary.csv` |
| - Mean Abs Error (Detailed vs. FHN) | 3.23 vs. **2.74** | **1.06** vs. 4.28 | 0.62 vs. **0.38** | **1.73** vs. 4.58 | `population_summary.csv` |
| **Waveform RMSE & Correlation:** | | | | | |
| - Step RMSE (Detailed vs. FHN) [mV] | **8.30** vs. 22.10 | **7.61** vs. 23.73 | **4.15** vs. 12.36 | **5.89** vs. 23.56 | `population_summary.csv` |
| - Overall RMSE (Detailed vs. FHN) [mV] | 12.73 vs. **8.24** | **4.04** vs. 11.97 | **4.73** vs. 4.81 | **2.23** vs. 9.03 | `population_summary.csv` |
| - Mean Pearson $r$ (Detailed vs. FHN) | 0.8036 vs. **0.8352** | **0.9570** vs. 0.8960 | **0.9610** vs. 0.8775 | **0.9699** vs. 0.8889 | `population_summary.csv` |
| **Adaptation & Dynamic Scope:** | | | | | |
| - Multi-Cycle Sweeps ($\ge 3$ spk) | 6 / 31 sweeps | 6 / 18 sweeps | 4 / 34 sweeps | 7 / 26 sweeps | `phase4c3_biological_adaptation_scope.csv` |
| - Biological ISI Expansion Ratio | 1.17–8.06 (med 3.45) | 1.45–3.97 (med 2.57) | 1.89–11.27 (med 2.83) | 1.13–2.47 (med 1.97) | `phase4c3_biological_adaptation_scope.csv` |
| - FHN Limit Cycle Adaptation | $\le 2$ cycles; stationary | $\le 2$ cycles; stationary | $\le 2$ cycles; stationary | $\le 2$ cycles; stationary | `phase4c2_isi_transient_adaptation.csv` |
| - Biological Hyperpolarization Sag ($I_h$) [mV] | 0.80 mV (modest) | 1.13 mV (modest) | 0.63 mV (modest) | 1.86 mV (modest) | `PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md` |
| - Detailed Model Hyperpolarization Sag [mV] | Not quantified | Not quantified | Not quantified | Not quantified | Phase 3B/4C metrics |
| - FHN Hyperpolarization Sag [mV] | 0.00 mV (absent) | 0.00 mV (absent) | 0.00 mV (absent) | 0.00 mV (absent) | `PHASE4C_HELDOUT_EVALUATION_REPORT.md` |

---

## 5. Population-by-Population Findings

### 5.1 Population A — VISp Layer 4 (Specimen `484564503`)
- **Biological Characteristics:** Low input resistance ($R_{\mathrm{in}} = 44.3\text{ M}\Omega$), high rheobase ($(270, 290]\text{ pA}$), moderate repetitive firing at high currents (up to 13 spikes at +410 pA), and substantial late-step firing cessation.
- **Detailed Model Behaviour:** Suffers from a critical fitting artifact: a $+13.6\text{ mV}$ resting membrane potential offset ($\Delta V_{\mathrm{baseline}} = +13.25\text{ mV}$). The resting potential sits at $-61.1\text{ mV}$ compared to the recorded $-73.7\text{ mV}$. In the COARSE protocol, the detailed model overestimates rheobase by $+60\text{ pA}$ (spiking in only 4 out of 11 biological spiking sweeps; sensitivity $36.4\%$). Whether this shift is causally related to the resting potential offset, to calibration on a strongly suprathreshold sweep (+370 pA), or to active conductances in the published fit remains an unresolved question, rather than a proven failure of conductance-based modeling generally. At extreme currents (+390 to +430 pA), the detailed model drastically overcounts spikes (up to 48 spikes vs. 12 recorded) due to lack of late-step spike cessation.
- **FHN Model Behaviour:** Maintains the exact resting potential ($-73.73\text{ mV}$). Detects 100% of biological spiking sweeps ($11/11$), but produces 4 false positives in near-threshold subthreshold sweeps (spiking at +210 to +270 pA due to its subcritical Hopf current $I_{H1} = 234.3\text{ pA}$). FHN produces a lower overall RMSE ($8.24\text{ mV}$ vs. $12.73\text{ mV}$) purely because its baseline is accurate; during the stimulus step, its RMSE ($22.10\text{ mV}$) is far worse than the detailed model ($8.30\text{ mV}$).

### 5.2 Population B — VISp Layer 2/3 (Specimen `318808427`)
- **Biological Characteristics:** Highest input resistance ($R_{\mathrm{in}} = 80.3\text{ M}\Omega$), lowest rheobase ($(110, 130]\text{ pA}$), fast repetitive firing (up to 18 spikes at +270 pA), and rapid action potentials with sharp afterhyperpolarizations.
- **Detailed Model Behaviour:** The best-performing detailed model across all metrics. Rheobase is closely tracked (+20 pA shift); step RMSE is $7.61\text{ mV}$, overall RMSE is $4.04\text{ mV}$, Pearson $r$ is $0.9570$, and spike count absolute error is only $1.06$ spikes per step.
- **FHN Model Behaviour:** Rapid recovery timescale ($\tau_w = 6.89\text{ ms}$) allows higher firing frequencies near threshold, but FHN collapses to only 1–2 spikes at high currents (+250 to +270 pA) due to premature exit into depolarization block. FHN step RMSE is high ($23.73\text{ mV}$) and spike count error is $4.28$ spikes.

### 5.3 Population C — VISp Layer 5 (Specimen `471129934`)
- **Biological Characteristics:** Lowest input resistance ($R_{\mathrm{in}} = 31.3\text{ M}\Omega$), high rheobase ($(270, 290]\text{ pA}$), low firing rate near threshold (sparse 1-spike onset transients across many suprathreshold steps), and extreme adaptation at high currents ($11.27\times$ ISI expansion at +430 pA).
- **Detailed Model Behaviour:** Strongly underfires near threshold (spiking in only 4/11 sweeps; sensitivity $36.4\%$), overestimating COARSE-protocol rheobase by $+60\text{ pA}$. The underlying cause for this rheobase shift remains unresolved, and calibration on a single suprathreshold sweep (+410 pA) is a possible methodological consideration rather than an established explanation. When it does fire, waveform fidelity is high (step RMSE $4.15\text{ mV}$, correlation $0.9610$).
- **FHN Model Behaviour:** Tracks sparse near-threshold excitability with low absolute spike error ($0.38$ vs. Detailed $0.62$). However, FHN cannot reproduce the 11-fold biological adaptation at +430 pA, firing stationary periodic spikes instead. Step RMSE ($12.36\text{ mV}$) is roughly triple that of the detailed model.

### 5.4 Population D — VISp Layer 6a (Specimen `471786879`)
- **Biological Characteristics:** Moderate input resistance ($52.6\text{ M}\Omega$), moderate rheobase ($(190, 210]\text{ pA}$), prominent onset latency ($57.95\text{ ms}$ at calibration; $1133\text{ ms}$ near threshold at 210 pA), and sustained firing (13 spikes at +250 pA, up to 27 spikes at +350 pA).
- **Detailed Model Behaviour:** Accurately captures rheobase (exact match: $(190, 210]\text{ pA}$, shift $0\text{ pA}$), achieves $100\%$ sensitivity and $100\%$ specificity, low step RMSE ($5.89\text{ mV}$), low overall RMSE ($2.23\text{ mV}$), and high correlation ($0.9699$). At the single calibration operating point (Sweep 42, COARSE, $+250\text{ pA}$), it captures both delayed first-spike latency ($52.97\text{ ms}$ vs. $57.95\text{ ms}$ recorded) and repetitive firing (14 spikes vs. 13 recorded). However, this simultaneous alignment is a single observed operating point rather than an invariant decoupling across conditions: near threshold at $+210\text{ pA}$ (Sweep 40), its first spike is delayed to $978.91\text{ ms}$ (firing 1 spike vs. 5 recorded), while in FINEST protocols at $+240\text{ pA}$ (Sweeps 52–54), it overfires with 11 spikes ($87.30\text{ ms}$) compared to 1 recorded biological spike.
- **FHN Model Behaviour:** Exhibits severe quantitative failure in spike count. To match the $58\text{ ms}$ first-spike latency, calibration converged to a large recovery timescale ($\tau_w = 38.86\text{ ms}, C_m = 206.59\text{ pF}$). This heavy recovery damping capped repetitive firing to only 4 spikes at calibration and a mean of $1.04$ spikes across held-out sweeps (vs. $4.85$ recorded). Step RMSE is $23.56\text{ mV}$.

---

## 6. Synthesis: Preserved, Restricted, Mismatched, and Absent Behaviours

Rather than forcing a simplistic binary classification, cortical electrophysiological behaviours fall into five distinct categories:

```
+-----------------------------------------------------------------------------------+
|               FIVE-TIER TAXONOMY OF MODEL REDUCTION FIDELITY                     |
+-----------------------------------------------------------------------------------+
| 1. Reproduced Reasonably Well     | Passive charging, R_in, resting V_rest        |
| 2. Reproduced Under Restrictions  | Subthreshold linearity, threshold switching   |
| 3. Systematically Mismatched /    | Action potential kinetics, spike counts,      |
|    Subspace-Constrained           | latency-frequency trade-off in tested grid   |
| 4. Structurally Absent from Model | Sustained multi-second adaptation, I_h sag    |
|    Formulation                    | (features lacking explicit equations/states)  |
| 5. Not Adequately Identifiable    | Channel attributions, projection phenotype    |
+-----------------------------------------------------------------------------------+
```

### Tier 1: Behaviours Reproduced Reasonably Well
1. **Resting Membrane Potential ($V_{\mathrm{rest}}$):**
   - *FHN:* Matches biological baseline by construction ($V_{\mathrm{rest}} \in [-75.9, -69.3]\text{ mV}$, offset $0.00\text{ mV}$).
   - *Detailed Model:* Generally good (offsets $\le 0.6\text{ mV}$ in B, C, D), but failed dramatically in Population A ($+13.6\text{ mV}$ offset).
2. **Hyperpolarizing Subthreshold Linearity and Input Resistance ($R_{\mathrm{in}}$):**
   - *FHN:* Captures steady-state passive $R_{\mathrm{in}}$ faithfully ($r^2 > 0.996$ in hyperpolarizing steps across all four populations; calibration $R_{\mathrm{in}}$ within $0.0\text{--}2.0\%$ of biology).
   - *Crucial Distinction:* High performance in the strictly hyperpolarizing regime must not be equated with general all-subthreshold performance, which includes near-threshold non-linearities.
   - *Detailed Model:* Excellent hyperpolarizing linearity.

### Tier 2: Behaviours Reproduced Only Under Restricted Conditions
1. **Mutually Subthreshold Linearity:**
   - *FHN:* High fidelity in Populations B ($r^2 = 0.9900$) and D ($r^2 = 0.9952$), but degrades in Populations A ($r^2 = 0.9249$) and C ($r^2 = 0.9518$) due to near-threshold subthreshold non-linearities and baseline shifts.
2. **Macroscopic Excitability Threshold (Spike Detection):**
   - *FHN:* High detection sensitivity ($92.5\%$, $37/40$ sweeps), but restricted by false positives near threshold ($89.9\%$ specificity, 7 FP sweeps).
   - *Detailed Model:* Perfect specificity ($100.0\%$, 0 FP sweeps), but poor sensitivity in COARSE protocols ($60.0\%$, missing 16 spiking sweeps).
   - *Crucial Qualification:* High binary spike-detection sensitivity indicates reliable bifurcation threshold crossing; it does **not** establish accurate reproduction of spike trains, spike timing, or rate coding.
3. **Monotonic Firing-Rate Scaling ($F-I$ Curves):**
   - *FHN:* Captures monotonic rate scaling across moderate current ranges in COARSE protocols for Populations A, B, and C. Breaks down at high currents where premature depolarization block caps firing, exhibits protocol-dependent inconsistencies in FINEST sweeps, and fails completely in Population D.

### Tier 3: Behaviours Systematically Mismatched or Subspace-Constrained
1. **Action Potential Waveform Kinetics [Provisional Supporting Observation]:**
   - *Observed Waveform Differences & Trajectory Envelope:* Biological intracellular recordings exhibit narrow action potentials ($< 1.5\text{ ms}$ width) with rapid repolarization and sharp afterhyperpolarization troughs. Detailed biophysical models produce narrow spike profiles closer in overall shape and duration to biology, achieving much lower step RMSE ($4.15\text{--}8.30\text{ mV}$) than FHN ($12.36\text{--}23.73\text{ mV}$). FHN produces broad cubic relaxation oscillations with gradual take-off and slow symmetric recovery.
   - *Separation of Step RMSE from Validated Kinetics:* Lower step RMSE reflects superior tracking of the spike trajectory envelope and rapid return to baseline relative to broad FHN waves, but does **not** establish directly validated action-potential kinetics. Fine kinetic features—such as rise times, upstroke velocities, repolarization rates, and AHP depths—were not directly benchmarked or validated for either model tier.
   - *Provisional Numerical Upstroke Comparison:* Unstandardized derivative calculations yield peak $\mathrm{d}V/\mathrm{d}t \approx 397\text{--}466\text{ V/s}$ in biological recordings vs. $5.7\text{--}6.2\text{ V/s}$ in FHN (a nominal $60\times\text{--}75\times$ divergence).
   - *What Remains Unverified:* Because analog filtering bandwidth, digital differentiation stencils (e.g., central differences vs. spline smoothing), and sampling alignment were not standardized between the 200 kHz biological recordings and model simulations, exact numerical upstroke velocities remain provisional. Furthermore, the detailed models' fine derivative kinetics ($\mathrm{d}V/\mathrm{d}t$ vs. $V$ phase planes) were not standardized or benchmarked against recorded spikes under identical stencils; therefore, claiming that detailed models "accurately reproduce" fine AP kinetics is unverified by repository evidence.
2. **Suprathreshold Spike Counts and Firing Frequency:**
   - *FHN:* Severely underpredicts high-frequency firing in Populations B and D (e.g., fires 1 spike vs. 27 biological spikes in Pop D at +350 pA). This reflects a parameter-damping limitation of the calibrated parameter sets rather than an inherent impossibility of the FHN equations.
   - *Detailed Model:* Closer to biology on average, but suffers from severe overfiring at high currents in Population A (48 spikes vs. 12 recorded) and in FINEST sweeps for Population D (11 spikes vs. 1 recorded).
3. **Decoupled First-Spike Latency and Repetitive Firing (Tested Subspace Constraint):**
   - *Biology:* Specimen `471786879` (L6a) sustains both delayed onset ($57.95\text{ ms}$) and repetitive firing (13 spikes) at the calibration condition (Sweep 42, COARSE, $+250\text{ pA}$).
   - *Detailed Model Calibration Operating Point:* In the identical calibration sweep, the detailed model reproduces this combination ($t_{\mathrm{lat}} = 52.97\text{ ms}$, $N_{\mathrm{spk}} = 14$). However, this represents a single observed operating point at $+250\text{ pA}$ rather than an unconstrained decoupling capability across all protocols (e.g., at $+210\text{ pA}$ in Sweep 40, its first spike is delayed to $978.91\text{ ms}$ with 1 spike vs. 5 biological spikes at $133.82\text{ ms}$; in FINEST sweeps at $+240\text{ pA}$, it fires 11 spikes vs. 1 recorded).
   - *FHN Empirical Constraint:* Across 961 explicit RK4 simulations in the tested $(C_m, \tau_w) \in [40, 220]\text{ pF} \times [8, 50]\text{ ms}$ subspace with fixed remaining parameters, parameter sets achieving biological repetitive rates ($N_{\mathrm{spk}} \ge 12$) collapse onset latency to $\le 17.40\text{ ms}$ ($\le 16.00\text{ ms}$ at target 13 spikes), while configurations matching biological latency ($t_{\mathrm{lat}} \ge 50\text{ ms}$) yield $\le 4$ spikes.
   - *Scope of Conclusion:* This is an empirically demonstrated limitation of the calibrated model within the investigated 2D parameter subspace under the calibration objective. It is **not** a proven universal mathematical impossibility across all two-variable planar systems.

### Tier 4: Behaviours Structurally Absent from the Current Model Formulation
1. **Sustained Multi-Second Spike-Frequency Adaptation:**
   - *Biology:* Continuous ISI expansion observed across all 23 qualifying multi-cycle sweeps ($\ge 3$ spikes across 4 specimens; ratios up to $11.3\times$).
   - *FHN Formulation Scope:* With only one recovery variable $w(t)$ operating on timescale $\tau_w \approx 7\text{--}39\text{ ms}$, trajectories contract onto the periodic limit cycle within $\le 2$ cycles ($\le 120\text{ ms}$; initial transient ISI adjustment of $-0.5\%\text{ to }+1.2\%$), after which successive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$). The current two-variable autonomous formulation and calibrated parameter sets did not reproduce the sustained multi-second adaptation observed in qualifying biological sweeps. In standard conductance-based or reduced neuron models, sustaining adaptation across multi-second stimulus steps typically requires slower activity-dependent processes (such as a second recovery variable or slow calcium-activated conductances), which are absent from this formulation.
2. **Hyperpolarization-Activated Inward Rectification ($I_h$ Sag):**
   - *Biology:* Modest depolarizing sag of $0.63\text{--}1.86\text{ mV}$ (Pop A: $0.80\text{ mV}$, Pop B: $1.13\text{ mV}$, Pop C: $0.63\text{ mV}$, Pop D: $1.86\text{ mV}$) observed during $-110\text{ pA}$ hyperpolarizing current pulses.
   - *Detailed Model:* Not quantified in repository evaluation metrics (no $\Delta V_{\mathrm{sag}}$ metric extracted in Phase 3B/4C).
   - *FHN Formulation Scope:* Under the tested $-110\text{ pA}$ condition, the calibrated FHN models produced zero measured sag ($\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$) because the linear recovery equation $w = a_w(V - V_{\mathrm{rest}})$ has no explicit hyperpolarization-activated inward conductance mechanism ($I_h$). This reflects the tested formulation and calibrated parameter sets under this protocol, and is not a universal mathematical claim about all conceivable parameterizations of two-variable planar systems.

### Tier 5: Behaviours Not Adequately Tested or Not Identifiable
1. **Specific Ionic Channel Attributions:**
   - Literature hypotheses attributing Population D latency to transient A-type potassium current ($I_A$), or adaptation to $I_{\mathrm{SK}}/I_M$, cannot be verified from current-clamp voltage recordings alone without pharmacological channel blockers.
2. **Projection-Class Phenotypes:**
   - IT, ET, PT, and CT functional phenotypes cannot be confirmed due to absence of projection tracking metadata in the Allen dataset.

---

## 7. Detailed Model versus FHN Trade-Offs

A balanced scientific evaluation demonstrates that neither model tier is universally superior across all electrophysiological criteria:

```
+-----------------------------------------------------------------------------------+
|               METRIC-DEPENDENT COMPARATIVE TRADE-OFF SUMMARY                      |
+-----------------------------------------------------------------------------------+
| Metric Category              | Detailed Biophysical Model | Reduced FHN Model     |
+------------------------------+----------------------------+-----------------------+
| Resting Potential Offset     | Poor (Pop A offset +13.6mV)| Excellent (0.00 mV)   |
| Spike Detection Sensitivity  | Poor (60.0%, 16 FN)        | Excellent (92.5%, 3 FN)|
| Spike Detection Specificity  | Perfect (100.0%, 0 FP)     | Moderate (89.9%, 7 FP)|
| Step Waveform RMSE           | Excellent (4.15 - 8.30 mV) | Poor (12.36 - 23.73mV)|
| Action Potential Waveform    | Fast spikes (narrow width) | Broad relaxation wave |
| Input Resistance Matching    | Variable (complex tree)    | Exact (R_in calibrated|
| Multi-cycle Adaptation       | Present (multi-channel)    | Absent in 2D limit cycle|
| Computational Cost           | High (NEURON solver)       | Minimal (2D ODE RK4)  |
+-----------------------------------------------------------------------------------+
*Note: Detailed model derivative kinetics and hyperpolarization sag were not independently standardized or quantified in project evaluation metrics.*
```

### 7.1 Excitability Detection vs. Firing Pattern
- **FHN Advantage:** Because FHN undergoes a clean subcritical Hopf bifurcation with an open bistability interval, it transitions into repetitive firing reliably near threshold, detecting **$37 / 40$ biological spiking sweeps** ($92.5\%$). The detailed models overestimate COARSE rheobase by approximately $+60\text{ pA}$ in Populations A and C, detecting only **$24 / 40$ biological spiking sweeps** ($60.0\%$). While calibration on a single suprathreshold sweep (+370/+410 pA) is a plausible methodological consideration, the definitive biophysical cause remains unresolved, and this discrepancy should not be construed as an established general failure of conductance-based modeling.
- **FHN Limitation:** FHN's high sensitivity is offset by 7 false positives (spiking on near-threshold subthreshold sweeps), and once suprathreshold, FHN firing rates do not match biological spike trains.

### 7.2 The Population A RMSE Paradox
- In Population A, FHN reports a lower overall RMSE ($8.24\text{ mV}$) than the detailed model ($12.73\text{ mV}$).
- **The Physical Reality:** The detailed model has a step RMSE of $8.30\text{ mV}$ (capturing action potentials reasonably well), but a non-step RMSE of $13.25\text{ mV}$ due to its $+13.6\text{ mV}$ baseline offset. Because non-stimulus intervals span $7.0\text{ s}$ ($87.5\%$ of duration), **$92.3\%$ of the detailed model's MSE is baseline error**. FHN has zero baseline error, but its step RMSE is $22.10\text{ mV}$ ($89.2\%$ of its MSE). FHN is superior solely as a baseline tracker, not as a waveform model.

### 7.3 Waveform Fidelity in Populations B, C, and D
- In Populations B and D, where the detailed model has accurate resting potentials ($\le 0.5\text{ mV}$ offset), the detailed model heavily outperforms FHN on every waveform metric:
  - *Pop B:* Det step RMSE $7.61\text{ mV}$ vs. FHN $23.73\text{ mV}$; Det corr $0.9570$ vs. FHN $0.8960$.
  - *Pop D:* Det step RMSE $5.89\text{ mV}$ vs. FHN $23.56\text{ mV}$; Det corr $0.9699$ vs. FHN $0.8889$.
- In Population C, overall RMSE is comparable ($4.73\text{ mV}$ vs. $4.81\text{ mV}$), but detailed step RMSE ($4.15\text{ mV}$) is roughly one-third of FHN ($12.36\text{ mV}$).
- *Methodological Distinction:* This step RMSE advantage reflects the detailed model's ability to track the narrow temporal profile of action potentials and return quickly to baseline, in contrast to the broad relaxation waves of FHN. It demonstrates waveform envelope fidelity, but does not constitute direct empirical validation of fine action-potential kinetics (such as upstroke velocity, rise time, or AHP depth), which were not standardized across models.

---

## 8. Population D Parameter-Scan Interpretation

The quantitative failure of FHN in Population D (L6a) prompted exhaustive 2D parameter grid scans over membrane capacitance $C_m$ and recovery timescale $\tau_w$ under the calibrated baseline parameters ($g_L = 0.9128\text{ nS}, V_{\mathrm{rest}} = -75.71\text{ mV}, V_{\mathrm{th}} = -57.49\text{ mV}, V_{\mathrm{peak}} = 65.00\text{ mV}, k_v = 0.002577\text{ nS/mV}^2, a_w = 11.72\text{ nS}$, stimulus $+250\text{ pA}$).

### 8.1 Disentangling the Two Authoritative Scans
Two distinct scans were executed across Phases 4B.1 and 4B.2:

```
+-----------------------------------------------------------------------------------+
|               POPULATION D PARAMETER-SCAN PROVENANCE MATRIX                      |
+-----------------------------------------------------------------------------------+
| Scan Identifier              | Phase 4B.1 Baseline Scan   | Phase 4B.2 Refined Scan|
+------------------------------+----------------------------+-----------------------+
| Grid Resolution              | 25 x 25 = 625 combinations | 31 x 31 = 961 comb.   |
| C_m Range [pF]               | 40.0 to 240.0 (step 8.33)  | 40.0 to 220.0 (step 6)|
| tau_w Range [ms]             | 8.0 to 60.0 (step 2.17)    | 8.0 to 50.0 (step 1.4)|
| Spiking / Quiescent Samples  | 553 (88.5%) / 72 (11.5%)   | 850 (88.4%) / 111     |
| Target Count (13 spk) Max Lat| 12.20 ms (mean 10.80 ms)   | 16.00 ms (mean 12.93) |
| High-Spiking (>=12) Max Lat  | 18.50 ms (at N_spk = 12)   | 17.40 ms (at N_spk=12)|
| Long-Latency (>=50 ms) Bound | Strictly N_spk <= 4        | Strictly N_spk <= 4   |
| Primary Artifact CSV         | fhn_population_d_pareto_   | fhn_population_d_grid_|
|                              | audit.csv                  | points.csv / refined_ |
+-----------------------------------------------------------------------------------+
```

### 8.2 Historical Discrepancy Resolved
In `results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md`, Section 2.1 correctly describes the 625-point scan and Section 2.2 correctly describes the 961-point scan. However, in Table 3.1 of that report, the row for "Demonstrated Numerical Result" inadvertently merged the parameter bounds of Scan 1 ($[40, 240]\text{ pF} \times [8, 60]\text{ ms}$, max latency $18.5\text{ ms}$) with the sample size of Scan 2 ($961$ simulations). The authoritative high-resolution scan is the **Phase 4B.2 961-point scan**, where maximum latency at the exact target count (13 spikes) is **$16.00\text{ ms}$**, and maximum latency for $N_{\mathrm{spk}} \ge 12$ is **$17.40\text{ ms}$**.

### 8.3 Scientific Interpretation: Parameter Subspace Constraint vs. Universal Impossibility
- **Verified Numerical Result:** Across 961 explicit RK4 simulations on specimen `471786879` (Sweep 42), every configuration producing biological spike counts ($N_{\mathrm{spk}} \ge 12$) has onset latency $\le 17.40\text{ ms}$ ($\le 16.00\text{ ms}$ at 13 spikes). Conversely, every configuration matching the biological onset latency ($t_{\mathrm{lat}} \ge 50\text{ ms}$) fires at most 4 spikes.
- **Rigorously Bounded Scope:** Per the Phase 4B.2 audit, this result is an empirical property of the investigated $(C_m, \tau_w)$ parameter space under the calibrated baseline parameters and calibration objective. It must **not** be extrapolated into an unproven "universal mathematical impossibility theorem" across all two-variable planar systems, unconstrained $\mathbb{R}^7$ parameterizations, or non-standard nullcline geometries.

---

## 9. Biological Interpretation and Methodological Limitations

### 9.1 The 14 Non-Negotiable Methodological Caveats
1. **Sample Size:** Findings are based on four individual representative specimens (one per layer). They do not establish general layer-wide cortical statistics.
2. **Layer ≠ Projection Class:** Groups are layer-defined excitatory neurons; projection targets (IT, ET, PT, CT) are unverified.
3. **L4 Morphology:** All 47 identity-compatible L4 cells possess intact apical dendrites; spiny stellate morphology is unconfirmed (classified as star-pyramidal/IT-like unresolved).
4. **L5 Heterogeneity:** Rbp4-Cre_KL100 targets L5 pyramidal cells but does not resolve ET versus PT subclasses.
5. **L6a Identity:** Ntsr1-Cre_GN220 is corticothalamic-compatible, but CT identity is not directly confirmed.
6. **Morphology Substitution:** Population B's published detailed model used a substitute reconstruction (`491771090` $\ne$ recorded cell's `674389884`), introducing unquantified dendritic filtering bias.
7. **Protocol Nonstationarity:** COARSE and FINEST protocols exhibit measurable biological drift and threshold shifts within the same cell (Phase 2F).
8. **Phenomenological Nature of FHN:** FHN is a minimal nonlinear dynamical model, not a biophysical simulation of ion channels.
9. **Metric-Dependent Evaluation:** Lower overall RMSE in Population A is driven by detailed-model baseline error, not FHN waveform fidelity.
10. **Bistability Boundary Semantics:** Bistability strictly applies to the open interval $(I_{\mathrm{fold}}, I_{H1})$. Fold boundaries are non-hyperbolic orbit coalescence points with conservative numerical uncertainty $\pm 0.01\text{ pA}$; they are forward-integration extinction thresholds, not continuation-derived bifurcation points.
11. **Local vs. Global Bifurcation Separation:** Subcritical Hopf criticality ($l_1 > 0$) is a strictly local property at $I_{H1}$; global limit-cycle folding must be separated from local analysis.
12. **Adaptation Data Scope:** Sustained biological adaptation was audited in 23 qualifying multi-cycle sweeps from 4 specimens, not 109 independent neurons.
13. **Untested Ionic Mechanisms:** Proposed attributions to $I_A$ (latency), $I_{\mathrm{SK}}/I_M$ (adaptation), and $I_h$ (sag) remain literature-consistent hypotheses.
14. **Population D Trade-Off Bounded to Parameter Subspace:** The trade-off is proven within the tested $(C_m, \tau_w)$ grid under the calibration objective, not as a universal theorem for all planar systems.

---

## 10. Direct Answer to the Research Question

### Question:
*"How much biological detail does a neuron model need to reproduce a real neuron's electrophysiological behaviour, and which behaviours are preserved or lost when a detailed conductance-based model is reduced to a FitzHugh–Nagumo model?"*

### Direct Empirical Answer:

#### 1. What a 2-Variable Phenomenological FHN Model Needs (and What It Preserves):
A two-variable dimensional FHN model requires only **7 parameters** ($C_m, g_L, V_{\mathrm{rest}}, V_{\mathrm{th}}, V_{\mathrm{peak}}, k_v, \tau_w, a_w$) and a single calibration sweep to successfully capture:
- The **resting membrane potential** ($V_{\mathrm{rest}}$) and steady-state subthreshold input resistance ($R_{\mathrm{in}}$), matching biological charging with high fidelity ($r^2 > 0.996$ on hyperpolarizing steps).
- The **macroscopic excitability boundary** (rheobase transition), capturing the onset of repetitive firing via a subcritical Hopf bifurcation ($92.5\%$ sensitivity across 109 held-out sweeps).
- Qualitative monotonic firing-rate scaling across moderate suprathreshold current steps.

#### 2. What Is Lost When Reducing to 2 Variables:
When all biological active conductances and morphology are condensed into two planar variables ($V, w$), four critical neurocomputational behaviours are fundamentally lost or constrained:
1. **Sustained Multi-Second Spike-Frequency Adaptation:** Biological neurons expand ISIs by up to $11\times$ across 1-second steps (verified across 23 qualifying multi-cycle sweeps), whereas the tested two-variable autonomous FHN formulation contracts to stationary limit cycles within $\le 2$ cycles. Sustained multi-second adaptation was not reproduced in this formulation due to the absence of a slow secondary recovery process.
2. **Action Potential Kinetics and Shape [Provisional Upstroke Metrics]:** Without fast transient sodium gating, FHN generates smooth cubic relaxation oscillations (provisional upstroke velocity $5.7\text{--}6.2\text{ V/s}$), resulting in high step RMSE ($12\text{--}24\text{ mV}$) and broad repolarization.
3. **Decoupled Latency and Frequency Scaling in Tested Subspace:** In Layer 6a, the biological specimen displays delayed onset ($58\text{ ms}$) followed by fast repetitive firing (13 spikes). Within the investigated 2D parameter subspace, FHN parameter sets matching onset latency yield $\le 4$ spikes, whereas parameter sets achieving repetitive firing collapse onset latency to $\le 17.40\text{ ms}$.
4. **Hyperpolarization Inward Rectification ($I_h$ Sag):** Linear recovery cannot produce the depolarizing sag observed in cortical pyramidal cells during hyperpolarization.

#### 3. How Much Biological Detail Is Actually Needed?
- **For Subthreshold Integration & Excitability Gating:** A 2-variable dimensional FHN model is **sufficient**. It matches passive charging and captures threshold switching better than under-calibrated biophysical models.
- **For Spike-Train Timing, Rate Coding, and Waveform Fidelity:** The tested 2-variable model is **insufficient**. To capture sustained adaptation, delayed onset, and fast action potentials within conventional reduced dynamical frameworks, models typically require:
  - An additional dynamical recovery process (e.g., a second slow recovery variable or slow adaptation current) operating on a multi-second timescale ($\tau \gg 100\text{ ms}$).
  - An independent **transient inactivating conductance** (or variable threshold) to decouple onset latency from steady-state cycling.
  - Multi-conductance kinetics ($\mathrm{Na}_v / K_v$) to capture millisecond upstroke and downstroke kinetics.

---

## 11. Implications for Model Reduction

1. **Hierarchy of Model Reduction:**
   $$\text{Morphologically Detailed (NEURON)} \;\longrightarrow\; \text{Point Biophysical (Hodgkin–Huxley)} \;\longrightarrow\; \text{3D Adaptive (AdEx/Izhikevich)} \;\longrightarrow\; \text{2D Planar (FHN)}$$
   The jump from 3D adaptive systems (e.g., Adaptive Exponential Integrate-and-Fire, AdEx) down to 2D planar systems (FHN) represents the critical boundary where multi-timescale adaptation and delayed firing are extinguished.
2. **Calibration Objective Sensitivity:**
   In multi-compartment biophysical models, the detailed models for Populations A and C overestimated COARSE rheobase by approximately $+60\text{ pA}$. While fitting to a single suprathreshold sweep (+370/+410 pA) is a plausible methodological contributor, the definitive cause remains unresolved. This highlights the practical importance of evaluating models across the entire dynamic range rather than assuming suprathreshold parameter fits generalize to threshold activation.
3. **The Role of FHN in Large-Scale Cortical Networks:**
   FHN remains ideal for large-scale mesoscopic network models where computational efficiency and macroscopic bifurcation gating (on/off switching) are paramount, provided the network does not rely on spike-frequency adaptation or precise spike-timing codes.

---

## 12. Authoritative Source File Traceability

The following matrix documents the exact repository artifacts supporting every quantitative conclusion in this synthesis:

| Major Conclusion / Metric | Supporting Repository Source Files | Status |
| :--- | :--- | :---: |
| **FHN Frozen Parameters (7 params)** | [`results/phase4b/fhn_fitted_parameters.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b/fhn_fitted_parameters.csv) | Frozen |
| **FHN Calibration Metrics & $R_{\mathrm{in}}$** | [`results/phase4b/fhn_calibration_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b/fhn_calibration_metrics.csv) | Frozen |
| **Detailed Model Held-Out Metrics** | [`results/phase3b/heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv) | Frozen |
| **Detailed Model Rheobase & Shifts** | [`results/phase3b/heldout_rheobase.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_rheobase.csv) | Frozen |
| **FHN Held-Out Population Summary** | [`results/phase4c/population_summary.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c/population_summary.csv) | Frozen |
| **Protocol Family Breakdown** | [`results/phase4c/protocol_family_summary.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c/protocol_family_summary.csv) | Frozen |
| **Spike Detection Confusion Matrix** | [`results/phase4c1/phase4c1_spike_detection_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_spike_detection_audit.csv) | Audited |
| **Subthreshold Correlations ($r^2, R^2$)** | [`results/phase4c1/phase4c1_subthreshold_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_subthreshold_audit.csv) | Audited |
| **Pop A RMSE Decomposition (92.3%)** | [`results/phase4c1/phase4c1_rmse_decomposition.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c1/phase4c1_rmse_decomposition.csv) | Audited |
| **FHN Transient Adaptation (1–2 cycles)**| [`results/phase4c2/phase4c2_isi_transient_adaptation.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c2/phase4c2_isi_transient_adaptation.csv) | Audited |
| **Biological Adaptation Scope (23 sweeps)**| [`results/phase4c3/phase4c3_biological_adaptation_scope.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_biological_adaptation_scope.csv) | Audited |
| **Hopf Bifurcation Verification ($l_1 > 0$)**| [`results/phase4c3/phase4c3_hopf_independent_checks.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_hopf_independent_checks.csv) | Audited |
| **Bistability Open Intervals & Folds** | [`results/phase4c3/phase4c3_bistability_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_bistability_verification.csv) | Audited |
| **Fold Extinction Verification** | [`results/phase4c3/phase4c3_fold_verification.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4c3/phase4c3_fold_verification.csv) | Audited |
| **Pop D Exploratory Scan (625 pts)** | [`results/phase4b1/fhn_population_d_pareto_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b1/fhn_population_d_pareto_audit.csv) | Audited |
| **Pop D Refined Scan (961 pts raw)** | [`results/phase4b2/fhn_population_d_grid_points.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/fhn_population_d_grid_points.csv) | Audited |
| **Pop D Refined Pareto Envelope** | [`results/phase4b2/fhn_population_d_refined_pareto.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4b2/fhn_population_d_refined_pareto.csv) | Audited |
| **Handoff & Caveats Document** | [`results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md) | Verified |

---

*Synthesis completed on 2026-11-08 under INCM Phase 5B mandate. All findings adhere to non-negotiable scientific protections and are grounded directly in serialized repository artifacts.*

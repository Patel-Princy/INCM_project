# PHASE 3C — FITZHUGH–NAGUMO (FHN) READINESS SPECIFICATION

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3C — Independent Scientific Consistency Audit and Phase 3B Results Correction  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  
**Purpose:** Define the mathematical, biophysical, computational, and scientific specification for Phase 4 (FHN Model Calibration and Evaluation). **No implementation is performed in this phase.**

---

## 1. Research Question and Dimensional Reduction Objective

The fundamental research question is:
> *How much biological detail does a neuron model need to reproduce a real neuron's electrophysiological behaviour, and which behaviours are preserved or lost when a detailed conductance-based model is reduced to a FitzHugh–Nagumo (FHN) model?*

To answer this question rigorously:
1. The reduced model must be calibrated **strictly on the identical calibration sweeps** used for the detailed perisomatic models in Phase 3A:
   - **Population A (VISp L4, Specimen 484564503):** Sweep 49 ($+370.0\text{ pA}$)
   - **Population B (VISp L2/3, Specimen 318808427):** Sweep 40 ($+190.0\text{ pA}$)
   - **Population C (VISp L5, Specimen 471129934):** Sweep 51 ($+410.0\text{ pA}$)
   - **Population D (VISp L6a, Specimen 471786879):** Sweep 42 ($+250.0\text{ pA}$)
2. The calibrated FHN models must then be evaluated **out-of-sample across the exact same 109 held-out sweeps** evaluated in Phase 3B.
3. The comparison between detailed models and FHN models must use **identical metric definitions and evaluation criteria**.

---

## 2. Mathematical Formulation of the 2D FitzHugh–Nagumo Model

### 2.1 Dimensional (Biophysical Unit) Formulation
To enable direct point-by-point comparison with biological recordings without arbitrary re-scaling, the FHN model is formulated in physical units (millivolts, picoamperes, milliseconds):

$$
C_m \frac{dV}{dt} = - g_L (V - V_{\text{rest}}) + k_v (V - V_{\text{rest}})(V - V_{\text{th}})(V_{\text{peak}} - V) - w + I_{\text{stim}}(t)
$$

$$
\tau_w \frac{dw}{dt} = a_w (V - V_{\text{rest}}) - w
$$

Where:
- $V(t)$: Somatic membrane potential ($\text{mV}$).
- $w(t)$: Slow recovery / adaptation current ($\text{pA}$).
- $I_{\text{stim}}(t)$: Injected current waveform ($\text{pA}$).
- $C_m$: Apparent somatic capacitance ($\text{pF}$).
- $g_L$: Passive leak conductance ($\text{nS}$).
- $V_{\text{rest}}$: Resting membrane potential ($\text{mV}$).
- $V_{\text{th}}$: Apparent voltage threshold parameter ($\text{mV}$).
- $V_{\text{peak}}$: Peak action potential depolarization parameter ($\text{mV}$).
- $k_v$: Cubic non-linearity scaling coefficient ($\text{nS/mV}^2$).
- $\tau_w$: Recovery variable time constant ($\text{ms}$).
- $a_w$: Recovery-to-voltage coupling conductance ($\text{nS}$).

### 2.2 Classical Rescaled Dimensionless Formulation
Alternatively, the canonical dimensionless FitzHugh-Nagumo formulation can be employed with an explicit affine coordinate mapping:

$$
\tau_v \frac{dv}{dt} = v - \frac{v^3}{3} - w + \gamma I_{\text{stim}}(t)
$$

$$
\tau_w \frac{dw}{dt} = \epsilon (v + \alpha - \beta w)
$$

With physical readout mapping:
$$
V(t) = V_0 + \Delta V \cdot v(t)
$$
Where $V_0$ is the baseline voltage offset ($\text{mV}$) and $\Delta V$ is the action potential voltage scale ($\text{mV}$).

---

## 3. Biophysical Capabilities and Intrinsic Limitations of 2D FHN

### 3.1 What a 2D FHN Model Can Reproduce:
1. **Resting Potential ($V_{\text{rest}}$):** Stable fixed point $(V^*, w^*)$ at $I_{\text{stim}} = 0$.
2. **Subthreshold Input Resistance ($R_{\text{in}}$):** Linear slope of steady-state $V$-$I$ curve around rest:
   $$
   R_{\text{in}} = \left. \frac{dV}{dI} \right|_{I=0} = \frac{1}{g_L + a_w}
   $$
3. **Membrane Time Constant ($\tau_m$):** Effective capacitive charging time $\tau_m = C_m / (g_L + a_w)$.
4. **All-or-None Excitation:** Threshold transition from subthreshold damped oscillation to large-amplitude limit cycle.
5. **Periodic Repetitive Spiking:** Sustained limit cycle firing under steady depolarizing current.

### 3.2 What a 2D FHN Model CANNOT Reproduce (A Priori Limitations):
1. **Dendritic Spatial Cable Filtering:** FHN is a single-compartment isopotential point model ($0\text{D}$). It cannot account for distance-dependent dendritic attenuation or non-uniform channel distributions.
2. **True Spiking Waveform Details:** FHN action potentials have broad downstrokes and shallow afterhyperpolarizations (AHPs) because recovery $w$ operates on a single timescale ($\tau_w$). It cannot decouple the fast sodium downstroke ($< 1\text{ ms}$) from slow potassium AHPs ($> 50\text{ ms}$).
3. **Multi-Timescale Spike Frequency Adaptation:** In 2D FHN, the limit cycle is two-dimensional; once the orbit is entered, inter-spike intervals (ISIs) reach steady-state within 1–2 cycles. Real visual cortical neurons exhibit adaptation across hundreds of milliseconds.
4. **Late-Step Spike Cessation / Depolarization Block:** As observed in L4 (Specimen 484564503), the biological neuron ceases firing midway through a large depolarizing step. A standard 2D FHN model with a monotonic limit cycle will fire indefinitely for the duration of the current pulse unless an auxiliary slow variable drives the state out of the limit cycle.

### 3.3 Scientifically Justified Extension: Adaptive 3D FHN (AdFHN)
If the standard 2D FHN model fails to capture the multi-spike adaptation or cessation observed in cortical neurons, the designated scientific extension is a **3-variable Adaptive FHN (AdFHN)**:
$$
\tau_u \frac{du}{dt} = a_u (V - V_{\text{rest}}) - u
$$
where $u(t)$ is an ultra-slow adaptation current ($\tau_u \approx 200 - 1000\text{ ms}$) added to the voltage equation: $- w - u$.
*(Note: Phase 4 will evaluate standard 2D FHN first to maintain baseline fidelity before introducing extensions).*

---

## 4. Excitability and Bifurcation Selection

The choice of bifurcation structure determines the frequency-current ($F$-$I$) onset characteristics:
- **Type I Excitability (Saddle-Node on Invariant Circle - SNIC):** Firing frequency emerges continuously from zero frequency ($f \to 0$ as $I \to I_{\text{rheo}}^+$).
- **Type II Excitability (Hopf Bifurcation):** Firing frequency emerges with a non-zero jump ($f > f_{\text{min}} > 0$ at onset).

### Empirical Constraint from Phase 3B:
- Populations B (L2/3) and D (L6a) exhibit low-frequency onset ($1 - 5\text{ Hz}$ near rheobase), characteristic of Type I dynamics.
- Standard cubic FHN models with symmetrical nullclines default to Hopf bifurcations (Type II). To prevent severe rheobase overestimation, the FHN calibration must allow nullcline geometry adjustments (or asymmetry) so that firing onset is not forced into high-frequency discontinuous jumps.

---

## 5. Multi-Component Loss Function for FHN Calibration

To prevent a single metric (e.g. point-by-point voltage RMSE) from dominating the optimization at the expense of firing rate and excitability, calibration must minimize an explicit **multi-component weighted loss function**:

$$
\mathcal{L}_{\text{calib}}(\theta) = \lambda_{\text{rest}} \mathcal{L}_{\text{rest}} + \lambda_{\text{sub}} \mathcal{L}_{\text{sub}} + \lambda_{\text{spk}} \mathcal{L}_{\text{spk}} + \lambda_{\text{lat}} \mathcal{L}_{\text{lat}} + \lambda_{\text{shape}} \mathcal{L}_{\text{shape}}
$$

### Component Definitions:
1. **Resting Potential Error ($\mathcal{L}_{\text{rest}}$):**
   $$
   \mathcal{L}_{\text{rest}} = \left( \frac{V_{\text{rest}}^{\text{sim}} - V_{\text{rest}}^{\text{rec}}}{\sigma_V} \right)^2, \quad \sigma_V = 1.0\text{ mV}
   $$
2. **Subthreshold Input Resistance Error ($\mathcal{L}_{\text{sub}}$):**
   $$
   \mathcal{L}_{\text{sub}} = \left( \frac{R_{\text{in}}^{\text{sim}} - R_{\text{in}}^{\text{rec}}}{\sigma_R} \right)^2, \quad \sigma_R = 10.0\text{ M}\Omega
   $$
3. **Spike Count Delta on Calibration Sweep ($\mathcal{L}_{\text{spk}}$):**
   $$
   \mathcal{L}_{\text{spk}} = \left( \frac{N_{\text{spk}}^{\text{sim}} - N_{\text{spk}}^{\text{rec}}}{\max(1, N_{\text{spk}}^{\text{rec}})} \right)^2
   $$
4. **First-Spike Latency Delta ($\mathcal{L}_{\text{lat}}$):**
   $$
   \mathcal{L}_{\text{lat}} = \left( \frac{t_{\text{first}}^{\text{sim}} - t_{\text{first}}^{\text{rec}}}{\sigma_{\text{lat}}} \right)^2, \quad \sigma_{\text{lat}} = 5.0\text{ ms}
   $$
5. **Waveform Correlation / Shape ($\mathcal{L}_{\text{shape}}$):**
   $$
   \mathcal{L}_{\text{shape}} = 1.0 - r(V^{\text{sim}}, V^{\text{rec}})
   $$

### Justified Default Weighting:
- $\lambda_{\text{rest}} = 1.0$ (Must settle at biological baseline).
- $\lambda_{\text{sub}} = 1.0$ (Must preserve passive input resistance).
- $\lambda_{\text{spk}} = 2.0$ (Firing count at calibration amplitude is critical).
- $\lambda_{\text{lat}} = 0.5$ (Onset latency constraint).
- $\lambda_{\text{shape}} = 0.5$ (Trajectory guidance).

---

## 6. Numerical Integration, Stability, and Failure Criteria

### 6.1 Numerical Scheme
- Fixed-step 4th-order Runge-Kutta (RK4) or adaptive Dormand-Prince (RK45) with time step $\Delta t \le 0.05\text{ ms}$ (matching the experimental sampling rate $200\text{ kHz} \implies 0.005\text{ ms}$, downsampled to $20\text{ kHz}$ for numerical integration).
- Must avoid Euler forward integration due to stiffness near cubic fold points.

### 6.2 Programmatic Model Failure Criteria
A candidate parameter set $\theta$ is flagged as **FAILED** if:
1. Voltage diverges ($|V(t)| > 200\text{ mV}$ or `NaN` / `Inf`).
2. Spontaneous spiking occurs at $I_{\text{stim}} = 0$ (unstable resting equilibrium).
3. The model exhibits runaway high-frequency firing ($f > 200\text{ Hz}$).
4. Jacobian eigenvalues at rest have positive real parts ($\text{Re}(\lambda) > 0$).

---

## 7. Direct Comparison Methodology with Detailed Models

When Phase 4 evaluates FHN models on the 109 held-out sweeps, the resulting data must be formatted identically to [`results/phase3b/heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv):
- `fhn_metrics.csv` containing identical column names:
  `specimen_id, population, layer, sweep_number, stimulus_amplitude_pa, baseline_delta_mv, rmse_overall_mv, mae_mv, correlation, spike_count_simulated_in_step, spike_count_delta, first_spike_simulated_ms`.
- Direct statistical comparison across:
  1. F-I curve slope $df/dI$ (Detailed vs FHN vs Recorded).
  2. Rheobase interval midpoint $\hat{I}_{\text{rheo}}$ (Detailed vs FHN vs Recorded).
  3. Mean Absolute Error and RMSE.
  4. Number of parameters (Detailed: $> 30$ spatial & conductance parameters vs FHN: $5-7$ parameters).
  5. Computational speedup (wall-clock execution time per second of biological time).

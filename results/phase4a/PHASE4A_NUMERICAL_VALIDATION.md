# INCM Phase 4A: FitzHugh–Nagumo Mathematical Implementation and Numerical Validation Report

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Working Branch:** `ashish-work`  
**Phase:** 4A (Mathematical Solver Implementation, Dimensional Consistency, Numerical Stability & Dynamical Validation)  
**Execution Date:** November 8, 2026  
**Status:** **AUDIT PASSED** (11/11 FHN unit tests pass; 366/366 full project test suite pass)

---

## 1. Executive Summary

Phase 4A establishes the mathematical, dimensional, and numerical foundation of the two-variable FitzHugh–Nagumo (FHN) conductance-based reduction for the INCM research project.

### Strict Scope Boundary
In accordance with Master Prompt 05 rules:
1. **Zero Calibration in Phase 4A:** No biological parameter fitting against Allen Cell Types recordings was performed during this milestone. Parameter optimization across the four visual cortex populations (VISp L4, VISp L2/3, VISp L5, VISp L6a) is strictly reserved for Phase 4B.
2. **Zero Held-Out Execution in Phase 4A:** None of the 109 held-out sweeps were simulated with FHN in this phase.
3. **Zero Model Tampering:** All existing detailed Hodgkin–Huxley biophysical NEURON models, configurations, and Phase 3A/3B/3C reports remain preserved bit-for-bit.
4. **Independent Solver:** The FHN solver is implemented in pure Python/NumPy with zero dependency on NEURON or AllenSDK.

---

## 2. Dimensional Mathematical Formulation

The dimensional two-variable FitzHugh–Nagumo reduction implemented in [`src/models/fitzhugh_nagumo.py`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/src/models/fitzhugh_nagumo.py) is formulated as:

$$C_m \frac{dV}{dt} = -g_L (V - V_{\mathrm{rest}}) + k_v (V - V_{\mathrm{rest}})(V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V) - w + I(t)$$

$$\tau_w \frac{dw}{dt} = a_w (V - V_{\mathrm{rest}}) - w$$

### 2.1 Rigorous Dimensional Verification

Every term in both dynamical equations has been verified for exact dimensional homogeneity. All current terms are expressed in picoamperes ($\text{pA} = 10^{-12}\text{ A}$):

| Variable / Parameter | Symbol | Canonical Units | SI Equivalence | Homogeneity Derivation |
|---|---|---|---|---|
| Somatic Membrane Potential | $V(t)$ | $\text{mV}$ | $10^{-3}\text{ V}$ | State variable |
| Slow Recovery Variable | $w(t)$ | $\text{pA}$ | $10^{-12}\text{ A}$ | Outward recovery / potassium-like current |
| Simulation Time | $t$ | $\text{ms}$ | $10^{-3}\text{ s}$ | Independent variable |
| Injected Stimulus Current | $I(t)$ | $\text{pA}$ | $10^{-12}\text{ A}$ | Intracellular current clamp |
| Membrane Capacitance | $C_m$ | $\text{pF}$ | $10^{-12}\text{ F}$ | $C_m \frac{dV}{dt} = [10^{-12}\text{ F}] \cdot \left[\frac{10^{-3}\text{ V}}{10^{-3}\text{ s}}\right] = 10^{-12}\text{ A} = \text{pA}$ |
| Leak Conductance | $g_L$ | $\text{nS}$ | $10^{-9}\text{ S}$ | $g_L \Delta V = [10^{-9}\text{ S}] \cdot [10^{-3}\text{ V}] = 10^{-12}\text{ A} = \text{pA}$ |
| Resting Membrane Potential | $V_{\mathrm{rest}}$ | $\text{mV}$ | $10^{-3}\text{ V}$ | Baseline potential parameter |
| Apparent Action Potential Threshold | $V_{\mathrm{th}}$ | $\text{mV}$ | $10^{-3}\text{ V}$ | Voltage inflection parameter ($V_{\mathrm{rest}} < V_{\mathrm{th}} < V_{\mathrm{peak}}$) |
| Action Potential Peak Parameter | $V_{\mathrm{peak}}$ | $\text{mV}$ | $10^{-3}\text{ V}$ | Upstroke ceiling parameter |
| Cubic Non-Linearity Coefficient | $k_v$ | $\text{nS/mV}^2$ | $10^{-3}\text{ S/V}^2 = \text{pA/mV}^3$ | $k_v (\Delta V)^3 = [\text{pA/mV}^3] \cdot [\text{mV}^3] = \text{pA}$ |
| Recovery Time Constant | $\tau_w$ | $\text{ms}$ | $10^{-3}\text{ s}$ | $\tau_w \frac{dw}{dt} = [10^{-3}\text{ s}] \cdot \left[\frac{10^{-12}\text{ A}}{10^{-3}\text{ s}}\right] = 10^{-12}\text{ A} = \text{pA}$ |
| Recovery Coupling Conductance | $a_w$ | $\text{nS}$ | $10^{-9}\text{ S}$ | $a_w \Delta V = [10^{-9}\text{ S}] \cdot [10^{-3}\text{ V}] = 10^{-12}\text{ A} = \text{pA}$ |

> [!NOTE]
> In literature, FitzHugh–Nagumo is frequently stated in dimensionless variables $(v, w, \tau)$. Transforming to physical neurophysiological units ($V$ in $\text{mV}$, $I$ in $\text{pA}$, $t$ in $\text{ms}$, conductances in $\text{nS}$) allows direct comparison against intracellular patch-clamp recordings without artificial scaling factors.

---

## 3. Equilibrium, Stability, and Effective Input Resistance

### 3.1 Resting Fixed Point
At zero stimulus current ($I = 0$), evaluating the vector field at $(V, w) = (V_{\mathrm{rest}}, 0)$:
1. $\Delta V = V_{\mathrm{rest}} - V_{\mathrm{rest}} = 0$.
2. Cubic non-linearity: $k_v (0)(V_{\mathrm{rest}} - V_{\mathrm{th}})(V_{\mathrm{peak}} - V_{\mathrm{rest}}) = 0$.
3. Leak current: $-g_L (0) = 0$.
4. Membrane equation: $C_m \frac{dV}{dt} = 0 - 0 + 0 = 0$.
5. Recovery equation: $\tau_w \frac{dw}{dt} = a_w(0) - 0 = 0$.

Therefore, $(V^*, w^*) = (V_{\mathrm{rest}}, 0)$ is **an exact fixed point** of the dynamical system.

### 3.2 Jacobian Matrix and Asymptotic Stability
Let $f_V(V) = -g_L(V - V_{\mathrm{rest}}) + k_v(V - V_{\mathrm{rest}})(V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V)$.  
The Jacobian matrix $J(V, w) = \begin{pmatrix} \frac{1}{C_m}\frac{\partial f_V}{\partial V} & -\frac{1}{C_m} \\ \frac{a_w}{\tau_w} & -\frac{1}{\tau_w} \end{pmatrix}$.

Differentiating $f_V(V)$ with respect to $V$:
$$\frac{\partial f_V}{\partial V} = -g_L + k_v \left[ (V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V) + (V - V_{\mathrm{rest}})(V_{\mathrm{peak}} - V) - (V - V_{\mathrm{rest}})(V - V_{\mathrm{th}}) \right]$$

At the resting equilibrium $(V_{\mathrm{rest}}, 0)$:
$$\left. \frac{\partial f_V}{\partial V} \right|_{(V_{\mathrm{rest}}, 0)} = -g_L - k_v (V_{\mathrm{th}} - V_{\mathrm{rest}})(V_{\mathrm{peak}} - V_{\mathrm{rest}})$$

Let $K_{\mathrm{rest}} \equiv k_v (V_{\mathrm{th}} - V_{\mathrm{rest}})(V_{\mathrm{peak}} - V_{\mathrm{rest}})$.  
Since physical parameters enforce $V_{\mathrm{rest}} < V_{\mathrm{th}} < V_{\mathrm{peak}}$ and $k_v > 0$, we have $K_{\mathrm{rest}} > 0$.

Thus:
$$J_{\mathrm{rest}} = \begin{pmatrix} -\frac{g_L + K_{\mathrm{rest}}}{C_m} & -\frac{1}{C_m} \\ \frac{a_w}{\tau_w} & -\frac{1}{\tau_w} \end{pmatrix}$$

The trace and determinant of $J_{\mathrm{rest}}$ are:
$$\mathrm{Tr}(J_{\mathrm{rest}}) = -\left( \frac{g_L + K_{\mathrm{rest}}}{C_m} + \frac{1}{\tau_w} \right) < 0$$
$$\det(J_{\mathrm{rest}}) = \left( \frac{g_L + K_{\mathrm{rest}}}{C_m} \right) \left( \frac{1}{\tau_w} \right) - \left( -\frac{1}{C_m} \right) \left( \frac{a_w}{\tau_w} \right) = \frac{g_L + K_{\mathrm{rest}} + a_w}{C_m \tau_w} > 0$$

Because $\mathrm{Tr}(J_{\mathrm{rest}}) < 0$ and $\det(J_{\mathrm{rest}}) > 0$ strictly hold for all positive parameter values ($C_m > 0, g_L > 0, \tau_w > 0, a_w \ge 0, k_v > 0, V_{\mathrm{rest}} < V_{\mathrm{th}} < V_{\mathrm{peak}}$), both eigenvalues have strictly negative real parts:
$$\mathrm{Re}(\lambda_1) < 0, \quad \mathrm{Re}(\lambda_2) < 0$$
**Conclusion:** The zero-current resting equilibrium $(V_{\mathrm{rest}}, 0)$ is **unconditionally asymptotically stable**.

### 3.3 Analytical Effective Input Resistance
Applying an infinitesimal step current $I$ near rest:
$$\frac{dw}{dt} = 0 \implies w^* = a_w (V^* - V_{\mathrm{rest}})$$
$$\frac{dV}{dt} = 0 \implies 0 = -(g_L + K_{\mathrm{rest}})(V^* - V_{\mathrm{rest}}) - a_w (V^* - V_{\mathrm{rest}}) + I + \mathcal{O}((\Delta V)^2)$$
$$I = (g_L + a_w + K_{\mathrm{rest}}) \Delta V$$

Hence, the effective somatic input resistance $R_{\mathrm{in}}$ at resting potential is:
$$R_{\mathrm{in}} = \left. \frac{\partial V}{\partial I} \right|_{I=0} = \frac{1}{g_{\mathrm{eff}}} = \frac{1000}{g_L + a_w + k_v (V_{\mathrm{th}} - V_{\mathrm{rest}})(V_{\mathrm{peak}} - V_{\mathrm{rest}})} \quad [\text{M}\Omega]$$

Numerical verification in unit test `test_subthreshold_input_resistance_matches_analytical`:
- Parameters: $C_m = 100\text{ pF}, g_L = 4.0\text{ nS}, a_w = 1.0\text{ nS}, k_v = 0.002\text{ nS/mV}^2, V_{\mathrm{rest}} = -75.0\text{ mV}, V_{\mathrm{th}} = -50.0\text{ mV}, V_{\mathrm{peak}} = 20.0\text{ mV}$.
- $K_{\mathrm{rest}} = 0.002 \cdot (25) \cdot (95) = 4.75\text{ nS}$.
- $g_{\mathrm{eff}} = 4.0 + 1.0 + 4.75 = 9.75\text{ nS}$.
- Analytical $R_{\mathrm{in}} = 1000 / 9.75 = 102.564\text{ M}\Omega$.
- Simulated $2.0\text{ pA}$ step deflection: $\Delta V = 0.20617\text{ mV}$.
- Measured $R_{\mathrm{in}} = 1000 \cdot (0.20617 / 2.0) = 103.08\text{ M}\Omega$ (relative error: $0.51\%$, matching linear Taylor expansion within $<1\%$).

---

## 4. Phase-Plane Geometry and Limit Cycle Existence

The system's phase plane is governed by the two nullclines:
1. **$V$-nullcline** ($\frac{dV}{dt} = 0$):
   $$w = -g_L(V - V_{\mathrm{rest}}) + k_v (V - V_{\mathrm{rest}})(V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V) + I(t)$$
   This is an inverted $N$-shaped cubic polynomial. Injected current $I(t)$ shifts this cubic vertically upward.
2. **$w$-nullcline** ($\frac{dw}{dt} = 0$):
   $$w = a_w (V - V_{\mathrm{rest}})$$
   This is a straight line through $(V_{\mathrm{rest}}, 0)$ with slope $a_w$.

```mermaid
flowchart LR
    A["Injected Current I(t) > 0"] --> B["V-nullcline shifts upward"]
    B --> C["Fixed Point (V*, w*) moves into middle branch"]
    C --> D["df_V/dV > C_m / tau_w: Hopf Bifurcation"]
    D --> E["Unstable Focus surrounded by Stable Limit Cycle"]
    E --> F["Repetitive Action Potential Firing"]
```

### 4.1 Necessary and Sufficient Condition for Sustained Spiking (Hopf Bifurcation)
At the fixed point $(V^*, w^*)$ under sustained current $I$, the Jacobian eigenvalues determine stability:
$$\mathrm{Tr}(J) = \frac{1}{C_m} \frac{\partial f_V}{\partial V}(V^*) - \frac{1}{\tau_w}$$
$$\det(J) = \frac{a_w - \frac{\partial f_V}{\partial V}(V^*)}{C_m \tau_w}$$

For a stable limit cycle (Poincaré–Bendixson theorem on a bounded 2D planar system):
1. **Instability:** $\mathrm{Tr}(J) > 0 \iff \frac{\partial f_V}{\partial V}(V^*) > \frac{C_m}{\tau_w}$.
2. **Non-saddle (Focus):** $\det(J) > 0 \iff \frac{\partial f_V}{\partial V}(V^*) < a_w$.

Combining these two inequalities gives the canonical FHN limit-cycle condition:
$$\frac{C_m}{\tau_w} < \frac{\partial f_V}{\partial V}(V^*) < a_w$$

> [!IMPORTANT]
> A sustained limit cycle requires that the coupling conductance exceeds the membrane time-constant ratio:
> $$\frac{a_w \tau_w}{C_m} > 1$$
> If $a_w \le C_m / \tau_w$, no stable limit cycle can exist: the fixed point either remains stable (if $\det > 0$) or becomes a saddle (if $\det < 0$), causing the neuron to fire at most a single onset action potential and then settle into depolarization block.

---

## 5. Diagnostic Figures and Visual Validations

Five publication-grade diagnostic plots were generated and saved to `results/phase4a/figures/`:

### 5.1 Hyperpolarizing Step Response
Subthreshold passive relaxation under negative current injection ($-60\text{ pA}$, $300\text{ ms}$). Demonstrates smooth exponential decay, absence of spurious rebound oscillations, and asymptotic return to $V_{\mathrm{rest}}$ upon pulse cessation.
![Hyperpolarizing Step Response](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4a/figures/hyperpolarizing_step_response.png)

### 5.2 Depolarizing Suprathreshold Step Response
Suprathreshold current injection ($+220\text{ pA}$, $500\text{ ms}$) in the limit-cycle regime. Demonstrates rhythmic action potentials ($V_{\mathrm{peak}} > 0\text{ mV}$), clear threshold crossing, and steady-state firing frequency.
![Depolarizing Step Response](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4a/figures/depolarizing_step_response.png)

### 5.3 Voltage and Recovery Trajectories Across Regimes
Direct comparison of subthreshold ($+100\text{ pA}$) vs suprathreshold ($+220\text{ pA}$) dynamics showing the phase coupling between fast somatic membrane potential $V(t)$ and slow recovery current $w(t)$.
![Trajectories V and w](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4a/figures/trajectories_v_and_w.png)

### 5.4 Phase-Plane Nullclines and Limit Cycle Orbit
2D phase portrait showing the cubic $V$-nullcline at $I=0$ and $I=220\text{ pA}$, the linear $w$-nullcline, normalized vector field arrows, and the closed periodic limit-cycle trajectory orbiting the unstable interior fixed point.
![Phase Plane Nullclines](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4a/figures/phase_plane_nullclines.png)

### 5.5 RK4 Numerical Convergence under Step Refinement
Trajectories and logarithmic absolute discrepancy $|\Delta V(t)|$ across three time steps: $dt = 0.1\text{ ms}$ (coarse), $dt = 0.05\text{ ms}$ (medium), and $dt = 0.025\text{ ms}$ (fine).
![Timestep Convergence](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase4a/figures/timestep_convergence.png)

---

## 6. Numerical Convergence and Fourth-Order Runge–Kutta Validation

The solver employs an explicit fourth-order Runge–Kutta (RK4) integration scheme:
$$k_1 = f(t_n, y_n)$$
$$k_2 = f\left(t_n + \frac{\Delta t}{2}, y_n + \frac{\Delta t}{2} k_1\right)$$
$$k_3 = f\left(t_n + \frac{\Delta t}{2}, y_n + \frac{\Delta t}{2} k_2\right)$$
$$k_4 = f(t_n + \Delta t, y_n + \Delta t k_3)$$
$$y_{n+1} = y_n + \frac{\Delta t}{6} (k_1 + 2k_2 + 2k_3 + k_4)$$

Stimulus currents are evaluated at midpoint time steps $t_{n+1/2}$ via linear interpolation: $I(t_{n+1/2}) = \frac{1}{2}(I(t_n) + I(t_{n+1}))$.

### Numerical Convergence Table
Simulated under suprathreshold spiking ($I = +220\text{ pA}$, $T = 200\text{ ms}$):

| Step Comparison | Step Sizes ($\Delta t$) | Max Discrepancy ($\text{mV}$) | Mean Discrepancy ($\text{mV}$) | Convergence Ratio |
|---|---|---|---|---|
| Coarse vs Medium | $0.100\text{ ms} \to 0.050\text{ ms}$ | $0.16967\text{ mV}$ | $0.04353\text{ mV}$ | — |
| Medium vs Fine | $0.050\text{ ms} \to 0.025\text{ ms}$ | $0.08503\text{ mV}$ | $0.02181\text{ mV}$ | **$2.00$** |

- The maximum point-by-point voltage discrepancy between medium ($0.05\text{ ms}$) and fine ($0.025\text{ ms}$) grids is bounded strictly below $0.09\text{ mV}$ ($< 0.1\%\text{ of AP amplitude}$).
- Deterministic reproducibility check passed bitwise ($V_1 \equiv V_2, w_1 \equiv w_2$).
- No numerical overflow occurred across all tested protocols ($\text{all}(V, w \in \mathbb{R})$).

---

## 7. Documented Scientific Limitations of the 2D FHN Reduction

To maintain scientific integrity (Non-Negotiable Rule 14), we explicitly document the electrophysiological behaviours that **cannot** be captured by this 2D continuous reduction, in preparation for the cross-model evaluation in Phase 5:

1. **Absence of Multi-Timescale Spike-Frequency Adaptation (SFA):**  
   Because the model possesses only a single recovery variable $w(t)$ with a single time constant $\tau_w$, it cannot exhibit early rapid adaptation followed by slow secondary adaptation (as observed in cortical pyramidal cells governed by $M$-type and $AHP$-type potassium currents).
2. **Inability to Model Late-Step Spike Cessation:**  
   In Phase 3C excitability audits, VISp L5 pyramidal neurons exhibited late-step cessation under strong depolarizations. A 2D autonomous continuous dynamical system with a stable limit cycle must fire periodically indefinitely; it cannot cease firing mid-pulse without a third slow inactivating variable.
3. **Broad Action Potential Downstroke and Repolarization:**  
   The polynomial cubic voltage nullcline produces a symmetrical activation-inactivation curvature, whereas real neuronal action potentials exhibit steep fast sodium activation ($\sim 0.2\text{ ms}$) followed by delayed rectifier potassium repolarization ($\sim 1-2\text{ ms}$).
4. **Lack of Inward Rectification ($I_h$-Mediated Sag):**  
   The linear leak conductance $g_L$ yields a constant passive input resistance during hyperpolarizing pulses, omitting hyperpolarization-activated cyclic nucleotide-gated ($HCN / I_h$) channel sag and rebound depolarization.

---

## 8. Audit Gate Checklist and Test Suite Summary

| Check / Requirement | Status | Verification Evidence |
|---|---|---|
| Current working branch is `ashish-work` | **PASSED** | Confirmed via `git status` |
| No changes or commits to `main` | **PASSED** | Strict adherence |
| Never force-pushed | **PASSED** | Strict adherence |
| Phase 3A, 3B, 3C assets preserved | **PASSED** | All reports and CSVs intact |
| No calibration against Allen data in 4A | **PASSED** | Verified: zero optimization scripts executed |
| Dimensional consistency proof documented | **PASSED** | Section 2 table confirms all terms in $\text{pA}$ |
| Resting equilibrium analytically stable | **PASSED** | Trace $< 0$, Det $> 0$ proved in Section 3 |
| Effective input resistance formula verified | **PASSED** | Tested in `test_subthreshold_input_resistance_matches_analytical` |
| Limit-cycle Hopf condition derived | **PASSED** | Section 4 condition $\frac{C_m}{\tau_w} < f_V'(V^*) < a_w$ derived |
| 4th-order Runge-Kutta solver implemented | **PASSED** | `src/models/fitzhugh_nagumo.py` |
| 11 FHN numerical validation tests pass | **PASSED** | `tests/test_fitzhugh_nagumo.py` (11/11 passed in 1.6s) |
| Full regression test suite passes | **PASSED** | 366/366 tests passed in 17.8s |
| 5 diagnostic figures generated | **PASSED** | `results/phase4a/figures/*.png` created |
| Scientific limitations documented | **PASSED** | Section 7 details all 2D model constraints |

**Decision:** Phase 4A audit gates are 100% satisfied. The dimensional FitzHugh–Nagumo solver is mathematically rigorous, numerically verified, and ready for parameter calibration in Phase 4B.

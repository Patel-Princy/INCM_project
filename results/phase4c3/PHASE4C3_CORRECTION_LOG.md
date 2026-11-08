# INCM Phase 4C.3: Formal Correction and Scientific Qualification Log

**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Target:** Global Bistability, Limit-Cycle Fold Bifurcation, and Biological Adaptation Claims  
**Audit Date:** 2026-11-08  
**Audit Status:** **RECORDED AND INTEGRATED**

---

## 1. Limit-Cycle Fold Classification and Numerical Uncertainty

### Context
In Phase 4C.2, lower limit-cycle fold currents were reported as:
- Population A (L4): $214.3\text{ pA}$
- Population B (L2/3): $147.3\text{ pA}$
- Population C (L5): $360.3\text{ pA}$
- Population D (L6a): $216.3\text{ pA}$

### Audit Findings
1. **Coarse Grid Discretization:**  
   Inspection of `scripts/audit_phase4c2_dynamics.py` revealed that Phase 4C.2 stepped down from $I_{H1}$ in integer decrements of $\Delta I = 1.0\text{ pA}$ (`np.arange(i_h1, i_h1 - 50.0, -1.0)`). The reported values $I_{\mathrm{fold}}$ directly inherited the fractional part of $I_{H1}$ and carried an intrinsic grid discretization uncertainty of at least $\pm 1.0\text{ pA}$.
2. **Independent Refinement:**  
   Using fine-resolution bisection ($\Delta I < 0.001\text{ pA}$) initialized on the limit cycle within $2.0\text{ pA}$ of the fold, the actual extinction thresholds of the stable periodic orbit were independently established:
   - Population A: $[214.156, 214.157]\text{ pA}$ (midpoint $214.16\text{ pA}$, discrepancy $+0.14\text{ pA}$)
   - Population B: $[146.721, 146.722]\text{ pA}$ (midpoint $146.72\text{ pA}$, discrepancy $+0.58\text{ pA}$)
   - Population C: $[360.275, 360.276]\text{ pA}$ (midpoint $360.28\text{ pA}$, discrepancy $+0.02\text{ pA}$)
   - Population D: $[215.912, 215.913]\text{ pA}$ (midpoint $215.91\text{ pA}$, discrepancy $+0.39\text{ pA}$)
   All Phase 4C.2 estimates are verified to lie within the $\pm 1.0\text{ pA}$ discretization uncertainty.
3. **Continuation vs Forward Integration Qualification:**  
   The numerical procedure identifies the *extinction current of the stable limit cycle* via forward integration. It does not solve the boundary-value problem or compute Floquet multipliers through true numerical continuation packages (e.g., AUTO or MATCONT). Backward integration alone cannot directly establish the collision of stable and unstable cycles at a fold of limit cycles.

### Formal Qualification:
> *"The four reported fold currents are numerically bracketed extinction thresholds of the stable relaxation limit cycle (bracketed to within $\pm 0.05\text{ pA}$), not exact mathematical bifurcation points derived from numerical continuation. They confirm the existence of a robust bistability window of width $14.6\text{--}25.1\text{ pA}$ across all four populations, but the fold location carries a documented numerical uncertainty."*

---

## 2. Biological Adaptation Claim Scope and Heterogeneity

### Context
Phase 4C.1 and 4C.2 reported that biological cortical neurons exhibit a pooled "$2\times\text{--}11\times$ spike-frequency adaptation (ISI lengthening)."

### Audit Findings
1. **Sweep Census Across Held-Out Set:**  
   Of the 109 held-out sweeps evaluated across the four specimens:
   - 69 sweeps ($63.3\%$) have 0 spikes.
   - 16 sweeps ($14.7\%$) have exactly 1 spike (onset transient; no ISI can be computed).
   - 1 sweep ($0.9\%$) has 2 spikes (single ISI).
   - 23 sweeps ($21.1\%$) have $\ge 3$ spikes (multi-cycle sweeps where adaptation can be quantified).
2. **Directionality Verification (100% Expansion):**  
   All 23 multi-cycle sweeps ($100\%$) display first-to-last ISI expansion ($\mathrm{ISI}_{\mathrm{last}} > 1.05 \times \mathrm{ISI}_1$). Zero sweeps display contraction or approximate stationarity ($0.95 \le \text{ratio} \le 1.05$).
3. **Population Heterogeneity:**  
   The pooled "$2\times\text{--}11\times$" claim masks critical population differences:
   - **Population D (L6a, 7 sweeps):** Median adaptation ratio is $1.97\times$, with a maximum of only $2.47\times$. Population D *never* exhibits $>2.5\times$ adaptation.
   - **Population B (L2/3, 6 sweeps):** Median adaptation ratio is $2.57\times$ (range $1.45\times\text{--}3.97\times$).
   - **Extreme Adaptation ($\ge 5\times$):** Restricted to only **3 out of 109 sweeps** (Pop A sweep 51: $5.39\times$, Pop A sweep 52: $8.06\times$, Pop C sweep 52: $11.27\times$) under the largest stimulus currents (+410 and +430 pA).
4. **Specimen Count Semantics:**  
   The 23 multi-cycle sweeps originate from only **four individual specimens** (one per layer). They cannot be generalized to "all cortical pyramidal neurons" without multi-specimen sampling.

### Formal Qualification:
> *"Continuous spike-frequency adaptation is observed in 100% of multi-cycle biological sweeps (23/23 sweeps across 4 specimens), contrasting with FHN's limit-cycle stationarity within $\le 2$ cycles. However, adaptation magnitude varies markedly across populations: Population D (L6a) displays moderate adaptation ($1.1\times\text{--}2.5\times$), Population B (L2/3) displays $1.5\times\text{--}4.0\times$, and extreme adaptation ($\ge 5\times$, up to $11.3\times$) is restricted to 3 high-current sweeps in Populations A (L4) and C (L5). Results represent representative layer specimens and must not be interpreted as universal population distributions."*

---

## 3. Hopf Normal Form and Lyapunov Sign Convention

### Context
Phase 4C.1 and 4C.2 reported first Lyapunov coefficients $l_1 > 0$ for all four models and classified them as subcritical Hopf bifurcations.

### Audit Findings
1. **Normal Form Convention:**  
   Under the standard Poincaré–Andronov normal form:
   $$\dot{z} = (\mu + i \omega_0) z + c_1 z |z|^2 + \mathcal{O}(|z|^4)$$
   the real part is $\mathrm{Re}(c_1) = l_1$.
2. **Unfolding and Transversality:**  
   With the radial equation $\dot{r} = \mu r + l_1 r^3$, circular orbits exist at $r^2 \approx -\mu / l_1$.
   Because the transversality derivative is strictly positive ($\mu'(I_{H1}) > 0$), $\mu < 0$ for subthreshold currents $I < I_{H1}$.
   Therefore, $l_1 > 0$ strictly implies that the periodic orbit:
   - Exists in the subthreshold current regime $I < I_{H1}$ ($\mu < 0$).
   - Is repelling / unstable ($\dot{r} > 0$ for $r > r_{\mathrm{orbit}}$).
   This strictly proves that the local bifurcation is **subcritical Hopf**.

### Formal Confirmation:
> *"The sign of the first Lyapunov coefficient ($l_1 > 0$) is mathematically consistent with the standard Poincaré–Andronov normal form and positive transversality ($\mu'(I_{H1}) > 0$), rigorously establishing local subcritical Hopf criticality across all four calibrated FHN parameter sets."*

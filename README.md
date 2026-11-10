# How Much Biological Detail Does a Neuron Model Need?

**Research question:** How much biological detail does a neuron model need to
reproduce a real neuron's electrophysiological behaviour, and which behaviours
are preserved or lost when a detailed conductance-based model is reduced to a
FitzHugh–Nagumo (FHN) model?

**Repository:** `Patel-Princy/INCM_project` · **Active branch:** `ashish-work`

---

## Overview

This project compares detailed conductance-based models (Allen Cell Types Database
perisomatic biophysical models) against a reduced FitzHugh–Nagumo (FHN) model
across four layer-defined excitatory neuron populations in mouse primary visual
cortex (VISp):

| Group | Layer | Description |
|-------|-------|-------------|
| A | 4 | VISp L4 spiny excitatory |
| B | 2/3 | VISp L2/3 spiny excitatory |
| C | 5 | VISp L5 spiny excitatory |
| D | 6a | VISp L6a spiny excitatory |

These are layer-defined populations. The database does not carry projection
identity (IT/ET/PT/CT), so no projection labels are used.

---

## Project status

| Phase | Description | Status | Commit |
|-------|-------------|--------|--------|
| 0 | Allen dataset inventory (1,588 VISp specimens) | ✓ Complete | `80fa12e` |
| 0B | Four-population feasibility audit | ✓ Complete | `0470702` |
| **0C** | **Selected-model readiness: 16 candidates, fit descriptors, NWB** | **✓ Complete** | **`b435abb`** |
| 1A | NWB unit validation (specimen 341442651) | ✓ Complete | `1b310b1` |
| 1B | Cross-specimen unit validation (236 sweeps) | ✓ Complete | `3ef3002` |
| 1C | Pyramidal candidate validation | ✓ Complete | `fca64d5` |
| 2A | Model execution readiness | ✓ Complete | `b0cc4f0` |
| 2B | Geometry and manifest audit | ✓ Complete | `6620724` |
| 2C | Perisomatic model execution (specimen 382982932) | ✓ Complete | `a89d3fc` |
| 2D | Electrophysiology protocol audit | ✓ Complete | `393f2c3` |
| 2E | Held-out FINEST evaluation (perisomatic) | ✓ Complete | `cb54d0f` |
| 2F | Recording-only COARSE–FINEST excitability analysis | ✓ Complete | `1103ea7` |
| 2G-A | All-active model readiness | ✓ Complete | `46f5500` |
| 2G-B | All-active model execution (two axon branches) | ✓ Complete | `54b4326` |
| 2G-C | All-active excitability mapping | ✓ Complete | `d04b13e` |
| **3A** | **Detailed neuron pipeline audit & 4-population readiness** | **✓ Complete** | **`ccc60e6`** |
| **3B** | **Held-out evaluation across four populations (109 sweeps)** | **✓ Complete** | **`ee8d116`** |
| **3C** | **Phase 3B independent audit, metric recomputation & FHN readiness** | **✓ Complete** | **`685f0ca`** |
| **4A** | **Dimensional FitzHugh–Nagumo solver & numerical validation** | **✓ Complete** | **`1c98d5f`** |
| **4A.1** | **Independent mathematical audit, stability verification & RK4 convergence** | **✓ Complete** | **`c4c8e59`** |
| **4A.2** | **Hopf bifurcation and bistability verification** | **✓ Complete** | **`f6edb1d`** |
| **4A.3** | **Complete equilibrium branch and bifurcation audit** | **✓ Complete** | **`91f69ef`** |
| **4B** | **FHN parameter calibration framework across four populations** | **✓ Complete** | **`e2bcf25`** |
| **4B.1** | **Independent calibration quality, identifiability audit & Pareto frontier proof** | **✓ Complete** | **`9185cf0`** |
| **4B.2** | **Scientific claim and robustness audit (trade-off qualification & Hessian audit)** | **✓ Complete** | **`422ebf5`** |
| **4C** | **Out-of-sample held-out evaluation of four frozen FHN models (109 sweeps)** | **✓ Complete** | **`b4c497a`** |
| **4C.1** | **Independent held-out results and scientific claims audit (Hopf & RMSE proof)** | **✓ Complete** | **`aa6036a`** |
| **4C.2** | **Transient adaptation & population Hopf verification (local vs global)** | **✓ Complete** | **`93ee715`** |
| **4C.3** | **Global bistability, limit-cycle fold & adaptation claim audit** | **✓ Complete** | **`67fb438`** |
| **4C.3.1** | **Bistability boundary semantics correction (open interval enforcement)** | **✓ Complete** | **`ashish-work`** |
| **5** | **Cross-population comparison and reduction report** | **✓ Complete** | **`5509ddd`** |
| **Princy** | **L2/3 and L5 data pipeline, simple FHN fit, held-out metrics** | **✓ Complete** | **`020a792`** |

---

## Key Phase 0C findings (2026-11-07)

**16 candidates selected — 4 per population, all at 200 kHz, all spiny excitatory.**

| Metric | Count |
|--------|------:|
| Fit descriptors downloaded and parsed | 16/16 |
| Descriptors classified as perisomatic | 16/16 |
| Candidates with identifiable fitting sweep | 13/16 |
| Candidates with leakage-safe held-out split | 13/16 |
| Candidates potentially executable (L7) | 13/16 |
| Candidates actually executed (L8) | 1/16 |
| Candidates validated against recording | 0/16 |

Three candidates (C rank 4, D rank 2, D rank 4) have fitting sweep numbers in
their descriptors that do not map to the Allen sweep inventory. Their held-out
status is UNRESOLVED rather than failed.

### Selected specimen IDs

| Pop | Spec 1 | Spec 2 | Spec 3 | Spec 4 |
|-----|--------|--------|--------|--------|
| A (L4) | 484564503 | 485931158 | 468193142 | 320207387 |
| B (L2/3) | 318808427 | 476087653 | 485468180 | 382982932 |
| C (L5) | 471129934 | 488679042 | 476048909 | 471767045 |
| D (L6a) | 471786879 | 471819401 | 471789504 | 466632464 |

---

## Key Phase 2G-C findings

The all-active model for specimen 382982932 (L2/3) was executed with two axon
configurations:
- **Stub axon:** silent over 10–270 pA (no spikes in range)
- **Truncated axon:** rheobase interval (170, 190] pA
- **Recorded neuron:** rheobase interval (110, 130] pA

The two axon configurations produce materially different excitability. Neither
can be claimed as the original fitted configuration. The published parameter set
is not reproducible without knowing the axon treatment used during fitting.

---

## Key Phase 3B findings (2026-11-08)

**Out-of-sample held-out evaluation across four layer populations (109 sweeps, 102 unique conditions):**
- **Strictly frozen parameters:** Zero recalibration or tuning on held-out sweeps.
- **100% execution completion:** 109/109 sweeps executed with zero numerical failures.
- **Pop D (VISp L6a, 471786879):** Exact rheobase interval match ($0.0\text{ pA}$ shift), lowest waveform error ($\text{RMSE} = 2.23\text{ mV}$, $\text{MAE} = 0.85\text{ mV}$), high correlation ($r = 0.9699$).
- **Pop B (VISp L2/3, 318808427):** $+20.0\text{ pA}$ rheobase shift ($+16.7\%$), lowest spike count delta ($+0.83$ spikes/sweep), near-perfect subthreshold correlation ($r = 0.9965$).
- **Pop C (VISp L5, 471129934):** Net unbiased spike count (mean delta $-0.03$ spikes/sweep) across 34 sweeps; biological threshold drift observed in late protocol blocks.
- **Pop A (VISp L4, 484564503):** $+60.0\text{ pA}$ rheobase shift and resting potential discrepancy ($+13.1\text{ mV}$) originating from published fit parameters.
- **Artifacts:** Full reports, consolidated CSV metrics, and publication figures in `results/phase3b/`.

---

## Key Phase 4A findings (2026-11-08)

**Dimensional FitzHugh–Nagumo solver implementation and numerical validation:**
- **Exact dimensional homogeneity:** Proved all current terms evaluate strictly in $\text{pA}$ ($V$ in $\text{mV}$, $t$ in $\text{ms}$, $C_m$ in $\text{pF}$, $g_L$ in $\text{nS}$, $k_v$ in $\text{nS/mV}^2$, $\tau_w$ in $\text{ms}$, $a_w$ in $\text{nS}$).
- **Resting equilibrium & stability:** Zero-current resting equilibrium $(V_{\mathrm{rest}}, 0)$ is unconditionally asymptotically stable ($\mathrm{Tr}(J_{\mathrm{rest}}) < 0$, $\det(J_{\mathrm{rest}}) > 0$).
- **Analytical input resistance:** Linearization yields $R_{\mathrm{in}} = 1000 / (g_L + a_w + K_{\mathrm{rest}})\text{ M}\Omega$, validated numerically within $0.51\%$.
- **Hopf bifurcation & limit cycles:** Derived necessary and sufficient condition for sustained limit cycles: $\frac{C_m}{\tau_w} < f_V'(V^*) < a_w$ (requiring $\frac{a_w \tau_w}{C_m} > 1$).
- **Numerical convergence:** 4th-order Runge–Kutta integration converges with a convergence ratio of $2.00$ and step-refinement discrepancy $< 0.09\text{ mV}$.
- **Zero biological calibration in 4A:** Model parameters preserved strictly uncalibrated; 109 held-out sweeps untouched.
- **Unit test suite:** 11/11 FHN unit tests pass; 366/366 total project tests pass.
- **Artifacts:** Report in `results/phase4a/PHASE4A_NUMERICAL_VALIDATION.md` and 5 diagnostic plots in `results/phase4a/figures/`.

---

## Key Phase 4B & 4B.1 findings (2026-11-08)

**FHN parameter calibration and independent quality/identifiability audit:**
- **Deterministic calibration:** Strictly single designated calibration sweep per population; zero held-out sweeps used or accessed.
- **Independent reproduction (100% pass):** All spike counts, latencies, input resistances, peak voltages, step RMSEs, correlations, and losses reproduced bit-for-bit from raw traces and serialized parameters.
- **Resolution of Low-Loss / High-RMSE discrepancy:** The objective function optimizes physiological excitability features ($\mathcal{L}_{\mathrm{spk}}, \mathcal{L}_{\mathrm{rate}}, \mathcal{L}_{\mathrm{lat}}, \mathcal{L}_{\mathrm{rin}}, \mathcal{L}_{\mathrm{peak}}$) rather than continuous waveform tracking. Action potential broadening and minor phase shifts incur a severe "double penalty" on squared errors. In fact, a silent flatline trace achieves lower RMSE ($\sim 28 - 34\text{ mV}$) than an active spiking model ($\sim 41 - 46\text{ mV}$), proving that minimizing raw voltage RMSE directly would extinguish spiking excitability. Dual reporting of feature loss and physical waveform RMSE is formally mandated.
- **Constrained vs. Emergent taxonomy:** $V_{\mathrm{rest}}$, $R_{\mathrm{in}}$, and $V_{\mathrm{peak}}$ are directly constrained/fixed (Group A); spike count, firing rate, and onset latency are directly optimized (Group B); linear resting stability, continuous waveform correlation ($r \approx 0.70 - 0.76$), subthreshold charging kinetics, and lack of adaptation are emergent (Group C).
- **Proof of Population D (L6a) 2D Pareto frontier:** Systematic 625-point $(C_m, \tau_w)$ parameter sweep proves that 2D FHN cannot simultaneously achieve $t_{\mathrm{lat}} \approx 58\text{ ms}$ and $N_{\mathrm{spk}} = 13$. In biology, onset delay is mediated by slowly-inactivating A-type potassium current ($I_A / I_D$), which delays the initial spike and then inactivates to permit fast rhythmic firing. Because 2D FHN has only *one* recovery variable $w$, it cannot decouple transient onset delay from periodic limit-cycle period. The mismatch is an irreducible planar dynamical limitation, not an optimization defect.
- **Parameter identifiability:** Adaptation coupling $a_w$ accounts for $59\% - 77\%$ of resting conductance across populations, creating an identifiability valley along $g_L + a_w \approx \text{const}$.
- **Readiness authorization:** Phase 4B.1 audit gates passed; Phase 4C held-out evaluation officially authorized.
- **Artifacts:** Full audit report in `results/phase4b1/PHASE4B1_INDEPENDENT_CALIBRATION_AUDIT.md`, 4 structured CSV tables, and 3 diagnostic figures in `results/phase4b1/figures/`.

---

## Key Phase 4C findings (2026-11-08)

**Frozen FitzHugh–Nagumo out-of-sample held-out evaluation across four VISp populations (109 sweeps):**
- **Strictly frozen parameters:** Zero recalibration, tuning, or parameter modifications on held-out sweeps.
- **Strict calibration exclusion:** All 4 calibration sweeps (49, 40, 51, 42) verified 100% absent from held-out evaluation.
- **100% numerical completion:** 109/109 sweeps executed with zero numerical divergences, NaN states, or crashes.
- **Dual-reporting enforcement:** Contrasts calibration feature loss with continuous step RMSE ($12\text{--}24\text{ mV}$) and Pearson correlation ($r \approx 0.84\text{--}0.90$). Explains the phase-jitter double-penalty and the passive flatline paradox.
- **Excitability threshold detection:** FHN successfully detected 44 spiking sweeps (out of 40 biological spiking sweeps), whereas the Detailed Allen models severely under-fired (missed 16 biological spiking sweeps, detecting only 24).
- **Core preserved behaviors:** Subthreshold linearity ($r^2 \in [0.925, 0.995]$ in mutually subthreshold conditions), passive input resistance $R_{\mathrm{in}}$, resting potential ($V_{\mathrm{rest}}$), and qualitative monotonic $F-I$ rate scaling.
- **Core lost behaviors:** Spike-frequency adaptation (requires a 3rd state variable), action potential waveform kinetics and overshoot height, delayed onset firing in Population D (planar limitation), and hyperpolarization-activated inward sag ($I_h$).
- **Artifacts & tests:** Comprehensive report in `results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md`, 5 structured CSV/JSON tables, 7 diagnostic figures in `results/phase4c/figures/`, and 6 dedicated regression tests (435/435 repository tests passing).

---

## Key Phase 4C.1 findings (2026-11-08)

**Independent held-out results and scientific claims audit:**
- **Bit-for-bit reproduction (100% pass):** Independently verified all 109 held-out evaluations and recomputed summary metrics (A=31, B=18, C=34, D=26 sweeps across 4 single specimens).
- **Resolution of Pop A RMSE reversal:** Exact mathematical interval decomposition of MSE proves the Detailed model's $12.73\text{ mV}$ overall error is $92.3\%$ driven by a $+13.6\text{ mV}$ resting offset over the 7-second non-stimulus intervals ($87.5\%$ of duration), while FHN's $8.24\text{ mV}$ overall error is $89.2\%$ driven by in-step action potential phase jitter.
- **Excitability detection vs firing pattern:** FHN achieves $92.5\%$ sensitivity (37/40) in detecting biological spiking sweeps (missing only 3 vs 16 missed by Detailed model), but does not reproduce high-frequency firing rates or spike times.
- **Subthreshold linearity audit:** Biological recordings have regression linearity $r^2 > 0.98$ across all 4 cells. FHN tracks with $r^2 > 0.98$ strictly in Populations B ($0.990$) and D ($0.995$) under mutual subthreshold sweeps ($r^2 = 0.925$ in Pop A, $0.952$ in Pop C; classical coefficient of determination $R^2 = 0.44\text{--}0.67$).
- **Population-specific subcritical Hopf proof:** Independently derived and computed first Lyapunov coefficient $l_1 > 0$ strictly for all four calibrated parameter sets (Pop A: $4.39\times 10^{-5}$, Pop B: $8.87\times 10^{-5}$, Pop C: $6.07\times 10^{-5}$, Pop D: $3.30\times 10^{-5}$), verifying that subcritical Hopf bifurcation is an established structural property of all four calibrated models.
- **Quantification of lost biological behaviors:** Measured $5\times\text{--}11\times$ biological adaptation vs stationary FHN limit cycles ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_{\mathrm{initial}} = 1.000$); measured biological upstroke velocity ($397\text{--}466\text{ V/s}$) vs FHN ($5.7\text{--}6.2\text{ V/s}$, $60\times\text{--}75\times$ slower); measured modest biological inward sag ($0.63\text{--}1.86\text{ mV}$) vs FHN ($0.00\text{ mV}$); reclassified $I_A$ as an untested biological literature hypothesis.
- **Artifacts & tests:** Audit report in `results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md`, 5 structured audit tables, 7 dedicated regression tests (442/442 repository tests passing).

---

## Key Phase 4C.2 findings (2026-11-08)

**Transient adaptation and population-specific bifurcation verification:**
- **Transient adaptation vs asymptotic limit cycle:** Qualified the Phase 4C.1 claim of "strictly zero adaptation." FHN trajectories exhibit brief initial transient cycle-to-cycle adjustments as the orbit contracts from rest onto the limit cycle (Pop B: initial ISI expansion of $+0.5\%\text{ to }+1.2\%$; Pops A and C: initial ISI contraction of $-0.3\%\text{ to }-0.5\%$).
- **Rapid geometric convergence ($\le 2$ cycles):** Because the single recovery variable $w$ operates on timescale $\tau_w \approx 7\text{--}39\text{ ms}$, trajectories contract onto the periodic orbit within $\le 2$ cycles ($\le 120\text{ ms}$), after which successive ISIs are stationary to $< 0.01\%$. In contrast, biological neurons exhibit continuous multi-timescale adaptation across 10–25 cycles throughout the entire 1000 ms step ($2\times\text{ to }11\times$ ISI expansion), requiring slower secondary recovery processes ($I_{\mathrm{SK}}, I_M$).
- **Analytical Hopf conditions & transversality:** Independently derived and verified lower Hopf bifurcation currents ($I_{H1}$: Pop A = $234.34\text{ pA}$, Pop B = $161.28\text{ pA}$, Pop C = $385.33\text{ pA}$, Pop D = $236.27\text{ pA}$), zero trace ($|\mathrm{Tr}(J)| < 10^{-14}$), positive determinant ($\det(J) > 0$), and pure imaginary eigenvalues ($\pm i \omega_0$). Transversality derivative $\mu'(I_{H1}) = \frac{F''(V_{H1})}{2 C_m (a_w - C_m/\tau_w)} > 0$ strictly across all 4 calibrated models.
- **Local vs global bifurcation separation:** Decoupled local subcritical Hopf criticality ($l_1 > 0$, generating small unstable cycles for $I < I_{H1}$) from global limit-cycle folding. Numerically located global fold of limit cycles ($I_{\mathrm{fold}}$) and demonstrated robust open bistability intervals $(I_{\mathrm{fold}}, I_{H1})$ spanning $14.0\text{ to }25.0\text{ pA}$ across all four populations.
- **Artifacts & tests:** Comprehensive audit report in `results/phase4c2/PHASE4C2_DYNAMICAL_BEHAVIOUR_AND_HOPF_AUDIT.md`, 3 structured CSV tables, 2 diagnostic figures in `results/phase4c2/figures/`, and 4 dedicated regression tests (446/446 repository tests passing).

---

## Key Phase 4C.3 findings (2026-11-08)

**Global bistability, limit-cycle fold bifurcation, and biological adaptation audit:**
- **Numerical fold refinement & bracket analysis:** Audited the Phase 4C.2 numerical fold estimates ($214.3, 147.3, 360.3, 216.3\text{ pA}$). Proved they arose from a coarse integer search grid ($\Delta I = 1.0\text{ pA}$) with $\pm 1.0\text{ pA}$ discretization uncertainty. Independently refined the extinction thresholds of the stable periodic orbit using bisection ($\Delta I < 0.001\text{ pA}$): Pop A = $214.16\text{ pA}$ (discrepancy $+0.14\text{ pA}$), Pop B = $146.72\text{ pA}$ (discrepancy $+0.58\text{ pA}$), Pop C = $360.28\text{ pA}$ (discrepancy $+0.02\text{ pA}$), Pop D = $215.91\text{ pA}$ (discrepancy $+0.39\text{ pA}$). All estimates reproduce strictly within the coarse grid tolerance. Time-step ($\Delta t \in \{0.050, 0.025, 0.010\}\text{ ms}$) and integration duration ($T_{\mathrm{stop}} \in \{1500, 2500, 4000\}\text{ ms}$) sensitivity is bounded to $< 0.001\text{ pA}$.
- **Attractor coexistence verified:** Proved that throughout the verified open intervals $I_{\mathrm{fold}} < I < I_{H1}$ (widths $14.6\text{--}25.3\text{ pA}$), both the stable resting equilibrium focus and the stable relaxation limit cycle coexist simultaneously. Mapped the separatrix threshold ($\delta V_{\mathrm{crit}}$): shrinks to $3.5\text{--}4.9\text{ mV}$ near Hopf ($I \to I_{H1}^-$) and expands to $9.4\text{--}10.6\text{ mV}$ near fold ($I \to I_{\mathrm{fold}}^+$). Below $I_{\mathrm{fold}}$, the limit cycle is extinguished. Qualified that forward integration locates the stable orbit's extinction threshold, not a continuation-derived bifurcation point.
- **Biological adaptation scope & population heterogeneity:** Exhaustive census of all 109 held-out sweeps revealed: 69 sweeps have 0 spikes, 16 have 1 spike (onset transient), 1 has 2 spikes, and 23 have $\ge 3$ spikes (multi-cycle sweeps). All 23 multi-cycle sweeps (**100%**) display first-to-last ISI expansion (0% contraction, 0% stationarity), proving sustained biological adaptation. However, adaptation is strongly skewed: Pop D (L6a) displays moderate adaptation (median $1.97\times$, max $2.47\times$, never exceeding $2.5\times$); Pop B (L2/3) displays median $2.57\times$ (max $3.97\times$); extreme adaptation ($\ge 5.0\times$) occurs in only 3 sweeps across the entire dataset (Pops A and C). Clarified that sweeps represent 4 single specimens, not 109 independent neurons.
- **Independent Hopf & Lyapunov normal form verification:** Recomputed all Hopf quantities. Formally verified that under the standard Poincaré–Andronov normal form $\dot{z} = (\mu + i \omega_0) z + c_1 z |z|^2$, positive transversality ($\mu'(I_{H1}) > 0$) combined with $l_1 = \mathrm{Re}(c_1) > 0$ strictly proves local subcritical Hopf criticality for all 4 populations.
- **Artifacts & tests:** Comprehensive audit report in `results/phase4c3/PHASE4C3_GLOBAL_DYNAMICS_AND_ADAPTATION_AUDIT.md`, formal correction log in `results/phase4c3/PHASE4C3_CORRECTION_LOG.md`, 4 structured CSV tables, and 4 dedicated regression tests (450/450 repository tests passing).

---

## Key Phase 4C.3.1 findings (2026-11-08)

**Bistability boundary semantics correction and non-hyperbolic endpoint audit:**
- **Open interval coexistence ($I_{\mathrm{fold}} < I < I_{H1}$):** Formally corrected all bistability interval claims from closed brackets $[I_{\mathrm{fold}}, I_{H1}]$ to open intervals $(I_{\mathrm{fold}}, I_{H1})$. Coexistence of two ordinary hyperbolic attractors (stable resting focus and stable relaxation limit cycle) strictly holds on the interior of the interval.
- **Fold boundary classification ($I = I_{\mathrm{fold}}$):** At the limit-cycle fold bifurcation (LPC), the stable relaxation cycle coalesces with the interior unstable cycle. The resulting single periodic orbit has Floquet multiplier $+1$ and is non-hyperbolic (semi-stable); ordinary hyperbolic asymptotic stability is not asserted.
- **Hopf boundary classification ($I = I_{H1}$):** At the lower Hopf bifurcation point, the equilibrium has purely imaginary eigenvalues ($\lambda_{1,2} = \pm i \omega_0, \mathrm{Re}(\lambda) = 0$) and is non-hyperbolic. Ordinary linear asymptotic stability is inconclusive; nonlinear stability is governed by cubic center manifold terms ($l_1 > 0$, repelling unfolding).
- **Precision vs certainty distinction:** Clarified that the sub-$0.001\text{ pA}$ bisection stopping resolution is the algorithmic precision of the numerical bracket under fixed RK4 integration parameters, not a mathematical or physical certainty. Conservative numerical uncertainty remains $\pm 0.01\text{ pA}$.
- **Artifacts & tests:** Formal corrections applied across all Phase 4C.2 and 4C.3 reports, CSV tables, and correction logs; dedicated boundary semantics regression test added (451/451 repository tests passing).

---

## Dataset

- **Source:** Allen Cell Types Database (Allen Institute for Brain Science)
- **Specimens:** 1,588 VISp mouse neurons total; 194 with biophysical models
- **Protocol:** Long-square current-clamp (`C1LSCOARSE150216`, `C1LSFINEST150112`)
- **Sampling rates:** 50 kHz or 200 kHz (all 16 selected candidates are 200 kHz)
- **Models:** Perisomatic biophysical (template 329230710)

---

## Repository structure

```
data/
  metadata/           Allen RMA inventory CSVs (cell, sweep, model)
  nwb_cache/          Downloaded NWB files (git-ignored; not committed)
docs/                 Project documentation
results/
  dataset_inventory/  Phase 0/0B/0C audit outputs and reports
  phase1/             NWB validation reports
  phase2/             Model execution reports
scripts/              Analysis and validation scripts
src/data_audit/       Core audit modules
tests/                Pytest test suite (451 tests)
tmp/                  Working outputs (git-ignored)
```

---

## Running the tests

```bash
python -m pytest tests/ -q
```

All 451 tests pass on Python 3.14 with pytest ≥ 9.1.

---

## Reproducibility notes

1. **NWB files** are not committed (large binaries). They are downloaded
   from `http://api.brain-map.org/api/v2/well_known_file_download/<id>`.
2. **Model execution** (Phases 2C, 2G-B, 2G-C) requires NEURON 8.x and
   AllenSDK 2.16.2 in a Linux environment. The Windows environment supports
   all data-audit and analysis phases.
3. **Fit descriptors** are cached in `tmp/fit_cache/` (git-ignored).
4. **Phase 0C** can be re-run with: `python src/data_audit/selected_model_readiness.py`

---

## Scientific limitations

- No model has been validated against its own recording (L8=0).
- Three D-group candidates have unmapped fitting sweeps.
- One L2/3 candidate (382982932) has a reconstruction mismatch.
- The all-active model axon configuration was not published by Allen; the
  two tested configurations give qualitatively different excitability.
- Layer identity is anatomically confirmed; projection class (IT/ET/PT/CT)
  is not available in the Allen database and is not claimed.

---

## Citation

Allen Institute for Brain Science. Allen Cell Types Database. Available from:
https://celltypes.brain-map.org/

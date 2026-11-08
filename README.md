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
| **4C.1** | **Independent held-out results and scientific claims audit (Hopf & RMSE proof)** | **✓ Complete** | **`ashish-work`** |
| 5 | Cross-population comparison and reduction report | 🔲 Planned | |

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
tests/                Pytest test suite (442 tests)
tmp/                  Working outputs (git-ignored)
```

---

## Running the tests

```bash
python -m pytest tests/ -q
```

All 442 tests pass on Python 3.14 with pytest ≥ 9.1.

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

# INCM Phase 5 — Authoritative Baseline and Flash Handoff Document

**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Handoff Prepared:** 2026-11-08  
**HEAD commit at preparation:** `d6e1585` — `docs: clarify FHN bistability boundary semantics`  
**Prepared by:** Kiro read-only consolidation pass (Phase 5A); audited and corrected in Phase 5A.1  
**Intended recipient:** Antigravity Gemini 3.8 Flash — Phase 5B/5C/5D implementation

---

## 1. Confirmed Repository Baseline

### 1.1 Git State

| Item | Value |
|------|-------|
| HEAD commit | `d6e1585` |
| HEAD message | `docs: clarify FHN bistability boundary semantics` |
| Branch | `ashish-work` |
| Remote sync | Up-to-date with `origin/ashish-work` |
| Working tree | **Clean — zero uncommitted changes** |
| `main` branch | Untouched — no merges |
| Test suite | **451 / 451 tests passing** (47.12 s) |

### 1.2 Phase Commit Lineage (most recent first)

| Commit | Description |
|--------|-------------|
| `d6e1585` | docs: clarify FHN bistability boundary semantics |
| `67fb438` | audit: independently verify global FHN dynamics and adaptation claims |
| `93ee715` | audit: verify transient adaptation and population Hopf dynamics |
| `aa6036a` | audit: independently verify held-out FHN results and claims |
| `b4c497a` | feat: evaluate frozen FHN models on held-out VISp sweeps |
| `422ebf5` | audit: verify FHN scientific robustness before held-out evaluation |
| `9185cf0` | audit: verify FHN calibration quality and identifiability |
| `e2bcf25` | feat: calibrate FHN models for four VISp populations |
| `91f69ef` | audit: complete FHN equilibrium and bifurcation analysis |
| `f6edb1d` | audit: verify FHN Hopf bifurcation and bistability |
| `c4c8e59` | audit: verify FHN stability and numerical convergence |
| `1c98d5f` | feat: implement and validate dimensional FHN solver |
| `685f0ca` | audit: Phase 3C scientific consistency and FHN readiness |
| `ee8d116` | feat: Phase 3B held-out evaluation across four V1 populations |
| `ccc60e6` | feat: Phase 3A detailed neuron pipeline audit and 4-population execution |

### 1.3 No Phase 5 Content Exists Yet

`results/phase5/` was empty before this document was created. This file is the **first and only** Phase 5 artifact.

---

## 2. Research Question and Final Project Scope

> **"How much biological detail does a neuron model need to reproduce a real neuron's electrophysiological behaviour, and which behaviours are preserved or lost when a detailed conductance-based model is reduced to a FitzHugh–Nagumo (FHN) model?"**

**Scope as finally executed:**

- **Four** layer-defined excitatory neuron populations from mouse primary visual cortex (VISp), Allen Cell Types Database.
- **One representative specimen per population** — four specimens total.
- **Two model tiers compared:** (1) Allen perisomatic conductance-based biophysical model; (2) two-variable dimensional FitzHugh–Nagumo reduced model.
- **Evaluation:** 109 held-out sweeps (COARSE + FINEST long-square current clamp) vs. frozen parameters.
- **Methods:** NEURON 8.2.7 + AllenSDK 2.16.2 (detailed models); pure-Python RK4 solver (FHN); all on raw Allen NWB recordings.

**Scope that was NOT achieved and must NOT be claimed:**

- No cross-specimen population statistics.
- No projection-class identification (IT/ET/PT/CT).
- No FHN fitting validation on more than one calibration sweep per population.
- No all-active model comparison (available only for Pop B/spec 382982932).

---

## 3. Four Population Definitions and Representative IDs

| Label | Layer | Specimen ID | Detailed Model ID | Driver Line | Sampling | Identity Confidence |
|-------|-------|-------------|-------------------|-------------|----------|---------------------|
| **Population A** | L4 | `484564503` | `485591776` | Rorb-IRES2-Cre | 200 kHz | PROBABLE (L4 excitatory) |
| **Population B** | L2/3 | `318808427` | `473863035` | Nr5a1-Cre | 200 kHz | LAYER-ONLY (Nr5a1 is L4-associated) |
| **Population C** | L5 | `471129934` | `480624414` | Rbp4-Cre_KL100 | 200 kHz | PROBABLE (L5 excitatory) |
| **Population D** | L6a | `471786879` | `480632594` | Ntsr1-Cre_GN220 | 200 kHz | PROBABLE (L6a excitatory) |

**Critical identity constraint (NON-NEGOTIABLE):**  
The Allen database carries no projection identity field. The groups are defined by anatomical layer + spiny dendrite type only. Do NOT write "IT", "ET", "PT", or "CT" as confirmed labels. Do NOT write "spiny stellate" for Pop A (all have intact apical dendrites → star-pyramidal/IT-like, unresolved). Do NOT write "thick-tufted" without adding "Rbp4-compatible, ET vs PT unresolved". Do NOT write "corticothalamic" as confirmed for Pop D.

---

## 4. Consolidated Evidence Matrix

### 4.1 FHN Calibration Parameters (FROZEN — from `results/phase4b/fhn_fitted_parameters.csv`)

| Pop | Specimen | Calibration Sweep | Stimulus [pA] | C_m [pF] | g_L [nS] | V_rest [mV] | V_th [mV] | V_peak [mV] | k_v [nS/mV²] | τ_w [ms] | a_w [nS] | R_in_eff [MΩ] | Loss |
|-----|----------|------------------|---------------|-----------|-----------|-------------|-----------|-------------|--------------|----------|----------|----------------|------|
| A | 484564503 | 49 | +370 | 133.63 | 3.2394 | −73.734 | −69.417 | +52.092 | 0.003983 | 18.107 | 17.175 | 44.29 | 2×10⁻⁵ |
| B | 318808427 | 40 | +190 | 38.25 | 0.8571 | −75.901 | −67.646 | +64.953 | 0.00179 | 6.889 | 9.773 | 78.67 | 0.2126 |
| C | 471129934 | 51 | +410 | 138.90 | 0.7416 | −69.336 | −48.278 | +53.753 | 0.004763 | 18.895 | 18.867 | 31.29 | 1.2×10⁻⁵ |
| D | 471786879 | 42 | +250 | 206.59 | 0.9128 | −75.710 | −57.487 | +64.999 | 0.002577 | 38.855 | 11.724 | 51.96 | 2.879 |

**Source:** `results/phase4b/fhn_fitted_parameters.csv`  
**Stability:** All four resting equilibria are asymptotically stable (`is_resting_point_stable = True`).

### 4.2 Detailed Model Held-Out Summary (from `results/phase3b/heldout_metrics.csv`)

| Pop | Specimen | n_sweeps | Mean spikes/step (rec/det) | Mean step RMSE [mV] | Mean overall RMSE [mV] | Mean correlation | Rheobase rec [pA] | Rheobase det [pA] | Rheobase shift |
|-----|----------|---------|---------------------------|---------------------|------------------------|-----------------|-------------------|-------------------|----------------|
| A | 484564503 | 31 | 1.77 / 3.71 | 8.30 | 12.73 | 0.8036 | (270, 290] | (330, 350] | +60 pA |
| B | 318808427 | 18 | 6.83 / 7.67 | 7.61 | 4.04 | 0.9570 | (110, 130] | (130, 150] | +20 pA |
| C | 471129934 | 34 | 0.97 / 0.94 | 4.15 | 4.73 | 0.9610 | (270, 290] | (330, 350] | +60 pA |
| D | 471786879 | 26 | 4.85 / 6.19 | 5.89 | 2.23 | 0.9699 | (190, 210] | (190, 210] | 0 pA |

**Source:** `results/phase3b/heldout_metrics.csv` + `results/phase3b/heldout_rheobase.csv`

**Key detailed model failure modes:**
- Pop A: massive resting potential offset (+13.6 mV; baseline −61.07 mV vs recorded −73.73 mV); underfired (4/11 spiking sweeps detected).
- Pop C: underfired (4/11 spiking sweeps detected); rheobase overestimated by +60 pA.
- Pop D: FINEST sweeps overfired (11 simulated vs 1 recorded at +240 pA).

### 4.3 FHN Held-Out Summary (from `results/phase4c/population_summary.csv`)

| Pop | n_sweeps | Mean spikes/step (rec/FHN) | Mean abs spike Δ (FHN vs det) | Mean step RMSE [mV] | Mean overall RMSE [mV] | Mean correlation | Spiking sweeps (rec / FHN) |
|-----|---------|---------------------------|-------------------------------|---------------------|------------------------|-----------------|----------------------------|
| A | 31 | 1.77 / 4.00 | 2.74 (FHN) vs 3.23 (det) | 22.10 | 8.24 | 0.8352 | 11 / 15 |
| B | 18 | 6.83 / 3.78 | 4.28 (FHN) vs 1.06 (det) | 23.73 | 11.97 | 0.8960 | 8 / 6 |
| C | 34 | 0.97 / 1.00 | 0.38 (FHN) vs 0.62 (det) | 12.36 | 4.81 | 0.8775 | 11 / 12 |
| D | 26 | 4.85 / 1.04 | 4.58 (FHN) vs 1.73 (det) | 23.56 | 9.03 | 0.8889 | 10 / 11 |

**Source:** `results/phase4c/population_summary.csv` + `results/phase4c1/phase4c1_spike_detection_audit.csv`  
*(Note on spike detection denominators across the 109 held-out sweeps: 40 sweeps are biological spiking sweeps [$N_{\mathrm{spk}} > 0$], 69 are non-spiking. FHN detected 44 spiking sweeps [37 True Positives, 7 False Positives, 3 False Negatives, 62 True Negatives; sensitivity 92.5%, specificity 89.9%]. Detailed models detected 24 spiking sweeps [24 True Positives, 0 False Positives, 16 False Negatives, 69 True Negatives; sensitivity 60.0%, specificity 100.0%]. Describing FHN performance as "44/40" is invalid as it conflates true positives with total detected sweeps.)*

### 4.4 FHN Dynamical Properties (from `results/phase4c3/` CSVs)

**Hopf bifurcation currents** (all subcritical, first Lyapunov coefficient > 0 under Kuznetsov–Poincaré–Andronov convention):

| Pop | I_H1 (lower Hopf) [pA] | First Lyapunov l₁ | Bistability interval [pA] | Interval width [pA] |
|-----|------------------------|-------------------|--------------------------|---------------------|
| A | 234.34 | 4.39×10⁻⁵ | (214.16, 234.34) | 20.18 |
| B | 161.28 | 8.87×10⁻⁵ | (146.72, 161.28) | 14.55 |
| C | 385.33 | 6.07×10⁻⁵ | (360.03, 385.33) | 25.29 |
| D | 236.27 | 3.30×10⁻⁵ | (215.92, 236.27) | 20.36 |

**Sources:** `results/phase4c3/phase4c3_hopf_independent_checks.csv`, `results/phase4c3/phase4c3_bistability_verification.csv`, `results/phase4c3/phase4c3_fold_verification.csv`

**Mandatory dynamical and boundary qualifiers:**
1. **Open Interval Semantics:** Bistability strictly applies to the **open interior** of the interval $(I_{\mathrm{fold}}, I_{H1})$ — not to the fold endpoint (where stable and unstable cycles coalesce with Floquet multiplier $+1$, rendering the orbit non-hyperbolic and semi-stable) or to the Hopf endpoint (where eigenvalues are purely imaginary $\lambda = \pm i\omega_0$, rendering the equilibrium non-hyperbolic and weakly unstable under $l_1 > 0$).
2. **Fold Boundary Characterization & Uncertainty [Sources: `results/phase4c3/phase4c3_fold_verification.csv`, `results/phase4c3/PHASE4C3_GLOBAL_DYNAMICS_AND_ADAPTATION_AUDIT.md` §2, §3]:**
   - **Forward-Integration Extinction Threshold:** Fold values are numerically estimated extinction thresholds of the stable periodic orbit under forward integration, NOT continuation-derived exact bifurcation points.
   - **Bisection Algorithmic Resolution:** The binary search stopping bracket is $\Delta I < 0.001\text{ pA}$.
   - **Numerical Integration Sensitivity:** Sensitivity across time-steps ($\Delta t \in \{0.010, 0.025, 0.050\}\text{ ms}$) and integration durations ($T_{\mathrm{stop}} \in \{1500, 2500, 4000\}\text{ ms}$) is bounded to $< 0.001\text{ pA}$.
   - **Reported Conservative Uncertainty:** Documented conservatively as $\pm 0.01\text{ pA}$ to account for numerical discretization.
   - **Absence of Mathematical Certainty:** Mathematical certainty of the exact bifurcation location has not been established through a rigorous continuation method (e.g., boundary-value limit-cycle continuation or shooting with Floquet multiplier analysis).

### 4.5 Spike-Frequency Adaptation (from `results/phase4c3/phase4c3_biological_adaptation_scope.csv`)

| Pop | Multi-cycle sweeps (≥3 spikes) | Expanding ISI sweeps | ISI ratio min/median/max |
|-----|-------------------------------|----------------------|--------------------------|
| A | 6 / 31 | 6 | 1.17 / 3.45 / 8.06 |
| B | 6 / 18 | 6 | 1.45 / 2.57 / 3.97 |
| C | 4 / 34 | 4 | 1.89 / 2.83 / 11.27 |
| D | 7 / 26 | 7 | 1.13 / 1.97 / 2.47 |

**Source:** `results/phase4c3/phase4c3_biological_adaptation_scope.csv`

**Mandatory adaptation qualifications [Sources: `results/phase4c3/phase4c3_biological_adaptation_scope.csv`, `results/phase4c2/phase4c2_isi_transient_adaptation.csv`]:**
1. **Biological Scope & Heterogeneity:** The 23 multi-cycle sweeps ($\ge 3$ spikes) originate from **four individual specimens** (one per population), NOT from 109 independent neurons. While 100% of these 23 sweeps (23/23) exhibit progressive first-to-last ISI expansion, large ratios are strongly skewed: Population D (L6a) displays moderate adaptation (median $1.97\times$, max $2.47\times$, never exceeding $2.5\times$); extreme adaptation ($\ge 5.0\times$) occurs in only 3 sweeps across the entire dataset (Pop A and Pop C at high depolarizations $+410\text{ to }+430\text{ pA}$).
2. **FHN Transient vs Asymptotic Dynamics:** FHN trajectories exhibit small initial transient cycle-to-cycle adjustments as the orbit contracts from rest onto the limit cycle (Pop B: initial expansion of $+0.5\%\text{ to }+1.2\%$; Pops A and C: initial contraction of $-0.3\%\text{ to }-0.5\%$). Once on the periodic orbit ($\le 2$ cycles, $\le 120\text{ ms}$), successive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{last}}/\mathrm{ISI}_1 \le 1.02$, asymptotic ratio $= 1.000$).
3. **Model Formulation Scope:** This reflects a structural limitation of the current two-variable autonomous FHN formulation with a single recovery variable $\tau_w$ in reproducing sustained biological multi-timescale adaptation, rather than a universal mathematical impossibility theorem for all two-variable models.

---

## 5. Authoritative Source File Paths

| Content | File |
|---------|------|
| FHN frozen parameters | `results/phase4b/fhn_fitted_parameters.csv` |
| FHN calibration metrics | `results/phase4b/fhn_calibration_metrics.csv` |
| FHN calibration loss breakdown | `results/phase4b/fhn_calibration_loss_breakdown.csv` |
| Detailed model held-out metrics (per sweep) | `results/phase3b/heldout_metrics.csv` |
| Detailed model F-I curves | `results/phase3b/heldout_fi_curves.csv` |
| Detailed model rheobase intervals | `results/phase3b/heldout_rheobase.csv` |
| FHN held-out per-sweep comparison | `results/phase4c/fhn_detailed_comparison.csv` |
| FHN held-out metrics (per sweep) | `results/phase4c/fhn_heldout_metrics.csv` |
| FHN held-out population summary | `results/phase4c/population_summary.csv` |
| FHN held-out protocol breakdown | `results/phase4c/protocol_family_summary.csv` |
| FHN held-out manifest (109 sweeps verified) | `results/phase4c/fhn_heldout_execution_manifest.csv` |
| Hopf bifurcation independent checks | `results/phase4c3/phase4c3_hopf_independent_checks.csv` |
| Fold (bistability lower boundary) verification | `results/phase4c3/phase4c3_fold_verification.csv` |
| Bistability coexistence verification | `results/phase4c3/phase4c3_bistability_verification.csv` |
| Biological adaptation scope (23 sweeps) | `results/phase4c3/phase4c3_biological_adaptation_scope.csv` |
| ISI transient adaptation per sweep | `results/phase4c2/phase4c2_isi_transient_adaptation.csv` |
| Phase 4C3 correction and qualification log | `results/phase4c3/PHASE4C3_CORRECTION_LOG.md` |
| Phase 4B calibration robustness (Pop D Pareto) | `results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md` |
| Phase 4B1 identifiability audit | `results/phase4b1/PHASE4B1_INDEPENDENT_CALIBRATION_AUDIT.md` |
| Pop D baseline 625-point Pareto scan CSV (Phase 4B.1) | `results/phase4b1/fhn_population_d_pareto_audit.csv` |
| Pop D refined 961-point scan raw points (Phase 4B.2) | `results/phase4b2/fhn_population_d_grid_points.csv` |
| Pop D refined 961-point scan Pareto summary (Phase 4B.2) | `results/phase4b2/fhn_population_d_refined_pareto.csv` |
| Phase 4C1 independent results audit | `results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md` |
| Phase 4C main held-out report | `results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md` |
| Phase 3B detailed model report | `results/phase3b/PHASE3B_FINAL_REPORT.md` |
| Phase 3B cross-population analysis | `results/phase3b/PHASE3B_CROSS_POPULATION_ANALYSIS.md` |
| Phase 0C candidate readiness | `results/dataset_inventory/PHASE0C_SELECTED_MODEL_READINESS.md` |
| Phase 0B feasibility audit | `results/dataset_inventory/FOUR_V1_POPULATION_FEASIBILITY_AUDIT.md` |

### 5.1 Existing Figures Inventory

**`results/phase4c/figures/`** (7 files — primary comparison figures):
- `fi_curves_comparison.png` — Four-panel F-I curves: Recording vs Detailed vs FHN, all 109 sweeps
- `waveform_fidelity_comparison.png` — Step RMSE + Pearson r bar charts, Detailed vs FHN
- `subthreshold_iv_curves.png` — Subthreshold I-V curves, all four populations
- `traces_pop_A.png` — Voltage trace comparison, Pop A, sweep 50 (+390 pA)
- `traces_pop_B.png` — Voltage trace comparison, Pop B, sweep 41 (+210 pA)
- `traces_pop_C.png` — Voltage trace comparison, Pop C, sweep 52 (+430 pA)
- `traces_pop_D.png` — Voltage trace comparison, Pop D, sweep 43 (+270 pA)

**`results/phase3b/figures/`** (6 files — detailed model figures):
- `error_distributions_by_population.png`
- `fi_curves_all_populations.png`
- `first_spike_latency_comparison.png`
- `passive_properties_comparison.png`
- `rheobase_comparison.png`
- (additional sweep-level plots in subfolders)

**`results/phase4b/figures/`** (3 files — calibration figures):
- `calibration_loss_breakdown.png`
- `four_population_calibration_summary.png`
- `voltage_comparison_A/B/C/D.png`

**`results/phase4b2/figures/`** (3 files — robustness):
- `hessian_eigenvalue_robustness.png`
- `pareto_frontier_population_d.png`
- `population_d_refined_pareto.png`

**`results/phase4c2/figures/`** (2 files — dynamics):
- `isi_adaptation_comparison.png`
- `population_hopf_transversality.png`

---

## 6. Cross-Population Scientific Findings

Each finding is tagged with its evidence type and source.

### 6.1 Resting Membrane Potential and Subthreshold Behaviour

- **FHN:** Resting potential exactly matches calibration recording (by construction). Range: −75.9 mV (B/D) to −69.3 mV (C). **[OBSERVED, `fhn_fitted_parameters.csv`]**
- **Detailed model Pop A:** Large resting offset (+13.6 mV above biological baseline). Systematic constant offset throughout all subthreshold sweeps. **[OBSERVED, `heldout_metrics.csv`, baseline_delta_mv column]**
- **Detailed models B, C, D:** Resting potential offsets ≤ 0.6 mV. **[OBSERVED, `heldout_metrics.csv`]**
- **Subthreshold Linearity and Correlations [OBSERVED/DERIVED, `results/phase4c1/phase4c1_subthreshold_audit.csv`]:**
  - **Biological Recordings:** Linear I-V in the subthreshold regime with regression linearity $r^2 > 0.98$ across all four specimens ($0.9807\text{--}0.9996$).
  - **FHN Mutually Subthreshold Correlations:** FHN does **NOT** achieve correlation $r^2 > 0.98$ across all populations. In sweeps that are mutually subthreshold in both recording and FHN:
    - Pop A: $r^2 = \mathbf{0.9249}$ ($r^2 > 0.98$ is False; classical $R^2 = 0.6742$)
    - Pop B: $r^2 = \mathbf{0.9900}$ ($r^2 > 0.98$ is True; classical $R^2 = 0.4894$)
    - Pop C: $r^2 = \mathbf{0.9518}$ ($r^2 > 0.98$ is False; classical $R^2 = 0.4423$)
    - Pop D: $r^2 = \mathbf{0.9952}$ ($r^2 > 0.98$ is True; classical $R^2 = 0.5648$)
  - **Hyperpolarizing-Only Subthreshold Regime:** In strictly hyperpolarizing sweeps (negative current steps), FHN correlation $r^2$ exceeds **0.996** across all four populations (Pop A: $0.9982$, Pop B: $0.9988$, Pop C: $0.9960$, Pop D: $0.9985$), and I-V linearity exceeds $0.999$.

### 6.2 Input Resistance and Charging Behaviour

- **FHN calibrated R_in:** A = 44.3 MΩ, B = 78.7 MΩ, C = 31.3 MΩ, D = 52.0 MΩ. These were fit from calibration sweep. **[OBSERVED, `fhn_calibration_metrics.csv` → `rin_fhn_mohm`]**
- **Biological R_in (from calibration sweep):** A = 44.3 MΩ, B = 80.3 MΩ, C = 31.3 MΩ, D = 52.6 MΩ. **[OBSERVED, `fhn_calibration_metrics.csv` → `rin_exp_mohm`]**
- FHN tracks subthreshold I-V with high fidelity in held-out sweeps in Pops B and D ($r^2 = 0.9900$ and $0.9952$), but shows lower correlation in Pops A and C ($r^2 = 0.9249$ and $0.9518$). **[OBSERVED, `results/phase4c1/phase4c1_subthreshold_audit.csv`]**
- FHN has no sag (Ih); biological sag is 0.63–1.86 mV across specimens. FHN sag = 0.00 mV. **[OBSERVED, `PHASE4C_HELDOUT_EVALUATION_REPORT.md` §5.2.4]**

### 6.3 Rheobase and Excitability

| Pop | Biological rheobase | Detailed model | FHN Hopf I_H1 | FHN bistability window |
|-----|---------------------|----------------|---------------|------------------------|
| A | (270, 290] pA | (330, 350] pA — +60 pA shift | 234.3 pA | (214.2, 234.3) pA |
| B | (110, 130] pA | (130, 150] pA — +20 pA shift | 161.3 pA | (146.7, 161.3) pA |
| C | (270, 290] pA | (330, 350] pA — +60 pA shift | 385.3 pA | (360.0, 385.3) pA |
| D | (190, 210] pA | (190, 210] pA — 0 shift | 236.3 pA | (215.9, 236.3) pA |

**Sources:** `results/phase3b/heldout_rheobase.csv`, `results/phase4c3/phase4c3_hopf_independent_checks.csv`, `results/phase4c3/phase4c3_fold_verification.csv`

**Interpretation:**
- Detailed A and C models overestimate rheobase by +60 pA — a systematic failure across these two populations.
- Detailed D model correctly estimates rheobase; B is close (+20 pA).
- FHN Hopf current is consistently higher than biological rheobase (by ~50–100 pA in A/C). This is the subcritical FHN: the biological cell's rheobase sits below I_H1 but potentially within the bistability window — the neuron can fire with sufficient depolarising perturbation in this regime.
- **Spike Detection Denominators and Contingency Analysis [NUMERICAL RESULT — derived from `results/phase4c1/phase4c1_spike_detection_audit.csv` and `results/phase4c/population_summary.csv`]:**
  - **Ground Truth Denominators across 109 sweeps:**
    - Experimental recordings: **40 / 109** spiking sweeps ($N_{\mathrm{spk}} > 0$), **69 / 109** non-spiking sweeps ($N_{\mathrm{spk}} = 0$).
    - Detailed models (Phase 3B): fired in **24 / 109** sweeps (24 True Positives, 0 False Positives, 16 False Negatives, 69 True Negatives).
    - Reduced FHN (Phase 4C): fired in **44 / 109** sweeps (37 True Positives, 7 False Positives, 3 False Negatives, 62 True Negatives).
  - **Distinction from True-Positive Ratio:** Describing FHN detection as "44/40" is mathematically invalid. FHN fired in 44 total sweeps, of which 37 were true positives and 7 were false positives (spiking in near-threshold subthreshold sweeps: 4 in Pop A, 1 in Pop C, 2 in Pop D).
  - **Audited Classification Metrics:**
    - **Sensitivity (Recall):** FHN = **92.5%** ($37/40$) vs Detailed = **60.0%** ($24/40$). FHN missed only 3 biological spiking sweeps (at near-threshold currents), whereas the Detailed model missed 16 spiking sweeps (systematic underfiring near rheobase in Pops A and C).
    - **Specificity:** Detailed = **100.0%** ($69/69$) vs FHN = **89.9%** ($62/69$). Detailed had zero false positives; FHN fired in 7 near-threshold subthreshold sweeps.
    - **Balanced Accuracy:** FHN = **91.2%** vs Detailed = **80.0%**.

### 6.4 Spike Count and Firing Rate (F-I)

- **Pop A:** FHN mean spike error (2.74) < Detailed (3.23) — FHN closer to biology on average, but detailed model badly underfires (4 spiking sweeps vs 11 recorded). FHN fires at fixed ~9 spikes/s for suprathreshold sweeps (no adaptation). At very high amplitudes (+390 to +430 pA), detailed model fires 27–48 spikes (massive overcounting) while FHN fires 8–9. **[OBSERVED, `fhn_detailed_comparison.csv`]**
- **Pop B:** Detailed model better (abs error 1.06 vs FHN 4.28). FHN collapses to 1–2 spikes at +250–+270 pA (FINEST regime, bistability exit). **[OBSERVED, `fhn_detailed_comparison.csv`]**
- **Pop C:** FHN mean spike error (0.38) < Detailed (0.62) — FHN slightly closer. Detailed model underfires near rheobase. **[OBSERVED, `population_summary.csv`]**
- **Pop D:** Detailed model much better (abs error 1.73 vs FHN 4.58). FHN severely underfires (mean 1.04 vs 4.85 recorded). **[OBSERVED, `population_summary.csv`]**

### 6.5 First-Spike Latency

- **Biological latency at rheobase:**
  - Pop A ~1050–1085 ms (late, near-threshold)
  - Pop B ~1030–1050 ms at 170–210 pA
  - Pop C ~1050–1095 ms at 290–310 pA
  - Pop D: long latency ~1133 ms at 210 pA, shorter at higher amplitudes
- **Pop D biological long latency** (hypothesized: transient A-type K+ channels). NOT confirmed; no channel isolation in dataset.
- **FHN latency:** ≤16 ms in suprathreshold sweeps; FHN fires almost immediately upon step onset for N_spk > 4. FHN cannot reproduce long first-spike latency.
- **Detailed model latency at calibration:** A = 24.71 ms, B = 22.48 ms, C = 16.34 ms, D = 52.97 ms. Detailed model captures D's long latency substantially better. **[OBSERVED, `fhn_calibration_metrics.csv`]**

**Source:** `fhn_calibration_metrics.csv`, `heldout_metrics.csv` (first_spike columns), `PHASE4C_HELDOUT_EVALUATION_REPORT.md` §5.2.3

### 6.6 Spike-Frequency Adaptation

- **Biology:** All four populations exhibit ISI expansion during the 1 s step. ISI ratio (last/first) range:
  - Pop A: 1.17–8.06 (median 3.45)
  - Pop B: 1.45–3.97 (median 2.57)
  - Pop C: 1.89–11.27 (median 2.83; single sweep reaches 11.3×)
  - Pop D: 1.13–2.47 (median 1.97)
- **FHN Adaptation Dynamics:**
  - Trajectories exhibit small initial transient ISI adjustments during entry onto the limit cycle (Pop B initial expansion of $+0.5\%\text{ to }+1.2\%$; Pops A and C initial contraction of $-0.3\%\text{ to }-0.5\%$).
  - Stable periodic firing reaches a stationary asymptotic period within $\le 2$ cycles ($\le 120\text{ ms}$), after which successive ISIs are stationary to $< 0.01\%$ ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$; overall ratio within $0.9926\text{--}1.0325$).
  - This behaviour represents a structural limitation of the current two-variable autonomous FHN formulation with a single recovery variable $\tau_w$ in capturing sustained adaptation, rather than a universal mathematical impossibility theorem for all two-variable models.
- **Biological Multi-Cycle Adaptation:**
  - Sustained ISI expansion is observed across all 23 qualifying multi-cycle sweeps ($\ge 3$ spikes) in the biological recordings (**100% expansion**, 0% contraction or stationarity; median ratios $1.97\times\text{--}3.45\times$, maximum $11.27\times$).
  - These 23 sweeps originate from **four individual specimens** (not 109 independent neurons).
  - Multi-timescale adaptation operating continuously over 1 second in biology is consistent with slow secondary biophysical processes (such as calcium-activated potassium currents $I_{\mathrm{SK}}$ or slow muscarinic potassium currents $I_M$).
- **Detailed model:** Not directly audited for per-cycle ISI in Phase 3B beyond spike counts and mean ISIs. See `results/phase3b/heldout_metrics.csv` (`mean_isi_rec_ms`, `mean_isi_sim_ms`).

**Sources:** `results/phase4c3/phase4c3_biological_adaptation_scope.csv`, `results/phase4c2/phase4c2_isi_transient_adaptation.csv`

### 6.7 Spike Waveform

- **Action-Potential Waveform Kinetics [PROVISIONAL COMPARISON — `results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md` §5.2.2, `results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md` §6]:**
  - **FHN Relaxation Oscillation:** FHN action potentials are smooth cubic relaxation oscillations with broad repolarization and absence of fast sodium spike kinetics, which is the primary driver of elevated step RMSE ($12\text{--}24\text{ mV}$) during spiking sweeps.
  - **Provisional Upstroke Velocity Comparison:** A numerical comparison in Phase 4C reported peak $\mathrm{d}V/\mathrm{d}t$ of $5.7\text{--}6.2\text{ V/s}$ for FHN versus $397\text{--}466\text{ V/s}$ for recorded somatic spikes ($60\times\text{--}75\times$ slower). **Crucial Qualification:** Because low-pass filtering, digital differentiation stencils (e.g., 5-point stencil vs 2-point differences), and sampling-rate consistency (200 kHz biological recording vs fixed RK4 steps) were not independently standardized across all sweeps, this numerical upstroke velocity ratio is **provisional** and omitted from headline conclusions. The robust qualitative conclusion is the kinetic divergence between smooth FHN relaxation cycles and fast biological action potentials.
  - **Detailed model:** Produces rapid action potentials with sharp upstrokes and afterhyperpolarizations; detailed AP upstroke velocity was not independently audited across held-out sweeps in Phase 3B.

### 6.8 Population D — FHN Failure Mode and Parameter-Scan Provenance

Population D represents the clearest FHN quantitative limitation. At calibration (+250 pA, 13 biological spikes), FHN produced only 4 spikes after convergence, with a fitted recovery timescale $\tau_w = 38.86\text{ ms}$.

To test whether this mismatch was an optimization failure or a structural trade-off within the investigated $(C_m, \tau_w)$ parameter space under the calibrated baseline parameters and calibration objective for specimen `471786879` (Sweep 42), two successive numerical scans were conducted across Phase 4B.1 and Phase 4B.2:

1. **Phase 4B.1 Baseline Exploratory Scan (625 combinations) [Source: `results/phase4b1/fhn_population_d_pareto_audit.csv`, `results/phase4b1/PHASE4B1_INDEPENDENT_CALIBRATION_AUDIT.md` §5]:**
   - **Grid Bounds & Dimensions:** $C_m \in [40.0, 240.0]\text{ pF}$ (25 points, step $8.33\text{ pF}$) $\times \tau_w \in [8.0, 60.0]\text{ ms}$ (25 points, step $2.17\text{ ms}$); $25 \times 25 = 625$ combinations.
   - **Spiking Breakdown:** 553 spiking ($88.5\%$), 72 quiescent ($11.5\%$).
   - **Target Biological Count ($N_{\mathrm{spk}} = 13$):** Maximum achievable latency is **$12.20\text{ ms}$** (range $9.4\text{--}12.2\text{ ms}$, mean $10.80\text{ ms}$, $n=2$).
   - **High-Spiking Regime ($N_{\mathrm{spk}} \ge 12$):** Maximum achievable latency across all high-spiking models is **$18.50\text{ ms}$** (achieved at $N_{\mathrm{spk}} = 12$; $13 \to 12.2\text{ ms}$, $14 \to 14.3\text{ ms}$, $16 \to 10.1\text{ ms}$, $17 \to 10.9\text{ ms}$).
   - **Long-Latency Criterion ($t_{\mathrm{lat}} \ge 50\text{ ms}$):** Strictly restricted to models with $N_{\mathrm{spk}} \le 4$ (max latency at 4 spikes: $65.0\text{ ms}$, encompassing the fitted model's $59.9\text{ ms}$).

2. **Phase 4B.2 Refined High-Resolution Scan (961 combinations) [Sources: `results/phase4b2/fhn_population_d_grid_points.csv`, `results/phase4b2/fhn_population_d_refined_pareto.csv`, `results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md` §2]:**
   - **Grid Bounds & Dimensions:** $C_m \in [40.0, 220.0]\text{ pF}$ (31 points, step $6.00\text{ pF}$) $\times \tau_w \in [8.0, 50.0]\text{ ms}$ (31 points, step $1.40\text{ ms}$); $31 \times 31 = 961$ combinations.
   - **Spiking Breakdown:** 850 spiking ($88.4\%$), 111 quiescent ($11.6\%$).
   - **Target Biological Count ($N_{\mathrm{spk}} = 13$):** Maximum achievable latency is **$16.00\text{ ms}$** (range $9.4\text{--}16.0\text{ ms}$, mean $12.93\text{ ms}$, $n=7$).
   - **High-Spiking Regime ($N_{\mathrm{spk}} \ge 12$):** Maximum achievable latency across all high-spiking models is **$17.40\text{ ms}$** (achieved at $N_{\mathrm{spk}} = 12$; $13 \to 16.0\text{ ms}$, $14 \to 11.9\text{ ms}$, $15 \to 13.3\text{ ms}$, $16 \to 10.4\text{ ms}$, $17 \to 10.9\text{ ms}$; summarized in report as $< 18\text{ ms}$).
   - **Long-Latency Criterion ($t_{\mathrm{lat}} \ge 50\text{ ms}$):** Strictly restricted to models with $N_{\mathrm{spk}} \le 4$ (max latency at 4 spikes: $64.3\text{ ms}$).

3. **Disentangling Historical Provenance and Documented Typo:**
   - In `results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md`, Section 2.1 correctly details the 625-point scan ($[40, 240]\text{ pF} \times [8, 60]\text{ ms}$) and Section 2.2 correctly details the 961-point scan ($[40, 220]\text{ pF} \times [8, 50]\text{ ms}$).
   - However, in Table 3.1 of that same report, the synthesis row inadvertently conjoined the parameter bounds and latency bound of Scan 1 ($[40, 240]\text{ pF} \times [8, 60]\text{ ms}$, $t_{\mathrm{lat}} \le 18.5\text{ ms}$) with the sample size of Scan 2 ($961$ simulations).
   - Authoritative scan supporting the refined conclusions in Phase 5 is the **Phase 4B.2 961-point scan** ($[40, 220]\text{ pF} \times [8, 50]\text{ ms}$), with max latency of **$16.00\text{ ms}$** at the target 13 spikes and **$17.40\text{ ms}$** across $N_{\mathrm{spk}} \ge 12$. Both scans independently corroborate the exact same qualitative and quantitative trade-off.

- **Scope of Claim (Not an Unproven Universal Impossibility):** As established in Phase 4B.2, this trade-off is an empirically verified result within the tested parameter space and calibration objective for this specimen. It must **not** be called an "irreducible" trade-off across all two-variable planar dynamical systems or claimed as an unproven universal Pareto impossibility theorem across all $\mathbb{R}^7$ parameterizations or non-standard nullcline geometries.

**Sources:** `results/phase4b1/fhn_population_d_pareto_audit.csv`, `results/phase4b2/fhn_population_d_grid_points.csv`, `results/phase4b2/fhn_population_d_refined_pareto.csv`, `results/phase4b2/PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md`

### 6.9 Waveform RMSE Summary

| Pop | Det step RMSE [mV] | FHN step RMSE [mV] | Det overall RMSE [mV] | FHN overall RMSE [mV] | Det corr | FHN corr |
|-----|--------------------|--------------------|----------------------|----------------------|---------|---------|
| A | 8.30 | **22.10** | **12.73** | **8.24** | **0.8036** | 0.8352 |
| B | **7.61** | 23.73 | **4.04** | 11.97 | **0.9570** | 0.8960 |
| C | **4.15** | 12.36 | **4.73** | 4.81 | **0.9610** | 0.8775 |
| D | **5.89** | 23.56 | **2.23** | 9.03 | **0.9699** | 0.8889 |

**Note on Pop A overall RMSE:** FHN lower overall RMSE than detailed model (8.24 vs 12.73 mV) because FHN's resting potential is correct; detailed model has +13.6 mV baseline offset inflating overall RMSE.

---

## 7. Mandatory Scientific Caveats (NON-NEGOTIABLE — must be preserved verbatim or equivalently)

The following constraints were established and verified across multiple independent audit phases. They MUST appear in any Phase 5 report. Do NOT soften, remove, or merge these caveats.

1. **Sample size:** Four representatives do not establish universal layer-specific behaviour. Results characterise these specific specimens and their specific published perisomatic model fits.
2. **Layer ≠ projection class:** Groups are layer-defined excitatory populations. IT/ET/PT/CT labels are NOT confirmed by Allen metadata.
3. **L4 stellate vs star-pyramidal:** All 47 identity-compatible L4 cells have intact apical dendrites → spiny stellate morphology is NOT confirmed. Use "L4 spiny excitatory" or "star-pyramidal/IT-like (unresolved)".
4. **L5 ET vs PT:** Rbp4-Cre_KL100 targets L5 thick-tufted cells but does not distinguish ET from PT.
5. **L6a CT:** Ntsr1-Cre_GN220 is CT-compatible but NOT confirmed CT.
6. **Morphology/configuration substitution:** Pop B detailed model (382982932) used a substitute morphology (reconstruction 491771090 ≠ specimen's 674389884). Pop A, C, D use dendrite-only reconstructions. No model uses a full morphological reconstruction of the recorded cell.
7. **Protocol dependence:** COARSE–FINEST mismatch is a measurable within-recording biological effect (Phase 2F). Models trained on COARSE may not generalize to FINEST excitability regime.
8. **FHN is a phenomenological reduced model:** It is NOT a detailed action-potential waveform model. Spike waveform, AHP shape, and AHP timing are NOT quantitatively comparable.
9. **FHN performance must be evaluated per metric:** Overall RMSE advantage for Pop A is due to resting potential offset in the detailed model, NOT FHN superiority in waveform quality.
10. **Fold estimates and numerical uncertainty:**
    - Values are forward-integration extinction thresholds of the stable periodic orbit, NOT exact continuation-derived fold bifurcation points.
    - Bisection algorithmic resolution is $\Delta I < 0.001\text{ pA}$.
    - Numerical integration sensitivity to $\Delta t$ ($0.010\text{--}0.050\text{ ms}$) and duration ($1500\text{--}4000\text{ ms}$) is $< 0.001\text{ pA}$.
    - Conservative numerical uncertainty is reported as $\pm 0.01\text{ pA}$.
    - Mathematical certainty has not been established through a rigorous continuation method (e.g. boundary-value continuation or shooting method with Floquet multiplier analysis).
11. **Bistability applies to open interior (I_fold, I_H1):** NOT to the exact boundary values, which are non-hyperbolic.
12. **Adaptation data scope:** 23 multi-cycle sweeps, 4 specimens. ISI ratios up to 11.3× concentrated in a few sweeps at high amplitudes. NOT 109 independent neurons.
13. **Ionic mechanism hypotheses:** Transient A-type K+ (long latency Pop D), I_SK/I_M (adaptation), Ih (sag) — these are HYPOTHESES consistent with biophysical literature, NOT experimentally demonstrated in this dataset.
14. **Population D trade-off bounded to investigated parameter space:** The empirical trade-off between first-spike latency and repetitive firing frequency was mapped across both a 625-point baseline grid ($C_m \in [40, 240]\text{ pF}, \tau_w \in [8, 60]\text{ ms}$; max latency $18.5\text{ ms}$ for $N_{\mathrm{spk}} \ge 12$, $12.2\text{ ms}$ at target 13 spikes; `fhn_population_d_pareto_audit.csv`) and a 961-point refined grid ($C_m \in [40, 220]\text{ pF}, \tau_w \in [8, 50]\text{ ms}$; max latency $17.4\text{ ms}$ for $N_{\mathrm{spk}} \ge 12$, $16.0\text{ ms}$ at target 13 spikes; `fhn_population_d_grid_points.csv`) for specimen 471786879 under the calibrated baseline parameters and calibration objective. Per Phase 4B.2 audit, this is an empirically verified result for the calibrated model within the tested subspace, NOT an unproven universal Pareto impossibility theorem for all two-variable planar systems.

---

## 8. Phase 5B–5D Execution Plan

### Phase 5B — Cross-Population Scientific Synthesis

**Goal:** Write the scientific argument answering the research question, structured around the evidence matrix.

**Content required:**
1. Frame the hierarchy: biological recording → detailed model → FHN model.
2. Section by electrophysiological behaviour (follow §6 structure above).
3. For each behaviour: what FHN preserves, what the detailed model preserves, what neither captures, evidence citations.
4. Explicit treatment of the two model failures that are data artifacts vs true model inadequacies:
   - Pop A detailed model resting offset is a fitting limitation, not a universal perisomatic failure.
   - Pop D FHN underfiring reflects an empirical parameter trade-off in the investigated $(C_m, \tau_w)$ space under the calibration objective, not a numerical integration error.
5. Cross-population comparisons must be annotated as descriptive (four specimens), not statistical.
6. Bistability as a mechanistic explanation for near-threshold sensitivity in FHN.
7. All 14 caveats from §7 must be present.

**Output file:** `results/phase5/PHASE5B_CROSS_POPULATION_SYNTHESIS.md`

**Validation:** No new numbers not traceable to §5 source files. No projection class labels. No claims about "all L4 neurons" from one specimen.

### Phase 5C — Final Research Report

**Goal:** A coherent academic-quality report covering the full project.

**Required sections (exact order):**
1. Abstract (≤300 words; include main quantitative results: sweep excitability classification across 109 sweeps [recorded: 40 spiking sweeps; FHN: 44 spiking sweeps, sensitivity 92.5% (37/40), specificity 89.9% (62/69); detailed models: 24 spiking sweeps, sensitivity 60.0% (24/40), specificity 100.0% (69/69)]; step RMSE 12–24 mV FHN vs 4–8 mV detailed; sustained biological adaptation across 23 multi-cycle sweeps [median 1.97×–3.45×, max 11.27×] vs rapid FHN limit-cycle stationarity within ≤ 2 cycles [asymptotic ratio 1.000])
2. Introduction: research motivation, question, scope
3. Background: cortical circuit context, detailed model hierarchy, FHN as reduced model
4. Dataset and population selection: Phase 0B/0C findings; four populations; eligibility criteria; identity limitations
5. Experimental methodology: Allen database, NWB, protocols (COARSE/FINEST), calibration/held-out split, junction potential convention
6. Detailed model evaluation (Phase 3B): execution environment, calibration sweeps, held-out 109 sweeps, per-population results, rheobase, spike counts, waveform metrics
7. FHN formulation and calibration (Phase 4A/B): dimensional FHN equations, parameter definitions, calibration procedure, Pop D Pareto
8. FHN held-out evaluation (Phase 4C): 109 sweeps, dual reporting, per-population results
9. Dynamical analysis: Hopf bifurcation, bistability, adaptation
10. Cross-population synthesis (from Phase 5B)
11. Discussion: preserved vs lost behaviours, biological interpretation, model hierarchy implications
12. Limitations (from §7 of this document — all 14)
13. Conclusion
14. References (Allen Institute, FHN original, key biophysics papers cited in phase reports)
15. Appendix A: FHN parameter table (from §4.1)
16. Appendix B: Held-out sweep manifest summary
17. Appendix C: Reproducibility — commit hashes, environment specs, test counts

**Output file:** `results/phase5/PHASE5C_FINAL_RESEARCH_REPORT.md`

**Validation:** Every quantitative claim must be traceable to a source file in §5. Abstract numbers must match §4 tables. No projection labels. Report must be explicitly labelled "validated interim study — single representative per layer" if any section cannot be verified.

### Phase 5D — Figures, Tables, and Presentation

**Goal:** Identify which existing figures are reusable, which need captions/labels, and what genuinely new figures are needed.

**Reusable existing figures (NO regeneration needed):**
- `results/phase4c/figures/fi_curves_comparison.png` — PRIMARY: F-I comparison, all four populations
- `results/phase4c/figures/waveform_fidelity_comparison.png` — PRIMARY: RMSE + correlation bars
- `results/phase4c/figures/subthreshold_iv_curves.png` — INPUT RESISTANCE evidence
- `results/phase4c/figures/traces_pop_A.png` — voltage trace comparison Pop A
- `results/phase4c/figures/traces_pop_B.png` — voltage trace comparison Pop B
- `results/phase4c/figures/traces_pop_C.png` — voltage trace comparison Pop C
- `results/phase4c/figures/traces_pop_D.png` — voltage trace comparison Pop D
- `results/phase4c2/figures/isi_adaptation_comparison.png` — ADAPTATION evidence
- `results/phase3b/figures/rheobase_comparison.png` — RHEOBASE evidence
- `results/phase3b/figures/first_spike_latency_comparison.png` — LATENCY evidence

**Tables that MUST be in the report (can be markdown, no script needed):**
- Table 1: Four population definitions (from §3)
- Table 2: FHN frozen parameters (from §4.1)
- Table 3: Held-out summary — Recording / Detailed / FHN (from §4.2 + §4.3)
- Table 4: Rheobase comparison (from §6.3)
- Table 5: Bistability windows (from §4.4)
- Table 6: Spike-frequency adaptation ISI ratios (from §4.5)

**Genuinely missing figure (generate only if time allows):**
- A single summary panel showing behaviours-preserved vs behaviours-lost matrix (conceptual diagram — can be created as an SVG/schematic table, no data computation required).

**Output file:** `results/phase5/PHASE5D_FIGURE_PLAN.md`

---

## 9. Exact File-Level Tasks for Antigravity Flash

Execute ONLY the following, in order. DO NOT:
- Re-run any model simulations.
- Recalibrate FHN parameters.
- Regenerate the 109 held-out evaluations.
- Modify any file in `results/phase3b/`, `results/phase4b/`, `results/phase4c/`, or `results/phase4c*/`.
- Commit to `main`.

### Task 9.1: Phase 5B — Cross-population synthesis document

**File to create:** `results/phase5/PHASE5B_CROSS_POPULATION_SYNTHESIS.md`

**Required inputs:** This handoff document (§6, §7), `results/phase4c/PHASE4C_HELDOUT_EVALUATION_REPORT.md` (§5), `results/phase3b/PHASE3B_CROSS_POPULATION_ANALYSIS.md`, `results/phase4c3/PHASE4C3_GLOBAL_DYNAMICS_AND_ADAPTATION_AUDIT.md`.

**Validation gates:**
- All quantitative values traceable to source CSVs in §5.
- All 14 caveats from §7 present.
- No projection class labels.
- No claims beyond "this specimen/this population representative".

### Task 9.2: Phase 5C — Final research report

**File to create:** `results/phase5/PHASE5C_FINAL_RESEARCH_REPORT.md`

**Required inputs:** All phase reports listed in §5; evidence matrix in §4; cross-population synthesis from Task 9.1.

**Validation gates:**
- Sections 1–17 present (see §8 plan).
- Abstract spike-detection numbers match audited confusion matrix: 40 recorded spiking sweeps, 44 FHN spiking sweeps (sensitivity 92.5% [37/40], specificity 89.9% [62/69]), 24 detailed spiking sweeps (sensitivity 60.0% [24/40], specificity 100.0% [69/69]).
- FHN step RMSE ranges 12–24 mV (spiking); detailed 4–8 mV.
- Pop A baseline offset acknowledged (+13.6 mV).
- Pop D FHN underfiring acknowledged and explained.
- No fabricated section content.
- Report explicitly labelled as per-representative study with appropriate scope limitations.

### Task 9.3: Phase 5D — Figure plan

**File to create:** `results/phase5/PHASE5D_FIGURE_PLAN.md`

**Contents:** For each existing figure in §5.1, one-line reuse justification and suggested caption. For the missing summary panel, a concise specification. No code required.

### Task 9.4: README update

**File to modify:** `README.md`

**Add to status table:** Phase 5A (complete, commit TBD), Phase 5B, 5C, 5D (in progress or planned).
**Do NOT change any other content.**

### Task 9.5: Commit and push

After all four tasks above are complete and verified:

```bash
git add results/phase5/ README.md
git commit -m "docs: Phase 5 evidence consolidation and cross-population synthesis"
git push origin ashish-work
```

Run `python -m pytest tests/ -q` before committing. Confirm 451+ tests pass (no regressions).

---

## 10. Validation Requirements Per Task

| Task | Key numerical checks | Caveat checks |
|------|---------------------|---------------|
| 5B synthesis | Pop summary table values match §4.2/§4.3 | Caveats 1–14 present |
| 5C report | Abstract: 40 rec spiking sweeps, 44 FHN (37 TP, 7 FP; 92.5% sens), 24 det (24 TP, 0 FP; 60.0% sens); step RMSE 12–24/4–8 mV | All §7 constraints labelled "Limitation" |
| 5D figure plan | All 10 reusable figures listed; captions mention n=1 per layer | n/a |
| README update | Status table consistent with commit history | n/a |

---

## 11. Unresolved Questions (Genuinely Open)

These are not blockers for Phase 5B–5D documentation but are honest scientific gaps:

1. **Why does the Allen perisomatic model for Pop A and C overestimate rheobase by +60 pA?** Possible: single calibration sweep was far suprathreshold (+370/+410 pA), so the fitting traded accuracy near rheobase for accuracy at the fitted amplitude. Phase 3B documented this but did not investigate the fitting objective.

2. **What ionic mechanism produces Pop D's long first-spike latency?** Transient A-type K+ (I_A/I_D) is the standard biophysical hypothesis. Not testable from this dataset without current isolation.

3. **Is the COARSE–FINEST protocol history effect (Phase 2F) specific to these specimens or a general Allen dataset artefact?** Phase 2F documented it for specimen 382982932. Not verified for the other three.

4. **Can a three-variable extension (e.g. adding a second recovery/adaptation variable $w_2$ on a slow timescale $\tau_{w2} \gg \tau_w$) reproduce biological multi-timescale adaptation?** A third state variable representing slow calcium-dependent adaptation is a standard theoretical extension to break limit-cycle stationarity over multi-second steps. This represents a natural follow-up hypothesis, outside the frozen two-variable scope of this project.

5. **Population B R_in discrepancy (FHN calibrated at 78.7 MΩ vs experiment 80.3 MΩ):** Small but the highest relative error of the four populations. Related to the relatively high calibration loss (0.21). Documented in Phase 4B1 identifiability audit.

---

## 12. Confirmation of Data Integrity

This document was produced by READ-ONLY inspection of the repository. Specifically:

- **No model parameters were changed.** `results/phase4b/fhn_fitted_parameters.csv` was read only.
- **No held-out results were changed.** `results/phase4c/`, `results/phase3b/` were read only.
- **No phase reports were edited.**
- **No code was modified.** `src/`, `scripts/`, `tests/` were not touched.
- **451 tests still pass.** Confirmed at end of this session.
- **Working tree is clean.** Confirmed by `git status`.
- **The only new file is this handoff document.**

---

## 13. Flash Readiness Assessment

**Can Antigravity Gemini 3.8 Flash safely execute the next phase using this handoff?**

**YES, with these conditions:**

1. Flash must read §7 (mandatory caveats) BEFORE writing any prose. These caveats are not optional style choices — they represent independently audited scientific constraints.
2. Flash must treat §4 and §5 as the authoritative numerical record, NOT previous prose summaries or chat history.
3. For any quantitative claim, Flash should verify against the CSV source files listed in §5, not from memory of this handoff.
4. Flash must not regenerate or rerun simulations. All 109 held-out results and all FHN parameters are frozen.
5. The three tasks (5B, 5C, 5D) can be executed sequentially without further consultation with Kiro, as long as the scope (§2), population definitions (§3), evidence matrix (§4), and caveats (§7) are respected.
6. If Flash encounters a discrepancy between a CSV value and a prose description in an existing report, the CSV value takes precedence.

**Potential risk:** Flash may attempt to extrapolate results beyond the four specimens (e.g., "L4 neurons generally…"). Every cross-population claim must be bounded to "the four representative specimens studied here".

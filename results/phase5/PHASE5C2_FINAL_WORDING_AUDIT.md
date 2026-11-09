# INCM Phase 5C.2 — Final F–I Mapping and Model-Reduction Language Audit

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Authoritative Milestone:** Phase 5C.2 Final Wording & F–I Mapping Audit  
**Date:** November 2026  
**Audited Artifacts:**
- [`results/phase5/FINAL_RESEARCH_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/FINAL_RESEARCH_REPORT.md)
- [`results/phase5/PHASE5C_REPORT_VERIFICATION.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C_REPORT_VERIFICATION.md)
- [`results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md)

---

## 1. Executive Summary

Phase 5C.2 performed a targeted, evidence-grounded scientific audit to resolve the remaining two wording and data-mapping concerns across the Phase 5 deliverables:
1. **Population A F–I Mapping:** Constructed an exhaustive, per-sweep mapping of all Population A current-clamp sweeps (COARSE and FINEST) across biological recordings, detailed biophysical models, and FitzHugh–Nagumo (FHN) models. Corrected inaccurate claims regarding monotonic F–I scaling to document that FHN limit cycles rapidly saturate at 9 spikes across a 140 pA current span, biological firing displays non-monotonic cessation at high currents (+430 pA), and detailed models reproduce monotonic scaling once above their shifted rheobase.
2. **Model-Reduction Hierarchy Qualification:** Removed all categorical statements asserting that 2D models cannot mathematically produce adaptation or that a third state variable is a universal mathematical necessity. Reframed the findings around the scientifically supported distinction: the *tested autonomous cubic FHN formulation with linear recovery* cannot sustain multi-second adaptation or decouple latency from rate under the evaluated conditions, providing strong scientific motivation for exploring modelling extensions (e.g., secondary recovery variables or calcium-dependent adaptation processes) rather than proving a universal impossibility theorem.

---

## 2. Population A Exact F–I Mapping

### 2.1 Complete Per-Sweep Empirical Census
Data were extracted directly from the frozen primary artifacts:
- Held-out sweeps: `results/phase3b/heldout/484564503/aggregated_metrics.csv`
- Per-sweep JSON records: `results/phase3b/heldout/484564503/sweep_{id}/summary.json`
- Three-way model comparison: `results/phase4c/fhn_detailed_comparison.csv`
- Primary calibration sweep (Sweep 49): `results/phase3/detailed_model/484564503/summary.json` and `results/phase4b/fhn_calibration_metrics.csv`

All current-clamp pulses have a duration of $1000.0\text{ ms}$, with stimulus onset at $t = 1020.0\text{ ms}$ and offset at $t = 2020.0\text{ ms}$.

| Sweep ID | Protocol Family | Current Amplitude (pA) | Biological Spikes | Detailed-Model Spikes | FHN Spikes | Evaluation Category | Primary Data Source |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **25** | COARSE | $-110.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **26** | COARSE | $-90.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **27** | COARSE | $-70.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **28** | COARSE | $-50.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **29** | COARSE | $-30.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **30** | COARSE | $-10.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **31** | COARSE | $+10.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **32** | COARSE | $+30.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **33** | COARSE | $+50.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **34** | COARSE | $+70.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **35** | COARSE | $+90.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **36** | COARSE | $+110.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **37** | COARSE | $+130.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **38** | COARSE | $+150.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **39** | COARSE | $+170.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **40** | COARSE | $+190.0$ | 0 | 0 | 0 | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **41** | COARSE | $+210.0$ | 0 | 0 | **1** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **42** | COARSE | $+230.0$ | 0 | 0 | **8** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **43** | COARSE | $+250.0$ | 0 | 0 | **8** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **44** | COARSE | $+270.0$ | 0 | 0 | **9** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **45** | COARSE | $+290.0$ | **1** | 0 | **9** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **46** | COARSE | $+310.0$ | **3** | 0 | **9** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **47** | COARSE | $+330.0$ | **6** | 0 | **9** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **48** | COARSE | $+350.0$ | **7** | **1** | **9** | Held-Out | `results/phase4c/fhn_detailed_comparison.csv` |
| **49** | COARSE | $+370.0$ | **9** | **9** | **9** | **Calibration Baseline** | `results/phase3/detailed_model/484564503/summary.json` & `results/phase4b/` |
| **50** | COARSE | $+390.0$ | **9** | **27** | **9** | Held-Out | `results/phase3b/heldout/484564503/sweep_50/summary.json` |
| **51** | COARSE | $+410.0$ | **13** | **39** | **9** | Held-Out | `results/phase3b/heldout/484564503/sweep_51/summary.json` |
| **52** | COARSE | $+430.0$ | **12** | **48** | **8** | Held-Out | `results/phase3b/heldout/484564503/sweep_52/summary.json` |
| **55** | FINEST | $+300.0$ | **1** | 0 | **9** | Held-Out (Protocol Discrepancy) | `results/phase4c/fhn_detailed_comparison.csv` |
| **58** | FINEST | $+310.0$ | **1** | 0 | **9** | Held-Out (Protocol Discrepancy) | `results/phase4c/fhn_detailed_comparison.csv` |
| **60** | FINEST | $+310.0$ | **1** | 0 | **9** | Held-Out (Protocol Discrepancy) | `results/phase4c/fhn_detailed_comparison.csv` |
| **61** | FINEST | $+310.0$ | **1** | 0 | **9** | Held-Out (Protocol Discrepancy) | `results/phase4c/fhn_detailed_comparison.csv` |

### 2.2 Protocols and Amplitude Points That Cannot Be Directly Compared
1. **Sweep 49 (+370.0 pA) is the Primary Calibration Sweep:** Sweep 49 was used to optimize the detailed model and fit the 8 FHN parameters ($C_m, g_L, V_{\mathrm{rest}}, V_{\mathrm{th}}, V_{\mathrm{peak}}, k_v, \tau_w, a_w$). It is not part of the held-out test set in `results/phase3b/heldout/` or `results/phase4c/fhn_heldout_metrics.csv`.
2. **FINEST Protocol Sweeps (Sweeps 55, 58, 60, 61):** Sweeps delivered under the FINEST protocol family (with fine 10 pA steps) reflect protocol-dependent biological non-stationarity. For instance, at $+310.0\text{ pA}$, the biological cell fired **3 spikes** during COARSE Sweep 46, but only **1 spike** in each of the three FINEST sweeps (58, 60, 61). Therefore, COARSE and FINEST sweeps cannot be merged into a single 1D F–I curve without introducing protocol bias.
3. **Subthreshold-to-Suprathreshold Mismatch Across Models:**
   - **FHN Model Rheobase:** $(190, 210]\text{ pA}$ (Fires 1 spike at +210 pA; 8 spikes at +230 pA).
   - **Biological Rheobase:** $(270, 290]\text{ pA}$ (Fires 1 spike at +290 pA; silent at +270 pA).
   - **Detailed Model Rheobase:** $(330, 350]\text{ pA}$ (Fires 1 spike at +350 pA; silent at +330 pA; shifted $+60\text{ pA}$ relative to biology).
4. **FHN Rate Saturation vs. Biological Non-Monotonicity:**
   - The biological recording does not increase strictly monotonically across all suprathreshold steps: it plateaus at 9 spikes between +370 and +390 pA, and decreases from 13 to 12 spikes at +430 pA due to premature late-step cessation / depolarization block.
   - The detailed model exhibits steep, strictly monotonic rate expansion once above its rheobase ($1 \to 9 \to 27 \to 39 \to 48$ spikes across +350 to +430 pA), but lacks premature cessation.
   - The FHN model exhibits **immediate limit-cycle frequency saturation**: after crossing threshold, it fires exactly 9 spikes across the entire 140 pA current span from $+270\text{ pA}$ to $+410\text{ pA}$, before dropping to 8 spikes at $+430\text{ pA}$. FHN does not display monotonic F–I rate expansion in Population A.

---

## 3. Bounding the Model-Reduction Conclusion

### 3.1 Scientific Boundaries
In accordance with rigorous dynamical systems theory and the empirical findings:
- **Supported:** The tested autonomous two-variable cubic FHN formulation with linear recovery rapidly settles into nearly stationary periodic firing under the evaluated conditions.
- **Supported:** It does not reproduce the sustained multi-second adaptation observed in the qualifying biological sweeps.
- **Not established:** All two-dimensional models are incapable of adaptation.
- **Not established:** A third state variable is mathematically necessary for every model capable of reproducing these observations.

### 3.2 Before and After Text Revisions

#### Abstract (Lines 21–22)
- **Before:**
  > *"We conclude that a two-variable dimensional FHN model is sufficient for subthreshold integration and macroscopic threshold gating, but insufficient for spike-train timing, rate coding, and waveform kinetics, which require higher-dimensional dynamical representations."*
- **After:**
  > *"We conclude that the tested two-variable dimensional FHN formulation is sufficient for passive subthreshold integration and macroscopic threshold gating, but cannot reproduce spike-train timing, multi-second rate adaptation, or waveform kinetics under the evaluated parameterizations, providing strong scientific motivation for exploring modelling extensions such as secondary recovery variables or calcium-dependent adaptation processes."*

#### Section 9.2 (Population B Diagram and Narrative)
- **Before (Diagram):**
  > `* FHN Rate Capping: 4 spk vs 14 rec`  
  > `* Both models capture monotonic F-I across moderate currents.`
- **After (Diagram):**
  > `* FHN Rate Capping: Saturates at 17 spk`  
  > `* Det captures monotonic F-I; FHN collapses at strong steps (>230 pA).`
- **Before (Narrative):**
  > *"However, at higher currents (+210 to +290 pA), FHN firing rates saturate prematurely (firing 6 spikes vs. 15 biological spikes at +210 pA) due to cubic nullcline damping, yielding elevated step RMSE ($23.73\text{ mV}$)."*
- **After (Narrative):**
  > *"However, at higher currents (+210 to +270 pA), FHN firing rates saturate at 17 spikes (+210 pA vs. 22 biological spikes) and then collapse precipitously due to strong recovery feedback and cubic damping (firing only 2 spikes at +250 pA and 1 spike at +270 pA, vs. 27 and 29 biological spikes), yielding elevated step RMSE ($23.73\text{ mV}$)."*

#### Section 10 (Tier 2 Taxonomy and Narrative)
- **Before (Table):**
  > `Tier 2: Preserved Under Restrictions | ... monotonic F-I scaling at moderate current.`
- **After (Table):**
  > `Tier 2: Preserved Under Restrictions | ... coarse threshold onset tracking.`
- **Before (Narrative):**
  > *"Monotonic F–I Scaling Across Moderate Currents: Firing rate increases monotonically with injected current amplitude across moderate suprathreshold current ranges in COARSE protocols for Populations A (+290 to +410 pA: 1, 3, 6, 7, 9, 13 recorded spikes vs. 0, 0, 0, 1, 9, 27, 39 detailed spikes)..."*
- **After (Narrative):**
  > *"F–I Firing Rate Scaling and Rate Saturation: The ability to scale firing frequency with injected current differs markedly across models and populations:*  
  > *- **Detailed Multi-Compartment Models:** Once above rheobase, detailed models reproduce monotonic firing rate increases across moderate current ranges in Populations A (+350 to +430 pA: 1, 9, 27, 39, 48 spikes), B (+150 to +270 pA: 11, 16, 19, 23, 26, 29, 33 spikes), C (+350 to +430 pA: 2, 4, 5, 8, 21 spikes), and D (+210 to +350 pA: 1, 9, 14, 18, 21, 24, 26, 29 spikes). However, detailed models overestimate rheobase by +60 pA in Populations A and C, and severely overcount spikes at strong depolarizations (+390 to +430 pA in Pop A) because they lack late-step biological spike cessation.*  
  > *- **Biological Recordings:** Biological neurons exhibit monotonic or non-decreasing firing across moderate suprathreshold ranges, but display plateaus (e.g., Pop A firing 9 spikes at both +370 and +390 pA) and non-monotonic decreases at high currents due to late-step cessation or depolarization block (Pop A dropping to 12 spikes at +430 pA). Furthermore, within-cell non-stationarity between COARSE and FINEST protocols disrupts simple monotonic scaling.*  
  > *- **FitzHugh–Nagumo Models:** FHN models do **not** capture continuous monotonic F–I rate expansion. Due to planar cubic nullcline geometry and strong recovery feedback, FHN limit cycles rapidly saturate in frequency: in Population A, FHN fires exactly 9 spikes across the entire 140 pA span from +270 to +410 pA (dropping to 8 at +430 pA); in Population B, FHN firing rate scales only from +150 to +170 pA (15 to 17 spikes) before plateauing and then collapsing to 1–2 spikes at +250 to +270 pA; and in Population D, FHN firing is heavily suppressed to 1–4 spikes."*

#### Section 12.1 (Direct Answer to the Research Question)
- **Before:**
  > *"2. For Spike-Train Timing, Rate Coding, and Waveform Kinetics: The tested two-variable planar FHN formulation is insufficient. Compressing all voltage-dependent conductances and recovery processes into a single linear recovery variable (w) eliminates the dynamical degrees of freedom required to sustain multi-second spike-frequency adaptation..."*
- **After:**
  > *"2. For Spike-Train Timing, Rate Coding, and Waveform Kinetics: The tested autonomous two-variable cubic FHN formulation with linear recovery is **empirically insufficient**. Compressing active conductances and recovery processes into a single linear recovery variable ($w$) prevents this formulation from sustaining multi-second spike-frequency adaptation, decoupling onset latency from firing rate, capturing rapid sodium upstroke kinetics, or reproducing hyperpolarization-activated inward sag under the evaluated conditions."*

#### Section 12.2 (The Hierarchy of Model Reduction)
- **Before:**
  > *"While non-polynomial 2D systems with subthreshold non-linearities or dynamic reset thresholds can generate richer transient dynamics, reproducing continuous multi-second adaptation and latency-frequency decoupling in current-clamp steps empirically requires higher-dimensional dynamical representations (e.g., a second slow recovery variable $w_2$ or intracellular calcium accumulation $[\mathrm{Ca}^{2+}]_i$ operating on a timescale $\tau \gg 100\text{ ms}$)."*
- **After:**
  > *"While certain non-polynomial 2D dynamical systems with subthreshold non-linearities or dynamic reset thresholds can generate transient slowing, capturing continuous multi-second adaptation and latency-frequency decoupling across experimental current-clamp steps provides strong scientific motivation for exploring model extensions that incorporate secondary slow processes (such as a second recovery variable $w_2$ or intracellular calcium accumulation $[\mathrm{Ca}^{2+}]_i$ operating on a timescale $\tau \gg 100\text{ ms}$), rather than establishing a universal mathematical impossibility for all two-dimensional models."*

#### Section 14 (Conclusion)
- **Before:**
  > *"However, for studies where spike-timing codes, rate adaptation, or dendritic integration are essential, computational models must incorporate at least a third dynamical state variable and fast-activating conductances."*
- **After:**
  > *"However, for studies where spike-timing codes, sustained rate adaptation, or fine waveform kinetics are central, researchers should consider modelling extensions beyond the standard planar cubic formulation, such as incorporating secondary slow recovery variables, calcium-dependent adaptation processes, or fast-activating active conductances."*

---

## 4. Final Consistency Verification

The audit verified that all requirements and non-negotiable boundaries were respected:
1. **Original Data Provenance:** All quantitative metrics (109 sweeps, 40 biological spiking / 69 silent, contingency matrices, open bistability intervals, biological sag) retain their original frozen provenance.
2. **Zero Calibration Contamination:** Held-out data were strictly isolated; no held-out data were accessed or utilized to fit or recalibrate FHN parameters.
3. **Eight Dimensional Parameters:** The eight-parameter count ($C_m, g_L, V_{\mathrm{rest}}, V_{\mathrm{th}}, V_{\mathrm{peak}}, k_v, \tau_w, a_w$) remains consistent across equations, descriptions, and tables.
4. **Morphological Reconstruction Provenance:** Reconstructions for Populations A, B, C, and D remain correctly assigned to their respective recorded donor specimens, with the substitute morphology artifact isolated to exploratory specimen `382982932` in Phase 2.
5. **Population A High-Current Assignments:** Sweeps 50 (+390 pA, 9 rec vs. 27 det), 51 (+410 pA, 13 rec vs. 39 det), and 52 (+430 pA, 12 rec vs. 48 det) remain accurately differentiated.
6. **No Unsupported Mechanistic Hypotheses:** Explanations involving transient potassium currents ($I_A$) or slow calcium processes ($I_{\mathrm{SK}}/I_M$) are framed neutrally as literature-supported hypotheses and potential modelling extensions, rather than proven facts.

---

## 5. Files Changed

1. [`results/phase5/FINAL_RESEARCH_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/FINAL_RESEARCH_REPORT.md) — Refined Abstract, §9.2, §10 (Tier 2), §12.1, §12.2, and §14.
2. [`results/phase5/PHASE5C_REPORT_VERIFICATION.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C_REPORT_VERIFICATION.md) — Updated verification matrix to reflect F–I rate scaling and bounded model-reduction language.
3. [`results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md`](file:///e:/INCM%20project/new incm project/INCM-Project/results/phase5/PHASE5C1_FINAL_REPORT_AUDIT.md) — Harmonized Section 5 and Section 6 with bounded language and complete F–I mapping.
4. [`results/phase5/PHASE5C2_FINAL_WORDING_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C2_FINAL_WORDING_AUDIT.md) — Authored this comprehensive audit artifact.

---

## 6. Unresolved Scientific Limitations

1. **Protocol-Dependent Biological Non-stationarity:** Within-cell firing rate discrepancies between COARSE and FINEST protocols in Populations C and D remain an inherent feature of the biological patch-clamp recording sessions.
2. **Single Representative Specimen ($n=1$):** Each population is represented by a single biological specimen and model pair; statistical distributions across entire cortical laminar sub-types cannot be inferred.
3. **Unquantified Detailed Model Sag:** Detailed models' hyperpolarization sag at $-110\text{ pA}$ was not extracted during Phase 3 evaluation.
4. **Provisional Action-Potential Kinetics:** Fine upstroke velocities ($397\text{--}466\text{ V/s}$ in detailed vs. $5.7\text{--}6.2\text{ V/s}$ in FHN) remain provisional supporting observations due to differences in analog filtering and differentiation stencils.
5. **Biological Cessation Mechanism:** The biophysical ionic mechanism responsible for late-step spike cessation in specimen `484564503` (Layer 4) remains unverified.

---

## 7. Confirmation of Zero Simulations or Recalibrations

- **Simulations Run:** 0
- **Model Recalibrations:** 0
- **Parameter Adjustments:** 0
- **Precursor Phase Modifications:** 0 (all files in `results/phase0/` through `results/phase4c3/`, `data/`, and `tests/` remain 100% bit-for-bit untouched).

---

## 8. Regression Test Suite and Git Status

The automated regression test suite was executed across the full codebase:
```
python -m pytest tests -q
============================= 451 passed in 65.72s =============================
```

### Git Isolation Check
```
On branch ashish-work
Your branch is up to date with 'origin/ashish-work'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	results/phase5/

nothing added to commit but untracked files present (use "git add" to track)
```
All working tree changes remain strictly uncommitted on branch `ashish-work`. The `main` branch was never accessed or modified.


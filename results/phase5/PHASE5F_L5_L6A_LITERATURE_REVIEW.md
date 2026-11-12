# Phase 5F — Layer 5 and Layer 6a Literature Review and Biological Interpretation

**Repository:** `Patel-Princy/INCM_project` · **Branch:** `ashish-work` · **Base commit:** `5509ddd`
**Owner of this contribution:** Ashish (Layer 5 = Population C; Layer 6a = Population D)
**Scope boundary:** Layer 2/3 (Population B) and Layer 4 (Population A) literature is owned by Princy and is **not** written here; §8 lists the fields that must be supplied for integration.
**Frozen-data statement:** No Phase 0–4 data, model, parameter, sweep, CSV, manifest, source file or test was modified, re-run or re-calibrated. All numbers below are read from frozen artifacts or from external databases/literature and are labelled accordingly.

---

## 0. Evidence Labels

Every interpretive statement in this document carries one of the following labels.

| Label | Meaning | Source of truth |
| :---: | :--- | :--- |
| **[M]** | Measured in this project's recordings | Frozen CSVs in `results/phase3b/`, `results/phase4b/`, `results/phase4c/` |
| **[A]** | Allen Cell Types Database metadata or Allen-computed feature (external cross-check, not a frozen project value) | `data/metadata/cell_inventory.csv`; Allen `EphysFeature` API |
| **[L]** | Supported by peer-reviewed literature (see §9 and `PHASE5F_REFERENCE_VERIFICATION.md`) | Cited source |
| **[DP]** | Prediction of the frozen Allen perisomatic (detailed) model | `results/phase3b/` |
| **[RP]** | Prediction of the frozen dimensional FHN (reduced) model | `results/phase4b/`, `results/phase4c/` |
| **[H]** | Hypothesis: plausible, consistent with [L], but **not demonstrated** for this specimen | — |

Derived values marked **[M, derived]** were obtained by read-only arithmetic on frozen CSV columns (scripts kept in the git-ignored `tmp/phase5f/` workspace); no simulation was run.

---

## 1. The Canonical V1 Laminar Hierarchy (Placement of All Four Populations)

A simplified "canonical" description of neocortical processing, developed largely from cat and rodent sensory cortex, routes feedforward thalamic input primarily to Layer 4, from Layer 4 to Layers 2/3, from Layers 2/3 to Layer 5, and from deep layers to subcortical targets, with Layer 6 corticothalamic neurons returning feedback to the thalamus (Douglas & Martin, 2004; Thomson, 2010; Harris & Mrsic-Flogel, 2013) **[L]**. Cortical excitatory neurons fall into a small number of main projection classes—intratelencephalic (IT), pyramidal-tract/extratelencephalic (PT/ET) and corticothalamic (CT)—whose properties are largely conserved across areas (Harris & Shepherd, 2015; Baker et al., 2018) **[L]**. The canonical scheme is a simplification: thalamic axons also reach deep layers and the deep layers receive substantial non-L2/3 input (Harris & Mrsic-Flogel, 2013; Harris & Shepherd, 2015) **[L]**.

| Population | Allen layer [A] | Cre line [A] | Canonical position (simplified) [L] | Detailed literature owner |
| :---: | :---: | :--- | :--- | :--- |
| **A** | VISp L4 | Rorb-IRES2-Cre | Principal thalamorecipient layer; feedforward relay to L2/3 | Princy (pending) |
| **B** | VISp L2/3 | Nr5a1-Cre | Receives L4 input; intracortical (corticocortical) output; projects to L5 | Princy (pending) |
| **C** | VISp L5 | Rbp4-Cre_KL100 | Principal cortical output layer to cortical (IT) and subcortical (PT/ET) targets | Ashish (§2–§3) |
| **D** | VISp L6a | Ntsr1-Cre_GN220 | Origin of corticothalamic feedback to dLGN/TRN; intracortical modulation of L4–L6 | Ashish (§4–§5) |

*Note on Population B's Cre line:* a Phase 5 handoff document (`PHASE5_BASELINE_AND_FLASH_HANDOFF.md`) already records that Nr5a1-Cre is usually described as L4-associated, so specimen B's L2/3 assignment rests on the Allen layer annotation **[A]**, not on the driver line. This is passed to the L2/3 owner as an integration item (§8).

---

## 2. Layer 5 — Literature Background

### 2.1 Circuit position and projection classes
- L5 pyramidal neurons integrate inputs from many sources and distribute outputs to cortical and subcortical structures; in mouse V1, Kim et al. (2015) distinguished cortico-cortical (CC), cortico-subcortical (CS) and a cortico-cortical non-striatal (CC-NS) type, which differ in long-range input, morphology, physiology and visual responses (CS neurons were more direction-selective and preferred faster stimuli) **[L, mouse V1]**.
- Using retrograde labelling plus in vivo imaging in mouse V1, Lur et al. (2016) reported that corticotectal, corticostriatal and corticocortical L5 neurons encode visual features differently, although the populations overlap **[L, mouse V1]**.
- The two broad deep-layer classes are IT neurons (axons confined to the telencephalon: cortex, striatum) and ET/PT neurons (additional targets outside the telencephalon: thalamus, midbrain, pons, spinal cord) (Shepherd, 2013; Harris & Shepherd, 2015; Baker et al., 2018) **[L, review]**.
- L5 PT/ET neurons also send "driver"-type input to higher-order thalamus, whereas L6 CT input to first-order thalamus is "modulator"-type (Sherman & Guillery, 1998) **[L, review/theory]**.
- Transcriptomic taxonomies of mouse V1 resolve L5 IT, L5 PT (ET) and L5 NP subclasses and match glutamatergic types to projection targets using retrograde labelling (Tasic et al., 2016, 2018) **[L, mouse V1]**.

### 2.2 Morphology and dendrites
- In rat visual cortex, L5 pyramids divide into cells with thick apical dendrites reaching layer 1 (thick-tufted) and cells with thinner apical dendrites not reaching layer 1; burst firing to current pulses was confined to thick-tufted cells (Mason & Larkman, 1990) **[L, rat V1]**.
- Two genetically identified L5 types (thick-tufted vs. slender-tufted) in mouse visual and somatosensory cortex show mostly cell-type-specific rather than area-specific properties, "with important exceptions" (Groh et al., 2010) **[L, mouse V1 + S1]**.
- Thick-tufted L5 neurons can generate dendritic Ca²⁺ spikes coupled to back-propagating somatic action potentials (BAC firing; Larkum, Zhu & Sakmann, 1999; reviewed in Larkum, 2013), which a detailed L5b model reproduces only with active dendrites (Hay et al., 2011) **[L, rat S1 / model]**.
- **Relevance for this project:** the Allen perisomatic models place active conductances at the soma with passive dendrites (Gouwens et al., 2018) **[L]**, and FHN is a single-compartment model **[RP]**. Neither model tier can represent dendritic electrogenesis, and somatic step injection does not probe it. Dendritic properties are therefore **outside** what this project can evaluate.

### 2.3 Intrinsic electrophysiology by projection class
- Classical cortical firing classes are regular-spiking (RS, adapting), intrinsically bursting (IB) and fast-spiking (Connors & Gutnick, 1990) **[L, review]**.
- In projection-identified L5 neurons outside V1:
  - Mouse somatosensory cortex: corticothalamic/corticotrigeminal (PT-like) neurons differ from callosal/corticostriatal (IT-like) neurons in morphology, intrinsic membrane properties, firing and afterpotentials (Hattox & Nelson, 2007) **[L, mouse S1]**.
  - Rat mPFC: commissural (IT) neurons show spike-frequency accommodation and high temporal summation, whereas corticopontine (PT) neurons accelerate in firing and resonate; the subthreshold differences are accounted for by the h-current (Dembrow et al., 2010) **[L, rat PFC]**.
  - Mouse motor cortex: I_h expression is high in corticospinal (PT) and low in corticostriatal/corticocortical (IT) neurons (Sheets et al., 2011) **[L, mouse M1]**.
- **Generalisation caveat:** these projection-identified physiology studies are from S1, PFC and M1, not V1. Groh et al. (2010) support partial cross-area conservation for two L5 types, but this is not a substitute for V1 projection identification **[L, limitation]**.

### 2.4 Heterogeneity and the Rbp4-Cre_KL100 driver line
- Rbp4-Cre_KL100 is a GENSAT BAC-Cre line characterised for L5 expression (Gerfen et al., 2013; Harris et al., 2014) **[L]**.
- In the Allen mouse connectome analysis, Rbp4 was used as a broad L5 line; the authors note that "within L5, IT cells have the most overlap with Rbp4 targets" while also using Rbp4 to represent L5 PT because of its comprehensive coverage (Harris et al., 2019) **[L]**. **Rbp4-Cre_KL100 labels both IT and PT neurons and does not by itself identify projection class.**
- Allen electrophysiological classification of the same database shows multiple e-types and m-types within each layer, with correspondence to transcriptomic types via the same transgenic lines (Gouwens et al., 2019) **[L, mouse V1]**.

---

## 3. Layer 5 Specimen Profile — Population C (`471129934`)

| Item | Value | Label |
| :--- | :--- | :---: |
| Allen annotation | VISp5, Rbp4-Cre_KL100;Ai14, spiny, apical dendrite intact, dendrite-only reconstruction | [A] |
| Detailed model | `480624414` (perisomatic, specimen's own reconstruction `495335491`) | [A] |
| Calibration sweep | Sweep 51, +410 pA COARSE: 9 recorded spikes, first-spike latency 23.13 ms | [M] |
| Pre-stimulus baseline | −69.34 mV (calibration-sweep baseline, `fhn_calibration_metrics.csv`) | [M] |
| Apparent R_in (10-ms, 50-pA test pulse, window 8–14.5 ms) | 31.3 MΩ | [M] |
| Steady-state R_in on 1000-ms hyperpolarising steps (median, n=5) | 90.6 MΩ | [M, derived] |
| Allen input resistance / τ_m / V_rest | 94.38 MΩ / 15.60 ms / −68.62 mV | [A] |
| Rheobase (COARSE bracket) | (270, 290] pA (Allen: 290 pA) | [M] / [A] |
| First-spike latency vs. current | 75.03 ms (290 pA) → 55.82 → 43.77 → 36.86 → 30.58 → 27.79 → 23.13 → 22.72 ms (430 pA) | [M] |
| Spike counts 290→430 pA (COARSE) | 1, 1, 2, 3, 5, 6, 9, 11 | [M] |
| Adaptation (last/first ISI) | 1.89× (350 pA), 2.60× (370), 3.06× (390), 11.27× (430 pA; frozen `phase4c3_biological_adaptation_scope.csv` max 11.27, `phase4c2_isi_transient_adaptation.csv` 11.2733) | [M, derived] |
| Burst doublets | None; minimum first ISI 27.12 ms (at +430 pA) | [M, derived] |
| Sag at −110 pA | 0.63 mV (Allen sag ratio 0.0468) | [M] / [A] |
| AP threshold / peak / upstroke:downstroke | −33.8 mV / 35.5 mV / 3.54 | [A] |

**Interpretation.**
1. Specimen C is a **regular-spiking, strongly adapting** L5 neuron with small sag and no burst doublets at any tested current **[M]**. Allen's feature extraction also reports `has_burst = False` **[A]**.
2. In projection-identified studies outside V1, strong accommodation and low h-current/sag are more often associated with IT than with PT neurons (Dembrow et al., 2010; Sheets et al., 2011; Hattox & Nelson, 2007; Baker et al., 2018) **[L]**. An IT-like identity for specimen C is therefore a **hypothesis [H]**. It is **not** a classification, because (i) Rbp4-Cre_KL100 labels both IT and PT neurons **[L]**, (ii) no retrograde or axonal data exist for this cell **[A]**, (iii) the supporting physiology is from other areas **[L, limitation]**, and (iv) n = 1.
3. The detailed model raises the COARSE rheobase by +60 pA (4 of 11 spiking sweeps detected) and sits a median +4.71 mV above the recorded baseline on held-out sweeps (+5.69 mV on the calibration sweep: −63.65 vs. −69.34 mV) **[DP, M derived]**. When suprathreshold, it reproduces waveform best of all populations (step RMSE 4.15 mV; overall RMSE 4.73 mV; r = 0.9610) **[DP]**.
4. FHN detects the threshold transition well (TP 10, FP 2, FN 1, TN 21; overall RMSE 4.81 mV) but contracts to a stationary limit cycle within ≤ 2 cycles and cannot express the 11× ISI expansion **[RP]**. Its bistable interval (360.03, 385.33) pA lies inside the recorded transition from 3 to 6 spikes **[RP, M]**.

---

## 4. Layer 6a — Literature Background

### 4.1 Corticothalamic feedback, feedforward vs. feedback, driver vs. modulator
- L6 is the origin of the massive cortical feedback to thalamus (Brumberg et al., 2003; Thomson, 2010) and "the sole purveyor of corticothalamic feedback to first-order thalamus" (Kirchgessner et al., 2020) **[L]**.
- L6 CT axons excite thalamic relay cells directly and inhibit them indirectly via the thalamic reticular nucleus (TRN) (Lam & Sherman, 2010; Crandall et al., 2015) **[L, S1]**.
- In the driver/modulator framework, L6 CT input to first-order relays such as dLGN is classed as modulatory (it alters transmission probability and engages metabotropic receptors), in contrast to retinal driver input (Sherman & Guillery, 1998) **[L, theory/review]**. Feedback thus forms a thalamo-cortico-thalamic loop rather than a simple feedforward relay (Briggs & Usrey, 2008; Sillito, Cudeiro & Jones, 2006) **[L, review]**.

### 4.2 State and frequency dependence of CT influence
- In somatosensory slices, CT influence is mainly suppressive at low frequency and switches to enhancement at higher frequency, through short-term plasticity in multiple circuit components (Crandall et al., 2015) **[L, mouse S1]**.
- In awake mouse V1→dLGN/pulvinar, sustained L6 CT photostimulation suppresses thalamic activity whereas 10 Hz stimulation facilitates it (Kirchgessner et al., 2020) **[L, mouse visual]**.
- Driving Ntsr1 projections reduced dLGN spike counts, but removing them produced both increases and decreases (Denman & Contreras, 2015) **[L, mouse visual]**.
- In awake mice, CT feedback sharpens dLGN receptive fields and increases surround suppression, probably via the visual TRN (Born et al., 2021) **[L, mouse visual]**.
- Within cortex, L6 controls the gain of upper-layer visual responses without changing orientation tuning (Olsen et al., 2012). It does so partly by recruiting translaminar fast-spiking interneurons (Bortone et al., 2014), and L6 CT axons strongly excite L5a while suppressing L4 (Kim et al., 2014) **[L, mouse V1/S1]**.

### 4.3 L6a vs. L6b and CT vs. intracortical L6 neurons
- Layer 6b (adjacent to white matter) is generally treated as the adult derivative of the developmental subplate, which is distinct in origin and properties from L6a (reviewed by Hoerder-Suabedissen & Molnár, 2015) **[L, review; the abstract does not itself define L6b — medium confidence]**. Specimen D is annotated VISp6a **[A]**, so subplate/L6b literature does not apply directly.
- L6a contains at least two principal excitatory classes: CT neurons and intracortical (corticocortical, CC) neurons (Thomson, 2010; Bortone et al., 2014; Vélez-Fort et al., 2014) **[L]**.
  - In mouse V1, CT-projecting cells were ultrasparse-firing and sharply tuned in vivo, while CC cells were broadly tuned and predominantly innervated by deep-layer V1 neurons (Vélez-Fort et al., 2014) **[L, mouse V1]**.
  - In mouse V1 slices, antidromically identified corticofugal (likely corticogeniculate) L6 neurons were more excitable, had narrower action potentials and smaller AHPs than neighbouring non-antidromic neurons, with similar input resistances and longer apical dendrites (Brumberg et al., 2003) **[L, mouse V1]**.
  - Transcriptomic taxonomies separate L6 IT, L6 CT and L6b subclasses (Tasic et al., 2016, 2018) **[L, mouse V1]**.

### 4.4 The Ntsr1-Cre_GN220 driver line
- Ntsr1-Cre (GN220) is a GENSAT BAC-Cre line (Gong et al., 2007; Gerfen et al., 2013) **[L]**.
- Of the two major L6 excitatory types, the NTSR1-Cre line selectively targets CT neurons and not intracortically projecting cells (Bortone et al., 2014). The GN220 line was used specifically to manipulate an L6 corticogeniculate population (Denman & Contreras, 2015) **[L, mouse V1]**.
- **Limitation:** selectivity is established at the population level. For this specimen, CT identity is **plausible by genotype** but unconfirmed, because no axonal or retrograde data exist **[A, H]**.

### 4.5 Delayed first-spike latency — what the literature does and does not support
- Delayed spike onset is often attributed to slowly inactivating A-type/D-type K⁺ currents. However, **no verified V1-specific source attributing delayed firing to L6 CT neurons was identified in this review**. The Phase 4C.1 audit's attribution of Pop D delay to "Kv4/Kv1.4 per literature" (`scripts/audit_phase4c1_heldout.py`) has no citation and is treated as **[H]**.
- Allen's feature extraction reports `has_delay = False` for specimen D **[A]**.
- The measured latency of specimen D is **graded with current** (§5), consistent with slow subthreshold charging near threshold as well as with an outward current. The mechanism is unresolved **[M, H]**.

---

## 5. Layer 6a Specimen Profile — Population D (`471786879`)

| Item | Value | Label |
| :--- | :--- | :---: |
| Allen annotation | VISp6a, Ntsr1-Cre_GN220;Ai14, spiny | [A] |
| Detailed model | `480632594` (perisomatic, specimen's own reconstruction `491392868`) | [A] |
| Calibration sweep | Sweep 42, +250 pA COARSE: 13 recorded spikes, latency 57.95 ms | [M] |
| Pre-stimulus baseline | −75.71 mV | [M] |
| Apparent R_in (test pulse) | 52.6 MΩ | [M] |
| Steady-state R_in on 1000-ms hyperpolarising steps (median, n=6) | 125.5 MΩ | [M, derived] |
| Allen input resistance / τ_m / V_rest | 115.47 MΩ / 13.67 ms / −75.92 mV | [A] |
| Rheobase (COARSE bracket) | (190, 210] pA (Allen: 210 pA) | [M] / [A] |
| First-spike latency vs. current (COARSE) | 113.82 ms (210 pA), 72.88 (230), 57.95 (250), 47.06 (270), 41.74 (290), 37.35 (310), 30.59 (330), 27.37 ms (350 pA) | [M] |
| FINEST +240 pA (sweeps 52–54) | 1 spike each, latencies 119.67, 109.81, 180.02 ms | [M] |
| Spike counts 210→350 pA (COARSE) | 5, 10, 13, 17, 19, 21, 24, 27 | [M] |
| Adaptation (last/first ISI) | 1.13× (210 pA) rising to 2.47× (350 pA) | [M, derived] |
| Sag at −110 pA | 1.86 mV — largest of the four specimens (Allen sag ratio 0.1228) | [M] / [A] |
| f–I slope; AP threshold / peak / upstroke:downstroke | 0.192 Hz/pA; −33.3 mV / 44.8 mV / 2.81 | [A] |

**Interpretation.**
1. Specimen D fires repetitively over a wide current range, with moderate adaptation and a near-threshold latency that shortens monotonically from ≈114 ms to ≈27 ms as current increases **[M]**. The previously reported "> 1000 ms near threshold" is **not supported** by the frozen spike times (see the QA report).
2. Its largest sag of the four cells **[M]** is a measured property only. It cannot be assigned to a specific channel without pharmacology **[H]**.
3. A CT identity is consistent with the Ntsr1-GN220 genotype (Bortone et al., 2014) **[L]**, but remains a hypothesis for this specimen **[H]**. The in vivo ultrasparse firing of V1 CT cells (Vélez-Fort et al., 2014) concerns synaptically driven activity and **cannot** be compared with the cell's in vitro current-step excitability **[L, limitation]**.
4. The detailed model reproduces rheobase, detection (TP 10, FP 0, FN 0, TN 16), the calibration latency (52.97 ms vs. 57.95 ms) and spike count (14 vs. 13) **[DP]**. It does not reproduce the near-threshold behaviour: 1 spike at 958.91 ms at +210 pA vs. 5 recorded spikes from 113.82 ms, and 11 spikes from 67.30 ms vs. 1 recorded spike in the FINEST +240 pA sweeps **[DP, M]**.
5. FHN detects threshold (TP 10, FP 1, FN 0, TN 15) and matches the calibration latency (59.9 ms), but only with 4 spikes. It averages 1.04 spikes per held-out sweep vs. 4.85 recorded, and across 961 (C_m, τ_w) combinations latency ≥ 50 ms and ≥ 12 spikes were never achieved together **[RP]**.

---

## 6. Cross-Laminar Synthesis

### 6.1 Cross-laminar table
Literature roles for A and B are intentionally left for the L2/3–L4 owner. Measured/model fields are taken from frozen project files.

| Pop | Layer | Literature role | Measured [M] | Detailed [DP] | FHN [RP] |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **A** | L4 | *Pending Princy contribution* (canonical: principal thalamorecipient layer [L]) | Baseline −73.73 mV; test-pulse R_in 44.3 MΩ (step 134.4 MΩ); rheobase (270, 290] pA; sag 0.80 mV; late-step firing cessation ≥ +390 pA | Baseline −61.07 mV; +60 pA rheobase shift; 4/11 spiking sweeps; step RMSE 8.30 mV | 15 spiking sweeps (11 recorded); step RMSE 22.10 mV; overall RMSE 8.24 mV; spike count saturates at 9 |
| **B** | L2/3 | *Pending Princy contribution* (canonical: L4 recipient, corticocortical output [L]) | Baseline −75.90 mV; test-pulse R_in 80.3 MΩ (step 217.5 MΩ); rheobase (110, 130] pA; sag 1.13 mV; up to 29 spikes at +270 pA | 6/8 spiking sweeps; step RMSE 7.61 mV; overall RMSE 4.04 mV | 6/8 spiking sweeps; rate collapses ≥ +250 pA; step RMSE 23.73 mV |
| **C** | L5 | Main cortical output layer with IT and PT/ET classes (§2) [L] | Baseline −69.34 mV; test-pulse R_in 31.3 MΩ (step 90.6 MΩ); rheobase (270, 290] pA; RS, no bursts; ISI ratio up to 11.27×; sag 0.63 mV | +4.71 mV median baseline offset; +60 pA rheobase shift; 4/11; step RMSE 4.15 mV; overall RMSE 4.73 mV | TP 10/FP 2/FN 1/TN 21; overall RMSE 4.81 mV; stationary limit cycle (no SFA) |
| **D** | L6a | CT feedback to dLGN/TRN; intracortical gain control (§4) [L] | Baseline −75.71 mV; test-pulse R_in 52.6 MΩ (step 125.5 MΩ); rheobase (190, 210] pA; graded latency 113.8→27.4 ms; sag 1.86 mV | Rheobase matched; 10/10; overall RMSE 2.23 mV; overfires in FINEST +240 pA (11 vs. 1) | TP 10/FP 1/FN 0/TN 15; overall RMSE 9.03 mV; latency–rate trade-off (≤ 4 spikes at ≥ 50 ms latency) |

Pooled held-out detection (109 sweeps; 40 spiking, 69 silent): detailed TP 24, FP 0, FN 16, TN 69 (sensitivity 60.0%, specificity 100%); FHN TP 37, FP 7, FN 3, TN 62 (sensitivity 92.5%, specificity ≈ 89.9%) **[DP, RP]**.

### 6.2 Relating biological properties to detailed-vs-FHN differences
| Property | What is observed | Interpretation (label) |
| :--- | :--- | :--- |
| **R_in** | FHN reproduces the 10-ms test-pulse *apparent* R_in (exact for A and C; within 2.1% for B and D) **[RP]**. On 1000-ms hyperpolarising steps the recorded steady-state R_in (90.6–217.5 MΩ) is 2.4–3.0× the test-pulse value and 2.5–3.2× the FHN steady-state R_in on the same steps (30.1–72.1 MΩ) **[M, derived; RP]**. Allen's R_in (94.4 MΩ for C, 115.5 MΩ for D) agrees with the steady-state value **[A]**. | The calibration target was a pre-steady-state quantity: τ_m ≈ 14–21 ms **[A]**, so a 10-ms pulse samples the charging transient. FHN therefore matches the **shape** of subthreshold responses (r² ≥ 0.996 on hyperpolarising sweeps) but under-predicts their steady-state **amplitude** by ≈ 3× (coefficient of determination R² = −2.28 to −0.07 on the same sweeps, `phase4c1_subthreshold_audit.csv`) **[M, RP]**. The detailed models under-predict amplitude for A and C as well **[DP]**. |
| **Rheobase** | FHN detects threshold well; detailed models shift rheobase +60 pA in A and C **[RP, DP]** | FHN's threshold is set by the fold/Hopf geometry fitted to one suprathreshold sweep, not by R_in. Its success in detection does not imply correct subthreshold gain **[RP, H]**. |
| **V_rest** | FHN V_rest equals the recorded baseline by construction. Detailed baselines: A +12.66 mV, C +4.7–5.7 mV, B/D < 0.3 mV **[M, DP]** | A detailed-model offset raises overall RMSE and can mask waveform fidelity (Pop A) **[DP]**. |
| **Threshold** | FHN's V_th (C −48.3, D −57.5 mV) is the middle root of the cubic, not the AP threshold measured by Allen (≈ −33 mV) **[RP, A]** | V_th should not be read as a measured AP threshold **[RP]**. |
| **SFA** | ISI ratio up to 11.27× (C) and 2.47× (D) **[M]**; FHN stationary within ≤ 2 cycles **[RP]** | Sustained adaptation requires a slow variable beyond the single recovery variable (Benda & Herz, 2003; Pospischil et al., 2008); generalized integrate-and-fire models with additional mechanisms predict held-out spiking better (Teeter et al., 2018) **[L]**. |
| **Latency** | D latency graded 113.8→27.4 ms **[M]**; FHN cannot combine ≥ 50 ms latency with ≥ 12 spikes **[RP]** | Separating slow onset from fast repetitive firing needs ≥ 2 distinct slow timescales; the mechanism in the cell is unresolved **[H]**. |
| **Sag** | Recorded 0.63–1.86 mV at −110 pA **[M]**. FHN contains no hyperpolarization-activated conductance **[RP]**. | The manuscript's "0.00 mV FHN sag" is not backed by a stored computation (see QA report). An analytic linearisation of the frozen parameters predicts a fast, transient, recovery-variable undershoot (≈ 1.7–4.1 mV, peaking 9–38 ms after onset) that is not an I_h mechanism **[RP, derived analytically; requires formal confirmation]**. |
| **Firing rate / f–I** | B and D sustain high rates; FHN saturates or collapses **[M, RP]** | A planar cubic oscillator near a subcritical Hopf has a narrow frequency range (Izhikevich, 2007); adaptation linearises f–I curves (Ermentrout, 1998) **[L]**. |

### 6.3 What a two-variable model retains, and what needs more state variables
- **Retained [RP]:**
  - Resting state.
  - Test-pulse apparent R_in.
  - The time course (not the amplitude) of hyperpolarising responses.
  - An all-or-none excitability transition with bistability (subcritical Hopf, class-2-like onset; Prescott, De Koninck & Sejnowski, 2008; Izhikevich, 2007) **[L]**.
- **Requires more state variables [L/H]:**
  - Sustained SFA: a slow adaptation current such as M-type or AHP-type, with τ ≫ 100 ms (Benda & Herz, 2003; Pospischil et al., 2008).
  - Latency–rate decoupling: a separate slow outward/inactivating current [H].
  - Hyperpolarization-activated sag: an I_h-like variable (Dembrow et al., 2010; Sheets et al., 2011).
  - Fast spike waveform: separate fast Na⁺/K⁺ kinetics as in HH (Hodgkin & Huxley, 1952).
  - Dendritic electrogenesis: multiple compartments (Larkum et al., 1999; Hay et al., 2011).
- **Trade-off, not superiority:**
  - FHN's higher sensitivity (92.5% vs. 60.0%) comes with lower specificity (89.9% vs. 100%), 3× under-predicted steady-state subthreshold amplitude, 12–24 mV step RMSE and no adaptation.
  - The detailed models carry calibration offsets but reproduce waveform and spike trains better where suprathreshold.

---

## 7. Claim Boundaries Applied
1. **n = 1 per layer.** Every statement about "L5" or "L6a" in this project is a case study of one specimen.
2. **Cre line ≠ projection class.** Rbp4-Cre_KL100 is mixed IT/PT. Ntsr1-Cre_GN220 is CT-selective at population level only. No IT/PT/ET/CT label is assigned to any specimen.
3. **No axon-target inference.** Morphology files are dendrite-only reconstructions; no axonal target is inferred.
4. **No channel-mechanism claims.** Adaptation, latency and sag mechanisms are hypotheses; neither model tier was used to identify them.
5. **Cross-area literature.** Projection-identified physiology outside V1 (S1, M1, PFC) is cited as context, labelled by species and area.

---

## 8. Integration Requirements for the L2/3 and L4 Contribution (Princy)
These items are required for a complete four-population manuscript. They are **not** written here.

| ID | Requirement | Population |
| :---: | :--- | :---: |
| P-1 | Literature role of L4 spiny neurons in mouse V1 (thalamorecipient input, star/pyramid morphology, Rorb-IRES2-Cre specificity) with verified citations | A |
| P-2 | Literature role of L2/3 pyramidal neurons in mouse V1 (corticocortical output, intrinsic physiology) with verified citations | B |
| P-3 | Discussion of why an Nr5a1-Cre specimen is annotated VISp2/3 (Nr5a1 is usually described as L4-associated) | B |
| P-4 | Biological context for Pop A late-step firing cessation (+390 to +430 pA), labelled [H] where unverified | A |
| P-5 | Resolution of the Pop A baseline-offset figures used inconsistently in the manuscript: +13.6 mV (Abstract, §12.3), "ΔV_baseline = +13.25 mV" (§9.1; 13.25 mV is the non-step RMSE in `PHASE5_CROSS_POPULATION_SYNTHESIS.md`), and the calibration-sweep difference of +12.66 mV (−61.07 vs. −73.73 mV) | A |
| P-6 | Confirmation of the provenance correction to Pop B V_rest (Table 1 / §9.2: −78.96 → −75.90 mV) | B |
| P-7 | Cross-laminar table "Literature role" cells for A and B (§6.1) | A, B |

---

## 9. References Used in This Review
All entries were verified against Crossref and/or PubMed (see `PHASE5F_REFERENCE_VERIFICATION.md`).

- Baker, A., Kalmbach, B., Morishima, M., Kim, J., Juavinett, A., Li, N., & Dembrow, N. (2018). Specialized subpopulations of deep-layer pyramidal neurons in the neocortex: bridging cellular properties to functional consequences. *J. Neurosci.*, 38(24), 5441–5455. https://doi.org/10.1523/JNEUROSCI.0150-18.2018
- Benda, J., & Herz, A. V. M. (2003). A universal model for spike-frequency adaptation. *Neural Comput.*, 15(11), 2523–2564. https://doi.org/10.1162/089976603322385063
- Born, G., Schneider-Soupiadis, F. A., Erisken, S., et al. (2021). Corticothalamic feedback sculpts visual spatial integration in mouse thalamus. *Nat. Neurosci.*, 24(12), 1711–1720. https://doi.org/10.1038/s41593-021-00943-0
- Bortone, D. S., Olsen, S. R., & Scanziani, M. (2014). Translaminar inhibitory cells recruited by layer 6 corticothalamic neurons suppress visual cortex. *Neuron*, 82(2), 474–485. https://doi.org/10.1016/j.neuron.2014.02.021
- Briggs, F., & Usrey, W. M. (2008). Emerging views of corticothalamic function. *Curr. Opin. Neurobiol.*, 18(4), 403–407. https://doi.org/10.1016/j.conb.2008.09.002
- Brumberg, J. C., Hamzei-Sichani, F., & Yuste, R. (2003). Morphological and physiological characterization of layer VI corticofugal neurons of mouse primary visual cortex. *J. Neurophysiol.*, 89(5), 2854–2867. https://doi.org/10.1152/jn.01051.2002
- Connors, B. W., & Gutnick, M. J. (1990). Intrinsic firing patterns of diverse neocortical neurons. *Trends Neurosci.*, 13(3), 99–104. https://doi.org/10.1016/0166-2236(90)90185-D
- Crandall, S. R., Cruikshank, S. J., & Connors, B. W. (2015). A corticothalamic switch: controlling the thalamus with dynamic synapses. *Neuron*, 86(3), 768–782. https://doi.org/10.1016/j.neuron.2015.03.040
- Dembrow, N. C., Chitwood, R. A., & Johnston, D. (2010). Projection-specific neuromodulation of medial prefrontal cortex neurons. *J. Neurosci.*, 30(50), 16922–16937. https://doi.org/10.1523/JNEUROSCI.3644-10.2010
- Denman, D. J., & Contreras, D. (2015). Complex effects on in vivo visual responses by specific projections from mouse cortical layer 6 to dorsal lateral geniculate nucleus. *J. Neurosci.*, 35(25), 9265–9280. https://doi.org/10.1523/JNEUROSCI.0027-15.2015
- Douglas, R. J., & Martin, K. A. C. (2004). Neuronal circuits of the neocortex. *Annu. Rev. Neurosci.*, 27, 419–451. https://doi.org/10.1146/annurev.neuro.27.070203.144152
- Ermentrout, B. (1998). Linearization of F-I curves by adaptation. *Neural Comput.*, 10(7), 1721–1729. https://doi.org/10.1162/089976698300017106
- Gerfen, C. R., Paletzki, R., & Heintz, N. (2013). GENSAT BAC cre-recombinase driver lines to study the functional organization of cerebral cortical and basal ganglia circuits. *Neuron*, 80(6), 1368–1383. https://doi.org/10.1016/j.neuron.2013.10.016
- Gong, S., Doughty, M., Harbaugh, C. R., Cummins, A., Hatten, M. E., Heintz, N., & Gerfen, C. R. (2007). Targeting Cre recombinase to specific neuron populations with bacterial artificial chromosome constructs. *J. Neurosci.*, 27(37), 9817–9823. https://doi.org/10.1523/JNEUROSCI.2707-07.2007
- Gouwens, N. W., Berg, J., Feng, D., et al. (2018). Systematic generation of biophysically detailed models for diverse cortical neuron types. *Nat. Commun.*, 9, 710. https://doi.org/10.1038/s41467-017-02718-3
- Gouwens, N. W., Sorensen, S. A., Berg, J., et al. (2019). Classification of electrophysiological and morphological neuron types in the mouse visual cortex. *Nat. Neurosci.*, 22(7), 1182–1195. https://doi.org/10.1038/s41593-019-0417-0
- Groh, A., Meyer, H. S., Schmidt, E. F., Heintz, N., Sakmann, B., & Krieger, P. (2010). Cell-type specific properties of pyramidal neurons in neocortex underlying a layout that is modifiable depending on the cortical area. *Cereb. Cortex*, 20(4), 826–836. https://doi.org/10.1093/cercor/bhp152
- Harris, J. A., Hirokawa, K. E., Sorensen, S. A., et al. (2014). Anatomical characterization of Cre driver mice for neural circuit mapping and manipulation. *Front. Neural Circuits*, 8, 76. https://doi.org/10.3389/fncir.2014.00076
- Harris, J. A., Mihalas, S., Hirokawa, K. E., et al. (2019). Hierarchical organization of cortical and thalamic connectivity. *Nature*, 575(7781), 195–202. https://doi.org/10.1038/s41586-019-1716-z
- Harris, K. D., & Mrsic-Flogel, T. D. (2013). Cortical connectivity and sensory coding. *Nature*, 503(7474), 51–58. https://doi.org/10.1038/nature12654
- Harris, K. D., & Shepherd, G. M. G. (2015). The neocortical circuit: themes and variations. *Nat. Neurosci.*, 18(2), 170–181. https://doi.org/10.1038/nn.3917
- Hattox, A. M., & Nelson, S. B. (2007). Layer V neurons in mouse cortex projecting to different targets have distinct physiological properties. *J. Neurophysiol.*, 98(6), 3330–3340. https://doi.org/10.1152/jn.00397.2007
- Hay, E., Hill, S., Schürmann, F., Markram, H., & Segev, I. (2011). Models of neocortical layer 5b pyramidal cells capturing a wide range of dendritic and perisomatic active properties. *PLoS Comput. Biol.*, 7(7), e1002107. https://doi.org/10.1371/journal.pcbi.1002107
- Hodgkin, A. L., & Huxley, A. F. (1952). A quantitative description of membrane current and its application to conduction and excitation in nerve. *J. Physiol.*, 117(4), 500–544. https://doi.org/10.1113/jphysiol.1952.sp004764
- Hoerder-Suabedissen, A., & Molnár, Z. (2015). Development, evolution and pathology of neocortical subplate neurons. *Nat. Rev. Neurosci.*, 16(3), 133–146. https://doi.org/10.1038/nrn3915
- Izhikevich, E. M. (2007). *Dynamical Systems in Neuroscience*. MIT Press. https://doi.org/10.7551/mitpress/2526.001.0001
- Kim, E. J., Juavinett, A. L., Kyubwa, E. M., Jacobs, M. W., & Callaway, E. M. (2015). Three types of cortical layer 5 neurons that differ in brain-wide connectivity and function. *Neuron*, 88(6), 1253–1267. https://doi.org/10.1016/j.neuron.2015.11.002
- Kim, J., Matney, C. J., Blankenship, A., Hestrin, S., & Brown, S. P. (2014). Layer 6 corticothalamic neurons activate a cortical output layer, layer 5a. *J. Neurosci.*, 34(29), 9656–9664. https://doi.org/10.1523/JNEUROSCI.1325-14.2014
- Kirchgessner, M. A., Franklin, A. D., & Callaway, E. M. (2020). Context-dependent and dynamic functional influence of corticothalamic pathways to first- and higher-order visual thalamus. *PNAS*, 117(23), 13066–13077. https://doi.org/10.1073/pnas.2002080117
- Lam, Y.-W., & Sherman, S. M. (2010). Functional organization of the somatosensory cortical layer 6 feedback to the thalamus. *Cereb. Cortex*, 20(1), 13–24. https://doi.org/10.1093/cercor/bhp077
- Larkum, M. (2013). A cellular mechanism for cortical associations: an organizing principle for the cerebral cortex. *Trends Neurosci.*, 36(3), 141–151. https://doi.org/10.1016/j.tins.2012.11.006
- Larkum, M. E., Zhu, J. J., & Sakmann, B. (1999). A new cellular mechanism for coupling inputs arriving at different cortical layers. *Nature*, 398(6725), 338–341. https://doi.org/10.1038/18686
- Lur, G., Vinck, M. A., Tang, L., Cardin, J. A., & Higley, M. J. (2016). Projection-specific visual feature encoding by layer 5 cortical subnetworks. *Cell Rep.*, 14(11), 2538–2545. https://doi.org/10.1016/j.celrep.2016.02.050
- Mason, A., & Larkman, A. (1990). Correlations between morphology and electrophysiology of pyramidal neurons in slices of rat visual cortex. II. Electrophysiology. *J. Neurosci.*, 10(5), 1415–1428. https://doi.org/10.1523/JNEUROSCI.10-05-01415.1990
- Olsen, S. R., Bortone, D. S., Adesnik, H., & Scanziani, M. (2012). Gain control by layer six in cortical circuits of vision. *Nature*, 483(7387), 47–52. https://doi.org/10.1038/nature10835
- Pospischil, M., Toledo-Rodriguez, M., Monier, C., et al. (2008). Minimal Hodgkin–Huxley type models for different classes of cortical and thalamic neurons. *Biol. Cybern.*, 99(4–5), 427–441. https://doi.org/10.1007/s00422-008-0263-8
- Prescott, S. A., De Koninck, Y., & Sejnowski, T. J. (2008). Biophysical basis for three distinct dynamical mechanisms of action potential initiation. *PLoS Comput. Biol.*, 4(10), e1000198. https://doi.org/10.1371/journal.pcbi.1000198
- Sheets, P. L., Suter, B. A., Kiritani, T., Chan, C. S., Surmeier, D. J., & Shepherd, G. M. G. (2011). Corticospinal-specific HCN expression in mouse motor cortex. *J. Neurophysiol.*, 106(5), 2216–2231. https://doi.org/10.1152/jn.00232.2011
- Shepherd, G. M. G. (2013). Corticostriatal connectivity and its role in disease. *Nat. Rev. Neurosci.*, 14(4), 278–291. https://doi.org/10.1038/nrn3469
- Sherman, S. M., & Guillery, R. W. (1998). On the actions that one nerve cell can have on another: distinguishing "drivers" from "modulators". *PNAS*, 95(12), 7121–7126. https://doi.org/10.1073/pnas.95.12.7121
- Sillito, A. M., Cudeiro, J., & Jones, H. E. (2006). Always returning: feedback and sensory processing in visual cortex and thalamus. *Trends Neurosci.*, 29(6), 307–316. https://doi.org/10.1016/j.tins.2006.05.001
- Tasic, B., Menon, V., Nguyen, T. N., et al. (2016). Adult mouse cortical cell taxonomy revealed by single cell transcriptomics. *Nat. Neurosci.*, 19(2), 335–346. https://doi.org/10.1038/nn.4216
- Tasic, B., Yao, Z., Graybuck, L. T., et al. (2018). Shared and distinct transcriptomic cell types across neocortical areas. *Nature*, 563(7729), 72–78. https://doi.org/10.1038/s41586-018-0654-5
- Teeter, C., Iyer, R., Menon, V., et al. (2018). Generalized leaky integrate-and-fire models classify multiple neuron types. *Nat. Commun.*, 9, 709. https://doi.org/10.1038/s41467-017-02717-4
- Thomson, A. M. (2010). Neocortical layer 6, a review. *Front. Neuroanat.*, 4, 13. https://doi.org/10.3389/fnana.2010.00013
- Vélez-Fort, M., Rousseau, C. V., Niedworok, C. J., et al. (2014). The stimulus selectivity and connectivity of layer six principal cells reveals cortical microcircuits underlying visual processing. *Neuron*, 83(6), 1431–1443. https://doi.org/10.1016/j.neuron.2014.08.001

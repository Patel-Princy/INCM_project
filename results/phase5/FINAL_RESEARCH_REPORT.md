# How Much Biological Detail Does a Neuron Model Need?
## Evaluating Conductance-Based Multi-Compartment versus Dimensional FitzHugh–Nagumo Reductions Across Four Mouse Visual Cortex Populations

**Course:** Introduction to Neural and Cognitive Modelling (INCM)  
**Academic Milestone:** Phase 5F Integrated Final Research Report (Phase 5C base + Layer 5 / Layer 6a biological context)  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Date:** November 2026  
**Authors:** INCM Project Research Team  

---

## Abstract

A central question in computational neuroscience is how much biological detail a neuron model requires to reproduce electrophysiological behaviour, and which computational features are preserved or lost when high-dimensional conductance-based models are reduced to low-dimensional phenomenological models. We investigated this question by conducting a systematic, three-way empirical comparison across four layer-defined spiny excitatory neuronal representatives from mouse primary visual cortex (VISp layers 4, 2/3, 5, and 6a) from the Allen Cell Types Database. We compared somatic intracellular current-clamp recordings against: (1) published, frozen perisomatic multi-compartment biophysical models simulated in NEURON containing passive leak and up to seven active conductances ($\mathrm{Na}_v$, $K_v$, $K_v3$, $K_{\mathrm{slow}}$, $I_A$, $I_h$, and $\mathrm{Ca}$); and (2) two-variable dimensional FitzHugh–Nagumo (FHN) models parameterized by eight biophysical quantities ($C_m, g_L, V_{\mathrm{rest}}, V_{\mathrm{th}}, V_{\mathrm{peak}}, k_v, \tau_w, a_w$) calibrated on a single current sweep per population. 

Models were evaluated out-of-sample on 109 previously held-out experimental sweeps (97 unique current levels). Across the held-out dataset, biological recordings exhibited action potentials in 40 sweeps, the detailed models fired in 24 sweeps, and the FHN models fired in 44 sweeps (37 True Positives, 7 False Positives, 3 False Negatives, 62 True Negatives; sensitivity 92.5%, specificity 89.9%). FHN matched the time course of passive subthreshold charging (squared correlation $r^2 \ge 0.996$ on hyperpolarizing sweeps) but, because its input resistance was calibrated to a 10 ms test-pulse (apparent) value, under-predicted the steady-state subthreshold amplitude by approximately threefold; it accurately detected near-threshold excitability transitions through an analytically verified subcritical Andronov–Hopf bifurcation with numerically confirmed open bistability intervals across all four populations: A (214.16, 234.34) pA, B (146.72, 161.28) pA, C (360.03, 385.33) pA, and D (215.92, 236.27) pA. 

However, model reduction to two planar variables resulted in four distinct limitations: (1) an inability to sustain multi-second spike-frequency adaptation (observed across all 23 qualifying biological multi-cycle sweeps, with median inter-spike interval expansions of $1.97\times\text{--}3.45\times$), as autonomous FHN limit cycles contract to stationary periodic firing within $\le 2$ cycles; (2) substantial step-waveform error (step RMSE $12.36\text{--}23.73\text{ mV}$ vs. $4.15\text{--}8.30\text{ mV}$ in detailed models) driven by broad cubic relaxation oscillations compared to fast biological spikes; (3) an empirical trade-off between delayed onset latency and sustained repetitive firing across 961 tested parameter combinations in Layer 6a, where parameter sets achieving biological repetitive rates ($\ge 12$ spikes) collapsed latency to $\le 17.40\text{ ms}$; and (4) absence of any hyperpolarization-activated ($I_h$-like) inward mechanism in the FHN recovery equation, whereas the biological cells showed modest sag ($0.63\text{--}1.86\text{ mV}$ at $-110\text{ pA}$). Conversely, detailed models exhibited vulnerability to parameter-tuning artifacts: an uncalibrated $+13.6\text{ mV}$ resting offset in Layer 4 accounted for 92.3% of its overall mean squared error, and calibration on suprathreshold sweeps correlated with a $+60\text{ pA}$ rheobase overestimation in Layers 4 and 5. 

Placed in the canonical laminar circuit of visual cortex, the Layer 5 specimen (Rbp4-Cre_KL100, a driver line labelling both intratelencephalic and pyramidal-tract neurons) is a regular-spiking, strongly adapting cell (last/first inter-spike-interval ratio up to $11.27\times$, no burst doublets), and the Layer 6a specimen (Ntsr1-Cre_GN220, a line that is corticothalamic-selective at the population level) shows a first-spike latency graded with current ($113.82\text{ ms}$ at $+210\text{ pA}$ to $27.37\text{ ms}$ at $+350\text{ pA}$) and the largest sag of the four cells. Because each layer is represented by one specimen and no axonal data exist, no projection class or ion-channel mechanism is assigned to any cell; literature-based interpretations are labelled as hypotheses.

We conclude that the tested two-variable dimensional FHN formulation is sufficient for the time course (but not the steady-state amplitude) of passive subthreshold responses and for macroscopic threshold gating, with higher sensitivity but lower specificity than the detailed models, but cannot reproduce spike-train timing, multi-second rate adaptation, or waveform kinetics under the evaluated parameterizations, providing strong scientific motivation for exploring modelling extensions such as secondary recovery variables or calcium-dependent adaptation processes.

---

## 1. Introduction

Mathematical models of single neurons span a broad spectrum of abstraction, from highly detailed multi-compartment models that incorporate complex dendritic morphologies and tens of spatially distributed voltage-gated ion channels, to low-dimensional phenomenological models that capture the geometry of excitability with two coupled ordinary differential equations (ODEs). Choosing the appropriate level of abstraction is a foundational problem in computational neuroscience. Highly detailed models offer biophysical interpretability and allow direct pharmacological manipulation of specific conductances, but they require high computational overhead and suffer from parameter indeterminacy and calibration complexity. Conversely, low-dimensional models, such as the FitzHugh–Nagumo (FHN) model or the Integrate-and-Fire family, provide analytical tractability, geometric phase-plane intuition, and computational scalability suitable for large-scale network simulations, but necessarily compress multiple biophysical mechanisms into a few phenomenological variables.

The central scientific challenge is determining what neurocomputational capabilities are preserved and what behaviours are irrecoverably lost when a biological neuron is abstracted into a low-dimensional model. While theoretical reductions—such as asymptotic reductions of the Hodgkin–Huxley equations to planar systems via timescale separation and fast-slow analysis—are mathematically well-established, quantitative out-of-sample evaluations of such models against real intracellular mammalian recordings across diverse cortical layers remain scarce. Furthermore, comparative studies frequently compare models on different datasets or evaluate models on the same data used for calibration, conflating parameter-fitting flexibility with predictive validity.

In this study, conducted as part of the Introduction to Neural and Cognitive Modelling (INCM) research program, we present an empirical evaluation of model reduction. We systematically compare three tiers of evidence: (1) intracellular somatic recordings from four layer-defined spiny excitatory neuronal representatives from the primary visual cortex (VISp) of adult mice; (2) frozen, published perisomatic multi-compartment biophysical models developed by the Allen Institute for Brain Science; and (3) dimensional two-variable FitzHugh–Nagumo models calibrated on a single stimulus sweep per population. By isolating 109 held-out experimental sweeps encompassing diverse stimulus protocols, amplitudes, and durations, we provide an objective, cross-population benchmark of the limits and capabilities of two-variable neuron models. Finally, we place the four populations in the canonical laminar circuit of visual cortex (§3.4) and interpret the Layer 5 and Layer 6a results against the published biology of these layers (§12.4–§12.5), distinguishing measured values, model predictions, literature support and hypotheses.

---

## 2. Research Question and Specific Objectives

### 2.1 The Central Research Question
The core scientific question guiding this research is:

> **"How much biological detail does a neuron model need to reproduce a real neuron's electrophysiological behaviour, and which behaviours are preserved or lost when a detailed conductance-based model is reduced to a FitzHugh–Nagumo model?"**

### 2.2 Specific Research Objectives
To address this question empirically and mathematically, we pursued four specific objectives:
1. **Pipeline and Data Readiness:** Validate and curate somatic current-clamp electrophysiology recordings from the Allen Cell Types Database across four layer-defined VISp spiny excitatory populations (Layer 4, Layer 2/3, Layer 5, and Layer 6a), ensuring rigorous Neurodata Without Borders (NWB) format compliance and physical unit consistency.
2. **Biophysical Baseline Execution:** Execute and benchmark the frozen, published Allen perisomatic multi-compartment models in the NEURON simulation environment on identical stimulus sweeps, establishing the detailed conductance-based baseline.
3. **Dimensional FHN Calibration:** Formulate a physically dimensional two-variable FitzHugh–Nagumo model parameterized by measurable biophysical quantities ($C_m, g_L, V_{\mathrm{rest}}, V_{\mathrm{th}}, V_{\mathrm{peak}}, k_v, \tau_w, a_w$), and calibrate it on a single representative current-clamp sweep per population using a dual-objective optimization algorithm.
4. **Held-Out Evaluation and Dynamical Audit:** Evaluate both model tiers out-of-sample across 109 held-out sweeps, perform independent mathematical bifurcation analysis (computing first Lyapunov coefficients and limit-cycle fold boundaries), and quantify behaviours across a five-tier taxonomy of model reduction fidelity.

---

## 3. Biological and Mathematical Background

### 3.1 Electrophysiological Properties of Cortical Pyramidal Neurons
Neocortical spiny excitatory neurons exhibit complex, non-linear membrane dynamics in response to somatic current injection:
- **Passive Subthreshold Charging:** In the hyperpolarizing and weak depolarizing regimes, current flows primarily through passive potassium and chloride leak channels, yielding an exponential charging curve governed by the membrane time constant $\tau_m = R_{\mathrm{in}} C_m$.
- **Inward Rectification (Sag):** Strong hyperpolarization activates hyperpolarization-activated cyclic nucleotide-gated (HCN) non-specific cation channels, generating an inward current ($I_h$) that depolarizes the membrane toward rest during prolonged pulses, producing a characteristic "sag" ($\Delta V_{\mathrm{sag}}$). In deep-layer pyramidal neurons, $I_h$ expression and sag differ between projection classes (Dembrow et al., 2010; Sheets et al., 2011).
- **Threshold Excitability:** Depolarization beyond a threshold voltage triggers rapid activation of voltage-gated sodium channels ($\mathrm{Na}_v$), generating action potentials followed by delayed-rectifier potassium channel ($K_v$) activation that repolarizes the membrane.
- **Spike-Frequency Adaptation (SFA):** During sustained depolarizing steps, cortical pyramidal cells typically exhibit progressive lengthening of successive inter-spike intervals (ISIs), mediated by slow calcium-activated potassium currents ($I_{\mathrm{AHP}}$, $I_{\mathrm{SK}}$) and non-inactivating muscarinic-sensitive potassium currents ($I_M$). Regular-spiking (adapting) and intrinsically bursting firing are classical cortical firing classes (Connors & Gutnick, 1990), and sustained adaptation is generically described by an additional slow adaptation variable (Benda & Herz, 2003).
- **Delayed Firing:** Some cortical neurons fire their first spike only after a long delay when stimulated just above threshold. Such delays are often attributed to slowly inactivating A-type or D-type potassium currents, but the Phase 5F literature review identified no verified V1-specific source attributing delayed firing to Layer 6a corticothalamic neurons. For the Layer 6a specimen studied here, the measured latency is graded with current ($113.82\text{ ms}$ at $+210\text{ pA}$ to $27.37\text{ ms}$ at $+350\text{ pA}$), and its mechanism is treated as a hypothesis.

### 3.2 The Hodgkin–Huxley and Perisomatic Conductance Framework
The biophysical conductance-based framework, pioneered by Hodgkin and Huxley (1952), describes membrane potential dynamics by summing individual ionic currents across the lipid bilayer:

$$C_m \frac{\mathrm{d}V}{\mathrm{d}t} = -\sum_i \bar{g}_i m_i^p h_i^q (V - E_i) - g_L (V - E_L) + I_{\mathrm{inj}}(t)$$

where $\bar{g}_i$ represents maximal channel conductance, $E_i$ is the Nernst equilibrium potential for ion species $i$, and $m_i, h_i$ are activation and inactivation gating variables governed by voltage-dependent first-order kinetics:

$$\frac{\mathrm{d}m_i}{\mathrm{d}t} = \frac{m_{\infty, i}(V) - m_i}{\tau_{m, i}(V)}$$

In multi-compartment perisomatic models (Gouwens et al., 2018), the cable equation is discretized across reconstructed dendritic and axonal geometries, with active conductances placed at the soma and axon initial segment. This framework requires integrating dozens of coupled non-linear ODEs alongside spatial cable equations.

### 3.3 The FitzHugh–Nagumo Reduction
FitzHugh (1961) and Nagumo et al. (1962) demonstrated that the four-variable Hodgkin–Huxley model can be reduced to a planar dynamical system by exploiting timescale separation. Because sodium activation ($m$) operates on a sub-millisecond timescale ($\tau_m < 0.1\text{ ms}$), $m$ can be replaced by its steady-state function $m_\infty(V)$. Furthermore, sodium inactivation ($h$) and potassium activation ($n$) evolve on similar, slower timescales and exhibit complementary voltage dependencies ($h \approx 1 - n$). Grouping these into a single effective recovery variable $w$ yields a two-variable planar vector field:

$$\begin{aligned}
\frac{\mathrm{d}V}{\mathrm{d}t} &= F(V) - w + I_{\mathrm{inj}} \\
\frac{\mathrm{d}w}{\mathrm{d}t} &= \epsilon (G(V) - w)
\end{aligned}$$

where $F(V)$ is a non-monotonic cubic nullcline capturing regenerative upstroke and downstroke dynamics, and $G(V)$ is a monotonic linear recovery nullcline.

### 3.4 Laminar Circuit Context of the Four Populations
A simplified "canonical" account of neocortical processing routes feedforward thalamic input mainly to Layer 4, from Layer 4 to Layers 2/3, from Layers 2/3 to Layer 5, and from the deep layers to subcortical targets, with Layer 6 corticothalamic (CT) neurons returning feedback to the thalamus (Douglas & Martin, 2004; Thomson, 2010; Harris & Mrsic-Flogel, 2013). Cortical excitatory neurons fall into a few main projection classes—intratelencephalic (IT), pyramidal-tract/extratelencephalic (PT/ET) and CT—whose properties are largely conserved across areas (Harris & Shepherd, 2015; Baker et al., 2018). The canonical scheme is a simplification: thalamic axons also reach the deep layers, which receive substantial input from outside Layer 2/3 (Harris & Mrsic-Flogel, 2013; Harris & Shepherd, 2015). Within this scheme, the four populations occupy the following positions:
- **Population A (VISp L4, Rorb-IRES2-Cre):** principal thalamorecipient layer; feedforward relay to Layer 2/3. *(Detailed literature pending from the Layer 2/3–Layer 4 contribution.)*
- **Population B (VISp L2/3, Nr5a1-Cre):** receives Layer 4 input; corticocortical output; projects to Layer 5. *(Detailed literature pending from the Layer 2/3–Layer 4 contribution. Nr5a1-Cre is usually described as Layer 4-associated, so the Layer 2/3 assignment rests on the Allen layer annotation.)*
- **Population C (VISp L5, Rbp4-Cre_KL100):** principal cortical output layer, containing IT neurons projecting within the telencephalon and PT/ET neurons projecting additionally to thalamus, midbrain, pons and spinal cord (Shepherd, 2013; Harris & Shepherd, 2015; Baker et al., 2018). In mouse V1, Layer 5 neurons with different long-range targets differ in morphology, physiology and visual responses (Kim et al., 2015; Lur et al., 2016), and transcriptomic taxonomies separate L5 IT, L5 PT and L5 NP subclasses (Tasic et al., 2016, 2018).
- **Population D (VISp L6a, Ntsr1-Cre_GN220):** origin of corticothalamic feedback to the dorsal lateral geniculate nucleus (dLGN) and thalamic reticular nucleus (TRN) (Thomson, 2010; Briggs & Usrey, 2008), and of intracortical gain control over the upper layers (Olsen et al., 2012; Bortone et al., 2014). Layer 6a contains both CT and intracortical (corticocortical) principal cells (Vélez-Fort et al., 2014), and is distinct from Layer 6b, which is generally treated as the adult derivative of the subplate (Hoerder-Suabedissen & Molnár, 2015).

---

## 4. Dataset and Specimen Selection

### 4.1 The Allen Cell Types Database
Electrophysiological data were curated from the publicly available Allen Cell Types Database (Allen Institute for Brain Science, n.d.). Recordings were obtained via whole-cell patch-clamp electrophysiology from visually identified neurons in acute brain slices of adult mouse primary visual cortex (VISp), recorded at a sampling rate of $200\text{ kHz}$ ($5\,\mu\text{s}$ sampling interval) at physiological temperature ($34^\circ\text{C}$).

### 4.2 Four Layer-Defined VISp Populations
Rather than pooling heterogeneous cells across cortical layers, we selected four representative spiny excitatory neurons, each corresponding to an anatomically defined laminar group in VISp:

| Population | Cortical Layer | Specimen ID | Transgenic Cre Line | Dendritic Morphology | Apparent Input Resistance ($R_{\mathrm{in}}$, test pulse) | Whole-Cell Biological $V_{\mathrm{rest}}$ | Calibration-Sweep Baseline $V_{\mathrm{baseline}}$ | Primary Calibration Sweep |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **Layer 4** | `484564503` | Rorb-IRES2-Cre | Spiny excitatory (morphological subtype unresolved) | $44.3\text{ M}\Omega$ | $-73.70\text{ mV}$ | $-73.73\text{ mV}$ | Sweep 49 (+370 pA, COARSE) |
| **B** | **Layer 2/3** | `318808427` | Nr5a1-Cre | Spiny (Pyramidal) | $80.3\text{ M}\Omega$ | $-78.96\text{ mV}$ | $-75.90\text{ mV}$ | Sweep 40 (+190 pA, COARSE) |
| **C** | **Layer 5** | `471129934` | Rbp4-Cre_KL100 | Spiny (Pyramidal) | $31.3\text{ M}\Omega$ | $-68.62\text{ mV}$ | $-69.34\text{ mV}$ | Sweep 51 (+410 pA, COARSE) |
| **D** | **Layer 6a** | `471786879` | Ntsr1-Cre_GN220 | Spiny (Pyramidal) | $52.6\text{ M}\Omega$ | $-75.92\text{ mV}$ | $-75.71\text{ mV}$ | Sweep 42 (+250 pA, COARSE) |

*Electrophysiological baseline and provenance note:* (i) Table 1 dual-reports both the whole-cell session biological resting potential ($V_{\mathrm{rest}}$) from the Allen Cell Types Database ephys feature pipeline (`data/metadata/cell_inventory.csv`) and the local pre-stimulus baseline of the designated calibration sweep ($V_{\mathrm{baseline}}$; `results/phase4b/fhn_calibration_metrics.csv`). The single-sweep pre-stimulus baseline (exact values: A $-73.7340$, B $-75.9007$, C $-69.3360$, D $-75.7102\text{ mV}$) serves as the direct mathematical anchor for the dimensional FHN nullcline fixed points in Table 3 ($V_{\mathrm{rest}}$ parameter), whereas the session-level $V_{\mathrm{rest}}$ represents the cell-wide biological feature. (ii) $R_{\mathrm{in}}$ is the *apparent* input resistance from a $10\text{ ms}$, $50\text{ pA}$ test pulse, which samples the charging transient because $\tau_m \approx 14\text{--}21\text{ ms}$. The steady-state input resistance on $1000\text{ ms}$ hyperpolarizing steps is $2.4\text{--}3.0\times$ larger (A $134.4$, B $217.5$, C $90.6$, D $125.5\text{ M}\Omega$; median across hyperpolarizing steps) and agrees with the Allen-computed values (e.g., C $94.38$, D $115.47\text{ M}\Omega$). (iii) For Population A (specimen `484564503`), the Allen 3D morphological reconstruction is truncated (`dendrite-only`, lacking an apical trunk reaching Layer 1); because Layer 4 spiny excitatory neurons in rodent V1 comprise both star-pyramidal and spiny stellate subtypes, the specific morphological subtype is classified as unresolved, whereas Populations B, C, and D exhibit intact apical trunks characteristic of pyramidal morphology.

```
Layer 1   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ (Acellular)
Layer 2/3 [ Population B: Specimen 318808427 ]  Nr5a1-Cre (High Rin = 80 MOhm)
Layer 4   [ Population A: Specimen 484564503 ]  Rorb-IRES2-Cre (Low Rin = 44 MOhm)
Layer 5   [ Population C: Specimen 471129934 ]  Rbp4-Cre (High Rheobase, 11x SFA)
Layer 6a  [ Population D: Specimen 471786879 ]  Ntsr1-Cre (Delayed onset, 58 ms)
White M.  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

### 4.3 Crucial Scope Clarification: Layer-Defined Groups vs. Projection Classes
A vital methodological boundary must be emphasized: **these four groups are defined strictly by anatomical cortical layer and spiny morphology, not by confirmed axonal projection classes.** 
In cortical physiology, pyramidal neurons in Layers 5 and 6 exhibit distinct functional phenotypes depending on projection targets (e.g., Intratelencephalic [IT], Pyramidal Tract [PT], Extratelencephalic [ET], or Corticothalamic [CT]) (Hattox & Nelson, 2007; Dembrow et al., 2010; Harris & Shepherd, 2015; Baker et al., 2018). The Allen Cell Types metadata does not contain retrograde tracer or axonal projection tracking for these specimens, and the reconstructions contain no long-range axonal projection data. The deep-layer driver lines, both GENSAT BAC-Cre lines (Gong et al., 2007; Gerfen et al., 2013), do not resolve projection class for a single cell either: Rbp4-Cre_KL100 labels both IT and PT Layer 5 neurons (Harris et al., 2019), and Ntsr1-Cre_GN220 is CT-selective only at the population level (Bortone et al., 2014). No IT, PT/ET or CT label is therefore assigned to any specimen. Therefore, our findings characterize layer-specific representative specimens rather than broad, homogenous projection classes. Furthermore, because each population is represented by a single biological specimen ($n=1$), our results reflect detailed case studies of layer-specific electrophysiology rather than statistical population distributions across all neurons in a cortical layer.

### 4.4 Stimulation Protocols and Data Isolation
Recordings evaluated in this project belong to the **Long Square** current-clamp protocol family:
- **Step Duration:** $1000\text{ ms}$ constant-amplitude current step.
- **Total Sweep Duration:** Variable, typically $1140\text{--}8000\text{ ms}$, including pre-stimulus baseline ($1020\text{ ms}$) and post-stimulus recovery.
- **Protocol Sub-types:**
  - `COARSE` (`Long Square`): Coarse current steps with amplitude increments of $\Delta I = 20\text{ pA}$, spanning deeply hyperpolarizing ($-110\text{ pA}$) to strongly suprathreshold ($+430\text{ pA}$) regimes.
  - `FINEST` (`Long Square - Subthreshold / Fine`): Fine current steps with amplitude increments of $\Delta I \le 10\text{ pA}$ focused tightly around rheobase.
- **Held-Out Isolation:** For each population, exactly **one** suprathreshold COARSE sweep was designated as the primary calibration sweep. All remaining sweeps—amounting to **109 sweeps across the four specimens** (31 in Pop A, 18 in Pop B, 34 in Pop C, and 26 in Pop D)—were placed in strict quarantine and evaluated only after models were frozen bit-for-bit.

---

## 5. Detailed Allen Biophysical Models

### 5.1 Architecture and Conductance Manifest
The detailed models evaluated in this study are the authoritative, frozen perisomatic active models generated by the Allen Institute (Gouwens et al., 2018). These models were simulated in the NEURON simulation environment (version 8.2.7) driven by the AllenSDK (version 2.16.2).

Each detailed model consists of a reconstructed perisomatic morphology (soma and truncated dendritic/axonal tree) containing:
1. **Passive Properties:** Specific membrane capacitance ($c_m \approx 1\,\mu\text{F/cm}^2$), axial resistivity ($R_a \approx 100\,\Omega\cdot\text{cm}$), and passive leak conductance ($g_L, E_L$).
2. **Active Conductances (Perisomatic):**
   - Fast transient sodium conductance ($\mathrm{Na}_v$)
   - Delayed rectifier potassium conductance ($K_v$)
   - Fast potassium conductance ($K_v3\_1$)
   - Slow non-inactivating potassium conductance ($K_{\mathrm{slow}}$)
   - Transient A-type potassium conductance ($I_A$)
   - Hyperpolarization-activated cation conductance ($I_h$)
   - High-voltage-activated calcium conductance ($\mathrm{Ca}$) with intracellular calcium dynamics ($[\mathrm{Ca}^{2+}]_i$ decay).

### 5.2 Morphological Reconstructions and Provenance
All four representative perisomatic models utilize 3D reconstructed neuronal morphologies corresponding to each specimen's own recorded histological donor experiment, as confirmed by inspecting the Allen Institute cell inventory (`data/metadata/cell_inventory.csv`), model inventory (`data/metadata/model_inventory.csv`), and cached SWC file headers:

| Population | Specimen ID | Model ID | Specimen Reconstruction ID (`cell_inventory.csv`) | Model Reconstruction ID (`model_inventory.csv`) | SWC File | SWC Header Donor Experiment | Morphological Donor Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A (L4)** | `484564503` | `485591776` | `491459182` | `491459182` | `484564503.swc` | `Rorb-IRES2-Cre-D_Ai14-201965.05.01.01` | **Original Specimen Donor** |
| **B (L2/3)** | `318808427` | `473863035` | `491119754` | `491119754` | `318808427.swc` | `Nr5a1-Cre_Ai14_IVSCC_-169250.03.02.01` | **Original Specimen Donor** |
| **C (L5)** | `471129934` | `480624414` | `495335491` | `495335491` | `471129934.swc` | `Rbp4-Cre_KL100_Ai14_IVSCC_-180747.06.01.01` | **Original Specimen Donor** |
| **D (L6a)** | `471786879` | `480632594` | `491392868` | `491392868` | `471786879.swc` | `Ntsr1-Cre_Ai14_GSL_-181184.05.02.01` | **Original Specimen Donor** |

*(Provenance Note: In exploratory screening during Phase 2A and Phase 2G, an alternative candidate L2/3 specimen, `382982932` / model `473862496`, lacked an available morphology file in the Allen API [reconstruction ID `491771090`] and required downloading a published substitute reconstruction [`674389901`]. By contrast, the four frozen representative models selected for Phase 3 through 5 possess fully matched, specimen-derived reconstructed anatomies).*

---

## 6. Dimensional FitzHugh–Nagumo Model Formulation

### 6.1 Governing Differential Equations
Standard textbook presentations of the FHN model utilize dimensionless variables ($v, w$). To enable direct, sample-by-sample physical comparison against intracellular voltage recordings (in millivolts) and current injections (in picoamperes), we formulated a fully **dimensional, 8-parameter FitzHugh–Nagumo model**:

$$\begin{aligned}
C_m \frac{\mathrm{d}V}{\mathrm{d}t} &= -g_L (V - V_{\mathrm{rest}}) + k_v (V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V)(V - V_{\mathrm{rest}}) - w + I_{\mathrm{inj}}(t) \\
\tau_w \frac{\mathrm{d}w}{\mathrm{d}t} &= a_w (V - V_{\mathrm{rest}}) - w
\end{aligned}$$

### 6.2 Physical Interpretation of State Variables and Parameters
The dynamical system comprises two dynamical state variables ($V, w$), one time-dependent driving input ($I_{\mathrm{inj}}(t)$), and **eight calibrated dimensional parameters**, each possessing unambiguous physical units and direct physiological relevance:

**Dynamical State Variables:**
- $V(t)$ [$\text{mV}$]: Somatic membrane potential.
- $w(t)$ [$\text{pA}$]: Net slow outward recovery current.

**Time-Dependent Input:**
- $I_{\mathrm{inj}}(t)$ [$\text{pA}$]: Somatically injected electrode current.

**Eight Calibrated Dimensional Parameters:**
1. $C_m$ [$\text{pF}$]: Total somatic membrane capacitance.
2. $g_L$ [$\text{nS}$]: Passive leak conductance near resting potential.
3. $V_{\mathrm{rest}}$ [$\text{mV}$]: Resting membrane potential (zero-current baseline equilibrium).
4. $V_{\mathrm{th}}$ [$\text{mV}$]: Apparent instantaneous action-potential activation threshold.
5. $V_{\mathrm{peak}}$ [$\text{mV}$]: Peak action-potential voltage ceiling.
6. $k_v$ [$\text{nS/mV}^2$]: Non-linear cubic voltage sensitivity scaling active sodium-like inward current.
7. $\tau_w$ [$\text{ms}$]: Recovery timescale governing slow potassium-like outward current deactivation.
8. $a_w$ [$\text{nS}$]: Steady-state feedback conductance coupling recovery current to membrane depolarization.

### 6.3 Frozen Calibrated Parameter Sets
Parameters were calibrated in Phase 4B using a dual-objective Nelder–Mead simplex search optimizing both passive charging and active spike waveforms on the single primary calibration sweep. The frozen parameter sets are listed below:

| Population | Layer | $C_m$ (pF) | $g_L$ (nS) | $V_{\mathrm{rest}}$ (mV) | $V_{\mathrm{th}}$ (mV) | $V_{\mathrm{peak}}$ (mV) | $k_v$ ($\text{nS/mV}^2$) | $\tau_w$ (ms) | $a_w$ (nS) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **L4** | $133.6293$ | $3.2394$ | $-73.734$ | $-69.4172$ | $52.092$ | $0.003983$ | $18.1072$ | $17.1751$ |
| **B** | **L2/3** | $38.2489$ | $0.8571$ | $-75.9007$ | $-67.6462$ | $64.9531$ | $0.00179$ | $6.8893$ | $9.7725$ |
| **C** | **L5** | $138.9047$ | $0.7416$ | $-69.336$ | $-48.2778$ | $53.7525$ | $0.004763$ | $18.8946$ | $18.8666$ |
| **D** | **L6a** | $206.5891$ | $0.9128$ | $-75.7102$ | $-57.4868$ | $64.9985$ | $0.002577$ | $38.8553$ | $11.7242$ |

### 6.4 Numerical Integration
Simulations of the dimensional FHN model were integrated using the classical 4th-order Runge–Kutta (RK4) algorithm with a fixed time-step of $\Delta t = 0.025\text{ ms}$ ($40\text{ kHz}$ effective numerical resolution). Numerical stability and convergence across $\Delta t \in \{0.005, 0.010, 0.025\}\text{ ms}$ were validated in Phase 4A.

---

## 7. Calibration and Evaluation Methodology

### 7.1 Quantitative Evaluation Metrics
Models were evaluated against experimental recordings using seven standardized, objective metrics:
1. **Spike Detection Accuracy:** A binary classification metric assessing whether a model fires $\ge 1$ spike during a sweep where the biological neuron fired $\ge 1$ spike. Evaluated via True Positives (TP), False Positives (FP), False Negatives (FN), True Negatives (TN), Sensitivity ($\frac{\mathrm{TP}}{\mathrm{TP}+\mathrm{FN}}$), and Specificity ($\frac{\mathrm{TN}}{\mathrm{TN}+\mathrm{FP}}$). Spikes were identified using a standardized derivative threshold ($\mathrm{d}V/\mathrm{d}t > 5\text{ V/s}$ crossing) and absolute voltage peak check ($V_{\mathrm{peak}} > -20\text{ mV}$).
2. **Absolute Spike Count Error:** $|\Delta N_{\mathrm{spk}}| = |N_{\mathrm{model}} - N_{\mathrm{rec}}|$.
3. **First-Spike Onset Latency Error:** $|\Delta t_{\mathrm{lat}}| = |t_{\mathrm{lat, model}} - t_{\mathrm{lat, rec}}|$, where latency is measured from stimulus onset ($t_{\mathrm{onset}} = 1020\text{ ms}$) to the first action-potential peak.
4. **Step Root-Mean-Square Error (Step RMSE):**
   $$\mathrm{RMSE}_{\mathrm{step}} = \sqrt{\frac{1}{N_{\mathrm{step}}} \sum_{k \in \mathrm{step}} \left( V_{\mathrm{model}}(t_k) - V_{\mathrm{rec}}(t_k) \right)^2}$$
   evaluated strictly during the $1000\text{ ms}$ current injection ($[1020, 2020]\text{ ms}$).
5. **Overall Root-Mean-Square Error (Overall RMSE):** Evaluated across the entire recording window (duration up to $8000\text{ ms}$), combining pre-stimulus, step, and post-stimulus intervals.
6. **Pearson Correlation Coefficient ($r$):**
   $$r = \frac{\sum_k (V_{\mathrm{model}}(t_k) - \bar{V}_{\mathrm{model}})(V_{\mathrm{rec}}(t_k) - \bar{V}_{\mathrm{rec}})}{\sqrt{\sum_k (V_{\mathrm{model}}(t_k) - \bar{V}_{\mathrm{model}})^2 \sum_k (V_{\mathrm{rec}}(t_k) - \bar{V}_{\mathrm{rec}})^2}}$$
7. **Coefficient of Determination ($R^2$):** $R^2 = 1 - \frac{\sum_k (V_{\mathrm{rec}}(t_k) - V_{\mathrm{model}}(t_k))^2}{\sum_k (V_{\mathrm{rec}}(t_k) - \bar{V}_{\mathrm{rec}})^2}$.

---

## 8. Results: Quantitative Three-Way Evaluation

Across all 109 held-out sweeps, the performance of the biological ground truth, the detailed Allen models, and the calibrated FHN models is summarized below.

### 8.1 Population-Level Held-Out Summary
From the audited records in `results/phase4c/population_summary.csv` and `results/phase4c1/PHASE4C1_INDEPENDENT_RESULTS_AUDIT.md`:

| Population | Layer | Sweeps Evaluated | Spiking Sweeps (Rec / Det / FHN) | Mean Rec Spikes | Mean Det Spikes | Mean FHN Spikes | Det Abs Spk Err | FHN Abs Spk Err | Det Step RMSE (mV) | FHN Step RMSE (mV) | Det Ovr RMSE (mV) | FHN Ovr RMSE (mV) | Det Mean $r$ | FHN Mean $r$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **4** | 31 | 11 / 4 / **15** | 1.77 | 3.71 | **4.00** | 3.23 | **2.74** | **8.30** | 22.10 | 12.73 | **8.24** | 0.8036 | **0.8352** |
| **B** | **2/3** | 18 | 8 / 6 / 6 | 6.83 | **7.67** | 3.78 | **1.06** | 4.28 | **7.61** | 23.73 | **4.04** | 11.97 | **0.9570** | 0.8960 |
| **C** | **5** | 34 | 11 / 4 / **12** | 0.97 | 0.94 | **1.00** | 0.62 | **0.38** | **4.15** | 12.36 | **4.73** | 4.81 | **0.9610** | 0.8775 |
| **D** | **6a** | 26 | 10 / 10 / **11** | 4.85 | **6.19** | 1.04 | **1.73** | 4.58 | **5.89** | 23.56 | **2.23** | 9.03 | **0.9699** | 0.8889 |
| **TOTAL** | — | **109** | **40 / 24 / 44** | — | — | — | — | — | — | — | — | — | — | — |

### 8.2 Spike Detection Contingency Analysis
Across all 109 held-out sweeps, the biological recordings fired in **40 sweeps** and remained silent in **69 sweeps**. The binary classification performance of both model tiers diverged markedly:

```
+-----------------------------------------------------------------------------------+
|               SPIKE DETECTION CONTINGENCY MATRICES (109 SWEEPS)                   |
+-----------------------------------------------------------------------------------+
| DETAILED BIOPHYSICAL MODELS                       REDUCED FHN MODELS             |
|                    Actual Positive Actual Negative               Actual Positive Actual Negative |
| Predicted Positive       24              0        Predicted Positive       37              7      |
| Predicted Negative       16             69        Predicted Negative        3             62      |
|                                                   |
| Sensitivity:  60.0% (16 False Negatives)          | Sensitivity:  92.5% (3 False Negatives)  |
| Specificity: 100.0% (0 False Positives)           | Specificity:  89.9% (7 False Positives)  |
| Balanced Acc: 80.0%                               | Balanced Acc: 91.2%                      |
+-----------------------------------------------------------------------------------+
```

- **Detailed Model Under-sensitivity:** The detailed models suffered from severe under-sensitivity in Populations A and C, failing to fire in 7 biological spiking sweeps in Pop A and 7 in Pop C. This was driven by a $+60\text{ pA}$ coarse rheobase overestimation.
- **FHN High Sensitivity:** FHN captured the threshold transition reliably, firing in 37 of 40 biological spiking sweeps (92.5% sensitivity). Its 7 false positives were confined to near-threshold subthreshold sweeps where small subthreshold biological depolarizations crossed FHN's threshold.

---

## 9. Four-Population Comparative Analysis

```
    POPULATION A (Layer 4)                   POPULATION B (Layer 2/3)
    [ Rorb-IRES2-Cre, Specimen 484564503 ]   [ Nr5a1-Cre, Specimen 318808427 ]
    * Rin = 44.3 MOhm; Rheobase = (270, 290] * Rin = 80.3 MOhm; Rheobase = (110, 130]
    * Det Baseline Offset: +13.6 mV          * Det Step RMSE: 7.61 mV (FHN 23.73 mV)
    * Det Rheobase Shift: +60 pA             * FHN Rate Capping: Saturates at 17 spk
    * Pop A RMSE Reversal: Det Ovr 12.73 mV  * Det captures monotonic F-I; FHN
      vs FHN Ovr 8.24 mV (Baseline Error)      collapses at strong steps (>230 pA).
    ----------------------------------------------------------------------------
    POPULATION C (Layer 5)                   POPULATION D (Layer 6a)
    [ Rbp4-Cre, Specimen 471129934 ]         [ Ntsr1-Cre, Specimen 471786879 ]
    * Rin = 31.3 MOhm; Rheobase = (270, 290] * Rin = 52.6 MOhm; Rheobase = (190, 210]
    * Massive Adaptation: 11.3x ISI expand   * Latency Delay: 57.95 ms at cal (+250 pA)
    * Det Rheobase Shift: +60 pA             * FHN Latency/Rate Trade-off: Damped
    * FHN Stationary limit cycle fails SFA.    tau_w = 38.9 ms caps firing to 1 spk.
    * Det Step RMSE: 4.15 mV (FHN 12.36 mV)  * Det overfires in FINEST (11 spk vs 1)
```

### 9.1 Population A — VISp Layer 4 (Specimen `484564503`)
- **Biological Profile:** Low input resistance ($44.3\text{ M}\Omega$), high rheobase ($(270, 290]\text{ pA}$), and pronounced late-step firing cessation at high currents (+390 to +430 pA).
- **The Detailed Model Offset:** The detailed model exhibits an uncalibrated resting baseline potential of $-61.1\text{ mV}$ compared to recorded $-73.7\text{ mV}$ ($\Delta V_{\mathrm{baseline}} = +13.25\text{ mV}$). It overestimates COARSE rheobase by $+60\text{ pA}$ ($(330, 350]\text{ pA}$), firing in only 4 of 11 biological spiking sweeps. 
- **Late-Step Spike Cessation at High Currents:** Across strong 1000 ms depolarizing steps (+390 to +430 pA, COARSE protocol, step interval 1020–2020 ms), the biological cell ceased firing roughly midway through the pulse, whereas the detailed model continued firing through the end of the step:
  - **+390 pA (Sweep 50):** Biological cell fired 9 spikes (first spike 1039.43 ms, last spike 1335.27 ms; silent for the remaining 684.73 ms); detailed model fired 27 spikes (last spike 1971.36 ms); FHN fired 9 spikes.
  - **+410 pA (Sweep 51):** Biological cell fired 13 spikes (first spike 1034.54 ms, last spike 1522.03 ms; silent for the remaining 497.97 ms); detailed model fired 39 spikes (last spike 1992.51 ms); FHN fired 9 spikes.
  - **+430 pA (Sweep 52):** Biological cell fired 12 spikes (first spike 1036.79 ms, last spike 1498.34 ms; silent for the remaining 521.66 ms); detailed model fired 48 spikes (last spike 2003.26 ms); FHN fired 8 spikes.
  *(Baseline: On the primary calibration sweep, Sweep 49 at +370 pA, recorded, detailed, and FHN models all fired exactly 9 spikes, with first-spike latencies of 20.24 ms, 24.71 ms, and 22.20 ms respectively). The detailed model severely overcounts spikes at +410 pA and +430 pA because it lacks the biological cell's premature late-step cessation mechanism.*
- **The Population A RMSE Paradox:** FHN reports a lower overall RMSE ($8.24\text{ mV}$) than the detailed model ($12.73\text{ mV}$). Mathematical decomposition reveals that **$92.3\%$ of the detailed model's overall MSE arises during the non-stimulus baseline interval** ($87.5\%$ of duration) due to the $+13.6\text{ mV}$ offset. Conversely, during the stimulus step, the detailed model's step RMSE is $8.30\text{ mV}$ compared to FHN's $22.10\text{ mV}$. FHN's overall RMSE advantage is entirely a baseline tracking artifact, not superior action-potential reproduction.

### 9.2 Population B — VISp Layer 2/3 (Specimen `318808427`)
- **Biological Profile:** High input resistance ($80.3\text{ M}\Omega$), low rheobase ($(110, 130]\text{ pA}$), and robust high-frequency repetitive firing (up to 29 spikes at +270 pA).
- **Detailed Model Behaviour:** The detailed model matches the recorded pre-stimulus baseline on the calibration sweep (calibration-sweep baseline $-75.90\text{ mV}$; detailed model $-75.93\text{ mV}$; whole-cell session biological $V_{\mathrm{rest}}$ is $-78.96\text{ mV}$) and achieves excellent performance across all metrics (Step RMSE $7.61\text{ mV}$, Overall RMSE $4.04\text{ mV}$, Pearson $r = 0.9570$, Mean absolute spike error $1.06$).
- **FHN Model Behaviour:** Accurately reproduces subthreshold charging (squared correlation $r^2 = 0.9900$ on mutually subthreshold sweeps) and tracks near-threshold firing. However, at higher currents (+210 to +270 pA), FHN firing rates saturate at 17 spikes (+210 pA vs. 22 biological spikes; 16 spikes at +230 pA vs. 22 biological spikes) and then collapse precipitously due to strong recovery feedback and cubic damping (firing only 2 spikes at +250 pA and 1 spike at +270 pA, vs. 27 and 29 biological spikes), yielding elevated step RMSE ($23.73\text{ mV}$).

### 9.3 Population C — VISp Layer 5 (Specimen `471129934`)
- **Biological Profile (measured):** Low apparent input resistance ($31.3\text{ M}\Omega$ test pulse; $90.6\text{ M}\Omega$ steady state on $1000\text{ ms}$ hyperpolarizing steps; Allen $94.38\text{ M}\Omega$), high rheobase ($(270, 290]\text{ pA}$), first-spike latency shortening from $75.03\text{ ms}$ ($+290\text{ pA}$) to $22.72\text{ ms}$ ($+430\text{ pA}$), regular spiking with no burst doublets at any tested current (minimum first ISI $27.12\text{ ms}$), small sag ($0.63\text{ mV}$ at $-110\text{ pA}$), and the most extreme spike-frequency adaptation in the dataset (last/first ISI ratio $1.89\times$ at $+350\text{ pA}$ rising to $11.27\times$ at $+430\text{ pA}$).
- **Biological Context (literature and hypothesis):** Layer 5 is the principal output layer of V1, with IT and PT/ET projection classes that differ in morphology, intrinsic physiology and visual responses (Kim et al., 2015; Lur et al., 2016; Baker et al., 2018). Thick-tufted (PT-like) Layer 5 neurons are associated with burst firing and dendritic Ca$^{2+}$ electrogenesis (Mason & Larkman, 1990; Larkum et al., 1999; Hay et al., 2011), whereas in projection-identified studies outside V1, strong accommodation and low $I_h$/sag are more often associated with IT neurons (Hattox & Nelson, 2007; Dembrow et al., 2010; Sheets et al., 2011). An IT-like identity for specimen C is therefore a **hypothesis only**: Rbp4-Cre_KL100 labels both IT and PT neurons (Harris et al., 2019), no axonal data exist, the supporting physiology comes from somatosensory, motor and prefrontal cortex, and $n = 1$. Dendritic electrogenesis cannot be evaluated here, because the perisomatic models have passive dendrites (Gouwens et al., 2018), FHN has a single compartment, and somatic step injection does not probe it.
- **Detailed Model Behaviour:** Overestimates COARSE rheobase by $+60\text{ pA}$ (firing in 4/11 spiking sweeps) and sits a median $+4.71\text{ mV}$ above the recorded baseline on held-out sweeps. However, when suprathreshold, it achieves the lowest step RMSE in the study ($4.15\text{ mV}$), an overall RMSE of $4.73\text{ mV}$ and high correlation ($r = 0.9610$).
- **FHN Model Behaviour:** Matches subthreshold integration (squared correlation $r^2 = 0.9518$ on mutually subthreshold sweeps), detects the threshold transition (TP 10, FP 2, FN 1, TN 21) with low absolute spike error ($0.38$) and an overall RMSE of $4.81\text{ mV}$, and its bistability interval $(360.03, 385.33)\text{ pA}$ lies inside the recorded transition from 3 spikes ($+350\text{ pA}$) to 6 spikes ($+390\text{ pA}$). However, FHN contracts to stationary limit cycles within $\le 2$ cycles, completely failing to reproduce the biological cell's $11\times$ adaptation.

### 9.4 Population D — VISp Layer 6a (Specimen `471786879`)
- **Biological Profile (measured):** Moderate apparent input resistance ($52.6\text{ M}\Omega$ test pulse; $125.5\text{ M}\Omega$ steady state; Allen $115.47\text{ M}\Omega$), moderate rheobase ($(190, 210]\text{ pA}$), delayed first-spike onset that is graded with current ($113.82\text{ ms}$ at $+210\text{ pA}$, $57.95\text{ ms}$ at the $+250\text{ pA}$ calibration sweep, $27.37\text{ ms}$ at $+350\text{ pA}$; single spikes with latencies of $109.81\text{--}180.02\text{ ms}$ in the FINEST $+240\text{ pA}$ sweeps), moderate adaptation (last/first ISI $1.13\times$ to $2.47\times$), the largest sag of the four specimens ($1.86\text{ mV}$ at $-110\text{ pA}$), and sustained high-frequency firing (up to 27 spikes at +350 pA). *(Phase 5F provenance correction: the Phase 5C text reported a latency "$> 1000\text{ ms}$ near threshold"; this is not supported by the frozen recorded spike times, in which the longest COARSE latency is $113.82\text{ ms}$.)*
- **Biological Context (literature and hypothesis):** Layer 6a is the origin of corticothalamic feedback, which excites dLGN relay cells directly and inhibits them via the TRN (Lam & Sherman, 2010; Crandall et al., 2015). This input is classed as modulatory rather than driving (Sherman & Guillery, 1998), and its net effect depends on stimulation frequency and brain state, from suppression to facilitation (Crandall et al., 2015; Denman & Contreras, 2015; Kirchgessner et al., 2020; Born et al., 2021). Within V1, Layer 6 also controls the gain of upper-layer responses (Olsen et al., 2012; Bortone et al., 2014; Kim et al., 2014). The Ntsr1-Cre line selectively targets CT rather than intracortical Layer 6 neurons at the population level (Bortone et al., 2014), so a CT identity for specimen D is plausible by genotype but **remains a hypothesis**. The ultrasparse in vivo firing of V1 CT cells (Vélez-Fort et al., 2014) concerns synaptically driven activity and cannot be compared with in vitro step responses. The Phase 4C.1 audit's attribution of the latency to Kv4/Kv1.4 currents carried no citation and is treated as a hypothesis; Allen's own feature extraction reports no delay flag for this cell.
- **Detailed Model Behaviour:** Accurately matches rheobase ($(190, 210]\text{ pA}$, shift $0\text{ pA}$), achieves $100\%$ sensitivity and specificity, low step RMSE ($5.89\text{ mV}$), and high correlation ($r = 0.9699$). At the $+250\text{ pA}$ calibration sweep (Sweep 42), it matches both delayed latency ($52.97\text{ ms}$) and repetitive firing (14 spikes). However, in FINEST protocol sweeps at $+240\text{ pA}$ (Sweeps 52–54), the detailed model fires 11 repetitive spikes whereas the biological cell fired only 1 spike; at $+210\text{ pA}$ it fires a single late spike (latency $958.91\text{ ms}$) where the cell fired 5 spikes (first-spike latency $113.82\text{ ms}$).
- **FHN Model Quantitative Failure:** Calibrating FHN to match the $58\text{ ms}$ latency forced the optimizer to select a large recovery timescale ($\tau_w = 38.86\text{ ms}, C_m = 206.59\text{ pF}$). This heavy recovery damping capped repetitive firing to only 4 spikes at calibration and a mean of $1.04$ spikes across held-out sweeps (vs. $4.85$ recorded), resulting in severe underfiring, high step RMSE ($23.56\text{ mV}$) and an overall RMSE of $9.03\text{ mV}$ (detailed: $2.23\text{ mV}$). Threshold detection nevertheless remained good (TP 10, FP 1, FN 0, TN 15).

---

## 10. Behaviours Preserved and Lost Under Model Reduction

To establish a clear, evidence-grounded answer to the research question, we synthesized results across a **Five-Tier Taxonomy of Model Reduction Fidelity**:

```
===================================================================================
                FIVE-TIER TAXONOMY OF MODEL REDUCTION FIDELITY
===================================================================================
Tier 1: Preserved Across Contexts       | Subthreshold response time course,
                                        | hyperpolarizing charging (r^2 >= 0.996),
                                        | test-pulse R_in (not steady-state gain),
                                        | resting V_rest.
-----------------------------------------------------------------------------------
Tier 2: Preserved Under Restrictions    | Macroscopic excitability gating (Hopf
                                        | bifurcation, 92.5% sensitivity),
                                        | mutually subthreshold charging (r^2 > 0.92),
                                        | coarse threshold onset tracking.
-----------------------------------------------------------------------------------
Tier 3: Systematically Mismatched /     | Waveform envelope & step RMSE (12-24 mV),
        Subspace-Constrained            | suprathreshold spike counts at high I,
                                        | Pop D latency-frequency decoupling.
-----------------------------------------------------------------------------------
Tier 4: Structurally Absent from Model  | Sustained multi-second adaptation (SFA),
                                        | I_h-like hyperpolarization-activated sag.
-----------------------------------------------------------------------------------
Tier 5: Unidentifiable from Dataset     | Specific ionic channel mechanisms (I_A,
                                        | I_SK/I_M, I_h), cortical projection
                                        | classes (IT, PT/ET, CT).
===================================================================================
```

### Tier 1: Behaviours Preserved Across Contexts
- **Resting Potential ($V_{\mathrm{rest}}$) and Apparent Input Resistance ($R_{\mathrm{in}}$):** FHN reproduces the recorded pre-stimulus baseline by construction and the $10\text{ ms}$ test-pulse (apparent) input resistance used as the calibration target. Linearizing the frozen model at rest gives

  $$R_{\mathrm{in}} = \frac{1}{G_0 + a_w}, \qquad G_0 = g_L + k_v (V_{\mathrm{th}} - V_{\mathrm{rest}})(V_{\mathrm{peak}} - V_{\mathrm{rest}}),$$

  which equals the apparent value for Populations A and C and lies within $2.1\%$ (B) and $1.2\%$ (D). *(Phase 5F provenance correction: Phase 5C gave $R_{\mathrm{in}} = (g_L + a_w)^{-1}$, which omits the cubic term's contribution at rest, and stated that $R_{\mathrm{in}}$ is preserved "exactly" for all four populations.)* On purely hyperpolarizing sweeps, FHN tracks the time course of biological charging with squared correlation $r^2 \ge 0.996$ across all four populations ($0.9960\text{--}0.9988$; `results/phase4c1/phase4c1_subthreshold_audit.csv`).
- **Qualification: steady-state amplitude is not preserved (Phase 5F).** The test-pulse value is not the steady-state input resistance. On $1000\text{ ms}$ hyperpolarizing steps the recorded steady-state $R_{\mathrm{in}}$ (A $134.4$, B $217.5$, C $90.6$, D $125.5\text{ M}\Omega$; median across steps) agrees with the Allen-computed values (C $94.38$, D $115.47\text{ M}\Omega$) and is $2.5\text{--}3.2\times$ larger than the FHN steady-state $R_{\mathrm{in}}$ on the same steps ($42.1$, $72.1$, $30.1$, $49.4\text{ M}\Omega$). FHN therefore under-predicts steady-state subthreshold voltage deflections by approximately threefold, and the coefficient of determination on the same hyperpolarizing sweeps is negative ($R^2 = -2.28$ to $-0.07$ in the same audit file). Tier 1 holds for response *shape* and resting level, not for subthreshold *gain*.

### Tier 2: Behaviours Preserved Under Restrictions
- **Macroscopic Excitability Gating:** Through a subcritical Hopf bifurcation, FHN reliably captures the onset of repetitive firing near threshold (92.5% sensitivity across 109 sweeps, versus 60.0% for the detailed models). This comes at the cost of lower specificity (89.9% versus 100%; 7 false positives versus 0), so it is a trade-off rather than an overall superiority.
- **Mutually Subthreshold Linearity:** High squared correlation in Populations B ($r^2 = 0.9900$) and D ($r^2 = 0.9952$), but slight degradation in Populations A ($r^2 = 0.9249$) and C ($r^2 = 0.9518$) due to small non-linear inward rectifications in biology. *(Phase 5F: these values are squared correlations, `fhn_vs_recorded_correlation_r2`; Phase 5C labelled them $r$.)*
- **F–I Firing Rate Scaling and Rate Saturation:** The ability to scale firing frequency with injected current differs markedly across models and populations:
  - **Detailed Multi-Compartment Models:** Once above rheobase, detailed models reproduce monotonic firing rate increases across moderate current ranges in Populations A (+350 to +430 pA: 1, 9, 27, 39, 48 spikes), B (+150 to +270 pA: 11, 16, 19, 23, 26, 29, 33 spikes), C (+350 to +430 pA: 2, 4, 5, 8, 21 spikes), and D (+210 to +350 pA: 1, 9, 14, 18, 21, 24, 26, 29 spikes). However, detailed models overestimate rheobase by +60 pA in Populations A and C, and severely overcount spikes at strong depolarizations (+390 to +430 pA in Pop A) because they lack late-step biological spike cessation.
  - **Biological Recordings:** Biological neurons exhibit monotonic or non-decreasing firing across moderate suprathreshold ranges, but display plateaus (e.g., Pop A firing 9 spikes at both +370 and +390 pA) and non-monotonic decreases at high currents due to late-step cessation or depolarization block (Pop A dropping to 12 spikes at +430 pA). Furthermore, within-cell non-stationarity between COARSE and FINEST protocols disrupts simple monotonic scaling (e.g., Pop A firing 3 spikes at 310 pA in COARSE vs. 1 spike at 310 pA in FINEST).
  - **FitzHugh–Nagumo Models:** FHN models do **not** capture continuous monotonic F–I rate expansion. Due to planar cubic nullcline geometry and strong recovery feedback, FHN limit cycles rapidly saturate in frequency: in Population A, FHN fires exactly 9 spikes across the entire 140 pA span from +270 to +410 pA (dropping to 8 at +430 pA); in Population B, FHN firing rate scales only from +150 to +170 pA (15 to 17 spikes) before plateauing and then collapsing to 1–2 spikes at +250 to +270 pA; and in Population D, FHN firing is heavily suppressed to 1–4 spikes.

### Tier 3: Behaviours Systematically Mismatched or Subspace-Constrained
- **Action-Potential Waveform Fidelity and Step RMSE:** Detailed models achieve low step RMSE ($4.15\text{--}8.30\text{ mV}$) by generating narrow spikes with rapid repolarization. FHN produces broad cubic relaxation waves that elevate step RMSE to $12.36\text{--}23.73\text{ mV}$. (Note: Directly validated derivative upstroke metrics remain provisional).
- **Population D Latency-Frequency Decoupling:** In Layer 6a, biological neurons sustain both delayed onset ($57.95\text{ ms}$) and repetitive firing (13 spikes) at the calibration current, and the recorded latency is graded with current ($113.82\text{ ms}$ at $+210\text{ pA}$ to $27.37\text{ ms}$ at $+350\text{ pA}$). Within the investigated $(C_m, \tau_w)$ parameter subspace ($[40, 220]\text{ pF} \times [8, 50]\text{ ms}$), FHN models matching biological latency ($t_{\mathrm{lat}} \ge 50\text{ ms}$) are strictly constrained to $\le 4$ spikes, while models achieving repetitive firing ($\ge 12$ spikes) collapse onset latency to $\le 17.40\text{ ms}$.

### Tier 4: Behaviours Structurally Absent from the Current Model Formulation
- **Sustained Multi-Second Spike-Frequency Adaptation:** Observed in 100% of the 23 qualifying biological multi-cycle sweeps (median ISI expansion $1.97\times\text{--}3.45\times$, maximum $11.3\times$). FHN exhibits only transient ISI adjustment ($-0.5\%\text{ to }+1.2\%$) over the first $1\text{--}2$ cycles ($\le 120\text{ ms}$), settling to stationary limit cycles ($\mathrm{ISI}_{\mathrm{final}}/\mathrm{ISI}_1 \approx 1.000$, $\Delta \mathrm{ISI} < 0.01\%$). Sustained multi-second adaptation was not reproduced due to the absence of a slow secondary recovery process.
- **Hyperpolarization Sag ($I_h$):** Biological recordings exhibit modest depolarizing sag at $-110\text{ pA}$ ($0.63\text{--}1.86\text{ mV}$; largest in the Layer 6a specimen). The FHN recovery equation is linear and contains no hyperpolarization-activated inward conductance, so an $I_h$-like sag mechanism is structurally absent. *(Phase 5F provenance correction: Phase 5C reported a measured FHN sag of $\Delta V_{\mathrm{sag}} = 0.00\text{ mV}$. This value is hard-coded in `scripts/audit_phase4c1_heldout.py` and was not computed from a simulation. A linearization of the frozen parameters instead predicts a fast transient undershoot of the recovery variable after step onset (approximately $1.7\text{--}4.1\text{ mV}$, peaking $9\text{--}38\text{ ms}$ after onset), which a peak-minus-steady-state metric would register as "sag" but which is not an $I_h$ mechanism. This analytical prediction has not been confirmed by simulation.)*

### Tier 5: Behaviours Unidentifiable from Current Dataset
- **Specific Channel Mechanisms:** Literature hypotheses attributing Population D latency to transient A-type potassium current ($I_A$), or adaptation to $I_{\mathrm{SK}}/I_M$, cannot be confirmed without pharmacological channel blockers. The Phase 4C.1 audit's attribution of Population D latency to "Kv4/Kv1.4 per literature" carried no citation and is treated as a hypothesis.
- **Projection Class:** Whether specimen C is an IT or PT/ET neuron, and whether specimen D is a CT or intracortical Layer 6 neuron, cannot be determined: Rbp4-Cre_KL100 labels both IT and PT neurons (Harris et al., 2019), Ntsr1-Cre_GN220 is CT-selective only at the population level (Bortone et al., 2014), and no axonal or retrograde data exist for either specimen.

---

## 11. Bifurcation, Dynamical, and Bistability Analysis

### 11.1 Local Stability, Jacobian, and Hopf Bifurcation
The fixed points $(V^*, w^*)$ of the dimensional FHN model satisfy:

$$w^* = a_w(V^* - V_{\mathrm{rest}})$$
$$-g_L(V^* - V_{\mathrm{rest}}) + k_v(V^* - V_{\mathrm{th}})(V_{\mathrm{peak}} - V^*)(V^* - V_{\mathrm{rest}}) - a_w(V^* - V_{\mathrm{rest}}) + I_{\mathrm{inj}} = 0$$

Linearizing around $(V^*, w^*)$ yields the Jacobian matrix:

$$J = \begin{pmatrix} \frac{f'(V^*)}{C_m} & -\frac{1}{C_m} \\ \frac{a_w}{\tau_w} & -\frac{1}{\tau_w} \end{pmatrix}$$

where $f'(V) = -g_L + k_v \left[ -(V - V_{\mathrm{th}})(V - V_{\mathrm{rest}}) + (V_{\mathrm{peak}} - V)(V - V_{\mathrm{rest}}) + (V - V_{\mathrm{th}})(V_{\mathrm{peak}} - V) \right]$.

The trace and determinant are:

$$\mathrm{Tr}(J) = \frac{f'(V^*)}{C_m} - \frac{1}{\tau_w}, \qquad \det(J) = -\frac{f'(V^*)}{C_m \tau_w} + \frac{a_w}{C_m \tau_w}$$

An Andronov–Hopf bifurcation occurs at current $I_{H1}$ where the trace vanishes while the determinant remains positive:

$$f'(V^*(I_{H1})) = \frac{C_m}{\tau_w}, \qquad \det(J) = \frac{a_w - C_m / \tau_w}{C_m \tau_w} > 0$$

This establishes the fundamental mathematical condition for Hopf bifurcation in our dimensional model:

$$a_w > \frac{C_m}{\tau_w}$$

For all four calibrated models, this condition is satisfied with margin ($a_w / (C_m / \tau_w)$ ranges from $1.76$ to $2.57$).

### 11.2 First Lyapunov Coefficient ($l_1$) and Subcriticality
To determine whether the Hopf bifurcation is supercritical (soft onset of firing) or subcritical (hard threshold with bistability), we performed coordinate transformation to normal form and evaluated the first Lyapunov coefficient ($l_1$) per Kuznetsov (2004) in Phase 4C.1 and 4C.3:

| Population | Lower Hopf Voltage $V_{H1}^*$ (mV) | Lower Hopf Current $I_{H1}$ (pA) | Imaginary Eigenfrequency $\omega_0$ (rad/ms) | Transversality $\left.\frac{\mathrm{d}\mathrm{Re}(\lambda)}{\mathrm{d}I}\right|_{I_{H1}}$ | First Lyapunov Coefficient $l_1$ | Bifurcation Criticality |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $-58.8510$ | $234.3396$ | $0.0636$ | $+0.000260$ | $+4.39 \times 10^{-5}$ | **SUBCRITICAL** ($l_1 > 0$) |
| **B** | $-56.0194$ | $161.2757$ | $0.1266$ | $+0.000992$ | $+8.89 \times 10^{-5}$ | **SUBCRITICAL** ($l_1 > 0$) |
| **C** | $-50.9232$ | $385.3268$ | $0.0662$ | $+0.000265$ | $+6.07 \times 10^{-5}$ | **SUBCRITICAL** ($l_1 > 0$) |
| **D** | $-56.5864$ | $236.2722$ | $0.0283$ | $+0.000198$ | $+3.29 \times 10^{-5}$ | **SUBCRITICAL** ($l_1 > 0$) |

Because $l_1 > 0$ strictly holds across all four calibrated models, **all four populations undergo subcritical Hopf bifurcations**. This mathematically proves the local existence of an unstable limit cycle for currents immediately below $I_{H1}$.

### 11.3 Limit-Cycle Folds and Verified Open Bistability Intervals
In a subcritical Hopf bifurcation, the branch of unstable periodic orbits turns around at a limit-cycle fold (saddle-node of limit cycles, $I_{\mathrm{fold}}$) and gains stability, creating a large-amplitude stable periodic orbit. 

Through independent numerical bisection and temporal step-refinement audits ($\Delta t \in \{0.005, 0.010, 0.025\}\text{ ms}$, numerical uncertainty $\pm 0.01\text{ pA}$) in Phase 4C.3 and Phase 4C.3.1, we identified the fold currents and established the verified open bistability intervals:

| Population | Lower Hopf $I_{H1}$ (pA) | Limit-Cycle Fold $I_{\mathrm{fold}}$ (pA) | Numerical Uncertainty (pA) | Verified Open Bistability Interval $(I_{\mathrm{fold}}, I_{H1})$ | Bistability Width $\Delta I$ (pA) | Stable Resting State in Interior | Stable Limit Cycle in Interior |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | $234.34$ | $214.16$ | $\pm 0.01$ | **(214.16, 234.34) pA** | $20.18$ | True | True |
| **B** | $161.28$ | $146.72$ | $\pm 0.01$ | **(146.72, 161.28) pA** | $14.55$ | True | True |
| **C** | $385.33$ | $360.03$ | $\pm 0.01$ | **(360.03, 385.33) pA** | $25.29$ | True | True |
| **D** | $236.27$ | $215.92$ | $\pm 0.01$ | **(215.92, 236.27) pA** | $20.36$ | True | True |

```
                       BISTABILITY REGIME DIAGRAM
 ----------------------------------------------------------------------
        Quiescent State         |    Bistable Coexistence    | Repetitive Firing
  (Resting Equilibrium Stable)  | (Stable Rest + Stable Cycle)| (Limit Cycle Only)
 -------------------------------+----------------------------+-----------------> Current I
                                I_fold                      I_H1
 
 * At I = I_fold: Saddle-node of limit cycles (non-hyperbolic cycle fold).
 * On open interval (I_fold, I_H1): Coexistence of resting equilibrium and spiking cycle.
 * At I = I_H1: Subcritical Hopf bifurcation (non-hyperbolic equilibrium).
```

- **Boundary Semantics:** At the exact fold current $I_{\mathrm{fold}}$, the stable and unstable cycles coalesce into a non-hyperbolic orbit with Floquet multiplier $+1$. At the exact Hopf current $I_{H1}$, the equilibrium has purely imaginary eigenvalues. Hence, true bistable coexistence of hyperbolic attractors strictly applies to the **open interval** $I_{\mathrm{fold}} < I < I_{H1}$.

### 11.4 Population D Parameter Grid Scans
To determine whether the quantitative failure of FHN in Population D could be resolved by alternative parameterizations, two extensive two-dimensional grid scans over membrane capacitance $C_m$ and recovery timescale $\tau_w$ were evaluated:
- **Scan 1 (Phase 4B.1 Baseline Scan, 625 points):** $(C_m, \tau_w) \in [40, 240]\text{ pF} \times [8, 60]\text{ ms}$. For configurations achieving $\ge 12$ spikes, the maximum latency was $18.50\text{ ms}$ ($12.20\text{ ms}$ at target 13 spikes).
- **Scan 2 (Phase 4B.2 Refined Scan, 961 points):** $(C_m, \tau_w) \in [40, 220]\text{ pF} \times [8, 50]\text{ ms}$. For configurations achieving $\ge 12$ spikes, the maximum latency was $17.40\text{ ms}$ ($16.00\text{ ms}$ at target 13 spikes). Crucially, every configuration achieving biological latency ($t_{\mathrm{lat}} \ge 50\text{ ms}$) fired at most 4 spikes ($N_{\mathrm{spk}} \le 4$).

This confirms an empirical trade-off between delayed onset latency and repetitive firing frequency across the tested two-dimensional parameter subspace.

---

## 12. Discussion

### 12.1 Direct Answer to the Research Question
Returning to our central research question:
*How much biological detail does a neuron model need to reproduce a real neuron's electrophysiological behaviour, and which behaviours are preserved or lost when a detailed conductance-based model is reduced to a FitzHugh–Nagumo model?*

Our empirical and mathematical findings demonstrate that:
1. **For Subthreshold Passive Integration and Macroscopic Excitability Gating:** A dimensional two-variable FitzHugh–Nagumo model is **sufficient for the time course of subthreshold responses and for threshold gating, but not for subthreshold gain**. By calibrating eight parameters to a single sweep, FHN reproduces the time course of passive membrane charging ($r^2 \ge 0.996$ on hyperpolarizing sweeps) and the test-pulse (apparent) input resistance, but under-predicts steady-state subthreshold deflections by approximately threefold. It reliably detects the boundary between silence and repetitive firing (92.5% sensitivity across 109 sweeps, versus 60.0% for the detailed models, which suffered from a $+60\text{ pA}$ coarse rheobase overestimation in Populations A and C). This higher sensitivity is a trade-off rather than an overall superiority: FHN's specificity is lower (89.9% versus 100%), its step RMSE is higher ($12.36\text{--}23.73\text{ mV}$ versus $4.15\text{--}8.30\text{ mV}$), and it has no sustained adaptation.
2. **For Spike-Train Timing, Rate Coding, and Waveform Kinetics:** The tested two-variable planar FHN formulation is **insufficient**. Compressing all voltage-dependent conductances and recovery processes into a single linear recovery variable ($w$) eliminates the dynamical degrees of freedom required to sustain multi-second spike-frequency adaptation, decouple onset latency from firing rate, capture rapid sodium upstroke kinetics, or reproduce hyperpolarization-activated inward sag.

### 12.2 The Hierarchy of Model Reduction
Our results clarify the boundaries across the hierarchy of computational neuron models:

$$\text{Multi-Compartment (NEURON)} \;\longrightarrow\; \text{Point Conductance (HH)} \;\longrightarrow\; \text{3D Adaptive (AdEx/Izhikevich)} \;\longrightarrow\; \text{2D Planar (FHN)}$$

The comparison between adaptive conductance models and the tested 2D planar cubic FHN formulation highlights the boundary where **multi-timescale adaptation and delayed onset decoupling are constrained**. In the tested autonomous two-variable cubic FHN formulation with linear recovery, sustaining adaptation across multi-second stimulus steps is structurally unavailable because the phase plane contains only a single slow recovery degree of freedom ($w$), causing limit cycle orbits to rapidly settle into stationary periodic firing ($\le 2$ cycles). While certain non-polynomial 2D dynamical systems with subthreshold non-linearities or dynamic reset thresholds can generate transient slowing, capturing continuous multi-second adaptation and latency-frequency decoupling across experimental current-clamp steps provides strong scientific motivation for exploring model extensions that incorporate secondary slow processes (such as a second recovery variable $w_2$ or intracellular calcium accumulation $[\mathrm{Ca}^{2+}]_i$ operating on a timescale $\tau \gg 100\text{ ms}$), rather than establishing a universal mathematical impossibility for all two-dimensional models.

### 12.3 Trade-offs Between Biophysical Realism and Computational Cost
Our evaluation highlights that neither model tier is universally superior across all electrophysiological criteria:
- **Detailed Multi-Compartment Models:** Excel at capturing action-potential waveform profiles (step RMSE $4\text{--}8\text{ mV}$) and multi-timescale adaptation, but require high computational overhead, suffer from calibration sensitivity (e.g., Pop A $+13.6\text{ mV}$ baseline offset), and can miss near-threshold excitability transitions.
- **Reduced FitzHugh–Nagumo Models:** Provide computational efficiency (simulating thousands of times faster via simple RK4 integration) and robust threshold detection via subcritical Hopf bifurcations, but sacrifice waveform fidelity and multi-timescale firing rate dynamics.

### 12.4 Biological Interpretation of the Layer 5 and Layer 6a Results
The Layer 5 and Layer 6a results are interpreted below with explicit evidence labels: **measured** (this project's recordings), **literature**, **model prediction** (detailed or FHN), and **hypothesis**.

**Layer 5 (Population C).**
- *Measured:* a regular-spiking, strongly adapting cell (last/first ISI ratio up to $11.27\times$), with no burst doublets, small sag ($0.63\text{ mV}$), high rheobase and low input resistance.
- *Literature:* Layer 5 contains IT and PT/ET neurons with different targets, intrinsic properties and visual responses (Kim et al., 2015; Lur et al., 2016; Baker et al., 2018). Classical firing classes are regular spiking and intrinsically bursting (Connors & Gutnick, 1990), and bursting is associated with thick-tufted neurons (Mason & Larkman, 1990). Outside V1, accommodation and low $I_h$ characterize IT rather than PT neurons (Hattox & Nelson, 2007; Dembrow et al., 2010; Sheets et al., 2011).
- *Hypothesis:* specimen C is IT-like. This is not a classification, because Rbp4-Cre_KL100 is a mixed IT/PT line (Harris et al., 2019), no axonal data exist, the supporting physiology is from other cortical areas, and $n = 1$.
- *Model implication:* the cell's dominant feature, strong sustained adaptation, is exactly what the two-variable FHN cannot express (stationary limit cycle within $\le 2$ cycles). Sustained adaptation generically requires an additional slow adaptation variable (Benda & Herz, 2003; Pospischil et al., 2008), and adaptation also linearizes f–I curves (Ermentrout, 1998). Reduced models of Allen cells that add after-spike currents and threshold adaptation predict spike times better (Teeter et al., 2018). Dendritic electrogenesis of thick-tufted Layer 5 neurons (Larkum et al., 1999; Hay et al., 2011) lies outside what either model tier or somatic step data can test.

**Layer 6a (Population D).**
- *Measured:* repetitive firing over a wide current range, moderate adaptation, a first-spike latency graded from $113.82$ to $27.37\text{ ms}$, and the largest sag of the four cells ($1.86\text{ mV}$).
- *Literature:* Layer 6a CT neurons provide modulatory feedback to dLGN and TRN (Sherman & Guillery, 1998; Briggs & Usrey, 2008; Thomson, 2010). Its sign depends on frequency and state (Crandall et al., 2015; Kirchgessner et al., 2020), and it sharpens dLGN receptive fields in awake mice (Born et al., 2021). Within cortex, Layer 6 controls the gain of upper layers (Olsen et al., 2012; Bortone et al., 2014). Ntsr1-Cre targets CT rather than intracortical Layer 6 neurons at the population level (Bortone et al., 2014). CT and corticocortical Layer 6 cells differ in visual tuning and connectivity (Vélez-Fort et al., 2014), and antidromically identified corticofugal Layer 6 neurons in mouse V1 slices differ in excitability and spike shape from their neighbours (Brumberg et al., 2003).
- *Hypothesis:* specimen D is a CT neuron (plausible by genotype only). The mechanism of its delayed, current-graded first spike is also a hypothesis; no verified V1-specific source links delayed firing to Layer 6 CT neurons.
- *Model implication:* the cell combines a slow onset with fast repetitive firing. The two-variable FHN cannot combine $\ge 50\text{ ms}$ latency with $\ge 12$ spikes anywhere in the 961-point grid, which indicates that at least two distinct slow processes would be required (hypothesis). The detailed model reproduces rheobase and the calibration latency, but not the near-threshold sweeps (1 late spike versus 5 at $+210\text{ pA}$; 11 spikes versus 1 at FINEST $+240\text{ pA}$).

### 12.5 Cross-Laminar Synthesis
Table 7 places the four populations side by side. Literature roles for Populations A and B are left for the Layer 2/3–Layer 4 contribution; measured and model values are taken from frozen project files.

| Population | Layer | Literature role | Measured | Detailed model | FHN model |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **A** | L4 | *Pending Layer 4 contribution* (canonical: principal thalamorecipient layer) | Biological $V_{\mathrm{rest}}$ $-73.70\text{ mV}$ (calibration baseline $-73.73\text{ mV}$); $R_{\mathrm{in}}$ $44.3\text{ M}\Omega$ test pulse ($134.4\text{ M}\Omega$ step); rheobase $(270, 290]\text{ pA}$; sag $0.80\text{ mV}$; late-step firing cessation $\ge +390\text{ pA}$ | Baseline $-61.07\text{ mV}$; $+60\text{ pA}$ rheobase shift; 4/11 spiking sweeps; step RMSE $8.30\text{ mV}$ | 15 spiking sweeps (11 recorded); step RMSE $22.10\text{ mV}$; overall RMSE $8.24\text{ mV}$; spike count saturates at 9 |
| **B** | L2/3 | *Pending Layer 2/3 contribution* (canonical: Layer 4 recipient, corticocortical output) | Biological $V_{\mathrm{rest}}$ $-78.96\text{ mV}$ (calibration baseline $-75.90\text{ mV}$); $R_{\mathrm{in}}$ $80.3\text{ M}\Omega$ test pulse ($217.5\text{ M}\Omega$ step); rheobase $(110, 130]\text{ pA}$; sag $1.13\text{ mV}$; up to 29 spikes at $+270\text{ pA}$ | 6/8 spiking sweeps; step RMSE $7.61\text{ mV}$; overall RMSE $4.04\text{ mV}$ | 6/8 spiking sweeps; rate collapses $\ge +250\text{ pA}$; step RMSE $23.73\text{ mV}$ |
| **C** | L5 | Principal output layer with IT and PT/ET classes | Biological $V_{\mathrm{rest}}$ $-68.62\text{ mV}$ (calibration baseline $-69.34\text{ mV}$); $R_{\mathrm{in}}$ $31.3\text{ M}\Omega$ test pulse ($90.6\text{ M}\Omega$ step); rheobase $(270, 290]\text{ pA}$; regular spiking, no bursts; ISI ratio up to $11.27\times$; sag $0.63\text{ mV}$ | $+4.71\text{ mV}$ median baseline offset; $+60\text{ pA}$ rheobase shift; 4/11; step RMSE $4.15\text{ mV}$; overall RMSE $4.73\text{ mV}$ | TP 10 / FP 2 / FN 1 / TN 21; overall RMSE $4.81\text{ mV}$; stationary limit cycle (no SFA) |
| **D** | L6a | CT feedback to dLGN/TRN; intracortical gain control | Biological $V_{\mathrm{rest}}$ $-75.92\text{ mV}$ (calibration baseline $-75.71\text{ mV}$); $R_{\mathrm{in}}$ $52.6\text{ M}\Omega$ test pulse ($125.5\text{ M}\Omega$ step); rheobase $(190, 210]\text{ pA}$; latency graded $113.8 \to 27.4\text{ ms}$; sag $1.86\text{ mV}$ | Rheobase matched; 10/10; overall RMSE $2.23\text{ mV}$; overfires at FINEST $+240\text{ pA}$ (11 vs. 1) | TP 10 / FP 1 / FN 0 / TN 15; overall RMSE $9.03\text{ mV}$; latency–rate trade-off ($\le 4$ spikes at $\ge 50\text{ ms}$ latency) |

Across the four populations, the pattern is consistent with the model structure rather than with layer identity alone:
- **Where the cells differ most from a two-variable oscillator** (strong sustained adaptation in Layer 5; slow onset combined with fast repetitive firing in Layer 6a), FHN fails in a way that its single recovery variable predicts.
- **Where FHN succeeds** (threshold detection, resting level, subthreshold time course), the property is set by the fitted fold/Hopf geometry and the test-pulse calibration, not by a biologically specific mechanism.
- **The detailed models' errors** (baseline offsets in A and C, rheobase shifts, near-threshold mismatch in D) are calibration-specific and do not follow laminar position.

Pooled held-out detection (109 sweeps; 40 spiking, 69 silent): detailed TP 24, FP 0, FN 16, TN 69 (sensitivity 60.0%, specificity 100%); FHN TP 37, FP 7, FN 3, TN 62 (sensitivity 92.5%, specificity 89.9%). With $n = 1$ per layer, none of these differences can be attributed to laminar identity rather than to the individual specimen.

*Integration requirements for the Layer 2/3 and Layer 4 contribution:*
- Literature roles for Populations A and B, with verified citations.
- Discussion of the Nr5a1-Cre / Layer 2/3 annotation.
- Biological context for the Population A late-step firing cessation.
- Resolution of the Population A baseline-offset figures used in this report ($+13.6$, $+13.25$ and $+12.66\text{ mV}$).
- Confirmation of the Population B $V_{\mathrm{rest}}$ correction.

These items are listed in `results/phase5/PHASE5F_L5_L6A_LITERATURE_REVIEW.md` §8.

---

## 13. Limitations and Scientific Caveats

To ensure academic rigor, fifteen explicit scientific caveats and boundaries must be documented:

1. **Representative Specimens ($n=1$ per Layer):** Results characterize four individual biological specimens and their corresponding model fits. They do not constitute a statistically representative sample of entire cortical layers.
2. **Unconfirmed Projection Classes:** Layer-defined populations cannot be equated with functional projection classes (IT, ET, PT, CT) due to the absence of retrograde tracing metadata in the Allen dataset. The Cre driver line does not settle this either: Rbp4-Cre_KL100 labels both IT and PT neurons, and Ntsr1-Cre_GN220 is CT-selective only at the population level. Literature-based identities (IT-like for C, CT for D) are hypotheses.
3. **Morphological Reconstruction Sourcing and Tissue Processing:** All four selected representative perisomatic models in Phase 3–5 utilize reconstructed 3D morphologies matching their respective recorded donor specimens (unlike exploratory candidate `382982932` in Phase 2, which required a substitute morphology due to missing Allen API files). Nevertheless, dendritic reconstructions from in vitro acute slices inherently experience tissue shrinkage, optical sectioning boundaries, and slicing truncations that introduce geometric approximations into multi-compartment passive cable calculations. Furthermore, for Population A (specimen `484564503`), the reconstruction is truncated (`dendrite-only`) without an apical dendrite reaching Layer 1, leaving the specific morphological subtype within spiny excitatory Layer 4 neurons (star-pyramidal vs. spiny stellate) empirically unresolved.
4. **Protocol-Dependent Biological Non-stationarity:** In Populations C (L5) and D (L6a), biological cells displayed protocol-dependent firing non-stationarity between COARSE and FINEST sweeps within the same recording session (e.g., Pop D firing 1 spike at +240 pA in FINEST vs. multiple spikes in COARSE).
5. **Layer 4 Late-Step Spike Cessation:** Specimen `484564503` ceased firing prematurely during strong 1000 ms depolarizing steps (+390 to +430 pA, COARSE protocol, 1020–2020 ms): at +410 pA (Sweep 51), the biological cell ceased firing at 1522.03 ms (13 recorded spikes; silent for the remaining 497.97 ms) vs. 39 detailed-model spikes (firing through 1992.51 ms); at +430 pA (Sweep 52), the biological cell ceased firing at 1498.34 ms (12 recorded spikes; silent for the remaining 521.66 ms) vs. 48 detailed-model spikes (firing through 2003.26 ms). The detailed model continued firing through the end of the pulse across all high currents. The biological mechanism responsible for this premature cessation remains unverified.
6. **Detailed-Model Rheobase Overestimation:** The $+60\text{ pA}$ rheobase mismatch in Populations A and C remains an unresolved empirical observation; while calibration sweep amplitude selection is a plausible methodological contributor, it has not been causally isolated.
7. **FHN Adaptation Scope:** The distinction between transient initial ISI adjustments ($\le 2$ cycles) and sustained multi-second adaptation must be preserved; FHN limit cycles are stationary to $< 0.01\%$.
8. **Biological Adaptation Census:** Continuous adaptation was observed across all 23 qualifying multi-cycle biological sweeps ($\ge 3$ spikes), with extreme adaptation ($\ge 5\times$) confined to 3 sweeps.
9. **Hyperpolarization Sag Provenance:** Biological sag at $-110\text{ pA}$ was measured as modest ($0.63\text{--}1.86\text{ mV}$); detailed model sag was **not quantified** in evaluation metrics. The Phase 5C value of $0.00\text{ mV}$ for FHN was hard-coded in `scripts/audit_phase4c1_heldout.py` rather than computed; FHN contains no $I_h$-like mechanism, and an analytical linearization predicts a transient recovery-variable undershoot that has not been confirmed by simulation.
10. **Provisional Action-Potential Kinetics:** Numerical upstroke velocities ($397\text{--}466\text{ V/s}$ vs. $5.7\text{--}6.2\text{ V/s}$) remain provisional supporting observations due to unstandardized filtering, sampling rates, and digital differentiation stencils.
11. **Subspace Boundedness of Population D Scans:** The latency-frequency trade-off in Population D is empirically demonstrated within the investigated 2D parameter subspace ($[40, 220]\text{ pF} \times [8, 50]\text{ ms}$), not as an unproven universal theorem across all planar systems.
12. **Numerical Uncertainty of Bistability Intervals:** Fold currents ($I_{\mathrm{fold}}$) and bistability widths are numerically estimated with an uncertainty of $\pm 0.01\text{ pA}$ based on step-refinement audits, and are not exact analytical proofs.
13. **Input-Resistance Definition:** The project's $R_{\mathrm{in}}$ (Table 1) is an apparent value from a $10\text{ ms}$ test pulse, while the steady-state input resistance on $1000\text{ ms}$ steps is $2.4\text{--}3.0\times$ larger. FHN was calibrated to the apparent value and therefore under-predicts steady-state subthreshold amplitude by approximately threefold.
14. **Cross-Area and Cross-Species Literature:** Much of the projection-identified physiology cited for Layer 5 comes from mouse somatosensory and motor cortex and rat prefrontal cortex, and some corticothalamic circuit findings come from somatosensory cortex. These are used as context only, not as evidence about the V1 specimens.
15. **Phase 5F/5F.2 Provenance Corrections:** Table 1 reports both the whole-cell session biological resting potential from the Allen Ephys feature pipeline ($V_{\mathrm{rest}}$: Pop A $-73.70$, B $-78.96$, C $-68.62$, D $-75.92\text{ mV}$) and the pre-stimulus baseline of the designated calibration sweep ($V_{\mathrm{baseline}}$: Pop A $-73.73$, B $-75.90$, C $-69.34$, D $-75.71\text{ mV}$), resolving previous conflation between session-level features and single-sweep baselines. The FHN model $V_{\mathrm{rest}}$ parameter anchors directly to the single-sweep baseline. Other Phase 5F corrections include Population D near-threshold latency (from "$> 1000\text{ ms}$" to $113.82\text{ ms}$), the FHN input-resistance formula, the FHN sag statement, the uncited "Kv4/Kv1.4" attribution, and two reference entries. No frozen data, parameters, model outputs or tests were changed; the corrections are documented in `results/phase5/PHASE5F_FINAL_RESEARCH_QA_REPORT.md` and `results/phase5/PHASE5F2_FINAL_CORRECTION_REPORT.md`.

---

## 14. Conclusion

This project evaluated the electrophysiological consequences of model reduction by comparing intracellular cortical recordings, detailed multi-compartment biophysical models, and two-variable dimensional FitzHugh–Nagumo models across four layer-defined mouse visual cortex populations.

Our findings demonstrate that a two-variable dimensional FHN model provides an effective representation of **the time course of passive subthreshold charging ($r^2 \ge 0.996$ on hyperpolarizing sweeps) and macroscopic excitability gating (92.5% spike detection sensitivity)** via a verified subcritical Hopf bifurcation. Its subthreshold gain is not preserved (steady-state amplitude under-predicted approximately threefold under the test-pulse calibration), and its higher sensitivity comes with lower specificity than the detailed models (89.9% versus 100%). However, reducing the biophysical state space to two planar variables results in the systematic loss of **sustained multi-second spike-frequency adaptation, fine action-potential waveform fidelity, hyperpolarization-activated inward sag, and latency-frequency decoupling**. 

These losses map onto the most distinctive measured properties of the deep-layer specimens: strong sustained adaptation in the Layer 5 cell and a slow, current-graded onset combined with fast repetitive firing in the Layer 6a cell. The biological roles of these layers—cortical output through IT and PT/ET neurons in Layer 5, and modulatory corticothalamic feedback and intracortical gain control from Layer 6a—provide context for why such properties matter, but with one specimen per layer and no axonal data, no projection class or channel mechanism is assigned to either cell.

For large-scale neural network simulations prioritizing computational efficiency and macroscopic state transitions, the dimensional FHN model offers a calibrated alternative to abstract dimensionless formulations. However, for studies where spike-timing codes, sustained rate adaptation, or fine waveform kinetics are central, researchers should consider modelling extensions beyond the standard planar cubic formulation, such as incorporating secondary slow recovery variables, calcium-dependent adaptation processes, or fast-activating active conductances.

---

## 15. Future Work

Several promising avenues remain for extending this research:
1. **Three-Variable Adaptive Reductions:** Extending the dimensional FHN framework to a three-variable system (e.g., adding an activity-dependent adaptation current $w_2$ or slow calcium variable) to systematically evaluate whether a third dynamical variable restores sustained adaptation and latency decoupling.
2. **Standardized Kinetic Benchmarking:** Implementing a standardized digital filtering and differentiation pipeline (e.g., 5-point central difference stencils on 10 kHz filtered traces) to benchmark action-potential phase-plane dynamics ($\mathrm{d}V/\mathrm{d}t$ vs. $V$) across detailed and reduced models.
3. **Multi-Specimen Population Sampling:** Expanding the sample size from single representative specimens ($n=1$) to multi-cell cohorts ($n \ge 20$) per cortical layer to quantify biological variance and statistical confidence intervals across cortical laminar sub-types.
4. **Higher-Dimensional Global Optimization:** Applying multi-objective genetic algorithms across all eight FHN parameters to investigate whether non-standard parameter regimes can achieve broader firing-rate ranges in Layer 6a without sacrificing latency.
5. **Projection-Identified and Steady-State-Calibrated Benchmarks:** Repeating the comparison on projection-identified neurons (e.g., retrogradely labelled IT, PT/ET and CT cells in V1), and recalibrating reduced models to steady-state rather than test-pulse input resistance, would allow layer-, class- and gain-specific conclusions that the present $n = 1$ design cannot support.

---

## 16. References

1. **Allen Institute for Brain Science.** *Allen Cell Types Database* (cell types: [celltypes.brain-map.org](https://celltypes.brain-map.org)); technical white papers "Electrophysiology Overview" and "Neuronal Models: Biophysical – Perisomatic". Available from: [celltypes.brain-map.org](https://celltypes.brain-map.org) and [community.brain-map.org](https://community.brain-map.org/t/documentation-cell-types-database/2845).
2. **Baker, A., Kalmbach, B., Morishima, M., Kim, J., Juavinett, A., Li, N., & Dembrow, N.** (2018). Specialized subpopulations of deep-layer pyramidal neurons in the neocortex: bridging cellular properties to functional consequences. *J. Neurosci.*, 38(24), 5441–5455. https://doi.org/10.1523/JNEUROSCI.0150-18.2018
3. **Benda, J., & Herz, A. V. M.** (2003). A universal model for spike-frequency adaptation. *Neural Comput.*, 15(11), 2523–2564. https://doi.org/10.1162/089976603322385063
4. **Born, G., Schneider-Soupiadis, F. A., Erisken, S., Vaiceliunaite, A., Lao, C. L., Mobarhan, M. H., Spacek, M. A., Einevoll, G. T., & Busse, L.** (2021). Corticothalamic feedback sculpts visual spatial integration in mouse thalamus. *Nat. Neurosci.*, 24(12), 1711–1720. https://doi.org/10.1038/s41593-021-00943-0
5. **Bortone, D. S., Olsen, S. R., & Scanziani, M.** (2014). Translaminar inhibitory cells recruited by layer 6 corticothalamic neurons suppress visual cortex. *Neuron*, 82(2), 474–485. https://doi.org/10.1016/j.neuron.2014.02.021
6. **Brette, R., & Gerstner, W.** (2005). Adaptive exponential integrate-and-fire model as an effective description of neuronal activity. *Journal of Neurophysiology*, 94(5), 3637–3642. https://doi.org/10.1152/jn.00686.2005
7. **Briggs, F., & Usrey, W. M.** (2008). Emerging views of corticothalamic function. *Curr. Opin. Neurobiol.*, 18(4), 403–407. https://doi.org/10.1016/j.conb.2008.09.002
8. **Brumberg, J. C., Hamzei-Sichani, F., & Yuste, R.** (2003). Morphological and physiological characterization of layer VI corticofugal neurons of mouse primary visual cortex. *J. Neurophysiol.*, 89(5), 2854–2867. https://doi.org/10.1152/jn.01051.2002
9. **Connors, B. W., & Gutnick, M. J.** (1990). Intrinsic firing patterns of diverse neocortical neurons. *Trends Neurosci.*, 13(3), 99–104. https://doi.org/10.1016/0166-2236(90)90185-D
10. **Crandall, S. R., Cruikshank, S. J., & Connors, B. W.** (2015). A corticothalamic switch: controlling the thalamus with dynamic synapses. *Neuron*, 86(3), 768–782. https://doi.org/10.1016/j.neuron.2015.03.040
11. **Dembrow, N. C., Chitwood, R. A., & Johnston, D.** (2010). Projection-specific neuromodulation of medial prefrontal cortex neurons. *J. Neurosci.*, 30(50), 16922–16937. https://doi.org/10.1523/JNEUROSCI.3644-10.2010
12. **Denman, D. J., & Contreras, D.** (2015). Complex effects on in vivo visual responses by specific projections from mouse cortical layer 6 to dorsal lateral geniculate nucleus. *J. Neurosci.*, 35(25), 9265–9280. https://doi.org/10.1523/JNEUROSCI.0027-15.2015
13. **Douglas, R. J., & Martin, K. A. C.** (2004). Neuronal circuits of the neocortex. *Annu. Rev. Neurosci.*, 27, 419–451. https://doi.org/10.1146/annurev.neuro.27.070203.144152
14. **Ermentrout, B.** (1998). Linearization of F-I curves by adaptation. *Neural Comput.*, 10(7), 1721–1729. https://doi.org/10.1162/089976698300017106
15. **FitzHugh, R.** (1961). Impulses and physiological states in theoretical models of nerve membrane. *Biophysical Journal*, 1(6), 445–466. https://doi.org/10.1016/S0006-3495(61)86902-6
16. **Gerfen, C. R., Paletzki, R., & Heintz, N.** (2013). GENSAT BAC cre-recombinase driver lines to study the functional organization of cerebral cortical and basal ganglia circuits. *Neuron*, 80(6), 1368–1383. https://doi.org/10.1016/j.neuron.2013.10.016
17. **Gong, S., Doughty, M., Harbaugh, C. R., Cummins, A., Hatten, M. E., Heintz, N., & Gerfen, C. R.** (2007). Targeting Cre recombinase to specific neuron populations with bacterial artificial chromosome constructs. *J. Neurosci.*, 27(37), 9817–9823. https://doi.org/10.1523/JNEUROSCI.2707-07.2007
18. **Gouwens, N. W., Berg, J., Feng, D., Sorensen, S. A., Zeng, H., Hawrylycz, M. J., Koch, C., & Arkhipov, A.** (2018). Systematic generation of biophysically detailed models for diverse cortical neuron types. *Nature Communications*, 9, 710. https://doi.org/10.1038/s41467-017-02718-3
19. **Gouwens, N. W., Sorensen, S. A., Berg, J., Lee, C., Jarsky, T., Ting, J., et al.** (2019). Classification of electrophysiological and morphological neuron types in the mouse visual cortex. *Nature Neuroscience*, 22(7), 1182–1195. https://doi.org/10.1038/s41593-019-0417-0
20. **Groh, A., Meyer, H. S., Schmidt, E. F., Heintz, N., Sakmann, B., & Krieger, P.** (2010). Cell-type specific properties of pyramidal neurons in neocortex underlying a layout that is modifiable depending on the cortical area. *Cereb. Cortex*, 20(4), 826–836. https://doi.org/10.1093/cercor/bhp152
21. **Harris, J. A., Hirokawa, K. E., Sorensen, S. A., Gu, H., Mills, M., Ng, L. L., et al.** (2014). Anatomical characterization of Cre driver mice for neural circuit mapping and manipulation. *Front. Neural Circuits*, 8, 76. https://doi.org/10.3389/fncir.2014.00076
22. **Harris, J. A., Mihalas, S., Hirokawa, K. E., Whitesell, J. D., Choi, H., Bernard, A., et al.** (2019). Hierarchical organization of cortical and thalamic connectivity. *Nature*, 575(7781), 195–202. https://doi.org/10.1038/s41586-019-1716-z
23. **Harris, K. D., & Mrsic-Flogel, T. D.** (2013). Cortical connectivity and sensory coding. *Nature*, 503(7474), 51–58. https://doi.org/10.1038/nature12654
24. **Harris, K. D., & Shepherd, G. M. G.** (2015). The neocortical circuit: themes and variations. *Nat. Neurosci.*, 18(2), 170–181. https://doi.org/10.1038/nn.3917
25. **Hattox, A. M., & Nelson, S. B.** (2007). Layer V neurons in mouse cortex projecting to different targets have distinct physiological properties. *J. Neurophysiol.*, 98(6), 3330–3340. https://doi.org/10.1152/jn.00397.2007
26. **Hay, E., Hill, S., Schürmann, F., Markram, H., & Segev, I.** (2011). Models of neocortical layer 5b pyramidal cells capturing a wide range of dendritic and perisomatic active properties. *PLoS Comput. Biol.*, 7(7), e1002107. https://doi.org/10.1371/journal.pcbi.1002107
27. **Hines, M. L., & Carnevale, N. T.** (1997). The NEURON simulation environment. *Neural Computation*, 9(6), 1179–1209. https://doi.org/10.1162/neco.1997.9.6.1179
28. **Hodgkin, A. L., & Huxley, A. F.** (1952). A quantitative description of membrane current and its application to conduction and excitation in nerve. *The Journal of Physiology*, 117(4), 500–544. https://doi.org/10.1113/jphysiol.1952.sp004764
29. **Hoerder-Suabedissen, A., & Molnár, Z.** (2015). Development, evolution and pathology of neocortical subplate neurons. *Nat. Rev. Neurosci.*, 16(3), 133–146. https://doi.org/10.1038/nrn3915
30. **Izhikevich, E. M.** (2007). *Dynamical Systems in Neuroscience: The Geometry of Excitability and Bursting*. MIT Press. https://doi.org/10.7551/mitpress/2526.001.0001
31. **Kim, E. J., Juavinett, A. L., Kyubwa, E. M., Jacobs, M. W., & Callaway, E. M.** (2015). Three types of cortical layer 5 neurons that differ in brain-wide connectivity and function. *Neuron*, 88(6), 1253–1267. https://doi.org/10.1016/j.neuron.2015.11.002
32. **Kim, J., Matney, C. J., Blankenship, A., Hestrin, S., & Brown, S. P.** (2014). Layer 6 corticothalamic neurons activate a cortical output layer, layer 5a. *J. Neurosci.*, 34(29), 9656–9664. https://doi.org/10.1523/JNEUROSCI.1325-14.2014
33. **Kirchgessner, M. A., Franklin, A. D., & Callaway, E. M.** (2020). Context-dependent and dynamic functional influence of corticothalamic pathways to first- and higher-order visual thalamus. *PNAS*, 117(23), 13066–13077. https://doi.org/10.1073/pnas.2002080117
34. **Kuznetsov, Y. A.** (2004). *Elements of Applied Bifurcation Theory* (3rd ed.). Applied Mathematical Sciences, Vol. 112. Springer. https://doi.org/10.1007/978-1-4757-3978-7
35. **Lam, Y.-W., & Sherman, S. M.** (2010). Functional organization of the somatosensory cortical layer 6 feedback to the thalamus. *Cereb. Cortex*, 20(1), 13–24. https://doi.org/10.1093/cercor/bhp077
36. **Larkum, M.** (2013). A cellular mechanism for cortical associations: an organizing principle for the cerebral cortex. *Trends Neurosci.*, 36(3), 141–151. https://doi.org/10.1016/j.tins.2012.11.006
37. **Larkum, M. E., Zhu, J. J., & Sakmann, B.** (1999). A new cellular mechanism for coupling inputs arriving at different cortical layers. *Nature*, 398(6725), 338–341. https://doi.org/10.1038/18686
38. **Lur, G., Vinck, M. A., Tang, L., Cardin, J. A., & Higley, M. J.** (2016). Projection-specific visual feature encoding by layer 5 cortical subnetworks. *Cell Rep.*, 14(11), 2538–2545. https://doi.org/10.1016/j.celrep.2016.02.050
39. **Mason, A., & Larkman, A.** (1990). Correlations between morphology and electrophysiology of pyramidal neurons in slices of rat visual cortex. II. Electrophysiology. *J. Neurosci.*, 10(5), 1415–1428. https://doi.org/10.1523/JNEUROSCI.10-05-01415.1990
40. **Nagumo, J., Arimoto, S., & Yoshizawa, S.** (1962). An active pulse transmission line simulating nerve axon. *Proceedings of the IRE*, 50(10), 2061–2070. https://doi.org/10.1109/JRPROC.1962.288235
41. **Olsen, S. R., Bortone, D. S., Adesnik, H., & Scanziani, M.** (2012). Gain control by layer six in cortical circuits of vision. *Nature*, 483(7387), 47–52. https://doi.org/10.1038/nature10835
42. **Pospischil, M., Toledo-Rodriguez, M., Monier, C., Piwkowska, Z., Bal, T., Frégnac, Y., Markram, H., & Destexhe, A.** (2008). Minimal Hodgkin–Huxley type models for different classes of cortical and thalamic neurons. *Biol. Cybern.*, 99(4–5), 427–441. https://doi.org/10.1007/s00422-008-0263-8
43. **Prescott, S. A., De Koninck, Y., & Sejnowski, T. J.** (2008). Biophysical basis for three distinct dynamical mechanisms of action potential initiation. *PLoS Comput. Biol.*, 4(10), e1000198. https://doi.org/10.1371/journal.pcbi.1000198
44. **Sheets, P. L., Suter, B. A., Kiritani, T., Chan, C. S., Surmeier, D. J., & Shepherd, G. M. G.** (2011). Corticospinal-specific HCN expression in mouse motor cortex. *J. Neurophysiol.*, 106(5), 2216–2231. https://doi.org/10.1152/jn.00232.2011
45. **Shepherd, G. M. G.** (2013). Corticostriatal connectivity and its role in disease. *Nat. Rev. Neurosci.*, 14(4), 278–291. https://doi.org/10.1038/nrn3469
46. **Sherman, S. M., & Guillery, R. W.** (1998). On the actions that one nerve cell can have on another: distinguishing "drivers" from "modulators". *PNAS*, 95(12), 7121–7126. https://doi.org/10.1073/pnas.95.12.7121
47. **Sillito, A. M., Cudeiro, J., & Jones, H. E.** (2006). Always returning: feedback and sensory processing in visual cortex and thalamus. *Trends Neurosci.*, 29(6), 307–316. https://doi.org/10.1016/j.tins.2006.05.001
48. **Tasic, B., Menon, V., Nguyen, T. N., Kim, T. K., Jarsky, T., Yao, Z., et al.** (2016). Adult mouse cortical cell taxonomy revealed by single cell transcriptomics. *Nat. Neurosci.*, 19(2), 335–346. https://doi.org/10.1038/nn.4216
49. **Tasic, B., Yao, Z., Graybuck, L. T., Smith, K. A., Nguyen, T. N., Bertagnolli, D., et al.** (2018). Shared and distinct transcriptomic cell types across neocortical areas. *Nature*, 563(7729), 72–78. https://doi.org/10.1038/s41586-018-0654-5
50. **Teeter, C., Iyer, R., Menon, V., Gouwens, N., Feng, D., Berg, J., Szafer, A., Cain, N., Zeng, H., Hawrylycz, M., Koch, C., & Mihalas, S.** (2018). Generalized leaky integrate-and-fire models classify multiple neuron types. *Nature Communications*, 9, 709. https://doi.org/10.1038/s41467-017-02717-4
51. **Thomson, A. M.** (2010). Neocortical layer 6, a review. *Front. Neuroanat.*, 4, 13. https://doi.org/10.3389/fnana.2010.00013
52. **Vélez-Fort, M., Rousseau, C. V., Niedworok, C. J., Wickersham, I. R., Rancz, E. A., Brown, A. P. Y., Strom, M., & Margrie, T. W.** (2014). The stimulus selectivity and connectivity of layer six principal cells reveals cortical microcircuits underlying visual processing. *Neuron*, 83(6), 1431–1443. https://doi.org/10.1016/j.neuron.2014.08.001

---

## 17. Reproducibility and Artifact Availability

All code, data pipelines, calibration algorithms, and evaluation scripts are maintained on the `ashish-work` branch of repository `Patel-Princy/INCM_project`.

### 17.1 Authoritative Repository Artifacts
- **Primary Synthesis Artifact:** [`results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_CROSS_POPULATION_SYNTHESIS.md)
- **Baseline Flash Handoff:** [`results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5_BASELINE_AND_FLASH_HANDOFF.md)
- **Claim Audit Records:**
  - [`results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5B1_SCIENTIFIC_CLAIM_AUDIT.md)
  - [`results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5B2_EVIDENCE_DISCREPANCY_RESOLUTION.md)
  - [`results/phase5/PHASE5B3_FINAL_CONSISTENCY_CHECK.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5B3_FINAL_CONSISTENCY_CHECK.md)

### 17.2 Primary Data and Summary CSV Files
- Detailed Model Held-Out Metrics: `results/phase3b/heldout_metrics.csv`
- Detailed Model Rheobase Brackets: `results/phase3b/heldout_rheobase.csv`
- FHN Calibrated Parameters: `results/phase4b/fhn_fitted_parameters.csv`
- FHN Calibration Metrics: `results/phase4b/fhn_calibration_metrics.csv`
- FHN Held-Out Summary: `results/phase4c/population_summary.csv`
- FHN Held-Out Detailed Metrics: `results/phase4c/fhn_heldout_metrics.csv`
- Hopf Bifurcation Checks: `results/phase4c3/phase4c3_hopf_independent_checks.csv`
- Limit-Cycle Fold Verification: `results/phase4c3/phase4c3_fold_verification.csv`
- Open Bistability Verification: `results/phase4c3/phase4c3_bistability_verification.csv`
- Biological Adaptation Census: `results/phase4c3/phase4c3_biological_adaptation_scope.csv`
- Population D 625-Point Grid Scan: `results/phase4b1/fhn_population_d_pareto_audit.csv`
- Population D 961-Point Grid Scan: `results/phase4b2/fhn_population_d_grid_points.csv`

### 17.3 Automated Test Suite
The repository includes an extensive regression test suite containing **451 tests** verifying data integrity, numerical integration, bifurcation metrics, and scientific claims:
```bash
python -m pytest tests -q
# Status: 451 passed in 58.86s
```
Base commit baseline: `d6e1585` (Phase 4C.3.1).


> **Status: Supplementary literature draft. Not integrated into the main manuscript. The primary Layer 5 section is the Phase 5F review (results/phase5/PHASE5F_L5_L6A_LITERATURE_REVIEW.md). Citations in this draft are pending verification.**

# Layer 5 (Population C) Literature Review and Electrophysiological Validation Report

**Course Project:** Introduction to Neural & Cognitive Modelling (INCM)  
**Author:** Princy  
**Branch:** `Princy-work`  
**Target Specimen:** Specimen ID `471129934` (Mouse Primary Visual Cortex VISp, Layer 5)  
**Assigned Population:** Population C (VISp L5 Spiny Excitatory Neuron)  
**Transgenic Driver Line:** `Rbp4-Cre_KL100`  
**Detailed Biophysical Model ID:** `480624414` (Allen Perisomatic Active Model)  
**Designated Calibration Sweep:** Sweep 51 (+410.0 pA, 1.0 s step, 200 kHz sampling)  

---

## 1. Cortical Role and Synaptic Connectivity in Mouse V1

Layer 5 (L5) represents the primary infragranular output layer of the cerebral cortex, mediating long-range subcortical and cortical communication:

1. **Cortical Circuit Architecture & Projection Targets:**
   - L5 pyramidal neurons are classified morphologically and transcriptionally into two major sub-populations:
     - **Extratelencephalic (ET / PT-like) Neurons:** Large thick-tufted pyramidal cells that project to subcortical structures (superior colliculus, pons, striatum, and thalamus).
     - **Intratelencephalic (IT-like) Neurons:** Slender-tufted pyramidal cells that project bilaterally to other cortical areas and striatum.
   - The transgenic driver line `Rbp4-Cre_KL100` specifically enriches for L5 pyramidal tract and associative projection neurons.
2. **Apical Dendrite Integration:**
   - L5 pyramidal neurons possess prominent apical dendrites that ascend across Layers 4, 3, and 2 to arborize in Layer 1.
   - This architecture allows L5 neurons to perform coincidence detection: combining bottom-up sensory drive received at basal dendrites with top-down feedback/modulatory signals arriving in Layer 1.
3. **Translaminar & Recurrent Synaptic Inflow:**
   - They receive major feedforward inputs from Layer 2/3 and Layer 4, collaterals from neighboring L5 pyramidal neurons, and modulatory inputs from thalamic nucleus LP (lateral posterior nucleus / pulvinar).
4. **Functional In Vivo Role:**
   - As the principal motor and subcortical broadcast system of V1, L5 pyramidal cells drive ocular motor responses, feature extraction, and predictive visual signals.

---

## 2. Electrophysiological Traits: Literature vs. Recorded Specimen Data

In in vitro slice electrophysiology (Gouwens et al., 2019; Markram et al., 1997; Kasper et al., 1994), L5 pyramidal cells exhibit a distinct physiological profile characterized by low input resistance, high rheobase, hyperpolarization-activated inward rectification ($I_{\mathrm{h}}$ sag), and strong adaptation:

### 2.1 Resting Membrane Potential ($V_{\mathrm{rest}}$)
- **Literature Expectation:** $-67.0\text{ mV}$ to $-75.0\text{ mV}$.
- **Recorded Specimen `471129934`:** $-69.3\text{ mV}$.
- **Assessment:** Well within expected physiological bounds. L5 pyramidal cells frequently rest slightly more depolarized than L2/3 neurons due to tonic inward conductances (such as $I_{\mathrm{h}}$ at rest).

### 2.2 Input Resistance ($R_{\mathrm{in}}$)
- **Literature Expectation:** $25\text{ M}\Omega$ to $55\text{ M}\Omega$.
- **Recorded Specimen `471129934`:** $31.3\text{ M}\Omega$.
- **Assessment:** Exact canonical match. The massive soma and extensive dendritic tree of L5 pyramidal cells provide a large membrane surface area, resulting in low total input resistance ($R_{\mathrm{in}} \approx 31\text{ M}\Omega$).

### 2.3 Rheobase & Current Threshold
- **Literature Expectation:** $300\text{ pA}$ to $450\text{ pA}$.
- **Recorded Specimen `471129934`:** Sustained rheobase sits in the interval $(370.0, 390.0]\text{ pA}$.
  - Sweep 45 (+290 pA) to Sweep 48 (+350 pA): 1 to 3 isolated spikes (perithreshold transient discharge).
  - Sweep 49 (+370 pA): 5 spikes.
  - Sweep 50 (+390 pA): 6 spikes.
  - Sweep 51 (+410 pA, Calibration): 9 spikes ($9\text{ Hz}$).
  - Sweep 52 (+430 pA): 11 spikes ($11\text{ Hz}$).
- **Assessment:** Matches literature predictions. By Ohm's Law ($\Delta V = I \cdot R_{\mathrm{in}}$), a neuron with low input resistance ($31\text{ M}\Omega$) requires roughly $3\times$ more current to depolarize to spike threshold than an $80\text{ M}\Omega$ L2/3 neuron.

### 2.4 Hyperpolarization Sag ($I_{\mathrm{h}}$) & Firing Adaptation
- **Literature Expectation:** Prominent voltage sag during hyperpolarizing current injections due to hyperpolarization-activated cyclic nucleotide-gated (HCN) channel activation ($I_{\mathrm{h}}$ current).
- **Recorded Specimen `471129934`:**
  - Clear sag is visible in large negative sweeps (e.g., $-110\text{ pA}$ step depolarizes from a peak trough back towards baseline).
  - In calibration Sweep 51 (+410 pA): Initial $\mathrm{ISI}_1 = 52.4\text{ ms}$, terminating at $\mathrm{ISI}_8 = 154.2\text{ ms}$ (a $2.94\times$ deceleration).
- **Assessment:** Consistent with canonical Layer 5 thick-tufted regular-spiking pyramidal electrophysiology.

---

## 3. Comparative Synthesis: Literature vs. Recorded Data vs. Model Performance

The table below contrasts theoretical literature expectations, empirical recordings from Specimen `471129934`, and the performance of both the Detailed Biophysical Model (Hodgkin-Huxley perisomatic multi-conductance) and the Reduced FitzHugh-Nagumo (FHN) model:

| Electrophysiological Feature | Literature Expectation (Mouse V1 L5 RS Pyramidal) | Biological Recording (Specimen 471129934) | Detailed Allen Model (ID 480624414) | Reduced FHN Model (2-Variable ODE) | Key Mechanistic Insight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Resting Potential ($V_{\mathrm{rest}}$)** | $-67\text{ to }-75\text{ mV}$ | **$-69.3\text{ mV}$** | $-69.3\text{ mV}$ ($\Delta = 0.0\text{ mV}$) | $-69.3\text{ mV}$ ($\Delta = 0.0\text{ mV}$) | Both models anchor baseline resting equilibrium accurately. |
| **Input Resistance ($R_{\mathrm{in}}$)** | $25\text{ to }55\text{ M}\Omega$ | **$31.3\text{ M}\Omega$** | $31.8\text{ M}\Omega$ | $31.3\text{ M}\Omega$ | Both models reproduce the low input resistance characteristic of large L5 neurons. |
| **Rheobase Current** | $300\text{ to }450\text{ pA}$ | **$(370, 390]\text{ pA}$** | $(370, 390]\text{ pA}$ | $(210, 230]\text{ pA}$ | FHN undergoes subcritical Hopf bifurcation earlier than biological rheobase. |
| **Calibration Firing Rate (+410 pA)** | $8\text{ to }15\text{ Hz}$ | **$9\text{ Hz}$ (9 spikes)** | **$9\text{ Hz}$ (9 spikes)** | **$9\text{ Hz}$ (9 spikes)** | Exact match across all representations at the designated calibration point. |
| **Hyperpolarization Sag ($I_{\mathrm{h}}$)** | Strong inward rectification | **Present** (trough relaxation) | **Reproduced** (includes active $I_{\mathrm{h}}$ channels) | **Absent** (linear passive recovery) | 2D FHN lacks hyperpolarization-activated inward conductance dynamics. |
| **Held-Out Spike Count Error (MAE)** | $0\text{ spikes}$ (Ideal) | Ground Truth Reference | **$0.62\text{ spikes}$** | **$0.38\text{ spikes}$** | **Surprising Result:** The reduced FHN model slightly outperforms the detailed model on mean spike count error across 34 held-out sweeps! |
| **Subthreshold Voltage RMSE** | $< 5\text{ mV}$ | Ground Truth Reference | **$3.69\text{ mV}$** | **$7.41\text{ mV}$** | Detailed model achieves superior subthreshold waveform prediction. |
| **F-I Slope Above Rheobase** | Shallow, regular increase | **Moderate slope** | **Well matched** | **Well matched** | FHN matches the low-gain firing regime of L5 better than L2/3. |

---

## 4. Discussion & Educational Takeaway for First-Year Modelling

1. **Why FHN Performed Surprisingly Well on Layer 5:**
   - Across all 34 held-out test sweeps, the reduced FHN model achieved a Mean Absolute Spike Error of only **$0.38\text{ spikes}$** (compared to $0.62$ for the biophysical model).
   - Because Layer 5 neurons fire at moderate, steady frequencies ($1–11\text{ Hz}$) and do not reach the extreme high-firing rates where depolarization block occurs in FHN, the simple limit-cycle dynamics of FHN captured the overall spike output remarkably well.
2. **The Price of Model Reduction:**
   - Despite matching spike counts, FHN cannot reproduce the subthreshold voltage waveform features ($I_{\mathrm{h}}$ sag, afterhyperpolarization shapes), leading to a higher subthreshold voltage error ($7.41\text{ mV}$ vs $3.69\text{ mV}$).
   - This illustrates a fundamental principle of computational neuroscience: **phenomenological models can predict output spike counts accurately within a bounded operating range, but biophysical models are required to capture underlying ion-channel mechanisms and subthreshold integrative dynamics.**

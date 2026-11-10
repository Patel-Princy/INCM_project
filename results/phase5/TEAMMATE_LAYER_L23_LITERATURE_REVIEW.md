# Layer 2/3 (Population B) Literature Review and Electrophysiological Validation Report

**Course Project:** Introduction to Neural & Cognitive Modelling (INCM)  
**Author:** Princy  
**Branch:** `Princy-work`  
**Target Specimen:** Specimen ID `318808427` (Mouse Primary Visual Cortex VISp, Layer 2/3)  
**Assigned Population:** Population B (VISp L2/3 Spiny Excitatory Neuron)  
**Transgenic Driver Line:** `Nr5a1-Cre`  
**Detailed Biophysical Model ID:** `473863035` (Allen Perisomatic Active Model)  
**Designated Calibration Sweep:** Sweep 40 (+190.0 pA, 1.0 s step, 200 kHz sampling)  

---

## 1. Cortical Role and Synaptic Connectivity in Mouse V1

Layer 2/3 (L2/3) comprises the supragranular layers of the primary visual cortex (V1 / VISp) and serves as the principal hub for intracortical association, feature integration, and context-dependent visual processing:

1. **Feedforward Thalamocortical Relay Processing:**
   - L2/3 pyramidal neurons receive primary feedforward excitatory drive from Layer 4 spiny stellate and star pyramidal neurons.
   - They synthesize simple receptive field inputs into direction- and orientation-selective complex receptive fields.
2. **Horizontal Recurrent & Lateral Connections:**
   - L2/3 excitatory pyramidal cells establish dense horizontal axon collaterals that extend up to 1–2 mm within supragranular layers.
   - These recurrent networks interact with local inhibitory interneurons (parvalbumin-positive PV basket cells, somatostatin-positive SOM cells, and VIP disinhibitory cells) to generate surround suppression and gain control.
3. **Translaminar & Feedback Projections:**
   - L2/3 pyramidal neurons project descending axons to infragranular layers (Layer 5 and Layer 6), relaying processed supragranular representations to cortical output stages.
   - They provide the primary feedforward visual drive to higher visual areas (e.g., LM, AL, RL, PM).
4. **Functional In Vivo Firing Regime:**
   - Mouse V1 L2/3 pyramidal neurons operate in a sparse firing regime in vivo, exhibiting low spontaneous baseline firing rates ($< 1\text{ Hz}$) and selective, transient bursts in response to optimal visual stimuli.

---

## 2. Electrophysiological Traits: Literature vs. Recorded Specimen Data

In in vitro whole-cell patch-clamp recordings from acute cortical brain slices (Gouwens et al., 2019; Lefort et al., 2009; Mason et al., 1991), L2/3 pyramidal neurons display distinct regular-spiking (RS) electrophysiological features. Below, we compare literature expectations with the actual measurements from Specimen `318808427`:

### 2.1 Resting Membrane Potential ($V_{\mathrm{rest}}$)
- **Literature Expectation:** $-70.0\text{ mV}$ to $-80.0\text{ mV}$.
- **Recorded Specimen `318808427`:** $-75.8\text{ mV}$ to $-76.0\text{ mV}$ (Average baseline: $-75.9\text{ mV}$).
- **Assessment:** Excellent alignment. The recorded cell exhibits a hyperpolarized resting membrane potential typical of healthy cortical pyramidal neurons with strong resting potassium leak conductance ($I_{\mathrm{leak}}$).

### 2.2 Input Resistance ($R_{\mathrm{in}}$)
- **Literature Expectation:** $70\text{ M}\Omega$ to $150\text{ M}\Omega$ for mouse L2/3 pyramidal cells.
- **Recorded Specimen `318808427`:** $80.3\text{ M}\Omega$ (measured across subthreshold test hyperpolarizing pulses).
- **Assessment:** Consistent with literature. The input resistance of L2/3 neurons is substantially higher than that of large Layer 5 pyramidal neurons ($30–50\text{ M}\Omega$) due to smaller somatic surface area and lower total passive membrane conductance.

### 2.3 Rheobase & Threshold Excitability
- **Literature Expectation:** $100\text{ pA}$ to $160\text{ pA}$ for sustained action potential discharge.
- **Recorded Specimen `318808427`:** Sustained rheobase sits in the interval $(110.0, 130.0]\text{ pA}$.
  - Sweep 36 (+110 pA): 0 spikes (subthreshold passive depolarization to $-45.0\text{ mV}$).
  - Sweep 37 (+130 pA): 1 spike (perithreshold threshold crossing at $t = 1054.4\text{ ms}$).
  - Sweep 38 (+150 pA): 8 spikes ($8\text{ Hz}$).
  - Sweep 40 (+190 pA, Calibration): 19 spikes ($19\text{ Hz}$).
- **Assessment:** Fits empirical literature closely.

### 2.4 Spike-Frequency Adaptation (SFA)
- **Literature Expectation:** Moderate to strong spike-frequency adaptation driven by calcium-activated slow potassium conductances ($I_{\mathrm{AHP}}$) and muscarinic-sensitive potassium currents ($I_{\mathrm{M}}$).
- **Recorded Specimen `318808427`:**
  - In calibration Sweep 40 (+190 pA):
    - Initial inter-spike interval ($\mathrm{ISI}_1$): $27.8\text{ ms}$ ($36.0\text{ Hz}$ instantaneous rate).
    - Middle inter-spike interval ($\mathrm{ISI}_8$): $47.6\text{ ms}$ ($21.0\text{ Hz}$).
    - Final inter-spike interval ($\mathrm{ISI}_{18}$): $62.2\text{ ms}$ ($16.1\text{ Hz}$).
  - Adaptation ratio ($\mathrm{ISI}_{\mathrm{final}} / \mathrm{ISI}_1$): $\approx 2.24$.
- **Assessment:** Classic regular-spiking adaptation phenotype.

---

## 3. Comparative Synthesis: Literature vs. Recorded Data vs. Model Performance

The table below contrasts theoretical literature expectations, empirical recordings from Specimen `318808427`, and the performance of both the Detailed Biophysical Model (Hodgkin-Huxley perisomatic multi-conductance) and the Reduced FitzHugh-Nagumo (FHN) model:

| Electrophysiological Feature | Literature Expectation (Mouse V1 L2/3 RS Pyramidal) | Biological Recording (Specimen 318808427) | Detailed Allen Model (ID 473863035) | Reduced FHN Model (2-Variable ODE) | Key Mechanistic Insight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Resting Potential ($V_{\mathrm{rest}}$)** | $-70\text{ to }-80\text{ mV}$ | **$-75.9\text{ mV}$** | $-75.9\text{ mV}$ ($\Delta = 0.0\text{ mV}$) | $-75.9\text{ mV}$ ($\Delta = 0.0\text{ mV}$) | Both models anchor resting baseline accurately. |
| **Input Resistance ($R_{\mathrm{in}}$)** | $70\text{ to }150\text{ M}\Omega$ | **$80.3\text{ M}\Omega$** | $79.8\text{ M}\Omega$ | $78.7\text{ M}\Omega$ | FHN matches total linearized resting conductance well. |
| **Rheobase Current** | $100\text{ to }160\text{ pA}$ | **$(110, 130]\text{ pA}$** | $(130, 150]\text{ pA}$ | $(70, 90]\text{ pA}$ | FHN undergoes subcritical Hopf bifurcation early, initiating firing below biological rheobase. |
| **Calibration Firing Rate (+190 pA)** | $15\text{ to }25\text{ Hz}$ | **$19\text{ Hz}$ (19 spikes)** | **$19\text{ Hz}$ (19 spikes)** | **$17\text{–}19\text{ Hz}$ (17–19 spikes)** | Both models are calibrated to match the target sweep. |
| **Spike Adaptation** | Pronounced ($\mathrm{ISI}$ increases by $2\text{–}3\times$) | **$2.24\times$ deceleration** | **$2.15\times$ deceleration** | **$1.05\times$ (Negligible)** | FHN's single recovery variable $w$ cannot capture multi-timescale adaptation ($I_{\mathrm{AHP}} / I_{\mathrm{M}}$). |
| **High Current Firing (+250 pA to +270 pA)** | Sustained high-frequency firing ($25\text{–}35\text{ Hz}$) | **$27\text{ spikes}$ (+250 pA)<br>$29\text{ spikes}$ (+270 pA)** | **$29\text{ spikes}$ (+250 pA)<br>$33\text{ spikes}$ (+270 pA)** | **$2\text{ spikes}$ (+250 pA)<br>$1\text{ spike}$ (+270 pA)** | **Depolarization Block:** FHN limit cycle collapses via cubic nullcline geometry and heavy recovery lock. |
| **Held-Out Spike Count Error (MAE)** | $0\text{ spikes}$ (Ideal) | Ground Truth Reference | **$1.06\text{ spikes}$** | **$4.28\text{ spikes}$** | Detailed model generalizes $4\times$ better across held-out sweeps. |
| **Subthreshold Voltage RMSE** | $< 5\text{ mV}$ | Ground Truth Reference | **$4.14\text{ mV}$** | **$11.19\text{ mV}$** | Detailed model accurately predicts passive subthreshold charging curves. |

---

## 4. Discussion & Educational Takeaway for First-Year Modelling

1. **Where Reduced Models Excel:**
   - The 2-variable FitzHugh-Nagumo model captures the fundamental threshold excitation mechanism with minimal computational overhead.
   - It reliably matches quiescent baseline behavior, approximate onset latency, and firing rate at the single calibrated current.
2. **Where Biophysical Realism Is Indispensable:**
   - **Depolarization Block Collapse:** As stimulus current increases past +210 pA, FHN fails catastrophically for L2/3, collapsing to 1–2 spikes because the cubic recovery system enters an equilibrium fixed point lock. Biological pyramidal neurons employ persistent sodium and multiple delayed-rectifier potassium conductances that maintain repetitive firing up to high frequencies.
   - **Spike-Frequency Adaptation:** The single linear recovery variable $w$ in FHN cannot model slow calcium accumulation and calcium-dependent potassium channels ($K_{\mathrm{Ca}}$).

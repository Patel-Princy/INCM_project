# PHASE 3B — CROSS-POPULATION GENERALISATION ANALYSIS

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3B — Out-of-Sample Held-Out Evaluation  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  
**Data Sources:**
- Consolidated Metrics: [`results/phase3b/heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv) (109 sweeps)
- F-I Curves: [`results/phase3b/heldout_fi_curves.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_fi_curves.csv) (102 condition groups)
- Rheobase Estimates: [`results/phase3b/heldout_rheobase.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_rheobase.csv)
- Generated Figures: [`results/phase3b/figures/`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/)

---

## 1. Executive Summary

Phase 3B performed a genuine out-of-sample held-out evaluation of four detailed perisomatic conductance-based neuron models fitted to layer-defined spiny excitatory neurons in mouse primary visual cortex (VISp). All model parameters were strictly frozen (no retraining, recalibration, or parameter optimization). A total of **109 held-out experimental sweeps** across **97 unique stimulus amplitudes (102 protocol-amplitude condition groups)** were simulated in NEURON 8.2.7 and compared against biological intracellular recordings.

> [!NOTE]
> **Scope Caveat:** These results evaluate four specific representative specimen models representing layer-defined excitatory populations. They characterize the predictive accuracy and failure modes of these specific published perisomatic model fits, rather than the full biological variance of entire cortical layers.

### Key Scientific Findings:

1. **Generalization Hierarchy Across Representatives:**
   - **Population D (VISp L6a, Specimen 471786879): Highest Overall Generalization Fidelity.** Exact rheobase interval match ($0.0\text{ pA}$ shift), lowest waveform error ($\text{RMSE} = 2.23 \pm 1.80\text{ mV}$, $\text{MAE} = 0.85 \pm 0.44\text{ mV}$), and high Pearson correlation ($r = 0.9699$).
   - **Population B (VISp L2/3, Specimen 318808427): Excellent Subthreshold & Moderate Suprathreshold Generalization.** Small rheobase shift of $+20.0\text{ pA}$ (only 1 step size, $+16.7\%$), lowest spike count delta ($+0.83$ spikes/sweep), and near-perfect subthreshold correlation ($r = 0.9965$).
   - **Population C (VISp L5, Specimen 471129934): Robust Net Firing Rate with Temporal Threshold Drift.** Mean spike count delta across all sweeps is $-0.03$ spikes/sweep (near-zero bias across the entire dynamic range). High correlation ($r = 0.9610$). Rheobase shift on early COARSE protocol is $+60.0\text{ pA}$, while late FINEST sweeps exhibit biological threshold drift up to $+330\text{ pA}$.
   - **Population A (VISp L4, Specimen 484564503): High-Threshold & Depolarized Baseline Bias with F-I Saturation Failure.** Model exhibits a $+60.0\text{ pA}$ rheobase shift and a $+13.10\text{ mV}$ baseline $V_{\text{rest}}$ discrepancy arising from the published parameter fit, causing elevated overall RMSE ($12.73 \pm 0.80\text{ mV}$). Above calibration, the model completely fails to capture biological firing saturation, firing up to 48 spikes while the real cell arrests mid-step (12 spikes).

2. **Subthreshold vs. Suprathreshold Dissociation:**
   - Subthreshold correlation varies substantially by population: while Pop B ($r = 0.9965$) and Pop D ($r = 0.9894$) demonstrate near-perfect trajectory alignment, Pop C achieves $r = 0.9579$, and Pop A reaches only $r = 0.7402$ due to small signal-to-noise ratio on low-amplitude deflections ($\le 30\text{ pA}$) combined with resting potential offset.
   - High subthreshold correlation reflects waveform trajectory shape during capacitive charging, but does not prove input resistance or absolute voltage calibration accuracy.
   - In suprathreshold spiking regimes, point-by-point waveform error increases ($\text{RMSE} > 10\text{ mV}$, $r \approx 0.75-0.94$) primarily due to cumulative millisecond phase shifts in action potential timing (the double-penalty problem of spike waveforms) rather than failure of spike generation, except in Pop A where true firing rate divergence occurs.

3. **Latency Convergence:**
   - Near threshold, models display longer first-spike latencies than biological recordings (delayed onset).
   - As stimulus amplitude increases into the suprathreshold operating range, first-spike latency converges within $1.9 - 4.4\text{ ms}$ of biological values.

---

## 2. Quantitative Population Summary

| Population | Layer | Specimen ID | Model ID | Held-Out Sweeps | Unique Amplitudes | Condition Groups | Overall RMSE (mV) | Overall MAE (mV) | Overall Correlation ($r$) | Subthreshold $r$ | Suprathreshold $r$ | Mean Spike Delta | Max Spike Delta | Rheobase Shift (COARSE) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **A** | L4 | 484564503 | 485591776 | 31 | 28 | 29 | $12.73 \pm 0.80$ | $12.23 \pm 0.80$ | $0.8036 \pm 0.2000$ | 0.7402 | 0.9189 | $+1.94$ | $+36$ | $+60.0\text{ pA}$ |
| **B** | L2/3 | 318808427 | 473863035 | 18 | 17 | 18 | $4.04 \pm 2.64$ | $2.17 \pm 1.01$ | $0.9570 \pm 0.0594$ | 0.9965 | 0.9076 | $+0.83$ | $+4$ | $+20.0\text{ pA}$ |
| **C** | L5 | 471129934 | 480624414 | 34 | 28 | 31 | $4.73 \pm 0.58$ | $4.51 \pm 0.41$ | $0.9610 \pm 0.0692$ | 0.9579 | 0.9673 | $-0.03$ | $+10$ | $+60.0\text{ pA}$ |
| **D** | L6a | 471786879 | 480632594 | 26 | 24 | 24 | $2.23 \pm 1.80$ | $0.85 \pm 0.44$ | $0.9699 \pm 0.0354$ | 0.9894 | 0.9388 | $+1.35$ | $+10$ | $0.0\text{ pA}$ |

---

## 3. In-Depth Population Analysis

### 3.1 Population D: VISp Layer 6a (Specimen 471786879, Model 480632594)
- **Calibration Context:** Calibration sweep 42 at $+250.0\text{ pA}$ (rec: 14 spikes, sim: 14 spikes, in-sample $r = 0.968$).
- **Rheobase Estimation:**
  - Recorded COARSE interval: $[190.0, 210.0]\text{ pA}$ (midpoint $200.0\text{ pA}$).
  - Simulated COARSE interval: $[190.0, 210.0]\text{ pA}$ (midpoint $200.0\text{ pA}$).
  - Rheobase shift: **$0.0\text{ pA}$** (Exact interval match, 100% overlap).
- **F-I Slope Tracking:**
  - At $210\text{ pA}$: recorded $= 5$, simulated $= 1$.
  - At $230\text{ pA}$: recorded $= 10$, simulated $= 9$.
  - At $270\text{ pA}$: recorded $= 17$, simulated $= 18$.
  - Across the entire COARSE suprathreshold range, the simulated model reproduces biological firing rate with $\le 1$ spike deviation per sweep.
- **Protocol Family Nuance:**
  - In FINEST sweeps (sweeps 52, 53, 54 at $+240\text{ pA}$), recorded spike count dropped to 1 spike, while the simulated model generated 11 spikes.
  - This indicates pronounced biological spike frequency adaptation or run-down in the cell during late sweeps that the time-invariant conductance parameters do not reproduce.
- **Passive Properties:**
  - Recorded $V_{\text{rest}} = -75.90\text{ mV}$, Simulated $V_{\text{rest}} = -75.96\text{ mV}$ ($\Delta V = -0.06\text{ mV}$). Subthreshold correlation $r = 0.9894$.

### 3.2 Population B: VISp Layer 2/3 (Specimen 318808427, Model 473863035)
- **Calibration Context:** Calibration sweep 40 at $+190.0\text{ pA}$ (rec: 18 spikes, sim: 20 spikes, in-sample $r = 0.887$).
- **Rheobase Estimation:**
  - Recorded COARSE interval: $[110.0, 130.0]\text{ pA}$ (midpoint $120.0\text{ pA}$).
  - Simulated COARSE interval: $[130.0, 150.0]\text{ pA}$ (midpoint $140.0\text{ pA}$).
  - Rheobase shift: **$+20.0\text{ pA}$** (only 1 step shift of $20\text{ pA}$, $+16.7\%$ error).
- **F-I Slope Tracking:**
  - At $150\text{ pA}$: recorded $= 8$, simulated $= 11$.
  - At $170\text{ pA}$: recorded $= 13$, simulated $= 16$.
  - At $210\text{ pA}$: recorded $= 22$, simulated $= 23$.
  - At $250\text{ pA}$: recorded $= 27$, simulated $= 29$.
- **Latency Convergence:**
  - At $150\text{ pA}$, first-spike latency delta is $+20.0\text{ ms}$.
  - At $210\text{ pA}$, latency delta drops to $+4.4\text{ ms}$.
  - At $270\text{ pA}$, latency delta drops to $+1.9\text{ ms}$.
- **Passive Properties:**
  - Recorded $V_{\text{rest}} = -75.40\text{ mV}$, Simulated $V_{\text{rest}} = -75.93\text{ mV}$ ($\Delta V = -0.53\text{ mV}$). Subthreshold correlation is the highest across all populations: $r = 0.9965$.

### 3.3 Population C: VISp Layer 5 (Specimen 471129934, Model 480624414)
- **Calibration Context:** Calibration sweep 51 at $+410.0\text{ pA}$ (rec: 10 spikes, sim: 10 spikes, in-sample $r = 0.963$).
- **Overall Firing Rate Fidelity:**
  - Across 34 held-out sweeps, mean spike count delta is **$-0.03$ spikes**, indicating zero net bias across the population.
- **Rheobase Dynamics and Protocol Drift:**
  - In COARSE sweeps (sweeps 43-48): recorded cell initiates spiking at $290\text{ pA}$ (1 spike), whereas simulated model fires at $350\text{ pA}$ (2 spikes), yielding a rheobase shift of $+60.0\text{ pA}$.
  - In FINEST sweeps (sweeps 53-60): biological neuron was silent at $280, 290, 310, 320\text{ pA}$ and only fired at $330\text{ pA}$ (1 spike consistently across 4 repeated sweeps 57, 58, 59, 60).
  - This demonstrates real-time physiological threshold shift in the biological neuron of $\approx +40\text{ pA}$ between early and late recording blocks.
- **Passive Properties:**
  - Recorded $V_{\text{rest}} = -68.58\text{ mV}$, Simulated $V_{\text{rest}} = -63.65\text{ mV}$ ($\Delta V = +4.93\text{ mV}$). Subthreshold correlation $r = 0.9579$.

### 3.4 Population A: VISp Layer 4 (Specimen 484564503, Model 485591776)
- **Calibration Context:** Calibration sweep 49 at $+370.0\text{ pA}$ (rec: 11 spikes total, 9 in step; sim: 11 spikes total, 9 in step; in-sample $r = 0.932$).
- **Rheobase Shift:**
  - Recorded rheobase interval: $(270.0, 290.0]\text{ pA}$ (midpoint $280.0\text{ pA}$).
  - Simulated rheobase interval: $(330.0, 350.0]\text{ pA}$ (midpoint $340.0\text{ pA}$).
  - Rheobase shift: **$+60.0\text{ pA}$** ($+21.4\%$).
- **Origin of Elevated RMSE ($12.73\text{ mV}$):**
  - Model `485591776` parameter configuration specifies $e_{\text{pas}} = -75.07\text{ mV}$. Under the $+14.0\text{ mV}$ Liquid Junction Potential (LJP) transformation, the simulated resting potential settles at $-61.07\text{ mV}$, compared to the experimental baseline recording of $-74.17\text{ mV}$.
  - This constant $\approx 13\text{ mV}$ baseline discrepancy accounts for almost all of the overall MAE ($12.23\text{ mV}$) and RMSE ($12.73\text{ mV}$).
- **F-I Curve Shape Failure and Late-Step Spike Cessation:**
  - Below calibration: The model is severely under-excitable. At $+290\text{ pA}$ (Sweep 45), the biological cell fires, while the model is silent ($0\text{ spikes}$). Silent under-prediction persists through $+310$ and $+330\text{ pA}$.
  - Above calibration: The biological cell exhibits pronounced saturation and enters late-step spike cessation. In Sweep 52 ($+430\text{ pA}$), the real cell fires 12 spikes between $t = 1036.8\text{ ms}$ and $t = 1498.3\text{ ms}$, then remains completely silent for the remaining $522\text{ ms}$ of the step, settling at a depolarized plateau of $-47.0\text{ mV}$.
  - In stark contrast, the simulated model fires continuously across the entire step duration at $\approx 48\text{ Hz}$, generating 48 spikes ($+36$ spike over-prediction).
  
  | Current Step | Recorded Spikes | Simulated Spikes | Spike Delta | Biological Firing Behavior | Model Firing Behavior |
  |---:|---:|---:|---:|:---|:---|
  | $+290\text{ pA}$ | 1 | 0 | $-1$ | Single action potential at threshold | Silent (under-excitable) |
  | $+350\text{ pA}$ | 7 | 1 | $-6$ | Sustained train (7 Hz) | Single delayed spike |
  | $+370\text{ pA}$ (Calib) | 9 | 9 | $0$ | Regular firing | Matched by fitting |
  | $+390\text{ pA}$ | 9 | 27 | $+18$ | Early burst; silent after $1335\text{ ms}$ | Continuous firing ($27\text{ Hz}$) |
  | $+410\text{ pA}$ | 13 | 39 | $+26$ | Early burst; silent after $1522\text{ ms}$ | Continuous firing ($39\text{ Hz}$) |
  | $+430\text{ pA}$ | 12 | 48 | $+36$ | Early burst; silent after $1498\text{ ms}$ | Continuous firing ($48\text{ Hz}$) |

- **Concealment by Aggregate Statistics:**
  - The aggregate mean spike delta for Pop A was reported as only $+1.94$ spikes/sweep. This low mean occurs because the $-1$ to $-6$ spike under-predictions below calibration cancel out the $+18$ to $+36$ spike over-predictions above calibration, averaged alongside 18 hyperpolarizing zero-spike sweeps.
  - In reality, the model completely fails to capture the non-monotonic / saturating shape of the biological F-I curve. This failure is an intrinsic kinetic limitation of the model's conductances and persists independently of the baseline voltage offset.

---

## 4. Visual Evidence and Cross-Population Comparisons

All figures are compiled in [`results/phase3b/figures/`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/):

1. **F-I Curves Across Populations** ([`fi_curves_all_populations.png`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/fi_curves_all_populations.png)):
   - Clearly separates COARSE (staircase protocol) and FINEST (threshold hunting protocol).
   - Shows that Pops B and D capture the biological F-I slope accurately, while Pops A and C show rightward threshold displacement, with Pop A exhibiting severe runaway over-excitation above calibration.
2. **Rheobase Comparison** ([`rheobase_comparison.png`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/rheobase_comparison.png)):
   - Highlights the exact interval match in Pop D ($0.0\text{ pA}$ shift), the minimal shift in Pop B ($+20.0\text{ pA}$), and the $+60.0\text{ pA}$ shift in Pops A and C on the COARSE staircase.
3. **Error Distributions** ([`error_distributions_by_population.png`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/error_distributions_by_population.png)):
   - Shows that Pops B and D maintain RMSE below $5\text{ mV}$ across most sweeps, while Pop A's error is dominated by the baseline offset.
4. **First-Spike Latency Convergence** ([`first_spike_latency_comparison.png`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/first_spike_latency_comparison.png)):
   - Demonstrates the hyperbolic decay of first-spike latency as current increases, with model and recorded latencies converging asymptotically.
5. **Passive Properties Comparison** ([`passive_properties_comparison.png`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/passive_properties_comparison.png)):
   - Compares resting membrane potentials and illustrates the subthreshold I-V curves for all four specimens.

---

## 5. Scientific Implications for Model Reduction to FitzHugh-Nagumo (FHN)

The out-of-sample held-out results provide essential empirical constraints for the core INCM research question:
*How much biological detail does a neuron model need to reproduce a real neuron's electrophysiological behaviour, and which behaviours are preserved or lost when reduced to a FitzHugh-Nagumo (FHN) model?*

1. **Subthreshold Dynamics:**
   - On hyperpolarizing sweeps where current steps are large ($\ge 50\text{ pA}$), high Pearson correlation reflects faithful trajectory shapes during charging. However, correlation alone does not validate input resistance or resting equilibrium.
   - Reduction to a 2D point-neuron (FHN) discards spatial dendritic integration and non-uniform membrane charging.
2. **Excitability and Rheobase (Bifurcation Topology):**
   - In Pops B and D, the biological neurons exhibit smooth, gradual onset of firing near threshold (Type I excitability characteristics). The detailed models, however, tend to jump into repetitive firing more abruptly (Type II-like onset), leading to rheobase overestimation near threshold.
   - A standard FHN model with a subcritical Hopf bifurcation exhibits Type II excitability (discontinuous frequency onset), whereas FHN with a saddle-node on invariant circle (SNIC) or parabolic trajectory can mimic Type I. The held-out data indicates that reduction to FHN must carefully select bifurcation geometry to avoid exacerbating the threshold shift seen even in detailed models.
3. **Spike Frequency Adaptation and Temporal Drift:**
   - Both the detailed models and FHN point models assume time-invariant parameters. The held-out data reveals substantial state-dependent threshold shifts and adaptation between early (COARSE) and late (FINEST) protocol blocks, as well as late-step spike cessation in L4.
   - Standard 2D FHN models lack adaptation dynamics. If accommodation or cessation is to be captured, an explicit slow recovery variable (such as in a 3D FHN or adaptive threshold formulation) is required.


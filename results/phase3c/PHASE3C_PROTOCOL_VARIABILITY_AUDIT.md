# PHASE 3C — PROTOCOL AND TEMPORAL VARIABILITY AUDIT

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3C — Independent Scientific Consistency Audit and Phase 3B Results Correction  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  

---

## 1. Executive Summary

This audit evaluates the experimental differences between the two long-square stimulus protocol families used in the Allen Cell Types Database:
1. `C1LSCOARSE150216` (`COARSE`): Systematic current staircase spanning negative (hyperpolarizing) to large positive (suprathreshold) steps in increments of $20\text{ pA}$. Recorded early in the session.
2. `C1LSFINEST150112` (`FINEST`): Fine-grained stimulus hunting block ($10\text{ pA}$ increments, often with 3–4 repeated sweeps at target amplitudes near threshold). Recorded later in the experimental session.

The audit directly investigates the apparent threshold and firing discrepancies between these protocol blocks in **Specimen 471129934 (Pop C, VISp L5)** and **Specimen 471786879 (Pop D, VISp L6a)**.

---

## 2. Chronological Sweep Audit

### 2.1 Specimen 471129934 (Population C, VISp Layer 5)

Chronological trajectory of sweeps spanning the firing transition:

| Sweep | Protocol | Amplitude (pA) | Recorded Spikes | Simulated Spikes | Note |
|:---:|:---:|---:|:---:|:---:|:---|
| 43 | COARSE | $+250.0$ | 0 | 0 | Subthreshold |
| 44 | COARSE | $+270.0$ | 0 | 0 | Subthreshold |
| **45** | **COARSE** | **$+290.0$** | **1** | **0** | **Recorded Rheobase in COARSE** |
| 46 | COARSE | $+310.0$ | 1 | 0 | Model silent |
| 47 | COARSE | $+330.0$ | 2 | 0 | Model silent |
| 48 | COARSE | $+350.0$ | 3 | 2 | Model onset |
| ... | ... | ... | ... | ... | ... |
| 51 | COARSE | $+410.0$ | 10 | 10 | Calibration Sweep (In-sample) |
| **53** | **FINEST** | **$+280.0$** | **0** | **0** | Recorded silent |
| **54** | **FINEST** | **$+290.0$** | **0** | **0** | **Silent at $+290\text{ pA}$ (Fired in Sweep 45!)** |
| **55** | **FINEST** | **$+310.0$** | **0** | **0** | **Silent at $+310\text{ pA}$ (Fired in Sweep 46!)** |
| **56** | **FINEST** | **$+320.0$** | **0** | **0** | Recorded silent |
| **57** | **FINEST** | **$+330.0$** | **1** | **0** | Recorded fires 1 spike (Repeated sweep 1) |
| **58** | **FINEST** | **$+330.0$** | **1** | **0** | Recorded fires 1 spike (Repeated sweep 2) |
| **59** | **FINEST** | **$+330.0$** | **1** | **0** | Recorded fires 1 spike (Repeated sweep 3) |
| **60** | **FINEST** | **$+330.0$** | **1** | **0** | Recorded fires 1 spike (Repeated sweep 4) |

#### Empirical Findings for Specimen 471129934:
1. **Biological Threshold Shift:** During the early `COARSE` staircase, the biological neuron fired at $+290\text{ pA}$ (Sweep 45) and $+310\text{ pA}$ (Sweep 46). Later in the session during the `FINEST` block, the neuron was completely silent at $+280, +290, +310,$ and $+320\text{ pA}$, requiring $+330\text{ pA}$ to initiate an action potential. The biological rheobase shifted rightward by $\approx +40\text{ pA}$.
2. **High Repeatability within Block:** Within the `FINEST` block, all four repeated sweeps at $+330\text{ pA}$ (sweeps 57, 58, 59, 60) produced exactly 1 spike, demonstrating high within-block consistency.
3. **Data Pooling Consequence:** If sweeps from `COARSE` and `FINEST` are pooled without separating protocol families, the apparent "maximum subthreshold amplitude" is $+320\text{ pA}$ (from Sweep 56), while the "minimum suprathreshold amplitude" is $+290\text{ pA}$ (from Sweep 45). This inverted interval $[320, 290]\text{ pA}$ is a methodological artifact of pooling non-stationary recording blocks.

---

### 2.2 Specimen 471786879 (Population D, VISp Layer 6a)

Chronological trajectory of sweeps spanning the firing transition:

| Sweep | Protocol | Amplitude (pA) | Recorded Spikes | Simulated Spikes | Note |
|:---:|:---:|---:|:---:|:---:|:---|
| 39 | COARSE | $+190.0$ | 0 | 0 | Subthreshold |
| 40 | COARSE | $+210.0$ | 5 | 1 | Transition |
| 41 | COARSE | $+230.0$ | 10 | 9 | Close match |
| 42 | COARSE | $+250.0$ | 14 | 14 | Calibration Sweep (In-sample) |
| 43 | COARSE | $+270.0$ | 17 | 18 | Close match |
| 47 | COARSE | $+350.0$ | 27 | 29 | Close match |
| ... | ... | ... | ... | ... | ... |
| **52** | **FINEST** | **$+240.0$** | **1** | **11** | Biological cell fires only 1 spike |
| **53** | **FINEST** | **$+240.0$** | **1** | **11** | Biological cell fires only 1 spike |
| **54** | **FINEST** | **$+240.0$** | **1** | **11** | Biological cell fires only 1 spike |

#### Empirical Findings for Specimen 471786879:
1. **Dramatic Excitability Shift in Biological Cell:** In early `COARSE` sweeps, $+230\text{ pA}$ elicited 10 spikes and $+250\text{ pA}$ elicited 14 spikes. In late `FINEST` sweeps, an intermediate current of $+240\text{ pA}$ elicited only 1 spike consistently across all 3 repetitions (sweeps 52, 53, 54).
2. **Model Stationarity:** The conductance-based NEURON model has time-invariant parameters and resets to resting potential before each run. At $+240\text{ pA}$, it predicts 11 spikes, exactly interpolating its $+230\text{ pA}$ (9 spikes) and $+250\text{ pA}$ (14 spikes) responses.

---

## 3. Scientific Conclusions and Boundary Conditions

### 3.1 What Can Be Scientifically Concluded:
- **Temporal Non-Stationarity is Observable:** Real neurons in whole-cell patch-clamp configurations exhibit non-stationary excitability across an experiment. Excitability decreased over time in both specimens.
- **Protocol Families Must Not Be Pooled:** `COARSE` and `FINEST` protocols cannot be combined into a single rheobase estimate. `COARSE` sweeps represent a monotonic, unbiased staircase, whereas `FINEST` reflects a later experimental state.
- **Time-Invariant Models Cannot Capture State-Dependent Hysteresis:** Deterministic conductance-based models without dynamic slow variables (such as slow ion accumulation, pump dynamics, or metabolic modulation) cannot reproduce inter-sweep threshold shifts.

### 3.2 What Cannot Be Concluded (Unsupported Claims Removed):
- **Specific Biochemical Mechanisms:** Current-clamp somatic recordings do not permit attributing the threshold shift to specific biological causes such as "washout of intracellular second messengers", "metabolic run-down", "calcium-activated potassium current accumulation", or "pipette series resistance degradation". These hypotheses are plausible but unverified by independent measurements.
- In all reports, this phenomenon must be described strictly as **phenomenological temporal non-stationarity / between-protocol threshold drift**, avoiding unverified mechanistic claims.

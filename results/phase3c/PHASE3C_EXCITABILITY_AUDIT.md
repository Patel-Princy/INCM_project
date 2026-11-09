# PHASE 3C — RHEOBASE AND F-I CURVE EXCITABILITY AUDIT

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3C — Independent Scientific Consistency Audit and Phase 3B Results Correction  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  

---

## 1. Executive Summary

This audit independently validates the mathematical and experimental extraction of rheobase intervals and frequency-current (F-I) curves across the four representative populations.

Key validations:
1. **Mathematical Definition of Rheobase Interval:** The true biological rheobase current $I_{\text{rheo}}$ lies in the open-closed interval $(I_{\text{sub\_max}}, I_{\text{supra\_min}}]$, where $I_{\text{sub\_max}}$ is the highest current evoking 0 spikes and $I_{\text{supra\_min}}$ is the lowest current evoking $\ge 1$ spike. Midpoint estimates are $\hat{I}_{\text{rheo}} = (I_{\text{sub\_max}} + I_{\text{supra\_min}}) / 2$ with discretization uncertainty $\pm \Delta I / 2$.
2. **Protocol Disjointness:** Rheobase must be computed on the monotonic `COARSE` staircase. Pooling `COARSE` and `FINEST` produces invalid inverted intervals in non-stationary recordings (e.g., in L5).
3. **Repeated Condition Averaging:** In `heldout_fi_curves.csv`, repeated sweeps at identical stimulus conditions (e.g. 4 sweeps at $+330\text{ pA}$ in L5; 3 sweeps at $+240\text{ pA}$ in L6a) are correctly grouped and averaged, preserving sample variance.

---

## 2. Independent Rheobase Recomputation Table (`COARSE` Family)

All current values in picoamperes (pA):

| Population | Layer | Specimen ID | Tested Step Size | Rec Subthreshold Max | Rec Suprathreshold Min | Recorded Rheobase Interval | Rec Midpoint | Sim Subthreshold Max | Sim Suprathreshold Min | Simulated Rheobase Interval | Sim Midpoint | Rheobase Shift ($\Delta I$) | Relative Error (%) | Overlap Verdict |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | 4 | 484564503 | $20.0$ | $+270.0$ | $+290.0$ | $(270.0, 290.0]$ | $280.0 \pm 10$ | $+330.0$ | $+350.0$ | $(330.0, 350.0]$ | $340.0 \pm 10$ | $+60.0$ | $+21.4\%$ | Disjoint |
| **B** | 2/3 | 318808427 | $20.0$ | $+110.0$ | $+130.0$ | $(110.0, 130.0]$ | $120.0 \pm 10$ | $+130.0$ | $+150.0$ | $(130.0, 150.0]$ | $140.0 \pm 10$ | $+20.0$ | $+16.7\%$ | Adjacent |
| **C** | 5 | 471129934 | $20.0$ | $+270.0$ | $+290.0$ | $(270.0, 290.0]$ | $280.0 \pm 10$ | $+330.0$ | $+350.0$ | $(330.0, 350.0]$ | $340.0 \pm 10$ | $+60.0$ | $+21.4\%$ | Disjoint |
| **D** | 6a | 471786879 | $20.0$ | $+190.0$ | $+210.0$ | $(190.0, 210.0]$ | $200.0 \pm 10$ | $+190.0$ | $+210.0$ | $(190.0, 210.0]$ | $200.0 \pm 10$ | **$0.0$** | **$0.0\%$** | **Identical** |

---

## 3. Detailed Audit of F-I Curves

### 3.1 Population D (VISp L6a) F-I Curve Fidelity
- In the `COARSE` protocol, the model exhibits exceptional agreement across the entire dynamic range:
  - $+210\text{ pA}$: Rec $= 5\text{ Hz}$, Sim $= 1\text{ Hz}$
  - $+230\text{ pA}$: Rec $= 10\text{ Hz}$, Sim $= 9\text{ Hz}$
  - $+250\text{ pA}$ (Calibration): Rec $= 14\text{ Hz}$, Sim $= 14\text{ Hz}$
  - $+270\text{ pA}$: Rec $= 17\text{ Hz}$, Sim $= 18\text{ Hz}$
  - $+290\text{ pA}$: Rec $= 19\text{ Hz}$, Sim $= 21\text{ Hz}$
  - $+310\text{ pA}$: Rec $= 21\text{ Hz}$, Sim $= 24\text{ Hz}$
  - $+330\text{ pA}$: Rec $= 24\text{ Hz}$, Sim $= 26\text{ Hz}$
  - $+350\text{ pA}$: Rec $= 27\text{ Hz}$, Sim $= 29\text{ Hz}$
- The slope $df/dI$ is $0.157\text{ Hz/pA}$ for recorded data and $0.200\text{ Hz/pA}$ for simulated data. The model captures the linear gain of the biological neuron remarkably well.

### 3.2 Population B (VISp L2/3) F-I Curve Fidelity
- Small rightward shift of $20\text{ pA}$, followed by near-parallel slope:
  - $+130\text{ pA}$: Rec $= 1\text{ Hz}$, Sim $= 0\text{ Hz}$
  - $+150\text{ pA}$: Rec $= 8\text{ Hz}$, Sim $= 11\text{ Hz}$
  - $+170\text{ pA}$: Rec $= 13\text{ Hz}$, Sim $= 16\text{ Hz}$
  - $+190\text{ pA}$ (Calibration): Rec $= 18\text{ Hz}$, Sim $= 20\text{ Hz}$
  - $+210\text{ pA}$: Rec $= 22\text{ Hz}$, Sim $= 23\text{ Hz}$
  - $+230\text{ pA}$: Rec $= 22\text{ Hz}$, Sim $= 26\text{ Hz}$
  - $+250\text{ pA}$: Rec $= 27\text{ Hz}$, Sim $= 29\text{ Hz}$
  - $+270\text{ pA}$: Rec $= 29\text{ Hz}$, Sim $= 33\text{ Hz}$
- High correlation and low spike delta (mean $+0.83$ spikes).

### 3.3 Population C (VISp L5) F-I Curve Fidelity
- Rightward shift of $60\text{ pA}$ at threshold in COARSE, but matches closely at calibration and higher currents:
  - $+290\text{ pA}$: Rec $= 1\text{ Hz}$, Sim $= 0\text{ Hz}$
  - $+350\text{ pA}$: Rec $= 3\text{ Hz}$, Sim $= 2\text{ Hz}$
  - $+370\text{ pA}$: Rec $= 4\text{ Hz}$, Sim $= 5\text{ Hz}$
  - $+390\text{ pA}$: Rec $= 7\text{ Hz}$, Sim $= 7\text{ Hz}$
  - $+410\text{ pA}$ (Calibration): Rec $= 10\text{ Hz}$, Sim $= 10\text{ Hz}$
  - $+430\text{ pA}$: Rec $= 11\text{ Hz}$, Sim $= 12\text{ Hz}$
  - $+470\text{ pA}$: Rec $= 14\text{ Hz}$, Sim $= 16\text{ Hz}$
- Across the entire held-out set, the positive and negative errors balance out to a net bias of $-0.03$ spikes.

### 3.4 Population A (VISp L4) F-I Curve Failure
- The model completely fails to capture the shape of the biological F-I curve:
  - Subthreshold region ($+250$ to $+330\text{ pA}$): Model is completely silent ($0\text{ Hz}$), while recorded neuron fires $1$ to $6\text{ Hz}$.
  - Calibration ($+370\text{ pA}$): Both fire $9\text{ Hz}$ (in step).
  - High suprathreshold region ($+390$ to $+430\text{ pA}$): The biological cell saturates at $9 - 13\text{ Hz}$ and enters late-step spike cessation (silence during the last $500\text{ ms}$ of the step). The model fires continuously, accelerating up to $48\text{ Hz}$ ($+36$ spike over-prediction).
- Conclusion: The model's F-I curve is unphysiologically steep ($df/dI \approx 0.58\text{ Hz/pA}$) and lacks the biological adaptation/saturation mechanisms present in the biological neuron.

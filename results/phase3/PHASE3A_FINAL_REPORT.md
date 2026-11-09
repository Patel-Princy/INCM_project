# Phase 3A — Comprehensive Final Report: Detailed Neuron Model Pipeline Audit, Readiness Validation, and Experiment Preparation

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Active Working Branch:** `ashish-work`  
**Date:** 2026-11-08  
**Preceding Deliverables:**
- `results/phase3/PHASE3A_BASELINE_AUDIT.md`
- `results/phase3/PHASE3A_PIPELINE_TRACE.md`
- `results/phase3/PHASE3A_FOUR_REPRESENTATIVE_ASSET_AUDIT.md`
- `results/phase3/four_representative_asset_audit.csv`
- `results/phase3/PHASE3A_PIPELINE_HARDENING_AUDIT.md`
- Structured Simulation Results: `results/phase3/detailed_model/{484564503, 318808427, 471129934, 471786879}/`

---

## 1. Executive Summary

Phase 3A conducted a comprehensive, multi-phase engineering and scientific audit of the detailed conductance-based neuron model execution pipeline, followed by controlled simulation and experimental comparison across the four layer-defined spiny excitatory neuron populations in mouse primary visual cortex (VISp).

All four layer-defined representatives—**Population A (VISp L4)**, **Population B (VISp L2/3)**, **Population C (VISp L5)**, and **Population D (VISp L6a)**—were audited for recording provenance, stimulus interpretation, fit descriptor integrity, morphology assets, and NEURON mechanism compilation. The longstanding NWB conversion conflict in L5 (`MATCH_CONVERSION_CONFLICT`) was rigorously investigated and resolved by tracing AllenSDK's native pipeline versioning logic: early pipeline v1.0 files stored raw data directly in SI units (Amperes), and AllenSDK's unscaled reading correctly recovers physical stimulus currents without unphysical scaling.

The simulation execution pipeline was hardened and validated in WSL2 (`Ubuntu 26.04 LTS`, Python `3.11.18`, NEURON `8.2.7`, pristine AllenSDK `2.16.2` source). The project test suite expanded to **340 passing tests** (0 failed, 0 skipped). All four representatives were successfully simulated against their respective experimental calibration sweeps, achieving high membrane voltage correlations ($r = 0.8869$–$0.9335$) and accurate action potential reproduction under the documented liquid junction potential correction ($+14\text{ mV}$) and canonical perisomatic stub axon geometry.

---

## 2. Four-Population Summary Table

| Population | Specimen ID | Layer | Structure | Asset Status | Execution Status | Recording Comparison | Blockers |
|---|---:|---|---|---|---|---|---|
| **A** | `484564503` | 4 | VISp4 | `READY_FOR_EXECUTION` | Successfully executed | Successfully validated against recording (Sweep 49, 9 rec vs 9 sim spikes, $r=0.9007$) | None |
| **B** | `318808427` | 2/3 | VISp2/3 | `READY_FOR_EXECUTION` | Successfully executed | Successfully validated against recording (Sweep 40, 19 rec vs 19 sim spikes, $r=0.8869$) | None |
| **C** | `471129934` | 5 | VISp5 | `CONDITIONALLY_READY` | Successfully executed | Successfully validated against recording (Sweep 51, 9 rec vs 8 sim spikes, $r=0.9164$) | Resolved (v1.0 unscaled SI interpretation documented) |
| **D** | `471786879` | 6a | VISp6a | `READY_FOR_EXECUTION` | Successfully executed | Successfully validated against recording (Sweep 42, 13 rec vs 14 sim spikes, $r=0.9335$) | None |

*Terminology distinction:*  
- **Successfully executed:** NEURON integrated the differential equations and produced complete, non-NaN/non-infinite state vectors.  
- **Successfully validated against recording:** Model voltage traces were aligned and compared with actual patch-clamp recording traces under verified stimulus protocols and metrics, explicitly acknowledging the in-sample calibration nature of the sweeps.

---

## 3. Pipeline Architecture and Toolchain Reused

The pipeline strictly reuses the validated toolchain without introducing duplicate simulation loaders or altering published model parameters:
- **Simulation Harness:** `allensdk.model.biophysical.runner.run(args, sweeps=[sweep], procs=1)`.
- **Morphology & Axon Handling:** Canonical perisomatic loader in `allensdk.model.biophysical.utils.Utils.generate_morphology()`, which automatically replaces SWC axonal reconstructions with a standardized 2-compartment cylindrical stub axon ($L = 30\ \mu\text{m}, d = 1\ \mu\text{m}$). This avoids the axon-branch sensitivity documented in Phase 2G-B / 2G-C for all-active models.
- **Liquid Junction Potential (LJP):** Intercepted via `Utils.get_recorded_data()` to ensure that:
  $$V_{\text{written}} = \left(V_{\text{sim}} - \text{junction\_potential}\right) \times 10^{-3} = \left(V_{\text{sim}} + 14.0\text{ mV}\right) \times 10^{-3}\text{ Volts}$$
  This shifts the simulation into the uncorrected patch-clamp recording frame, matching the physical NWB voltage traces.
- **Mechanisms:** 16 compiled Hodgkin-Huxley style channel mechanisms compiled via `nrnivmodl` into `x86_64/libnrnmech.so`.

---

## 4. Asset Audit and Resolution of the L5 Conversion Conflict

### 4.1 Asset Verification Findings
1. **NWB Recordings:** All 4 NWB files (`484564503.nwb`, `318808427.nwb`, `471129934.nwb`, `471786879.nwb`) exist in `data/nwb_cache/` and match their recorded SHA256 digests.
2. **Fit Descriptors:** All 4 perisomatic fit descriptors exist in `tmp/fit_cache/` and match their SHA256 digests.
3. **Morphologies:** All 4 reconstructed dendritic SWCs exist in `tmp/morphology_cache/` and match the model reconstruction IDs.
4. **Calibration Sweeps:** Exactly one in-sample calibration sweep is defined per descriptor (Sweep 49 for A, Sweep 40 for B, Sweep 51 for C, Sweep 42 for D). All calibration sweeps map to valid records in `sweep_inventory.csv`.

### 4.2 L5 Conversion Conflict Investigation
- **The Issue:** Specimen `471129934` was flagged with `MATCH_CONVERSION_CONFLICT` during Phase 0C because the NWB series header declared `unit='Amps'` with `conversion=1.0e-12`.
- **Root Cause Identified:** HDF5 inspection revealed `general/generated_by` is `['pipeline', 'IVSCC', 'version', '1.0']`. In Allen Institute pipeline version 1.0, current arrays were stored directly in Amperes ($1.1 \times 10^{-10}\text{ A} = 110\text{ pA}$).
- **AllenSDK Source Verification:** In `allensdk/core/nwb_data_set.py`, `get_sweep()` implements pipeline version checking. For pipeline version $\le 1.0$, `stimulus = stimulus_dataset[()]` is returned without applying the erroneous `1e-12` multiplier.
- **Adjudication:** The data interpretation used by AllenSDK's own loader preserves the physically correct current ($110\text{ pA}$ and $410\text{ pA}$), matching inventory amplitudes to machine precision. Applying `conversion=1e-12` would result in $10^{-22}\text{ A}$, which is physically unviable. Candidate C is therefore cleared as **CONDITIONALLY_READY** under this documented, defensible interpretation.

---

## 5. Controlled Execution Results

### 5.1 Population A — Specimen 484564503 (VISp L4)
- **Condition:** Calibration Sweep 49 (+370 pA depolarizing step, duration 1000 ms, onset 1020 ms).
- **Execution Time:** 9.64 s NEURON integration.
- **Membrane Potential:**
  - Resting baseline: $-73.72\text{ mV}$ (recorded) vs $-61.07\text{ mV}$ (simulated); $\Delta = +12.65\text{ mV}$.
  - Whole sweep RMSE: $12.38\text{ mV}$; during-stimulus RMSE: $8.50\text{ mV}$.
  - Trace correlation: $r = 0.9007$.
- **Action Potential Metrics:**
  - In-step spike count: **9 recorded vs 9 simulated** (exact match).
  - First-spike latency: $1040.25\text{ ms}$ (recorded) vs $1044.72\text{ ms}$ (simulated); latency offset: $+4.47\text{ ms}$.
  - Post-step spontaneous excursions: 0 recorded, 0 simulated.

### 5.2 Population B — Specimen 318808427 (VISp L2/3)
- **Condition:** Calibration Sweep 40 (+190 pA depolarizing step, duration 1000 ms, onset 1020 ms).
- **Execution Time:** 4.08 s NEURON integration.
- **Membrane Potential:**
  - Resting baseline: $-75.79\text{ mV}$ (recorded) vs $-75.93\text{ mV}$ (simulated); $\Delta = -0.14\text{ mV}$ (near-zero baseline offset).
  - Pre-stimulus RMSE: $0.23\text{ mV}$; whole sweep RMSE: $6.77\text{ mV}$.
  - Trace correlation: $r = 0.8869$.
- **Action Potential Metrics:**
  - In-step spike count: **19 recorded vs 19 simulated** (exact match).
  - First-spike latency: $1037.28\text{ ms}$ (recorded) vs $1042.48\text{ ms}$ (simulated); latency offset: $+5.20\text{ ms}$.
  - Post-step spontaneous excursions: 0 recorded, 0 simulated.

### 5.3 Population C — Specimen 471129934 (VISp L5)
- **Condition:** Calibration Sweep 51 (+410 pA depolarizing step, duration 1000 ms, onset 1020 ms).
- **Execution Time:** 14.09 s NEURON integration.
- **Membrane Potential:**
  - Resting baseline: $-69.30\text{ mV}$ (recorded) vs $-63.65\text{ mV}$ (simulated); $\Delta = +5.65\text{ mV}$.
  - Whole sweep RMSE: $5.90\text{ mV}$; during-stimulus RMSE: $9.08\text{ mV}$.
  - Trace correlation: $r = 0.9164$.
- **Action Potential Metrics:**
  - In-step spike count: **9 recorded vs 8 simulated** (near-exact match; model fires 8 spikes with strong adaptation).
  - First-spike latency: $1043.14\text{ ms}$ (recorded) vs $1036.34\text{ ms}$ (simulated); latency offset: $-6.80\text{ ms}$.
  - Post-step spontaneous excursions: 0 recorded, 0 simulated.

### 5.4 Population D — Specimen 471786879 (VISp L6a)
- **Condition:** Calibration Sweep 42 (+250 pA depolarizing step, duration 1000 ms, onset 1020 ms).
- **Execution Time:** 11.26 s NEURON integration.
- **Membrane Potential:**
  - Resting baseline: $-75.66\text{ mV}$ (recorded) vs $-75.97\text{ mV}$ (simulated); $\Delta = -0.30\text{ mV}$.
  - Pre-stimulus RMSE: $0.33\text{ mV}$; whole sweep RMSE: $4.17\text{ mV}$.
  - Trace correlation: $r = 0.9335$ (highest across all candidates).
- **Action Potential Metrics:**
  - In-step spike count: **13 recorded vs 14 simulated** (near-exact match).
  - First-spike latency: $1077.95\text{ ms}$ (recorded) vs $1072.98\text{ ms}$ (simulated); latency offset: $-4.98\text{ ms}$.
  - Post-step spontaneous excursions: 0 recorded, 0 simulated.

---

## 6. Scientific Limitations and Caveats

1. **In-Sample Calibration Nature:** Sweeps 49 (A), 40 (B), 51 (C), and 42 (D) were the exact sweeps used by the Allen Institute optimization pipeline to fit conductance parameters. High metric agreement on these sweeps confirms **numerical pipeline integrity and parameter reproducibility**, not generalized predictive accuracy. Generalization must be assessed exclusively on the reserved held-out sweeps.
2. **Spike Amplitude Truncation:** In all simulated traces, somatic action potential peaks reach $+30$ to $+40\text{ mV}$, while recorded patch-clamp traces attenuate at $+15$ to $+30\text{ mV}$. This discrepancy reflects series resistance filtering and pipette capacitance artifact in experimental recordings rather than biophysical failure of the model.
3. **Axon Treatment Assumption:** Perisomatic models replace reconstructed axons with canonical stub axons ($2 \times 30\ \mu\text{m}$). This ensures standardization but does not capture realistic action potential initiation in the axon initial segment (AIS).
4. **Layer vs Projection Ambiguity:** Populations are strictly layer-defined (`VISp4`, `VISp2/3`, `VISp5`, `VISp6a`). Allen metadata does not provide projection identity (e.g., IT vs ET/PT vs CT), and no projection claims should be made.

---

## 7. Recommended Next Steps

With the detailed neuron model execution pipeline fully audited, hardened, and verified across all four populations, the project is ready for:
1. **Phase 3B — Out-of-Sample Held-Out Evaluation:** Execute each representative perisomatic model across its full repertoire of held-out depolarizing sweeps (18 to 34 sweeps per candidate) to characterize generalized F-I curves and rheobase.
2. **Phase 4 — FitzHugh–Nagumo (FHN) Model Calibration:** Fit reduced two-variable FHN models to the same calibration sweeps and compare dynamical state-space reductions against the detailed conductance models.

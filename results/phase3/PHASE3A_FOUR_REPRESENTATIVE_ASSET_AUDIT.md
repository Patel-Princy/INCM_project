# Phase 3A — Four-Representative Asset and Readiness Audit

**Date:** 2026-11-08  
**Repository:** `Patel-Princy/INCM_project`  
**Active Working Branch:** `ashish-work`  
**Target Populations:** Four layer-defined spiny excitatory populations in mouse primary visual cortex (VISp)  

---

## 1. Executive Summary

This audit validates all assets required to execute and evaluate detailed perisomatic biophysical models for the four representative VISp excitatory neurons:
- **Population A (VISp L4):** Specimen `484564503` — **READY_FOR_EXECUTION**
- **Population B (VISp L2/3):** Specimen `318808427` — **READY_FOR_EXECUTION**
- **Population C (VISp L5):** Specimen `471129934` — **CONDITIONALLY_READY** (resolved conversion conflict)
- **Population D (VISp L6a):** Specimen `471786879` — **READY_FOR_EXECUTION**

All four specimens have locally cached, verified NWB recordings, downloaded and parsed perisomatic fit descriptors, verified morphology SWC files matching specimen reconstructions, and 16 compiled NEURON mechanism sources.

---

## 2. Four-Representative Summary Table

| Attribute | Pop A (L4) | Pop B (L2/3) | Pop C (L5) | Pop D (L6a) |
|---|---|---|---|---|
| **Specimen ID** | `484564503` | `318808427` | `471129934` | `471786879` |
| **Structure** | `VISp4` | `VISp2/3` | `VISp5` | `VISp6a` |
| **Driver Line** | `Rorb-IRES2-Cre` | `Nr5a1-Cre` | `Rbp4-Cre_KL100` | `Ntsr1-Cre_GN220` |
| **Dendrite Type** | Spiny (intact) | Spiny (intact) | Spiny (intact) | Spiny (intact) |
| **Model ID** | `485591776` | `473863035` | `480624414` | `480632594` |
| **Fit File ID** | `497237137` | `497237588` | `497236153` | `497236229` |
| **Fit SHA-256** | `9495fe52...` | `6f0bb851...` | `24a34d42...` | `7af2a180...` |
| **NWB File ID** | `491317441` | `491199000` | `491202812` | `491202180` |
| **NWB SHA-256** | `e00a3f34...` | `c3165dba...` | `ecab60d2...` | `9a35a451...` |
| **NWB Size (bytes)** | 95,812,210 | 50,432,181 | 117,131,886 | 69,144,821 |
| **NWB Status** | `MATCH` | `MATCH` | `MATCH_CONVERSION_CONFLICT` | `MATCH` |
| **Sampling Rate (Hz)**| 200,000 | 200,000 | 200,000 | 200,000 |
| **Reconstruction ID**| `491459182` | `491119754` | `495335491` | `495335607` |
| **SWC SHA-256** | `6824f347...` | `d164756e...` | `a810d5ae...` | `1fecdb3d...` |
| **SWC Size (bytes)** | 104,346 | 66,139 | 185,694 | 142,187 |
| **Fitting Sweep** | Sweep 49 (+370 pA)| Sweep 40 (+190 pA)| Sweep 51 (+410 pA)| Sweep 42 (+250 pA)|
| **Fitting Mapped?** | YES (Sweep 49) | YES (Sweep 40) | YES (Sweep 51) | YES (Sweep 42) |
| **Held-Out Sweeps** | 31 sweeps | 18 sweeps | 34 sweeps | 26 sweeps |
| **Asset Verdict** | **READY** | **READY** | **CONDITIONALLY_READY** | **READY** |

---

## 3. Deep Dive: Specimen-Specific Audits

### 3.1 Population A — Specimen 484564503 (VISp L4)
- **Cell Identity:** Primary visual cortex Layer 4 spiny excitatory neuron. Driver line `Rorb-IRES2-Cre` is enriched in L4 excitatory neurons (spiny stellate vs star pyramidal distinction unresolved by metadata). Projection target unmeasured.
- **NWB Integrity:** File `data/nwb_cache/484564503.nwb` (95,812,210 bytes, SHA256 `e00a3f34...`). All 32 long-square sweeps match inventory amplitudes under declared units. Plateau onset: 1.02 s; step duration: 1000 ms.
- **Fitting vs Evaluation Split:** Fit descriptor `497237137.json` explicitly names Sweep 49 (+370 pA). Sweep 49 maps to `sweep_inventory.csv` for 484564503. 31 remaining sweeps are available for independent held-out evaluation (25 depolarizing, 22 distinct amplitudes).
- **Morphology:** Reconstructed dendritic tree `491459182.swc` (104,346 bytes) matches the model reconstruction specification. Canonical perisomatic stub axon ($2 \times 30\ \mu\text{m}$) applied by AllenSDK.
- **Verdict:** **READY_FOR_EXECUTION**.

---

### 3.2 Population B — Specimen 318808427 (VISp L2/3)
- **Cell Identity:** Primary visual cortex Layer 2/3 spiny excitatory neuron. Driver line `Nr5a1-Cre`. Projection class unmeasured.
- **NWB Integrity:** File `data/nwb_cache/318808427.nwb` (50,432,181 bytes, SHA256 `c3165dba...`). 19 long-square sweeps match inventory amplitudes. Step onset: 1.02 s; duration: 1000 ms.
- **Fitting vs Evaluation Split:** Fit descriptor `497237588.json` designates Sweep 40 (+190 pA). Sweep 40 is verified in the specimen inventory. 18 long-square sweeps reserved as held-out evaluation conditions (14 depolarizing, 13 distinct amplitudes).
- **Morphology:** Reconstruction `491119754.swc` (66,139 bytes) matches specimen and model specifications.
- **Verdict:** **READY_FOR_EXECUTION**.

---

### 3.3 Population C — Specimen 471129934 (VISp L5): Conversion Conflict Investigation
- **Cell Identity:** Layer 5 spiny excitatory neuron. Driver line `Rbp4-Cre_KL100` (corticostriatal / pyramidal tract compatible; projection target unmeasured).
- **NWB Integrity and Conversion Conflict Audit:**
  - NWB file: `data/nwb_cache/471129934.nwb` (117,131,886 bytes, SHA256 `ecab60d2...`).
  - Metadata in HDF5:
    - `general/generated_by`: `['pipeline', 'IVSCC', 'version', '1.0']`
    - `stimulus/timeseries/data.attrs['unit']`: `Amps`
    - `stimulus/timeseries/data.attrs['conversion']`: `1.0e-12`
  - Raw array values: For Sweep 36, maximum current is $1.1 \times 10^{-10}$. For fitting Sweep 51, maximum current is $4.1 \times 10^{-10}$.
  - Contradiction: If `conversion=1e-12` were applied, $1.1 \times 10^{-10} \times 1e-12 = 1.1 \times 10^{-22}\text{ A}$, which is unphysical. If raw data is read unscaled ($1.0$), $1.1 \times 10^{-10}\text{ A} = 110\text{ pA}$, which matches the Allen sweep inventory amplitude ($110.0\text{ pA}$) exactly.
  - AllenSDK Toolchain Verification:
    In `allensdk.core.nwb_data_set.NwbDataSet.get_sweep()`:
    ```python
    major, minor = self.get_pipeline_version()
    if (major == 1 and minor > 0) or major > 1:
        stimulus = stimulus_dataset[()] * conversion
    else:  # old file version (pipeline <= 1.0)
        stimulus = stimulus_dataset[()]
    ```
    AllenSDK's own reader natively checks pipeline version: early pipeline version 1.0 files **do not apply conversion**; they return unscaled raw values ($1.0 \times \text{data}$).
  - Scientific Adjudication: The raw data arrays in `471129934.nwb` were written directly in SI units (Amperes) by the Allen pipeline v1.0, while an erroneous `conversion=1e-12` attribute was attached. AllenSDK's native unscaled reader preserves the correct physical current ($110\text{ pA}$, $410\text{ pA}$).
  - Policy: Candidate is valid and executable under AllenSDK's documented unscaled pipeline reading convention.
- **Fitting vs Evaluation Split:** Fit descriptor `497236153.json` designates Sweep 51 (+410 pA). 34 long-square sweeps reserved as held-out evaluation conditions (29 depolarizing, 23 distinct amplitudes).
- **Morphology:** Reconstruction `495335491.swc` (185,694 bytes) matches model reconstruction specification.
- **Verdict:** **CONDITIONALLY_READY** (fully verified under documented unscaled SI interpretation).

---

### 3.4 Population D — Specimen 471786879 (VISp L6a)
- **Cell Identity:** Layer 6a spiny excitatory neuron. Driver line `Ntsr1-Cre_GN220` (corticothalamic-compatible line; projection target unmeasured).
- **NWB Integrity:** File `data/nwb_cache/471786879.nwb` (69,144,821 bytes, SHA256 `9a35a451...`). 27 long-square sweeps match inventory amplitudes under declared units.
- **Fitting vs Evaluation Split:** Fit descriptor `497236229.json` designates Sweep 42 (+250 pA). Sweep 42 is verified in `sweep_inventory.csv`. 26 long-square sweeps available for held-out evaluation (20 depolarizing, 18 distinct amplitudes).
- **Morphology:** Reconstruction `495335607.swc` (142,187 bytes) matches specimen reconstruction.
- **Verdict:** **READY_FOR_EXECUTION**.

---

## 4. Phase 2 Audit Gate Evaluation

| Audit Gate Condition | Requirement | Status |
|---|---|---|
| **Defensible Recording Identity** | NWB files verified with SHA256 against Phase 0/0C records | **PASS** (4/4 verified) |
| **Verified Stimulus Interpretation** | Current units verified; L5 conversion conflict adjudicated | **PASS** (4/4 verified) |
| **Compatible Model Configuration** | All 4 fit descriptors parsed; perisomatic schema verified | **PASS** (4/4 verified) |
| **Morphology & Mechanisms Available** | All 4 SWC files present; 16 .mod files compile | **PASS** (4/4 verified) |
| **Fitting-Sweep Exclusion Policy** | Fitting sweeps identified: A:49, B:40, C:51, D:42; reserved for calibration only | **PASS** (4/4 verified) |

**Phase 2 Audit Gate Verdict:** **PASS — ALL FOUR REPRESENTATIVES APPROVED FOR SIMULATION PIPELINE HARDENING AND EXECUTION**.

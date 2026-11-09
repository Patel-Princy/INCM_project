# Phase 3B — Fitting and Held-Out Sweep Provenance Audit

**Date:** 2026-11-08  
**Repository:** `Patel-Princy/INCM_project`  
**Active Working Branch:** `ashish-work`  
**Focus:** Derivation, verification, and provenance mapping of calibration fitting sweeps vs independent held-out evaluation sweeps across the four layer-defined VISp excitatory populations.

---

## 1. Executive Summary

A comprehensive provenance audit was conducted on all long-square electrophysiology recordings for the four representative spiny excitatory neurons in mouse primary visual cortex (VISp). Every fitting sweep was verified directly against the published Allen Institute perisomatic fit descriptors (`tmp/fit_cache/*.json`) and the committed sweep inventory (`data/metadata/sweep_inventory.csv`).

Exactly one calibration fitting sweep per representative was identified in the descriptor metadata:
- **Population A (VISp L4, 484564503):** Sweep `49` (+370 pA, `C1LSCOARSE150216[24]`)
- **Population B (VISp L2/3, 318808427):** Sweep `40` (+190 pA, `C1LSCOARSE141203[15]`)
- **Population C (VISp L5, 471129934):** Sweep `51` (+410 pA, `C1LSCOARSE150216[26]`)
- **Population D (VISp L6a, 471786879):** Sweep `42` (+250 pA, `C1LSCOARSE150216[18]`)

Across the four specimens, **109 valid held-out sweeps** were independently verified across **102 unique stimulus conditions**, spanning both `COARSE` and `FINEST` long-square current-clamp protocol families.

---

## 2. Sweep Inventory and Classification Breakdown

| Population | Specimen ID | Layer | Total Sweeps in Inventory | Long-Square Sweeps | Fitting Sweeps | Candidate Held-Out Sweeps | Unique Held-Out Conditions | Protocol Families |
|---|---:|---|---:|---:|---:|---:|---:|---|
| **A** | `484564503` | 4 | 81 | 32 | 1 (Swp 49) | **31** | 29 | COARSE (27), FINEST (4) |
| **B** | `318808427` | 2/3 | 88 | 19 | 1 (Swp 40) | **18** | 18 | COARSE (17), FINEST (1) |
| **C** | `471129934` | 5 | 147 | 35 | 1 (Swp 51) | **34** | 29 | COARSE (26), FINEST (8) |
| **D** | `471786879` | 6a | 61 | 27 | 1 (Swp 42) | **26** | 24 | COARSE (23), FINEST (3) |
| **Total** | | | **377** | **113** | **4** | **109** | **102** | |

---

## 3. Fit Descriptor Mapping and Provenance Rules

### 3.1 Fit Descriptor Scrutiny
In all four cases, the perisomatic model fit descriptor contains a single `fitting` block:
```json
"fitting": [
  {
    "junction_potential": -14.0,
    "sweeps": [ <sweep_id> ]
  }
]
```
The descriptor specifically targets individual sweep numbers, not sweep groups or entire protocol blocks:
1. **Specimen 484564503 (Model 485591776, Fit 497237137):** Fitting sweep is `[49]`.
2. **Specimen 318808427 (Model 473863035, Fit 497237588):** Fitting sweep is `[40]`.
3. **Specimen 471129934 (Model 480624414, Fit 497236153):** Fitting sweep is `[51]`.
4. **Specimen 471786879 (Model 480632594, Fit 497236229):** Fitting sweep is `[42]`.

### 3.2 Non-Fitting Sweeps as Held-Out Data
All remaining long-square sweeps for each specimen:
- Were recorded during the same patch-clamp session under identical recording temperature ($34^\circ\text{C}$) and pipette solutions.
- Share identical onset ($1020\text{ ms}$) and step duration ($1000\text{ ms}$).
- Were not included in the optimization objective function (`fitting[0].sweeps`).
- Are classified as strictly **HELDOUT**.

---

## 4. Protocol Family and Repeated Condition Analysis

### 4.1 Protocol Families
- **COARSE Protocols (`C1LSCOARSE`):** Primary depolarizing and hyperpolarizing series with coarse amplitude increments (typically 20 pA steps, from $-110\text{ pA}$ to suprathreshold plateaus).
- **FINEST Protocols (`C1LSFINEST`):** High-resolution step sweeps clustered around the firing threshold to precisely locate rheobase, often including multiple repeats of identical current amplitudes.

### 4.2 Repeated Measurements (Rule 10 Adherence)
Per scientific non-negotiable rules, repeated sweeps at identical stimulus conditions are classified as repeated measurements of a single condition, rather than independent stimulus conditions:
- **Pop A (484564503):** 3 repeated sweeps at $+310.0\text{ pA}$ in `FINEST` (Sweeps 58, 60, 61).
- **Pop C (471129934):** 4 repeated sweeps at $+330.0\text{ pA}$ in `FINEST` (Sweeps 57, 58, 59, 60).
- **Pop D (471786879):** 3 repeated sweeps at $+240.0\text{ pA}$ in `FINEST` (Sweeps 52, 53, 54).

These repeated sweeps are analyzed both individually (to quantify experimental variability) and grouped (to avoid weighting repeated amplitudes disproportionately in F-I curves).

---

## 5. Machine-Readable Audit Outputs

The following verified machine-readable CSVs have been generated:
1. [`results/phase3b/fitting_sweeps.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/fitting_sweeps.csv): 4 rows documenting the calibration sweeps.
2. [`results/phase3b/heldout_sweeps.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_sweeps.csv): 109 rows detailing all valid held-out sweeps.
3. [`results/phase3b/condition_groups.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/condition_groups.csv): 102 rows grouping sweeps into unique stimulus conditions.

---

## 6. Audit Gate 1 Evaluation

| Criterion | Requirement | Observed Status | Verdict |
|---|---|---|---|
| **Fitting Sweep Mapping** | Descriptors map to verified NWB sweeps | 4/4 mapped and verified | **PASS** |
| **No Overlap** | Zero fitting sweeps in held-out sets | Exactly 0 overlapping sweeps | **PASS** |
| **Protocol Separation** | COARSE vs FINEST explicitly tracked | 93 COARSE, 16 FINEST classified | **PASS** |
| **Repeated Condition Handling** | Repeated amplitudes grouped | 102 unique conditions across 109 sweeps | **PASS** |
| **Provenance Integrity** | All candidate sweeps in committed inventory and NWB | 109/109 sweeps verified in NWB | **PASS** |

**Audit Gate 1 Verdict:** **PASS — PROCEED TO PHASE 2 HELD-OUT DATA QUALITY AUDIT**.


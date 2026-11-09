# INCM Phase 5C.3 — Population B F–I Claim Verification Record

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Repository:** `Patel-Princy/INCM_project`  
**Branch:** `ashish-work`  
**Authoritative Milestone:** Phase 5C.3 Population B F–I Verification  
**Date:** November 2026  
**Audited Specimen:** Specimen `318808427` (VISp Layer 2/3, Model `473863035`, Nr5a1-Cre)  
**Audited Artifacts:**
- [`results/phase5/FINAL_RESEARCH_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/FINAL_RESEARCH_REPORT.md)
- [`results/phase5/PHASE5C2_FINAL_WORDING_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C2_FINAL_WORDING_AUDIT.md)

---

## 1. Executive Verification Overview

This audit was conducted to independently verify the factual accuracy and data provenance of the revised Population B (VISp Layer 2/3, Specimen `318808427`) firing rate (F–I) claims:
- **At +210 pA:** Biological recording fired **22 spikes**, FHN fired **17 spikes**.
- **At +250 pA:** Biological recording fired **27 spikes**, FHN fired **2 spikes**.
- **At +270 pA:** Biological recording fired **29 spikes**, FHN fired **1 spike**.

### Core Audit Findings
1. **Claims 100% Verified:** Every one of the three claims (+210 pA: 22 vs 17; +250 pA: 27 vs 2; +270 pA: 29 vs 1) was confirmed to be **100% factually genuine and strictly traceable** to the original frozen evaluation CSVs and per-sweep JSON records.
2. **Protocol Comparability Confirmed:** Sweeps 41 (+210 pA), 42 (+230 pA), 43 (+250 pA), and 44 (+270 pA) all belong to the identical `COARSE` protocol family ($1000.0\text{ ms}$ steps from $t = 1020.0$ to $2020.0\text{ ms}$, sampled at $200\text{ kHz}$) delivered sequentially in 20 pA increments. There are no inter-protocol discrepancies among these sweeps.
3. **FHN Collapse Genuinely Present:** The precipitous collapse of FHN firing from 17 spikes (+210 pA) and 16 spikes (+230 pA) down to 2 spikes (+250 pA) and 1 spike (+270 pA) is genuinely present in the frozen data. It is caused by cubic nullcline geometry and heavy recovery feedback deactivating repetitive firing as the system enters depolarizing block.
4. **Surrounding Text Inconsistencies Corrected:** While the three target F–I values were completely accurate, the audit uncovered residual drafting artifacts in surrounding sections of `FINAL_RESEARCH_REPORT.md` (Table 1 calibration sweep IDs, residual $101.4\text{ M}\Omega$ input resistance, $(70, 90]\text{ pA}$ rheobase, and an erroneous claim of "+290 pA"). These were corrected in-place to the true frozen values: $R_{\mathrm{in}} = 80.3\text{ M}\Omega$, rheobase $(110, 130]\text{ pA}$, calibration sweep 40 (+190 pA), and maximum firing up to 29 spikes at +270 pA.

---

## 2. Complete Population B Empirical Evidence Table

The table below compiles every current-clamp sweep for Population B (Specimen `318808427`) across biological recordings, detailed biophysical models, and FitzHugh–Nagumo models:

| Current (pA) | Sweep ID | Protocol | Biological spikes | Detailed spikes | FHN spikes | Source |
|:---:|:---:|:---:|---:|---:|---:|:---|
|  $-110.0$ | 25 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 31) |
|   $-70.0$ | 27 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 32) |
|   $-50.0$ | 28 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 33) |
|   $-30.0$ | 29 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 34) |
|   $+10.0$ | 31 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 35) |
|   $+30.0$ | 32 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 36) |
|   $+50.0$ | 33 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 37) |
|   $+70.0$ | 34 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 38) |
|   $+90.0$ | 35 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 39) |
|  $+110.0$ | 36 | COARSE | 0 | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 40) |
|  $+130.0$ | 37 | COARSE | **1** | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 41) |
|  $+150.0$ | 38 | COARSE | **8** | **11** | **15** | `results/phase4c/fhn_detailed_comparison.csv` (row 42) |
|  $+170.0$ | 39 | COARSE | **13** | **16** | **17** | `results/phase4c/fhn_detailed_comparison.csv` (row 43) |
|  $+190.0$ | 40 | COARSE | **19** | **19** | **17** | `results/phase3/detailed_model/318808427/summary.json` & `results/phase4b/` |
|  $+210.0$ | 41 | COARSE | **22** | **23** | **17** | `results/phase4c/fhn_detailed_comparison.csv` (row 44) |
|  $+230.0$ | 42 | COARSE | **22** | **26** | **16** | `results/phase4c/fhn_detailed_comparison.csv` (row 45) |
|  $+250.0$ | 43 | COARSE | **27** | **29** | **2** | `results/phase4c/fhn_detailed_comparison.csv` (row 46) |
|  $+270.0$ | 44 | COARSE | **29** | **33** | **1** | `results/phase4c/fhn_detailed_comparison.csv` (row 47) |
|  $+130.0$ | 46 | FINEST | **1** | 0 | 0 | `results/phase4c/fhn_detailed_comparison.csv` (row 48) |

---

## 3. Detailed Audit of Specific Verification Targets

### 3.1 Verification of +210 pA (Sweep 41, COARSE)
- **Current Amplitude:** $210.000003\text{ pA}$
- **Biological Spike Count:** **22 spikes** (first spike at $1033.54\text{ ms}$, last spike at $1991.005\text{ ms}$).
- **Detailed-Model Spike Count:** **23 spikes** (first spike at $1037.98\text{ ms}$, last spike at $2017.84\text{ ms}$).
- **FHN Spike Count:** **17 spikes** (first spike at $1035.15\text{ ms}$).
- **Authoritative Provenance:**
  - `results/phase3b/heldout/318808427/sweep_41/summary.json`
  - `results/phase3b/heldout/318808427/aggregated_metrics.csv` (row 13)
  - `results/phase4c/fhn_detailed_comparison.csv` (row 44)
  - `results/phase4c/fhn_heldout_metrics.csv` (row 44)
- **Status:** **VERIFIED (Exact match).**

### 3.2 Verification of +250 pA (Sweep 43, COARSE)
- **Current Amplitude:** $249.999993\text{ pA}$
- **Biological Spike Count:** **27 spikes** (first spike at $1030.72\text{ ms}$, last spike at $2014.70\text{ ms}$).
- **Detailed-Model Spike Count:** **29 spikes** (first spike at $1032.88\text{ ms}$, last spike at $1995.765\text{ ms}$).
- **FHN Spike Count:** **2 spikes** (transient onset firing followed by depolarization block).
- **Authoritative Provenance:**
  - `results/phase3b/heldout/318808427/sweep_43/summary.json`
  - `results/phase3b/heldout/318808427/aggregated_metrics.csv` (row 15)
  - `results/phase4c/fhn_detailed_comparison.csv` (row 46)
  - `results/phase4c/fhn_heldout_metrics.csv` (row 46)
- **Status:** **VERIFIED (Exact match).**

### 3.3 Verification of +270 pA (Sweep 44, COARSE)
- **Current Amplitude:** $269.999995\text{ pA}$
- **Biological Spike Count:** **29 spikes** (first spike at $1029.32\text{ ms}$, last spike at $1982.985\text{ ms}$).
- **Detailed-Model Spike Count:** **33 spikes** (first spike at $1031.275\text{ ms}$, last spike at $2005.43\text{ ms}$).
- **FHN Spike Count:** **1 spike** (single onset spike followed by depolarized equilibrium lock).
- **Authoritative Provenance:**
  - `results/phase3b/heldout/318808427/sweep_44/summary.json`
  - `results/phase3b/heldout/318808427/aggregated_metrics.csv` (row 16)
  - `results/phase4c/fhn_detailed_comparison.csv` (row 47)
  - `results/phase4c/fhn_heldout_metrics.csv` (row 47)
- **Status:** **VERIFIED (Exact match).**

---

## 4. Protocol Comparability and Dynamical Interpretation

### 4.1 Direct Protocol Comparability
- Sweeps 41, 42, 43, and 44 all belong to the `COARSE` long-square current-clamp protocol family.
- All four sweeps were recorded sequentially in the same recording session with identical sampling rates ($200\text{ kHz}$), identical pulse durations ($1000.0\text{ ms}$), and identical step timing ($t_{\mathrm{onset}} = 1020.0\text{ ms}$, $t_{\mathrm{offset}} = 2020.0\text{ ms}$).
- The steps advance in uniform $20\text{ pA}$ increments ($+210, +230, +250, +270\text{ pA}$).
- **Conclusion:** These four sweeps represent directly comparable, uniform experimental conditions.

### 4.2 Dynamical Basis of the FHN Collapse
- In the biological recording and detailed biophysical model, firing rates scale monotonically across this entire range (Biology: $22 \to 22 \to 27 \to 29$ spikes; Detailed: $23 \to 26 \to 29 \to 33$ spikes).
- In the calibrated FHN model ($C_m = 38.25\text{ pF}, \tau_w = 6.89\text{ ms}, a_w = 9.77\text{ nS}$), the firing rate increases from +150 to +170 pA ($15 \to 17$ spikes), plateaus at 17 spikes through +210 pA, and decreases slightly to 16 spikes at +230 pA.
- At $+250\text{ pA}$ and $+270\text{ pA}$, strong depolarizing current shifts the cubic $V$-nullcline upward to an extent where the system crosses its upper bifurcation threshold into **depolarization block**. The trajectory fires 1 or 2 initial spikes during the onset charging transient before settling onto the stable depolarized branch, causing repetitive firing to cease. This phenomenon was already recognized in the baseline handoff (`PHASE5_BASELINE_AND_FLASH_HANDOFF.md`, line 291: *"FHN collapses to 1–2 spikes at +250–270 pA"*).

---

## 5. Report Inconsistencies Discovered and Corrected

During the verification of surrounding narrative text, four historical drafting errors in `FINAL_RESEARCH_REPORT.md` were identified and corrected in-place:

1. **Table 1 Calibration Sweeps and Input Resistances:**
   - Pop A listed Sweep 48 (+370 pA) $\to$ Corrected to **Sweep 49 (+370 pA)**.
   - Pop B listed $101.4\text{ M}\Omega$ and Sweep 37 (+170 pA) $\to$ Corrected to **$R_{\mathrm{in}} = 80.3\text{ M}\Omega$** and **Sweep 40 (+190 pA)** (per `results/phase4b/fhn_calibration_metrics.csv`).
   - Pop C listed $43.1\text{ M}\Omega$ and Sweep 48 (+410 pA) $\to$ Corrected to **$R_{\mathrm{in}} = 31.3\text{ M}\Omega$** and **Sweep 51 (+410 pA)**.
2. **ASCII Architecture Diagram (Lines 256–271):**
   - Pop B box listed `Rin = 101.4 MOhm; Rheobase = (70, 90]` $\to$ Corrected to **`Rin = 80.3 MOhm; Rheobase = (110, 130]`**.
   - Pop C box listed `Rin = 43.1 MOhm` $\to$ Corrected to **`Rin = 31.3 MOhm`**.
3. **Population B Biological Profile (§9.2, Line 284):**
   - Previous draft stated: *"High input resistance ($101.4\text{ M}\Omega$), low rheobase ($(70, 90]\text{ pA}$), and robust high-frequency repetitive firing (up to 25 spikes at +290 pA)."*
   - Corrected to: **"High input resistance ($80.3\text{ M}\Omega$), low rheobase ($(110, 130]\text{ pA}$), and robust high-frequency repetitive firing (up to 29 spikes at +270 pA)."** (reflecting `results/phase3b/heldout_rheobase.csv` and the actual maximum tested sweep, Sweep 44 at +270 pA).
4. **Population C Biological Profile (§9.3, Line 289):**
   - Corrected $43.1\text{ M}\Omega$ to **$31.3\text{ M}\Omega$** (matching `rin_exp_mohm: 31.29` in `results/phase4b/fhn_calibration_metrics.csv`).

---

## 6. Files Changed

1. [`results/phase5/FINAL_RESEARCH_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/FINAL_RESEARCH_REPORT.md) — Corrected Table 1, ASCII diagram, and §9.2 / §9.3 profiles.
2. [`results/phase5/PHASE5C_REPORT_VERIFICATION.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C_REPORT_VERIFICATION.md) — Added explicit verification row for Population B high-current F–I dynamics.
3. [`results/phase5/PHASE5C3_POPULATION_B_FI_VERIFICATION.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase5/PHASE5C3_POPULATION_B_FI_VERIFICATION.md) — Authored this authoritative audit artifact.

---

## 7. Confirmation of Zero Simulations or Recalibrations

- **Simulations Executed:** 0
- **Model Recalibrations:** 0
- **Parameter Adjustments:** 0
- **Precursor Phase Modifications:** 0 (all historical files in `results/phase0/` through `results/phase4c3/`, `data/`, and `tests/` remain 100% bit-for-bit untouched).

---

## 8. Regression Test Suite and Git Status

The automated regression test suite was executed across all 451 tests:
```
python -m pytest tests -q
============================= 451 passed in 64.80s =============================
```
**Result:** 451/451 tests passed cleanly.

### Git Status
```
On branch ashish-work
Your branch is up to date with 'origin/ashish-work'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	results/phase5/

nothing added to commit but untracked files present (use "git add" to track)
```
- Active branch: `ashish-work`
- The `main` branch was not touched or modified.
- All working tree changes remain strictly uncommitted.


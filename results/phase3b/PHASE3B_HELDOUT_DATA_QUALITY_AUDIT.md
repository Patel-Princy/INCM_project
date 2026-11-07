# Phase 3B — Held-Out Stimulus and Data Quality Audit

**Date:** 2026-11-08  
**Repository:** `Patel-Princy/INCM_project`  
**Active Working Branch:** `ashish-work`  
**Focus:** Comprehensive data quality and waveform validation across all 109 candidate held-out sweeps.

---

## 1. Executive Summary

A programmatic data quality audit was conducted on every candidate held-out long-square sweep across the four target specimens in their cached NWB recordings. All **109 candidate held-out sweeps** passed every quality, continuity, and physical validity gate:
- Zero NaN or infinite values across all stimulus and response arrays.
- Perfect sample count parity between stimulus command and membrane voltage response.
- Step onsets verified at $1020.0\text{ ms} \pm 0.05\text{ ms}$.
- Step durations verified at $1000.0\text{ ms} \pm 0.05\text{ ms}$.
- Plateau current amplitudes match the committed sweep inventory amplitudes to $< 0.0001\text{ pA}$ across all 109 sweeps.
- Zero sweeps excluded; 100% data retention (109/109 valid).

---

## 2. Population-by-Population Data Quality Summary

| Population | Specimen ID | Layer | Total Long-Square | Fitting Sweeps | Candidate Held-Out | Valid Held-Out | Excluded Sweeps | Unique Amplitudes | Protocol Family Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| **A** | `484564503` | 4 | 32 | 1 (Swp 49) | 31 | **31** | 0 | 29 | COARSE: 27 sweeps ($-110$ to $+430$ pA)<br/>FINEST: 4 sweeps ($+300$ to $+310$ pA) |
| **B** | `318808427` | 2/3 | 19 | 1 (Swp 40) | 18 | **18** | 0 | 18 | COARSE: 17 sweeps ($-110$ to $+270$ pA)<br/>FINEST: 1 sweep ($+130$ pA) |
| **C** | `471129934` | 5 | 35 | 1 (Swp 51) | 34 | **34** | 0 | 29 | COARSE: 26 sweeps ($-110$ to $+430$ pA)<br/>FINEST: 8 sweeps ($+280$ to $+330$ pA) |
| **D** | `471786879` | 6a | 27 | 1 (Swp 42) | 26 | **26** | 0 | 24 | COARSE: 23 sweeps ($-110$ to $+350$ pA)<br/>FINEST: 3 sweeps ($+240$ pA repeated) |
| **Total** | | | **113** | **4** | **109** | **109** | **0** | **102** | **93 COARSE, 16 FINEST** |

---

## 3. Waveform Verification Details

### 3.1 Test Pulse vs Long Step Differentiation
Every Allen long-square current-clamp sweep consists of two contiguous current pulses:
1. An access-resistance test pulse delivering $-100\text{ pA}$ for approximately $10\text{ ms}$–$20\text{ ms}$ shortly after sweep start.
2. A main experimental step delivering the commanded current for $1000\text{ ms}$ starting at $1020\text{ ms}$.

For subthreshold sweeps where the command current magnitude is small (e.g. $+10\text{ pA}$ or $+30\text{ pA}$), sorting pulses purely by absolute amplitude mistakenly captures the $-100\text{ pA}$ test pulse rather than the experimental step. Applying a duration threshold filter ($\text{duration} > 100.0\text{ ms}$) unambiguously isolates the $1000\text{ ms}$ depolarizing or hyperpolarizing step across all amplitudes without exception.

### 3.2 L5 Specimen 471129934 Waveform Conformance
For specimen `471129934`, raw stimulus datasets in NWB were confirmed to be stored directly in Amperes:
- Minimum held-out step: Sweep 25 ($-1.1 \times 10^{-10}\text{ A} = -110.0\text{ pA}$).
- Maximum held-out step: Sweep 52 ($+4.3 \times 10^{-10}\text{ A} = +430.0\text{ pA}$).
- Maximum absolute deviation from inventory amplitude across all 34 held-out sweeps: $0.0000\text{ pA}$.
- All 34 held-out sweeps conform to the unscaled SI interpretation established in Phase 3A.

---

## 4. Audit Gate 2 Evaluation

| Audit Gate Condition | Requirement | Status |
|---|---|---|
| **No Corrupt or Missing Data** | 0 NaNs, 0 Infs, complete lengths | **PASS** (109/109 sweeps complete) |
| **Physical Waveform Plausibility** | Onset $1020\text{ ms}$, duration $1000\text{ ms}$ | **PASS** (109/109 verified) |
| **Amplitude Conformance** | Deviation from inventory $< 1.0\text{ pA}$ | **PASS** (max diff $0.0000\text{ pA}$) |
| **Fitting Exclusion** | Zero overlap with calibration sweeps | **PASS** (4 fitting sweeps excluded) |
| **Protocol Clarity** | Separation of COARSE and FINEST | **PASS** (93 COARSE, 16 FINEST) |

**Audit Gate 2 Verdict:** **PASS — ALL 109 HELD-OUT CONDITIONS APPROVED FOR PIPELINE HARDENING AND SIMULATION**.


# PHASE 3C — BASELINE AND FILE RECOVERY AUDIT

**Project:** How Much Biological Detail Does a Neuron Model Need?  
**Phase:** 3C — Independent Scientific Consistency Audit and Phase 3B Results Correction  
**Date:** 2026-11-08  
**Working Branch:** `ashish-work`  
**HEAD Commit:** `ee8d11635e9fa7e5e2b1062add94dd324f052a40` (`feat: Phase 3B held-out evaluation across four V1 populations`)  
**Previous Milestone:** Phase 3A commit `ccc60e6fe2350ef1fc28290e29b12d59392bca9e`  

---

## 1. Environment and Working Tree Verification

- **Branch Check:** Confirmed active on `ashish-work`. No commits on `main` or merge requests to `main`.
- **Working Tree Check:** Clean working tree; `nothing to commit, working tree clean`.
- **Remote Synchronization:** In sync with `origin/ashish-work` at commit `ee8d116`.
- **Automated Test Suite:** 349 tests collected and passing in `tests/` across 11 test modules.

---

## 2. Inventory of Recovered Assets

### 2.1 Phase 3A Artifacts (`results/phase3/`)
- [`PHASE3A_BASELINE_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3/PHASE3A_BASELINE_AUDIT.md)
- [`PHASE3A_PIPELINE_TRACE.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3/PHASE3A_PIPELINE_TRACE.md)
- [`PHASE3A_FOUR_REPRESENTATIVE_ASSET_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3/PHASE3A_FOUR_REPRESENTATIVE_ASSET_AUDIT.md)
- [`four_representative_asset_audit.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3/four_representative_asset_audit.csv)
- [`PHASE3A_PIPELINE_HARDENING_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3/PHASE3A_PIPELINE_HARDENING_AUDIT.md)
- [`PHASE3A_FINAL_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3/PHASE3A_FINAL_REPORT.md)
- In-sample calibration outputs in `results/phase3/detailed_model/` for all 4 specimens:
  - Specimen `484564503` (Pop A, L4, Sweep 49)
  - Specimen `318808427` (Pop B, L2/3, Sweep 40)
  - Specimen `471129934` (Pop C, L5, Sweep 51)
  - Specimen `471786879` (Pop D, L6a, Sweep 42)

### 2.2 Phase 3B Artifacts (`results/phase3b/`)
- Reports:
  - [`PHASE3B_BASELINE_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_BASELINE_AUDIT.md)
  - [`PHASE3B_SWEEP_PROVENANCE_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_SWEEP_PROVENANCE_AUDIT.md)
  - [`PHASE3B_HELDOUT_DATA_QUALITY_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_HELDOUT_DATA_QUALITY_AUDIT.md)
  - [`PHASE3B_EXECUTION_PIPELINE_AUDIT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_EXECUTION_PIPELINE_AUDIT.md)
  - [`PHASE3B_CROSS_POPULATION_ANALYSIS.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_CROSS_POPULATION_ANALYSIS.md)
  - [`PHASE3B_FINAL_REPORT.md`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/PHASE3B_FINAL_REPORT.md)
- Data CSVs:
  - [`fitting_sweeps.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/fitting_sweeps.csv) (4 rows)
  - [`heldout_sweeps.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_sweeps.csv) (109 rows)
  - [`condition_groups.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/condition_groups.csv) (102 rows)
  - [`heldout_metrics.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_metrics.csv) (109 rows)
  - [`heldout_fi_curves.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_fi_curves.csv) (102 rows)
  - [`heldout_rheobase.csv`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout_rheobase.csv) (4 rows)
- Figures in [`results/phase3b/figures/`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/figures/):
  - `fi_curves_all_populations.png` (285.9 KB)
  - `rheobase_comparison.png` (144.1 KB)
  - `error_distributions_by_population.png` (124.6 KB)
  - `first_spike_latency_comparison.png` (105.8 KB)
  - `passive_properties_comparison.png` (96.7 KB)
- Per-sweep simulation outputs under [`results/phase3b/heldout/`](file:///e:/INCM%20project/new%20incm%20project/INCM-Project/results/phase3b/heldout/):
  - Specimen `484564503` (31 sweep directories, `aggregated_metrics.csv`)
  - Specimen `318808427` (18 sweep directories, `aggregated_metrics.csv`)
  - Specimen `471129934` (34 sweep directories, `aggregated_metrics.csv`)
  - Specimen `471786879` (26 sweep directories, `aggregated_metrics.csv`)

---

## 3. Scope of Phase 3C Independent Audit

1. **Independent Recomputation:** Validate whether all aggregate statistics (mean/std of RMSE, MAE, correlation, spike count differences, rheobase intervals) match the underlying per-sweep JSON summaries and raw CSV data.
2. **L4 Discrepancy Investigation:** Scrutinize Population A (`484564503`, L4), where high suprathreshold current steps showed severe spike divergence (e.g., recorded 12 vs simulated 48 spikes at +430 pA), and determine whether this is an intrinsic model failure, stimulus mismatch, baseline artifact, or concealed by aggregate metrics.
3. **Subthreshold vs Suprathreshold Audit:** Reconcile prose claiming $> 0.98$ subthreshold correlation against the quantitative table showing L4 at 0.7402 and L5 at 0.9579.
4. **Protocol and Temporal Variability Audit:** Examine non-stationarity in L5 (repeated FINEST at +330 pA) and L6a (repeated FINEST at +240 pA) without attributing unverified biological mechanisms.
5. **Rheobase and F-I Curve Verification:** Audit interval definitions, step sizes, and repeated condition treatments.
6. **Report Corrections:** Prepare an honest, transparent correction log updating `PHASE3B_FINAL_REPORT.md` and `PHASE3B_CROSS_POPULATION_ANALYSIS.md`.
7. **FHN Readiness Specification:** Deliver mathematical and scientific specifications for Phase 4 FHN reduction without premature implementation.

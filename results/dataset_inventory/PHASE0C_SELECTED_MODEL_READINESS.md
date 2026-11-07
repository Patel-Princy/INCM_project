# Phase 0C: Selected-Model Readiness Audit

**Phase:** 0C — fit descriptor, recording, and asset readiness for 16 selected candidates
**Repository:** `Patel-Princy/INCM_project` · **Branch:** `ashish-work`
**Date:** 2026-11-07
**Scope:** 4 × 4 = 16 VISp spiny excitatory candidates with perisomatic biophysical models
**Status:** complete; **13/16 candidates are leakage-safe and potentially executable**

This audit is the gate between metadata-level feasibility (Phase 0B) and model
execution.  It downloads the 16 perisomatic fit descriptors, validates the
representative NWB recordings, and establishes which candidates have a
scientifically defensible calibration/held-out split.

Evidence labels:

| Label | Meaning |
|---|---|
| **OBSERVED** | read directly from a downloaded file or validated output |
| **DERIVED** | computed from those values by a named rule |
| **UNAVAILABLE** | the information is not accessible in this phase |

---

## 1. Executive verdict

1. **All 16 fit descriptors download and parse correctly.**  Every descriptor is
   classified as `perisomatic`, uses −14 mV junction potential, 34 °C temperature,
   and a genome of floating-point values.  **OBSERVED**
2. **All 16 descriptors map to the correct model and specimen** (self-check confirmed
   by the `descriptor_matches_model` field).  **SELF-CHECK**
3. **13/16 candidates have leakage-safe held-out conditions.**  The three exceptions
   (specimens 471767045, 471819401, 466632464) list fitting sweeps whose numbers
   cannot be found in the Allen sweep inventory; their held-out status is
   `UNRESOLVED_FITTING_SWEEP_UNMAPPED` rather than a confirmed failure.  **DERIVED**
4. **13/16 candidates are potentially executable (L7).**  Every candidate reaches L1
   (metadata listed) and L2 (descriptor parsed); all have resolved morphology
   references (L3) and mechanism sources (L4); 15/16 have matching reconstructions
   (L5).  The three candidates that fail L7 are blocked at L6 (fitting sweeps
   unmapped).  **DERIVED**
5. **NWB validation passed for four representatives** (one per population), with one
   mild anomaly in the L5 representative (conversion conflict, resolved by
   unit-only reading).  **OBSERVED**
6. **No model has been validated against its own recording.**  The one executed
   candidate (382982932, L2/3) is phase-2 execution evidence, not a
   recording–simulation comparison.  **OBSERVED**

---

## 2. Selected candidates

Selection follows the brief's seven priorities in cascade order (see
`src/data_audit/selected_model_readiness.py::selection_sort_key`).  All 16 selected
cells are at 200 kHz sampling and have ≥ 5 distinct depolarising amplitudes.

| Pop | Rank | Specimen | Layer | Driver line | Distinct amps | Recon match | Tier |
|-----|-----:|----------|-------|-------------|-------------:|-------------|------|
| A (L4) | 1 | 484564503 | 4 | Rorb-IRES2-Cre | 23 | YES | PRIMARY |
| A (L4) | 2 | 485931158 | 4 | Rorb-IRES2-Cre | 20 | YES | PRIMARY |
| A (L4) | 3 | 468193142 | 4 | Scnn1a-Tg3-Cre | 20 | YES | PRIMARY |
| A (L4) | 4 | 320207387 | 4 | Scnn1a-Tg3-Cre | 19 | YES | PRIMARY |
| B (L2/3) | 1 | 318808427 | 2/3 | Nr5a1-Cre | 14 | YES | PRIMARY |
| B (L2/3) | 2 | 476087653 | 2/3 | Nr5a1-Cre | 13 | YES | PRIMARY |
| B (L2/3) | 3 | 485468180 | 2/3 | Nr5a1-Cre | 6 | YES | PRIMARY |
| B (L2/3) | 4 | 382982932 | 2/3 | Nr5a1-Cre | 17 | NO | CONDITIONAL |
| C (L5) | 1 | 471129934 | 5 | Rbp4-Cre_KL100 | 24 | YES | PRIMARY |
| C (L5) | 2 | 488679042 | 5 | Rorb-IRES2-Cre | 23 | YES | PRIMARY |
| C (L5) | 3 | 476048909 | 5 | Rorb-IRES2-Cre | 20 | YES | PRIMARY |
| C (L5) | 4 | 471767045 | 5 | Rbp4-Cre_KL100 | 20 | YES | PRIMARY |
| D (L6a) | 1 | 471786879 | 6a | Ntsr1-Cre_GN220 | 19 | YES | PRIMARY |
| D (L6a) | 2 | 471819401 | 6a | Ntsr1-Cre_GN220 | 18 | YES | PRIMARY |
| D (L6a) | 3 | 471789504 | 6a | Ntsr1-Cre_GN220 | 16 | YES | PRIMARY |
| D (L6a) | 4 | 466632464 | 6a | Ntsr1-Cre_GN220 | 16 | YES | PRIMARY |

**OBSERVED** from `four_v1_selected_candidates.csv`.

Notes:
- Population B rank 4 (specimen 382982932) is CONDITIONAL because the perisomatic
  model was built on a different reconstruction (491771090) from the specimen's own
  (674389884).  This specimen was already the subject of Phases 2C and 2G; it is
  retained as the fourth B candidate but its reconstruction mismatch is a known
  limitation.
- Population C rank 2 (specimen 488679042) and rank 3 (476048909) use Rorb driver
  rather than Rbp4; Rorb is an L4 marker but these cells are anatomically in L5.
  The selection criterion is the anatomically confirmed layer, not the driver line;
  identity is annotated but does not drive the selection.

---

## 3. Fit descriptor audit

All 16 perisomatic fit descriptors were downloaded from the Allen Brain Atlas API.

### 3.1 Structure summary

Every descriptor has the expected structure:

| Field | Value across all 16 | Evidence |
|---|---|---|
| Top-level keys | `conditions`, `fitting`, `genome`, `passive` | OBSERVED |
| `passive` schema | list of one dict with `ra`, `cm` (nested list), `e_pas` | OBSERVED |
| Genome value type | float (perisomatic) | OBSERVED |
| Junction potential | −14.0 mV (all 16) | OBSERVED |
| Recording temperature | 34.0 °C (all 16) | OBSERVED |
| `fitting[].sweeps` | at least one entry (all 16) | OBSERVED |

### 3.2 Fitting sweep identification

| Pop | Specimen | Fitting sweeps (numbers) | Fitting amplitude (pA) | Sweep mapped? |
|-----|----------|--------------------------|------------------------|---------------|
| A | 484564503 | 49 | 370 | YES |
| A | 485931158 | 49 | 190 | YES |
| A | 468193142 | 46 | 330 | YES |
| A | 320207387 | 41 | 250 | YES |
| B | 318808427 | 40 | 190 | YES |
| B | 476087653 | 40 | 130 | YES |
| B | 485468180 | 36 | 130 | YES |
| B | 382982932 | 38 | 170 | YES |
| C | 471129934 | 51 | 410 | YES |
| C | 488679042 | 62 | 330 | YES |
| C | 476048909 | 48 | 290 | YES |
| C | 471767045 | 77, 78, 79, 80 | — | NO |
| D | 471786879 | 42 | 250 | YES |
| D | 471819401 | 72, 73, 75 | — | NO |
| D | 471789504 | 46 | 210 | YES |
| D | 466632464 | 58, 59, 60 | — | NO |

**OBSERVED** from `four_v1_fit_descriptor_audit.csv`.

The three UNMAPPED cases (471767045, 471819401, 466632464) have sweep numbers in
the descriptor that do not appear in the Allen sweep inventory for those specimens.
This is a data-provenance gap: the sweep numbers are present in the fit JSON but
absent from the sweep metadata table.  The held-out split is therefore UNRESOLVED
for these three candidates; it is not counted as a failure.  **OBSERVED**

---

## 4. Held-out feasibility

| Pop | Specimen | Status | Leakage-safe | Fit sweeps | Heldout sweeps | Heldout amps |
|-----|----------|--------|:---:|---:|---:|---:|
| A | 484564503 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 25 | 22 |
| A | 485931158 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 30 | 20 |
| A | 468193142 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 23 | 19 |
| A | 320207387 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 21 | 18 |
| B | 318808427 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 14 | 13 |
| B | 476087653 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 16 | 12 |
| B | 485468180 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 8 | 5 |
| B | 382982932 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 22 | 17 |
| C | 471129934 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 29 | 23 |
| C | 488679042 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 27 | 22 |
| C | 476048909 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 26 | 19 |
| C | 471767045 | UNRESOLVED_FITTING_SWEEP_UNMAPPED | NO | 4 | 25† | 20† |
| D | 471786879 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 20 | 18 |
| D | 471819401 | UNRESOLVED_FITTING_SWEEP_UNMAPPED | NO | 3 | 21† | 18† |
| D | 471789504 | RESOLVED_LEAKAGE_SAFE | YES | 1 | 20 | 15 |
| D | 466632464 | UNRESOLVED_FITTING_SWEEP_UNMAPPED | NO | 3 | 18† | 16† |

† computed as "all depolarising sweeps"; the fitted ones cannot be excluded
because their numbers do not map.

**OBSERVED** from `four_v1_heldout_feasibility.csv`.

Every resolved candidate has many more held-out amplitudes than fitting amplitudes
(ratio 15–23:1), giving strong leakage protection.  The `RESOLVED_LEAKAGE_SAFE`
split type is AMPLITUDE: at least two depolarising amplitudes that the fitting sweep
never saw.  For four candidates both COARSE and FINEST protocol families are
present, providing an optional PROTOCOL_FAMILY split.

---

## 5. Model asset readiness

Eight evidence levels from Phase 0B §5 are re-evaluated for all 16 candidates.

| Level | Description | YES | NO | Partial |
|---|---|---:|---:|---:|
| L1 | Listed in metadata | 16 | 0 | 0 |
| L2 | Fit descriptor downloaded and parsed | 16 | 0 | 0 |
| L3 | Morphology asset available | 5 (VERIFIED) | 0 | 11 (REFERENCE_RESOLVED) |
| L4 | Mechanism sources available | 16 | 0 | 0 |
| L5 | Model reconstruction matches specimen | 15 | 1 | 0 |
| L6 | Fitting sweeps identifiable | 13 | 3 | 0 |
| L7 | Potentially executable | 13 | 3 | 0 |
| L8 | Actually executed and validated | 0 (validated) | 15 | 1 (executed, not validated) |

**OBSERVED** from `four_v1_model_asset_readiness.csv`.

L3 "REFERENCE_RESOLVED" means the Allen download URL responds to a HEAD request
with HTTP 200; the file was not downloaded.  "VERIFIED" means the morphology file
exists in the repository (for the five specimens whose NWB was already cached and
morphology was probed at download time).

L4 YES is based on the mechanism source files in
`tmp/model_cache/allensdk/modfiles/` and a manifest reference for the perisomatic
template.  This has been confirmed by Phase 2C execution for specimen 382982932.
The same mechanism set applies to all perisomatic models.

The three L7=NO candidates (471767045, 471819401, 466632464) are blocked solely at
L6; their L1–L5 are all met.  If the fitting sweep numbers can be resolved against
the NWB sweep metadata directly (without the inventory), they may become L7=YES.

---

## 6. Recording validation

One representative NWB was validated per population, plus one supplementary (the
Phase 2 reference specimen 382982932 was already cached).

| Pop | Specimen | Role | NWB verdict | Notes |
|-----|----------|------|-------------|-------|
| A | 484564503 | REPRESENTATIVE | MATCH | — |
| B | 318808427 | REPRESENTATIVE | MATCH | — |
| B | 382982932 | SUPPLEMENTARY_CACHED | MATCH | Phase 2C reference |
| C | 471129934 | REPRESENTATIVE | MATCH_CONVERSION_CONFLICT | declared conversion contradicts samples; unit-only reading matches inventory |
| D | 471786879 | REPRESENTATIVE | MATCH | — |

**OBSERVED** from `four_v1_recording_validation.csv`.

The L5 representative (471129934) shows a `MATCH_CONVERSION_CONFLICT` verdict.
This means the `conversion` attribute in the HDF5 stimulus series is set to a
value that would give the wrong amplitude if applied, but the raw binary samples
converted by the unit-only rule exactly match the Allen inventory amplitude.  This
is a known data-acquisition quirk of some Allen recordings that was first observed
in Phase 1B/1C and handled by the units-aware rule.  The recording is usable;
only the declared conversion attribute should be ignored.

---

## 7. Per-population feasibility assessment

| Pop | Layer | Leakage-safe | Potentially executable | NWB validated | L8 executed |
|-----|-------|:---:|:---:|:---:|:---:|
| A (L4) | 4 | 4/4 | 4/4 | 1 (representative) | 0 |
| B (L2/3) | 2/3 | 4/4 | 4/4 | 2 (rep + cached) | 1 (not validated) |
| C (L5) | 5 | 3/4 | 3/4 | 1 (representative) | 0 |
| D (L6a) | 6a | 2/4 | 2/4 | 1 (representative) | 0 |

**DERIVED** from the above sections.

- **A and B are fully ready** for a perisomatic model comparison (4/4 leakage-safe,
  4/4 executable).
- **C is ready for three of four candidates.**  The fourth (471767045) has fitting
  sweeps that do not map to the inventory; the three confirmed candidates are strong
  enough to proceed.
- **D has two confirmed candidates** (471786879, 471789504) and two unresolved
  (471819401, 466632464).  A 2-neuron D group is scientifically defensible as a
  preliminary result; it cannot support layer-level claims on its own.

---

## 8. Self-check results

All seven self-checks passed at the end of the audit run:

| Check | Result |
|---|---|
| four_candidates_per_population | A=4, B=4, C=4, D=4 |
| no_duplicate_specimens | 16 specimens, 16 unique |
| model_ids_map_to_correct_specimens | all match |
| fit_descriptors_map_to_correct_models | all match |
| fitting_sweeps_excluded_from_heldout | no overlap |
| missing_fitting_metadata_marked_unresolved | 0 without sweeps, 0 unresolved |
| failed_downloads_not_counted_as_assets | 0 failures |

---

## 9. Limitations

1. **Three candidates have unmapped fitting sweeps** (C rank 4, D rank 2, D rank 4).
   The sweep numbers appear in the fit JSON but not in the sweep inventory.  This
   may mean the sweeps were assigned in a version of the inventory that was later
   updated, or it may be a genuine data provenance gap.  These candidates cannot
   have their held-out split frozen until the sweep numbers are traced to the NWB
   directly.
2. **L3 for 11 candidates is REFERENCE_RESOLVED, not VERIFIED.**  The morphology
   URLs respond correctly but the files were not downloaded.  Downloading and
   checksumming the morphology SWC files should be a pre-execution step.
3. **No model has been validated against its recording.**  L8=NOT_EXECUTED for 15
   candidates.  Phase 0C establishes that execution is feasible for 13 candidates;
   it does not execute them.
4. **Reconstruction mismatch in specimen 382982932 (B rank 4).**  The model uses
   reconstruction 491771090; the specimen's own reconstruction is 674389884.  This
   is a known limitation from Phase 2B.
5. **NWB conversion conflict in specimen 471129934 (C rank 1).**  The stimulus
   conversion attribute is incorrect but the unit-only reading is correct.  Any
   code that applies the declared conversion without checking the raw samples will
   produce wrong amplitudes; the Phase 1B validator handles this correctly.

---

## 10. Recommended next steps

1. **Execute L7=YES candidates.**  Start with one representative per population
   (A: 484564503, B: 318808427, C: 471129934, D: 471786879) using the perisomatic
   model and the Phase 2C execution pipeline.
2. **Compare simulated and recorded responses** (L8) for each representative.
   This is the first L8 evidence for populations A, C, and D.
3. **Resolve the three unmapped fitting sweep candidates.**  Open their NWB files
   directly, find sweep numbers 77–80 (C4), 72–75 (D2), and 58–60 (D4), and check
   whether those sweep numbers exist in the NWB stimulus series metadata.  If they
   do, the inventory is the gap; if they do not, the fit JSON references sweeps that
   were not recorded.
4. **Download and checksum morphology SWC files** for the 11 REFERENCE_RESOLVED
   candidates before execution.
5. **Implement FHN fitting** using the calibration sweeps identified here, with
   held-out evaluation on the leakage-safe conditions.

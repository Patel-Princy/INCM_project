# How Much Biological Detail Does a Neuron Model Need?

**Research question:** How much biological detail does a neuron model need to
reproduce a real neuron's electrophysiological behaviour, and which behaviours
are preserved or lost when a detailed conductance-based model is reduced to a
FitzHugh–Nagumo (FHN) model?

**Repository:** `Patel-Princy/INCM_project` · **Active branch:** `ashish-work`

---

## Overview

This project compares detailed conductance-based models (Allen Cell Types Database
perisomatic biophysical models) against a reduced FitzHugh–Nagumo (FHN) model
across four layer-defined excitatory neuron populations in mouse primary visual
cortex (VISp):

| Group | Layer | Description |
|-------|-------|-------------|
| A | 4 | VISp L4 spiny excitatory |
| B | 2/3 | VISp L2/3 spiny excitatory |
| C | 5 | VISp L5 spiny excitatory |
| D | 6a | VISp L6a spiny excitatory |

These are layer-defined populations. The database does not carry projection
identity (IT/ET/PT/CT), so no projection labels are used.

---

## Project status

| Phase | Description | Status | Commit |
|-------|-------------|--------|--------|
| 0 | Allen dataset inventory (1,588 VISp specimens) | ✓ Complete | `80fa12e` |
| 0B | Four-population feasibility audit | ✓ Complete | `0470702` |
| **0C** | **Selected-model readiness: 16 candidates, fit descriptors, NWB** | **✓ Complete** | **`b435abb`** |
| 1A | NWB unit validation (specimen 341442651) | ✓ Complete | `1b310b1` |
| 1B | Cross-specimen unit validation (236 sweeps) | ✓ Complete | `3ef3002` |
| 1C | Pyramidal candidate validation | ✓ Complete | `fca64d5` |
| 2A | Model execution readiness | ✓ Complete | `b0cc4f0` |
| 2B | Geometry and manifest audit | ✓ Complete | `6620724` |
| 2C | Perisomatic model execution (specimen 382982932) | ✓ Complete | `a89d3fc` |
| 2D | Electrophysiology protocol audit | ✓ Complete | `393f2c3` |
| 2E | Held-out FINEST evaluation (perisomatic) | ✓ Complete | `cb54d0f` |
| 2F | Recording-only COARSE–FINEST excitability analysis | ✓ Complete | `1103ea7` |
| 2G-A | All-active model readiness | ✓ Complete | `46f5500` |
| 2G-B | All-active model execution (two axon branches) | ✓ Complete | `54b4326` |
| 2G-C | All-active excitability mapping | ✓ Complete | `d04b13e` |
| 3 | Four-population perisomatic execution | 🔲 Planned |  |
| 4 | FHN fitting and held-out evaluation | 🔲 Planned |  |
| 5 | Cross-population comparison and report | 🔲 Planned |  |

---

## Key Phase 0C findings (2026-11-07)

**16 candidates selected — 4 per population, all at 200 kHz, all spiny excitatory.**

| Metric | Count |
|--------|------:|
| Fit descriptors downloaded and parsed | 16/16 |
| Descriptors classified as perisomatic | 16/16 |
| Candidates with identifiable fitting sweep | 13/16 |
| Candidates with leakage-safe held-out split | 13/16 |
| Candidates potentially executable (L7) | 13/16 |
| Candidates actually executed (L8) | 1/16 |
| Candidates validated against recording | 0/16 |

Three candidates (C rank 4, D rank 2, D rank 4) have fitting sweep numbers in
their descriptors that do not map to the Allen sweep inventory. Their held-out
status is UNRESOLVED rather than failed.

### Selected specimen IDs

| Pop | Spec 1 | Spec 2 | Spec 3 | Spec 4 |
|-----|--------|--------|--------|--------|
| A (L4) | 484564503 | 485931158 | 468193142 | 320207387 |
| B (L2/3) | 318808427 | 476087653 | 485468180 | 382982932 |
| C (L5) | 471129934 | 488679042 | 476048909 | 471767045 |
| D (L6a) | 471786879 | 471819401 | 471789504 | 466632464 |

---

## Key Phase 2G-C findings

The all-active model for specimen 382982932 (L2/3) was executed with two axon
configurations:
- **Stub axon:** silent over 10–270 pA (no spikes in range)
- **Truncated axon:** rheobase interval (170, 190] pA
- **Recorded neuron:** rheobase interval (110, 130] pA

The two axon configurations produce materially different excitability. Neither
can be claimed as the original fitted configuration. The published parameter set
is not reproducible without knowing the axon treatment used during fitting.

---

## Dataset

- **Source:** Allen Cell Types Database (Allen Institute for Brain Science)
- **Specimens:** 1,588 VISp mouse neurons total; 194 with biophysical models
- **Protocol:** Long-square current-clamp (`C1LSCOARSE150216`, `C1LSFINEST150112`)
- **Sampling rates:** 50 kHz or 200 kHz (all 16 selected candidates are 200 kHz)
- **Models:** Perisomatic biophysical (template 329230710)

---

## Repository structure

```
data/
  metadata/           Allen RMA inventory CSVs (cell, sweep, model)
  nwb_cache/          Downloaded NWB files (git-ignored; not committed)
docs/                 Project documentation
results/
  dataset_inventory/  Phase 0/0B/0C audit outputs and reports
  phase1/             NWB validation reports
  phase2/             Model execution reports
scripts/              Analysis and validation scripts
src/data_audit/       Core audit modules
tests/                Pytest test suite (335 tests)
tmp/                  Working outputs (git-ignored)
```

---

## Running the tests

```bash
python -m pytest tests/ -q
```

All 335 tests pass on Python 3.14 with pytest ≥ 9.1.

---

## Reproducibility notes

1. **NWB files** are not committed (large binaries). They are downloaded
   from `http://api.brain-map.org/api/v2/well_known_file_download/<id>`.
2. **Model execution** (Phases 2C, 2G-B, 2G-C) requires NEURON 8.x and
   AllenSDK 2.16.2 in a Linux environment. The Windows environment supports
   all data-audit and analysis phases.
3. **Fit descriptors** are cached in `tmp/fit_cache/` (git-ignored).
4. **Phase 0C** can be re-run with: `python src/data_audit/selected_model_readiness.py`

---

## Scientific limitations

- No model has been validated against its own recording (L8=0).
- Three D-group candidates have unmapped fitting sweeps.
- One L2/3 candidate (382982932) has a reconstruction mismatch.
- The all-active model axon configuration was not published by Allen; the
  two tested configurations give qualitatively different excitability.
- Layer identity is anatomically confirmed; projection class (IT/ET/PT/CT)
  is not available in the Allen database and is not claimed.

---

## Citation

Allen Institute for Brain Science. Allen Cell Types Database. Available from:
https://celltypes.brain-map.org/

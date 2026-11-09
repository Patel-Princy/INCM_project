# Results and Limitations

**Status as of 2026-11-07 (commit `b435abb`)**

This document summarises all completed quantitative results. Because the full
experiment has not been completed, this is a **validated interim report**,
not a finished study.

---

## 1. Completed results

### 1.1 Dataset inventory (Phase 0)

**Source:** Allen Cell Types Database, November 2026 snapshot.

| Quantity | Value |
|----------|------:|
| VISp mouse specimens total | 1,588 |
| Specimens with long-square current-clamp data | 1,585 |
| Specimens with ≥ 2 distinct depolarising amplitudes | 1,585 |
| Specimens with any biophysical model | 194 |
| Specimens with perisomatic model | 184 |
| Specimens with all-active model | 99 |
| Specimens with both model classes | 88 |

**OBSERVED** from committed inventory CSVs.

### 1.2 Four-population feasibility (Phase 0B)

| Pop | Layer | Final eligible | Spiny eligible | Spiny + perisomatic |
|-----|-------|-------------:|-------------:|-------------------:|
| A | 4 | 63 | 54 | 54 |
| B | 2/3 | 30 | 7 | 6 |
| C | 5 | 79 | 41 | 39 |
| D | 6a | 20 | 8 | 8 |

A four-population layer-defined perisomatic study is feasible. A four-population
projection-defined study is not: the database carries no projection identity field,
and identity-compatible counts are 47/2/15/5 (B fails the 4-neuron target).

**DERIVED** from Phase 0B audit (`0470702`).

### 1.3 Selected candidate readiness (Phase 0C)

All 16 candidates (4 per population) meet the 200 kHz and ≥ 5 distinct amplitude
requirements.

| Asset level | YES | PARTIAL | NO |
|-------------|----:|--------:|---:|
| L1: listed in metadata | 16 | — | 0 |
| L2: fit descriptor parsed | 16 | — | 0 |
| L3: morphology available | 5 (verified) | 11 (reference resolved) | 0 |
| L4: mechanism sources available | 16 | — | 0 |
| L5: reconstruction matches specimen | 15 | — | 1 |
| L6: fitting sweeps identifiable | 13 | — | 3 (unmapped) |
| L7: potentially executable | 13 | — | 3 |
| L8: executed and validated | 0 (validated) | 1 (executed, not compared) | 15 |

**OBSERVED** from Phase 0C outputs (`b435abb`).

Held-out feasibility: 13/16 RESOLVED_LEAKAGE_SAFE, 3/16 UNRESOLVED.

### 1.4 Perisomatic model execution (Phase 2C)

**Specimen:** 382982932 (L2/3, Nr5a1-Cre). **Model:** perisomatic 473862496.
**Calibration sweep:** 38 (COARSE, +170 pA, 1000 ms).

| Quantity | Simulation | Recording | Difference |
|----------|----------:|----------:|----------:|
| Spike count in-step | 12 | 12 | 0 |
| First spike latency | 1059.60 ms | 1059.21 ms | +0.39 ms |
| AP amplitude | +37.80 mV | +32.00 mV | +5.8 mV overshoot |
| AHP amplitude | −84.16 mV | −81.16 mV | −3.0 mV undershoot |
| Voltage RMSE (whole trace) | — | — | 4.456 mV |
| Voltage RMSE (baseline only) | — | — | 0.327 mV |
| Trace correlation | — | — | 0.9314 |
| Post-step anomalous spikes | 0 | 2 | +2 in recording |

**OBSERVED** from Phase 2C report (`a89d3fc`).

The two post-step spikes in the recording are genuine biological events rising
from ~−80 mV after the current step ended. The model correctly does not produce
them (they are absent from the FINEST recordings in Phase 2E).

**Status:** execution confirmed; model not validated on independent conditions.

### 1.5 Held-out evaluation (Phase 2E)

**Held-out block:** FINEST (`C1LSFINEST150112`), sweeps 49–52, +170 pA.

| Quantity | Simulation (mean) | Recording (mean) |
|----------|------------------:|-----------------:|
| Spike count | 12 | 1 |
| Verdict | — | MISMATCH |

The perisomatic model trained on the COARSE +170 pA sweep predicts 12 spikes on
the FINEST +170 pA sweep but the recording shows only 1 spike. **The mismatch is
in the biology, not the pipeline**: Phase 2F established that COARSE and FINEST
recordings use bit-identical stimulus arrays, and the 12→1 difference is a
within-recording protocol-history effect (prior adaptation in the FINEST
recording).

**OBSERVED** from Phase 2E report (`cb54d0f`), Phase 2F analysis (`1103ea7`).

### 1.6 All-active model excitability (Phase 2G-C)

**Specimen:** 382982932 (L2/3). **Model:** all-active 497233292.
Two axon treatments tested: stub and truncated.

| Quantity | Stub axon | Truncated axon | Recording (COARSE) |
|----------|----------:|:--------------:|-------------------:|
| Rheobase interval | > 270 pA (silent) | (170, 190] pA | (110, 130] pA |
| Input resistance (ohmic slope) | 44.9 MΩ | 84.5 MΩ | not measured here |
| Spike count at +270 pA | 0 | 26 | 32 |

The two axon configurations give qualitatively different excitability. Neither
matches the recording rheobase. The published parameters are insufficient for
execution without knowing the original axon treatment.

**OBSERVED** from Phase 2G-C report (`d04b13e`).

---

## 2. Not yet completed

The following results have not been produced:

| Item | Reason |
|------|--------|
| L8 execution for 15/16 candidates | Requires Linux environment + NEURON |
| Simulation–recording comparison for all 16 | Requires L8 first |
| FHN parameterisation for any candidate | Not implemented |
| F-I curve comparison (detailed vs FHN) | Requires FHN implementation |
| Cross-population comparison | Requires per-population results |
| Adaptation index comparison | Requires per-neuron execution |
| Spike shape comparison | Not applicable to FHN; detailed model pending |

---

## 3. Scientific limitations

### 3.1 Model provenance

- **One calibration sweep per model.** Allen's perisomatic fit uses a single
  long-square sweep. The model is not constrained by other amplitude responses.
- **Axon configuration unknown.** Phase 2G-C showed this is consequential; the
  perisomatic model is less sensitive to this than the all-active model, but it
  remains an unquantified uncertainty.
- **Reconstruction mismatch in 1/16 candidates.** Specimen 382982932 uses a model
  fitted on reconstruction 491771090 but the specimen's own reconstruction is
  674389884.

### 3.2 Data quality

- **Protocol-history effects.** The COARSE→FINEST mismatch in Phase 2E is a
  within-recording biological effect. Model evaluation must account for sweep
  order and protocol history; this is not yet implemented.
- **Conversion conflict in C representative.** Specimen 471129934 declares an
  incorrect `conversion` attribute in its NWB file. Unit-only reading is correct;
  any code applying the declared conversion will produce wrong amplitudes.
- **Three candidates have unmapped fitting sweeps** (D2, D4, C4). The held-out
  split is UNRESOLVED for these; they cannot be used in a leakage-safe evaluation
  without direct NWB inspection.

### 3.3 Interpretation

- **Small sample.** 4 neurons per layer. No population-level statistical claims
  are supportable.
- **Layer ≠ projection class.** No IT/ET/PT/CT labels are supported by the data.
- **One specimen cannot represent a layer.** The Phase 2C/2E results are for
  specimen 382982932 only; they describe that neuron, not L2/3 neurons in general.
- **Detailed model accuracy ≠ biological ground truth.** The perisomatic model is
  a published biophysical fit, but it is not the cell — it is a model of the cell
  fitted to one sweep.

---

## 4. Next steps required to finish the research

1. **Execute L7-ready candidates in Linux/NEURON environment** (13 candidates,
   one per population minimum).
2. **Compare simulated vs recorded responses** (L8) for each executed candidate.
3. **Resolve three unmapped fitting sweep candidates** by direct NWB inspection.
4. **Download and checksum morphology SWC files** for 11 REFERENCE_RESOLVED
   candidates.
5. **Implement FHN model** with a fitting interface accepting calibration sweeps.
6. **Fit FHN to calibration sweeps** and evaluate on held-out conditions.
7. **Produce F-I, rheobase, latency, adaptation, and subthreshold comparisons**
   for detailed model vs recording vs FHN.
8. **Cross-population comparison** after per-population results are available.
9. **Extend to all 13+ leakage-safe candidates** after validating one per
   population.

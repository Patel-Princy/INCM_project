# Dataset and Model Selection

## 1. Data source

Allen Cell Types Database, Allen Institute for Brain Science.
URL: https://celltypes.brain-map.org/
API: http://api.brain-map.org/api/v2/data (RMA v2)

All data were downloaded via the public API in November 2026.

---

## 2. Specimen eligibility

### 2.1 Scope

- Species: *Mus musculus* (house mouse)
- Region: VISp (primary visual cortex), identified by `structure_acronym` starting
  with `VISp`
- Layers: 4 (population A), 2/3 (population B), 5 (population C), 6a (population D)

### 2.2 Minimum eligibility requirements (Phase 0 PASS rule)

1. Long-square current-clamp recording present
2. At least 6 long-square sweeps
3. At least 3 depolarising sweeps (amplitude > 0 pA)
4. At least 2 distinct depolarising amplitudes
5. Biophysical model listed (perisomatic or all-active)
6. Model download reference resolved
7. NWB file reference resolved

All 1,588 VISp mouse specimens were assessed; 194 pass all criteria across the
four layers.

### 2.3 Units-aware rule

Allen's `stimulus_units` field is a campaign marker, not a guaranteed unit label.
Phase 1B validated that specimens with `stimulus_units='pA'` and a null
`clamp_mode` are current-clamp recordings with picoampere amplitudes. The rule:

```
current_clamp = (clamp_mode == 'current_clamp')
             OR (clamp_mode is null AND stimulus_units == 'pA')
```

This recovers 160 specimens with implicit clamp mode. All 160 have zero
biophysical models and are excluded before the model gate.

---

## 3. Population definitions

| Pop | Layer field | Dendrite | Model requirement |
|-----|-------------|----------|-------------------|
| A | `cortical_layer = '4'` | spiny | perisomatic |
| B | `cortical_layer = '2/3'` | spiny | perisomatic |
| C | `cortical_layer = '5'` | spiny | perisomatic |
| D | `cortical_layer = '6a'` | spiny | perisomatic |

Layer 6b is excluded: all 48 L6b specimens have zero biophysical models.
Aspiny and sparsely spiny cells are excluded as putative inhibitory neurons.

### 3.1 Eligible counts (Phase 0B)

| Pop | Layer final eligible | Spiny final | Spiny + perisomatic |
|-----|--------------------:|------------:|--------------------:|
| A | 63 | 54 | 54 |
| B | 30 | 7 | 6 |
| C | 79 | 41 | 39 |
| D | 20 | 8 | 8 |

---

## 4. Candidate selection (Phase 0C)

Four candidates were selected per population by applying the brief's seven
priorities in cascade order:

1. Correct layer + spiny dendrite (hard gate)
2. Perisomatic biophysical model (hard gate)
3. Model reconstruction matches specimen reconstruction (prefer YES)
4. At least 5 distinct depolarising amplitudes (prefer ≥ 5)
5. 200 kHz sampling rate (prefer 200 kHz over 50 kHz)
6. At least 6 long-square current-clamp sweeps (prefer more)
7. NWB reference, fit file id, morphology reference resolved (hard gate)

Tie-breaking: more distinct amplitudes > more sweeps > lower specimen id.

### 4.1 Selected candidates

| Pop | Rank | Specimen | Driver | Distinct amps | Recon match | Tier |
|-----|-----:|----------|--------|-------------:|-------------|------|
| A | 1 | 484564503 | Rorb-IRES2-Cre | 23 | YES | PRIMARY |
| A | 2 | 485931158 | Rorb-IRES2-Cre | 20 | YES | PRIMARY |
| A | 3 | 468193142 | Scnn1a-Tg3-Cre | 20 | YES | PRIMARY |
| A | 4 | 320207387 | Scnn1a-Tg3-Cre | 19 | YES | PRIMARY |
| B | 1 | 318808427 | Nr5a1-Cre | 14 | YES | PRIMARY |
| B | 2 | 476087653 | Nr5a1-Cre | 13 | YES | PRIMARY |
| B | 3 | 485468180 | Nr5a1-Cre | 6 | YES | PRIMARY |
| B | 4 | 382982932 | Nr5a1-Cre | 17 | NO | CONDITIONAL |
| C | 1 | 471129934 | Rbp4-Cre_KL100 | 24 | YES | PRIMARY |
| C | 2 | 488679042 | Rorb-IRES2-Cre | 23 | YES | PRIMARY |
| C | 3 | 476048909 | Rorb-IRES2-Cre | 20 | YES | PRIMARY |
| C | 4 | 471767045 | Rbp4-Cre_KL100 | 20 | YES | PRIMARY |
| D | 1 | 471786879 | Ntsr1-Cre_GN220 | 19 | YES | PRIMARY |
| D | 2 | 471819401 | Ntsr1-Cre_GN220 | 18 | YES | PRIMARY |
| D | 3 | 471789504 | Ntsr1-Cre_GN220 | 16 | YES | PRIMARY |
| D | 4 | 466632464 | Ntsr1-Cre_GN220 | 16 | YES | PRIMARY |

### 4.2 Identity annotations

No projection class is confirmed. Identity confidence is annotated for
provenance tracing only:

| Pop | Most common annotation | Basis |
|-----|----------------------|-------|
| A | PROBABLE (L4 excitatory) | Layer 4 + spiny + L4 Cre line (Rorb, Scnn1a, Nr5a1) |
| B | LAYER-ONLY | Nr5a1-Cre is an L4 marker used in L2/3; no IT-specific line present |
| C | PROBABLE (L5 excitatory) | Layer 5 + spiny + Rbp4 or Rorb line |
| D | PROBABLE (L6a excitatory) | Layer 6a + spiny + Ntsr1-Cre_GN220 |

**Not claimed:** IT (intratelencephalic), ET (extratelencephalic), PT (pyramidal
tract), CT (corticothalamic), spiny stellate, star pyramidal.

---

## 5. Model selection

Model class: perisomatic biophysical.
Template id: `329230710`.

For each selected specimen, one perisomatic model was identified from
`model_inventory.csv`. The model is identified by template id (never by
`well_known_file_type_id`, because the fit JSON and GLIF configurations share a
file type).

### 5.1 Fit descriptor structure (OBSERVED across all 16 candidates)

- `passive`: list of one dict with `ra`, `cm` (section-level list), `e_pas`
- `fitting`: list with `junction_potential = -14.0 mV` and `sweeps = [single sweep number]`
- `conditions`: list with `celsius = 34.0`
- `genome`: list of dicts with `section`, `name`, `value` (float), `mechanism`

All fitting sweeps use a single COARSE long-square sweep as the calibration
condition. Junction potential of −14.0 mV is applied at output only (written
voltage = simulated voltage + 14 mV); no parameter is modified.

### 5.2 Mechanisms (perisomatic template set)

All 16 perisomatic candidates use the same mechanism set:
`CaDynamics`, `Ca_HVA`, `Ca_LVA`, `Ih`, `Im_v2`, `K_T`, `Kd`, `Kv2like`,
`Kv3_1`, `SK`, `NaV`, `g_pas` (passive conductance).

Mechanism sources are available in `tmp/model_cache/allensdk/modfiles/` and were
validated by Phase 2C execution.

---

## 6. Calibration and held-out split design

| Condition | Definition |
|-----------|-----------|
| Calibration | The single sweep listed in `fitting[0].sweeps` of the fit descriptor |
| Held-out | All other depolarising sweeps |
| Leakage-safe | At least 2 held-out amplitudes not present in the calibration set |

The COARSE protocol provides the calibration condition; the FINEST protocol
provides the held-out protocol family. This is a **protocol-family split**,
which tests generalisation across recording protocols rather than amplitude
extrapolation alone.

13 of 16 candidates are leakage-safe. The 3 exceptions have unmapped fitting
sweep numbers (the sweep id in the fit descriptor does not appear in the sweep
inventory) and are marked UNRESOLVED pending direct NWB inspection.

# Phase 2C — Isolated Perisomatic Model Execution Validation

**Repository:** `Patel-Princy/INCM_project`  **Branch:** `ashish-work`
**Specimen:** `382982932` (mouse VISp, L2/3, `Nr5a1-Cre;Ai14-177333.03.01.01`)
**Model:** perisomatic `473862496`  **Sweep executed:** `38` only
**Reference stack:** AllenSDK `v2.16.2` (from source), NEURON `8.2.7`
**Predecessors:** `results/phase2/PHASE2A_MODEL_EXECUTION_READINESS.md`,
`results/phase2/PHASE2B_GEOMETRY_AND_MANIFEST_AUDIT.md`
**Validation script:** `scripts/validate_perisomatic_execution.py`

---

## 1. Executive verdict

**EXECUTION COMPLETED WITH WARNINGS.**

The perisomatic model `473862496` for specimen `382982932` was executed against
sweep 38 in an isolated Linux environment, and the output was independently
inspected against the recording. **The simulation genuinely ran**: NEURON
integrated 1,604,001 samples in 9.3 s, AllenSDK's own `runner` wrote a new NWB,
and every number below was read back out of that written file rather than
predicted.

**Fifty of fifty numerical pipeline checks passed** — inputs, mechanism
compilation, model dispatch, time base, units, the junction-potential convention,
sample integrity, and the write path. Sixteen of sixteen compiled mechanisms
loaded. The junction convention was verified exactly: `written = (V_sim + 14 mV)`
to `max |Δ| = 0.0 V`, applied at output only, with the raw simulator vector left
at its unshifted value (−94.869 mV) and no change to the input recording or to any
fitted parameter.

**The warnings are real and are not papered over.** The recorded sweep differs
from the simulation in a way that is now precisely localised:

1. **Inside the 170 pA step the spike counts agree exactly — 12 versus 12.** The
   first spike lands within **0.39 ms** of the recording (1059.60 vs 1059.21 ms).
2. **The recording contains two further action potentials that the model does
   not and should not produce.** They occur at **5514.0 and 5521.3 ms**, which is
   **3.49 s after the current step ended**, when the command current is
   **exactly 0.000 pA** and the trace has already returned to −80.6 mV. Each is
   a full-amplitude spike (~1.1–1.2 ms wide, reaching +28.75 mV) rising from
   rest, and they arrive as a **doublet 7.24 ms apart**. These two events are the
   whole of the 14-versus-12 spike-count discrepancy.
3. **Amplitude agreement is imperfect but coherent.** Baseline agrees to
   **+0.137 mV**; the model overshoots the action potential by **5.8 mV**
   (+37.80 vs +32.00 mV) and undershoots the afterhyperpolarisation by about
   **3.0 mV** (−84.16 vs −81.16 mV). Voltage RMSE is **4.456 mV** over the whole
   sweep, **0.327 mV** in the stimulus-free baseline and **11.126 mV** during the
   step. Trace correlation is **0.9314**.
4. **The model's firing is too regular.** Mean interspike interval is 84.95 ms
   (model) versus 81.51 ms (recording) — close — but the recording contains a
   single 114.7 ms gap the model never reproduces, and the model settles onto a
   ~92 ms plateau when the recording continues to fluctuate between 80 and 95 ms.

The toolchain substitution was independently controlled. **Allen's own
perisomatic regression assertion reproduces exactly in this environment: 27
spikes against Allen's documented 27** (§3.5). That control is the reason the
NEURON `8.2.7` substitution is classified as non-material for this code path
rather than left as an open numerical risk.

**What this does and does not settle.** It settles that the execution pipeline is
reproducible and numerically trustworthy: the same assets, the same code, the
same convention, and the same answers, given a documented environment. It does
**not** establish biological validity, because sweep 38 is the model's in-sample
fitting sweep, and it is additionally the sweep that Phase 1C flagged as a
recording anomaly. Nothing here should be read as a held-out prediction.

---

## 2. Scope of what was executed

| Item | Status |
|---|---|
| Perisomatic model `473862496`, specimen `382982932` | executed |
| Sweep `38` (COARSE, +170 pA) | executed — the only sweep run |
| All-active model `497233292` | **not executed** |
| Sweeps `24`–`43` other than `38` | **not executed** |
| FINEST trials (`49`–`52`) | **not executed** |
| FHN model | **not executed** |
| Parameter fitting / optimisation (`deap`, `optimize.py`) | **not executed** |
| Held-out evaluation | **not executed** |
| Allen's perisomatic fixture, specimen `491120155` | executed as an **environment control only** (§3.5) |
| Published descriptor, fit parameters, manifest drafts | **unmodified** |
| AllenSDK source | **unmodified** — 885/885 `.py` files byte-identical to the release tarball |

---

## 3. Environment

### 3.1 Isolation

WSL2 with an already-installed Ubuntu distribution was available, so Phase 2C was
not blocked at Step 1. **No Windows feature was enabled, no distribution was
installed, no BIOS setting was changed, and no system-level change was made.**
The environment is entirely user-scoped because `sudo` requires a password in
this distribution and was therefore never used.

| | |
|---|---|
| Host distro | Ubuntu 26.04 LTS (WSL2, pre-existing) |
| Kernel | `6.18.33.1-microsoft-standard-WSL2` |
| Cores | 16 |
| Compiler | `gcc (Ubuntu 15.2.0-16ubuntu1) 15.2.0` |
| Make | GNU Make 4.4.1 |
| Provisioner | `uv 0.13.7` → standalone CPython, no `sudo`, no `apt` |
| venv | `~/incm_phase2c/venv` (outside the repository) |
| Model workspace | `~/incm_phase2c/model` (outside the repository) |

NEURON was **not** installed on native Windows. The existing Windows Python
environment was **not** modified. Neither the venv nor the model workspace is
inside the repository or under Git tracking.

### 3.2 Exact versions

| Component | Version |
|---|---|
| Python | **3.11.18** |
| NEURON | **8.2.7** |
| AllenSDK | **2.16.2** (imported from the extracted release source tree; *not* pip-installed) |
| NumPy | **1.23.5** |
| SciPy | **1.10.1** |
| pandas | **1.5.3** |
| h5py | 3.10.0 |
| scikit-image | 0.21.0 |
| argschema | 3.0.4 |
| simplejson | 3.19.1 |
| pynwb | 2.2.0 |
| hdmf | 3.4.7 |
| SimpleITK | 2.3.1 |
| xarray | 2022.12.0 |
| six | 1.16.0 |
| setuptools | 69.5.1 |

Python 3.11 is the faithful choice, not an arbitrary one. AllenSDK `2.16.2`
requires `numpy<1.24`, `pandas==1.5.3` and `scipy<1.11`; the newest CPython that
all three still ship wheels for is 3.11, and NEURON `8.2.7` is the last `8.2.x`
release with a `cp311` manylinux wheel. Choosing a newer interpreter would have
forced a NumPy upgrade and violated AllenSDK's own constraint.

**NEURON is the one substitution.** AllenSDK `v2.16.2` does not pin NEURON at all
— `requirements.txt` contains no `neuron` entry, so Allen's fitting
interpreter's NEURON build is not recoverable from any published artefact. `8.2.7`
was chosen because it is the newest `8.2.x` with a `cp311` wheel. §3.5 tests
whether that matters.

### 3.3 The dependency closure is wider than the code path, and that is a finding

Step 2 said "install only the dependencies required for this execution". The
literal reading is a biophysics-only set: `numpy`, `scipy`, `pandas`, `h5py`,
`neuron`, `argschema`. **That set cannot import AllenSDK's own NWB reader.**

Runtime evidence, in the order the failures actually occurred:

| Attempt | Failure | Cause |
|---|---|---|
| 1 | `ModuleNotFoundError: SimpleITK` | `allensdk/core/__init__.py` → `_data_object_base.data_object` → `brain_observatory.comparison_utils` |
| 2 | `ModuleNotFoundError: pynwb` | `allensdk/core/_data_object_base/readable_interfaces.py:3` |
| 3 | `ModuleNotFoundError: simplejson` | `allensdk/core/json_utilities.py:40` |

The mechanism is an import side effect, not a code dependency: `from
allensdk.core.nwb_data_set import NwbDataSet` executes
`allensdk/core/__init__.py`, which imports `DataObject`, `readable_interfaces`
and `writable_interfaces`, which drag in the Brain Observatory comparison module
(SimpleITK, xarray) and PyNWB (hdmf). None of that code is ever called by a
biophysics simulation. **It cannot be avoided without patching AllenSDK source,
which Phase 2C forbids.** Four packages were therefore installed beyond the
code-path minimum — `simpleitk 2.3.1`, `xarray 2022.12.0`, `pynwb 2.2.0`,
`hdmf 3.4.7` — every one of them listed in AllenSDK's own `requirements.txt`, with
`hdmf` pinned to `3.4.7` to respect that file's
`hdmf!=3.5.*,!=3.6.*,!=3.7.*,!=3.8.*` exclusion.

This also corrects a plausible but wrong assumption: a project that only needs
the biophysical runner cannot vendor a trimmed AllenSDK by deleting the
`brain_observatory` package. The import graph forbids it.

The closure was then computed properly rather than discovered one error at a
time. A transitive walk from the five entry points we import
(`runner`, `utils`, `nwb_data_set`, `extract_cell_features`, `ephys_features`)
reaches **26 AllenSDK modules** and these third-party names:

```
argschema, h5py, neuron, nrn, numpy, pandas, scipy, simplejson, six, skimage,
pkg_resources
```

`ConfigParser`, `urllib2` and `urlparse` also appear but are Python-2 fallback
names inside `try/except ImportError` blocks
(`config/app/application_config.py`, `core/json_utilities.py`) and are inert on
3.11. `nrn` is not a missing package: NEURON installs it on import, and
`hoc_utils.HocUtils.__init__` imports `neuron` before `nrn`, so the ordering is
correct by construction.

### 3.4 AllenSDK integrity

AllenSDK was **not** pip-installed and **not** patched. It is imported from the
extracted `AllenSDK-2.16.2.tar.gz` by putting the source tree on `sys.path`, so
the executed code is exactly the tagged release. This was verified
cryptographically rather than assumed:

```
archived .py files under allensdk/: 885
extracted .py files             : 885
byte-identical to the tarball   : 885
modified                        : 0
missing from the tree           : 0
extra (not in the tarball)      : 0
__pycache__ directories removed : 5
__pycache__ remaining           : 0
VERDICT: AllenSDK source unmodified
```

Exploratory imports had left five `__pycache__` directories inside the source
tree; they were removed so the reference tree is pristine again. The deliverable
script and the control both run with `PYTHONDONTWRITEBYTECODE=1`.

### 3.5 Environment control — Allen's own perisomatic assertion

`allensdk/test/model/peri_model/test_biophysical_peri.py` is Allen's regression
test for the perisomatic model family. It is **not** this specimen and **not**
sweep 38: it drives a hardcoded 350 pA step (delay 1000 ms, duration 1000 ms,
`tstop` 3000 ms) into specimen `491120155` and asserts

```python
assert num_spikes == 27  # taken from the web app
```

It exercises the same perisomatic loader, the same 16 mechanisms, the same HOC
files and the same junction convention as sweep 38, and it needs nothing that
does not ship in the release. It is therefore the only published numerical anchor
available for the toolchain, and it was run **solely to test whether the NEURON
substitution changed the simulation path** — not as a model evaluation. The
fixture was copied out of the source tree first, so compiling its mechanisms
could not disturb the 885/885 verification in §3.4.

```
control specimen          : 491120155 (Allen's fixture, not 382982932)
control stimulus          : 350 pA, delay 1000 ms, dur 1000 ms, tstop 3000 ms
junction potential        : -14 mV
samples recorded          : 120001
voltage range (shifted)   : -76.18 .. 40.66 mV
spikes detected           : 27
Allen's asserted value    : 27

CONTROL: Allen's perisomatic reference assertion reproduces
```

**It reproduces exactly.** This is the strongest single piece of evidence in the
report: the perisomatic simulation path on NEURON 8.2.7 returns Allen's own
published answer, so the one unavoidable substitution did not move the result.
Note the division of labour — the control validates loading, compilation,
morphology and the junction convention through `Utils` directly, while sweep 38
validates the `runner` / manifest / NWB-write path the control bypasses.
Together they cover the chain; neither alone does.

---

## 4. Input verification (Step 3)

All checks below were recomputed from the staged files, not taken on trust, and
all passed.

### 4.1 Asset digests

| Asset | Bytes | SHA-256 | Matches |
|---|---|---|---|
| `382982932_fit.json` (published fit descriptor) | 2 891 | `d24d00aaed5a2a0e…f95b00a8e38f` | Phase 2A |
| `674389901_382982932_m.swc` (reconstruction `674389884`) | 335 924 | `71bb551b6ed6ce2f…56631ef36c` | Phase 2A |
| `674389910_382982932_m.marker` (WKF `674389910`) | 373 | `3cc83ad85e7caebd…890980925` | Phase 2B |
| `382982932.nwb` (validated specimen recording) | 94 207 824 | `d38b43fcbdf1c88d…598f237b63` | Phase 1C |
| `manifest.json` (Phase 2B draft) | 2 983 | `93ef8ca022cea0b1…b761692b0` | Phase 2B |
| 16 `.mod` sources | — | all 16 match | Phase 2A |
| `libnrnmech.so` (built here) | 149 016 | — | produced in-run |
| `work/382982932.nwb` (simulation output) | 95 166 399 | — | produced in-run |

The descriptor is **byte-identical** to the published descriptor
(`d24d00aa…`), so Step 3's "do not modify the descriptor or fit parameters" holds
by construction. The NWB digest and byte count match the validated recording
identified in Phase 1C, so the recording used is the documented one and not a
re-download. No NWB was downloaded and no model asset was replaced.

### 4.2 Descriptor and manifest

| Check | Result |
|---|---|
| Descriptor sections | `conditions`, `fitting`, `genome`, `passive` — Allen's four |
| Model id | perisomatic `473862496` |
| Junction potential | **−14 mV** |
| Fitting sweep list | `[38]` — sweep 38 only |
| Genome | 16 entries, all floats (perisomatic form) |
| Mechanisms referenced | 11: `CaDynamics, Ca_HVA, Ca_LVA, Ih, Im, K_P, K_T, Kv3_1, NaTs, Nap, SK` |
| Passive keys | `cm`, `e_pas`, `ra` |
| Manifest `biophys` entries | exactly one |
| Manifest `model_type` | `Biophysical - perisomatic` |
| `axon_type` authored in manifest | **absent**, as Phase 2B requires |
| `runs[0].sweeps` | 20 sweeps (24–43), includes 38 |
| `runs[0].sweeps_by_type` | present, 9 types |

Every mechanism the descriptor references has a corresponding `.mod` source; all
16 required sources are present (one more than the 11 used, which is expected —
the same module set serves both model classes).

### 4.3 Sweep 38 stimulus structure — a correction worth recording

Sweep 38 is **not** a single current step. Segmenting the command current
revealed two contiguous non-zero runs:

| Segment | Indices | Window | Duration | Amplitude |
|---|---|---|---|---|
| Access-resistance test pulse | 1 000–3 000 | 5.000–15.005 ms | 10.0 ms | **+50 pA** |
| Current step (the fitting step) | 204 000–403 999 | **1020.000–2020.000 ms** | **1000.0 ms** | **+170.000 pA** |

Treating every non-zero sample as "the step" — the obvious first implementation —
conflates the two and reports the test pulse's onset (5 ms) as the stimulus onset
and a 1010 ms duration. Both were wrong. The corrected values (1020 ms onset,
1000 ms duration) agree with Phase 1C's independently derived "step 1.02 s, 1 s",
which is a useful cross-confirmation that the segmentation is right. The
validation script now asserts all three properties.

Other sweep properties: 200 000 Hz, `dt` = 0.005 ms, **1 604 001 samples** =
8020.005 ms, `index_range` `[150000, 1604000]`, recorded baseline over the
stimulus-free pre-step window **−80.828 mV** (201 999 samples), recorded range
**−81.156 … +32.000 mV**, no NaN.

---

## 5. Mechanism compilation (Step 4.1)

Command, run from the model directory in the isolated environment:

```
/home/ashish/incm_phase2c/venv/bin/nrnivmodl modfiles/
rc: 0
--- stdout ---
/home/ashish/incm_phase2c/model
Mod files: "modfiles/modfiles//CaDynamics.mod" "modfiles/modfiles//Ca_HVA.mod"
  "modfiles/modfiles//Ca_LVA.mod" "modfiles/modfiles//Ih.mod"
  "modfiles/modfiles//Im.mod" "modfiles/modfiles//Im_v2.mod"
  "modfiles/modfiles//K_P.mod" "modfiles/modfiles//K_T.mod"
  "modfiles/modfiles//Kd.mod" "modfiles/modfiles//Kv2like.mod"
  "modfiles/modfiles//Kv3_1.mod" "modfiles/modfiles//NaTa.mod"
  "modfiles/modfiles//NaTs.mod" "modfiles/modfiles//NaV.mod"
  "modfiles/modfiles//Nap.mod" "modfiles/modfiles//SK.mod"

 -> Compiling mod_func.cpp
 => LINKING shared library ./libnrnmech.so
Successfully created x86_64/special

--- stderr ---
(empty)
```

| Property | Value |
|---|---|
| Exit code | **0** |
| Compiler warnings | **0** |
| Compiler errors | **0** |
| Wall time | 0.87 s |
| Artefacts | `x86_64/libnrnmech.so` (149 016 B), `x86_64/special` |
| Mechanisms loadable | **16 / 16** |

Two details that matter for reproducing this later:

1. The `Mod files:` line shows a **doubled path prefix** (`modfiles/modfiles//`).
   This is cosmetic — NEURON resolves the files and all 16 compile — but a reader
   comparing logs against a different NEURON version should not read it as a
   missing directory.
2. The build artefacts land in **`./x86_64/` at the model-directory level, not in
   `modfiles/x86_64/`**. NEURON resolves compiled mechanisms relative to the
   process working directory, so the simulation must run with `cwd` **equal to
   the model directory**. The validation script asserts `cwd` before executing.
   No `load_mechanisms` call and no environment variable is needed; the 16/16
   loadability check confirms auto-loading works, which is what Allen's own test
   relies on.

---

## 6. Manifest and model loading (Steps 3 and 4)

Execution went through AllenSDK's own `runner.run(args, sweeps=[38], procs=1)` —
not through `Utils` directly — because that is the only path that exercises model
dispatch, the `biophys` append in `load_description`, `prepare_nwb_output` and
`save_nwb`. Those were exactly the parts Phase 2B could only validate statically.

| Check | Result |
|---|---|
| `load_description` appended `axon_type` | `biophys` has **2** entries |
| `axon_type` reached `biophys[1]` | `truncated` |
| Model type dispatched to perisomatic loader | `Biophysical - perisomatic` |
| `cwd` is the model directory | `/home/ashish/incm_phase2c/model` |
| `procs` / `sweeps` | `1` / `[38]` |

`axon_type` deserves a note because Phase 2B showed it is the field most easily
misused. `create_utils` reads it unconditionally at line 74 but consumes it only
in the all-active branch:

```python
axon_type = description.data["biophys"][1]["axon_type"]

if model_type == PERISOMATIC_TYPE:
    return Utils(description)          # axon_type discarded
elif model_type == ALL_ACTIVE_TYPE:
    return AllActiveUtils(description, axon_type)
```

So supplying the runner's default `--axon_type truncated` is **provably a no-op
for a perisomatic model**. It was supplied because the signature requires it, it
was not authored into the manifest (which would have shifted the appended entry
to index 2 and misdispatched the model), and it cannot have influenced the
result.

---

## 7. Execution outcome (Step 4.2)

| Property | Value |
|---|---|
| Status | **executed** |
| Exception raised | none |
| NEURON integration time | 9.34 s |
| Wall time incl. setup and NWB write | 11.6 s |
| Output NWB | `~/incm_phase2c/model/work/382982932.nwb`, 95 166 399 B |
| Sweeps written | **1** (sweep 38) |
| `save_nwb` → `extract_sweep_features` | succeeded (12 spike times stored) |

### 7.1 Junction convention applied at output only

`Utils.get_recorded_data` computes `v = (v − junction_potential) × 1e-3`, i.e.
`V_written = V_sim + 14 mV` in volts. This was verified numerically rather than
by inspection, by wrapping `get_recorded_data` in-process for the duration of the
run: the wrapper calls the original unchanged and merely also retains the raw
vector. **Nothing on disk is patched and no model parameter is altered.**

| Check | Measured |
|---|---|
| `written == (V_sim + 14 mV)` | max absolute deviation **0.000e+00 V** |
| Raw vector is unshifted millivolts | raw range −98.16 … +23.80 mV |
| Shift is additive, not a scale factor | peak 23.797 → 37.797 mV |
| Raw and written lengths | 1 604 001 vs 1 604 001 |

The raw simulator resting value is **−94.869 mV**; adding exactly 14 mV gives
−80.869 mV, which is what appears in the file and what agrees with the
recording's −80.828 mV. The offset is applied once, at output. The input
recording was not shifted and no initial condition was adjusted to force
agreement.

---

## 8. Recorded versus simulated comparison (Step 5)

### 8.1 Numerical pipeline agreement — all asserted, all passed

| Check | Result |
|---|---|
| Simulated trace has no NaN or Inf | 1 604 001 samples |
| Simulated length matches recorded length | 1 604 001 vs 1 604 001 |
| Time vector strictly increasing (no duplicated samples) | 1 604 000 intervals |
| Sampling interval uniform | median 0.005000 ms |
| Padding beyond the run is zero, not stale data | 0 padded / 0 zero |
| Simulated trace contains action potentials | max +37.8 mV |
| Resting level agrees within 5 mV | −80.69 vs −80.83 mV |
| NWB-stored spikes match the detector on the written trace | stored 12 vs detected 12 |
| Output NWB inherits the recorded stimulus unchanged | max absolute deviation **0.0e+00 A** |

The last two matter more than they look. The first proves `save_nwb`'s
`extract_sweep_features` call ran and that its output agrees with an independent
pass of the same detector over the written trace — the write path is
self-consistent. The second proves `prepare_nwb_output` carried the command
current across bit-for-bit, so both traces genuinely describe the same stimulus.
Without that, a voltage comparison would be meaningless.

### 8.2 Numerical agreement — reported, not asserted

These are **biological agreement** measurements. They are reported, not gated,
because sweep 38 is the in-sample fitting sweep and Phase 1C documented it as an
anomalous recording. Asserting them would convert an in-sample, known-anomalous
sweep into a pass/fail verdict on the model, which is exactly what Step 5 says
must not happen.

| Metric | Value |
|---|---|
| Voltage RMSE, whole sweep | **4.456 mV** |
| Voltage RMSE, stimulus-free baseline | **0.327 mV** |
| Voltage RMSE, during the step (1020–2020 ms) | **11.126 mV** |
| Voltage RMSE, after the step (2020–8020 ms) | **2.426 mV** |
| Mean absolute error | 1.213 mV |
| Trace correlation | 0.9314 |
| Baseline offset (simulated − recorded) | **+0.137 mV** |
| Voltage range, recorded | −81.16 … +32.00 mV |
| Voltage range, simulated | −84.16 … +37.80 mV |

Reading these together: the baseline is reproduced almost exactly (0.327 mV RMSE,
0.137 mV offset), the gross shape is well captured (r = 0.93), and the residual is
concentrated in two amplitude details — the action potential overshoots by 5.8 mV
and the afterhyperpolarisation undershoots by ~3.0 mV. The 11.1 mV RMSE during
the step is dominated by those per-spike amplitude differences and by the spike
timing offsets in §8.3, not by a drifting baseline.

### 8.3 Spike analysis

Spike counts were produced by Allen's `detect_putative_spikes` — the same
function Allen's own fixture test uses — and cross-checked with an independent
0 mV threshold-crossing detector. **Both detectors agree on both traces**, so the
counts are not an artefact of one method.

| Measure | Simulated | Recorded |
|---|---|---|
| Spikes, whole sweep | 12 | 14 |
| **Spikes inside the step (1020–2020 ms)** | **12** | **12** |
| **Spikes outside the step** | **0** | **2** |
| Threshold-detector count | 12 | 14 |
| Stored in NWB by Allen's writer | 12 | 14 (annotated) |

**Inside the stimulated window the counts agree exactly, and the first spike
lands within 0.39 ms.** Latency from step onset is 39.60 ms (model) versus
39.21 ms (recording).

| # | Recorded (ms) | Simulated (ms) | Δ (ms) |
|---|---|---|---|
| 1 | 1059.21 | 1059.60 | +0.39 |
| 2 | 1098.44 | 1101.54 | +3.10 |
| 3 | 1157.44 | 1160.39 | +2.95 |
| 4 | 1236.93 | 1238.45 | +1.52 |
| 5 | 1312.63 | 1331.32 | +18.70 |
| 6 | 1393.46 | 1429.03 | +35.57 |
| 7 | 1508.13 | 1526.55 | +18.42 |
| 8 | 1587.92 | 1622.65 | +34.73 |
| 9 | 1680.13 | 1717.27 | +37.14 |
| 10 | 1775.23 | 1810.56 | +35.33 |
| 11 | 1869.87 | 1902.74 | +32.88 |
| 12 | 1955.81 | 1993.99 | +38.18 |
| — | **5514.05** | — | **no model spike** |
| — | **5521.29** | — | **no model spike** |

Median paired offset **+25.8 ms**, maximum |Δ| **38.2 ms**. The model's spikes
drift progressively late because its interspike intervals settle onto a ~92 ms
plateau, whereas the recording's intervals fluctuate:

| | Mean ISI | Range |
|---|---|---|
| Recorded (first 12) | 81.51 ms | 39.2 – **114.7** ms |
| Simulated | 84.95 ms | 42.0 – 97.7 ms |

Mean rate is therefore close (12.3 vs 11.8 Hz) while the model is markedly more
regular. The single 114.7 ms gap in the recording — between the 6th and 7th
spikes — has no counterpart in the model, and it is the main reason the timing
offset grows past spike 5.

### 8.4 The two events that account for the entire discrepancy

The 14-versus-12 count difference is **entirely** two action potentials in the
recording that lie outside the stimulus window. They were characterised
explicitly, because the interpretation depends on where they fall:

| Property | Value |
|---|---|
| Times | **5514.0 ms and 5521.3 ms** |
| Time after the step ended (2020 ms) | **+3.49 s** |
| Command current in that window | **0.000 pA** |
| Baseline immediately before | **−80.6 mV** (resting) |
| Peak reached | **+28.75 mV** |
| Width above −20 mV | 1.22 ms and 1.11 ms |
| Separation (doublet interval) | **7.24 ms** |
| Post-step excursions above −20 mV, model | **0** |
| Post-step excursions above −20 mV, recording | **2** |

These are not small depolarisations or noise: they are full-amplitude action
potentials, ~109 mV peak-to-rest, with a normal spike width, occurring as a
doublet from a resting membrane potential with **zero injected current**, more
than three seconds after the step ended. The trace returns cleanly to −80.69 mV
and stays there to the end of the sweep.

The model produces **zero** events in that window, and that is the correct
behaviour: with no current, an integrate-and-fire-compatible perisomatic model
with a −80.6 mV resting potential does not fire spontaneously. **The model is not
wrong here; the recording contains two events that the stimulus does not explain.**

This is exactly the anomaly Phase 1C flagged from the outside — 14 spikes at
170 pA in this COARSE sweep versus **1 spike** in each of four FINEST sweeps at an
identical 170 pA command and an identical baseline. Phase 1C could not establish
a cause and did not claim one. Phase 2C does not establish one either, but it now
localises the excess: it is **two events in a 7 ms doublet at 5.51 s**, not a
general elevation of excitability. The 12 driven spikes themselves agree in count
with the model.

Note that this does **not** make the COARSE sweep comparable to the FINEST
repeats. Even excluding the two late events, this COARSE sweep fires **12** spikes
at 170 pA where all four FINEST sweeps fire **1**. The discrepancy Phase 1C
identified is therefore at least two separate problems, and only one of them (the
late doublet) is explained away by the timing analysis above.

### 8.5 What these numbers do and do not mean

**Pipeline-level conclusions (asserted, defensible):** the model loads, compiles,
dispatches and integrates; the time base is exact; units and the junction
convention are exact; the stimulus is carried through unchanged; the write path is
self-consistent; and the output is a faithful function of the inputs and the
environment.

**Biological conclusions (reported, deliberately not decided):** on its own
fitting sweep the model reproduces the baseline, the broad response shape and the
driven spike count, while overshooting spike amplitude by ~5.8 mV, undershooting
the AHP by ~3.0 mV, and producing a more regular spike train than the recording.
Whether those differences reflect a limitation of the fitted model, a limitation
of the reconstruction, or a defect in this particular recording **cannot be
resolved from one in-sample sweep**, and Phase 2C makes no claim about it. Any
statement that the model is or is not biologically valid requires the held-out
sweeps that Step 4 explicitly excluded.

---

## 9. Failures, fixes and deviations (Step 6)

Every failure below is preserved with its first actual cause. No fix altered a
fitted parameter, a model assumption, or AllenSDK source.

### 9.1 Environment failures — resolved by dependency installation only

| # | First actual failure | Diagnosis | Narrow fix |
|---|---|---|---|
| 1 | `ModuleNotFoundError: No module named 'SimpleITK'` from `allensdk/core/__init__.py` | environment — import side effect via `brain_observatory.comparison_utils` | installed `simpleitk 2.3.1`, `xarray 2022.12.0` (both in AllenSDK `requirements.txt`) |
| 2 | `ModuleNotFoundError: No module named 'pynwb'` at `_data_object_base/readable_interfaces.py:3` | environment — `from pynwb import NWBFile` | installed `pynwb 2.2.0`, `hdmf 3.4.7` (honouring `hdmf!=3.5.*…!=3.8.*`) |
| 3 | `ModuleNotFoundError: No module named 'simplejson'` at `core/json_utilities.py:40` | environment | installed `simplejson 3.19.1` |
| 4 | `LookupError: 'tstop' is not a defined hoc variable name` | a standalone mechanism probe that had not yet loaded `stdgui.hoc` | expected; the real run loads the HOC files. Probe rewritten to insert/delete per `Section` |
| 5 | `import nrn` reported as missing by static analysis | not a failure — NEURON installs `nrn` on import, and `hoc_utils` imports `neuron` first | none needed; verified empirically |

None of these required changing AllenSDK source. Nothing was silently upgraded:
each package was pinned, and `pandas`, `numpy`, `scipy` stayed at AllenSDK's
required versions throughout.

### 9.2 Defects in the validation script itself — found and fixed before trusting any result

These are recorded because a validation script that is wrong silently converts
into a wrong scientific claim.

| # | Defect | Consequence if unnoticed | Fix |
|---|---|---|---|
| 6 | `detect_putative_spikes` returns **sample indices**, not times. The code multiplied them by `1e3` | spike times inflated ~200× — the first run reported "211842000 ms" instead of 1059.21 ms | map indices through the time vector (`t_n[idx]`) |
| 7 | Stimulus characterised as all non-zero samples | reported onset 5.0 ms and duration 1010 ms, conflating the 50 pA test pulse with the 170 pA step | contiguous-run segmentation; step = largest-magnitude segment (§4.3) |
| 8 | `v_rec * 1e3` passed to a detector documented as taking **mV** | would have silently returned 0 spikes (dv/dt cutoff never reached) | convert volts → mV before detection (caught by reading the docstring, before the first run) |
| 9 | `sys.path.insert` for AllenSDK performed inside `execute()` | `characterise_sweep` imported `allensdk.core` earlier and would fail | moved to `main()` immediately after `chdir` |
| 10 | `len(neuron.h.allsec())` | `TypeError: hoc all section iterator() has no len()` on NEURON 8.2.7 | materialise with `list()` before counting |
| 11 | Spike-count equality asserted as a pipeline check | an in-sample, documented-anomalous sweep would have gated the run, contradicting Step 5 | split into asserted pipeline checks and reported biological metrics (§8.2) |

One investigative dead end is also worth recording so it is not repeated: a
throwaway diagnostic computed its synthetic time base as `1.0e-3/rate` instead of
`1.0/rate`, compressing 8.02 s into 0.008 s, and consequently reported 3 spikes
where the validator correctly reported 14. The discrepancy was resolved by
re-running the detector over the saved time vector rather than by trusting either
number. **The validator was right and the diagnostic was wrong** — which is why
§8.3 reports counts from two independent detectors.

### 9.3 Deviations from a literal reading of the brief

| Deviation | Justification | Material risk |
|---|---|---|
| **NEURON 8.2.7** rather than "Allen's NEURON" | AllenSDK `2.16.2` pins no NEURON version; the fitting build is not recoverable from any published artefact. `8.2.7` is the newest `8.2.x` with a `cp311` wheel | **controlled and shown non-material** for this path — Allen's own 27-spike assertion reproduces (§3.5) |
| Four packages beyond the code-path minimum (`simpleitk`, `xarray`, `pynwb`, `hdmf`) | required by `allensdk.core`'s import side effects; unavoidable without patching source | none on results; documented in §3.3 |
| AllenSDK imported from source tree, not pip-installed | preserves the tagged release exactly and avoids modifying any environment; verified 885/885 byte-identical | none |
| `--axon_type truncated` supplied | `create_utils` reads `biophys[1]['axon_type']` unconditionally; the perisomatic branch discards it | **provably none** — no-op for perisomatic (§6) |
| Allen's fixture executed (§3.5) | the only published numerical anchor for the toolchain; run as a control, copied outside the source tree | none on sweep 38; clearly separated and labelled |

### 9.4 Warnings that remain open

1. **NEURON substitution not tested beyond one anchor.** The control in §3.5
   reproduces Allen's number for a 350 pA step on a different cell. That is strong
   but not exhaustive: a NEURON-version difference could in principle affect
   another amplitude regime without affecting that one.
2. **The two post-step spikes are unexplained.** Localised in time, amplitude and
   separation (§8.4), but no cause is established and none is claimed.
3. **COARSE-versus-FINEST remains a separate, unresolved discrepancy** (12 driven
   spikes here versus 1 in four FINEST repeats at the same command), independent
   of the late doublet.
4. **`save_nwb` calls `extract_sweep_features` outside a `try`/`except`**
   (`runner.py:188`). It succeeded here — 12 spike times were stored — but on a
   sweep where feature extraction raises, the exception would surface *after* the
   voltage had already been written, leaving a partially-written output file. Not
   triggered in this run; recorded because it would corrupt a batch job.
5. **A constant 0.055 ms offset** exists between the spike times Allen's writer
   stores and the detector's threshold crossings on the same written trace
   (e.g. 1059.535 vs 1059.595 ms; identical offset on all 12). It arises inside
   Allen's own `extract_sweep_features` → `s['threshold_t']` path, is 11 samples
   at this rate, and does not affect any count or any voltage comparison. Not
   investigated further because it cannot influence a conclusion here.
6. **`nrnivmodl` logs a doubled `modfiles/modfiles//` path prefix** (§5).
   Cosmetic, but it makes log comparison across NEURON versions misleading.

---

## 10. Does this support pipeline reproducibility? (Step 7.8)

**Yes, for the execution pipeline.** The evidence is of the kind that can be
re-run and compared, not asserted:

* Every input was hashed and matched a previously recorded digest — the descriptor
  byte-for-byte, the NWB against Phase 1C, the 16 `.mod` sources and the
  morphology against Phase 2A.
* AllenSDK source is provably unmodified (885/885 files byte-identical to the
  release tarball).
* All 16 mechanisms compile with zero warnings and zero errors, and all 16 load.
* The full `runner` path executed — dispatch, `biophys` append,
  `prepare_nwb_output`, `save_nwb` — not a shortcut through `Utils`.
* The output convention is exact (`max |Δ| = 0.0 V`), applied once, at output.
* 50/50 numerical checks pass, including sample integrity (no NaN, no duplicates,
  no stale padding), length, uniform sampling, and stimulus identity.
* The output was read back out of the written NWB and compared, not predicted.
* An independent control reproduces Allen's own published assertion exactly.

**The environmental ingredients are also pinned in a way that should reproduce:**
Python 3.11.18, NEURON 8.2.7, NumPy 1.23.5, SciPy 1.10.1, pandas 1.5.3, with
every other package version listed in §3.2 and every pin traceable to AllenSDK's
own `requirements.txt`.

**What is not yet reproducible is the science**, and that distinction is the point
of this phase.

---

## 11. What remains unresolved before held-out evaluation (Step 7.9)

1. **The COARSE/FINEST contradiction.** 12 driven spikes at 170 pA here versus 1
   in each of four FINEST repeats at the same command, the same step and the same
   baseline. Phase 2C localises the *late* excess but does not touch this. Until
   it is resolved, the COARSE block cannot be treated as ground truth for a rate
   comparison, and pooling COARSE with FINEST would inject apparent
   non-monotonicity into any F-I curve.
2. **The two post-step spikes have no explanation.** They are real features of the
   trace (full amplitude, normal width, resting baseline, zero current). Whether
   they are a recording artefact, an unrecorded input, or a genuine spontaneous
   event is undetermined.
3. **Whether NEURON 8.2.7 is adequate across the whole amplitude range.** One
   control at one amplitude on one cell is a single point. A defensible claim
   needs at least a few amplitudes, ideally the ones used for held-out scoring.
4. **The all-active model `497233292` is untouched.** Phase 2B classified it
   UNDER-SPECIFIED, and nothing in Phase 2C changes that.
5. **Mechanism sensitivity is unmeasured.** `Kd`, `Kv2like` and `NaV` are present
   in the module set but not referenced by this descriptor's genome; whether they
   are exercised by the morphology's section-dependent parameterisation was not
   established.
6. **Amplitude-level calibration.** The 5.8 mV overshoot and ~3.0 mV
   undershoot are consistent, systematic, and of the size that would matter for
   spike-threshold or AHP-based features. They were observed on one in-sample
   sweep and must not be corrected for or fitted against.
7. **Sweeps other than 38 have never been executed**, so nothing here establishes
   that the pipeline generalises across the 20 COARSE sweeps, let alone FINEST.

---

## 12. Reproducing Allen's model vs executing an Allen-compatible reconstruction

These are different claims and Phase 2C only supports the second.

**What was not done — reproducing Allen's original fitted model.** That would
require, at minimum, the exact NEURON build Allen's fitting pipeline used (not
published, not pinned anywhere in `v2.16.2`), the exact interpreter and numerical
library stack, and — for a claim about Allen's *results* — the original
`neuronal_model.neuron_reconstruction_id` `491771090`, which Phase 2B established
has no row anywhere in the Allen database, not even as a superseded record. None
of those is recoverable, so exact reproduction of Allen's run is **not** claimed.

**What was done — executing an Allen-compatible reconstruction.** The model was
executed with documented, individually auditable substitutions:

| Element | Allen's original | Used here | Status |
|---|---|---|---|
| Code | AllenSDK at some commit | AllenSDK `v2.16.2` release tarball, byte-identical | documented; verified |
| NEURON | unpinned, unrecoverable | `8.2.7` (newest `8.2.x` with `cp311`) | **substitution**, controlled by §3.5 |
| Python | unrecoverable | `3.11.18`, forced by `numpy<1.24` / `pandas==1.5.3` / `scipy<1.11` | documented |
| Morphology | `491771090` (absent from the database) | `674389884` / WKF `674389901`, the specimen's published reconstruction, resolved by Allen's own `specimen → neuron_reconstructions` rule | documented substitution, audited in Phase 2B |
| Descriptor | published `382982932_fit.json` | same file, byte-identical | **exact** |
| Mechanisms | AllenSDK `v2.16.2` module set | same 16 files, all digests matching | **exact** |
| Junction potential | −14 mV | −14 mV, applied at output | **exact** |
| Manifest | `BiophysicalApi.create_manifest` output | Phase 2B draft with the `sweeps_by_type` key Allen's own writer omits | documented; required to run at all |
| `axon_type` | command-line default | `truncated` | **no-op** for perisomatic |

The reconstruction is therefore **Allen-compatible and traceable**, not
Allen-identical. Every substitution is named, its origin recorded, and — in the
one case that could plausibly move the numbers (NEURON) — tested against Allen's
own published assertion and found not to.

---

## 13. Reproduction recipe and artefact inventory

The validation script is the deliverable; everything it produced stays outside Git.

```bash
# 1. isolated environment (user-scoped, no sudo, no apt)
#    uv -> CPython 3.11.18 -> venv at ~/incm_phase2c/venv
#    numpy 1.23.5  scipy 1.10.1  pandas 1.5.3  h5py 3.10.0
#    scikit-image 0.21.0  argschema 3.0.4  six 1.16.0  simplejson 3.19.1
#    simpleitk 2.3.1  xarray 2022.12.0  pynwb 2.2.0  hdmf 3.4.7
#    neuron 8.2.7

# 2. stage the cached assets into the model workspace (no downloads)
#    manifest.json  382982932_fit.json  674389901_382982932_m.swc
#    674389910_382982932_m.marker  modfiles/ (16)  382982932.nwb

# 3. run
PYTHONDONTWRITEBYTECODE=1 ~/incm_phase2c/venv/bin/python \
  scripts/validate_perisomatic_execution.py \
    --model-dir        ~/incm_phase2c/model \
    --allensdk-src     <repo>/tmp/model_cache/2b/src/AllenSDK-2.16.2 \
    --assets-manifest  <repo>/tmp/model_cache/assets_2a.json \
    --out-dir          ~/incm_phase2c/results
```

The script exits `0` when every numerical pipeline check passes, `1` when a
pipeline check fails, and `2` when the sweep could not be executed. Biological
agreement is printed as `report` rows and never changes the exit code.

Generated artefacts, all outside the repository and outside Git tracking:

| Artefact | Size | Note |
|---|---|---|
| `work/382982932.nwb` | 95 166 399 B | simulation output, sweep 38 written |
| `results/traces_sweep38.npz` | 19 361 729 B | `v_sim`, `t_ms`, `v_raw_mv` for independent inspection |
| `results/execution_summary.json` | 7 725 B | 50 checks, 17 metrics, all facts |
| `results/nrnivmodl.log` | 753 B | verbatim compiler output |
| `results/execution.log` | 1 542 B | verbatim runner log |
| `model/x86_64/libnrnmech.so` | 149 016 B | compiled mechanisms |
| `fixture_control/` | — | Allen's fixture copy, used for the §3.5 control |

Result tally for the canonical run:

```
checks: 50   passed: 50   failed: 0   skipped: 0   metrics: 17
  A. Input verification                       24
  B. Mechanism compilation                     4
  C. Execution                                 9
  D. Output convention                         4
  E. Recorded versus simulated comparison      9
```

---

## 14. Provenance and licensing

| Asset | Source | Licence |
|---|---|---|
| `382982932_fit.json` | RMA well-known file for model `473862496` | Allen Institute Terms of Use |
| `382982932.nwb` | RMA well-known file `491199232` | Allen Institute Terms of Use |
| SWC `674389901`, marker `674389910` | RMA well-known files, reconstruction `674389884` | Allen Institute Terms of Use |
| 16 `.mod` files, `cell.hoc`, `stdgui.hoc`, `import3d.hoc` | AllenSDK `v2.16.2`; the latter two ship with NEURON | Allen Institute Software License / NEURON |
| AllenSDK `v2.16.2` | PyPI sdist, cached | Allen Institute Software License (BSD-2-Clause + non-commercial clause) |
| NEURON `8.2.7` | PyPI wheel | NEURON licence (BSD-3-Clause style) |

No asset, recording, compiled mechanism or generated trace is committed. The
commit contains this report and the validation script — analysis, not data. The
model workspace, the virtual environment and the cached source all live outside
the repository, and `tmp/` is ignored by `.gitignore`.

---

**End of Phase 2C.** One sweep was executed. No fitted parameter, descriptor,
manifest, AllenSDK source file or published artefact was modified. The
all-active model, the other 19 COARSE sweeps, the FINEST block, FHN, parameter
fitting and held-out evaluation were not run. The simulation genuinely executed
and its output was read back and independently inspected.

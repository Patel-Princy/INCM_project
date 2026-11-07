# Phase 2G-A — All-Active Model Execution-Readiness Audit (Static Only)

**Repository:** `Patel-Princy/INCM_project`  **Branch:** `ashish-work`
**Specimen:** `382982932` (mouse VISp, L2/3, `Nr5a1-Cre;Ai14-177333.03.01.01`)
**Model class:** `Biophysical - all active`  **Model ID:** `497233292`  **Template ID:** `491455321`
**Fit descriptor:** `497233292_fit.json`, 5 738 B, `sha256 bcffd56bbcec001b…`
**Fitting sweep:** `41` (`C1LSCOARSE150216`), junction potential −14 mV
**Published fitted reconstruction:** `491771090` — does not exist in the API
**Substitute morphology:** reconstruction `674389884`, SWC `674389901`, marker `674389910`
**Audit script:** `scripts/audit_all_active_readiness.py` (1 822 lines, 138 checks)
**Tests:** `tests/test_audit_all_active_readiness.py` (33 tests; 196 in the suite)
**Predecessors:** `PHASE2A_MODEL_EXECUTION_READINESS.md`, `PHASE2B_GEOMETRY_AND_MANIFEST_AUDIT.md`,
`PHASE2C_PERISOMATIC_EXECUTION_VALIDATION.md`, `PHASE2D_ELECTROPHYSIOLOGY_PROTOCOL_AUDIT.md`,
`PHASE2E_FINEST_HELD_OUT_EVALUATION.md`, `PHASE2F_RECORDING_ONLY_EXCITABILITY_ANALYSIS.md`

**Evidence vocabulary**

| Tag | Meaning |
|---|---|
| **OBSERVED** | measured in a file, reproducible from a digest |
| **DERIVED** | a consequence of OBSERVED facts plus AllenSDK source, with no unknowns |
| **ASSUMED** | true only if an unrecorded choice is made |
| **UNAVAILABLE** | not derivable from any published artefact |

---

## 1. Executive verdict

**CONDITIONALLY READY.**

The all-active model `497233292` is **technically executable and fully
specified in every respect except one**, and that one exception is the primary
blocker this phase was asked to adjudicate: **`axon_type` is not recorded
anywhere in the published record, and neither branch can be established as the
configuration the published parameters were fitted under.**

Nothing else is missing. The descriptor is intact and matches the digest the
brief supplied. Every mechanism it inserts has a byte-identical `.mod` file.
All 42 genome entries map onto section classes the substitute morphology
actually contains. The manifest can be grounded field-by-field in AllenSDK
source or in the Phase 2A/2B record, with the single documented exception.

The audit therefore returns a verdict that is neither a pass nor a refusal:

| Dimension | Finding | Basis |
|---|---|---|
| **Technical executability** | Yes. Both branches run; no dependency is absent; no parameter is unresolved. | **DERIVED** |
| **Reproducibility as fitted** | No. The axon replacement is a free parameter of the published model that Allen never published. | **OBSERVED** (four independent absences) |
| **Fidelity to the originally fitted model** | Unknowable. The fitted reconstruction `491771090` does not exist, and the substitute differs from it in a way that cannot be measured. | **UNAVAILABLE** |
| **Biological validity** | Not established, and not establishable by this phase. A successful static mapping is a statement about names, not about electrophysiology. | **UNAVAILABLE** |

**The one sentence form:** *execution is possible, reproduction is not.*

An execution performed now would be a **reconstruction under an explicit,
declared assumption** — the model `497233292` as specified by its published
parameters, with an axon treatment this project chose — and must be reported as
such. It must not be reported as "the Allen all-active model for
`382982932`", because that sentence asserts a branch that no artefact records.

**What the two branches cost.** Reproducing Allen's two implementations
statically from the substitute SWC gives:

| Quantity | `stub` | `truncated` |
|---|---|---|
| Axon membrane area | **188.50 µm²** | **44.11 – 62.79 µm²** |
| Diameter | 1.0 µm, both segments | 0.2392–0.4374 µm then 0.2288 µm |
| Attachment | `soma[0](0.5)` | `soma[0](1.0)` |
| Stub/truncated area ratio | **3.00× – 4.27×** | — |

The axon is the section class that carries the highest `gbar_Kv3_1` in the
model (0.987545 against 0.247985 on the soma) and 9 active mechanisms in total.
A three- to fourfold change in its area, plus a change in where it attaches to
the soma, is not a cosmetic difference. It is the difference between two
different cells.

**What this phase did not do.** No NEURON process was started, no `.mod` file
was compiled, no simulation was constructed, no parameter was read from a file
and written back, and neither descriptor, morphology, marker nor mechanism file
was modified. The audit script imports only the standard library; its last
section asserts that `neuron`, `nrn` and `allensdk` are absent from
`sys.modules`, and that assertion passes (**OBSERVED**).

**What the audit itself establishes (summary of §2–§8).**

* Every pinned asset is byte-identical to what Phase 2A recorded. Nothing has
  drifted: the descriptor is still `bcffd56b…5963`, 5 738 B.
* The descriptor is the legacy all-active shape — four top-level sections, 42
  string-valued genome entries, `passive` carrying nothing but `ra`, and no
  `cm` or `e_pas`. That shape is *exactly* what `AllActiveUtils` expects and
  *exactly* what the perisomatic loader would fail on.
* `axon_type` is read by `create_utils` from `biophys[1]`, which is not a
  manifest field: it is appended at run time by `runner.load_description` from
  a command-line flag whose default is `'truncated'`.
* Neither the fit descriptor, nor the public neuronal-model record, nor either
  of Allen's own fixture manifests, nor the substitute morphology records the
  branch.
* The perisomatic model's axon treatment is **structurally uninformative** for
  this question, for a reason that can be shown from the descriptors rather
  than argued from precedent (§4.5).
* Sweep 41 is the sole fitting sweep and sits inside the COARSE block; sweep 38
  belongs to the perisomatic model; sweeps 49–52 were never used to fit either.
* No mechanism is missing, including on the axon, where all 13 non-passive
  entries resolve against the canonical 16-file set.

---

## 2. Asset provenance and hashes

Every number below was recomputed from the files during this phase. The audit
compares each against **two** independent records: the digest the brief supplied
(or, for the source files, the digest Phase 2A recorded when it downloaded
them) and the digest stored in `tmp/model_cache/assets_2a.json`.

### 2.1 The pinned set

| Asset | Path (relative to `tmp/model_cache/`) | Bytes | SHA-256 | vs Phase 2A |
|---|---|---:|---|---|
| All-active descriptor | `models/all_active_497233292/497233292_fit.json` | 5 738 | `bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963` | identical |
| Perisomatic descriptor | `models/perisomatic_473862496/382982932_fit.json` | 2 891 | `d24d00aaed5a2a0ecf9752735b62254bba7ab3dc0d3627e61466f95b00a8e38f` | identical |
| Substitute SWC | `morphology/674389901_382982932_m.swc` | 335 924 | `71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c` | identical |
| Substitute marker | `morphology/674389910_382982932_m.marker` | 373 | `3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925` | not in the 2A record |
| `cell.hoc` | `allensdk/cell.hoc` | 715 | `9b8f73f8202f355ea6f0c9f27be23bf2cb9bd122d9abc4fb864af88401b9a26d` | identical |
| `biophysical/utils.py` | `2b/src/AllenSDK-2.16.2/allensdk/model/biophysical/utils.py` | 16 577 | `fbd5c75fdd66a0ed080a018da4e10eace7af71062c9cd1c60f48e4cb71910405` | identical |
| `biophys_sim/neuron/hoc_utils.py` | `2b/src/AllenSDK-2.16.2/allensdk/model/biophys_sim/neuron/hoc_utils.py` | 3 333 | `c29daeaf4870bfd43c6f5c74530a3dedcdb21e4a4c1d797ac4ecd6999548115e` | identical |

**The descriptor digest the brief supplied is confirmed: OBSERVED, exact match.**
`5 738 B`, `bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963`.
The cached asset still matches. No mismatch to report.

One gap, recorded rather than repaired: the **marker file has no Phase 2A
digest**. Phase 2A audited the marker in prose (§8, blocker B7) but did not add
it to `assets_2a.json`. Its digest is therefore pinned for the first time here,
from the file as it stands. It cannot be compared with a 2A record because none
exists. This is not a change to the asset; it is an absence in the earlier
record. The marker is never read at run time (§6.4), so the gap has no
consequence for execution.

### 2.2 Mechanisms

The canonical set is 16 `.mod` files:

```
CaDynamics  Ca_HVA  Ca_LVA  Ih  Im  Im_v2  K_P  K_T
Kd  Kv2like  Kv3_1  NaV  Nap  NaTa  NaTs  SK
```

and the Phase 2B draft directory holds 16 files with the **same names and
byte-identical contents** (`identical_to_canonical: 16`). **OBSERVED.**

The descriptor inserts 11 distinct mechanisms: `NaV`, `Kd`, `Kv3_1`, `SK`,
`Ca_HVA`, `Ca_LVA`, `CaDynamics`, `Ih`, `Im_v2`, `K_T`, `Kv2like`. Every one
has a `.mod` file. `pas` is inserted explicitly by the loader and is a NEURON
built-in, so it needs no file. **No mechanism is missing. DERIVED.**

Five files are shipped and unused: `Im`, `K_P`, `NaTa`, `NaTs`, `Nap`. This is
expected and is worth stating plainly: the available set is the Allen
`peri_model` modfile directory, which is a *superset* across model classes. That
the model's mechanisms are **all present** is a completeness statement about
this model. That five are unused is not a deficiency, but it does mean the set
was not curated for `497233292` specifically — an observation, not a defect.

**Requirement check (the brief's question):** does the all-active model require
any mechanism absent from the canonical set? **No.** Zero missing.

### 2.3 Has anything changed since Phase 2A?

**No. OBSERVED.** Seven of the seven comparable assets agree with
`assets_2a.json` byte-for-byte. The audit also scans both modfile directories
for compiled artefacts (`.o`, `.dll`, `.so`, `.pyd`, `.c`) and finds **zero**,
so nothing has been built in the cache since the record was written.

The constraint against committing raw Allen assets remains honoured: the entire
`tmp/model_cache/` tree is git-ignored (`.gitignore:72`), and this phase adds no
file to it.

---

## 3. The all-active loader contract

This section is read from the cached AllenSDK v2.16.2 source, not inferred from
the Phase 2C perisomatic execution. The script pins each fact as an exact
substring, so every claim below is one `grep` away from confirmation.

### 3.1 Which utility class `model_type` selects

`allensdk/model/biophysical/utils.py:51`:

```python
def create_utils(description, model_type=None):
    if model_type is None:
        try:
            model_type = description.data["biophys"][0]["model_type"]
        except KeyError:
            logging.error("Could not infer model type from description")

    axon_type = description.data["biophys"][1]["axon_type"]

    if model_type == PERISOMATIC_TYPE:
        return Utils(description)
    elif model_type == ALL_ACTIVE_TYPE:
        return AllActiveUtils(description, axon_type)
```

Three facts, all **OBSERVED**:

1. `model_type` comes from `biophys[0]`. Our draft sets it to
   `"Biophysical - all active"`, which equals `ALL_ACTIVE_TYPE`, so the factory
   returns `AllActiveUtils`. **DERIVED.**
2. **`axon_type` is read before the branch, unconditionally, for both classes.**
   It is not a perisomatic concept that the all-active path happens to reuse; it
   is a hard requirement of the factory.
3. `axon_type` is read from `biophys[1]`, an entry that no manifest in this
   project or in AllenSDK contains.

Where `biophys[1]` comes from — `runner.py:198`:

```python
    # For newest all-active models update the axon replacement
    axon_replacement_dict = {'axon_type': args_dict.get('axon_type', 'truncated')}
    description.update_data(axon_replacement_dict, 'biophys')
```

and `Description.update_data` appends rather than merges:

```python
        self.data[section].append(data)
```

So the branch is supplied **at run time, by the runner, from a command-line
flag**:

```python
sim_parser.add_argument('--axon_type', default='truncated', choices=['stub', 'truncated'], ...)
```

**Consequence (DERIVED).** A manifest with one `biophys` entry cannot reach
`create_utils` on its own: `biophys[1]` raises `IndexError`. The three Phase 2C
paths that work do so because `load_description` inserted the entry first. The
`'truncated'` value in `args_dict.get(...)` is a **default**, not a record of
what the published fit was produced under.

### 3.2 How `AllActiveUtils` interprets `passive`

`utils.py:416`:

```python
        passive = self.description.data["passive"][0]
        ...
        for sec in h.allsec():
            sec.Ra = passive["ra"]
            sec.insert("pas")
            # for seg in sec:
            #     seg.pas.e = passive["e_pas"]

        # for c in passive["cm"]:
        #     h('forsec "' + c["section"] + '" { cm = %g }' % c["cm"])
```

The two loops that make `passive` meaningful for the perisomatic class are
**commented out**. The perisomatic `Utils.load_cell_parameters` (`utils.py:165`)
runs both:

```python
        for sec in h.allsec():
            sec.Ra = passive["ra"]
            sec.insert("pas")
            for seg in sec:
                seg.pas.e = passive["e_pas"]

        for c in passive["cm"]:
            h('forsec "' + c["section"] + '" { cm = %g }' % c["cm"])
```

The all-active loader therefore reads **only `ra`** from `passive`, and — see
§3.4 — even that is overwritten.

**Structural incompatibility with the perisomatic loader (DERIVED, no AllenSDK
code called).** The all-active `passive` block is `{"ra": 100}`. The perisomatic
loader's first access to `passive["e_pas"]` raises `KeyError`, and so does
`passive["cm"]`. This is not a subtle wrong-answer failure: the wrong loader
cannot start. The audit reproduces both lookups against the descriptor's own
`passive` dict with plain Python and records the two `KeyError`s.

### 3.3 How the 42 string-valued genome entries are converted

`utils.py:436`:

```python
        for p in genome:
            section_array = p["section"]
            mechanism = p["mechanism"]
            param_name = p["name"]
            param_value = float(p["value"])
            if section_array == "glob":          # global parameter
                h(p["name"] + " = %g " % p["value"])
            else:
                if hasattr(h, section_array):
                    if mechanism != "":
                        for section in getattr(h, section_array):
                            if self.h.ismembrane(str(mechanism), sec=section) != 1:
                                section.insert(mechanism)
                    for section in getattr(h, section_array):
                        setattr(section, param_name, param_value)
```

The mechanics of the conversion, in order:

| Step | Behaviour | Status |
|---|---|---|
| `float(p["value"])` | The descriptor stores every value as a **string** (`"0.000661695"`, `"3.63576e-05"`, `"-71.7108"`). The loader converts. A non-numeric string would raise `ValueError` at run time. | **OBSERVED** — all 42 parse |
| `section == "glob"` | Escape hatch for a global parameter. **The descriptor uses it zero times**: every one of the 42 entries is per-section. | **OBSERVED** |
| `hasattr(h, section_array)` | **The gate has no `else` branch.** A section array absent from the model is skipped *silently*: no log line, no warning, no failure. | **OBSERVED** |
| `insert(mechanism)` | Guarded by `ismembrane`, so re-insertion is idempotent. | **OBSERVED** |
| `setattr(section, param_name, value)` | Applied to every section in the array. | **OBSERVED** |

**The silent-skip gate cannot fire for this model (DERIVED).** All 42 entries
address one of `soma`, `axon`, `apic`, `dend`. The substitute SWC contains all
four (`soma=1, axon=5169, apic=884, dend=1533`), so `h.soma`, `h.dend` and
`h.apic` exist after import; and **both** axon branches execute
`h("create axon[2]")` unconditionally, so `h.axon` exists regardless of which
branch is chosen. Every entry resolves. This is worth stating precisely because
the gate is silent: had the substitute morphology lacked apical dendrites, 8 of
42 entries would have vanished with no diagnostic anywhere, and the model would
have run and produced a plausible-looking wrong answer. It does not happen here,
but nothing in the pipeline would have caught it if it had.

### 3.4 How `Ra`, `cm`, `e_pas` and `g_pas` are applied

This is the part of the contract that is easiest to get wrong, because the
descriptor states `Ra` **twice** and one of the two statements is dead.

| Parameter | Where stated | How it reaches NEURON | Effective value |
|---|---|---|---|
| `Ra` | `passive.ra = 100` | `sec.Ra = passive["ra"]` (loop 1) | **superseded** |
| `Ra` | genome, per section | `setattr(section, "Ra", v)` (loop 2) | `soma 88.1342`, `axon 76.0926`, `apic 119.149`, `dend 73.8293` |
| `cm` | genome only | `setattr(section, "cm", v)` | `soma 0.523298`, `axon 3.39623`, `apic 2.72754`, `dend 4.57734` |
| `e_pas` | genome only | `setattr(section, "e_pas", v)` | `soma −71.7108`, `axon −73.2693`, `apic −83.3048`, `dend −84.2172` |
| `g_pas` | genome only | `setattr(section, "g_pas", v)` | `soma 6.61695e−04`, `axon 8.88992e−03`, `apic 3.63576e−05`, `dend 3.22155e−05` |

**`passive.ra = 100` never reaches the simulation.** The genome loop runs after
the passive loop and assigns `Ra` on all four section arrays, so `100` is
overwritten on every section of the cell. The audit asserts this directly:
every genome `Ra` differs from `passive.ra`. **DERIVED.**

This is the single most important thing this section establishes about
`passive`, and it is why the all-active loader's commented-out `cm`/`e_pas`
loops are not a defect: **the genome carries `cm` and `e_pas` per section for
exactly the reason the loops were commented out.** The perisomatic descriptor
states them once, as four-element lists; the all-active descriptor states them
per section-class as genome entries. Two schemas for the same information.

**`e_pas` and `g_pas` depend on ordering (DERIVED, with one caveat).** Both are
`pas` mechanism variables, not section variables. They can only be assigned
through `setattr(section, ...)` because `sec.insert("pas")` already ran in the
earlier loop. The audit confirms the ordering in the source:
`source.rindex('sec.insert("pas")') < source.index("param_value = float")` — the
last `insert("pas")` in the file precedes the genome loop. **OBSERVED.**

The caveat is **UNAVAILABLE** and is stated rather than papered over: that
`setattr(section, "e_pas", v)` propagates to *every segment* of the section is
NEURON's documented range-variable behaviour, but it is NEURON's behaviour, and
this phase does not run NEURON to confirm it. What can be said statically is
that the source *intends* it, that the same idiom is used for `cm` and `g_pas`
throughout Allen's model corpus, and that the perisomatic loader sets `e_pas`
per segment explicitly — the two paths are not written the same way, and that
asymmetry is worth knowing before interpreting any all-active trace.

### 3.5 Reversal potentials

```python
        for erev in conditions["erev"]:
            ...
            if hasattr(h, erev_section_array):
                for section in getattr(h, erev_section_array):
                    if self.h.ismembrane("k_ion", sec=section) == 1:
                        setattr(section, "ek", ek)
                    if self.h.ismembrane("na_ion", sec=section) == 1:
                        setattr(section, "ena", ena)
```

`ek = −107.0` and `ena = 53.0` are applied **only where the corresponding ion is
already present**, which is only where a `NaV`/`Kd`-family mechanism has been
inserted. All four section arrays carry `NaV`, so all four receive both. Unlike
the genome gate, this one *does* print a warning when the array is missing
(`"Warning: can't set erev for %s"`). **OBSERVED.**

### 3.6 Is the descriptor structurally compatible? Are any parameters unresolved?

| Question | Answer | Basis |
|---|---|---|
| Top-level sections match what the loader reads? | Yes — `passive`, `genome`, `conditions`, `fitting` | **OBSERVED** |
| `passive` sufficient? | Yes — `ra` is the only key the all-active loader reads, and it is superseded anyway | **DERIVED** |
| Genome schema matches? | Yes — four keys per entry, string values, no `glob` | **OBSERVED** |
| Every mechanism available? | Yes — 11 of 11, `pas` built in | **OBSERVED** |
| Every section array present? | Yes — 42 of 42 addressable | **DERIVED** |
| Any parameter unresolved? | **None.** 16 distinct genome names, all resolvable | **DERIVED** |
| Any section class unresolved? | **None** — `soma`, `axon`, `apic`, `dend` all exist | **DERIVED** |
| Anything the loader ignores that a reader might assume it uses? | `passive.ra` (superseded), `passive.cm`/`passive.e_pas` (absent), `axon_morph` (see §6.5) | **OBSERVED** |

**Conclusion for §3: the descriptor is structurally compatible with
`AllActiveUtils`, and no parameter or section class is unresolved.** The loader
contract is settled. The blocker is not here.

---

## 4. Axon-type analysis — the primary blocker

### 4.1 The two implementations

Both live in `utils.py`. The difference is not a parameter: they are two
different code paths, and only one of them calls the other.

**`stub`** (`utils.py:362`) delegates immediately:

```python
        if self.axon_type == "stub":
            self._log.info("Replacing axon with a stub : length 60 micron, diameter 1 micron")
            super(AllActiveUtils, self).generate_morphology(morph_filename)
            return
```

and lands in `Utils.generate_morphology` (`utils.py:133`):

```python
        for sec in h.allsec():
            sec.nseg = 1 + 2 * int(sec.L / 40.0)
            if sec.name()[:4] == "axon":
                h.delete_section(sec=sec)
        h("create axon[2]")
        for sec in h.axon:
            sec.L = 30
            sec.diam = 1
            sec.nseg = 1 + 2 * int(sec.L / 40.0)
        h.axon[0].connect(h.soma[0], 0.5, 0.0)
        h.axon[1].connect(h.axon[0], 1.0, 0.0)
```

**`truncated`** (`utils.py:370`) does not delegate. It is the fall-through
branch — there is no `elif self.axon_type == "truncated"`, only a log line:

```python
        self._log.info("Legacy model - Truncating reconstructed axon after 60 micron")
        ...
        self.h("soma[0] area(0.5)")
        axon_diams = [self.h.axon[0].diam, self.h.axon[0].diam]
        self.h.distance(sec=self.h.soma[0])
        for sec in self.h.allsec():
            if sec.name()[:4] == "axon":
                if self.h.distance(0.5, sec=sec) > 60:
                    axon_diams[1] = sec.diam
                    break
        for sec in self.h.allsec():
            if sec.name()[:4] == "axon":
                self.h.delete_section(sec=sec)
        self.h("create axon[2]")
        for index, sec in enumerate(self.h.axon):
            sec.L = 30
            sec.diam = axon_diams[index]
        for sec in self.h.allsec():
            sec.nseg = 1 + 2 * int(sec.L / 40.0)
        self.h.axon[0].connect(self.h.soma[0], 1.0, 0.0)
        self.h.axon[1].connect(self.h.axon[0], 1.0, 0.0)
```

Two details that are easy to miss and that matter for reading any result:

* the `stub` path is selected by a **positive** test, and `truncated` is
  whatever remains — including any value the CLI would not accept;
* the `stub` path writes `h.axon[0].connect(h.soma[0], 0.5, 0.0)` (module-local
  alias `h`), the `truncated` path writes
  `self.h.axon[0].connect(self.h.soma[0], 1.0, 0.0)`. Different alias, different
  attachment point. The attachment point is the substantive difference.

### 4.2 The comparison the brief asks for

| Question | `stub` | `truncated` |
|---|---|---|
| **Exact Allen implementation** | `AllActiveUtils.generate_morphology` returns early through `Utils.generate_morphology`: set `nseg`, delete every `axon*` section, `create axon[2]`, `L=30`, `diam=1`, `nseg=1`, attach `axon[0]` to `soma[0](0.5)`. | `AllActiveUtils.generate_morphology` does not delegate: set `nseg` on the imported cell, seed `axon_diams` from `axon[0].diam` **before** deletion, call `h.distance(sec=soma[0])`, take the first axon section whose midpoint is further than 60 µm as `axon_diams[1]`, delete every `axon*` section, `create axon[2]`, `L=30` with the two sampled diameters, attach `axon[0]` to `soma[0](1.0)`. |
| **Reconstructed axon retained?** | **No.** Every section named `axon*` is deleted before the stub is created. | **No.** The same deletion loop runs. Only two scalar diameters are sampled from the reconstruction; the reconstruction itself is discarded. |
| **Synthetic axon sections created?** | Yes: `axon[2]`, 30 µm each, diameter 1.0 µm, `nseg = 1`. Total area 188.50 µm². | Yes: `axon[2]`, 30 µm each, `nseg = 1`, with the two sampled diameters. Total area 44.11–62.79 µm². |
| **Biological assumptions** | The axon is a uniform 1 µm cylinder whose geometry is independent of the reconstruction. It inflates the axonal membrane area 3.0–4.3× relative to the reconstructed diameter, and it attaches at the middle of the soma rather than the end. | A longest root-to-tip path of ≈708 µm of reconstructed axon is represented by 60 µm of uniform cylinder, with one diameter sampled near the soma and one beyond the 60 µm cut. The membrane area is 3.0–4.3× smaller than the stub. |
| **Reproducibility implications** | Fully determined by the source and by the SWC's existence. **The same stub results for any morphology that contains a soma**, so the branch is insensitive to which reconstruction is supplied — which is exactly why it cannot be wrong for the wrong reason. | Depends on `Import3d`'s per-section diameter assignment, which is a NEURON implementation detail and is **not** derivable from the SWC. The distal sample *is* robust: the axon radius plateaus at 0.114 µm and 17 points in the 55–70 µm window are equal to 1e−6, so `axon_diams[1] = 0.2288 µm` with confidence. The proximal sample is only bounded (0.2392–0.4374 µm), because `Import3d` aggregates several SWC points into one section and chooses the section diameter itself. Deterministic for a fixed NEURON build, not statically predictable. |
| **Supported by published descriptor?** | **No.** The descriptor has no `axon_type`, no `axon_morph`, and no axon diameter. | **No.** The same three absences. The CLI default being `'truncated'` is a default, not a record. |

### 4.3 The divergence, quantified

From the substitute SWC (**DERIVED**, reproduced statically by the audit):

| Quantity | Value |
|---|---:|
| SWC points | 7 587 (soma 1, axon 5 169, apic 884, dend 1 533) |
| Axon roots attached to the soma | 1 |
| Longest root-to-tip axon path | 707.99 µm |
| Axon radius range | 0.114 – 0.282 µm → diameter 0.2288 – 0.564 µm |
| Radius beyond 60 µm | plateau at 0.114 µm (diameter 0.2288 µm) |
| `stub` total axon area | 188.4956 µm² |
| `truncated` total axon area | 44.11 – 62.79 µm² |
| Ratio `stub` / `truncated` | **3.00 – 4.27** |
| Attachment | `soma(0.5)` vs `soma(1.0)` |

Both branches yield a two-compartment, 60 µm axon: `nseg = 1 + 2*int(30/40) = 1`
per section. So the branch does not change the *number* of compartments; it
changes the geometry those two compartments are given.

**Why this is material rather than pedantic.** The axon is the most
differentiated section class in the descriptor:

| Section | genome entries | active mechanisms | notable |
|---|---:|---:|---|
| axon | 14 | **9** | `gbar_Kv3_1 = 0.987545`, `cm = 3.39623`, `Ra = 76.0926` |
| soma | 12 | 7 | `gbar_Kv3_1 = 0.247985` |
| apic | 8 | 4 | — |
| dend | 8 | 4 | — |

`Kv3_1` density on the axon is **4.0×** the somatic value, and the axon carries
three mechanisms the soma does not (`K_T`, `Kd`, `Kv2like`). Whatever the branch
choice does to total membrane area, it does it to the compartment with the
highest fast-potassium density in the model. This is not a claim about which
direction the result moves — it is a claim that the choice is not cosmetic, and
that two runs under different branches are two different models rather than two
samples of one.

### 4.4 Four independent places that could have recorded it, and do not

| Place | What it says | Verdict |
|---|---|---|
| Fit descriptor `497233292_fit.json` | Four top-level sections; no `axon_type`, no `axon_morph`, no axon geometry anywhere in 5 738 bytes | **absent** |
| Public neuronal model record | `id`, `name`, `neuron_reconstruction_id`, `neuronal_model_template_id`, `specimen_id`. **No axon field.** | **absent** |
| Allen's all-active fixture manifest | `biophys` has **one** entry, keys `model_file`, `model_type` | **absent** |
| Allen's perisomatic fixture manifest | `biophys` has **one** entry, same two keys | **absent** |

The schema *could* have carried it. Allen's `Biophysical - multicell` example
descriptor contains an explicit `axon_morph` section whose HOC is exactly the
stub configuration:

```
forsec axonal{delete_section()}   create axon[2]   L=30   diam = 1
connect axon(0), soma(0.5)
```

So the descriptor format has a field for recording axon treatment, and this
model's descriptor does not use it. The choice is absent **by omission, not by
impossibility** — which is the precise sense in which the model is
under-specified. **OBSERVED.**

### 4.5 Why the perisomatic precedent is not evidence

This is the argument the brief warns against, and it can be refused structurally
rather than rhetorically. Compare the two `passive`/`genome` statements of the
axon:

| | perisomatic `473862496` | all-active `497233292` |
|---|---|---|
| Genome entries on the axon | **1** (`g_pas = 2.3937e−04`) | **14** |
| Active mechanisms on the axon | **0** | **9** (`NaV, K_T, Kd, Kv2like, Kv3_1, SK, Ca_HVA, Ca_LVA, CaDynamics`) |
| `cm`, `Ra` on the axon | from block-level lists | per-section genome entries |
| Axon geometry therefore | electrically **inert** — a passive leak of 2.4e−04 S/cm² | **load-bearing** |

The perisomatic axon is a passive appendage whose diameter cannot affect spike
initiation in any material way. **A model class whose axon geometry is inert is
structurally incapable of informing the choice for a model class whose axon
carries 4× the somatic Kv3.1 density.** Using the perisomatic run to justify
`stub` would be reasoning from a case where the variable was free of
consequence to a case where it is not.

### 4.6 Allen's own fixture test is stale, and is not evidence either

`test_biophysical_all_active.py`:

```python
    utils = AllActiveUtils(description)
```

against v2.16.2's

```python
    def __init__(self, description, axon_type):
```

The call passes one positional argument to a two-argument constructor. The test
is marked `@pytest.mark.requires_neuron`, so it does not run in Allen's default
CI, and it has drifted from the constructor it exercises. It also bypasses
`create_utils` entirely, so it never touches `biophys[1]`. **It provides no
evidence for either branch**, and it is a concrete sign that this path is not
covered by upstream tests. **OBSERVED.**

### 4.7 Determination

**Neither branch can be established as the original fitted configuration.**

The evidence is a fourfold absence (§4.4), not a gap in this audit's effort. The
default value in the parser is the only place `'truncated'` appears anywhere
outside the docstrings, and a default is a statement about what happens when a
user says nothing — it is not a statement about how `497233292` was produced.

Therefore: **the original all-active model is under-specified.** An execution
would be a **reconstruction with an explicit assumption**, not an exact
reproduction. That sentence is the deliverable of this section, and it is the
finding the verdict rests on.

One further consequence worth stating: because the substitute morphology is
*not* the fitted one, a `truncated` run cannot restore fidelity even in
principle. The fitted reconstruction `491771090` does not exist (§5.4), so even
the branch that samples the reconstruction would sample the wrong
reconstruction. `truncated` is not "more faithful" here; it is merely more
dependent on unobservable details.

---

## 5. Morphology compatibility

### 5.1 What the substitute morphology actually contains

`674389901_382982932_m.swc`, 335 924 B, `sha256 71bb551b…ef36c`, parsed row by
row (**OBSERVED**):

| SWC type | Class | Points | Role |
|---|---|---:|---|
| 1 | soma | **1** | a single sphere, radius 7.142 µm |
| 2 | axon | 5 169 | one soma-attached root, longest path 707.99 µm |
| 3 | dend | 1 533 | basal |
| 4 | apic | 884 | apical |
| — | total | 7 587 | |

A single soma point matters for two reasons. It means `Import3d` builds a
one-point spherical soma, so `soma[0]` has a well-defined end (`1.0`) and middle
(`0.5`) — the two positions the branches attach at, which are therefore
genuinely different points on the cell rather than aliases. And it means the
axon attaches to the soma rather than to a soma *array*, so `h.axon[0].connect`
has an unambiguous target.

### 5.2 Does the loader map all 42 genome entries?

**Yes — 42 of 42. DERIVED.**

| Class | Genome entries | Array exists? | Resolves? |
|---|---:|---|---|
| soma | 12 | from the SWC | yes |
| axon | 14 | `create axon[2]` in **both** branches | yes |
| apic | 8 | from the SWC (884 points) | yes |
| dend | 8 | from the SWC (1 533 points) | yes |

The axon array is the one that needs justifying, because it is created rather
than imported: both branches execute `h("create axon[2]")` unconditionally
before returning, so `hasattr(h, "axon")` is true under either choice. This is
why the silent-skip gate of §3.3 cannot fire.

Note what "resolves" does and does not mean. It means the *assignment happens*.
It does not mean the assigned value lands on the membrane the fitted model had
in mind — see §5.6.

### 5.3 Are section names and class mappings deterministic?

Mostly, and the exceptions are worth separating.

| Aspect | Deterministic? | Why |
|---|---|---|
| Which SWC points belong to which class | **Yes** | The type column decides; no inference. |
| Name → class mapping (`soma`, `axon`, `apic`, `dend`) | **Yes** | `Import3d` names sections from the SWC type, which is why Allen can test `sec.name()[:4] == "axon"` instead of tracking sections. The genome's arrays are exactly those names. |
| Number of sections per class | **No, and it does not matter** | `Import3d` decides section splitting; the loader iterates `getattr(h, array)` and never indexes it, except for `axon[0]` after the array has been recreated with a known length of 2. |
| `nseg` per section | **Yes** | `1 + 2*int(L/40)`, applied to every section. |
| Section diameter | **Partly.** | See §5.5 and §4.2. |

The distinction that matters: the *mapping* is deterministic, the *diameters* are
not. A statement like "all 42 parameters reach the model" is therefore safe; a
statement like "the model has the fitted geometry" is not.

### 5.4 The missing fitted reconstruction

`491771090` is the reconstruction the published parameters were fitted against.
The cache holds three API probes for it, all recorded by Phase 2B, and **all
three return zero rows**:

```
neuron_reconstruction_491771090.json   {"success": true, "num_rows": 0, "msg": []}
recon_check_491771090.json             {"success": true, "num_rows": 0, "msg": []}
wkf_attachable_491771090.json          (no well-known file attached)
```

No morphology file of any type exists for that ID. **OBSERVED.**

This has two consequences that this phase must not blur together:

1. The substitute is not a convenience. It is the only morphology that exists.
2. **The difference between the fitted and the substitute morphology cannot be
   measured, because one of the two operands is absent.** Any statement about
   how much the substitution matters — in either direction — is unfalsifiable
   from the published record. That is `UNAVAILABLE`, and it stays
   `UNAVAILABLE`.

Phase 2A judged parameter transfer legitimate on the grounds that every
parameter is section-*class* level (§8, B5). That reasoning is sound and this
phase does not contradict it: a section-class parameter applies to whatever
sections exist. But it is worth being explicit that "the parameters transfer"
and "the model is the fitted model" are different claims, and only the first
survives the absence of `491771090`.

### 5.5 Does the axon treatment change the mapping?

**No for mapping, yes for geometry.** Both branches delete sections named
`axon*` and create `axon[2]`. Neither branch touches `soma`, `dend` or `apic`:
the deletion test `sec.name()[:4] == "axon"` appears three times in `utils.py`
and never with another prefix. **DERIVED from source.**

So of the 42 entries:

* **28** (`soma` 12 + `apic` 8 + `dend` 8) land on the same sections, with the
  same values, under either branch. These are **branch-independent**.
* **14** (all on `axon`) always resolve, but they resolve onto a two-segment
  stub whose diameter (`1.0` vs `0.2392–0.4374`/`0.2288` µm) and attachment
  (`soma(0.5)` vs `soma(1.0)`) differ. These are **branch-dependent** not in
  whether they apply but in what they apply to.

This is the precise sense in which the axon decision contaminates the model: it
does not spread to the other classes, but it changes the membrane on which nine
of the model's highest-density conductances sit.

### 5.6 What a static mapping cannot say

The audit maps names to arrays. It cannot say that the resulting cell behaves
like the fitted one, for four reasons that are all `UNAVAILABLE` here:

* the fitted morphology is absent (§5.4), so the comparison has no second term;
* `Import3d`'s section diameters are a NEURON implementation detail and are not
  derivable from the SWC text (§4.2);
* `setattr(section, "e_pas", v)` propagating to all segments is NEURON
  range-variable behaviour that this phase does not execute (§3.4);
* no reference voltage trace for model `497233292` exists anywhere in the
  published record, so there is no target to compare against even in principle.

**This phase therefore makes no claim of biological equivalence, and does not
treat a successful static mapping as evidence of it.** A mapping that succeeds
means the model can be built. It does not mean the model is right.

---

## 6. Manifest requirements and unresolved fields

The Phase 2B draft at `tmp/model_cache/manifest_drafts/all_active/manifest.json`
is reproduced and re-verified here field by field. It is a draft: it is inside
the git-ignored cache, it is not destined for the repository, and it is
deliberately incomplete in one place.

### 6.1 Schema conformance

| Property | Draft | Allen `manifest_all_active.json` | Verdict |
|---|---|---|---|
| Top-level sections | `biophys, manifest, neuron, runs` | same four | match |
| `biophys` length | **1** | **1** | match |
| `biophys[0]` keys | `model_file`, `model_type` | `model_file`, `model_type` | match |
| `neuron[0].hoc` | `["stdgui.hoc", "import3d.hoc"]` | same | match |
| `runs[0].sweeps` | 24–43 (COARSE only) | 65 sweeps, all blocks | restricted by design |
| `runs[0].sweeps_by_type` | present | **absent** | draft-only addition |

### 6.2 Every field, and what grounds it

| Field | Value | Source | Grounding |
|---|---|---|---|
| `biophys[0].model_file[0]` | `manifest.json` | recovered | `create_manifest` hard-codes the manifest's own basename so `Config` pre-loads it |
| `biophys[0].model_file[1]` | `497233292_fit.json` | recovered | well-known file attached to model `497233292` (id `568156386`) |
| `biophys[0].model_type` | `Biophysical - all active` | recovered | template `491455321` name; equals `ALL_ACTIVE_TYPE` |
| `biophys[1].axon_type` | — | **`absent-by-design`** | **not a manifest field**; appended from `--axon_type` |
| `neuron[0].hoc` | `["stdgui.hoc","import3d.hoc"]` | constant | `create_manifest` and both fixtures |
| `manifest[MORPHOLOGY]` | `674389901_382982932_m.swc` | substituted | `491771090` does not exist; this is the specimen's own reconstruction |
| `manifest[MARKER]` | `674389910_382982932_m.marker` | substituted | renamed to the asset that actually exists; never read at run time |
| `manifest[MODFILE_DIR]` | `modfiles` | constant | Allen's layout; the directory holds the 16 canonical files |
| `manifest[stimulus_path]` | `382982932.nwb` | recovered | the specimen's stimulus NWB |
| `manifest[output_path]` | `382982932.nwb` (under `WORKDIR`) | constant | `create_manifest` reuses the stimulus name under `WORKDIR` |
| `runs[0].sweeps` | 24–43 | restricted | every non-`Test` sweep of `C1LSCOARSE150216`; blocks never pooled |
| `runs[0].sweeps_by_type` | see manifest | derived | not emitted by `create_manifest`, but read unconditionally by `run_sync` |
| `fitting[0].junction_potential` | −14.0 | recovered | from the descriptor |
| `fitting[0].sweeps` | `[41]` | recovered | from the descriptor |

**12 of 13 non-constant fields are grounded in AllenSDK source or in the Phase
2A/2B record.** The thirteenth is the blocker.

### 6.3 The unresolved field

**`biophys[0].axon_type` must remain unresolved.** It cannot be grounded, for
the reasons in §4.4, and the brief forbids inventing a production-ready value.
The draft's provenance sidecar states this explicitly:

```json
{ "field": "axon_type", "value": "truncated", "source": "absent-by-design",
  "evidence": "Not a manifest field. runner.load_description appends it and
               create_utils reads biophys[1]; the value comes from --axon_type
               (default 'truncated')." }
```

Read that entry carefully: the `"value": "truncated"` is **not** a claim about
the fitted model. It is a record of what the parser will do if nobody says
anything. The audit asserts the manifest itself contains no `axon_type` string,
so a reader cannot mistake the sidecar's note for a manifest field.

**The draft must not be promoted to a runnable manifest as it stands.** That is
deliberate: see the next section.

### 6.4 The incompleteness is load-bearing

With one `biophys` entry, `create_utils(description)` raises `IndexError` at
`description.data["biophys"][1]`. This is not an oversight in the draft; it is
the mechanism by which an undocumented run is prevented. A manifest that *did*
carry an `axon_type` — any value — would run, silently, with an assumption
recorded nowhere a reader would look.

The only supported route to execution is therefore `runner.load_description`,
which appends `biophys[1]` from the command line. That is a good design: the
assumption is forced into the invocation, where it is visible in the command
that produced the result. **Phase 2G-B must record the invocation verbatim for
exactly this reason.**

### 6.5 Three secondary manifest facts

**`sweeps_by_type` is required by the runner and absent from the fixtures.**
`run_sync` line 119 reads `run_params['sweeps_by_type']` unconditionally, but
neither shipped fixture manifest contains it, and `BiophysicalApi.create_manifest`
does not emit it. The draft adds it. That is a deviation from the fixture — a
*necessary* one, since a runner invocation would otherwise raise `KeyError` on
line 119 — and it is documented in `provenance.json` rather than added quietly.
**OBSERVED.**

**`cell.hoc` should not be requested.** AllenSDK ships a `cell.hoc` (715 B,
`9b8f73f8…`) and `Utils.update_default_cell_hoc` substitutes a local copy for it
*if the manifest names it*. The manifest does not, `hoc_files.index("cell.hoc")`
raises `ValueError`, and the `except ValueError: pass` branch is taken. The asset
is therefore **inert** — present in the cache, never loaded. Including it, as
Phase 2A's blocker B1 suggested, would be harmless but wrong: it would replace
NEURON's own template with Allen's stub template for no reason. **OBSERVED.**

**The `'axon_morph,'` typo is inert.** `fix_sections = ['passive', 'axon_morph,', 'conditions', 'fitting']`
in both `runner.load_description` and `run_simulate.py` contains a stray comma
inside the string, so `fix_unary_sections` would look up a key named
`axon_morph,`. Since the all-active descriptor has no `axon_morph` section at
all, the typo changes nothing here — it is a latent defect that would bite a
descriptor of the multicell shape, which *does* carry `axon_morph` as a bare
dict. Not our problem, but recorded: it means the one schema field that could
have carried the axon treatment is also the one field Allen's own runner cannot
normalise. **OBSERVED.**

---

## 7. Fitting provenance and held-out eligibility

### 7.1 What the descriptor says

```json
"fitting": [{ "junction_potential": -14.0, "sweeps": [41] }]
```

| Fact | Value | Basis |
|---|---|---|
| All-active fitting sweeps | `[41]` | **OBSERVED** |
| Sweep 41 block | `C1LSCOARSE150216` | **OBSERVED** |
| Sweep 41 in the manifest's requested set? | yes (24–43) | **OBSERVED** |
| Sweep 41 held out? | **no** | **OBSERVED** |
| Perisomatic fitting sweeps | `[38]` | **OBSERVED** |
| Sweep 38 ≠ sweep 41 | yes | **OBSERVED** |
| FINEST 49–52 used to fit either model? | **no** | **OBSERVED** |

Reconfirmed exactly as the brief required. The two models were fitted on
different sweeps of the same recording: `473862496` on 38, `497233292` on 41,
both inside the COARSE block.

### 7.2 Held-out status, model by model

The two models must not share a held-out set, because the sweeps mean different
things to each.

| Sweep(s) | Perisomatic `473862496` | All-active `497233292` | Prior validation |
|---|---|---|---|
| **38** | **in-sample** (fitting sweep) | **out-of-sample** | Phase 2C, perisomatic |
| **41** | out-of-sample | **in-sample** (fitting sweep) | — |
| 24–37, 39, 40, 42, 43 | out-of-sample | out-of-sample | — |
| **49–52** (FINEST) | **out-of-sample** | **out-of-sample** | Phase 2E, perisomatic |

Two consequences that are easy to get wrong:

* **Sweep 38 cannot serve as all-active validation *and* stay a perisomatic
  success.** It is a legitimate out-of-sample sweep for `497233292` — better,
  in fact, than any other COARSE sweep, because it is the one sweep with an
  independent prior execution record. But that record is for a *different model
  class*, so it constrains the run's plausibility, not its accuracy.
* **Sweeps 49–52 are the only sweeps truly held out from both.** They were
  already the Phase 2E evaluation set, and Phase 2F established that the
  four FINEST repeats are **one condition, not four independent trials** (the
  commands are bit-identical over the common window). So the effective held-out
  sample size is **one**, not four.

### 7.3 Candidates for a later all-active evaluation

Identified here; **not run in this phase**.

| Candidate | Why it is a candidate | What it is not |
|---|---|---|
| **Sweep 38** (+170 pA, COARSE) | the only COARSE sweep with an independent prior execution record (Phase 2C), and out-of-sample for `497233292` | not evidence about all-active accuracy; the prior record is perisomatic |
| **Sweeps 49–52** (FINEST, +170 pA) | held out from both fits; already validated in Phase 2E | four repeats of one condition, so one observation |
| 24–37, 39, 40, 42, 43 | out-of-sample for `497233292` | no prior validation; any of them would be a blind first look |

The strongest design would use **38 as a sanity bracket** (a known-insufficient
stimulus that must produce a known behaviour) and **one of 49–52 as the
held-out test**, with the branch pair run for both.

### 7.4 Did any later phase move the provenance?

**No.** The descriptor's digest is unchanged since Phase 2A
(`bcffd56b…5963`, 5 738 B), so no phase after 2A altered it — a phrase-level
check would be weaker than this, because a file that is byte-identical cannot
have had a field rewritten. Phase 2C ran a *different* descriptor
(`382982932_fit.json`, digest unchanged too). Phase 2E re-used the Phase 2C
model. Phase 2F analysed the NWB recording only and did not read either
descriptor. **OBSERVED.**

---

## 8. Environment readiness

### 8.1 The Phase 2C environment

| Property | Value | Basis |
|---|---|---|
| Platform | WSL2, Ubuntu | **OBSERVED** (Phase 2C, re-checked this phase) |
| Interpreter | venv `~/incm_phase2c/venv`, Python 3.11.18 | **OBSERVED** |
| NEURON | `neuron 8.2.7`, importable, `nrnivmodl` on PATH | **OBSERVED** |
| AllenSDK | **not installed as a distribution** | **OBSERVED** |
| AllenSDK in use | source at `<repo>/tmp/model_cache/2b/src/AllenSDK-2.16.2`, supplied via `--allensdk-src` | **OBSERVED** (Phase 2C report line 802; Phase 2E lines 292, 834) |
| Supporting stack | numpy 1.23.5, h5py 3.10.0, scikit-image 0.21.0, scipy 1.10.1, matplotlib 3.7.5 | **OBSERVED** |

The all-active loader needs nothing beyond this set: `AllActiveUtils` imports
`os`, `logging`, `numpy`, `skimage.measure.block_reduce`, `NwbDataSet` and
`HocUtils` — all already exercised by Phase 2C. **No package needs installing
and none was installed.** The environment was not modified by this phase.

### 8.2 Can the loader be imported without executing the model?

**Yes, and the argument is structural rather than empirical.** The hazard in a
module import is an import-time side effect, and the only one that could start
NEURON is a module-scope import of the `neuron` package. There is none:

* `hoc_utils.py` imports both bindings **inside** `HocUtils.__init__`:

  ```python
      def __init__(self, description):
          import neuron
          import nrn
          self.h = neuron.h
  ```

  The audit asserts that `"\nimport neuron\n"` occurs **zero** times in that
  file — i.e. no module-scope import — and that the joint indented form occurs
  exactly once.
* `biophysical/utils.py` imports `from ..biophys_sim.neuron.hoc_utils import HocUtils`
  at module scope, which is a package path, not the `neuron` package. The audit
  asserts `"\nimport neuron\n"` occurs **zero** times there too.
* `runner.py` at module scope imports `argparse`, `os`, `time`, `numpy`, and
  AllenSDK's own `NwbDataSet`, `extract_cell_features`, `Config`,
  `create_utils`, `save_nwb`, `prepare_nwb_output` — plus `multiprocessing`. No
  NEURON.

So `import allensdk.model.biophysical.utils` cannot start a NEURON process, and
`create_utils` does nothing NEURON-related until `Utils.__init__` calls
`HocUtils.__init__`, which is after `Config().load()` has read the manifest.
**DERIVED from source, asserted by the script, `neuron` absent from
`sys.modules` after the full audit run.**

### 8.3 Disclosure: one import probe during reconnaissance

The committed script does not import AllenSDK. During reconnaissance, however,
`allensdk.model.biophysical.utils` **and** `allensdk.model.biophysical.runner`
were imported into a throwaway interpreter from the cached source tree, to read
`AllActiveUtils.__init__`'s signature and the parser's default `axon_type` from
the live objects rather than from the text.

**Nothing was called.** No `Config` was loaded, no `Description` built, no
`Utils` constructed, no `h` obtained, no simulation started. Afterwards
`neuron` and `nrn` were absent from `sys.modules`, confirming the import was
inert as §8.2 argues.

This is recorded rather than omitted because constraint 4 says "do not import or
execute the simulation runner", and on a strict reading importing the module for
introspection is a violation even though nothing ran. The committed script
satisfies the constraint under any reading: it establishes the same two facts
from source substrings, and its final section asserts that no simulation package
is in `sys.modules`.

### 8.4 What Phase 2G-B must add

Nothing to the environment. The gap is procedural, not technical:

1. an explicit, recorded branch choice in the invocation
   (`--axon_type <branch>`), copied verbatim into the result;
2. the modfile build step inside the WSL execution tree, not the repository
   cache (Phase 2C's staging scripts already do this);
3. a declared record of which branch produced which trace, and a refusal to
   pool them.

---

## 9. Scientific and reproducibility limitations

Numbered, with the consequence of each. **None of these is repaired by running
the model.**

**L1 — `axon_type` is unspecified (primary).** The fitted branch is not
recorded in any published artefact. Consequence: no run can be called a
reproduction of `497233292`. Every run must carry a declared branch, and results
across branches must not be pooled. Mitigation: run both and report the bracket.

**L2 — the fitted reconstruction is absent.** `491771090` returns zero rows from
three independent API probes. Consequence: the geometry the parameters were
fitted against is unknown, and the magnitude of the substitution cannot be
measured in either direction. Mitigation: none available. This is permanent, and
it means the best achievable status for any all-active run of this specimen is
"reconstruction under a substituted morphology".

**L3 — `truncated` depends on unobservable geometry.** The proximal diameter
comes from `Import3d`'s section aggregation, which is a NEURON implementation
detail. Consequence: even choosing `truncated` does not make the model fully
specified; it makes it specified *given a NEURON build and an SWC*. The distal
diameter is robust (plateau, 17 points equal to 1e−6); the proximal one is only
bounded at 0.2392–0.4374 µm.

**L4 — `stub` is insensitive to the morphology, and that is a hazard.**
Because the stub ignores the reconstruction entirely, it will produce the same
axonal geometry for *any* somatic SWC. A `stub` run cannot fail in a way that
reveals a morphology problem, so a plausible-looking trace from a `stub` run
carries less diagnostic information than the same trace from a `truncated` run.

**L5 — range-variable assignment is unverified without NEURON.** `cm`, `e_pas`
and `g_pas` are set with `setattr(section, name, value)`; that this applies to
every segment is NEURON's behaviour, not something this phase can confirm
statically. The perisomatic loader sets `e_pas` per segment explicitly, so the
two paths are not written alike.

**L6 — `passive.ra` is stated and ignored.** A reader who takes `"ra": 100` as
the model's axial resistivity is wrong on all four sections: the genome sets
88.1342 (soma), 76.0926 (axon), 119.149 (apic) and 73.8293 (dend) — −11.9%,
−23.9%, +19.1% and −26.2% from the stated value. Consequence: descriptive
statistics quoted from the descriptor must not be read off `passive`.

**L7 — no upstream reference output exists.** Allen's all-active fixture test is
stale (§4.6) and references a different cell and stimulus (0.33 nA, sweep 46,
18 spikes) anyway. There is no published voltage trace for `497233292`.
Consequence: there is no target against which a run could be called correct.
Only *self-consistency* and *plausibility against the recording* are available.

**L8 — the Phase 2E prediction is not evidence.** Phase 2E evaluated the
**perisomatic** model on sweeps 49–52. It says nothing about all-active
performance and must not be quoted as a baseline for it. A perisomatic result
and an all-active result differ for structural reasons (§4.5) before any axon
question arises.

**L9 — the held-out sample is one condition, not four trials.** Phase 2F
established that sweeps 49–52 carry bit-identical commands. Any future
all-active comparison over those sweeps has n = 1.

**L10 — one stimulus.** The model was fitted on a single sweep (41) at a single
amplitude — ≈ +230 pA per the phase brief, not independently measured in this
phase, because the current array belongs to the recording rather than to the
model. Consequence: agreement or disagreement at any other amplitude is an
extrapolation. This is a property of the published model, not a defect
introduced here.

**L11 — biological validity is out of reach.** Even a run that matches the
recording would not establish that the model is biologically right: the axon is
60 µm of synthetic cylinder standing in for a 708 µm arbour, the morphology is a
substitute, and the perisomatic class fits the same cell with a different
parameter set. Distinguishing "the model is good" from "the model and the
recording share a bias" requires held-out data this specimen does not have
(L9).

**L12 — the marker asset is unaudited relative to Phase 2A.** It has no 2A
digest. Consequence: none for execution (it is never read), but it means the
marker is the one asset whose provenance rests on a single observation, made in
this phase.

---

## 10. Go/no-go recommendation

### 10.1 The recommendation

**GO — for isolated execution validation, as a declared-branch reconstruction,
and under the conditions below.**

**NO-GO — for any claim of reproducing the published all-active model `497233292`.**

The distinction is the whole point of this phase. Nothing in §2, §3, §5, §6 or
§7 blocks execution: the descriptor is compatible, the mechanisms are complete,
all 42 parameters resolve, the manifest is groundable, the environment exists,
and the fitting provenance is clean. The only obstruction is a missing
specification, not a missing capability.

An isolated execution is therefore **scientifically defensible** if and only if
it is framed as: *"model `497233292` as specified by its published parameters,
on substitute morphology `674389901`, with axon treatment X chosen by this
project on date Y, in NEURON Z"* — and never as *"the Allen all-active model"*.

### 10.2 Mandatory conditions on Phase 2G-B

1. **Declare the branch in the invocation and in the result.** `--axon_type`
   must appear verbatim in the recorded command, and the branch must be in every
   table, figure and filename. No default may be relied on.
2. **Run both branches.** One run per branch, on the same stimulus, with the
   same seed-free determinism. Report them as a **bracket**, not as a result and
   a control. If they agree, that is a finding about the model's sensitivity; if
   they disagree, that is the measurement of the under-specification.
3. **Never pool the branches.** No mean, no fitted line, no aggregate statistic
   across the pair.
4. **Label the morphology substitution in every output.** `674389901`, not
   `491771090`, with L2 attached.
5. **Use sweep 38 as a plausibility bracket and one of 49–52 as the held-out
   test** (§7.3), and report n = 1 for the latter.
6. **Carry forward the Phase 2C environment unchanged.** Same WSL2 venv, same
   `--allensdk-src` source tree, modfile build outside the repository.
7. **Do not present any all-active trace as a comparison against Phase 2E.**
   L8.
8. **Do not tune anything.** If the result is wrong, the finding is that the
   model does not reproduce the recording under either branch under a
   substituted morphology — which is a valid and publishable outcome, and is the
   most likely one.

### 10.3 What would move the verdict

| Would move to | If |
|---|---|
| **READY FOR ISOLATED EXECUTION VALIDATION** | Allen published, or the project recovered, a record that `497233292` was produced with a specific `axon_type` — for example the original model-run configuration, an NWB of the model's own output, or the internal fitting invocation. No such artefact exists in the public API today. |
| **BLOCKED** | The descriptor digest changed; a needed mechanism were absent; the SWC lacked a section class the genome addresses; or the perisomatic loader had to be used. **None of these is the case.** |

### 10.4 What remains before Phase 2G-B

1. Adopt an explicit written branch policy (recommended: run both, bracket,
   never pool).
2. Decide the held-out design (§7.3) and freeze it before the first run, so the
   choice cannot be made after seeing the traces.
3. Stage the all-active model tree in WSL from
   `tmp/model_cache/models/all_active_497233292/` plus the substitute SWC, marker
   and the 16 modfiles — the Phase 2C staging scripts are the template.
4. Compile the mechanisms **in the WSL tree**, not in the repository cache.
5. Record the exact invocation for each branch as part of the deliverable.

**No simulation, refit, parameter perturbation or NEURON invocation was
performed in this phase.**

---

## Appendix A — corrections to earlier phases

Reported rather than silently repaired, per the brief's instruction on
mismatches. Neither correction changes any earlier result; both change how a
later reader should interpret one.

**A1 — Phase 2A §6.2 (and blocker B6): `truncated` does not "preserve the
reconstructed axon to 60 µm".**

Phase 2A states:

> `"truncated"` (documented default, "Legacy model") → keep the reconstructed axon
> but delete everything beyond 60 µm and splice in two 30 µm sections whose
> diameters are read from the SWC at the cut point.

and, in B6:

> `"truncated"` preserves the reconstructed axon to 60 µm.

Both are contradicted by `utils.py:399–401`, which deletes **every** section
whose name begins with `axon` — the whole 708 µm arbour, not the part beyond
60 µm — and then creates two fresh 30 µm sections. Nothing of the reconstruction
survives except two scalar diameters. Phase 2A also omits the attachment
difference (`0.5` vs `1.0`), which is the second axis of the divergence.

*Effect on conclusions:* none. Phase 2A's actual claim — that the two branches
produce different cells and that Allen publishes no value — is correct, and B6's
remedy ("record the chosen branch in every result") is exactly what §10 of this
report requires. The description of the mechanism was wrong; the verdict was
right.

**A2 — Phase 2A blocker B1: `neuron[0].hoc` should not include `cell.hoc`.**

Phase 2A states the manifest "Needs ... `neuron[0].hoc = ["cell.hoc","stdgui.hoc","import3d.hoc"]`".

Both shipped fixture manifests use `["stdgui.hoc", "import3d.hoc"]`, and
`cell.hoc` is only substituted by `update_default_cell_hoc` when the manifest
names it. Including it would load Allen's stub template over NEURON's own for no
benefit. The draft correctly omits it (§6.5).

*Effect on conclusions:* none; B1's main point (that the manifest must be
authored and is fully documented by Allen's fixtures) stands.

**A3 — Phase 2A's `axon_type` analysis stopped short of the structural
argument.** Phase 2A noted the freedom but justified the perisomatic comparison
as "a concrete reason to regard it as the [more reliable class]". §4.5 shows the
stronger result: the perisomatic axon carries **one** passive genome entry and
**zero** active mechanisms, so its geometry is electrically inert and cannot
inform the choice for a class whose axon carries **14** entries including
9 active mechanisms. The observation was right; the inference available from it
is stronger than was drawn.

---

## Appendix B — reproducing this audit

```bash
python scripts/audit_all_active_readiness.py
python scripts/audit_all_active_readiness.py --json tmp/phase2g_a_summary.json
python -m pytest tests/test_audit_all_active_readiness.py -q
python -m pytest tests -q
```

**Result of the run reported here.**

| Section | Checks | Failed |
|---|---:|---:|
| 1. Asset provenance | 25 | 0 |
| 2. Descriptor | 19 | 0 |
| 3. Mechanisms | 5 | 0 |
| 4. Loader contract | 37 | 0 |
| 5. Axon treatment | 10 | 0 |
| 6. Morphology | 8 | 0 |
| 7. Manifest | 20 | 0 |
| 8. Fitting provenance | 8 | 0 |
| 9. Environment | 5 | 0 |
| 10. Self-guard | 1 | 0 |
| **Total** | **138** | **0** |

Plus 14 observations. Exit status 0. Verdict **CONDITIONALLY READY**.

A failing check makes the script exit non-zero and forces the verdict to
`BLOCKED`; the only assertion in the audit that reports a *negative* finding
("neither branch can be established as the fitted configuration") is written as
a passing check, because the absence of a record is a fact, not a defect in the
audit.

The script reads files and imports nothing outside the standard library. It does
not import NEURON, compile a `.mod` file, construct a `Config`, or touch the
NWB.

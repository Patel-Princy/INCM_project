"""Phase 2G-B: execute the Allen all-active model for specimen 382982932.

What this script is, and what it is not
---------------------------------------
The descriptor cached for model 497233292 is Allen's published parameter set, but
the axon treatment it was fitted under was never published: ``axon_type`` is a
run-time argument that ``runner.load_description`` injects into ``biophys[1]``,
not a field of the descriptor or the manifest.  Phase 2G-A established that
neither ``stub`` nor ``truncated`` can be shown to be the original configuration.

Every run therefore produces a *reconstruction*, not a reproduction, and prints
the same sentence before it starts:

    All-active model 497233292 using published parameters, substitute
    morphology 674389901, and project-declared axon treatment <branch>.

The script executes exactly one (branch, sweep) pair per process so that the four
required runs are four independent processes with four independent output files.
It writes the trace, the applied-parameter readback, the comparison metrics and a
machine-readable summary into ``--out-dir``.

Usage
-----
    python scripts/validate_all_active_execution.py \
        --model-dir    ~/incm_phase2g_b/model \
        --allensdk-src <repo>/tmp/model_cache/2b/src/AllenSDK-2.16.2 \
        --repo-cache   <repo>/tmp/model_cache \
        --run-id A --axon-type stub --sweep 38 \
        --out-dir      ~/incm_phase2g_b/results/A_stub_sweep38

Exit codes
----------
0  the run executed and every pipeline check passed
1  the run executed but at least one pipeline check failed
2  the run could not be executed

A non-zero exit code is a statement about the *pipeline* only.  Whether the
prediction resembles the recording is reported, never asserted: agreement with a
recording is not a test that a model is correct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import shlex
import subprocess
import sys
import time

SPECIMEN = 382982932
MODEL_ID = 497233292
TEMPLATE_ID = 491455321
PERISOMATIC_MODEL = 473862496

#: The reconstruction the published parameters were fitted with is gone: three
#: RMA probes return zero rows for it.  Reconstruction 674389884 / SWC 674389901
#: is a substitute from the same specimen, not the fitted geometry.
FITTING_RECONSTRUCTION = 491771090
SUBSTITUTE_RECONSTRUCTION = 674389884
SUBSTITUTE_SWC = 674389901
MARKER_WELL_KNOWN = 674389910

ALL_ACTIVE_TYPE = "Biophysical - all active"
PERISOMATIC_TYPE = "Biophysical - perisomatic"
ALLENSDK_VERSION = "2.16.2"

DESCRIPTOR = "497233292_fit.json"
MORPHOLOGY = "674389901_382982932_m.swc"
MARKER = "674389910_382982932_m.marker"
STIMULUS_NWB = "382982932.nwb"
MANIFEST = "manifest.json"
OUTPUT_RELATIVE = os.path.join("work", STIMULUS_NWB)

#: Digest and byte count of every input.  A mismatch is a stop condition, not a
#: warning: the audit exists to prove that the thing executed is the thing
#: described in the report.
EXPECTED = {
    DESCRIPTOR: ("bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963",
                 5738),
    MORPHOLOGY: ("71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c",
                 335924),
    MARKER: ("3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925",
             373),
    STIMULUS_NWB: ("d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63",
                   94207824),
}

MECHANISMS = (
    "CaDynamics", "Ca_HVA", "Ca_LVA", "Ih", "Im", "Im_v2",
    "K_P", "K_T", "Kd", "Kv2like", "Kv3_1", "NaTa", "NaTs", "NaV", "Nap", "SK",
)

#: Published junction potential, and the shift the output stage applies.  The
#: pipeline writes (V_sim + 14 mV); it never adds 14 mV to a model parameter.
JUNCTION_MV = -14.0
OUTPUT_SHIFT_MV = 14.0

FITTING_SWEEP = 41
PERISOMATIC_FITTING_SWEEP = 38
BRACKET_SWEEP = 38
HELD_OUT_SWEEP = 49
COARSE_SWEEPS = tuple(range(24, 44))
FINEST_SWEEPS = (49, 50, 51, 52)

AXON_BRANCHES = ("stub", "truncated")
RUN_PLAN = {
    "A": ("stub", BRACKET_SWEEP),
    "B": ("stub", HELD_OUT_SWEEP),
    "C": ("truncated", BRACKET_SWEEP),
    "D": ("truncated", HELD_OUT_SWEEP),
}

MODEL_CLAIM = ("All-active model %d using published parameters, substitute "
               "morphology %d, and project-declared axon treatment %%s"
               % (MODEL_ID, SUBSTITUTE_SWC))


# --------------------------------------------------------------------- helpers
def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Checker:
    """Accumulate pass/fail rows so the report can cite exact counts."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, bool | None, str]] = []
        self.metric_rows: list[tuple[str, str]] = []
        self.section_name = ""

    def heading(self, title: str) -> None:
        self.section_name = title
        print()
        print("=" * 78)
        print(title)
        print("=" * 78)

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.rows.append((self.section_name, label, bool(ok), detail))
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label,
                               ("  -- " + detail) if detail else ""))
        return bool(ok)

    def observe(self, label: str, detail: str = "") -> None:
        self.rows.append((self.section_name, label, None, detail))
        print("  [obs ] %s%s" % (label, ("  -- " + detail) if detail else ""))

    def metric(self, label: str, value) -> None:
        text = value if isinstance(value, str) else _fmt(value)
        self.metric_rows.append((label, text))
        print("  [met ] %s = %s" % (label, text))

    def skip(self, label: str, detail: str = "") -> None:
        self.rows.append((self.section_name, label, None, detail))
        print("  [skip] %s%s" % (label, ("  -- " + detail) if detail else ""))

    def failures(self) -> int:
        return sum(1 for _, _, ok, _ in self.rows if ok is False)

    def tally(self) -> dict:
        by_section: dict[str, int] = {}
        for section, _, _, _ in self.rows:
            by_section[section] = by_section.get(section, 0) + 1
        return {
            "checks": sum(1 for _, _, ok, _ in self.rows if ok is not None),
            "passed": sum(1 for _, _, ok, _ in self.rows if ok is True),
            "failed": self.failures(),
            "skipped": sum(1 for _, _, ok, _ in self.rows if ok is None),
            "metrics": len(self.metric_rows),
            "by_section": by_section,
        }

    def summary(self) -> int:
        tally = self.tally()
        print()
        print("-" * 78)
        print("checks %d | passed %d | failed %d | observations %d"
              % (tally["checks"], tally["passed"], tally["failed"],
                 tally["skipped"]))
        return tally["failed"]


def _fmt(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if value == 0:
            return "0"
        if abs(value) >= 1e4 or abs(value) < 1e-3:
            return "%.4e" % value
        return "%.4f" % value
    return str(value)


def model_claim(branch: str) -> str:
    """The sentence every output of this phase must carry."""
    return MODEL_CLAIM % branch


# ------------------------------------------------------------------ provenance
def verify_assets(checker: Checker, model_dir: pathlib.Path,
                  repo_cache: pathlib.Path) -> dict:
    """Prove the executed inputs are the audited inputs."""
    checker.heading("A. Asset provenance")

    facts: dict = {"sha256": {}, "bytes": {}}
    for name, (expected_sha, expected_bytes) in EXPECTED.items():
        path = model_dir / name
        if not checker.check(path.exists(), "%s is staged" % name, str(path)):
            continue
        digest = sha256_of(path)
        size = path.stat().st_size
        facts["sha256"][name] = digest
        facts["bytes"][name] = size
        checker.check(digest == expected_sha, "%s digest matches" % name,
                      digest[:16] + "..." if digest != expected_sha else "ok")
        checker.check(size == expected_bytes, "%s byte count matches" % name,
                      "%d B" % size)

    # --- the descriptor must be the all-active parameter set, and untouched
    descriptor = load_json(model_dir / DESCRIPTOR)
    checker.check(sorted(descriptor) == ["conditions", "fitting", "genome", "passive"],
                  "descriptor holds only the four parameter sections",
                  ", ".join(sorted(descriptor)))
    checker.check(not ({"model_type", "runs", "manifest", "neuron", "biophys"}
                       & set(descriptor)),
                  "descriptor carries no wiring, run list or axon_type",
                  "parameters only: the manifest wires, the argument selects the axon")
    genome = descriptor["genome"]
    checker.check(len(genome) == 42, "descriptor genome has 42 entries",
                  "%d" % len(genome))
    checker.check(descriptor["passive"][0]["ra"] == 100,
                  "descriptor still carries the published passive Ra of 100",
                  "dead field: the genome overwrites Ra on every section array")
    checker.check(descriptor["fitting"][0]["sweeps"] == [FITTING_SWEEP],
                  "descriptor fitting sweep is still 41",
                  str(descriptor["fitting"][0]["sweeps"]))
    checker.check(descriptor["fitting"][0]["junction_potential"] == JUNCTION_MV,
                  "descriptor junction potential is still -14 mV",
                  str(descriptor["fitting"][0]["junction_potential"]))

    # --- mechanism set, byte for byte against the Phase 2A manifest
    assets = load_json(repo_cache / "assets_2a.json")
    recorded = {entry["path"].split("/")[-1]: entry["sha256"]
                for entry in assets["assets"]}
    modfiles = sorted((model_dir / "modfiles").glob("*.mod"))
    mismatched, missing = [], []
    for path in modfiles:
        expected = recorded.get(path.name)
        if expected is None:
            missing.append(path.name)
        elif sha256_of(path) != expected:
            mismatched.append(path.name)
    checker.check(len(modfiles) == 16, "canonical mechanism set has 16 files",
                  "%d" % len(modfiles))
    checker.check(not missing, "every .mod is recorded in the Phase 2A manifest",
                  ", ".join(missing) if missing else "16/16")
    checker.check(not mismatched, "no .mod differs from its Phase 2A digest",
                  ", ".join(mismatched) if mismatched else "16/16")
    facts["modfiles"] = {path.name: sha256_of(path) for path in modfiles}

    checker.observe("AllenSDK source tree",
                    str(repo_cache / "2b" / "src"
                        / ("AllenSDK-%s" % ALLENSDK_VERSION)))
    return facts


def verify_allensdk_source(checker: Checker, allensdk_src: pathlib.Path) -> dict:
    """Version and loader-source identity of the AllenSDK tree that will import."""
    init = allensdk_src / "allensdk" / "__init__.py"
    utils = allensdk_src / "allensdk" / "model" / "biophysical" / "utils.py"
    hoc = (allensdk_src / "allensdk" / "model" / "biophys_sim" / "neuron"
           / "hoc_utils.py")
    runner = allensdk_src / "allensdk" / "model" / "biophysical" / "runner.py"

    checker.check(allensdk_src.is_dir(), "AllenSDK source tree exists",
                  allensdk_src.name)
    checker.check(allensdk_src.name == "AllenSDK-%s" % ALLENSDK_VERSION,
                  "AllenSDK source tree is the v2.16.2 release",
                  allensdk_src.name)
    for path in (init, utils, hoc, runner):
        checker.check(path.exists(), "%s present" % path.name, "")

    text = utils.read_text(encoding="utf-8")
    # Structural proof rather than a digest: the digest table for whole files
    # drifts whenever a comment changes, the markers below cannot.
    checker.check('axon_type = description.data["biophys"][1]["axon_type"]' in text,
                  "create_utils still reads axon_type from biophys[1]")
    checker.check(text.count("for c in passive[\"cm\"]:") == 2,
                  "one live and one commented-out perisomatic cm loop")
    runner_text = runner.read_text(encoding="utf-8")
    checker.check("default='truncated', choices=['stub', 'truncated']" in runner_text,
                  "runner CLI default for --axon_type is still truncated",
                  "we never rely on it: --axon-type is always explicit")

    return {
        "path": str(allensdk_src),
        "sha256": {path.name: sha256_of(path) for path in (utils, hoc, runner)},
    }


def verify_manifest(checker: Checker, model_dir: pathlib.Path) -> dict:
    """Every manifest field must be grounded in AllenSDK source or Phase 2A/2B."""
    checker.heading("B. Manifest and loader configuration")

    manifest = load_json(model_dir / MANIFEST)
    biophys = manifest["biophys"]
    checker.check(len(biophys) == 1,
                  "manifest carries a single biophys entry",
                  "%d" % len(biophys))
    checker.check(biophys[0]["model_type"] == ALL_ACTIVE_TYPE,
                  "manifest selects the all-active loader", biophys[0]["model_type"])
    checker.check("axon_type" not in json.dumps(manifest),
                  "manifest records no axon_type: the branch is a run-time argument",
                  "confirmed absent")

    run_params = manifest["runs"][0]
    sweeps = list(run_params["sweeps"])
    checker.check(tuple(sweeps) == COARSE_SWEEPS,
                  "manifest sweeps are the 20 recorded COARSE sweeps 24-43",
                  "%d..%d (%d)" % (sweeps[0], sweeps[-1], len(sweeps)))
    checker.check(FITTING_SWEEP in sweeps,
                  "the all-active fitting sweep 41 is inside the manifest runs")
    checker.check(HELD_OUT_SWEEP not in sweeps,
                  "the held-out sweep 49 is outside the manifest runs",
                  "it is reached only because --sweep is passed explicitly")
    long_square = run_params["sweeps_by_type"]["Long Square"]
    checker.check(BRACKET_SWEEP in long_square and HELD_OUT_SWEEP in long_square,
                  "both evaluation sweeps are Long Square",
                  "38 and 49")

    paths = {entry["key"]: entry["spec"] for entry in manifest["manifest"]}
    checker.check(paths.get("MORPHOLOGY") == MORPHOLOGY,
                  "MORPHOLOGY resolves to the substitute SWC",
                  paths.get("MORPHOLOGY", "?"))
    checker.check(paths.get("MARKER") == MARKER,
                  "MARKER resolves to the substitute marker",
                  paths.get("MARKER", "?"))
    checker.check(paths.get("stimulus_path") == STIMULUS_NWB,
                  "stimulus_path resolves to the staged recording")
    checker.check(paths.get("output_path") == STIMULUS_NWB,
                  "output_path writes into work/, leaving the stimulus intact")
    checker.check("cell.hoc" not in manifest["neuron"][0]["hoc"],
                  "no cell.hoc placeholder for AllenSDK to silently substitute",
                  ", ".join(manifest["neuron"][0]["hoc"]))

    return {
        "manifest": str(model_dir / MANIFEST),
        "sha256": sha256_of(model_dir / MANIFEST),
        "model_type": biophys[0]["model_type"],
        "manifest_sweeps": sweeps,
        "axon_type_in_manifest": False,
    }


# ------------------------------------------------------------------ compilation
def compile_mechanisms(checker: Checker, model_dir: pathlib.Path,
                       log_path: pathlib.Path) -> dict:
    checker.heading("C. Mechanism compilation")

    nrnivmodl = pathlib.Path(sys.executable).with_name("nrnivmodl")
    if not nrnivmodl.exists():
        checker.check(False, "nrnivmodl is available", str(nrnivmodl))
        return {"compiled": False}

    started = time.time()
    completed = subprocess.run([str(nrnivmodl), "modfiles/"],
                               cwd=str(model_dir), capture_output=True, text=True)
    elapsed = time.time() - started
    log_path.write_text(
        "command: %s modfiles/\ncwd: %s\nrc: %d\n--- stdout ---\n%s\n"
        "--- stderr ---\n%s\n"
        % (nrnivmodl, model_dir, completed.returncode, completed.stdout,
           completed.stderr), encoding="utf-8")

    combined = completed.stdout + completed.stderr
    warnings = sum(1 for line in combined.splitlines()
                   if "warning" in line.lower())
    errors = sum(1 for line in combined.splitlines() if "error" in line.lower())
    lib = model_dir / "x86_64" / "libnrnmech.so"

    checker.check(completed.returncode == 0, "nrnivmodl exited 0",
                  "%.1f s" % elapsed)
    checker.check(errors == 0, "no compiler errors", "%d" % errors)
    checker.check(warnings == 0, "no compiler warnings", "%d" % warnings)
    checker.check(lib.exists(), "libnrnmech.so was produced",
                  "%d B" % lib.stat().st_size if lib.exists() else "")
    checker.check(str(model_dir).startswith(str(pathlib.Path.home())),
                  "compiled mechanisms live outside the repository",
                  str(model_dir))

    return {
        "compiled": completed.returncode == 0 and lib.exists(),
        "returncode": completed.returncode,
        "warnings": warnings,
        "errors": errors,
        "elapsed_s": round(elapsed, 2),
        "library": str(lib) if lib.exists() else None,
        "library_bytes": lib.stat().st_size if lib.exists() else None,
        "log": str(log_path),
    }


# -------------------------------------------------------------------- execution
def _class_of(name: str) -> str:
    return name.split("[")[0]


def read_section_attribute(section, name: str):
    """Read one genome parameter back off a section.

    ``e_pas`` and ``g_pas`` are not attributes of ``nrn.Section``; NEURON maps
    the first onto ``pas.e`` and the second onto ``pas.g`` per segment, which is
    what makes Allen's all-active genome -- which describes the passive
    conductance per section array -- expressible at all.
    """
    if name == "e_pas":
        return float(section(0.5).pas.e)
    if name == "g_pas":
        return float(section(0.5).pas.g)
    return float(getattr(section, name))


def snapshot_cell_state(utils, descriptor: dict) -> dict:
    """Read the configured cell back and prove the genome landed where intended.

    ``AllActiveUtils.load_cell_parameters`` applies each of the 42 genome entries
    with ``setattr`` inside a ``hasattr(h, section_array)`` gate that has no
    ``else``: a missing section array drops an entry in silence.  The only
    defence is to read each value back, which is what this does.
    """
    h = utils.h
    inventory: dict[str, dict] = {}
    first_section: dict[str, object] = {}
    for sec in h.allsec():
        base = _class_of(sec.name())
        entry = inventory.setdefault(
            base, {"n_sections": 0, "area_um2": 0.0, "length_um": 0.0,
                   "diam_min_um": float("inf"), "diam_max_um": 0.0})
        entry["n_sections"] += 1
        entry["area_um2"] += float(h.area(0.5, sec=sec))
        entry["length_um"] += float(sec.L)
        entry["diam_min_um"] = min(entry["diam_min_um"], float(sec.diam))
        entry["diam_max_um"] = max(entry["diam_max_um"], float(sec.diam))
        first_section.setdefault(base, sec)

    applied, dropped = [], []
    for entry in descriptor["genome"]:
        name, section_array = entry["name"], entry["section"]
        target = float(entry["value"])
        if section_array == "glob":
            applied.append({"section": section_array, "name": name,
                            "target": target, "readback": None,
                            "n_sections": 0, "ok": None})
            continue
        if section_array not in first_section:
            dropped.append({"section": section_array, "name": name,
                            "target": target, "reason": "section array absent"})
            continue
        observed = read_section_attribute(first_section[section_array], name)
        scale = max(abs(target), 1e-12)
        applied.append({
            "section": section_array, "name": name, "mechanism": entry["mechanism"],
            "target": target, "readback": observed,
            "n_sections": inventory[section_array]["n_sections"],
            "ok": abs(observed - target) <= 1e-6 * scale,
        })

    axon = list(h.axon) if hasattr(h, "axon") else []
    geometry = {"n_sections": len(h.axon)}
    if axon:
        parent = axon[0].parentseg()
        geometry = {
            "n_sections": len(axon),
            "diam_um": [round(float(sec.diam), 6) for sec in axon],
            "length_um": [round(float(sec.L), 6) for sec in axon],
            "nseg": [int(sec.nseg) for sec in axon],
            "area_um2": round(sum(float(h.area(0.5, sec=sec)) for sec in axon), 6),
            "parent": (parent.sec.name() if parent is not None else None),
            "parent_x": (round(float(parent.x), 6) if parent is not None else None),
        }

    return {
        "inventory": {key: {k: (round(v, 6) if isinstance(v, float) else v)
                            for k, v in value.items()}
                      for key, value in inventory.items()},
        "applied": applied,
        "dropped": dropped,
        "axon_geometry": geometry,
        "n_sections_total": int(len(list(h.allsec()))),
    }


def execute(checker: Checker, model_dir: pathlib.Path, allensdk_src: pathlib.Path,
            branch: str, sweep: int, log_path: pathlib.Path) -> dict:
    """Run one (branch, sweep) pair through AllenSDK's own runner."""
    checker.heading("D. Execution: %s axon, sweep %d" % (branch, sweep))

    try:
        import numpy as np
        import neuron
        from allensdk.model.biophysical import runner
        from allensdk.model.biophysical import utils as biophys_utils
    except Exception as exc:                      # noqa: BLE001 - reported verbatim
        checker.check(False, "AllenSDK v2.16.2 and NEURON import",
                      "%s: %s" % (type(exc).__name__, exc))
        return {"executed": False, "reason": "import: %s" % exc}

    checker.check(True, "AllenSDK imports from the v2.16.2 source tree",
                  str(allensdk_src.name))
    checker.check(True, "NEURON imports", neuron.__version__)
    checker.check(os.getcwd() == str(model_dir.resolve()),
                  "cwd is the model directory", os.getcwd())

    missing = []
    for mechanism in MECHANISMS:
        section = neuron.h.Section(name="mech_probe_" + mechanism)
        try:
            section.insert(mechanism)
        except Exception:                          # noqa: BLE001
            missing.append(mechanism)
        finally:
            neuron.h.delete_section(sec=section)
    checker.check(not missing, "all 16 compiled mechanisms are loadable",
                  "%d/16" % (16 - len(missing)))
    residual = len(list(neuron.h.allsec()))
    checker.check(residual == 0, "mechanism probe left no sections behind",
                  "%d" % residual)

    descriptor = load_json(model_dir / DESCRIPTOR)
    state: dict = {}
    captured: dict = {}

    original_record = biophys_utils.Utils.get_recorded_data
    original_load = biophys_utils.AllActiveUtils.load_cell_parameters

    def instrumented_record(self, vec):
        raw_v = np.array(vec["v"], dtype=float)
        raw_t = np.array(vec["t"], dtype=float)
        result = original_record(self, vec)
        captured["raw_v_mv"] = raw_v
        captured["raw_t_ms"] = raw_t
        captured["out_v"] = np.array(result["v"], dtype=float)
        captured["out_t"] = np.array(result["t"], dtype=float)
        return result

    def instrumented_load(self):
        original_load(self)
        state.update(snapshot_cell_state(self, descriptor))

    biophys_utils.Utils.get_recorded_data = instrumented_record
    biophys_utils.AllActiveUtils.load_cell_parameters = instrumented_load

    rows: list[str] = []

    class _Capture:
        def write(self, text):
            if text.strip():
                rows.append(text.rstrip())

        def flush(self):
            pass

    import logging
    stream = _Capture()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    started = time.time()
    error = None
    loader_facts: dict = {}
    try:
        # The branch is passed explicitly.  ``args_dict.get('axon_type',
        # 'truncated')`` inside load_description means an omitted branch would
        # silently become truncated, which is the one thing 2G-A forbids.
        args = {"manifest_file": MANIFEST, "axon_type": branch}
        description = runner.load_description(args)
        checker.check(len(description.data["biophys"]) == 2,
                      "load_description appended a second biophys entry",
                      "%d" % len(description.data["biophys"]))
        checker.check(description.data["biophys"][1].get("axon_type") == branch,
                      "the requested branch reached biophys[1]", branch)
        checker.check(description.data["biophys"][0]["model_type"] == ALL_ACTIVE_TYPE,
                      "biophys[0] still dispatches to the all-active loader",
                      description.data["biophys"][0]["model_type"])

        utils = biophys_utils.create_utils(description)
        checker.check(isinstance(utils, biophys_utils.AllActiveUtils),
                      "create_utils returned AllActiveUtils",
                      type(utils).__name__)
        checker.check(getattr(utils, "axon_type", None) == branch,
                      "AllActiveUtils carries the requested axon treatment",
                      str(getattr(utils, "axon_type", None)))
        loader_facts["utils_class"] = type(utils).__name__

        runner.run(args, sweeps=[sweep], procs=1)
    except Exception as exc:                   # noqa: BLE001 - reported verbatim
        error = "%s: %s" % (type(exc).__name__, exc)
        import traceback
        rows.append(traceback.format_exc())
        checker.check(False, "runner.run completed without raising", error)
    finally:
        elapsed = time.time() - started
        root.removeHandler(handler)
        biophys_utils.Utils.get_recorded_data = original_record
        biophys_utils.AllActiveUtils.load_cell_parameters = original_load
        log_path.write_text("\n".join(rows), encoding="utf-8")

    output_nwb = model_dir / OUTPUT_RELATIVE
    checker.check(output_nwb.exists(), "output NWB was written",
                  "%d B" % output_nwb.stat().st_size if output_nwb.exists() else "")

    # --- the 42 genome entries, read back off the configured cell
    applied = state.get("applied", [])
    failed = [row for row in applied if row.get("ok") is False]
    checker.check(len(applied) == 42, "all 42 genome entries were read back",
                  "%d" % len(applied))
    checker.check(not failed, "every genome entry matches the configured cell",
                  "%d mismatched" % len(failed))
    checker.check(not state.get("dropped"),
                  "no genome entry was dropped by an absent section array",
                  "%d dropped" % len(state.get("dropped", [])))
    for base in ("soma", "axon", "apic", "dend"):
        inventory = state.get("inventory", {}).get(base)
        checker.check(inventory is not None and inventory["n_sections"] > 0,
                      "section class %s exists after morphology construction" % base,
                      ("%d sections, %.1f um2" % (inventory["n_sections"],
                                                  inventory["area_um2"])
                       if inventory else "absent"))

    geometry = state.get("axon_geometry", {})
    checker.check(geometry.get("n_sections") == 2,
                  "the axon was replaced with exactly two sections",
                  str(geometry.get("n_sections")))
    checker.observe("axon geometry under %s" % branch,
                    json.dumps({k: geometry.get(k) for k in
                                ("diam_um", "length_um", "nseg", "area_um2",
                                 "parent", "parent_x")}))

    return {
        "executed": output_nwb.exists() and error is None,
        "error": error,
        "elapsed_s": round(elapsed, 2),
        "output_nwb": str(output_nwb),
        "output_nwb_bytes": (output_nwb.stat().st_size
                             if output_nwb.exists() else None),
        "neuron_version": neuron.__version__,
        "log": str(log_path),
        "captured": captured,
        "state": state,
        "args": args,
        "loader": loader_facts,
        "sweep": sweep,
    }


def verify_convention(checker: Checker, captured: dict) -> dict:
    """Prove V_written = V_sim + 14 mV, applied at the output stage only."""
    import numpy as np

    checker.heading("E. Output convention")

    if not captured:
        checker.skip("junction convention verified", "no captured trace")
        return {}

    raw, out = captured["raw_v_mv"], captured["out_v"]
    n = min(raw.size, out.size)
    expected = (raw[:n] - JUNCTION_MV) * 1e-3
    delta = float(np.max(np.abs(out[:n] - expected)))

    checker.check(delta < 1e-12,
                  "written = (V_sim - junction) in volts, output only",
                  "max |delta| = %.3e V" % delta)
    checker.check(float(np.max(np.abs(raw))) > 1.0,
                  "the simulator vector is in mV and unshifted",
                  "%.2f..%.2f mV" % (raw.min(), raw.max()))
    checker.metric("output_shift_mv", round(float(out[:n].max() * 1e3
                                                 - raw[:n].max()), 9))
    checker.check(abs(float(out[:n].max() * 1e3 - raw[:n].max())
                      - OUTPUT_SHIFT_MV) < 1e-9,
                  "peak shifted by exactly +14 mV",
                  "%.3f -> %.3f mV" % (raw[:n].max(), out[:n].max() * 1e3))

    return {
        "max_abs_delta_v": delta,
        "junction_mv": JUNCTION_MV,
        "output_shift_mv": OUTPUT_SHIFT_MV,
        "raw_min_mv": float(raw.min()),
        "raw_max_mv": float(raw.max()),
        "written_min_mv": float(out[:n].min()) * 1e3,
        "written_max_mv": float(out[:n].max()) * 1e3,
        "raw_samples": int(raw.size),
        "written_samples": int(out.size),
    }


# ------------------------------------------------------------------ settling
def settling_report(v_mv, rate: float, onset_index: int,
                    window_ms: float = 100.0) -> dict:
    """How far the trace has drifted when the step starts.

    The protocol gives every sweep 1020 ms of lead-in before the step, and the
    descriptor's ``v_init`` is -90 mV.  A model started there need not have
    reached its steady state by 1020 ms, in which case the pre-step "baseline"
    is a transient average rather than a resting potential, and every
    comparison that leans on it is contaminated.  Measuring the approach
    separately from the average is what keeps that visible.
    """
    import numpy as np

    dt = 1e3 / rate
    marks = {}
    for label, when_ms in (("t_20ms", 20.0), ("t_200ms", 200.0),
                           ("t_500ms", 500.0), ("t_800ms", 800.0),
                           ("t_1000ms", 1000.0)):
        index = int(round(when_ms / dt))
        marks[label] = float(v_mv[index]) if index < v_mv.size else float("nan")
    marks["t_step_onset"] = (float(v_mv[onset_index - 1])
                              if onset_index else float("nan"))

    last = int(round(window_ms / dt))
    tail = v_mv[max(0, onset_index - last):onset_index]
    recent = int(round(20.0 / dt))
    before = v_mv[max(0, onset_index - recent):onset_index]
    marks["settled_baseline_mv"] = float(np.mean(tail)) if tail.size else float("nan")
    marks["drift_last_20ms_mv"] = (float(before[-1] - before[0])
                                    if before.size > 1 else float("nan"))
    marks["drift_full_leadin_mv"] = (float(v_mv[onset_index - 1] - v_mv[0])
                                       if onset_index else float("nan"))
    return marks


def compare(checker: Checker, model_dir: pathlib.Path, branch: str, sweep: int,
            p2e) -> dict:
    """Compare the written simulation with the recording, with Phase 2E metrics."""
    checker.heading("F. Recording versus prediction: %s axon, sweep %d"
                    % (branch, sweep))

    import numpy as np
    from allensdk.core.nwb_data_set import NwbDataSet

    rec_ds = NwbDataSet(str(model_dir / STIMULUS_NWB))
    recorded = rec_ds.get_sweep(sweep)
    # NWB stores the response in volts; every metric in Phase 2C and 2E is in
    # millivolts, and so is every threshold in the shared detector.
    v_rec = np.asarray(recorded["response"], dtype=float) * 1e3
    stim_pa = np.asarray(recorded["stimulus"], dtype=float) * 1e12
    rate = float(recorded["sampling_rate"])
    rec_times = np.asarray(rec_ds.get_spike_times(sweep), dtype=float)

    sim_ds = NwbDataSet(str(model_dir / OUTPUT_RELATIVE))
    simulated = sim_ds.get_sweep(sweep)
    v_sim = np.asarray(simulated["response"], dtype=float) * 1e3
    sim_times = np.asarray(sim_ds.get_spike_times(sweep), dtype=float)
    stim_roundtrip = np.array_equal(
        np.asarray(simulated["stimulus"], dtype=float),
        np.asarray(recorded["stimulus"], dtype=float))

    rec_idx = np.round(rec_times * rate).astype(int)
    sim_idx = np.round(sim_times * rate).astype(int)

    rec_desc = p2e.describe_trace("recorded %d" % sweep, v_rec, rate, stim_pa,
                                  rec_idx)
    sim_desc = p2e.describe_trace("simulated %s %d" % (branch, sweep), v_sim,
                                  rate, stim_pa, sim_idx)
    rec_desc["_v_mv"] = v_rec
    sim_desc["_v_mv"] = v_sim
    pair = p2e.compare_traces(rec_desc, sim_desc, stim_pa, rate)
    pair["stimulus_roundtrip_identical"] = bool(stim_roundtrip)

    # --- the single observed spike in sweep 49, examined directly
    n = min(v_rec.size, v_sim.size)
    dt = 1e3 / rate
    if rec_desc["n_in_step"]:
        centre = int(round(rec_desc["first_in_step_ms"] / dt))
        half = int(round(5.0 / dt))
        window = slice(max(0, centre - half), min(n, centre + half + 1))
        pair["recorded_first_spike_window_ms"] = [-5.0, 5.0]
        pair["rmse_around_recorded_first_spike_mv"] = float(np.sqrt(np.mean(
            (v_sim[window] - v_rec[window]) ** 2)))
        pair["peak_around_recorded_first_spike_mv"] = float(np.max(v_sim[window]))
        pair["recorded_peak_around_first_spike_mv"] = float(np.max(v_rec[window]))
        pair["simulated_minus_recorded_peak_mv"] = (
            pair["peak_around_recorded_first_spike_mv"]
            - pair["recorded_peak_around_first_spike_mv"])
        pair["simulated_reaches_zero_mv"] = bool(float(np.max(v_sim[window])) >= 0.0)
        checker.metric("simulated_minus_recorded_peak_mv",
                       pair["simulated_minus_recorded_peak_mv"])
        checker.metric("rmse_around_recorded_first_spike_mv",
                       pair["rmse_around_recorded_first_spike_mv"])
        checker.observe("the observed spike at %.3f ms"
                        % rec_desc["first_in_step_ms"],
                        "model peak %.2f mV there, cell peak %.2f mV"
                        % (pair["peak_around_recorded_first_spike_mv"],
                           pair["recorded_peak_around_first_spike_mv"]))

    checker.check(abs(float(np.median(stim_pa[stim_pa > 1])) - 170.0) < 1.0,
                  "the stimulus plateau is the +170 pA command",
                  "%.3f pA" % float(np.median(stim_pa[stim_pa > 1])))
    checker.check(stim_roundtrip,
                  "the simulated NWB carries the unmodified stimulus")
    checker.check(int(rec_desc["n_samples"]) == int(sim_desc["n_samples"]),
                  "recorded and simulated traces have the same length",
                  "%d vs %d" % (rec_desc["n_samples"], sim_desc["n_samples"]))
    checker.check(not np.isnan(v_sim).any(),
                  "the simulated trace contains no NaN")

    checker.metric("recorded_spikes_in_step", rec_desc["n_in_step"])
    checker.metric("simulated_spikes_in_step", sim_desc["n_in_step"])
    checker.metric("spike_count_delta", pair["spike_count_delta"])
    checker.metric("first_latency_recorded_ms",
                   rec_desc["first_in_step_latency_ms"])
    checker.metric("first_latency_simulated_ms",
                   sim_desc["first_in_step_latency_ms"])
    checker.metric("rmse_whole_mv", pair["rmse_whole_mv"])
    checker.metric("rmse_in_step_mv", pair["rmse_in_step_mv"])
    checker.metric("rmse_in_step_away_from_spikes_mv",
                   pair["rmse_in_step_away_from_spikes_mv"])
    checker.metric("corr_whole", pair["corr_whole"])
    checker.metric("corr_in_step", pair["corr_in_step"])
    checker.metric("baseline_delta_mv", pair["baseline_delta_mv"])
    checker.metric("plateau_recorded_mv", rec_desc["plateau_mv"])
    checker.metric("plateau_simulated_mv", sim_desc["plateau_mv"])

    # --- settling, measured on the same window in both traces
    onset_index = int(rec_desc["step_onset_sample"])
    rec_settle = settling_report(v_rec, rate, onset_index)
    sim_settle = settling_report(v_sim, rate, onset_index)
    pair["settled_baseline_recorded_mv"] = rec_settle["settled_baseline_mv"]
    pair["settled_baseline_simulated_mv"] = sim_settle["settled_baseline_mv"]
    pair["settled_baseline_delta_mv"] = (sim_settle["settled_baseline_mv"]
                                         - rec_settle["settled_baseline_mv"])
    pair["drift_last_20ms_simulated_mv"] = sim_settle["drift_last_20ms_mv"]
    pair["drift_full_leadin_simulated_mv"] = sim_settle["drift_full_leadin_mv"]
    pair["excitability_margin_mv"] = (sim_desc["v_max_mv"]
                                       - sim_settle["settled_baseline_mv"])
    checker.metric("settled_baseline_recorded_mv",
                   rec_settle["settled_baseline_mv"])
    checker.metric("settled_baseline_simulated_mv",
                   sim_settle["settled_baseline_mv"])
    checker.metric("drift_last_20ms_simulated_mv",
                   sim_settle["drift_last_20ms_mv"])
    checker.metric("excitability_margin_mv", pair["excitability_margin_mv"])
    if abs(sim_settle["drift_last_20ms_mv"]) > 1.0:
        checker.observe("the model is still moving when the step starts",
                        "%.3f mV in the last 20 ms of lead-in"
                        % sim_settle["drift_last_20ms_mv"])

    return {
        "recorded": p2e._plain(rec_desc),
        "simulated": p2e._plain(sim_desc),
        "pair": p2e._plain(pair),
        "recorded_spike_times_s": [float(x) for x in rec_times],
        "simulated_spike_times_s": [float(x) for x in sim_times],
        "settling": {"recorded": rec_settle, "simulated": sim_settle},
    }


# ------------------------------------------------------------------------- main
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--allensdk-src", required=True)
    parser.add_argument("--repo-cache", required=True)
    parser.add_argument("--run-id", required=True, choices=sorted(RUN_PLAN))
    parser.add_argument("--axon-type", required=True, choices=AXON_BRANCHES)
    parser.add_argument("--sweep", required=True, type=int)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--skip-compile", action="store_true")
    parser.add_argument("--skip-compare", action="store_true")
    args = parser.parse_args(argv)

    planned_branch, planned_sweep = RUN_PLAN[args.run_id]
    if (args.axon_type, args.sweep) != (planned_branch, planned_sweep):
        print("run %s is planned as (%s, sweep %d), not (%s, sweep %d)"
              % (args.run_id, planned_branch, planned_sweep, args.axon_type,
                 args.sweep))
        return 2
    if args.sweep == FITTING_SWEEP:
        print("sweep %d fitted this model; it is excluded from evaluation"
              % FITTING_SWEEP)
        return 2

    model_dir = pathlib.Path(args.model_dir).expanduser().resolve()
    allensdk_src = pathlib.Path(args.allensdk_src).expanduser().resolve()
    repo_cache = pathlib.Path(args.repo_cache).expanduser().resolve()
    out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(model_dir)
    sys.path.insert(0, str(allensdk_src))
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

    # The Phase 2E metric conventions are reused verbatim so that the all-active
    # numbers sit in the same table as the perisomatic ones without translation.
    import evaluate_finest_held_out as p2e

    checker = Checker()
    print("Phase 2G-B - all-active execution validation")
    print("run       : %s (%s axon, sweep %d)" % (args.run_id, args.axon_type,
                                                  args.sweep))
    print("model     : %s" % model_claim(args.axon_type))
    print("model dir : %s" % model_dir)
    print("allensdk  : %s" % allensdk_src)
    print("python    : %s | %s" % (sys.version.split()[0], sys.executable))

    facts: dict = {
        "phase": "2G-B",
        "run_id": args.run_id,
        "axon_type": args.axon_type,
        "sweep": args.sweep,
        "specimen": SPECIMEN,
        "model_id": MODEL_ID,
        "template_id": TEMPLATE_ID,
        "model_claim": model_claim(args.axon_type),
        # The literal command line, not a reconstruction of it.
        "command": shlex.join([sys.executable] + list(sys.argv)),
        "fitting_sweep_excluded": FITTING_SWEEP,
    }

    facts["assets"] = verify_assets(checker, model_dir, repo_cache)
    facts["allensdk"] = verify_allensdk_source(checker, allensdk_src)
    facts["manifest"] = verify_manifest(checker, model_dir)

    if args.skip_compile:
        checker.heading("C. Mechanism compilation")
        checker.skip("nrnivmodl re-run", "--skip-compile given")
        lib = model_dir / "x86_64" / "libnrnmech.so"
        facts["mechanisms"] = {"compiled": lib.exists(), "skipped": True,
                               "library": str(lib) if lib.exists() else None,
                               "library_bytes": lib.stat().st_size
                               if lib.exists() else None}
    else:
        facts["mechanisms"] = compile_mechanisms(
            checker, model_dir, out_dir / "nrnivmodl.log")

    if not facts["mechanisms"].get("compiled"):
        checker.summary()
        (out_dir / "run_summary.json").write_text(
            json.dumps({"facts": facts, "tally": checker.tally()}, indent=2,
                       default=str), encoding="utf-8")
        print("\nRESULT: mechanisms did not compile, execution aborted")
        return 2

    run_facts = execute(checker, model_dir, allensdk_src, args.axon_type,
                        args.sweep, out_dir / "execution.log")
    captured = run_facts.pop("captured", {})
    state = run_facts.pop("state", {})
    facts["execution"] = run_facts
    facts["cell_state"] = state
    facts["convention"] = verify_convention(checker, captured)

    if run_facts.get("executed") and not args.skip_compare:
        facts["comparison"] = compare(checker, model_dir, args.axon_type,
                                      args.sweep, p2e)
    else:
        checker.heading("F. Recording versus prediction")
        checker.skip("trace comparison", "the run did not execute")

    # --- the trace itself, for the branch-sensitivity analysis
    if captured:
        import numpy as np
        np.savez_compressed(
            out_dir / ("traces_%s_sweep%d.npz" % (args.axon_type, args.sweep)),
            raw_v_mv=captured.get("raw_v_mv"),
            t_ms=captured.get("raw_t_ms"),
            written_v_mv=None if captured.get("out_v") is None
            else captured["out_v"] * 1e3)

    # --- input and output identity
    output_nwb = model_dir / OUTPUT_RELATIVE
    facts["hashes"] = {
        "inputs": facts["assets"].get("sha256", {}),
        "output_nwb_sha256": sha256_of(output_nwb) if output_nwb.exists() else None,
        "output_nwb_bytes": (output_nwb.stat().st_size
                             if output_nwb.exists() else None),
        "mechanism_library": facts["mechanisms"].get("library"),
        "mechanism_library_bytes": facts["mechanisms"].get("library_bytes"),
    }
    if facts["mechanisms"].get("library"):
        facts["hashes"]["mechanism_library_sha256"] = sha256_of(
            pathlib.Path(facts["mechanisms"]["library"]))

    facts["status"] = ("success" if run_facts.get("executed")
                       and checker.failures() == 0 else
                       "executed-with-failures" if run_facts.get("executed")
                       else "failed")

    failures = checker.summary()
    tally = checker.tally()
    summary = {
        "facts": facts,
        "tally": tally,
        "metrics": [{"label": label, "value": value}
                    for label, value in checker.metric_rows],
        "status": facts["status"],
    }
    (out_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")

    print()
    print("model: %s" % model_claim(args.axon_type))
    print("status: %s" % facts["status"])
    print("summary written to", out_dir / "run_summary.json")
    if not run_facts.get("executed"):
        print("RESULT: run %s did not execute" % args.run_id)
        return 2
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

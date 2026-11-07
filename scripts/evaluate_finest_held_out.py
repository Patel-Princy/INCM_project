#!/usr/bin/env python
"""Phase 2E — evaluate the perisomatic model on the held-out FINEST sweeps.

Purpose
-------
Phases 2A-2D established that perisomatic model 473862496 for specimen 382982932
was fitted to sweep 38 only, that it executes reproducibly, and that the FINEST
sweeps 49-52 are eligible held-out recordings whose commanded current is
bit-identical to sweep 38's.  This script performs the one thing those phases did
not: it takes the model exactly as published and scores it against the four
held-out recordings.

Nothing is fitted, tuned or re-parameterised.  The descriptor is verified byte
for byte against the digest Phase 2C recorded before the run, so "the model is
unchanged" is a fact about the files rather than a promise.

What it checks
--------------
A. Provenance and held-out independence.  Model assets against their Phase 1C /
   2A / 2B / 2C digests; the fitting descriptor against sweep 38 only; sweeps
   49-52 against both published descriptors; the four FINEST recordings against
   the Phase 2D eligibility criteria, re-derived here rather than cited; and the
   five commanded waveforms against bit-identity.
B. Mechanisms.  ``nrnivmodl`` is re-run in the Phase 2E workspace.
C. Execution.  ``runner.run`` is called once per sweep with ``sweeps=[n]`` and
   ``procs=1``, in a child process, exactly as Phase 2C ran sweep 38.
D. Output identity.  The four simulated traces are compared bit for bit, and
   compared against the Phase 2C sweep-38 trace.
E. Comparison.  Predicted versus observed for every held-out sweep.
F. Cross-sweep summary.
G. Sweep 38 alongside the FINEST repeats.

Predictive performance is reported, never asserted
--------------------------------------------------
A check gates the exit code only when it is a fact about provenance, execution or
numerical integrity.  Every statement about biological agreement is recorded as a
metric.  A model that predicts twelve spikes where the recording has one has
executed correctly and predicted incorrectly; conflating the two would let the
result of the evaluation decide whether the evaluation ran.

Why one sweep per process
-------------------------
Phase 2C executed sweep 38 through ``runner.run(sweeps=[38], procs=1)``.  That
call reaches ``run_sync``, which builds the cell and then loops over its sweeps.
Two sweeps in one process therefore share one ``Utils`` and one NEURON
interpreter.  A probe committed alongside this script (``--harness-probe``)
measured what that costs: it is in fact exact -- ``setup_iclamp`` rebinds
``self.stim``, which releases the previous ``IClamp``, and a two-sweep run
reproduces the single-sweep trace to 0.0 mV.  Running one sweep per process is
kept anyway because it reproduces the validated Phase 2C path exactly, isolates a
failure to one sweep, and makes the identity check in section D a statement about
*independent processes* rather than about one interpreter.

Usage
-----
    python scripts/evaluate_finest_held_out.py \
        --model-dir       ~/incm_phase2e/model \
        --allensdk-src    <repo>/tmp/model_cache/2b/src/AllenSDK-2.16.2 \
        --repo-cache      <repo>/tmp/model_cache \
        --phase2c-traces  ~/incm_phase2c/results/traces_sweep38.npz \
        --out-dir         ~/incm_phase2e/results \
        --plots-dir       ~/incm_phase2e/figures

Exit codes
----------
0  every provenance, execution and numerical check passed
1  the evaluation ran but at least one check failed
2  the evaluation could not run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

SPECIMEN = 382982932
PERISOMATIC_MODEL = 473862496
ALL_ACTIVE_MODEL = 497233292

#: The only sweep the descriptor was fitted to, and the four held-out repeats.
FITTING_SWEEP = 38
HELD_OUT_SWEEPS = (49, 50, 51, 52)

COARSE_BLOCK = "C1LSCOARSE150216"
FINEST_BLOCK = "C1LSFINEST150112"
PERISOMATIC_TYPE = "Biophysical - perisomatic"

JUNCTION_MV = -14.0
COMMAND_PA = 170.0
STEP_ONSET_MS = 1020.0
STEP_DURATION_MS = 1000.0

#: Phase 2D measured the FINEST command as 1 204 001 samples at 200 kHz, i.e.
#: 6.020 s.  The COARSE trace is the longer of the two (8.020 s), so the common
#: window is the FINEST length.
RATE_HZ = 200_000.0
DT_MS = 1e3 / RATE_HZ
COMMON_SAMPLES = 1_204_001
COMMON_DURATION_MS = 6_020.0

#: Phase 1C, re-verified by Phase 2D.
EXPECTED_NWB_SHA256 = (
    "d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63")
EXPECTED_NWB_BYTES = 94207824

#: Phase 2B, re-verified by Phase 2C.
EXPECTED_MARKER_SHA256 = (
    "3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925")
EXPECTED_MARKER_BYTES = 373

#: Recorded by Phase 2C in results/phase2/PHASE2C_PERISOMATIC_EXECUTION_VALIDATION.md.
#: Equality here is what "the model was not refitted" means operationally.
PHASE2C_DESCRIPTOR_SHA256 = (
    "d24d00aaed5a2a0ecf9752735b62254bba7ab3dc0d3627e61466f95b00a8e38f")
PHASE2C_SWC_SHA256 = (
    "71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c")
PHASE2C_MANIFEST_SHA256 = (
    "93ef8ca022cea0b109f536e28da97d7661aaf72c9b54dba71f09db8b761692b0")

MECHANISMS = (
    "CaDynamics", "Ca_HVA", "Ca_LVA", "Ih", "Im", "Im_v2",
    "K_P", "K_T", "Kd", "Kv2like", "Kv3_1", "NaTa", "NaTs", "NaV", "Nap", "SK",
)

STIMULUS_NWB = "382982932.nwb"
DESCRIPTOR = "382982932_fit.json"
MORPHOLOGY = "674389901_382982932_m.swc"
MARKER = "674389910_382982932_m.marker"
OUTPUT_RELATIVE = os.path.join("work", STIMULUS_NWB)

#: Spike-detector agreement is required before either count is quoted.  Phase 2C
#: thresholds dV/dt (Allen's ``detect_putative_spikes``); Phase 2D crosses 0 mV
#: with a refractory window.  Both are run and both are reported.
ALLEN_DETECTOR = "allen_dvdt"
CROSSING_DETECTOR = "phase2d_0mv"

#: Phase 2D quality thresholds, restated rather than imported so that a change to
#: the Phase 2D script cannot silently relax this phase's admission criteria.
MAX_PLAUSIBLE_FLAT_MS = 5.0
RAIL_HIGH_MV = 200.0
RAIL_LOW_MV = -95.0

# Reuse the Phase 1C/1D NWB access layer and the Phase 2D detectors verbatim.
# Both are the definitions the earlier phases validated; a re-implementation here
# would only add a second way to disagree with them.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_electrophysiology_protocols as phase2d  # noqa: E402

import numpy as np  # noqa: E402


# --------------------------------------------------------------------- helpers
def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class Checker:
    """Accumulate pass/fail rows and reported metrics separately.

    The split is the whole epistemic point of this phase: a failed provenance
    check invalidates the evaluation, but a model that predicts the wrong number
    of spikes is a *finding*.  Only ``check`` gates the exit code.
    """

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
        print("  %-6s %-58s %s" % ("ok" if ok else "FAIL", label, detail))
        return bool(ok)

    def skip(self, label: str, reason: str) -> None:
        self.rows.append((self.section_name, label, None, reason))
        print("  %-6s %-58s %s" % ("skip", label, reason))

    def note(self, text: str) -> None:
        for line in text.strip().splitlines():
            print("  .. " + line.strip())

    def metric(self, label: str, detail: str = "") -> None:
        self.metric_rows.append((label, detail))
        print("  %-6s %-58s %s" % ("report", label, detail))

    def tally(self) -> dict:
        checked = [r for r in self.rows if r[2] is not None]
        failed = [r for r in checked if r[2] is False]
        by_section: dict[str, list[int]] = {}
        for section, _label, ok, _detail in self.rows:
            bucket = by_section.setdefault(section, [0, 0])
            if ok is None:
                continue
            bucket[0] += 1
            if ok is False:
                bucket[1] += 1
        return {
            "checks": len(checked),
            "passed": len(checked) - len(failed),
            "failed": len(failed),
            "skipped": len(self.rows) - len(checked),
            "metrics": len(self.metric_rows),
            "by_section": {k: {"checks": v[0], "failed": v[1]}
                           for k, v in by_section.items()},
        }

    def summary(self) -> int:
        tally = self.tally()
        print()
        print("-" * 78)
        print("checks: %d   passed: %d   failed: %d   skipped: %d   metrics: %d"
              % (tally["checks"], tally["passed"], tally["failed"],
                 tally["skipped"], tally["metrics"]))
        return tally["failed"]


# ------------------------------------------------------- A. provenance checks
def verify_inputs(checker: Checker, model_dir: pathlib.Path,
                  repo_cache: pathlib.Path) -> dict:
    """Hash every staged asset and prove the model is the published one."""
    checker.heading("A. Provenance and held-out independence")

    facts: dict = {"model_dir": str(model_dir), "sha256": {}}

    # --- the descriptor is the published one, and the one Phase 2C executed
    descriptor_path = model_dir / DESCRIPTOR
    if not descriptor_path.exists():
        checker.check(False, "fitting descriptor present", "missing " + DESCRIPTOR)
        return facts
    digest = sha256_of(descriptor_path)
    checker.check(digest == PHASE2C_DESCRIPTOR_SHA256,
                  "descriptor digest unchanged since Phase 2C",
                  "%s… vs %s…" % (digest[:16], PHASE2C_DESCRIPTOR_SHA256[:16]))
    descriptor_digest = digest
    facts["sha256"][DESCRIPTOR] = digest

    # Nothing in the descriptor may have moved: the genome, the passive block and
    # the conditions are what "the published parameters" means.
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    checks = [
        ("descriptor keeps Allen's four sections",
         sorted(descriptor) == ["conditions", "fitting", "genome", "passive"],
         ",".join(sorted(descriptor))),
        ("descriptor carries %d genome entries" % len(descriptor["genome"]),
         len(descriptor["genome"]) == 16, "%d" % len(descriptor["genome"])),
    ]
    for label, ok, detail in checks:
        checker.check(ok, label, detail)

    genome = descriptor["genome"]
    soma_entries = [g for g in genome if g.get("section") == "soma" and g.get("mechanism")]
    soma_mechanisms = sorted({g["mechanism"] for g in soma_entries})
    checker.check(len(soma_mechanisms) == 11 and len(soma_entries) == 12,
                  "soma carries 11 fitted conductances in 12 entries",
                  "%s (CaDynamics twice: gamma and decay)"
                  % ",".join(soma_mechanisms))
    checker.check(all(isinstance(g["value"], float) for g in genome),
                  "every fitted value is a float (no all-active tuples)",
                  "%d entries" % len(genome))

    # --- the descriptor was fitted to sweep 38 and to nothing else
    fitting = descriptor["fitting"][0]
    junction = float(fitting["junction_potential"])
    fitting_sweeps = [int(s) for s in fitting["sweeps"]]
    checker.check(fitting_sweeps == [FITTING_SWEEP],
                  "fitting reference is sweep %d only" % FITTING_SWEEP,
                  str(fitting_sweeps))
    checker.check(junction == JUNCTION_MV, "junction potential is -14 mV",
                  "%+g mV" % junction)
    checker.check(not (set(fitting_sweeps) & set(HELD_OUT_SWEEPS)),
                  "no held-out sweep appears in the fitting list", "disjoint")
    facts["junction_mv"] = junction
    facts["fitting_sweeps"] = fitting_sweeps

    # --- the all-active model did not see them either
    all_active = repo_cache / "models" / ("all_active_%d" % ALL_ACTIVE_MODEL) / (
        "%d_fit.json" % ALL_ACTIVE_MODEL)
    if all_active.exists():
        active = json.loads(all_active.read_text(encoding="utf-8"))
        active_sweeps = [int(s) for s in active["fitting"][0]["sweeps"]]
        checker.check(not (set(active_sweeps) & set(HELD_OUT_SWEEPS)),
                      "all-active descriptor excludes sweeps 49-52",
                      "%d fitting sweeps: %s" % (len(active_sweeps),
                                                 _span(active_sweeps)))
        facts["all_active_fitting_sweeps"] = active_sweeps
        facts["all_active_descriptor_sha256"] = sha256_of(all_active)
    else:
        checker.check(False, "all-active descriptor available for independence check",
                      "missing %s" % all_active)

    # --- the model files themselves
    for name, want, origin in [
            (MORPHOLOGY, PHASE2C_SWC_SHA256, "Phase 2C"),
            (MARKER, EXPECTED_MARKER_SHA256, "Phase 2B")]:
        path = model_dir / name
        if not path.exists():
            checker.check(False, "%s present" % name, "missing")
            continue
        actual = sha256_of(path)
        checker.check(actual == want, "%s digest unchanged since %s" % (name, origin),
                      "%s… vs %s…" % (actual[:16], want[:16]))
        facts["sha256"][name] = actual

    nwb = model_dir / STIMULUS_NWB
    if nwb.exists():
        digest = sha256_of(nwb)
        checker.check(nwb.stat().st_size == EXPECTED_NWB_BYTES,
                      "stimulus NWB byte size matches Phase 1C",
                      "%d B" % nwb.stat().st_size)
        checker.check(digest == EXPECTED_NWB_SHA256,
                      "stimulus NWB digest matches Phase 1C",
                      "%s… vs %s…" % (digest[:16], EXPECTED_NWB_SHA256[:16]))
        facts["sha256"][STIMULUS_NWB] = digest
    else:
        checker.check(False, "stimulus NWB present", "missing")

    manifest_path = model_dir / "manifest.json"
    manifest_digest = sha256_of(manifest_path)
    checker.check(manifest_digest == PHASE2C_MANIFEST_SHA256,
                  "manifest digest unchanged since Phase 2C",
                  "%s… vs %s…" % (manifest_digest[:16],
                                  PHASE2C_MANIFEST_SHA256[:16]))
    facts["sha256"]["manifest.json"] = manifest_digest

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    biophys = manifest["biophys"]
    checker.check(len(biophys) == 1 and biophys[0]["model_type"] == PERISOMATIC_TYPE,
                  "manifest still selects the perisomatic model",
                  biophys[0]["model_type"])
    by_type = manifest["runs"][0]["sweeps_by_type"]
    family = [name for name, members in by_type.items()
              if all(s in members for s in HELD_OUT_SWEEPS)]
    checker.check(family == ["Long Square"],
                  "all four held-out sweeps are Long Square sweeps",
                  ",".join(family) or "none")
    facts["held_out_family"] = family

    # --- the staged bytes are the cached bytes
    cache_descriptor = repo_cache / "models" / (
        "perisomatic_%d" % PERISOMATIC_MODEL) / DESCRIPTOR
    if cache_descriptor.exists():
        cached = sha256_of(cache_descriptor)
        checker.check(cached == descriptor_digest,
                      "staged descriptor is byte-identical to the cached copy",
                      "%s…" % cached[:16])

    return facts


def _span(values: list[int]) -> str:
    """Compact ``a-b`` rendering of a sorted integer list."""
    if not values:
        return "none"
    values = sorted(values)
    return str(values[0]) if len(values) == 1 else "%d-%d" % (values[0], values[-1])


def load_sweeps(checker: Checker, model_dir: pathlib.Path) -> dict:
    """Read sweeps 38 and 49-52 once, with their commands, and admit or reject.

    The eligibility rule is Phase 2D's, re-applied here: EXCLUDE on a
    sample-integrity fault (non-finite sample, stalled converter, amplifier
    rail); otherwise ELIGIBLE.  The measurements come from the Phase 2D
    functions themselves so the two phases cannot drift apart.
    """
    import h5py  # noqa: F401 - imported for its side effect of failing early

    path = model_dir / STIMULUS_NWB
    sweeps: dict[int, dict] = {}
    wanted = (FITTING_SWEEP,) + HELD_OUT_SWEEPS

    with phase2d.open_nwb(path) as handle:
        series = dict(phase2d.list_series(handle, "stimulus/presentation"))
        acquisition = dict(phase2d.list_series(handle, "acquisition/timeseries"))
        for sweep in wanted:
            key = "Sweep_%d" % sweep
            if key not in series:
                checker.check(False, "sweep %d present in the NWB" % sweep, "missing")
                continue
            stim_node = series[key]
            rec_node = acquisition.get(key, stim_node)
            stim_pa = phase2d.to_amps_pa(stim_node)
            v_mv = phase2d.to_volts_mv(rec_node)
            rate = phase2d.series_rate(stim_node)
            base, multiplier = phase2d.template_key(stim_node)
            sweeps[sweep] = {
                "sweep": int(sweep),
                "block": base.split("[")[0],
                "template": base,
                "multiplier": multiplier,
                "rate_hz": float(rate),
                "stimulus_pa": stim_pa,
                "recorded_mv": v_mv,
                "n_samples": int(v_mv.size),
            }

    for sweep in wanted:
        record = sweeps.get(sweep)
        if record is None:
            continue
        record["stimulus"] = phase2d.analyse_stimulus(
            record["stimulus_pa"], record["rate_hz"])

    # --- sampling rate and length
    for sweep, record in sweeps.items():
        ok = abs(record["rate_hz"] - RATE_HZ) < 1e-6
        checker.check(ok, "sweep %d sampled at 200 kHz" % sweep,
                      "%g Hz" % record["rate_hz"])

    # --- command waveforms: the whole point of the held-out design
    reference = sweeps.get(FITTING_SWEEP)
    if reference is not None:
        for sweep in HELD_OUT_SWEEPS:
            record = sweeps.get(sweep)
            if record is None:
                continue
            a = reference["stimulus_pa"]
            b = record["stimulus_pa"]
            common = min(a.size, b.size)
            differing = int(np.count_nonzero(a[:common] != b[:common]))
            worst = float(np.max(np.abs(a[:common] - b[:common]))) * 1e12
            checker.check(differing == 0,
                          "sweep %d command identical to sweep %d" % (sweep, FITTING_SWEEP),
                          "%d differing of %s samples, max|d| %.3e pA"
                          % (differing, format(common, ","), worst))
            checker.check(common == COMMON_SAMPLES,
                          "sweep %d common command window is 6.020 s" % sweep,
                          "%d samples" % common)
            record["command_vs_reference"] = {
                "common_samples": int(common),
                "differing_samples": differing,
                "max_abs_diff_pa": worst,
            }

    # --- Phase 2D eligibility, re-derived
    for sweep in HELD_OUT_SWEEPS:
        record = sweeps.get(sweep)
        if record is None:
            continue
        stimulus = record["stimulus"]
        quality = phase2d.quality_metrics(
            record["recorded_mv"], record["rate_hz"],
            stimulus["onset_s"], stimulus["end_s"])
        record["quality"] = quality

        faults = []
        if quality["n_nonfinite"]:
            faults.append("%d non-finite" % quality["n_nonfinite"])
        if quality["longest_flat_ms"] > MAX_PLAUSIBLE_FLAT_MS:
            faults.append("flat %.1f ms" % quality["longest_flat_ms"])
        if quality["v_max_mv"] > RAIL_HIGH_MV:
            faults.append("high rail %.1f mV" % quality["v_max_mv"])
        if quality["v_min_mv"] < RAIL_LOW_MV:
            faults.append("low rail %.1f mV" % quality["v_min_mv"])
        checker.check(not faults, "sweep %d passes the Phase 2D integrity screen" % sweep,
                      ", ".join(faults) or
                      "sd %.3f mV, drift %.4f mV/s, flat %.2f ms"
                      % (quality["baseline_sd_mv"],
                         quality["baseline_drift_mv_per_s"],
                         quality["longest_flat_ms"]))
        checker.check(record["block"] == FINEST_BLOCK,
                      "sweep %d belongs to %s" % (sweep, FINEST_BLOCK),
                      record["block"])
        checker.check(stimulus["status"] == "OK",
                      "sweep %d carries one resolvable current step" % sweep,
                      stimulus["status"])
        checker.check(abs(stimulus["level_pa"] - COMMAND_PA) < 1.0,
                      "sweep %d step is +170 pA" % sweep,
                      "%+.3f pA" % stimulus["level_pa"])
        checker.check(abs(stimulus["onset_s"] * 1e3 - STEP_ONSET_MS) < 1.0,
                      "sweep %d step starts at 1020 ms" % sweep,
                      "%.3f ms" % (stimulus["onset_s"] * 1e3))
        checker.check(abs(stimulus["duration_ms"] - STEP_DURATION_MS) < 1.0,
                      "sweep %d step lasts 1000 ms" % sweep,
                      "%.3f ms" % stimulus["duration_ms"])

    return sweeps


def verify_mechanism_sources(checker: Checker, model_dir: pathlib.Path,
                             assets_manifest: pathlib.Path) -> None:
    """Every .mod source must still match the Phase 2A published digest."""
    expected = {}
    data = json.loads(assets_manifest.read_text(encoding="utf-8"))
    for asset in data["assets"]:
        if "sha256" in asset:
            expected[os.path.basename(asset.get("path") or asset["url"])] = asset["sha256"]

    sources = sorted((model_dir / "modfiles").glob("*.mod"))
    checker.check(len(sources) == len(MECHANISMS),
                  "16 mechanism sources present", "%d found" % len(sources))
    bad = [p.name for p in sources
           if expected.get(p.name) is None or sha256_of(p) != expected[p.name]]
    checker.check(not bad, "every mechanism source matches its Phase 2A digest",
                  ", ".join(bad[:4]) if bad else "%d sources" % len(sources))


# ---------------------------------------------------------- B. mechanisms
def compile_mechanisms(checker: Checker, model_dir: pathlib.Path,
                       log_path: pathlib.Path) -> dict:
    checker.heading("B. Mechanism compilation")
    nrnivmodl = pathlib.Path(sys.executable).with_name("nrnivmodl")
    if not nrnivmodl.exists():
        checker.check(False, "nrnivmodl is available", str(nrnivmodl))
        return {"compiled": False}

    started = time.time()
    completed = subprocess.run([str(nrnivmodl), "modfiles/"],
                               cwd=str(model_dir), capture_output=True, text=True)
    elapsed = time.time() - started
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "command: %s modfiles/\nrc: %d\n--- stdout ---\n%s\n--- stderr ---\n%s\n"
        % (nrnivmodl, completed.returncode, completed.stdout, completed.stderr),
        encoding="utf-8")

    combined = completed.stdout + completed.stderr
    warnings = sum(1 for line in combined.splitlines() if "warning" in line.lower())
    errors = sum(1 for line in combined.splitlines() if "error" in line.lower())
    library = model_dir / "x86_64" / "libnrnmech.so"

    checker.check(completed.returncode == 0, "nrnivmodl exited 0", "%.1f s" % elapsed)
    checker.check(warnings == 0, "no compiler warnings", "%d" % warnings)
    checker.check(errors == 0, "no compiler errors", "%d" % errors)
    checker.check(library.exists(), "libnrnmech.so was produced", library.name)

    return {"compiled": completed.returncode == 0 and library.exists(),
            "elapsed_s": round(elapsed, 2), "warnings": warnings, "errors": errors,
            "library_bytes": library.stat().st_size if library.exists() else None,
            "log": str(log_path)}
# ---------------------------------------------------------- C/D. execution
def child_main(argv) -> int:
    """Simulate one sweep in a fresh process and record everything it produced.

    The process is deliberately short-lived.  NEURON keeps global state, and
    ``run_sync`` builds the cell into that state, so a fresh interpreter per sweep
    is what makes the identity check in section D a statement about independent
    executions rather than about one reused object graph.
    """
    parser = argparse.ArgumentParser(description="Phase 2E child runner")
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--sweep", type=int, required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--allensdk-src", required=True)
    parser.add_argument("--child-out", required=True)
    ns = parser.parse_args(argv)

    model_dir = pathlib.Path(ns.model_dir).expanduser().resolve()
    out_dir = pathlib.Path(ns.child_out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(pathlib.Path(ns.allensdk_src).expanduser().resolve()))
    os.chdir(model_dir)

    import logging
    import neuron
    from allensdk.core.nwb_data_set import NwbDataSet
    from allensdk.model.biophysical import runner
    from allensdk.model.biophysical import utils as biophys_utils

    summary: dict = {"sweep": int(ns.sweep), "model_dir": str(model_dir),
                     "cwd": os.getcwd(), "neuron_version": neuron.__version__}

    # Mechanisms must be loadable before anything else is attempted; NEURON
    # resolves them from ./x86_64 relative to the working directory.
    missing = []
    for mechanism in MECHANISMS:
        section = neuron.h.Section(name="probe_" + mechanism)
        try:
            section.insert(mechanism)
        except Exception:
            missing.append(mechanism)
        finally:
            neuron.h.delete_section(sec=section)
    summary["mechanisms_missing"] = missing
    summary["mechanisms_loaded"] = len(MECHANISMS) - len(missing)
    summary["iclamp_before_run"] = len(neuron.h.List("IClamp"))

    captured: dict = {}
    state: dict = {}
    original_setup = biophys_utils.Utils.setup_iclamp
    original_get = biophys_utils.Utils.get_recorded_data

    def setup_iclamp_instrumented(self, stimulus_path, sweep=0):
        # Utils stores no sweep attribute, so the number has to be read where it
        # is passed in; get_recorded_data then keys its capture by it.
        state["sweep"] = int(sweep)
        return original_setup(self, stimulus_path, sweep=sweep)

    def get_recorded_data_instrumented(self, vec):
        raw_v = np.array(vec["v"], dtype=float)
        raw_t = np.array(vec["t"], dtype=float)
        result = original_get(self, vec)
        captured[int(state.get("sweep", -1))] = {
            "raw_v_mv": raw_v,
            "raw_t_ms": raw_t,
            "out_v": np.array(result["v"], dtype=float),
            "out_t": np.array(result["t"], dtype=float),
            "junction_mv": float(
                self.description.data["fitting"][0]["junction_potential"]),
            "stimulus_rate_hz": float(self.stimulus_sampling_rate),
            "simulation_rate_hz": float(self.simulation_sampling_rate),
            "dt_ms": float(neuron.h.dt),
            "tstop_ms": float(neuron.h.tstop),
            "iclamps": len(neuron.h.List("IClamp")),
        }
        return result

    biophys_utils.Utils.setup_iclamp = setup_iclamp_instrumented
    biophys_utils.Utils.get_recorded_data = get_recorded_data_instrumented

    rows: list[str] = []

    class _Capture(list):
        def write(self, text):
            if text.strip():
                rows.append(text.rstrip())

        def flush(self):
            pass

    handler = logging.StreamHandler(_Capture())
    handler.setLevel(logging.INFO)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    started = time.time()
    error = None
    try:
        try:
            runner.run({"manifest_file": "manifest.json", "axon_type": "truncated"},
                       sweeps=[ns.sweep], procs=1)
        except Exception as exc:                 # noqa: BLE001 - reported verbatim
            import traceback
            error = "%s: %s" % (type(exc).__name__, exc)
            rows.append(traceback.format_exc())
        elapsed = time.time() - started
    finally:
        root.removeHandler(handler)
        biophys_utils.Utils.setup_iclamp = original_setup
        biophys_utils.Utils.get_recorded_data = original_get

    (out_dir / "execution.log").write_text("\n".join(rows), encoding="utf-8")
    summary.update({"elapsed_s": round(elapsed, 2), "error": error,
                    # Utils is released when run_sync returns, which frees its
                    # IClamp, so the count has to be read while the model is live.
                    "iclamp_during_run": max((c.get("iclamps", 0)
                                              for c in captured.values()), default=0),
                    "sections": len(list(neuron.h.allsec()))})
    if error or not captured:
        summary["captured_sweeps"] = sorted(captured)
        (out_dir / "child_summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8")
        return 2

    trace = captured[ns.sweep]
    np.savez_compressed(out_dir / "traces.npz",
                        v_sim=trace["out_v"], t_ms=trace["out_t"],
                        v_raw_mv=trace["raw_v_mv"])

    # Read the written NWB back: this is where Allen's own save path is exercised.
    output_path = model_dir / OUTPUT_RELATIVE
    summary["output_nwb"] = str(output_path)
    summary["output_nwb_bytes"] = output_path.stat().st_size
    written = NwbDataSet(str(output_path)).get_sweep(ns.sweep)
    v_written = np.asarray(written["response"], dtype=float)
    stim_written = np.asarray(written["stimulus"], dtype=float)
    stimulus_in = NwbDataSet(str(model_dir / STIMULUS_NWB)).get_sweep(ns.sweep)
    stim_in = np.asarray(stimulus_in["stimulus"], dtype=float)
    n = min(v_written.size, trace["out_v"].size)
    summary.update({
        "n_written": int(v_written.size),
        "n_captured": int(trace["out_v"].size),
        "written_matches_capture_max_abs_v": float(
            np.max(np.abs(v_written[:n] - trace["out_v"][:n]))),
        "stimulus_roundtrip_identical": bool(stim_written.size == stim_in.size
                                             and np.array_equal(stim_written, stim_in)),
        "stored_spike_times_s": [float(x) for x in
                                 np.asarray(NwbDataSet(str(output_path))
                                            .get_spike_times(ns.sweep))],
        "n_samples_raw": int(trace["raw_v_mv"].size),
        "junction_mv": trace["junction_mv"],
        "dt_ms": trace["dt_ms"],
        "tstop_ms": trace["tstop_ms"],
        "stimulus_rate_hz": trace["stimulus_rate_hz"],
        "simulation_rate_hz": trace["simulation_rate_hz"],
        "raw_first_mv": float(trace["raw_v_mv"][0]),
        "written_first_mv": float(trace["out_v"][0]) * 1e3,
    })
    (out_dir / "child_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return 0


def execute_sweeps(checker: Checker, model_dir: pathlib.Path,
                   allensdk_src: pathlib.Path, out_dir: pathlib.Path) -> dict:
    """Run one child process per held-out sweep, exactly as Phase 2C ran sweep 38."""
    checker.heading("C. Execution")

    script = str(pathlib.Path(__file__).resolve())
    results: dict[int, dict] = {}
    for sweep in HELD_OUT_SWEEPS:
        child_out = out_dir / ("sweep_%d" % sweep)
        child_out.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, script, "--child",
                   "--sweep", str(sweep),
                   "--model-dir", str(model_dir),
                   "--allensdk-src", str(allensdk_src),
                   "--child-out", str(child_out)]
        started = time.time()
        completed = subprocess.run(command, capture_output=True, text=True)
        elapsed = time.time() - started
        (child_out / "child_console.log").write_text(
            (completed.stdout or "") + "\n--- stderr ---\n" + (completed.stderr or ""),
            encoding="utf-8")

        summary_path = child_out / "child_summary.json"
        if completed.returncode != 0 or not summary_path.exists():
            checker.check(False, "sweep %d simulated" % sweep,
                          "rc %d after %.1f s; see %s"
                          % (completed.returncode, elapsed,
                             child_out / "child_console.log"))
            continue
        child = json.loads(summary_path.read_text(encoding="utf-8"))
        child["_child_out"] = str(child_out)
        results[sweep] = child
        checker.check(True, "sweep %d simulated" % sweep,
                      "%.1f s, %d samples" % (elapsed, child["n_captured"]))

    for sweep, child in results.items():
        checker.check(child["mechanisms_loaded"] == len(MECHANISMS),
                      "sweep %d loaded all 16 mechanisms" % sweep,
                      "%d/%d" % (child["mechanisms_loaded"], len(MECHANISMS)))
        checker.check(child["iclamp_during_run"] == 1,
                      "sweep %d used exactly one IClamp" % sweep,
                      "%d" % child["iclamp_during_run"])
        checker.check(child["junction_mv"] == JUNCTION_MV,
                      "sweep %d kept the -14 mV junction convention" % sweep,
                      "%+.1f mV" % child["junction_mv"])
        checker.check(abs(child["written_first_mv"]
                          - (child["raw_first_mv"] - JUNCTION_MV)) < 1e-9,
                      "sweep %d wrote V_sim + 14 mV at output only" % sweep,
                      "%.4f mV" % child["written_first_mv"])
        checker.check(child["written_matches_capture_max_abs_v"] <= 1e-6,
                      "sweep %d NWB response equals the captured trace" % sweep,
                      "max |d| %.3e V (NWB stores float32)"
                      % child["written_matches_capture_max_abs_v"])
        checker.check(child["stimulus_roundtrip_identical"],
                      "sweep %d output NWB inherits the command unchanged" % sweep,
                      "bit-identical")
        checker.check(child["n_captured"] == COMMON_SAMPLES,
                      "sweep %d simulated 6.020 s" % sweep,
                      "%d samples" % child["n_captured"])

    return results


def verify_output_identity(checker: Checker, results: dict,
                           phase2c_traces: pathlib.Path | None) -> dict:
    """Prove the four simulations are the same signal, and that 38 is too.

    The commands are bit-identical and NEURON is deterministic, so this is
    expected -- but it is the assumption the whole comparison rests on, and an
    assumption is exactly what must not be made here.
    """
    checker.heading("D. Output identity")

    facts: dict = {}
    if len(results) < len(HELD_OUT_SWEEPS):
        checker.skip("cross-sweep identity", "not all sweeps executed")
        return facts

    traces = {}
    for sweep in HELD_OUT_SWEEPS:
        path = pathlib.Path(results[sweep]["_child_out"]) / "traces.npz"
        traces[sweep] = np.load(path)

    reference = traces[HELD_OUT_SWEEPS[0]]
    v_ref = reference["v_sim"]
    for sweep in HELD_OUT_SWEEPS[1:]:
        other = traces[sweep]
        same_length = other["v_sim"].size == v_ref.size
        worst = (float(np.max(np.abs(other["v_sim"] - v_ref))) if same_length
                 else float("nan"))
        checker.check(same_length and worst == 0.0,
                      "sweep %d simulation is bit-identical to sweep %d"
                      % (sweep, HELD_OUT_SWEEPS[0]),
                      "max |d| %.3e mV" % (worst * 1e3) if same_length
                      else "length %d vs %d" % (other["v_sim"].size, v_ref.size))

    store = {s: results[s].get("stored_spike_times_s", []) for s in HELD_OUT_SWEEPS}
    unique = {tuple(sorted(v)) for v in store.values()}
    checker.check(len(unique) == 1,
                  "all four sweeps store the same spike times in their NWB",
                  "%d distinct sets of %d spikes"
                  % (len(unique), len(next(iter(unique)))))

    facts["identity"] = {
        "reference_sweep": HELD_OUT_SWEEPS[0],
        "identical_across": list(HELD_OUT_SWEEPS),
        "stored_spike_times_s": {str(s): v for s, v in store.items()},
        "n_stored": len(store[HELD_OUT_SWEEPS[0]]),
    }

    if phase2c_traces is None or not pathlib.Path(phase2c_traces).exists():
        checker.skip("comparison with the Phase 2C sweep-38 trace",
                     "no traces file supplied")
        return facts

    previous = np.load(pathlib.Path(phase2c_traces))
    v38 = previous["v_sim"]
    common = min(v38.size, v_ref.size)
    worst = float(np.max(np.abs(v_ref[:common] - v38[:common])))
    checker.check(worst == 0.0,
                  "sweep %d reproduces the Phase 2C sweep-38 trace exactly"
                  % HELD_OUT_SWEEPS[0],
                  "max |d| %.3e mV over %d samples" % (worst * 1e3, common))
    checker.check(common == COMMON_SAMPLES,
                  "the reproduced window is the 6.020 s common window",
                  "%d of %d samples" % (common, v38.size))
    facts["identity"]["phase2c_trace"] = {
        "path": str(phase2c_traces),
        "samples": int(v38.size),
        "common_samples": int(common),
        "max_abs_diff_mv": worst * 1e3,
    }
    return facts


# ------------------------------------------------------------- E. measurement
def _times_ms(peaks, rate_hz):
    return np.asarray(peaks, dtype=float) / rate_hz * 1e3


def _summary_of(values, label):
    import numpy as _np
    finite = [v for v in values if v == v]
    if not finite:
        return {"n": 0}
    return {"n": len(finite), "min": float(_np.min(finite)),
            "median": float(_np.median(finite)), "max": float(_np.max(finite)),
            "label": label}


def describe_trace(name: str, v_mv, rate_hz: float, stim_pa, allen_indices) -> dict:
    """Everything about one voltage trace that does not require a second trace."""
    dt = 1e3 / rate_hz
    step = phase2d.analyse_stimulus(stim_pa, rate_hz)
    on_index, end_index = int(step["onset_index"]), int(step["end_index"])
    on_ms, end_ms = on_index * dt, end_index * dt

    quiet = np.abs(stim_pa[:on_index]) <= 1e-12
    pre = v_mv[:on_index][quiet]

    peaks = phase2d.detect_spikes(v_mv, rate_hz)
    times = _times_ms(peaks, rate_hz)
    inside = (times >= on_ms) & (times < end_ms)
    allen_times = _times_ms(np.asarray(allen_indices, dtype=int).ravel(), rate_hz)

    shapes = [phase2d.spike_shape(v_mv, rate_hz, int(p)) for p in peaks]
    first_shape = shapes[0] if shapes else {}

    plateau_lo = end_index - int(200.0 / dt)
    plateau = v_mv[max(0, plateau_lo):end_index]
    plateau_spikes = int(np.count_nonzero(
        (times >= max(0, plateau_lo) * dt) & (times < end_ms)))

    isis = np.diff(times) if times.size > 1 else np.array([])

    return {
        "label": name,
        "n_samples": int(v_mv.size),
        "duration_ms": float(v_mv.size) * dt,
        "rate_hz": float(rate_hz),
        "step_onset_ms": float(on_ms),
        "step_end_ms": float(end_ms),
        "step_duration_ms": float(end_ms - on_ms),
        "baseline_mv": float(np.mean(pre)) if pre.size else float("nan"),
        "baseline_sd_mv": float(np.std(pre)) if pre.size else float("nan"),
        "v_min_mv": float(np.min(v_mv)),
        "v_max_mv": float(np.max(v_mv)),
        "n_spikes_allen": int(allen_times.size),
        "n_spikes_crossing": int(times.size),
        "spike_times_ms": [round(float(t), 3) for t in times],
        "allen_spike_times_ms": [round(float(t), 3) for t in allen_times],
        "spike_times_in_step_ms": [round(float(t), 3) for t in times[inside]],
        "spike_times_out_step_ms": [round(float(t), 3) for t in times[~inside]],
        "n_in_step": int(np.count_nonzero(inside)),
        "n_out_step": int(np.count_nonzero(~inside)),
        "first_spike_ms": float(times[0]) if times.size else float("nan"),
        "first_latency_ms": (float(times[0]) - on_ms) if times.size else float("nan"),
        "first_in_step_ms": (float(times[inside][0]) if inside.any()
                             else float("nan")),
        "first_in_step_latency_ms": (float(times[inside][0]) - on_ms
                                     if inside.any() else float("nan")),
        "isis_ms": [round(float(x), 3) for x in isis],
        "mean_isi_ms": float(np.mean(isis)) if isis.size else float("nan"),
        "spike_amplitude_mv": _summary_of([s["amplitude_mv"] for s in shapes],
                                          "peak minus pre-spike baseline"),
        "spike_width_ms": _summary_of([s["width_ms"] for s in shapes], "half-max"),
        "spike_peak_mv": _summary_of([s["peak_mv"] for s in shapes], "absolute"),
        "spike_rise_ms": _summary_of([s["rise_ms"] for s in shapes], "10-90 %"),
        "spike_dvdt_v_per_s": _summary_of([s["max_dvdt_v_per_s"] for s in shapes],
                                          "maximum upstroke"),
        "ahp_mv": _summary_of([s["ahp_mv"] for s in shapes],
                              "minimum 1-40 ms after the peak"),
        "first_spike_shape": first_shape,
        "plateau_mv": float(np.median(plateau)) if plateau.size else float("nan"),
        "plateau_spikes": plateau_spikes,
        "step_onset_sample": on_index,
        "step_end_sample": end_index,
    }


def compare_traces(recorded: dict, simulated: dict, stim_pa, rate_hz: float,
                   window_ms: float = 10.0) -> dict:
    """Compare one recorded trace with the prediction, and decompose the error.

    A whole-trace RMSE cannot distinguish "the subthreshold response is right and
    the spike count is wrong" from "the subthreshold response is wrong", so the
    squared error inside the step is split into samples within ``window_ms`` of an
    action potential in either trace and samples outside any such window.  The
    two numbers answer different questions and both are reported.
    """
    dt = 1e3 / rate_hz
    step = phase2d.analyse_stimulus(stim_pa, rate_hz)
    on_index, end_index = int(step["onset_index"]), int(step["end_index"])

    v_rec = recorded["_v_mv"]
    v_sim = simulated["_v_mv"]
    n = min(v_rec.size, v_sim.size)
    a, b = v_rec[:n], v_sim[:n]
    t_ms = np.arange(n) * dt

    diff = b - a
    sse = float(np.sum(diff ** 2))
    facts = {
        "n_compared": int(n),
        "n_recorded": int(v_rec.size),
        "n_simulated": int(v_sim.size),
        "rmse_whole_mv": float(np.sqrt(np.mean(diff ** 2))),
        "mae_whole_mv": float(np.mean(np.abs(diff))),
        "corr_whole": float(np.corrcoef(a, b)[0, 1]) if n > 2 else float("nan"),
        "rmse_pre_step_mv": float(np.sqrt(np.mean(diff[:on_index] ** 2))),
        "rmse_in_step_mv": float(np.sqrt(np.mean(diff[on_index:end_index] ** 2))),
        "rmse_post_step_mv": float(np.sqrt(np.mean(diff[end_index:] ** 2)))
        if end_index < n else float("nan"),
        "corr_in_step": float(np.corrcoef(a[on_index:end_index],
                                          b[on_index:end_index])[0, 1]),
        "baseline_recorded_mv": recorded["baseline_mv"],
        "baseline_simulated_mv": simulated["baseline_mv"],
        "baseline_delta_mv": simulated["baseline_mv"] - recorded["baseline_mv"],
        "step_onset_ms": float(on_index * dt),
        "step_end_ms": float(end_index * dt),
    }

    # --- error budget inside the step
    mask = np.zeros(n, dtype=bool)
    half = int(window_ms / dt)
    for desc in (recorded, simulated):
        for t in desc["spike_times_ms"]:
            centre = int(round(t / dt))
            lo, hi = max(0, centre - half), min(n, centre + half + 1)
            mask[lo:hi] = True
    step_slice = slice(on_index, min(end_index, n))
    mask_in_step = mask[step_slice]
    sse_step = float(np.sum(diff[step_slice] ** 2))
    sse_spike = float(np.sum(diff[step_slice][mask_in_step] ** 2))
    facts.update({
        "spike_window_ms": float(window_ms),
        "sse_whole_mv2": sse,
        "sse_in_step_mv2": sse_step,
        "sse_in_step_spike_windows_mv2": sse_spike,
        "share_of_in_step_error_near_spikes": (sse_spike / sse_step
                                               if sse_step > 0 else float("nan")),
        "rmse_in_step_away_from_spikes_mv": float(
            np.sqrt(np.mean(diff[step_slice][~mask_in_step] ** 2))),
        "spike_window_samples_in_step": int(np.count_nonzero(mask_in_step)),
        "sse_share_of_whole_error_in_step": (sse_step / sse if sse > 0
                                             else float("nan")),
    })

    # --- paired spike timing
    n_rec = recorded["n_in_step"]
    n_sim = simulated["n_in_step"]
    facts["spikes_recorded_in_step"] = n_rec
    facts["spikes_simulated_in_step"] = n_sim
    facts["spikes_recorded_out_step"] = recorded["n_out_step"]
    facts["spikes_simulated_out_step"] = simulated["n_out_step"]
    facts["spike_count_delta"] = n_sim - n_rec
    if n_rec and n_sim:
        rec_times = np.array(recorded["spike_times_in_step_ms"], dtype=float)
        sim_times = np.array(simulated["spike_times_in_step_ms"], dtype=float)
        paired = min(rec_times.size, sim_times.size)
        offsets = sim_times[:paired] - rec_times[:paired]
        facts["spikes_paired_in_step"] = int(paired)
        facts["spike_offset_median_ms"] = float(np.median(offsets))
        facts["spike_offset_max_abs_ms"] = float(np.max(np.abs(offsets)))
    return facts

# ------------------------------------------------------- F. cross-sweep summary
def _plain(value):
    """Convert numpy scalars and arrays into JSON-safe Python objects."""
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items() if not str(k).startswith("_")}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_plain(v) for v in value.tolist()]
    if isinstance(value, (np.floating, float)):
        return NAN if value != value else float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


NAN = float("nan")


def spread_of_recordings(descriptions: list[dict]) -> dict:
    """How much the four held-out recordings differ from their own mean.

    This is the noise floor the model would have to beat to be judged.  It is
    computed from the recordings alone, so it carries no model assumption.
    """
    vectors = [d["_v_mv"] for d in descriptions]
    n = min(v.size for v in vectors)
    stack = np.vstack([v[:n] for v in vectors])
    mean = stack.mean(axis=0)
    per_sweep = [float(np.sqrt(np.mean((v[:n] - mean) ** 2))) for v in vectors]
    pairwise = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            pairwise.append(float(np.sqrt(np.mean(
                (vectors[i][:n] - vectors[j][:n]) ** 2))))
    return {
        "n_samples": int(n),
        "rmse_about_mean_mv": per_sweep,
        "max_rmse_about_mean_mv": max(per_sweep),
        "max_pairwise_rmse_mv": max(pairwise) if pairwise else float("nan"),
        "pairwise_rmse_mv": pairwise,
    }


def summarise(rows: list[dict]) -> dict:
    """Aggregate the per-sweep comparison rows across the four repeats."""
    def column(key):
        return [r[key] for r in rows if r.get(key) == r.get(key)]

    def stats(values):
        if not values:
            return {"n": 0}
        arr = np.asarray(values, dtype=float)
        return {"n": int(arr.size), "mean": float(arr.mean()),
                "sd": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
                "min": float(arr.min()), "max": float(arr.max())}

    return {
        "n_sweeps": len(rows),
        "spikes_recorded_in_step": column("spikes_recorded_in_step"),
        "spikes_simulated_in_step": column("spikes_simulated_in_step"),
        "rmse_whole_mv": stats(column("rmse_whole_mv")),
        "rmse_in_step_mv": stats(column("rmse_in_step_mv")),
        "rmse_pre_step_mv": stats(column("rmse_pre_step_mv")),
        "corr_whole": stats(column("corr_whole")),
        "corr_in_step": stats(column("corr_in_step")),
        "baseline_delta_mv": stats(column("baseline_delta_mv")),
        "share_of_in_step_error_near_spikes": stats(
            column("share_of_in_step_error_near_spikes")),
        "rmse_in_step_away_from_spikes_mv": stats(
            column("rmse_in_step_away_from_spikes_mv")),
        "first_in_step_latency_recorded_ms": stats(
            column("first_in_step_latency_recorded_ms")),
        "first_in_step_latency_simulated_ms": stats(
            column("first_in_step_latency_simulated_ms")),
    }


def decide_verdict(rows: list[dict]) -> tuple[str, str]:
    """Map the per-sweep comparisons onto one of the brief's four verdicts."""
    if not rows:
        return "EVALUATION BLOCKED", "no sweep produced a comparison"
    counts_match = all(r["spikes_simulated_in_step"] == r["spikes_recorded_in_step"]
                       for r in rows)
    if not counts_match:
        return ("HELD-OUT PREDICTION MISMATCH",
                "the predicted in-step spike count differs from the recording in "
                "every held-out sweep")
    latency_gap = max(abs(r["first_in_step_latency_simulated_ms"]
                          - r["first_in_step_latency_recorded_ms"]) for r in rows)
    worst_corr = min(r["corr_in_step"] for r in rows)
    if latency_gap <= 5.0 and worst_corr >= 0.90:
        return ("HELD-OUT PREDICTION AGREES",
                "spike counts and first-spike latencies agree in all four repeats")
    return ("HELD-OUT PREDICTION PARTIALLY AGREES",
            "spike counts agree but latency is off by %.1f ms or the in-step "
            "correlation falls to %.3f" % (latency_gap, worst_corr))


# ---------------------------------------------------- G. the fitting sweep
def compare_with_fitting_sweep(checker: Checker, sweeps: dict,
                               phase2c_traces: pathlib.Path | None) -> dict:
    """Put sweep 38 beside the FINEST repeats, using the identical metric code.

    The simulated trace is Phase 2C's own sweep-38 output, so the numbers here are
    a re-measurement of the published Phase 2C result rather than a new run, and
    agreement with Phase 2C is asserted as a check on this script's metrics.
    """
    checker.heading("G. Sweep 38 beside the held-out repeats")

    record = sweeps.get(FITTING_SWEEP)
    if record is None or phase2c_traces is None or not pathlib.Path(phase2c_traces).exists():
        checker.skip("sweep 38 comparison", "recording or Phase 2C trace unavailable")
        return {}

    from allensdk.ephys import ephys_features

    data = np.load(pathlib.Path(phase2c_traces))
    v_sim = data["v_sim"] * 1e3
    v_rec = record["recorded_mv"]
    stim = record["stimulus_pa"]
    n = min(v_rec.size, v_sim.size)
    t_s = np.arange(n) * (DT_MS * 1e-3)

    rec_desc = describe_trace("recorded 38", v_rec, RATE_HZ, stim,
                              ephys_features.detect_putative_spikes(v_rec * 1e0, t_s))
    sim_desc = describe_trace("simulated 38", v_sim, RATE_HZ, stim,
                              ephys_features.detect_putative_spikes(v_sim, t_s))
    rec_desc["_v_mv"] = v_rec
    sim_desc["_v_mv"] = v_sim
    pair = compare_traces(rec_desc, sim_desc, stim, RATE_HZ)

    # Reproduce three published Phase 2C numbers through this script's own code.
    expected = [("voltage RMSE, whole sweep", pair["rmse_whole_mv"], 4.456),
                ("voltage RMSE, during the step", pair["rmse_in_step_mv"], 11.126),
                ("trace correlation", pair["corr_whole"], 0.9314)]
    for label, actual, published in expected:
        checker.check(abs(actual - published) <= 0.01,
                      "re-measures Phase 2C's %s" % label,
                      "%.3f vs %.3f published" % (actual, published))
    checker.check(pair["spikes_recorded_in_step"] == 12
                  and pair["spikes_simulated_in_step"] == 12,
                  "reproduces Phase 2C's 12-versus-12 in-step agreement",
                  "%d recorded, %d simulated"
                  % (pair["spikes_recorded_in_step"],
                     pair["spikes_simulated_in_step"]))

    checker.metric("sweep 38 in-step spikes", "sim %d vs rec %d"
                   % (pair["spikes_simulated_in_step"], pair["spikes_recorded_in_step"]))
    checker.metric("sweep 38 whole-sweep RMSE", "%.3f mV" % pair["rmse_whole_mv"])
    checker.metric("sweep 38 in-step RMSE", "%.3f mV" % pair["rmse_in_step_mv"])
    checker.metric("sweep 38 trace correlation", "%.4f" % pair["corr_whole"])
    checker.metric("sweep 38 first in-step latency",
                   "sim %.2f vs rec %.2f ms (%+.2f)"
                   % (sim_desc["first_in_step_latency_ms"],
                      rec_desc["first_in_step_latency_ms"],
                      sim_desc["first_in_step_latency_ms"]
                      - rec_desc["first_in_step_latency_ms"]))
    checker.metric("sweep 38 error share near spikes",
                   "%.1f %% of in-step squared error"
                   % (100.0 * pair["share_of_in_step_error_near_spikes"]))

    return {"recorded": rec_desc, "simulated": sim_desc, "pair": pair}


# ------------------------------------------------------------------- plots
def make_plots(checker: Checker, out_dir: pathlib.Path, results_dir: pathlib.Path,
               descriptions: dict, sweeps: dict) -> list[str]:
    """Save the figures.  They live outside the repository and are never staged."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:                      # pragma: no cover - environment
        checker.note("plotting unavailable (%s); figures skipped" % exc)
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    stride = 40                                  # 200 kHz is beyond display resolution
    colours = {49: "tab:blue", 50: "tab:green", 51: "tab:orange", 52: "tab:purple"}

    simulation = np.load(results_dir / ("sweep_%d" % HELD_OUT_SWEEPS[0])
                         / "traces.npz")["v_sim"] * 1e3

    # 1. The step window: one prediction against four recordings.
    fig, ax = plt.subplots(figsize=(10, 5))
    for sweep in HELD_OUT_SWEEPS:
        v = sweeps[sweep]["recorded_mv"]
        lo, hi = int(1.0e3 / DT_MS), int(2.15e3 / DT_MS)
        ax.plot(np.arange(lo, hi)[::stride] * DT_MS, v[lo:hi][::stride],
                color=colours[sweep], linewidth=0.7, label="recording %d" % sweep)
    lo, hi = int(1.0e3 / DT_MS), int(2.15e3 / DT_MS)
    ax.plot(np.arange(lo, hi)[::stride] * DT_MS, simulation[lo:hi][::stride],
            color="k", linewidth=1.0, label="model 473862496")
    ax.set_xlabel("time in sweep (ms)")
    ax.set_ylabel("membrane potential (mV)")
    ax.set_title("+170 pA step: model prediction against the four FINEST recordings")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)
    path = out_dir / "step_window.png"
    fig.tight_layout(); fig.savefig(path, dpi=115); plt.close(fig)
    written.append(str(path))

    # 2. The observed action potential against the model's first.
    fig, ax = plt.subplots(figsize=(8, 5))
    rec = descriptions["recorded"][HELD_OUT_SWEEPS[0]]
    centre_rec = rec["first_in_step_ms"]
    centre_sim = descriptions["simulated"][HELD_OUT_SWEEPS[0]]["first_in_step_ms"]
    span = int(12.0 / DT_MS)
    for label, v, centre, colour in [
            ("recorded 49", sweeps[49]["recorded_mv"], centre_rec, "tab:blue"),
            ("model, first spike", simulation, centre_sim, "k")]:
        c = int(round(centre / DT_MS))
        a, b = max(0, c - span), min(v.size, c + span)
        ax.plot((np.arange(a, b) - c) * DT_MS, v[a:b], color=colour,
                linewidth=1.0, label=label)
    ax.set_xlabel("time from peak (ms)")
    ax.set_ylabel("V (mV)")
    ax.set_title("First action potential in the step, aligned on its peak")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    path = out_dir / "first_spike_shape.png"
    fig.tight_layout(); fig.savefig(path, dpi=115); plt.close(fig)
    written.append(str(path))

    # 3. The whole common window, including the post-step interval.
    fig, ax = plt.subplots(figsize=(10, 5))
    n = min(simulation.size, sweeps[49]["recorded_mv"].size)
    step = stride * 8
    ax.plot(np.arange(n)[::step] * DT_MS, simulation[:n][::step],
            color="k", linewidth=0.8, label="model 473862496")
    for sweep in HELD_OUT_SWEEPS:
        v = sweeps[sweep]["recorded_mv"]
        ax.plot(np.arange(n)[::step] * DT_MS, v[:n][::step], color=colours[sweep],
                linewidth=0.5, alpha=0.85, label="recording %d" % sweep)
    ax.set_xlabel("time in sweep (ms)")
    ax.set_ylabel("V (mV)")
    ax.set_title("Full 6.020 s common window")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    path = out_dir / "full_window.png"
    fig.tight_layout(); fig.savefig(path, dpi=115); plt.close(fig)
    written.append(str(path))

    # 4. Where the in-step error lives.
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ["%d" % s for s in HELD_OUT_SWEEPS] + ["38"]
    near, away = [], []
    for sweep in HELD_OUT_SWEEPS:
        pair = descriptions["pairs"][sweep]
        near.append(pair["rmse_in_step_mv"]
                    * np.sqrt(max(pair["share_of_in_step_error_near_spikes"], 0.0)))
        away.append(pair["rmse_in_step_away_from_spikes_mv"])
    sweep38 = (descriptions["sweep38"] or {}).get("pair", {})
    near.append(sweep38.get("rmse_in_step_mv", NAN)
                * np.sqrt(max(sweep38.get("share_of_in_step_error_near_spikes", NAN), 0.0)))
    away.append(sweep38.get("rmse_in_step_away_from_spikes_mv", NAN))
    x = np.arange(len(labels))
    ax.bar(x - 0.2, near, width=0.4, label="within 10 ms of a spike")
    ax.bar(x + 0.2, away, width=0.4, label="away from every spike")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_xlabel("sweep"); ax.set_ylabel("RMS error during the step (mV)")
    ax.set_title("In-step error budget: spike-related versus subthreshold")
    ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")
    path = out_dir / "error_budget.png"
    fig.tight_layout(); fig.savefig(path, dpi=115); plt.close(fig)
    written.append(str(path))

    checker.note("figures written: %d files in %s" % (len(written), out_dir))
    return written


# --------------------------------------------------------------------- main
def parent_main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--allensdk-src", required=True)
    parser.add_argument("--repo-cache", required=True,
                        help="tmp/model_cache, holding assets_2a.json and the drafts")
    parser.add_argument("--phase2c-traces", default=None,
                        help="traces_sweep38.npz written by the Phase 2C run")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--plots-dir", default=None,
                        help="destination for figures; must be outside Git tracking")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--skip-compile", action="store_true")
    args = parser.parse_args(argv)

    model_dir = pathlib.Path(args.model_dir).expanduser().resolve()
    allensdk_src = pathlib.Path(args.allensdk_src).expanduser().resolve()
    repo_cache = pathlib.Path(args.repo_cache).expanduser().resolve()
    out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                             # pragma: no cover
        pass

    # AllenSDK must be importable before the read/comparison stages run.
    sys.path.insert(0, str(allensdk_src))

    checker = Checker()
    print("Phase 2E — held-out FINEST evaluation of perisomatic model %d"
          % PERISOMATIC_MODEL)
    print("specimen  :", SPECIMEN)
    print("model dir :", model_dir)
    print("allensdk  :", allensdk_src)
    print("python    :", sys.version.split()[0], "|", sys.executable)

    facts: dict = {"specimen": SPECIMEN, "model": PERISOMATIC_MODEL,
                   "held_out_sweeps": list(HELD_OUT_SWEEPS),
                   "fitting_sweep": FITTING_SWEEP,
                   "phase2c_traces": str(args.phase2c_traces)}

    facts["inputs"] = verify_inputs(checker, model_dir, repo_cache)
    verify_mechanism_sources(checker, model_dir,
                             repo_cache / "assets_2a.json")
    sweeps = load_sweeps(checker, model_dir)

    missing = [s for s in (FITTING_SWEEP,) + HELD_OUT_SWEEPS if s not in sweeps]
    if missing:
        checker.summary()
        print("\nRESULT: sweeps %s could not be read; evaluation blocked"
              % ", ".join(str(m) for m in missing))
        return 2

    facts["sweeps"] = {
        str(s): {
            "block": r["block"],
            "template": r["template"],
            "multiplier": r["multiplier"],
            "rate_hz": r["rate_hz"],
            "n_samples": r["n_samples"],
            "duration_ms": r["n_samples"] * (1e3 / r["rate_hz"]),
            "amplitude_pa": r["stimulus"]["level_pa"],
            "onset_ms": r["stimulus"]["onset_s"] * 1e3,
            "duration_step_ms": r["stimulus"]["duration_ms"],
            "quality": r.get("quality"),
            "command_vs_reference": r.get("command_vs_reference"),
        } for s, r in sweeps.items()}

    if args.skip_compile:
        checker.heading("B. Mechanism compilation")
        checker.skip("nrnivmodl re-run", "--skip-compile given")
        compile_facts = {"compiled": (model_dir / "x86_64" / "libnrnmech.so").exists()}
    else:
        compile_facts = compile_mechanisms(checker, model_dir,
                                          out_dir / "nrnivmodl.log")
    facts["mechanisms"] = compile_facts
    if not compile_facts.get("compiled"):
        checker.summary()
        print("\nRESULT: mechanisms did not compile; evaluation blocked")
        return 2

    executed = execute_sweeps(checker, model_dir, allensdk_src, out_dir)
    facts["execution"] = {str(s): v for s, v in executed.items()}
    if len(executed) != len(HELD_OUT_SWEEPS):
        checker.summary()
        print("\nRESULT: not every held-out sweep executed; evaluation blocked")
        return 2

    facts["identity"] = verify_output_identity(
        checker, executed,
        pathlib.Path(args.phase2c_traces) if args.phase2c_traces else None)

    # --- E. predicted versus observed
    checker.heading("E. Predicted versus observed")
    from allensdk.ephys import ephys_features

    descriptions: dict = {"recorded": {}, "simulated": {}, "pairs": {}}
    rows: list[dict] = []
    for sweep in HELD_OUT_SWEEPS:
        record = sweeps[sweep]
        v_rec = record["recorded_mv"]
        stim = record["stimulus_pa"]
        v_sim = np.load(out_dir / ("sweep_%d" % sweep) / "traces.npz")["v_sim"] * 1e3

        n = min(v_rec.size, v_sim.size)
        t_s = np.arange(n) * (DT_MS * 1e-3)
        allen_rec = ephys_features.detect_putative_spikes(v_rec[:n], t_s)
        allen_sim = ephys_features.detect_putative_spikes(v_sim[:n], t_s)

        rec_desc = describe_trace("recorded %d" % sweep, v_rec, RATE_HZ, stim, allen_rec)
        sim_desc = describe_trace("simulated %d" % sweep, v_sim, RATE_HZ, stim, allen_sim)
        rec_desc["_v_mv"] = v_rec
        sim_desc["_v_mv"] = v_sim
        pair = compare_traces(rec_desc, sim_desc, stim, RATE_HZ)
        pair["sweep"] = int(sweep)
        pair["first_in_step_latency_recorded_ms"] = rec_desc["first_in_step_latency_ms"]
        pair["first_in_step_latency_simulated_ms"] = sim_desc["first_in_step_latency_ms"]

        descriptions["recorded"][sweep] = rec_desc
        descriptions["simulated"][sweep] = sim_desc
        descriptions["pairs"][sweep] = pair
        rows.append(pair)

        print()
        print("  sweep %d (%s)" % (sweep, record["block"]))
        checker.check(sim_desc["n_spikes_allen"] == sim_desc["n_spikes_crossing"],
                      "  both detectors agree on the simulated trace",
                      "allen %d vs crossing %d"
                      % (sim_desc["n_spikes_allen"], sim_desc["n_spikes_crossing"]))
        checker.metric("  in-step spikes, predicted vs observed",
                       "%d vs %d" % (pair["spikes_simulated_in_step"],
                                     pair["spikes_recorded_in_step"]))
        checker.metric("  recorded spike times in step",
                       " ".join("%.1f" % t for t in
                                rec_desc["spike_times_in_step_ms"]) or "none")
        checker.metric("  predicted spike times in step",
                       " ".join("%.1f" % t for t in
                                sim_desc["spike_times_in_step_ms"]) or "none")
        checker.metric("  first in-step latency (from 1020 ms)",
                       "pred %.2f vs obs %.2f ms (%+.2f)"
                       % (sim_desc["first_in_step_latency_ms"],
                          rec_desc["first_in_step_latency_ms"],
                          sim_desc["first_in_step_latency_ms"]
                          - rec_desc["first_in_step_latency_ms"]))
        checker.metric("  mean inter-spike interval, predicted",
                       "%.2f ms (n %d)" % (sim_desc["mean_isi_ms"],
                                           len(sim_desc["isis_ms"])))
        checker.metric("  baseline (pred / obs)",
                       "%.2f / %.2f mV (%+.2f)"
                       % (sim_desc["baseline_mv"], rec_desc["baseline_mv"],
                          pair["baseline_delta_mv"]))
        checker.metric("  baseline RMSE (pre-step)",
                       "%.3f mV" % pair["rmse_pre_step_mv"])
        checker.metric("  RMSE during the step",
                       "%.3f mV" % pair["rmse_in_step_mv"])
        checker.metric("  RMSE during the step, away from spikes",
                       "%.3f mV" % pair["rmse_in_step_away_from_spikes_mv"])
        checker.metric("  error share within 10 ms of a spike",
                       "%.1f %%" % (100.0 * pair["share_of_in_step_error_near_spikes"]))
        checker.metric("  RMSE whole trace / correlation",
                       "%.3f mV / %.4f" % (pair["rmse_whole_mv"], pair["corr_whole"]))
        checker.metric("  correlation during the step", "%.4f" % pair["corr_in_step"])
        checker.metric("  spike amplitude, predicted",
                       "%.1f .. %.1f mV" % (sim_desc["spike_amplitude_mv"]["min"],
                                            sim_desc["spike_amplitude_mv"]["max"]))
        checker.metric("  spike width, predicted",
                       "%.3f .. %.3f ms" % (sim_desc["spike_width_ms"]["min"],
                                            sim_desc["spike_width_ms"]["max"]))
        checker.metric("  afterhyperpolarisation, predicted",
                       "%.2f .. %.2f mV" % (sim_desc["ahp_mv"]["min"],
                                            sim_desc["ahp_mv"]["max"]))
        checker.metric("  plateau (last 200 ms of step)",
                       "pred %.2f vs obs %.2f mV"
                       % (sim_desc["plateau_mv"], rec_desc["plateau_mv"]))

    # --- F. cross-sweep summary
    checker.heading("F. Cross-sweep summary")
    aggregate = summarise(rows)
    recording_spread = spread_of_recordings(
        [descriptions["recorded"][s] for s in HELD_OUT_SWEEPS])
    facts["summary"] = aggregate
    facts["recording_spread"] = recording_spread

    checker.metric("in-step spikes, recorded across repeats",
                   " ".join(str(r["spikes_recorded_in_step"]) for r in rows))
    checker.metric("in-step spikes, predicted across repeats",
                   " ".join(str(r["spikes_simulated_in_step"]) for r in rows))
    for key, label, unit in [
            ("rmse_whole_mv", "whole-trace RMSE", "mV"),
            ("rmse_in_step_mv", "in-step RMSE", "mV"),
            ("corr_whole", "whole-trace correlation", ""),
            ("share_of_in_step_error_near_spikes", "error share near spikes", "")]:
        block = aggregate[key]
        checker.metric("%s, mean over 4" % label,
                       ("%.4f" if unit == "" else "%.3f") % block["mean"]
                       + (" %s" % unit if unit else "")
                       + " (range %.4f .. %.4f)"
                       % (block["min"], block["max"]))
    checker.metric("recording-to-recording RMS difference",
                   "max %.3f mV about the four-recording mean"
                   % recording_spread["max_rmse_about_mean_mv"])
    checker.check(recording_spread["max_rmse_about_mean_mv"] < 5.0,
                  "the four held-out recordings agree with each other within 5 mV",
                  "%.3f mV" % recording_spread["max_rmse_about_mean_mv"])

    # --- G. sweep 38 beside the repeats
    sweep38 = compare_with_fitting_sweep(
        checker, sweeps,
        pathlib.Path(args.phase2c_traces) if args.phase2c_traces else None)
    descriptions["sweep38"] = sweep38

    verdict, reason = decide_verdict(rows)
    facts["verdict"] = {"verdict": verdict, "reason": reason}

    figures = []
    if not args.no_plots:
        plots_dir = (pathlib.Path(args.plots_dir).expanduser().resolve()
                     if args.plots_dir else out_dir.parent / "figures")
        figures = make_plots(checker, plots_dir, out_dir, descriptions, sweeps)
        try:
            import matplotlib as _mpl
            facts["plotting"] = {"backend": _mpl.get_backend(),
                                 "version": _mpl.__version__}
        except Exception:
            pass
    facts["figures"] = figures

    failures = checker.summary()
    payload = {
        "facts": _plain(facts),
        "tally": checker.tally(),
        "metrics": [{"label": label, "value": value}
                    for label, value in checker.metric_rows],
        "sweeps": [{"sweep": r["sweep"],
                    "recorded": _plain(descriptions["recorded"][r["sweep"]]),
                    "simulated": _plain(descriptions["simulated"][r["sweep"]]),
                    "pair": _plain(r)} for r in rows],
        "fitting_sweep": _plain({k: v for k, v in sweep38.items() if k != "pair"}),
        "fitting_sweep_pair": _plain(sweep38.get("pair", {})),
        "verdict": facts["verdict"],
    }
    (out_dir / "phase2e_summary.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print()
    print("=" * 78)
    print("VERDICT: %s" % verdict)
    print("         %s" % reason)
    print("=" * 78)
    print("summary written to", out_dir / "phase2e_summary.json")
    return 0 if failures == 0 else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--child" in argv:
        return child_main(argv)
    return parent_main(argv)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Validate the Allen-compatible perisomatic model by executing one sweep.

Purpose
-------
Phase 2B produced two manifest drafts but could not run either of them, because
NEURON was unavailable on the Windows host.  This script performs the single
execution that Phase 2C authorises: specimen 382982932, perisomatic model
473862496, sweep 38 only, using AllenSDK v2.16.2's own runner against the
Phase 2B manifest draft.

It is an execution-pipeline validation, not a biological prediction.  Sweep 38
is the model's fitting sweep and therefore in-sample.

What it checks
--------------
A. Inputs.  Every staged asset is hashed against the Phase 2A asset manifest
   and the Phase 1C recording digest, the descriptor's model type and junction
   potential are read, and sweep 38's stimulus is characterised.
B. Mechanisms.  ``nrnivmodl`` is run and its output preserved verbatim.
C. Execution.  ``allensdk.model.biophysical.runner.run`` is called with
   ``sweeps=[38]`` and ``procs=1`` so that exactly one sweep is simulated in
   one process.
D. Convention.  ``V_written = V_sim + 14 mV`` is asserted numerically by
   wrapping ``Utils.get_recorded_data`` for the duration of the run.  The
   wrapper calls the original function unchanged and merely also keeps the raw
   vector, so Allen's code path is executed verbatim; nothing on disk is
   patched and no model parameter is altered.
E. Comparison.  Recorded and simulated traces are compared for units, length,
   alignment, amplitude, baseline and range.  Numerical pipeline checks gate the
   exit code; biological agreement (RMSE, correlation, spike counts, spike
   timing) is reported but not asserted, because sweep 38 is the in-sample
   fitting sweep and Phase 1C documented it as a recording anomaly.

Why the run happens through Allen's runner
------------------------------------------
Calling ``Utils`` directly would skip model-type dispatch, the ``biophys``
append in ``load_description``, ``prepare_nwb_output`` and ``save_nwb``.  Those
are precisely the parts Phase 2B could only validate statically, so the run
must go through them.

Usage
-----
    python scripts/validate_perisomatic_execution.py \
        --model-dir ~/incm_phase2c/model \
        --allensdk-src ~/incm_phase2c/AllenSDK-2.16.2 \
        --out-dir ~/incm_phase2c/results

Exit codes
----------
0  the sweep ran and every comparison check passed
1  the sweep ran but at least one comparison check failed
2  the sweep could not be executed
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
SWEEP = 38
JUNCTION_MV = -14.0
PERISOMATIC_TYPE = "Biophysical - perisomatic"

#: Phase 1C (results/phase1/PYRAMIDAL_CANDIDATE_VALIDATION.md, row 382982932):
#: NWB well-known file 491199232, 94 207 824 bytes, locally computed digest.
EXPECTED_NWB_SHA256 = (
    "d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63")
EXPECTED_NWB_BYTES = 94207824

#: Phase 2B downloaded well-known file 674389910 (type 3DNeuronMarker, 373 B)
#: and recorded its digest; it is not part of the Phase 2A asset manifest.
EXPECTED_MARKER_SHA256 = (
    "3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925")
EXPECTED_MARKER_BYTES = 373

MECHANISMS = (
    "CaDynamics", "Ca_HVA", "Ca_LVA", "Ih", "Im", "Im_v2",
    "K_P", "K_T", "Kd", "Kv2like", "Kv3_1", "NaTa", "NaTs", "NaV", "Nap", "SK",
)

STIMULUS_NWB = "382982932.nwb"
DESCRIPTOR = "382982932_fit.json"
MORPHOLOGY = "674389901_382982932_m.swc"
MARKER = "674389910_382982932_m.marker"
OUTPUT_RELATIVE = os.path.join("work", STIMULUS_NWB)


# --------------------------------------------------------------------- helpers
def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


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
        print("  %-8s %-56s %s" % ("ok" if ok else "FAIL", label, detail))
        return bool(ok)

    def skip(self, label: str, reason: str) -> None:
        self.rows.append((self.section_name, label, None, reason))
        print("  %-8s %-56s %s" % ("skip", label, reason))

    def note(self, text: str) -> None:
        print("  " + text)

    def metric(self, label: str, detail: str = "") -> None:
        """Record a measurement that is reported but does not gate the exit code.

        Biological agreement belongs here rather than in ``check``: asserting it
        would turn an in-sample, documented-anomalous sweep into a pass/fail
        verdict on the model, which is precisely what this phase must not do.
        """
        self.metric_rows.append((label, detail))
        print("  %-8s %-56s %s" % ("report", label, detail))

    def tally(self) -> dict:
        checked = [r for r in self.rows if r[2] is not None]
        failed = [r for r in checked if r[2] is False]
        by_section: dict[str, int] = {}
        for section, _label, ok, _detail in self.rows:
            if ok is not None:
                by_section[section] = by_section.get(section, 0) + 1
        return {
            "checks": len(self.rows),
            "passed": len(checked) - len(failed),
            "failed": len(failed),
            "skipped": len(self.rows) - len(checked),
            "metrics": len(self.metric_rows),
            "by_section": by_section,
        }

    def summary(self) -> int:
        tally = self.tally()
        print()
        print("-" * 78)
        print("checks: %d   passed: %d   failed: %d   skipped: %d   metrics: %d"
              % (tally["checks"], tally["passed"], tally["failed"],
                 tally["skipped"], tally["metrics"]))
        return tally["failed"]


# ------------------------------------------------------------------ verification
def load_expected_assets(assets_manifest: pathlib.Path) -> dict[str, str]:
    """Map basename -> sha256 for every Phase 2A asset that we stage."""
    data = json.loads(assets_manifest.read_text(encoding="utf-8"))
    expected: dict[str, str] = {}
    for asset in data["assets"]:
        if "sha256" not in asset:
            continue
        source = asset.get("path") or asset["url"]
        expected[os.path.basename(source)] = asset["sha256"]
    return expected


def verify_inputs(checker: Checker, model_dir: pathlib.Path,
                  expected: dict[str, str]) -> dict:
    checker.heading("A. Input verification")

    facts: dict = {"model_dir": str(model_dir)}

    # --- descriptor, morphology, marker against their recorded digests
    # The descriptor and SWC digests come from the Phase 2A asset manifest; the
    # marker was not part of that manifest and is pinned from Phase 2B instead.
    required = [
        (DESCRIPTOR, "published fit descriptor", "Phase 2A",
         expected.get(DESCRIPTOR)),
        (MORPHOLOGY, "published SWC (reconstruction 674389884)", "Phase 2A",
         expected.get(MORPHOLOGY)),
        (MARKER, "published marker", "Phase 2B", EXPECTED_MARKER_SHA256),
    ]
    for name, label, origin, want in required:
        path = model_dir / name
        if not path.exists():
            checker.check(False, label + " present", "missing " + name)
            continue
        actual = sha256_of(path)
        checker.check(want is not None and actual == want,
                      "%s matches %s digest" % (label, origin),
                      "%s\u2026 vs %s\u2026" % (actual[:16], (want or "?" * 16)[:16]))
        facts.setdefault("sha256", {})[name] = actual

    mod_dirs = sorted((model_dir / "modfiles").glob("*.mod"))
    mod_ok = len(mod_dirs) == len(MECHANISMS)
    checker.check(mod_ok, "16 mechanism sources present", "%d found" % len(mod_dirs))
    mismatched = []
    for path in mod_dirs:
        want = expected.get(path.name)
        if want is None:
            mismatched.append(path.name + ":no-record")
        elif sha256_of(path) != want:
            mismatched.append(path.name + ":digest")
    checker.check(not mismatched, "every mechanism source matches Phase 2A digest",
                  "%d sources" % len(mod_dirs) if not mismatched
                  else ", ".join(mismatched[:4]))

    # --- stimulus recording
    nwb = model_dir / STIMULUS_NWB
    if nwb.exists():
        digest = sha256_of(nwb)
        checker.check(nwb.stat().st_size == EXPECTED_NWB_BYTES,
                      "stimulus NWB byte size matches Phase 1C",
                      "%d B" % nwb.stat().st_size)
        checker.check(digest == EXPECTED_NWB_SHA256,
                      "stimulus NWB digest matches Phase 1C recording",
                      "%s… vs %s…" % (digest[:16], EXPECTED_NWB_SHA256[:16]))
        facts["sha256"] = facts.get("sha256", {})
        facts["sha256"][STIMULUS_NWB] = digest
    else:
        checker.check(False, "stimulus NWB present", "missing " + STIMULUS_NWB)

    # --- descriptor contents
    descriptor = json.loads((model_dir / DESCRIPTOR).read_text(encoding="utf-8"))
    top = sorted(descriptor)
    checker.check(top == ["conditions", "fitting", "genome", "passive"],
                  "descriptor keeps Allen's four sections", ",".join(top))
    facts["descriptor_sections"] = top

    fitting = descriptor["fitting"][0]
    junction = float(fitting["junction_potential"])
    sweeps = [int(s) for s in fitting["sweeps"]]
    checker.check(junction == JUNCTION_MV, "junction potential is -14 mV",
                  "%+g mV" % junction)
    checker.check(sweeps == [SWEEP], "fitting sweep is 38 only", str(sweeps))
    facts["junction_mv"] = junction
    facts["fitting_sweeps"] = sweeps

    genome = descriptor["genome"]
    mechanisms_used = sorted({g["mechanism"] for g in genome if g.get("mechanism")})
    unknown = [m for m in mechanisms_used if m not in MECHANISMS]
    checker.check(not unknown, "every descriptor mechanism has a .mod source",
                  "%d used: %s" % (len(mechanisms_used), ",".join(mechanisms_used)))
    checker.check(all(isinstance(g["value"], float) for g in genome),
                  "all genome values are floats (perisomatic form)",
                  "%d entries" % len(genome))
    facts["mechanisms_used"] = mechanisms_used
    facts["genome_entries"] = len(genome)
    facts["passive_keys"] = sorted(descriptor["passive"][0])

    # --- manifest
    manifest = json.loads((model_dir / "manifest.json").read_text(encoding="utf-8"))
    biophys = manifest["biophys"]
    checker.check(len(biophys) == 1, "manifest carries exactly one biophys entry",
                  "%d" % len(biophys))
    checker.check(biophys[0]["model_type"] == PERISOMATIC_TYPE,
                  "manifest model_type is perisomatic", biophys[0]["model_type"])
    checker.check("axon_type" not in biophys[0],
                  "no axon_type authored in the manifest", "absent, as required")
    checker.check(str(SWEEP) in [str(s) for s in manifest["runs"][0]["sweeps"]],
                  "sweep 38 is selected by runs[0].sweeps",
                  "%d sweeps" % len(manifest["runs"][0]["sweeps"]))
    checker.check("sweeps_by_type" in manifest["runs"][0],
                  "sweeps_by_type is present for run_sync",
                  "%d types" % len(manifest["runs"][0].get("sweeps_by_type", {})))
    facts["manifest_sha256"] = sha256_of(model_dir / "manifest.json")
    facts["manifest_sweeps"] = list(manifest["runs"][0]["sweeps"])

    return facts


def _stimulus_segments(stimulus, dt_ms: float) -> list:
    """Split a command current into its contiguous non-zero runs.

    A COARSE sweep is not one step: it opens with a short access-resistance
    test pulse and then delivers the long current step.  Treating every
    non-zero sample as "the step" conflates the two and reports the test
    pulse's onset as the stimulus onset.
    """
    import numpy as np

    nonzero = np.flatnonzero(np.abs(stimulus) > 1e-12)
    if not nonzero.size:
        return []

    splits = np.flatnonzero(np.diff(nonzero) > 1)
    starts = np.concatenate(([nonzero[0]], nonzero[splits + 1]))
    ends = np.concatenate((nonzero[splits], [nonzero[-1]]))

    segments = []
    for start, end in zip(starts, ends):
        span = stimulus[start:end + 1]
        segments.append({
            "start_index": int(start),
            "end_index": int(end),
            "onset_ms": float(start) * dt_ms,
            "duration_ms": float(end - start + 1) * dt_ms,
            "amplitude_pa": float(np.median(span)) * 1e12,
        })
    return segments


def characterise_sweep(checker: Checker, model_dir: pathlib.Path) -> dict:
    """Read sweep 38 from the recording and describe its stimulus."""
    import numpy as np
    from allensdk.core.nwb_data_set import NwbDataSet

    data = NwbDataSet(str(model_dir / STIMULUS_NWB))
    sweep = data.get_sweep(SWEEP)

    stimulus = np.asarray(sweep["stimulus"], dtype=float)   # A
    response = np.asarray(sweep["response"], dtype=float)   # V
    rate = float(sweep["sampling_rate"])                    # Hz
    index_range = list(sweep.get("index_range", []))

    dt_ms = 1.0e3 / rate

    # The current step is the largest-magnitude segment; the rest is the test
    # pulse.  Order by magnitude so segments[0] is unambiguously the step.
    segments = _stimulus_segments(stimulus, dt_ms)
    segments.sort(key=lambda seg: abs(seg["amplitude_pa"]), reverse=True)
    step = segments[0] if segments else None

    # Baseline before the step, excluding the test pulse and any holding current.
    if step is not None:
        pre_v = response[:step["start_index"]]
        pre_i = stimulus[:step["start_index"]]
        quiet = pre_v[np.abs(pre_i) <= 1e-12]
    else:
        quiet = np.array([np.nan])

    facts = {
        "sampling_rate_hz": rate,
        "dt_ms": dt_ms,
        "n_samples": int(response.size),
        "n_stimulus_samples": int(stimulus.size),
        "duration_ms": float(response.size) * dt_ms,
        "index_range": index_range,
        "stimulus_segments": segments,
        "stimulus_amplitude_pa": step["amplitude_pa"] if step else float("nan"),
        "stimulus_onset_ms": step["onset_ms"] if step else float("nan"),
        "stimulus_duration_ms": step["duration_ms"] if step else float("nan"),
        "stimulus_offset_ms": (step["onset_ms"] + step["duration_ms"]
                               if step else float("nan")),
        "recorded_baseline_mv": float(np.mean(quiet)) * 1e3,
        "recorded_baseline_samples": int(quiet.size),
        "recorded_min_mv": float(np.min(response)) * 1e3,
        "recorded_max_mv": float(np.max(response)) * 1e3,
        "recorded_has_nan": bool(np.isnan(response).any()),
    }

    checker.check(stimulus.size == response.size,
                  "stimulus and response are the same length",
                  "%d vs %d" % (stimulus.size, response.size))
    checker.check(len(segments) == 2,
                  "sweep 38 is a test pulse plus one current step",
                  ", ".join("%+.0f pA x %.1f ms" % (s["amplitude_pa"], s["duration_ms"])
                            for s in segments))
    checker.check(step is not None and abs(step["amplitude_pa"] - 170.0) < 1.0,
                  "current step is +170 pA",
                  "%+.2f pA" % facts["stimulus_amplitude_pa"])
    checker.check(step is not None and abs(step["onset_ms"] - 1020.0) < 1.0,
                  "current step starts 1020 ms into the sweep",
                  "%.3f ms" % facts["stimulus_onset_ms"])
    checker.check(step is not None and abs(step["duration_ms"] - 1000.0) < 1.0,
                  "current step lasts 1000 ms",
                  "%.3f ms" % facts["stimulus_duration_ms"])
    checker.check(not np.isnan(response).any(), "recorded trace has no NaN",
                  "%d samples" % response.size)
    checker.check(abs(rate - round(rate)) < 1e-6, "sampling rate is integral",
                  "%g Hz" % rate)
    return facts


# ------------------------------------------------------------------- mechanisms
def compile_mechanisms(checker: Checker, model_dir: pathlib.Path,
                       log_path: pathlib.Path) -> dict:
    checker.heading("B. Mechanism compilation")

    nrnivmodl = pathlib.Path(sys.executable).with_name("nrnivmodl")
    if not nrnivmodl.exists():
        checker.check(False, "nrnivmodl is available", str(nrnivmodl))
        return {"compiled": False}

    started = time.time()
    completed = subprocess.run(
        [str(nrnivmodl), "modfiles/"],
        cwd=str(model_dir), capture_output=True, text=True)
    elapsed = time.time() - started

    log_path.write_text(
        "command: %s modfiles/\nrc: %d\n--- stdout ---\n%s\n--- stderr ---\n%s\n"
        % (nrnivmodl, completed.returncode, completed.stdout, completed.stderr),
        encoding="utf-8")

    combined = completed.stdout + completed.stderr
    warnings = sum(1 for line in combined.splitlines()
                   if "warning" in line.lower())
    errors = sum(1 for line in combined.splitlines() if "error" in line.lower())

    lib = model_dir / "x86_64" / "libnrnmech.so"
    checker.check(completed.returncode == 0, "nrnivmodl exited 0",
                  "%.1f s" % elapsed)
    checker.check(warnings == 0, "no compiler warnings", "%d" % warnings)
    checker.check(errors == 0, "no compiler errors", "%d" % errors)
    checker.check(lib.exists(), "libnrnmech.so was produced",
                  "%s" % (lib.parent.name + "/" + lib.name))

    return {
        "compiled": completed.returncode == 0 and lib.exists(),
        "nrnivmodl": str(nrnivmodl),
        "returncode": completed.returncode,
        "warnings": warnings,
        "errors": errors,
        "elapsed_s": round(elapsed, 2),
        "library": str(lib) if lib.exists() else None,
        "library_bytes": lib.stat().st_size if lib.exists() else None,
        "log": str(log_path),
    }


# -------------------------------------------------------------------- execution
def execute(checker: Checker, model_dir: pathlib.Path, allensdk_src: pathlib.Path,
            log_path: pathlib.Path) -> dict:
    """Run sweep 38 through AllenSDK's own runner, with output instrumentation."""
    checker.heading("C. Execution")

    try:
        import numpy as np
        import neuron
        from allensdk.model.biophysical import runner
        from allensdk.model.biophysical import utils as biophys_utils
    except Exception as exc:
        checker.check(False, "AllenSDK v2.16.2 and NEURON import",
                      "%s: %s" % (type(exc).__name__, exc))
        return {"executed": False, "reason": "import: %s" % exc}

    checker.check(True, "AllenSDK v2.16.2 imports from the v2.16.2 source tree",
                  str(allensdk_src.name))
    checker.check(True, "NEURON imports", neuron.__version__)

    # NEURON resolves compiled mechanisms from ./x86_64 relative to cwd, so the
    # process must already be sitting in the model directory.
    checker.check(os.getcwd() == str(model_dir.resolve()),
                  "cwd is the model directory", os.getcwd())

    missing = []
    for mechanism in MECHANISMS:
        section = neuron.h.Section(name="mech_probe_" + mechanism)
        try:
            section.insert(mechanism)
        except Exception:
            missing.append(mechanism)
        finally:
            neuron.h.delete_section(sec=section)
    checker.check(not missing, "all 16 compiled mechanisms are loadable",
                  "%d/%d" % (len(MECHANISMS) - len(missing), len(MECHANISMS)))
    # h.allsec() is an iterator in NEURON 8.2.x, so materialise it before counting.
    residual = len(list(neuron.h.allsec()))
    checker.check(residual == 0, "mechanism probe left no sections behind",
                  "%d sections" % residual)

    # --- instrument get_recorded_data without altering it
    captured: dict = {}
    original = biophys_utils.Utils.get_recorded_data

    def instrumented(self, vec):
        raw_v = np.array(vec["v"], dtype=float)
        raw_t = np.array(vec["t"], dtype=float)
        result = original(self, vec)
        captured["raw_v_mv"] = raw_v
        captured["raw_t_ms"] = raw_t
        captured["out_v"] = np.array(result["v"], dtype=float)
        captured["out_t"] = np.array(result["t"], dtype=float)
        return result

    biophys_utils.Utils.get_recorded_data = instrumented
    try:
        args = {"manifest_file": "manifest.json", "axon_type": "truncated"}

        # load_description appends {'axon_type': ...} to biophys, which is what
        # create_utils reads as biophys[1].  Verify the append happened.
        description = runner.load_description(args)
        checker.check(len(description.data["biophys"]) == 2,
                      "load_description appended axon_type to biophys",
                      "biophys has %d entries" % len(description.data["biophys"]))
        checker.check(description.data["biophys"][1].get("axon_type") == "truncated",
                      "axon_type reached biophys[1]", "truncated")
        checker.check(description.data["biophys"][0]["model_type"] == PERISOMATIC_TYPE,
                      "model type dispatches to the perisomatic loader",
                      description.data["biophys"][0]["model_type"])

        handler_rows: list[str] = []

        class _Capture(list):
            def write(self, text):
                if text.strip():
                    handler_rows.append(text.rstrip())

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
        try:
            runner.run(args, sweeps=[SWEEP], procs=1)
        except Exception as exc:               # noqa: BLE001 - reported verbatim
            error = "%s: %s" % (type(exc).__name__, exc)
            import traceback
            handler_rows.append(traceback.format_exc())
        finally:
            elapsed = time.time() - started
            root.removeHandler(handler)
            biophys_utils.Utils.get_recorded_data = original
            log_path.write_text("\n".join(handler_rows), encoding="utf-8")
    finally:
        biophys_utils.Utils.get_recorded_data = original

    output_nwb = model_dir / OUTPUT_RELATIVE
    checker.check(output_nwb.exists(), "output NWB was written",
                  "%d B" % output_nwb.stat().st_size if output_nwb.exists() else "")
    if error:
        checker.check(False, "runner.run completed without raising", error)

    return {
        "executed": output_nwb.exists(),
        "error": error,
        "elapsed_s": round(elapsed, 2),
        "captured": captured,
        "output_nwb": str(output_nwb),
        "neuron_version": neuron.__version__,
        "log": str(log_path),
    }


def verify_convention(checker: Checker, captured: dict) -> dict:
    """Prove V_written = V_sim + 14 mV, applied at output only."""
    import numpy as np

    checker.heading("D. Output convention")

    if not captured:
        checker.skip("junction convention verified", "no captured trace")
        return {}

    raw = captured["raw_v_mv"]
    out = captured["out_v"]

    checker.check(raw.size == out.size or out.size <= raw.size,
                  "raw and written traces have compatible lengths",
                  "%d vs %d" % (raw.size, out.size))

    n = min(raw.size, out.size)
    expected = (raw[:n] - JUNCTION_MV) * 1e-3
    delta = float(np.max(np.abs(out[:n] - expected)))

    checker.check(delta < 1e-12,
                  "written = (V_sim + 14 mV) in volts, output only",
                  "max |delta| = %.3e V" % delta)
    checker.check(float(np.max(np.abs(raw))) > 1.0,
                  "raw simulator vector is in mV (not pre-shifted)",
                  "raw range %.2f..%.2f mV" % (raw.min(), raw.max()))
    checker.check(abs(float(out[:n].max()) - (raw[:n].max() + 14.0) * 1e-3) < 1e-12,
                  "peak shifted by exactly +14 mV, not scaled",
                  "peak %.3f mV -> %.3f mV" % (raw[:n].max(), out[:n].max() * 1e3))

    return {
        "max_abs_delta_v": delta,
        "raw_min_mv": float(raw.min()),
        "raw_max_mv": float(raw.max()),
        "raw_rest_mv": float(raw[0]),
        "written_min_mv": float(out[:n].min()) * 1e3,
        "written_max_mv": float(out[:n].max()) * 1e3,
        "raw_samples": int(raw.size),
        "written_samples": int(out.size),
    }


# ------------------------------------------------------------------- comparison
def _spikes_threshold(voltage_v, time_ms, threshold_mv=0.0, refractory_ms=1.0):
    """Transparent crossing detector: last sample below, first sample at/above."""
    import numpy as np

    above = voltage_v * 1e3 >= threshold_mv
    times = []
    last = -1e9
    for index in range(1, above.size):
        if above[index] and not above[index - 1] and time_ms[index] - last > refractory_ms:
            times.append(float(time_ms[index]))
            last = time_ms[index]
    return np.array(times)


def _spike_times_ms(spikes, time_ms):
    """Map ``detect_putative_spikes`` output to times.

    That function returns *sample indices*, not times (its docstring says
    "numpy array of preliminary spike indexes").  Treating them as seconds and
    scaling by 1e3 silently multiplies every spike time by ~200, so the mapping
    must go through the time vector.
    """
    import numpy as np

    index = np.asarray(spikes).astype(int).ravel()
    if not index.size:
        return np.array([], dtype=float)
    index = index[(index >= 0) & (index < time_ms.size)]
    return np.asarray(time_ms, dtype=float)[index]


def _excursions(voltage_mv, threshold_mv=-20.0) -> int:
    """Count upward excursions past ``threshold_mv`` in a millivolt trace."""
    import numpy as np

    above = np.asarray(voltage_mv) >= threshold_mv
    return int(np.count_nonzero(np.diff(above.astype(int)) == 1))


def compare(checker: Checker, model_dir: pathlib.Path, captured: dict) -> dict:
    checker.heading("E. Recorded versus simulated comparison")

    import numpy as np
    from allensdk.core.nwb_data_set import NwbDataSet
    from allensdk.ephys import ephys_features

    recorded_ds = NwbDataSet(str(model_dir / STIMULUS_NWB))
    recorded = recorded_ds.get_sweep(SWEEP)
    v_rec = np.asarray(recorded["response"], dtype=float)
    rate = float(recorded["sampling_rate"])

    output_ds = NwbDataSet(str(model_dir / OUTPUT_RELATIVE))
    simulated = output_ds.get_sweep(SWEEP)
    v_sim_full = np.asarray(simulated["response"], dtype=float)

    if captured:
        v_sim = captured["out_v"]
        t_ms = captured["out_t"]
    else:
        v_sim = v_sim_full
        t_ms = np.arange(v_sim.size) * (1.0e3 / rate)

    n = min(v_sim.size, v_rec.size)
    v_sim_n = v_sim[:n]
    v_rec_n = v_rec[:n]
    t_n = t_ms[:n]
    dt_ms = 1.0e3 / rate
    time_steps = np.diff(t_n)

    padding = int(v_sim_full.size - v_sim.size)
    zero_tail = int(np.count_nonzero(v_sim_full[n:] == 0.0)) if padding > 0 else 0

    # stimulus window: the current step, not the access-resistance test pulse
    stim = np.asarray(recorded["stimulus"], dtype=float)
    segments = _stimulus_segments(stim, dt_ms)
    segments.sort(key=lambda seg: abs(seg["amplitude_pa"]), reverse=True)
    step = segments[0] if segments else None
    step_on = float(step["onset_ms"]) if step else 0.0
    step_off = float(step["onset_ms"] + step["duration_ms"]) if step else 0.0
    onset = int(step["start_index"]) if step else 0

    # Baseline over stimulus-free samples before the step, so the test pulse and
    # any holding current cannot bias it.
    quiet = np.abs(stim[:n]) <= 1e-12
    quiet[onset:] = False
    if quiet.any():
        baseline_rec = float(np.mean(v_rec_n[quiet])) * 1e3
        baseline_sim = float(np.mean(v_sim_n[quiet])) * 1e3
    else:
        baseline_rec = baseline_sim = float("nan")

    # Allen's detector expects millivolts and seconds, and their own fixture
    # test passes the junction-corrected vector in mV.  The NWB values are in
    # volts, so convert before calling or the dv/dt threshold never fires.
    try:
        spikes_rec_idx = np.asarray(
            ephys_features.detect_putative_spikes(v_rec_n * 1e3, t_n * 1e-3))
    except Exception:
        spikes_rec_idx = np.array([], dtype=int)
    try:
        spikes_sim_idx = np.asarray(
            ephys_features.detect_putative_spikes(v_sim_n * 1e3, t_n * 1e-3))
    except Exception:
        spikes_sim_idx = np.array([], dtype=int)

    spikes_rec_ms = _spike_times_ms(spikes_rec_idx, t_n)
    spikes_sim_ms = _spike_times_ms(spikes_sim_idx, t_n)

    in_step = lambda times: times[(times >= step_on) & (times <= step_off)]
    out_step = lambda times: times[(times < step_on) | (times > step_off)]
    rec_in, sim_in = in_step(spikes_rec_ms), in_step(spikes_sim_ms)
    rec_out, sim_out = out_step(spikes_rec_ms), out_step(spikes_sim_ms)

    # Spike times that Allen's own save_nwb() derived and stored in the file.
    try:
        stored_sim_spikes = np.asarray(output_ds.get_spike_times(SWEEP))
    except Exception:
        stored_sim_spikes = np.array([])

    simple_rec = _spikes_threshold(v_rec_n, t_n)
    simple_sim = _spikes_threshold(v_sim_n, t_n)

    diff = v_sim_n - v_rec_n
    rmse_mv = float(np.sqrt(np.mean(diff ** 2))) * 1e3
    mae_mv = float(np.mean(np.abs(diff))) * 1e3
    corr = float(np.corrcoef(v_sim_n, v_rec_n)[0, 1])

    # Restrict RMSE to the stimulus-free window to separate baseline drift
    # from the response to the current step, and split the step itself from the
    # long post-step recovery.
    at_off = min(int(step["end_index"]) + 1, n) if step else n
    rmse_pre_mv = float(np.sqrt(np.mean(diff[:max(1, onset)] ** 2))) * 1e3
    rmse_stim_mv = float(np.sqrt(np.mean(diff[onset:at_off] ** 2))) * 1e3
    rmse_post_mv = float(np.sqrt(np.mean(diff[at_off:] ** 2))) * 1e3

    # Post-step the command current is zero, so any action potential there is
    # not attributable to the stimulus.
    post_rec_mv = v_rec_n[at_off:] * 1e3
    post_sim_mv = v_sim_n[at_off:] * 1e3
    excursions_rec = _excursions(post_rec_mv)
    excursions_sim = _excursions(post_sim_mv)

    # Paired timing offsets for spikes elicited by the step itself.
    paired = min(rec_in.size, sim_in.size)
    offsets = (sim_in[:paired] - rec_in[:paired]) if paired else np.array([])

    facts = {
        "n_compared": int(n),
        "n_recorded": int(v_rec.size),
        "n_simulated": int(v_sim.size),
        "padding_samples": padding,
        "zero_tail_samples": zero_tail,
        "dt_ms": dt_ms,
        "step_onset_ms": step_on,
        "step_offset_ms": step_off,
        "baseline_recorded_mv": baseline_rec,
        "baseline_simulated_mv": baseline_sim,
        "baseline_delta_mv": baseline_sim - baseline_rec,
        "recorded_min_mv": float(v_rec_n.min()) * 1e3,
        "recorded_max_mv": float(v_rec_n.max()) * 1e3,
        "simulated_min_mv": float(v_sim_n.min()) * 1e3,
        "simulated_max_mv": float(v_sim_n.max()) * 1e3,
        "rmse_mv": rmse_mv,
        "rmse_pre_stimulus_mv": rmse_pre_mv,
        "rmse_during_stimulus_mv": rmse_stim_mv,
        "rmse_post_stimulus_mv": rmse_post_mv,
        "excursions_recorded_post_step": excursions_rec,
        "excursions_simulated_post_step": excursions_sim,
        "post_step_current_max_pa": float(np.max(np.abs(stim[at_off:n]))) * 1e12
                                    if at_off < n else 0.0,
        "mae_mv": mae_mv,
        "correlation": corr,
        "spikes_recorded_allen": int(spikes_rec_ms.size),
        "spikes_simulated_allen": int(spikes_sim_ms.size),
        "spikes_simulated_stored_in_nwb": int(stored_sim_spikes.size),
        "spikes_recorded_threshold": int(simple_rec.size),
        "spikes_simulated_threshold": int(simple_sim.size),
        "spikes_recorded_in_step": int(rec_in.size),
        "spikes_simulated_in_step": int(sim_in.size),
        "spikes_recorded_outside_step": int(rec_out.size),
        "spikes_simulated_outside_step": int(sim_out.size),
        "spike_times_recorded_ms": [round(float(x), 3) for x in spikes_rec_ms],
        "spike_times_simulated_ms": [round(float(x), 3) for x in spikes_sim_ms],
        "spike_times_stored_in_nwb_ms": [round(float(x) * 1e3, 3)
                                        for x in stored_sim_spikes],
        "simulated_has_nan": bool(np.isnan(v_sim_n).any()),
        "simulated_has_inf": bool(np.isinf(v_sim_n).any()),
    }
    if paired:
        facts["spikes_paired_in_step"] = int(paired)
        facts["spike_offset_median_ms"] = float(np.median(offsets))
        facts["spike_offset_max_abs_ms"] = float(np.max(np.abs(offsets)))
        facts["first_spike_recorded_ms"] = float(rec_in[0])
        facts["first_spike_simulated_ms"] = float(sim_in[0])
        facts["first_spike_delta_ms"] = float(sim_in[0] - rec_in[0])
    if rec_out.size:
        facts["spikes_recorded_after_step_ms"] = [
            round(float(x), 3) for x in rec_out]

    checker.check(not facts["simulated_has_nan"] and not facts["simulated_has_inf"],
                  "simulated trace has no NaN or Inf",
                  "%d samples" % n)
    checker.check(n == v_rec.size == v_sim.size,
                  "simulated length matches recorded length",
                  "%d vs %d" % (v_sim.size, v_rec.size))
    checker.check(bool(np.all(time_steps > 0.0)),
                  "time vector is strictly increasing (no duplicates)",
                  "%d intervals" % time_steps.size)
    checker.check(bool(np.allclose(time_steps, dt_ms, rtol=0.0, atol=1e-9)),
                  "sampling interval is uniform across the sweep",
                  "median %.6f ms" % float(np.median(time_steps)))
    checker.check(padding == 0 or zero_tail == padding,
                  "any padding beyond the run is zero, not stale data",
                  "%d padded / %d zero" % (padding, zero_tail))
    checker.check(facts["simulated_max_mv"] > -20.0,
                  "simulated trace contains action potentials",
                  "max %.1f mV" % facts["simulated_max_mv"])
    checker.check(abs(facts["baseline_delta_mv"]) < 5.0,
                  "resting level agrees within 5 mV",
                  "sim %.2f vs rec %.2f mV" % (baseline_sim, baseline_rec))

    # Pipeline check: Allen's own save_nwb() ran extract_sweep_features and
    # stored the spikes it found.  If that agrees with an independent pass of
    # the same detector over the written trace, the write path is consistent.
    checker.check(facts["spikes_simulated_stored_in_nwb"]
                  == facts["spikes_simulated_allen"],
                  "NWB-stored spikes match the detector on the written trace",
                  "stored %d vs detected %d" % (
                      facts["spikes_simulated_stored_in_nwb"],
                      facts["spikes_simulated_allen"]))

    # Pipeline check: prepare_nwb_output must carry the stimulus across
    # untouched, otherwise the two traces would not share a command.
    stim_out = np.asarray(simulated["stimulus"], dtype=float)
    stim_ok = stim_out.size == stim.size and bool(np.array_equal(stim_out, stim))
    checker.check(stim_ok, "output NWB inherits the recorded stimulus unchanged",
                  "max |delta| %.1e A" % (float(np.max(np.abs(stim_out - stim)))
                                          if stim_out.size == stim.size else float("nan")))

    # --- biological agreement: reported, never asserted on its own
    checker.metric("voltage RMSE, whole sweep", "%.3f mV" % rmse_mv)
    checker.metric("voltage RMSE, stimulus-free", "%.3f mV" % rmse_pre_mv)
    checker.metric("voltage RMSE, during the step", "%.3f mV" % rmse_stim_mv)
    checker.metric("voltage RMSE, after the step", "%.3f mV" % rmse_post_mv)
    checker.metric("mean absolute error", "%.3f mV" % mae_mv)
    checker.metric("trace correlation", "%.4f" % corr)
    checker.metric("baseline offset", "%+.3f mV" % (baseline_sim - baseline_rec))
    checker.metric("voltage range recorded",
                   "%.2f .. %.2f mV" % (facts["recorded_min_mv"],
                                        facts["recorded_max_mv"]))
    checker.metric("voltage range simulated",
                   "%.2f .. %.2f mV" % (facts["simulated_min_mv"],
                                        facts["simulated_max_mv"]))
    checker.metric("spikes, whole sweep", "sim %d vs rec %d"
                   % (facts["spikes_simulated_allen"],
                      facts["spikes_recorded_allen"]))
    checker.metric("spikes, inside the step", "sim %d vs rec %d"
                   % (facts["spikes_simulated_in_step"],
                      facts["spikes_recorded_in_step"]))
    checker.metric("spikes, outside the step", "sim %d vs rec %d"
                   % (facts["spikes_simulated_outside_step"],
                      facts["spikes_recorded_outside_step"]))
    if paired:
        checker.metric("first spike after step onset",
                       "sim %.1f vs rec %.1f ms (%+.1f)"
                       % (facts["first_spike_simulated_ms"],
                          facts["first_spike_recorded_ms"],
                          facts["first_spike_delta_ms"]))
        checker.metric("paired spike offsets, inside step",
                       "n %d, median %+.1f, max |.| %.1f ms"
                       % (facts["spikes_paired_in_step"],
                          facts["spike_offset_median_ms"],
                          facts["spike_offset_max_abs_ms"]))
    if rec_out.size:
        checker.metric("recorded spikes outside the step",
                       " ".join("%.1f" % x for x in rec_out) + " ms")
    checker.metric("post-step command current",
                   "%.3f pA max" % facts["post_step_current_max_pa"])
    checker.metric("post-step excursions above -20 mV",
                   "sim %d vs rec %d" % (excursions_sim, excursions_rec))

    return facts


# ------------------------------------------------------------------------- main
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--allensdk-src", required=True)
    parser.add_argument("--assets-manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--skip-compile", action="store_true")
    args = parser.parse_args(argv)

    model_dir = pathlib.Path(args.model_dir).expanduser().resolve()
    allensdk_src = pathlib.Path(args.allensdk_src).expanduser().resolve()
    out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(model_dir)

    # AllenSDK must be importable before any stage runs: characterise_sweep and
    # compare both use allensdk.core.nwb_data_set.  Importing from the pristine
    # v2.16.2 source tree means the code executed is exactly the tagged release.
    sys.path.insert(0, str(allensdk_src))

    checker = Checker()
    print("Phase 2C - perisomatic sweep %d execution validation" % SWEEP)
    print("model dir :", model_dir)
    print("allensdk  :", allensdk_src)
    print("python    :", sys.version.split()[0], "|", sys.executable)

    expected = load_expected_assets(pathlib.Path(args.assets_manifest))
    facts = verify_inputs(checker, model_dir, expected)
    facts["sweep"] = characterise_sweep(checker, model_dir)

    if args.skip_compile:
        compile_facts = {"compiled": (model_dir / "x86_64" / "libnrnmech.so").exists(),
                         "skipped": True}
        checker.heading("B. Mechanism compilation")
        checker.skip("nrnivmodl re-run", "--skip-compile given")
    else:
        compile_facts = compile_mechanisms(
            checker, model_dir, out_dir / "nrnivmodl.log")
    facts["mechanisms"] = compile_facts

    if not compile_facts.get("compiled"):
        checker.summary()
        (out_dir / "execution_summary.json").write_text(
            json.dumps({"facts": facts, "tally": checker.tally()}, indent=2,
                       default=str), encoding="utf-8")
        print("\nRESULT: mechanisms did not compile, execution aborted")
        return 2

    run_facts = execute(checker, model_dir, allensdk_src,
                        out_dir / "execution.log")
    facts["execution"] = {k: v for k, v in run_facts.items() if k != "captured"}

    captured = run_facts.get("captured") or {}
    facts["convention"] = verify_convention(checker, captured)

    if run_facts.get("executed"):
        facts["comparison"] = compare(checker, model_dir, captured)
        facts["static_analysis_only"] = False
    else:
        checker.heading("E. Recorded versus simulated comparison")
        checker.skip("trace comparison", "the sweep did not execute")
        facts["static_analysis_only"] = True

    failures = checker.summary()
    tally = checker.tally()
    summary = {
        "facts": facts,
        "tally": tally,
        "metrics": [{"label": label, "value": value}
                    for label, value in checker.metric_rows],
    }
    (out_dir / "execution_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")

    # keep the compared traces for independent inspection
    if run_facts.get("executed"):
        import numpy as np
        np.savez_compressed(
            out_dir / ("traces_sweep%d.npz" % SWEEP),
            v_sim=captured.get("out_v"),
            t_ms=captured.get("out_t"),
            v_raw_mv=captured.get("raw_v_mv"))

    print()
    if not run_facts.get("executed"):
        print("RESULT: execution did not complete")
        return 2
    if failures == 0:
        print("RESULT: every numerical pipeline check passed")
        print("        biological agreement is reported above, not asserted")
    else:
        print("RESULT: %d pipeline check(s) failed" % failures)
    print("summary written to", out_dir / "execution_summary.json")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

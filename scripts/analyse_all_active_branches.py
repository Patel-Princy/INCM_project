"""Phase 2G-B: compare the two axon branches and the two recordings.

The executor produces four independent run directories.  This script reads them
back, checks that they really are four separate answers to four separate
questions, and quantifies how much the unpublished axon treatment changes the
prediction.

What the numbers mean
---------------------
Every run is a *reconstruction*:

    All-active model 497233292 using published parameters, substitute
    morphology 674389901, and project-declared axon treatment <branch>.

Nothing here selects a branch.  A branch that matches a recording better is not
thereby the branch Allen fitted, because the fitted geometry and the fitted axon
configuration are both unavailable.  The only branch-level statements this
script makes are about the size of the difference between them.

Usage
-----
    python scripts/analyse_all_active_branches.py \
        --results-root  ~/incm_phase2g_b/results \
        --repro-root    ~/incm_phase2g_b/repro \
        --figures-dir   <repo>/tmp/phase2g_b_figures \
        --out-dir       ~/incm_phase2g_b/results

Exit codes
----------
0  every consistency check passed and the summary was written
1  at least one run is missing, failed, or is inconsistent with the others
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import sys

import numpy as np

RATE_HZ = 200_000.0
DT_MS = 1e3 / RATE_HZ
STEP_ONSET_MS = 1020.0
STEP_DURATION_MS = 1000.0
COMMAND_PA = 170.0

ON_INDEX = int(round(STEP_ONSET_MS / DT_MS))
END_INDEX = int(round((STEP_ONSET_MS + STEP_DURATION_MS) / DT_MS))

RUN_DIRS = {
    "A": ("stub", 38),
    "B": ("stub", 49),
    "C": ("truncated", 38),
    "D": ("truncated", 49),
}
PAIRS = (("A", "C"), ("B", "D"))          # same sweep, different branch
REPEATS = (("A", "B"), ("C", "D"))        # same branch, different sweep


# --------------------------------------------------------------------- loading
def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_run(results_root: pathlib.Path, run_id: str, pattern: str | None = None) -> dict:
    """Load one run directory: its summary, its trace, and its identity."""
    branch, sweep = RUN_DIRS[run_id]
    if pattern is None:
        # Directory names are written as <run-id>_<branch>_sweep<sweep>.
        matches = sorted(results_root.glob("*_%s_sweep%d" % (branch, sweep)))
    else:
        matches = sorted(results_root.glob(pattern))
    if not matches:
        raise FileNotFoundError("no directory for run %s (%s, sweep %d) under %s"
                                % (run_id, branch, sweep, results_root))
    directory = matches[0]
    summary_path = directory / "run_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError("%s has no run_summary.json" % directory)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    trace_path = next(directory.glob("traces_*.npz"), None)
    trace = np.load(trace_path) if trace_path is not None else None
    return {
        "run_id": run_id,
        "axon_type": branch,
        "sweep": sweep,
        "dir": directory,
        "summary": summary,
        "trace_path": trace_path,
        "raw_v_mv": None if trace is None else np.asarray(trace["raw_v_mv"]),
        "written_v_mv": None if trace is None else np.asarray(trace["written_v_mv"]),
        "trace_sha256": sha256_of(trace_path) if trace_path else None,
    }


# ----------------------------------------------------------------- trace facts
def trace_facts(v_mv: np.ndarray, label: str = "") -> dict:
    """Baseline, plateau and response amplitude, measured the same way each time.

    ``settled_baseline`` is the mean of the last 100 ms before the step, not the
    mean of the whole lead-in: the model starts at ``v_init`` = -90 mV and the
    first 20 ms of every trace is the approach from there.
    """
    tail = v_mv[max(0, ON_INDEX - int(round(100.0 / DT_MS))):ON_INDEX]
    plateau_window = v_mv[max(0, END_INDEX - int(round(200.0 / DT_MS))):END_INDEX]
    step = v_mv[ON_INDEX:min(END_INDEX, v_mv.size)]
    recent = int(round(20.0 / DT_MS))
    before = v_mv[max(0, ON_INDEX - recent):ON_INDEX]
    baseline = float(np.mean(tail))
    plateau = float(np.median(plateau_window))
    response = plateau - baseline
    return {
        "label": label,
        "n_samples": int(v_mv.size),
        "settled_baseline_mv": baseline,
        "drift_last_20ms_mv": float(before[-1] - before[0]) if before.size > 1
        else float("nan"),
        "plateau_mv": plateau,
        "step_peak_mv": float(np.max(step)) if step.size else float("nan"),
        "step_trough_mv": float(np.min(step)) if step.size else float("nan"),
        "response_mv": response,
        # 1 mV / 1 pA = 1000 MOhm, so the quotient of the two raw numbers is
        # in GOhm and has to be scaled to get megohms.
        "input_resistance_mohm": (abs(response) / COMMAND_PA * 1e3
                                  if COMMAND_PA else float("nan")),
        "max_dvdt_v_per_s": (float(np.max(np.diff(step))) / DT_MS
                             if step.size > 1 else float("nan")),
        "post_step_min_mv": (float(np.min(v_mv[END_INDEX:END_INDEX
                                                + int(round(480.0 / DT_MS))]))
                             if END_INDEX < v_mv.size else float("nan")),
    }


def branch_difference(v_first: np.ndarray, v_second: np.ndarray,
                      first_label: str, second_label: str) -> dict:
    """How far apart two branches are, over their common window.

    The whole-trace and in-step numbers are reported separately: a difference
    that lives entirely in the first 20 ms of initialisation is not a
    difference in the modelled response.
    """
    n = min(v_first.size, v_second.size)
    if n <= END_INDEX:
        raise ValueError("traces are too short to contain the step")
    diff = v_first[:n] - v_second[:n]
    in_step = diff[ON_INDEX:END_INDEX]
    pre = diff[:ON_INDEX]
    return {
        "first": first_label,
        "second": second_label,
        "n_compared": int(n),
        "rms_difference_mv": float(np.sqrt(np.mean(diff ** 2))),
        "max_abs_difference_mv": float(np.max(np.abs(diff))),
        "rms_difference_pre_step_mv": float(np.sqrt(np.mean(pre ** 2))),
        "max_abs_difference_pre_step_mv": float(np.max(np.abs(pre))),
        "rms_difference_in_step_mv": float(np.sqrt(np.mean(in_step ** 2))),
        "max_abs_difference_in_step_mv": float(np.max(np.abs(in_step))),
        "mean_difference_in_step_mv": float(np.mean(in_step)),
        "samples_above_1mv_in_step": int(np.count_nonzero(
            np.abs(in_step) >= 1.0)),
    }


def traces_identical_except_length(a: np.ndarray, b: np.ndarray) -> dict:
    """Do two traces agree sample for sample over their common window?"""
    n = min(a.size, b.size)
    diff = np.abs(a[:n] - b[:n])
    return {
        "n_compared": int(n),
        "max_abs_difference_mv": float(np.max(diff)) if n else float("nan"),
        "identical": bool(n and float(np.max(diff)) == 0.0),
    }


# ------------------------------------------------------------------- summaries
def recording_row(run: dict) -> dict:
    """One row of the recording-versus-model table."""
    facts = run["summary"]["facts"]
    comparison = facts.get("comparison") or {}
    rec = comparison.get("recorded", {})
    sim = comparison.get("simulated", {})
    pair = comparison.get("pair", {})
    settle = comparison.get("settling", {})
    return {
        "run": run["run_id"],
        "axon_type": run["axon_type"],
        "sweep": run["sweep"],
        "status": run["summary"].get("status"),
        "recorded_spikes_in_step": rec.get("n_in_step"),
        "simulated_spikes_in_step": sim.get("n_in_step"),
        "recorded_first_latency_ms": rec.get("first_in_step_latency_ms"),
        "simulated_first_latency_ms": sim.get("first_in_step_latency_ms"),
        "recorded_mean_isi_ms": rec.get("mean_isi_ms"),
        "simulated_mean_isi_ms": sim.get("mean_isi_ms"),
        "recorded_amplitude_mv": rec.get("spike_amplitude_mv", {}).get("median"),
        "simulated_amplitude_mv": sim.get("spike_amplitude_mv", {}).get("median"),
        "recorded_width_ms": rec.get("spike_width_ms", {}).get("median"),
        "simulated_width_ms": sim.get("spike_width_ms", {}).get("median"),
        "recorded_ahp_mv": rec.get("ahp_mv", {}).get("median"),
        "simulated_ahp_mv": sim.get("ahp_mv", {}).get("median"),
        "recorded_plateau_mv": rec.get("plateau_mv"),
        "simulated_plateau_mv": sim.get("plateau_mv"),
        "recorded_settled_baseline_mv": settle.get("recorded", {}).get(
            "settled_baseline_mv"),
        "simulated_settled_baseline_mv": settle.get("simulated", {}).get(
            "settled_baseline_mv"),
        "rmse_whole_mv": pair.get("rmse_whole_mv"),
        "rmse_in_step_mv": pair.get("rmse_in_step_mv"),
        "rmse_away_from_spikes_mv": pair.get("rmse_in_step_away_from_spikes_mv"),
        "share_of_error_near_spikes": pair.get("share_of_in_step_error_near_spikes"),
        "corr_whole": pair.get("corr_whole"),
        "corr_in_step": pair.get("corr_in_step"),
        "spike_count_delta": pair.get("spike_count_delta"),
        "rmse_around_recorded_first_spike_mv": pair.get(
            "rmse_around_recorded_first_spike_mv"),
        "simulated_minus_recorded_peak_mv": pair.get(
            "simulated_minus_recorded_peak_mv"),
    }


def perisomatic_reference(phase2c: pathlib.Path, phase2e: pathlib.Path) -> dict:
    """The perisomatic numbers this phase is allowed to be compared against.

    Sweep 38 was the perisomatic model's *fitting* sweep, so the sweep 38 entry
    is in-sample for that model even though it is out-of-sample for the
    all-active one.  Sweep 49 is the only genuinely comparable condition.
    """
    reference: dict = {"available": False, "sweep38": None, "sweep49": None}
    if phase2c.exists():
        data = json.loads(phase2c.read_text(encoding="utf-8"))
        facts = data.get("facts", {})
        comparison = facts.get("comparison", {})
        reference["sweep38"] = {
            "model": "perisomatic 473862496",
            "relation": "in-sample: this was the perisomatic model's fitting sweep",
            "rmse_whole_mv": comparison.get("rmse_mv"),
            "rmse_in_step_mv": comparison.get("rmse_during_stimulus_mv"),
            "corr_whole": comparison.get("correlation"),
            "spikes_recorded_in_step": comparison.get("spikes_recorded_in_step"),
            "spikes_simulated_in_step": comparison.get("spikes_simulated_in_step"),
            "first_spike_delta_ms": comparison.get("first_spike_delta_ms"),
            "source": str(phase2c),
        }
        reference["available"] = True
    if phase2e.exists():
        data = json.loads(phase2e.read_text(encoding="utf-8"))
        rows = data.get("sweeps", [])
        for row in rows:
            if int(row.get("sweep", -1)) != 49:
                continue
            rec, sim, pair = row["recorded"], row["simulated"], row["pair"]
            reference["sweep49"] = {
                "model": "perisomatic 473862496",
                "relation": "held out: not used to fit either model",
                "rmse_whole_mv": pair.get("rmse_whole_mv"),
                "rmse_in_step_mv": pair.get("rmse_in_step_mv"),
                "corr_whole": pair.get("corr_whole"),
                "spikes_recorded_in_step": rec.get("n_in_step"),
                "spikes_simulated_in_step": sim.get("n_in_step"),
                "first_latency_recorded_ms": rec.get("first_in_step_latency_ms"),
                "first_latency_simulated_ms": sim.get("first_in_step_latency_ms"),
                "source": str(phase2e),
            }
            reference["available"] = True
    return reference


# ------------------------------------------------------------------ consistency
def verify_runs(runs: dict, repro: dict | None) -> dict:
    """Checks on the quartet: four runs, four outputs, one input set."""
    rows = []

    def check(ok, label, detail=""):
        rows.append({"label": label, "ok": bool(ok), "detail": detail})
        return ok

    check(all(run["summary"].get("status") == "success" for run in runs.values()),
          "all four runs report success",
          ", ".join("%s=%s" % (key, run["summary"].get("status"))
                    for key, run in sorted(runs.items())))
    check(all(run["trace_path"] is not None for run in runs.values()),
          "all four runs wrote a trace")

    inputs = {key: run["summary"]["facts"]["hashes"]["inputs"]
              for key, run in runs.items()}
    first = inputs["A"]
    check(all(value == first for value in inputs.values()),
          "all four runs consumed byte-identical inputs",
          "%d files per run" % len(first))
    libraries = {key: run["summary"]["facts"]["hashes"].get(
        "mechanism_library_sha256") for key, run in runs.items()}
    check(len(set(libraries.values())) == 1 and None not in libraries.values(),
          "all four runs loaded the same compiled mechanism library",
          str(sorted(set(libraries.values()))[0])[:16] + "...")

    outputs = {key: run["summary"]["facts"]["hashes"]["output_nwb_sha256"]
               for key, run in runs.items()}
    check(len(set(outputs.values())) == 4,
          "the four output NWB files are four distinct artefacts",
          ", ".join("%s:%s" % (key, (value or "")[:8])
                    for key, value in sorted(outputs.items())))

    # A branch that made no difference would make the whole comparison vacuous.
    for first_id, second_id in PAIRS:
        a, b = runs[first_id], runs[second_id]
        if a["raw_v_mv"] is None or b["raw_v_mv"] is None:
            check(False, "branch pair %s/%s is loadable" % (first_id, second_id))
            continue
        difference = branch_difference(a["raw_v_mv"], b["raw_v_mv"],
                                       a["axon_type"], b["axon_type"])
        check(difference["rms_difference_in_step_mv"] > 0.0,
              "%s and %s differ inside the step"
              % (first_id, second_id),
              "rms %.4f mV" % difference["rms_difference_in_step_mv"])

    # The two sweeps deliver the same command, so a deterministic model must
    # return the same response; only the recorded traces differ.
    for first_id, second_id in REPEATS:
        a, b = runs[first_id], runs[second_id]
        if a["raw_v_mv"] is None or b["raw_v_mv"] is None:
            continue
        same = traces_identical_except_length(a["raw_v_mv"], b["raw_v_mv"])
        check(same["identical"],
              "%s and %s return the same response to the same command"
              % (first_id, second_id),
              "max |delta| = %.3e mV over %d samples"
              % (same["max_abs_difference_mv"], same["n_compared"]))

    determinism = None
    if repro is not None:
        determinism = traces_identical_except_length(runs["A"]["raw_v_mv"],
                                                     repro["raw_v_mv"])
        determinism["replicate_output_sha256"] = repro["summary"]["facts"][
            "hashes"]["output_nwb_sha256"]
        determinism["original_output_sha256"] = runs["A"]["summary"]["facts"][
            "hashes"]["output_nwb_sha256"]
        determinism["output_digest_matches"] = (
            determinism["replicate_output_sha256"]
            == determinism["original_output_sha256"])
        check(determinism["identical"] and determinism["output_digest_matches"],
              "a second process reproduces run A exactly",
              "trace delta %.3e mV, NWB digest %s"
              % (determinism["max_abs_difference_mv"],
                 "equal" if determinism["output_digest_matches"] else "differs"))

    return {
        "checks": rows,
        "passed": sum(1 for row in rows if row["ok"]),
        "failed": sum(1 for row in rows if not row["ok"]),
        "determinism": determinism,
        "input_sha256": first,
        "mechanism_library_sha256": libraries["A"],
        "output_sha256": outputs,
    }


# --------------------------------------------------------------------- figures
def make_figures(runs: dict, rows: list, differences: dict, branch_table: list,
                 figures_dir: pathlib.Path, stimulus_nwb: pathlib.Path,
                 allensdk_src: pathlib.Path) -> list:
    """Five figures.  No figure ever plots a pooled or averaged branch."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # AllenSDK is used from the cached v2.16.2 source tree, never installed.
    if str(allensdk_src) not in sys.path:
        sys.path.insert(0, str(allensdk_src))
    from allensdk.core.nwb_data_set import NwbDataSet

    figures_dir.mkdir(parents=True, exist_ok=True)
    written = []

    def recorded(sweep):
        data = NwbDataSet(str(stimulus_nwb)).get_sweep(sweep)
        v = np.asarray(data["response"], dtype=float) * 1e3
        t = np.arange(v.size) * DT_MS
        return t, v

    def simulated(run):
        v = run["written_v_mv"]
        t = np.arange(v.size) * DT_MS
        return t, v

    colours = {"stub": "#1b6ca8", "truncated": "#b3491f"}

    def spikes(run):
        return run["summary"]["facts"]["comparison"]["simulated"]["n_in_step"]

    # --- 1 and 2: one per stimulus, recorded plus each branch separately
    for sweep, first_id, second_id, title in (
            (38, "A", "C", "sweep 38, COARSE +170 pA (plausibility bracket)"),
            (49, "B", "D", "sweep 49, FINEST +170 pA (held-out test)")):
        figure, axes = plt.subplots(2, 1, figsize=(11, 7))
        t_rec, v_rec = recorded(sweep)
        step = 30
        axes[0].plot(t_rec[::step], v_rec[::step], color="black", lw=0.8,
                     label="recorded, sweep %d (%d spikes in step)"
                           % (sweep, rows[sweep]["recorded_spikes_in_step"]))
        for run_id in (first_id, second_id):
            run = runs[run_id]
            t_sim, v_sim = simulated(run)
            axes[0].plot(t_sim[::step], v_sim[::step], lw=0.8,
                         color=colours[run["axon_type"]],
                         label="axon treatment %s, sweep %d (%d spikes in step)"
                               % (run["axon_type"], sweep, spikes(run)))
        axes[0].set_ylabel("V (mV)")
        axes[0].set_title(title)
        axes[0].legend(loc="upper right", fontsize=8)
        axes[0].axvspan(STEP_ONSET_MS, STEP_ONSET_MS + STEP_DURATION_MS,
                        color="0.9", zorder=0)

        zoom = slice(int(1000.0 / DT_MS), int(1250.0 / DT_MS))
        axes[1].plot(t_rec[zoom], v_rec[zoom], color="black", lw=1.0,
                     label="recorded, sweep %d" % sweep)
        for run_id in (first_id, second_id):
            run = runs[run_id]
            t_sim, v_sim = simulated(run)
            axes[1].plot(t_sim[zoom], v_sim[zoom], lw=1.0,
                         color=colours[run["axon_type"]],
                         label="axon treatment %s, sweep %d"
                               % (run["axon_type"], sweep))
        axes[1].set_xlabel("time (ms)")
        axes[1].set_ylabel("V (mV)")
        axes[1].set_xlim(1000.0, 1250.0)
        axes[1].set_title("sweep %d, first 250 ms of the step" % sweep)
        axes[1].legend(loc="lower right", fontsize=8)
        name = figures_dir / ("fig%d_sweep%d_recorded_and_branches.png"
                              % (1 if sweep == 38 else 2, sweep))
        figure.tight_layout()
        figure.savefig(name, dpi=130)
        plt.close(figure)
        written.append(str(name))

    # --- 3: branch-to-branch difference, one panel per stimulus
    figure, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    for axis, (first_id, second_id) in zip(axes, PAIRS):
        a, b = runs[first_id], runs[second_id]
        n = min(a["raw_v_mv"].size, b["raw_v_mv"].size)
        diff = a["raw_v_mv"][:n] - b["raw_v_mv"][:n]
        t = np.arange(n) * DT_MS
        axis.plot(t[::20], diff[::20], color="#4b2e83", lw=0.9)
        axis.axhline(0.0, color="0.6", lw=0.6)
        axis.axvspan(STEP_ONSET_MS, STEP_ONSET_MS + STEP_DURATION_MS,
                     color="0.9", zorder=0)
        key = "%s_vs_%s" % (first_id, second_id)
        detail = differences[key]
        axis.set_ylabel("V_stub - V_truncated (mV)")
        axis.set_title("sweep %d: rms %.3f mV, max %.3f mV in step"
                       % (a["sweep"], detail["rms_difference_in_step_mv"],
                          detail["max_abs_difference_in_step_mv"]))
    axes[-1].set_xlabel("time (ms)")
    name = figures_dir / "fig3_branch_difference.png"
    figure.tight_layout()
    figure.savefig(name, dpi=130)
    plt.close(figure)
    written.append(str(name))

    # --- 4: the observed spike in sweep 49, against both branches
    figure, axis = plt.subplots(figsize=(9, 4.5))
    t_rec, v_rec = recorded(49)
    lo, hi = int(1100.0 / DT_MS), int(1160.0 / DT_MS)
    axis.plot(t_rec[lo:hi], v_rec[lo:hi], color="black", lw=1.4,
              label="recorded spike, sweep 49")
    for run_id in ("B", "D"):
        run = runs[run_id]
        t_sim, v_sim = simulated(run)
        axis.plot(t_sim[lo:hi], v_sim[lo:hi], lw=1.2,
                  color=colours[run["axon_type"]],
                  label="%s axon at the same time" % run["axon_type"])
    axis.set_xlabel("time (ms)")
    axis.set_ylabel("V (mV)")
    axis.set_title("sweep 49 around the single observed spike "
                   "(stub: %d spikes, truncated: %d spikes)"
                   % (spikes(runs["B"]), spikes(runs["D"])))
    axis.legend(loc="upper left", fontsize=8)
    name = figures_dir / "fig4_sweep49_spike_window.png"
    figure.tight_layout()
    figure.savefig(name, dpi=130)
    plt.close(figure)
    written.append(str(name))

    # --- 5: compact metric comparison.  Four separate panels, because the
    # metrics have different units; within each panel the four runs stay
    # individual bars and are never averaged.
    panels = (("rmse_in_step_mv", "RMSE in step (mV)"),
              ("response_mv", "step response (mV)"),
              ("settled_baseline_mv", "settled baseline (mV)"),
              ("input_resistance_mohm", "input resistance (MOhm)"))
    figure, axes = plt.subplots(2, 2, figsize=(11, 7))
    for axis, (key, label) in zip(axes.ravel(), panels):
        positions = np.arange(len(branch_table))
        values = [entry[key] for entry in branch_table]
        bars = axis.bar(positions, values, width=0.65,
                        color=[colours[entry["axon_type"]]
                               for entry in branch_table])
        axis.set_xticks(positions)
        axis.set_xticklabels(["%s\nsweep %d" % (entry["axon_type"], entry["sweep"])
                              for entry in branch_table], fontsize=7)
        axis.set_ylabel(label, fontsize=8)
        axis.grid(axis="y", alpha=0.3)
        for bar, value in zip(bars, values):
            axis.annotate("%.2f" % value,
                          (bar.get_x() + bar.get_width() / 2.0, value),
                          textcoords="offset points", xytext=(0, 2),
                          ha="center", fontsize=6)
    figure.suptitle("sweep 38 and sweep 49, stub and truncated: four separate "
                    "reconstructions, never pooled", fontsize=9)
    name = figures_dir / "fig5_metric_comparison.png"
    figure.tight_layout()
    figure.savefig(name, dpi=130)
    plt.close(figure)
    written.append(str(name))

    return written


# ------------------------------------------------------------------------ main
def build_summary(runs: dict, repro: dict | None, phase2c: pathlib.Path,
                  phase2e: pathlib.Path, stimulus_nwb: pathlib.Path) -> dict:
    recording_table = [recording_row(runs[run_id])
                       for run_id in ("A", "B", "C", "D")]

    differences = {}
    for first_id, second_id in PAIRS:
        a, b = runs[first_id], runs[second_id]
        key = "%s_vs_%s" % (first_id, second_id)
        differences[key] = branch_difference(
            a["raw_v_mv"], b["raw_v_mv"], a["axon_type"], b["axon_type"])
        differences[key]["sweep"] = a["sweep"]

    branch_table = []
    for run_id in ("A", "B", "C", "D"):
        run = runs[run_id]
        facts = trace_facts(run["raw_v_mv"], "%s %s" % (run["axon_type"],
                                                       run["sweep"]))
        facts["axon_type"] = run["axon_type"]
        facts["sweep"] = run["sweep"]
        facts["run"] = run_id
        facts["simulated_spikes_in_step"] = run["summary"]["facts"][
            "comparison"]["simulated"]["n_in_step"]
        facts["rmse_in_step_mv"] = run["summary"]["facts"]["comparison"][
            "pair"]["rmse_in_step_mv"]
        facts["corr_in_step"] = run["summary"]["facts"]["comparison"][
            "pair"]["corr_in_step"]
        branch_table.append(facts)

    return {
        "phase": "2G-B",
        "model_claim": runs["A"]["summary"]["facts"]["model_claim"],
        "recording_table": recording_table,
        "branch_table": branch_table,
        "branch_differences": differences,
        "consistency": verify_runs(runs, repro),
        "perisomatic_reference": perisomatic_reference(phase2c, phase2e),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results-root", required=True)
    parser.add_argument("--repro-root", default="")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--figures-dir", default="")
    parser.add_argument("--stimulus-nwb", default="")
    parser.add_argument("--allensdk-src", default="")
    parser.add_argument("--phase2c-summary", default="~/incm_phase2c/results/execution_summary.json")
    parser.add_argument("--phase2e-summary", default="~/incm_phase2e/results/phase2e_summary.json")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)

    results_root = pathlib.Path(args.results_root).expanduser().resolve()
    out_dir = pathlib.Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = {run_id: load_run(results_root, run_id) for run_id in RUN_DIRS}
    repro = None
    if args.repro_root:
        repro_root = pathlib.Path(args.repro_root).expanduser().resolve()
        try:
            # The replicate lives in its own sub-directory with its own name.
            repro = load_run(repro_root, "A", pattern="**/*_stub_sweep38")
        except FileNotFoundError:
            repro = None

    phase2c = pathlib.Path(args.phase2c_summary).expanduser()
    phase2e = pathlib.Path(args.phase2e_summary).expanduser()
    stimulus_nwb = (pathlib.Path(args.stimulus_nwb).expanduser()
                    if args.stimulus_nwb else
                    pathlib.Path(results_root).parent / "model" / "382982932.nwb")
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    allensdk_src = (pathlib.Path(args.allensdk_src).expanduser()
                    if args.allensdk_src else
                    repo_root / "tmp" / "model_cache" / "2b" / "src"
                    / "AllenSDK-2.16.2")
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

    summary = build_summary(runs, repro, phase2c, phase2e, stimulus_nwb)

    print("Phase 2G-B branch analysis")
    print("model: %s" % summary["model_claim"])
    print()
    for row in summary["consistency"]["checks"]:
        print("  [%s] %s  -- %s" % ("PASS" if row["ok"] else "FAIL",
                                    row["label"], row["detail"]))

    print()
    print("recording comparison")
    print("  %-3s %-10s %5s %8s %9s %9s %8s %8s"
          % ("run", "axon", "sweep", "rec/sim", "rmse_in", "rmse_all", "corr", "dBase"))
    for row in summary["recording_table"]:
        print("  %-3s %-10s %5d %8s %9.3f %9.3f %8.4f %8.3f"
              % (row["run"], row["axon_type"], row["sweep"],
                 "%d/%d" % (row["recorded_spikes_in_step"],
                            row["simulated_spikes_in_step"]),
                 row["rmse_in_step_mv"], row["rmse_whole_mv"],
                 row["corr_whole"],
                 row["simulated_settled_baseline_mv"]
                 - row["recorded_settled_baseline_mv"]))

    print()
    print("branch table")
    print("  %-3s %-10s %5s %10s %10s %9s %9s"
          % ("run", "axon", "sweep", "baseline", "plateau", "response", "Rin"))
    for row in summary["branch_table"]:
        print("  %-3s %-10s %5d %10.3f %10.3f %9.3f %9.1f"
              % (row["run"], row["axon_type"], row["sweep"],
                 row["settled_baseline_mv"], row["plateau_mv"],
                 row["response_mv"], row["input_resistance_mohm"]))

    print()
    for key, value in summary["branch_differences"].items():
        print("  %s: rms in step %.4f mV, max in step %.4f mV, "
              "rms whole %.4f mV" % (key, value["rms_difference_in_step_mv"],
                                     value["max_abs_difference_in_step_mv"],
                                     value["rms_difference_mv"]))

    reference = summary["perisomatic_reference"]
    if reference["available"]:
        print()
        print("perisomatic reference")
        for key in ("sweep38", "sweep49"):
            entry = reference[key]
            if not entry:
                continue
            print("  %s: %s | rmse %.3f mV whole, %.3f mV in step | spikes %s/%s"
                  % (key, entry["relation"], entry["rmse_whole_mv"],
                     entry["rmse_in_step_mv"], entry["spikes_recorded_in_step"],
                     entry["spikes_simulated_in_step"]))

    if not args.no_figures and args.figures_dir:
        figures = make_figures(runs, {38: summary["recording_table"][0],
                                      49: summary["recording_table"][1]},
                               summary["branch_differences"],
                               summary["branch_table"],
                               pathlib.Path(args.figures_dir).expanduser(),
                               stimulus_nwb, allensdk_src)
        summary["figures"] = figures
        print()
        for path in figures:
            print("  figure:", path)

    summary["figure_dir"] = args.figures_dir or None
    payload = json.loads(json.dumps(summary, default=_json_default))
    (out_dir / "phase2g_b_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    print()
    print("summary written to", out_dir / "phase2g_b_summary.json")
    return 0 if summary["consistency"]["failed"] == 0 else 1


def _json_default(value):
    if isinstance(value, (np.floating, float)):
        return None if value != value else float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, pathlib.Path):
        return str(value)
    return str(value)


if __name__ == "__main__":
    sys.exit(main())
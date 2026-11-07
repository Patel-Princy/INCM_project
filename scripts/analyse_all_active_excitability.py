"""Phase 2G-C: descriptive excitability and rheobase mapping of both all-active
reconstructions.

The executor has measured model 497233292 (published parameters, substitute
morphology 674389901) under both declared axon treatments at every depolarizing
amplitude of the validated COARSE long-square block, plus the -110 pA control.
This script reads the 28 run directories back, checks that they really are 28
separate answers, and derives the excitability description.

What the numbers mean
---------------------
Every run is a *reconstruction*:

    All-active model 497233292 using published parameters, substitute
    morphology 674389901, and project-declared axon treatment <branch>.

Nothing here selects a branch, fits a parameter, or extrapolates a rheobase
beyond the tested amplitudes.  The rheobase of a reconstruction is reported as
an interval bounded by tested amplitudes, or as an explicit bound ("above the
tested range") when no tested amplitude elicits a spike.  Model-only results
are kept structurally separate from the recorded neuron's response: the
recording columns are derived from the same run summaries but never enter the
excitability tables.

Usage
-----
    python scripts/analyse_all_active_excitability.py \
        --results-root  ~/incm_phase2gc/results \
        --baseline-root ~/incm_phase2g_b/results \
        --figures-dir   <repo>/tmp/phase2g_c_figures \
        --out-dir       ~/incm_phase2gc/results

Exit codes
----------
0  every consistency check passed and the summary was written
1  at least one run is missing, failed, or is inconsistent with the others
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np

RATE_HZ = 200_000.0
DT_MS = 1e3 / RATE_HZ

#: The frozen measurement plan: one label per COARSE condition, in execution
#: order.  Sweep 41 (+230 pA) fitted the model and is excluded by construction.
CONDITIONS = (
    ("M01", 24, -110.0, "coarse_n110"),
    ("M02", 30, 10.0, "coarse_p010"),
    ("M03", 31, 30.0, "coarse_p030"),
    ("M04", 32, 50.0, "coarse_p050"),
    ("M05", 33, 70.0, "coarse_p070"),
    ("M06", 34, 90.0, "coarse_p090"),
    ("M07", 35, 110.0, "coarse_p110"),
    ("M08", 36, 130.0, "coarse_p130"),
    ("M09", 37, 150.0, "coarse_p150"),
    ("M10", 38, 170.0, "coarse_p170"),
    ("M11", 39, 190.0, "coarse_p190"),
    ("M12", 40, 210.0, "coarse_p210"),
    ("M13", 42, 250.0, "coarse_p250"),
    ("M14", 43, 270.0, "coarse_p270"),
)
CONDITIONS_BY_SWEEP = {sweep: (rid, level, label) for rid, sweep, level, label
                       in CONDITIONS}
BRANCHES = ("stub", "truncated")
FITTING_SWEEP = 41
COARSE_BLOCK = "C1LSCOARSE150216"

#: Amplitudes at or below this magnitude are treated as the ohmic region for
#: the slope-based input resistance; above it the active conductances bend the
#: I-V relation and the slope stops being a resistance.  The DAC writes levels
#: like 110.000002 pA, so the boundary is compared with a small tolerance --
#: a strict comparison would silently drop the +/-110 pA points and report an
#: ohmic region that is not the one documented.
OHMIC_LIMIT_PA = 110.0
OHMIC_LIMIT_TOLERANCE_PA = 0.01


# --------------------------------------------------------------------- loading
def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_run(results_root: pathlib.Path, run_id: str, branch: str,
             sweep: int) -> dict:
    """Load one run directory: its summary, its trace, and its identity."""
    # Directory names are written as <run-id>_<branch>_sweep<sweep>.
    matches = sorted(results_root.glob("%s_%s_sweep%d" % (run_id, branch, sweep)))
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
        "trace_sha256": sha256_of(trace_path) if trace_path else None,
    }


def load_all_runs(results_root: pathlib.Path) -> dict:
    return {branch: [load_run(results_root, run_id, branch, sweep)
                     for run_id, sweep, _level, _label in CONDITIONS]
            for branch in BRANCHES}


# ---------------------------------------------------------------- excitable row
def input_resistance_mohm(response_mv: float, current_pa: float) -> float:
    """Apparent input resistance at one amplitude.

    1 mV / 1 pA = 1000 MOhm, so the quotient of the two raw numbers is in
    GOhm and has to be scaled by 1e3 to become megohms.  The sign convention:
    a passive membrane gives response and current of equal sign, hence a
    positive resistance; a negative value would report rectification, not a
    resistance.
    """
    if current_pa == 0.0:
        return float("nan")
    return response_mv / current_pa * 1e3


def mean_rate_hz(n_spikes: int, step_duration_ms: float) -> float:
    """Mean in-step firing rate: spikes divided by the step duration."""
    if step_duration_ms <= 0.0:
        return float("nan")
    return n_spikes / (step_duration_ms / 1e3)


def excitability_row(run: dict) -> dict:
    """One row of the per-branch excitability table, from the run summary.

    Every value comes from the executor's recorded facts (Phase 2E metric
    conventions); nothing is recomputed from the trace here, so the table
    cannot drift away from the checked numbers.
    """
    facts = run["summary"]["facts"]
    comparison = facts["comparison"]
    sim = comparison["simulated"]
    stimulus = comparison["stimulus"]
    settle = comparison["settling"]["simulated"]
    level_pa = float(stimulus["level_pa"])
    n_in_step = int(sim["n_in_step"])
    step_duration_ms = float(sim["step_duration_ms"])
    baseline = float(settle["settled_baseline_mv"])
    plateau = float(sim["plateau_mv"])
    response = plateau - baseline
    isis = [b - a for a, b in zip(sim["spike_times_in_step_ms"][:-1],
                                  sim["spike_times_in_step_ms"][1:])]
    return {
        "run_id": run["run_id"],
        "condition": facts.get("condition"),
        "sweep": int(facts["sweep"]),
        "block": str(stimulus["block"]),
        "level_pa": level_pa,
        "level_matches": bool(stimulus["level_matches"]),
        "spikes_in_step": n_in_step,
        "spikes_allen": int(sim["n_spikes_allen"]),
        "first_latency_ms": (float(sim["first_in_step_latency_ms"])
                             if n_in_step else None),
        "mean_rate_hz": mean_rate_hz(n_in_step, step_duration_ms),
        "isis_ms": [round(x, 3) for x in isis],
        "mean_isi_ms": float(np.mean(isis)) if len(isis) > 1 else None,
        "settled_baseline_mv": baseline,
        "settles_before_step": bool(abs(settle["drift_last_20ms_mv"]) <= 1.0),
        "drift_last_20ms_mv": float(settle["drift_last_20ms_mv"]),
        "plateau_mv": plateau,
        "response_mv": round(response, 4),
        "input_resistance_mohm": round(input_resistance_mohm(response, level_pa), 3),
        "v_max_mv": float(sim["v_max_mv"]),
        "excitability_margin_mv": float(sim["v_max_mv"]) - baseline,
        "recorded_spikes_in_step": int(comparison["recorded"]["n_in_step"]),
    }


def branch_rows(runs: list[dict], branch: str) -> list[dict]:
    """Excitability rows for one branch, refusing any pooling of branches.

    The executor runs each branch in its own process with its own outputs; if a
    run of the other branch reaches this function the caller is trying to pool
    them, which the brief forbids and this function prevents.
    """
    rows = []
    for run in runs:
        if run["axon_type"] != branch:
            raise ValueError("run %s is a %s run; the %s excitability table "
                             "must contain only %s runs"
                             % (run["run_id"], run["axon_type"], branch, branch))
        rows.append(excitability_row(run))
    rows.sort(key=lambda r: r["level_pa"])
    return rows


# ------------------------------------------------------------------- rheobase
def rheobase_interval(rows: list[dict]) -> dict:
    """Rheobase as an interval bounded by tested amplitudes, never a guess.

    Only depolarizing amplitudes participate: a hyperpolarizing step cannot
    bound rheobase from above.  The interval is [highest silent amplitude
    below the first spike, lowest spiking amplitude]; a silent range has no
    upper bound inside the tested set and is reported as such.
    """
    depolarizing = sorted((r for r in rows if r["level_pa"] > 0.0),
                          key=lambda r: r["level_pa"])
    if not depolarizing:
        return {"kind": "none_tested",
                "statement": "no depolarizing amplitude was tested"}
    levels = [r["level_pa"] for r in depolarizing]
    spiked = [bool(r["spikes_in_step"]) for r in depolarizing]
    if not any(spiked):
        return {
            "kind": "above_range",
            "highest_tested_pa": levels[-1],
            "statement": ("no tested amplitude elicited a spike; the rheobase "
                          "is above the highest tested amplitude (%.0f pA)"
                          % levels[-1]),
        }
    if all(spiked):
        return {
            "kind": "below_range",
            "lowest_tested_pa": levels[0],
            "statement": ("every tested amplitude elicited a spike; the "
                          "rheobase is at or below the lowest tested "
                          "amplitude (%.0f pA)" % levels[0]),
        }
    first = spiked.index(True)
    lower = levels[first - 1] if first > 0 else None
    upper = levels[first]
    return {
        "kind": "interval",
        "lower_pa": lower,
        "upper_pa": upper,
        "statement": ("between %.0f pA (no spike) and %.0f pA (first spike)"
                      % (lower, upper)) if lower is not None else
                     ("at or below %.0f pA (first spike at the lowest "
                      "depolarizing amplitude tested)" % upper),
    }


def slope_input_resistance(rows: list[dict]) -> dict:
    """Input resistance from the slope of the subthreshold I-V relation.

    Apparent resistance at one amplitude confounds resistance with the active
    conductances recruited at that amplitude; the slope over the ohmic region
    (|I| <= %.0f pA, subthreshold amplitudes only) separates them.
    """ % OHMIC_LIMIT_PA
    region = [r for r in rows
              if abs(r["level_pa"]) <= OHMIC_LIMIT_PA + OHMIC_LIMIT_TOLERANCE_PA
              and r["spikes_in_step"] == 0]
    if len(region) < 3:
        return {"kind": "insufficient_points", "n_points": len(region)}
    x = np.asarray([r["level_pa"] for r in region], dtype=float)
    y = np.asarray([r["response_mv"] for r in region], dtype=float)
    slope_mohm, intercept = np.polyfit(x, y, 1)
    predicted = slope_mohm * x + intercept
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return {
        "kind": "fit",
        "n_points": len(region),
        "points_pa": [float(v) for v in x],
        "slope_mohm": float(slope_mohm * 1e3),
        "intercept_mv": float(intercept),
        "r_squared": (1.0 - ss_res / ss_tot) if ss_tot > 0.0 else float("nan"),
    }


# ---------------------------------------------------------- branch sensitivity
def in_step_difference(run_a: dict, run_b: dict) -> dict:
    """RMS and maximum voltage difference between two branches, in the step.

    Computed on the raw simulation traces over the common step window; the
    +14 mV output-stage shift is identical for both branches and cancels.
    """
    sim_a = run_a["summary"]["facts"]["comparison"]["simulated"]
    on = int(round(float(sim_a["step_onset_ms"]) / DT_MS))
    end = int(round(float(sim_a["step_end_ms"]) / DT_MS))
    a = run_a["raw_v_mv"]
    b = run_b["raw_v_mv"]
    n = min(a.size, b.size)
    window = slice(on, min(end, n))
    delta = a[window] - b[window]
    return {
        "onset_ms": float(sim_a["step_onset_ms"]),
        "end_ms": float(sim_a["step_end_ms"]),
        "n_samples": int(delta.size),
        "rms_mv": float(np.sqrt(np.mean(delta ** 2))),
        "max_abs_mv": float(np.max(np.abs(delta))),
    }


def compare_branches(stub_runs: list[dict], trunc_runs: list[dict]) -> dict:
    """Branch sensitivity at shared stimulus conditions, amplitude by amplitude.

    The two branches are never pooled: each entry is a pairwise comparison of
    the two answers to the *same* condition.
    """
    shared = []
    for stub, trunc in zip(stub_runs, trunc_runs):
        assert stub["sweep"] == trunc["sweep"]
        row_s = excitability_row(stub)
        row_t = excitability_row(trunc)
        shared.append({
            "run_id": row_s["run_id"],
            "condition": row_s["condition"],
            "sweep": row_s["sweep"],
            "level_pa": row_s["level_pa"],
            "spikes_stub": row_s["spikes_in_step"],
            "spikes_truncated": row_t["spikes_in_step"],
            "response_stub_mv": row_s["response_mv"],
            "response_truncated_mv": row_t["response_mv"],
            "response_delta_mv": round(row_t["response_mv"]
                                       - row_s["response_mv"], 4),
            "r_in_stub_mohm": row_s["input_resistance_mohm"],
            "r_in_truncated_mohm": row_t["input_resistance_mohm"],
            "r_in_ratio_truncated_over_stub": (
                round(row_t["input_resistance_mohm"]
                      / row_s["input_resistance_mohm"], 4)
                if row_s["input_resistance_mohm"] else None),
            "voltage_difference": in_step_difference(stub, trunc),
        })
    return {
        "shared_conditions": shared,
        "first_spike_amplitude": _first_spike_amplitude(stub_runs, trunc_runs),
    }


def _first_spike_amplitude(stub_runs: list[dict], trunc_runs: list[dict]) -> dict:
    """The amplitude at which each branch first spikes, and their difference."""
    out = {}
    for branch, runs in (("stub", stub_runs), ("truncated", trunc_runs)):
        rows = branch_rows(runs, branch)
        interval = rheobase_interval(rows)
        out[branch] = interval
    stub_kind = out["stub"]["kind"]
    trunc_kind = out["truncated"]["kind"]
    if stub_kind == "interval" and trunc_kind == "interval":
        out["difference_pa"] = (out["truncated"]["upper_pa"]
                                - out["stub"]["upper_pa"])
        out["statement"] = (
            "the first-spike amplitude differs by %.0f pA between the tested "
            "bounds" % abs(out["difference_pa"]))
    elif stub_kind == "above_range" and trunc_kind == "above_range":
        out["statement"] = ("neither branch spikes within the tested range, so "
                            "no first-spike amplitude difference is measurable")
    else:
        out["statement"] = ("only one branch spikes within the tested range; "
                            "the difference is not a single number")
    return out


# ---------------------------------------------------------------- verification
def verify_runs(runs_by_branch: dict, baseline_root: pathlib.Path | None,
                out: list[str]) -> bool:
    """Consistency checks over the whole measurement set.  Appends PASS/FAIL
    lines to ``out`` and returns whether everything passed."""
    ok = True

    def check(condition: bool, label: str, detail: str = "") -> None:
        nonlocal ok
        out.append("%s %s%s" % ("PASS" if condition else "FAIL", label,
                                (" (%s)" % detail) if detail else ""))
        if not condition:
            ok = False

    all_runs = runs_by_branch["stub"] + runs_by_branch["truncated"]

    # 1. the plan itself: both branches, every condition, no fitting sweep.
    check(len(runs_by_branch["stub"]) == len(CONDITIONS)
          and len(runs_by_branch["truncated"]) == len(CONDITIONS),
          "both branches executed all %d conditions" % len(CONDITIONS))
    check(all(r["sweep"] != FITTING_SWEEP for r in all_runs),
          "no run executed the fitting sweep %d" % FITTING_SWEEP)

    # 2. every run succeeded and every pipeline check passed.
    check(all(r["summary"].get("status") == "success" for r in all_runs),
          "all %d runs report status success" % len(all_runs),
          "%d runs" % len(all_runs))
    check(all(r["summary"]["facts"].get("phase") == "2G-C" for r in all_runs),
          "every run is recorded as a Phase 2G-C measurement")
    check(all(r["summary"]["facts"].get("condition") for r in all_runs),
          "every run carries an explicit --condition label")

    # 3. the command line is recorded and names the branch explicitly.
    check(all("--axon-type" in r["summary"]["facts"]["command"]
              and "--condition" in r["summary"]["facts"]["command"]
              for r in all_runs),
          "every recorded command line names --axon-type and --condition")

    # 4. every measured level matches the validated table for its sweep.
    bad_levels = [r["run_id"] for r in all_runs
                  if not r["summary"]["facts"]["comparison"]["stimulus"]
                  ["level_matches"]]
    check(not bad_levels, "every command level matches the validated table",
          ",".join(bad_levels) if bad_levels else "")

    # 5. one model: identical input digests across all 28 runs.
    input_sets = {json.dumps(r["summary"]["facts"]["hashes"]["inputs"],
                             sort_keys=True) for r in all_runs}
    check(len(input_sets) == 1,
          "all runs consumed byte-identical inputs (descriptor, morphology, "
          "marker, NWB)", "%d distinct input sets" % len(input_sets))

    # 6. one library: the same compiled mechanism set served every run.
    libraries = {r["summary"]["facts"]["hashes"].get("mechanism_library_sha256")
                 for r in all_runs}
    check(len(libraries) == 1,
          "all runs executed the same compiled mechanism library",
          "%d distinct libraries" % len(libraries))

    # 7. the two spike detectors agree in every run.
    disagreeing = [r["run_id"] for r in all_runs
                   if r["summary"]["facts"]["comparison"]["simulated"]
                   ["n_in_step"]
                   != r["summary"]["facts"]["comparison"]["simulated"]
                   ["n_spikes_allen"]]
    check(not disagreeing,
          "the crossing detector and the Allen detector agree on every run",
          ",".join(disagreeing) if disagreeing else "")

    # 8. within a branch, the lead-in is the same 0 pA segment, so the settled
    #    baseline must be identical across all 14 conditions of that branch.
    for branch in BRANCHES:
        baselines = {round(float(
            r["summary"]["facts"]["comparison"]["settling"]["simulated"]
            ["settled_baseline_mv"]), 6)
            for r in runs_by_branch[branch]}
        check(len(baselines) == 1,
              "%s branch: one settled baseline across all conditions" % branch,
              "%.6f mV" % baselines.pop() if len(baselines) == 1
              else "%d values" % len(baselines))

    # 9. the +170 pA condition reproduces the Phase 2G-B outputs byte-for-byte.
    if baseline_root is not None and baseline_root.exists():
        for branch, run_id_2gb in (("stub", "A"), ("truncated", "C")):
            try:
                old = json.loads(
                    (baseline_root / ("%s_%s_sweep38" % (run_id_2gb, branch))
                     / "run_summary.json").read_text(encoding="utf-8"))
                old_sha = old["facts"]["hashes"]["output_nwb_sha256"]
            except (OSError, ValueError):
                check(False, "%s baseline summary readable" % branch)
                continue
            new_run = next(r for r in runs_by_branch[branch]
                           if r["sweep"] == 38)
            new_sha = new_run["summary"]["facts"]["hashes"][
                "output_nwb_sha256"]
            check(new_sha == old_sha,
                  "%s +170 pA reproduces the 2G-B output NWB byte-for-byte"
                  % branch, new_sha[:16])
    else:
        check(False, "Phase 2G-B baseline root exists")

    # 10. the traces are distinct across conditions (each run is its own run).
    trace_digests = {r["trace_sha256"] for r in all_runs}
    check(len(trace_digests) == len(all_runs),
          "every run wrote a distinct trace file",
          "%d distinct traces over %d runs" % (len(trace_digests),
                                               len(all_runs)))

    return ok


# --------------------------------------------------------------------- figures
def make_figures(runs_by_branch: dict, rows_by_branch: dict,
                 differences: dict, figures_dir: pathlib.Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures_dir.mkdir(parents=True, exist_ok=True)
    identity = ("All-active model 497233292 (published parameters)\n"
                "substitute morphology 674389901 | stimulus: %s 1 s steps"
                % COARSE_BLOCK)
    written = []

    def style(axis):
        axis.grid(True, alpha=0.3)
        axis.set_axisbelow(True)

    # --- figures 1 and 2: amplitude versus spike count, one branch each.
    for branch, figure_no in (("stub", 1), ("truncated", 2)):
        rows = rows_by_branch[branch]
        levels = [r["level_pa"] for r in rows]
        counts = [r["spikes_in_step"] for r in rows]
        fig, axis = plt.subplots(figsize=(9, 5.5))
        axis.plot(levels, counts, "o-", color="#1a6faa")
        for x, y in zip(levels, counts):
            axis.annotate(str(y), (x, y), textcoords="offset points",
                          xytext=(0, 6), ha="center", fontsize=9)
        interval = rheobase_interval(rows)
        axis.set_title("%s | axon treatment: %s\n%s"
                       % (identity, branch, interval["statement"]),
                       fontsize=10)
        axis.set_xlabel("command current (pA)")
        axis.set_ylabel("in-step spike count")
        style(axis)
        axis.set_ylim(-0.5, max(counts) + 1.5)
        path = figures_dir / ("fig%d_%s_spikecount.png" % (figure_no, branch))
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        written.append(str(path))

    # --- figure 3: both branches, amplitude versus steady-state response.
    fig, axis = plt.subplots(figsize=(9, 6))
    for branch, color in (("stub", "#1a6faa"), ("truncated", "#c2571a")):
        rows = rows_by_branch[branch]
        axis.plot([r["level_pa"] for r in rows],
                  [r["response_mv"] for r in rows], "o-", color=color,
                  label="axon treatment: %s" % branch)
    axis.axhline(0.0, color="grey", linewidth=0.8)
    axis.set_title("%s | both axon treatments, never pooled\n"
                   "steady-state response: plateau (median, last 200 ms) "
                   "minus settled baseline" % identity, fontsize=10)
    axis.set_xlabel("command current (pA)")
    axis.set_ylabel("steady-state response (mV)")
    axis.legend()
    style(axis)
    path = figures_dir / "fig3_depolarisation.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    written.append(str(path))

    # --- figure 4: amplitude versus mean firing rate, where measurable.
    fig, axis = plt.subplots(figsize=(9, 5.5))
    any_rate = False
    for branch, color in (("stub", "#1a6faa"), ("truncated", "#c2571a")):
        rows = [r for r in rows_by_branch[branch] if r["mean_rate_hz"]]
        if rows:
            any_rate = True
            axis.plot([r["level_pa"] for r in rows],
                      [r["mean_rate_hz"] for r in rows], "o-", color=color,
                      label="axon treatment: %s" % branch)
        else:
            # The absence of a series is a result, not a gap in the plot: say
            # so on the figure rather than leaving an unexplained empty branch.
            axis.plot([], [], "o-", color=color,
                      label="axon treatment: %s (no spikes at any tested "
                            "amplitude)" % branch)
    if not any_rate:
        axis.text(0.5, 0.5,
                  "no tested amplitude elicited a spike in either branch:\n"
                  "no firing rate is measurable within the tested range",
                  transform=axis.transAxes, ha="center", va="center",
                  fontsize=11)
    axis.legend()
    axis.set_title("%s | both axon treatments, never pooled\n"
                   "mean in-step firing rate" % identity, fontsize=10)
    axis.set_xlabel("command current (pA)")
    axis.set_ylabel("mean firing rate (Hz)")
    style(axis)
    path = figures_dir / "fig4_firing_rate.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    written.append(str(path))

    # --- figure 5: branch difference in voltage response at shared conditions.
    shared = differences["shared_conditions"]
    levels = [entry["level_pa"] for entry in shared]
    rms = [entry["voltage_difference"]["rms_mv"] for entry in shared]
    peak = [entry["voltage_difference"]["max_abs_mv"] for entry in shared]
    fig, axis = plt.subplots(figsize=(9, 5.5))
    axis.plot(levels, rms, "o-", color="#7a1a6f",
              label="RMS difference in step")
    axis.plot(levels, peak, "s--", color="#6f7a1a",
              label="maximum absolute difference in step")
    axis.set_title("%s\nbranch difference (truncated minus stub) in the "
                   "simulated voltage, per shared condition" % identity,
                   fontsize=10)
    axis.set_xlabel("command current (pA)")
    axis.set_ylabel("voltage difference between axon treatments (mV)")
    axis.legend()
    style(axis)
    path = figures_dir / "fig5_branch_difference.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    written.append(str(path))

    return written


# ----------------------------------------------------------------------- main
def build_summary(runs_by_branch: dict, differences: dict) -> dict:
    rows_by_branch = {branch: branch_rows(runs_by_branch[branch], branch)
                      for branch in BRANCHES}
    return {
        "phase": "2G-C",
        "model_claim": (runs_by_branch["stub"][0]["summary"]["facts"]
                        ["model_claim"]),
        "conditions": [{"run_id": rid, "sweep": sweep, "level_pa": level,
                        "label": label}
                       for rid, sweep, level, label in CONDITIONS],
        "fitting_sweep_excluded": FITTING_SWEEP,
        "excitability": {
            branch: {
                "rows": rows_by_branch[branch],
                "rheobase": rheobase_interval(rows_by_branch[branch]),
                "slope_input_resistance":
                    slope_input_resistance(rows_by_branch[branch]),
            } for branch in BRANCHES
        },
        "branch_sensitivity": differences,
    }


def _print_table(rows: list[dict], title: str) -> None:
    print()
    print(title)
    header = ("%-5s %-6s %-6s %-7s %-7s %-8s %-9s %-10s %-9s %-9s"
              % ("run", "sweep", "pA", "spikes", "allen", "lat ms",
                 "rate Hz", "resp mV", "R_in MO", "rec spikes"))
    print(header)
    print("-" * len(header))
    for row in rows:
        print("%-5s %-6d %-6.0f %-7d %-7d %-8s %-9s %-10.3f %-9s %-9d"
              % (row["run_id"], row["sweep"], row["level_pa"],
                 row["spikes_in_step"], row["spikes_allen"],
                 ("%.1f" % row["first_latency_ms"])
                 if row["first_latency_ms"] is not None else "-",
                 ("%.2f" % row["mean_rate_hz"]) if row["mean_rate_hz"] else "-",
                 row["response_mv"],
                 ("%.1f" % row["input_resistance_mohm"])
                 if row["input_resistance_mohm"] == row["input_resistance_mohm"]
                 else "-",
                 row["recorded_spikes_in_step"]))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results-root", required=True)
    parser.add_argument("--baseline-root", required=True,
                        help="Phase 2G-B results root (A/C baseline digests)")
    parser.add_argument("--figures-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    results_root = pathlib.Path(args.results_root).expanduser()
    baseline_root = pathlib.Path(args.baseline_root).expanduser()
    figures_dir = pathlib.Path(args.figures_dir).expanduser()
    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        runs_by_branch = load_all_runs(results_root)
    except FileNotFoundError as exc:
        print("MISSING RUN: %s" % exc)
        return 1

    report: list[str] = []
    ok = verify_runs(runs_by_branch, baseline_root, report)
    print("=== consistency checks ===")
    for line in report:
        print(line)
    print("checks: %d PASS, %d FAIL" % (
        sum(1 for line in report if line.startswith("PASS")),
        sum(1 for line in report if line.startswith("FAIL"))))

    rows_by_branch = {branch: branch_rows(runs_by_branch[branch], branch)
                      for branch in BRANCHES}
    differences = compare_branches(runs_by_branch["stub"],
                                   runs_by_branch["truncated"])

    for branch in BRANCHES:
        _print_table(rows_by_branch[branch],
                     "=== excitability: %s axon treatment ===" % branch)
        interval = rheobase_interval(rows_by_branch[branch])
        print("rheobase: %s" % interval["statement"])
        slope = slope_input_resistance(rows_by_branch[branch])
        if slope["kind"] == "fit":
            print("slope R_in over ohmic region (|I| <= %.0f pA): %.1f MOhm "
                  "(r^2 = %.4f, %d points)"
                  % (OHMIC_LIMIT_PA, slope["slope_mohm"], slope["r_squared"],
                     slope["n_points"]))
        else:
            print("slope R_in: %s" % slope["kind"])

    print()
    print("=== branch sensitivity at shared conditions ===")
    print("%-5s %-6s %-13s %-13s %-13s %-12s"
          % ("run", "pA", "resp stub mV", "resp trunc mV", "delta mV",
             "R_in ratio"))
    for entry in differences["shared_conditions"]:
        print("%-5s %-6.0f %-13.3f %-13.3f %-13.3f %-12s"
              % (entry["run_id"], entry["level_pa"],
                 entry["response_stub_mv"], entry["response_truncated_mv"],
                 entry["response_delta_mv"],
                 ("%.2f" % entry["r_in_ratio_truncated_over_stub"])
                 if entry["r_in_ratio_truncated_over_stub"] else "-"))
    print("first-spike amplitude: %s"
          % differences["first_spike_amplitude"]["statement"])

    figures = make_figures(runs_by_branch, rows_by_branch, differences,
                           figures_dir)
    print()
    print("=== figures ===")
    for path in figures:
        print("  %s" % path)

    summary = build_summary(runs_by_branch, differences)
    summary["consistency_report"] = report
    summary_path = out_dir / "phase2g_c_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str),
                            encoding="utf-8")
    print()
    print("summary written to", summary_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

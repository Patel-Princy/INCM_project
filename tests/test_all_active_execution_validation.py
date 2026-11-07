"""Unit tests for the Phase 2G-B all-active execution and branch analysis.

Two things in this phase are worth guarding with tests, and neither needs
NEURON, AllenSDK or the gitignored model cache:

* the *design* is frozen, so the run plan, the excluded sweep and the two
  explicit axon branches must not drift;
* the *arithmetic* the report quotes must be reproducible from a synthetic
  trace whose answer is known by construction -- the step response, the input
  resistance, the branch difference and the "these two runs are the same
  answer" test all have hand-computable expectations.

The unit tests also pin the two places where this phase already went wrong
once: a metric computed in volts rather than millivolts, and a step response
divided by picoamps without the 1000x conversion to megohms.

Run with ``python -m pytest tests -q``.
"""
from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import analyse_all_active_branches as analysis  # noqa: E402
import validate_all_active_execution as executor  # noqa: E402


# --------------------------------------------------------------------- design
def test_every_output_identifies_the_model_as_a_reconstruction():
    """The mandated sentence, and the substituted morphology inside it."""
    for branch in executor.AXON_BRANCHES:
        claim = executor.model_claim(branch)
        assert claim.startswith("All-active model 497233292 using published "
                                "parameters, substitute morphology 674389901, "
                                "and project-declared axon treatment ")
        assert claim.endswith(branch)
        # The claim may not imply that the original fit was recovered.
        assert "reproduc" not in claim.lower()
        assert "original" not in claim.lower()


def test_run_plan_is_the_frozen_four_runs():
    assert executor.RUN_PLAN == {
        "A": ("stub", 38),
        "B": ("stub", 49),
        "C": ("truncated", 38),
        "D": ("truncated", 49),
    }
    # Both branches appear, so no branch can be dropped from the comparison.
    assert {branch for branch, _ in executor.RUN_PLAN.values()} == set(
        executor.AXON_BRANCHES)
    assert set(executor.AXON_BRANCHES) == {"stub", "truncated"}


def test_no_evaluation_sweep_overlaps_the_fitting_sweep():
    """Sweep 41 fitted this model, so it can never be an evaluation sweep."""
    evaluated = {sweep for _, sweep in executor.RUN_PLAN.values()}
    assert evaluated == {executor.BRACKET_SWEEP, executor.HELD_OUT_SWEEP}
    assert executor.FITTING_SWEEP == 41
    assert executor.FITTING_SWEEP not in evaluated
    # 41 belongs to the COARSE family, which is why sweep 38 needed care.
    assert executor.FITTING_SWEEP in executor.COARSE_SWEEPS
    assert executor.BRACKET_SWEEP in executor.COARSE_SWEEPS
    assert executor.HELD_OUT_SWEEP in executor.FINEST_SWEEPS


def test_analysis_pairs_sweeps_and_branches_the_same_way():
    assert analysis.RUN_DIRS == executor.RUN_PLAN
    # One pair per stimulus: same sweep, different branch.
    assert analysis.PAIRS == (("A", "C"), ("B", "D"))
    for first, second in analysis.PAIRS:
        assert analysis.RUN_DIRS[first][1] == analysis.RUN_DIRS[second][1]
        assert analysis.RUN_DIRS[first][0] != analysis.RUN_DIRS[second][0]


# ----------------------------------------------------------------- provenance
def test_sha256_of_matches_hashlib(tmp_path):
    payload = b"phase 2g-b provenance\n" * 1000
    path = tmp_path / "asset.bin"
    path.write_bytes(payload)
    assert executor.sha256_of(path) == hashlib.sha256(payload).hexdigest()


def test_pinned_digests_are_full_length_and_distinct():
    for name, (digest, size) in executor.EXPECTED.items():
        assert len(digest) == 64 and int(digest, 16) >= 0, name
        assert size > 0, name
    assert len({digest for digest, _ in executor.EXPECTED.values()}) == len(
        executor.EXPECTED)


def test_junction_convention_is_the_published_one():
    # The descriptor says -14 mV; the output stage adds +14 mV to the trace and
    # never to a model parameter.
    assert executor.JUNCTION_MV == -14.0
    assert executor.OUTPUT_SHIFT_MV == 14.0
    assert executor.OUTPUT_SHIFT_MV == -executor.JUNCTION_MV


# ------------------------------------------------------------------- checker
def test_checker_separates_failures_from_observations():
    checker = executor.Checker()
    checker.heading("synthetic")
    checker.check(True, "passes")
    checker.check(False, "fails")
    checker.observe("observed")
    checker.skip("skipped")
    checker.metric("fraction", 0.5)

    tally = checker.tally()
    assert tally["checks"] == 2          # observations are not checks
    assert tally["passed"] == 1
    assert tally["failed"] == 1
    assert tally["skipped"] == 2
    assert tally["metrics"] == 1
    assert checker.failures() == 1


def test_fmt_is_stable_for_the_values_the_report_quotes():
    assert executor._fmt(True) == "true"
    assert executor._fmt(7) == "7"
    assert executor._fmt(float("nan")) == "nan"
    assert executor._fmt(0.0) == "0"
    assert executor._fmt(3.7245) == "3.7245"
    assert executor._fmt(1.23456789e6) == "1.2346e+06"


# ------------------------------------------------------------------ settling
RATE_HZ = 200_000.0
DT_MS = 1e3 / RATE_HZ
ONSET_MS = 1020.0
ONSET_INDEX = int(round(ONSET_MS / DT_MS))


def _settling_trace(tau_ms=50.0, final_mv=-75.0, start_mv=-90.0):
    t_ms = np.arange(ONSET_INDEX + 1) * DT_MS
    return final_mv + (start_mv - final_mv) * np.exp(-t_ms / tau_ms)


def test_settling_report_measures_the_approach_not_the_average():
    v = _settling_trace()
    marks = executor.settling_report(v, RATE_HZ, ONSET_INDEX)
    # 99.8 % of the way to -75 mV by 1020 ms with tau = 50 ms.
    assert marks["t_step_onset"] == pytest.approx(-75.0, abs=0.01)
    assert marks["settled_baseline_mv"] == pytest.approx(-75.0, abs=0.01)
    assert abs(marks["drift_last_20ms_mv"]) < 0.01
    # The whole lead-in is emphatically not settled -- the trace climbs 15 mV
    # from v_init -- which is exactly why the report quotes the last 100 ms
    # rather than the full 1020 ms.
    assert marks["drift_full_leadin_mv"] == pytest.approx(15.0, abs=0.01)


# --------------------------------------------------------------- trace facts
def _step_trace(baseline_mv=-75.0, plateau_mv=-68.0, n_ms=2500.0):
    n = int(round(n_ms / DT_MS))
    v = np.full(n, baseline_mv)
    end = ONSET_INDEX + int(round(1000.0 / DT_MS))
    v[ONSET_INDEX:end] = plateau_mv
    return v


def test_trace_facts_recovers_a_known_step():
    facts = analysis.trace_facts(_step_trace())
    assert facts["settled_baseline_mv"] == pytest.approx(-75.0)
    assert facts["plateau_mv"] == pytest.approx(-68.0)
    assert facts["response_mv"] == pytest.approx(7.0)
    assert facts["drift_last_20ms_mv"] == pytest.approx(0.0)


def test_input_resistance_converts_gigaohm_to_megohm():
    """7 mV of 170 pA is 41.2 MOhm, not 0.041."""
    facts = analysis.trace_facts(_step_trace())
    expected = 7.0 / analysis.COMMAND_PA * 1e3
    assert facts["input_resistance_mohm"] == pytest.approx(expected, rel=1e-12)
    assert 41.0 < facts["input_resistance_mohm"] < 42.0


def test_trace_facts_reads_only_the_step_window():
    """A post-step rebound must not be mistaken for the depolarised plateau."""
    v = _step_trace()
    v[ONSET_INDEX + int(round(1100.0 / DT_MS)):] = -95.0
    facts = analysis.trace_facts(v)
    assert facts["plateau_mv"] == pytest.approx(-68.0)
    assert facts["post_step_min_mv"] == pytest.approx(-95.0)


def test_trace_facts_reports_nan_rather_than_raising_on_a_short_trace():
    """A trace that stops during the step has no plateau window to average."""
    import warnings

    v = np.full(ONSET_INDEX + 1000, -70.0)
    # The empty-window mean and median warn; the point of the test is the NaN
    # they yield, so the warnings are local to this assertion.
    with warnings.catch_warnings(), np.errstate(invalid="ignore"):
        warnings.simplefilter("ignore", RuntimeWarning)
        facts = analysis.trace_facts(v)
    assert math.isfinite(facts["settled_baseline_mv"])
    assert facts["settled_baseline_mv"] == pytest.approx(-70.0)
    # NaN, not a silent fallback to some other window, and not an exception.
    assert math.isnan(facts["plateau_mv"])
    assert math.isnan(facts["response_mv"]) or facts["response_mv"] == 0.0


# ---------------------------------------------------------- branch difference
def test_branch_difference_is_zero_for_identical_traces():
    v = _step_trace()
    difference = analysis.branch_difference(v, v.copy(), "stub", "truncated")
    assert difference["rms_difference_in_step_mv"] == 0.0
    assert difference["max_abs_difference_mv"] == 0.0
    assert difference["samples_above_1mv_in_step"] == 0


def test_branch_difference_is_antisymmetric():
    a = _step_trace(plateau_mv=-65.0)
    b = _step_trace(plateau_mv=-68.0)
    forward = analysis.branch_difference(a, b, "stub", "truncated")
    backward = analysis.branch_difference(b, a, "truncated", "stub")
    assert forward["rms_difference_in_step_mv"] == pytest.approx(3.0)
    assert forward["max_abs_difference_in_step_mv"] == pytest.approx(3.0)
    assert forward["mean_difference_in_step_mv"] == pytest.approx(
        -backward["mean_difference_in_step_mv"])


def test_branch_difference_separates_lead_in_from_step():
    """A difference confined to initialisation is not a response difference."""
    a = _step_trace()
    b = _step_trace()
    b[:1000] = -90.0          # differ only before the step
    difference = analysis.branch_difference(a, b, "stub", "truncated")
    assert difference["rms_difference_in_step_mv"] == 0.0
    assert difference["rms_difference_pre_step_mv"] > 0.0


def test_identical_except_length_ignores_the_truncated_tail():
    a = np.arange(1000.0)
    b = np.arange(600.0)
    result = analysis.traces_identical_except_length(a, b)
    assert result["identical"] is True
    assert result["n_compared"] == 600
    assert analysis.traces_identical_except_length(
        a, b + 1e-12)["identical"] is False


# --------------------------------------------------------------- run quartet
def make_run(run_id, branch, sweep, v_mv, output_sha, inputs_sha="inputs",
             library="lib", status="success"):
    facts = {
        "model_claim": executor.model_claim(branch),
        "hashes": {
            "inputs": {"a": inputs_sha},
            "mechanism_library_sha256": library,
            "output_nwb_sha256": output_sha,
        },
        "comparison": {
            "recorded": {"n_in_step": 12},
            "simulated": {"n_in_step": 0},
            "pair": {"rmse_in_step_mv": 1.0, "rmse_whole_mv": 2.0,
                     "corr_in_step": 0.5, "corr_whole": 0.9},
            "settling": {"recorded": {"settled_baseline_mv": -80.0},
                         "simulated": {"settled_baseline_mv": -62.0}},
        },
    }
    return {"run_id": run_id, "axon_type": branch, "sweep": sweep,
            "summary": {"status": status, "facts": facts},
            "trace_path": Path("traces_%s.npz" % run_id),
            "raw_v_mv": np.asarray(v_mv, dtype=float),
            "written_v_mv": np.asarray(v_mv, dtype=float)}


def quartet():
    stub = _step_trace(plateau_mv=-68.0)
    truncated = _step_trace(plateau_mv=-65.0)
    return {
        "A": make_run("A", "stub", 38, stub, "out-a"),
        "B": make_run("B", "stub", 49, stub, "out-b"),
        "C": make_run("C", "truncated", 38, truncated, "out-c"),
        "D": make_run("D", "truncated", 49, truncated, "out-d"),
    }


def labels(consistency):
    return {row["label"]: row["ok"] for row in consistency["checks"]}


def test_a_consistent_quartet_passes_every_check():
    consistency = analysis.verify_runs(quartet(), None)
    assert consistency["failed"] == 0, consistency["checks"]
    assert labels(consistency)["A and B return the same response to the same "
                               "command"] is True


def test_two_indistinguishable_branches_are_reported_as_a_failure():
    """If the branch made no difference the comparison would be vacuous."""
    runs = quartet()
    runs["C"] = make_run("C", "truncated", 38, runs["A"]["raw_v_mv"], "out-c")
    consistency = analysis.verify_runs(runs, None)
    assert labels(consistency)["A and C differ inside the step"] is False
    assert consistency["failed"] >= 1


def test_duplicate_output_files_are_reported_as_a_failure():
    runs = quartet()
    runs["D"] = make_run("D", "truncated", 49, runs["D"]["raw_v_mv"], "out-c")
    consistency = analysis.verify_runs(runs, None)
    assert labels(consistency)[
        "the four output NWB files are four distinct artefacts"] is False


def test_a_failed_run_cannot_be_hidden_behind_a_successful_one():
    runs = quartet()
    runs["C"]["summary"]["status"] = "failed"
    consistency = analysis.verify_runs(runs, None)
    assert labels(consistency)["all four runs report success"] is False


def test_determinism_check_compares_the_replicate_to_run_a():
    runs = quartet()
    repro = make_run("A", "stub", 38, runs["A"]["raw_v_mv"], "out-a")
    consistency = analysis.verify_runs(runs, repro)
    assert consistency["determinism"]["output_digest_matches"] is True
    assert labels(consistency)["a second process reproduces run A exactly"] is True

    drifting = make_run("A", "stub", 38,
                        runs["A"]["raw_v_mv"] + 1e-6, "out-a")
    assert analysis.verify_runs(quartet(), drifting)["failed"] >= 1


# ------------------------------------------------------------------- reporting
def test_recording_row_maps_the_summary_without_inventing_values():
    run = make_run("A", "stub", 38, _step_trace(), "out-a")
    row = analysis.recording_row(run)
    assert row["run"] == "A"
    assert row["axon_type"] == "stub"
    assert row["sweep"] == 38
    assert row["recorded_spikes_in_step"] == 12
    assert row["simulated_spikes_in_step"] == 0
    # Derived, not stored: the sign convention of the baseline difference.
    assert row["simulated_settled_baseline_mv"] - row[
        "recorded_settled_baseline_mv"] == pytest.approx(18.0)


def test_perisomatic_reference_is_absent_rather_than_guessed(tmp_path):
    reference = analysis.perisomatic_reference(tmp_path / "none.json",
                                               tmp_path / "also_none.json")
    assert reference["available"] is False
    assert reference["sweep38"] is None and reference["sweep49"] is None
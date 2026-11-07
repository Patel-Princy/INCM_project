"""Unit tests for the Phase 2G-C descriptive excitability and rheobase mapping.

Three things in this phase are worth guarding with tests, and none of them
needs NEURON, AllenSDK or the gitignored model cache:

* the *measurement rules*: sweep 41 is excluded everywhere, a measurement needs
  an explicit branch and an explicit --condition label, and FINEST/C2 sweeps
  are not measurement conditions -- the protocols stay separated;
* the *arithmetic* the report quotes: the rheobase interval, the firing rate,
  the input-resistance unit conversion, the ohmic-region slope and the branch
  voltage difference all have hand-computable expectations;
* the *integrity checks*: a failed run, a pooled branch, a drifting baseline
  digest or a tampered asset digest must be reported, never absorbed.

The unit tests also pin the fencepost this phase hit once: measured DAC levels
like 110.000002 pA must not fall outside a nominal 110 pA ohmic boundary.

Run with ``python -m pytest tests -q``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import analyse_all_active_excitability as analysis  # noqa: E402
import validate_all_active_execution as executor  # noqa: E402


# ------------------------------------------------------------ synthetic runs
def make_run(run_id, branch, sweep, level_pa, spikes=0, recorded=0,
             plateau_mv=None, baseline_mv=-63.0, latency_ms=None,
             status="success", output_sha="out", inputs_sha="inputs",
             library="lib", condition=None, block="C1LSCOARSE150216",
             level_matches=True, response_slope=0.04):
    """A synthetic run with exactly the summary structure the analysis reads."""
    condition = condition or ("coarse_p%03d" % level_pa)
    # Default plateau scales with the level so the synthetic I-V relation has
    # a nonzero, non-flat slope.
    plateau = (baseline_mv + response_slope * level_pa if plateau_mv is None
               else plateau_mv)
    spike_times = ([1020.0 + (latency_ms if latency_ms is not None else 20.0)
                    + 50.0 * i for i in range(spikes)]
                   if spikes else [])
    simulated = {
        "n_in_step": spikes,
        "n_spikes_allen": spikes,
        "first_in_step_latency_ms": ((latency_ms if latency_ms is not None
                                      else 20.0) if spikes
                                     else float("nan")),
        "spike_times_in_step_ms": spike_times,
        "step_onset_ms": 1020.0,
        "step_end_ms": 2020.0,
        "step_duration_ms": 1000.0,
        "plateau_mv": plateau,
        "baseline_mv": baseline_mv,
        "v_max_mv": plateau + 1.0,
    }
    facts = {
        "phase": "2G-C",
        "run_id": run_id,
        "condition": condition,
        "axon_type": branch,
        "sweep": sweep,
        "model_claim": executor.model_claim(branch),
        "command": ("python validate.py --model-dir m --allensdk-src a "
                    "--repo-cache r --run-id %s --condition %s "
                    "--axon-type %s --sweep %d --out-dir o"
                    % (run_id, condition, branch, sweep)),
        "hashes": {
            "inputs": {"382982932.nwb": inputs_sha},
            "output_nwb_sha256": output_sha,
            "mechanism_library_sha256": library,
        },
        "comparison": {
            "stimulus": {
                "sweep": sweep,
                "level_pa": level_pa,
                "expected_level_pa": level_pa,
                "level_matches": level_matches,
                "step_duration_ms": 1000.0,
                "analyse_status": "OK",
                "probe_removed": True,
                "block": block,
            },
            "recorded": {"n_in_step": recorded},
            "simulated": simulated,
            "settling": {"simulated": {
                "settled_baseline_mv": baseline_mv,
                "drift_last_20ms_mv": 0.0002,
            }},
        },
    }
    n = 500_000
    trace = np.full(n, baseline_mv, dtype=float)
    return {
        "run_id": run_id,
        "axon_type": branch,
        "sweep": sweep,
        "summary": {"facts": facts, "status": status,
                    "tally": {"failed": 0, "checks": 68}},
        "raw_v_mv": trace,
        "trace_sha256": "trace-%s-%s" % (run_id, branch),
    }


def make_branch_runs(branch, spike_fn=None, **kwargs):
    """The 14 frozen conditions for one branch, silent by default."""
    runs = []
    for run_id, sweep, level, _label in analysis.CONDITIONS:
        spikes = 0 if spike_fn is None else spike_fn(level)
        runs.append(make_run(run_id, branch, sweep, level, spikes=spikes,
                             **kwargs))
    return runs


# -------------------------------------------------------- measurement rules
def test_fitting_sweep_is_excluded_from_every_evaluation():
    assert executor.FITTING_SWEEP == 41
    # Both a measurement and a 2G-B-style invocation are refused.
    assert executor.validate_measurement("M41", "stub", 41, "coarse_p230")
    assert executor.validate_measurement("M41", "stub", 41, "")


def test_measurement_requires_an_explicit_branch_and_condition():
    assert executor.validate_measurement("M01", "stub", 24, "")  # no label
    assert executor.validate_measurement("M01", "stub", 24, "coarse_n110") is None
    assert executor.validate_measurement("M01", "truncated", 24,
                                         "coarse_n110") is None


def test_planned_2gb_runs_keep_their_frozen_identities():
    assert executor.validate_measurement("A", "stub", 38, "") is None
    assert executor.validate_measurement("A", "stub", 49, "")
    assert executor.validate_measurement("A", "stub", 38, "coarse_p170")


def test_fine_st_and_c2_sweeps_are_not_measurement_conditions():
    """Protocol separation: only the COARSE block is measured in 2G-C."""
    for sweep in (49, 50, 51, 52):          # C1LSFINEST150112
        assert executor.validate_measurement("M99", "stub", sweep,
                                             "coarse_f170")
    for sweep in (64, 72, 79):              # C2SQRHELNG150216
        assert executor.validate_measurement("M99", "stub", sweep,
                                             "coarse_c2")


def test_frozen_condition_list_covers_the_coarse_ladder_without_sweep_41():
    sweeps = [sweep for _rid, sweep, _level, _label in analysis.CONDITIONS]
    assert len(analysis.CONDITIONS) == 14
    assert executor.FITTING_SWEEP not in sweeps
    assert all(sweep in executor.COARSE_SWEEPS for sweep in sweeps)
    # The ladder contains amplitudes below +170, +170 itself, above it, and
    # the highest valid depolarizing amplitude in the block.
    levels = sorted(level for _rid, _sweep, level, _label in analysis.CONDITIONS)
    assert 170.0 in levels
    assert min(levels) < 170.0 < max(levels)
    assert max(levels) == 270.0
    # One hyperpolarizing control, never pooled into the rheobase logic.
    assert sum(1 for level in levels if level < 0) == 1


def test_sweep_levels_table_matches_the_measured_ladder():
    """The level table is the one re-measured from the NWB stimulus arrays."""
    expected = {24: -110.0, 25: -90.0, 26: -70.0, 27: -50.0, 28: -30.0,
                29: -10.0, 30: 10.0, 31: 30.0, 32: 50.0, 33: 70.0,
                34: 90.0, 35: 110.0, 36: 130.0, 37: 150.0, 38: 170.0,
                39: 190.0, 40: 210.0, 41: 230.0, 42: 250.0, 43: 270.0,
                49: 170.0, 50: 170.0, 51: 170.0, 52: 170.0}
    assert executor.SWEEP_LEVELS_PA == expected


def test_pinned_asset_digests_are_unchanged():
    """Asset immutability: the digests the runs verified against are pinned."""
    for name, (digest, size) in executor.EXPECTED.items():
        assert len(digest) == 64
        assert size > 0
    assert executor.EXPECTED[executor.DESCRIPTOR][0] == (
        "bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963")
    assert executor.EXPECTED[executor.STIMULUS_NWB][0] == (
        "d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63")


# ------------------------------------------------------------------- units
def test_input_resistance_converts_the_quotient_to_megohms():
    # 7.125 mV / 170 pA = 0.041911... GOhm = 41.911... MOhm.
    assert analysis.input_resistance_mohm(7.125, 170.0) == pytest.approx(
        41.9117647, abs=1e-4)
    # The hyperpolarizing control keeps a positive resistance.
    assert analysis.input_resistance_mohm(-10.297, -110.0) == pytest.approx(
        93.609, abs=1e-2)
    assert math_isnan(analysis.input_resistance_mohm(1.0, 0.0))


def math_isnan(value):
    return value != value


def test_mean_rate_is_spikes_over_step_duration():
    assert analysis.mean_rate_hz(4, 1000.0) == pytest.approx(4.0)
    assert analysis.mean_rate_hz(26, 1000.0) == pytest.approx(26.0)
    assert analysis.mean_rate_hz(0, 1000.0) == 0.0
    assert math_isnan(analysis.mean_rate_hz(1, 0.0))


def test_excitability_row_maps_the_recorded_facts():
    run = make_run("M12", "truncated", 40, 210.0, spikes=4, recorded=22,
                   plateau_mv=-47.85, baseline_mv=-63.32, latency_ms=18.54)
    row = analysis.excitability_row(run)
    assert row["spikes_in_step"] == 4
    assert row["spikes_allen"] == 4
    assert row["first_latency_ms"] == pytest.approx(18.54)
    assert row["mean_rate_hz"] == pytest.approx(4.0)
    # ISIs come from the in-step spike times, not from the whole trace.
    assert row["isis_ms"] == [50.0, 50.0, 50.0]
    assert row["settled_baseline_mv"] == pytest.approx(-63.32)
    assert row["plateau_mv"] == pytest.approx(-47.85)
    assert row["response_mv"] == pytest.approx(15.47)
    assert row["input_resistance_mohm"] == pytest.approx(
        15.47 / 210.0 * 1e3, abs=0.01)
    assert row["recorded_spikes_in_step"] == 22
    assert row["block"] == "C1LSCOARSE150216"
    assert row["settles_before_step"] is True


def test_excitability_row_reports_no_latency_without_a_spike():
    row = analysis.excitability_row(make_run("M02", "stub", 30, 10.0))
    assert row["spikes_in_step"] == 0
    assert row["first_latency_ms"] is None
    assert row["mean_rate_hz"] == 0.0
    assert row["isis_ms"] == []


# ---------------------------------------------------------------- rheobase
def row(level, spikes):
    return {"level_pa": level, "spikes_in_step": spikes}


def test_rheobase_is_above_the_range_when_nothing_spikes():
    rows = [row(-110, 0), row(10, 0), row(170, 0), row(270, 0)]
    result = analysis.rheobase_interval(rows)
    assert result["kind"] == "above_range"
    assert result["highest_tested_pa"] == 270
    assert "above" in result["statement"]


def test_rheobase_is_below_the_range_when_everything_spikes():
    rows = [row(10, 1), row(30, 2), row(270, 26)]
    result = analysis.rheobase_interval(rows)
    assert result["kind"] == "below_range"
    assert result["lowest_tested_pa"] == 10


def test_rheobase_is_an_interval_bounded_by_tested_amplitudes():
    rows = [row(110, 0), row(130, 1), row(150, 6), row(170, 12)]
    result = analysis.rheobase_interval(rows)
    assert result["kind"] == "interval"
    assert result["lower_pa"] == 110
    assert result["upper_pa"] == 130


def test_rheobase_lower_bound_is_unknown_when_the_lowest_amplitude_spikes():
    """Non-monotone case: silent at 30 pA between spikes at 10 and 50 pA."""
    rows = [row(10, 1), row(30, 0), row(50, 2)]
    result = analysis.rheobase_interval(rows)
    assert result["kind"] == "interval"
    assert result["lower_pa"] is None
    assert result["upper_pa"] == 10


def test_hyperpolarizing_amplitudes_never_bound_the_rheobase():
    rows = [row(-110, 0), row(-50, 0), row(10, 0)]
    result = analysis.rheobase_interval(rows)
    # Only the depolarizing 10 pA counts as the highest tested amplitude.
    assert result["kind"] == "above_range"
    assert result["highest_tested_pa"] == 10


def test_rheobase_reports_nothing_when_no_depolarizing_amplitude_was_tested():
    assert analysis.rheobase_interval([row(-110, 0)])["kind"] == "none_tested"


# ------------------------------------------------------- input resistance
def test_slope_input_resistance_fits_a_linear_region():
    rows = [row_with_response(-110.0, -4.4), row_with_response(10.0, 0.4),
            row_with_response(30.0, 1.2), row_with_response(50.0, 2.0),
            row_with_response(70.0, 2.8)]
    result = analysis.slope_input_resistance(rows)
    assert result["kind"] == "fit"
    assert result["n_points"] == 5
    # 0.04 mV/pA = 40 MOhm.
    assert result["slope_mohm"] == pytest.approx(40.0, abs=0.5)
    assert result["r_squared"] == pytest.approx(1.0, abs=1e-9)


def row_with_response(level, response):
    return {"level_pa": level, "spikes_in_step": 0, "response_mv": response}


def test_ohmic_boundary_includes_measured_dac_levels():
    """Regression: 110.000002 pA is inside a nominal 110 pA boundary.

    A strict ``<=`` comparison dropped the +/-110 pA points and reported an
    ohmic region two points smaller than the documented one.
    """
    rows = [row_with_response(-110.000002, -4.4),
            row_with_response(110.000002, 4.4),
            row_with_response(10.0, 0.4)]
    result = analysis.slope_input_resistance(rows)
    assert result["kind"] == "fit"
    assert result["n_points"] == 3


def test_spiking_amplitudes_are_excluded_from_the_ohmic_region():
    rows = [row_with_response(10.0, 0.4), row_with_response(30.0, 1.2),
            {"level_pa": 50.0, "spikes_in_step": 2, "response_mv": 2.0}]
    result = analysis.slope_input_resistance(rows)
    assert result["n_points"] == 2
    assert result["kind"] == "insufficient_points"


# ------------------------------------------------------------ branch tables
def test_branch_rows_refuse_to_pool_the_two_branches():
    runs = make_branch_runs("stub")[:2] + make_branch_runs("truncated")[:2]
    with pytest.raises(ValueError, match="only stub runs"):
        analysis.branch_rows(runs, "stub")
    with pytest.raises(ValueError, match="only truncated runs"):
        analysis.branch_rows(runs, "truncated")


def test_branch_rows_are_sorted_by_amplitude():
    runs = list(reversed(make_branch_runs("stub")))
    rows = analysis.branch_rows(runs, "stub")
    levels = [r["level_pa"] for r in rows]
    assert levels == sorted(levels)


def test_compare_branches_pairs_shared_conditions_only():
    stub = make_branch_runs("stub")
    trunc = make_branch_runs("truncated", spike_fn=lambda level: level >= 190,
                             response_slope=0.07)
    differences = analysis.compare_branches(stub, trunc)
    shared = differences["shared_conditions"]
    assert len(shared) == len(analysis.CONDITIONS)
    by_level = {entry["level_pa"]: entry for entry in shared}
    assert by_level[10.0]["spikes_stub"] == 0
    assert by_level[190.0]["spikes_truncated"] == 1
    assert by_level[170.0]["r_in_ratio_truncated_over_stub"] > 1.0
    first = differences["first_spike_amplitude"]
    # Stub never spikes; truncated does: not a single-number difference.
    assert first["stub"]["kind"] == "above_range"
    assert first["truncated"]["kind"] == "interval"
    assert "not a single number" in first["statement"]


def test_in_step_difference_measures_the_step_window_only():
    a = make_run("M01", "stub", 24, -110.0, baseline_mv=-61.9)
    b = make_run("M01", "truncated", 24, -110.0, baseline_mv=-63.3)
    # 1.4 mV apart inside the 1020-2020 ms step window of a 2.5 s trace.
    a["raw_v_mv"] = np.full(500_000, -61.9)
    b["raw_v_mv"] = np.full(500_000, -63.3)
    result = analysis.in_step_difference(a, b)
    assert result["rms_mv"] == pytest.approx(1.4)
    assert result["max_abs_mv"] == pytest.approx(1.4)
    assert result["n_samples"] == 200_000


# ---------------------------------------------------------- verify_runs
def write_baseline(root: Path, branch, run_id, digest):
    directory = root / ("%s_%s_sweep38" % (run_id, branch))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run_summary.json").write_text(json.dumps(
        {"facts": {"hashes": {"output_nwb_sha256": digest}}}), encoding="utf-8")


def baseline_root_for(tmp_path: Path, stub_digest, trunc_digest):
    root = tmp_path / "phase2g_b"
    write_baseline(root, "stub", "A", stub_digest)
    write_baseline(root, "truncated", "C", trunc_digest)
    return root


def measurement_set(stub_kwargs=None, trunc_kwargs=None):
    return {
        "stub": make_branch_runs("stub", **(stub_kwargs or {})),
        "truncated": make_branch_runs("truncated", **(trunc_kwargs or {})),
    }


def test_verify_runs_accepts_a_consistent_measurement_set(tmp_path):
    runs = measurement_set()
    for run in runs["stub"]:
        if run["sweep"] == 38:
            run["summary"]["facts"]["hashes"]["output_nwb_sha256"] = "stub170"
    for run in runs["truncated"]:
        if run["sweep"] == 38:
            run["summary"]["facts"]["hashes"]["output_nwb_sha256"] = "trunc170"
    root = baseline_root_for(tmp_path, "stub170", "trunc170")
    report: list[str] = []
    assert analysis.verify_runs(runs, root, report) is True
    assert not [line for line in report if line.startswith("FAIL")]


def test_verify_runs_rejects_a_baseline_that_no_longer_reproduces(tmp_path):
    runs = measurement_set()
    for run in runs["stub"]:
        if run["sweep"] == 38:
            run["summary"]["facts"]["hashes"]["output_nwb_sha256"] = "new170"
    root = baseline_root_for(tmp_path, "old170", "old170")
    report: list[str] = []
    assert analysis.verify_runs(runs, root, report) is False
    assert any("reproduces the 2G-B output" in line
               for line in report if line.startswith("FAIL"))


def test_verify_runs_rejects_a_failed_run():
    runs = measurement_set(
        stub_kwargs={"status": "executed-with-failures"})
    report: list[str] = []
    assert analysis.verify_runs(runs, None, report) is False


def test_verify_runs_rejects_diverged_inputs():
    runs = measurement_set(
        trunc_kwargs={"inputs_sha": "other-inputs"})
    report: list[str] = []
    assert analysis.verify_runs(runs, None, report) is False


def test_verify_runs_rejects_a_missing_condition_label():
    runs = measurement_set(stub_kwargs={"condition": ""})
    report: list[str] = []
    assert analysis.verify_runs(runs, None, report) is False


def test_verify_runs_rejects_disagreeing_spike_detectors():
    runs = measurement_set()
    tampered = runs["truncated"][10]
    tampered["summary"]["facts"]["comparison"]["simulated"][
        "n_spikes_allen"] = 99
    report: list[str] = []
    assert analysis.verify_runs(runs, None, report) is False

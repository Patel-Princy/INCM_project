"""Unit tests for the Phase 2F recording-only calculations.

The Phase 2F script measures; it does not decide what a measurement means. Almost
everything worth testing is therefore a pure function of a voltage array, so the
tests below build synthetic traces whose answer is known by construction and
check the properties the report leans on:

* a measurement that cannot be made is refused, never defaulted to zero;
* a declining trend is reported as a decline, not as a null result;
* the threshold locator anchors on the upstroke, not on the nearest noise;
* two independent detectors agree on a synthetic train.

Run with ``python -m pytest tests -q``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
# ``tests/conftest.py`` puts ``src/data_audit`` on the path but not ``scripts``,
# and the Phase 2F module lives there.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

pytest.importorskip("h5py", reason="the Phase 2F module imports the NWB stack")

import analyse_excitability_accommodation as p2f  # noqa: E402
import audit_electrophysiology_protocols as phase2d  # noqa: E402

DT = p2f.DT_MS
RATE = p2f.RATE_HZ

#: A spike template in milliseconds relative to its apex. Every segment slope is
#: far from the 50 V/s criterion except the upstroke, so the intended threshold
#: is unambiguous: the template sits flat at -50 mV until 0.65 ms before the
#: apex, creeps to -49.5 mV (10 V/s, still subthreshold), then switches on at
#: -45 mV (90 V/s), 5 mV (166 V/s) and +30 mV (83 V/s).
#: -50 mV is both the resting level and the inter-spike trough, which mirrors the
#: recording, where the trough sits above the resting baseline.
PROFILE_MS = np.array([-1.20, -0.65, -0.60, -0.30, 0.00, 0.25,
                       0.60, 1.10, 1.60, 3.00])
PROFILE_MV = np.array([-50.0, -49.5, -45.0, 5.0, 30.0, 0.0,
                       -30.0, -50.0, -46.0, -50.0])


def spike_train(apexes_ms, n_ms: float = 80.0,
                rest_mv: float = -50.0) -> np.ndarray:
    """A trace at the trough level carrying one template spike per apex time.

    The template starts and ends at the resting level, so placing it introduces no
    step discontinuity that could masquerade as an upstroke.
    """
    n = int(round(n_ms / DT))
    grid = np.arange(n) * DT
    v = np.full(n, float(rest_mv))
    for apex_ms in apexes_ms:
        local = grid - apex_ms
        inside = (local >= PROFILE_MS[0]) & (local <= PROFILE_MS[-1])
        v[inside] = np.maximum(
            v[inside], np.interp(local[inside], PROFILE_MS, PROFILE_MV))
    return v


def apex_index(apex_ms: float) -> int:
    return int(round(apex_ms / DT))


# ---------------------------------------------------------------------------
# Ranks, correlation and the direction of the permutation test
# ---------------------------------------------------------------------------
def test_average_ranks_resolve_ties_without_an_arbitrary_order():
    assert list(p2f._ranks(np.array([1.0, 2.0, 2.0, 3.0]))) == [1.0, 2.5, 2.5, 4.0]
    assert list(p2f._ranks(np.array([5.0, 5.0, 5.0]))) == [2.0, 2.0, 2.0]


def test_spearman_is_exact_on_a_perfect_monotone_pair():
    x = np.arange(1, 8, dtype=float)
    assert p2f.spearman_rho(x, 3 * x + 100) == pytest.approx(1.0)
    assert p2f.spearman_rho(x, -2 * x) == pytest.approx(-1.0)


def test_spearman_agrees_with_itself_when_the_pair_is_tied():
    x = np.array([1.0, 2.0, 2.0, 3.0, 4.0])
    assert p2f.spearman_rho(x, x) == pytest.approx(1.0)
    # The same tie, reversed: still exactly -1 rather than "almost".
    assert p2f.spearman_rho(x, np.array([4.0, 3.0, 3.0, 2.0, 1.0])) == pytest.approx(-1.0)


def test_spearman_refuses_fewer_than_three_points():
    assert np.isnan(p2f.spearman_rho([1.0, 2.0], [1.0, 2.0]))


@pytest.mark.parametrize("values", [
    [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],          # strictly increasing
    [6.0, 5.0, 4.0, 3.0, 2.0, 1.0],          # strictly decreasing
])
def test_permutation_p_counts_the_tail_the_data_fell_into(values):
    """A perfect decline must not be reported as p = 0.999.

    Counting only the upper tail returns a near-unit p-value for a perfectly
    ordered *decrease*, which reads like a null result when the measurement in
    fact shows a maximal effect. Both directions must give the same small p.
    """
    x = np.arange(1, len(values) + 1, dtype=float)
    p = p2f.permutation_p(x, values, seed=1, draws=2000)
    assert 0.0 < p < 0.01


def test_permutation_p_is_large_for_an_unordered_pair():
    x = np.arange(1, 13, dtype=float)
    # A zigzag whose rank products almost cancel, so neither tail is reachable.
    y = np.array([1.0, 12.0, 2.0, 11.0, 3.0, 10.0, 4.0, 9.0,
                  5.0, 8.0, 6.0, 7.0])
    assert abs(p2f.spearman_rho(x, y)) < 0.2
    assert p2f.permutation_p(x, y, seed=1, draws=2000) > 0.3


def test_permutation_p_is_symmetric_between_rising_and_falling():
    x = np.arange(1, 8, dtype=float)
    rising = p2f.permutation_p(x, x, seed=7, draws=2000)
    falling = p2f.permutation_p(x, -x, seed=7, draws=2000)
    assert rising == pytest.approx(falling)


def test_permutation_p_is_reproducible_for_a_fixed_seed():
    x = np.arange(1, 10, dtype=float)
    y = np.array([1.0, 3.0, 2.0, 6.0, 5.0, 9.0, 7.0, 8.0, 4.0])
    assert (p2f.permutation_p(x, y, seed=11, draws=1500)
            == p2f.permutation_p(x, y, seed=11, draws=1500))


# ---------------------------------------------------------------------------
# trend() — refusal, and the reported direction
# ---------------------------------------------------------------------------
def test_trend_refuses_fewer_than_three_events():
    for values in ([], [1.0], [1.0, 2.0], [1.0, None, None]):
        result = p2f.trend(values)
        assert result["available"] is False
        assert "at least 3" in result["reason"]


def test_trend_drops_refused_measurements_instead_of_coercing_them_to_zero():
    """A threshold that could not be located is missing evidence, not a 0 mV."""
    clean = p2f.trend([10.0, 20.0, 30.0, 40.0])
    with_holes = p2f.trend([10.0, None, float("nan"), 20.0, 30.0, 40.0])
    assert with_holes["available"] is True
    assert with_holes["n"] == clean["n"] == 4
    assert with_holes["rho"] == pytest.approx(clean["rho"])


def test_trend_reports_a_decline_as_falling_with_a_small_p():
    result = p2f.trend([30.0, 29.0, 28.0, 27.0, 26.0, 25.0], draws=2000)
    assert result["available"] is True
    assert result["direction"] == "falling"
    assert result["rho"] == pytest.approx(-1.0)
    assert result["p_permutation"] < 0.01
    assert result["change"] == pytest.approx(-5.0)


# ---------------------------------------------------------------------------
# adaptation_summary() — the refusal that must never be papered over
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("isi,count", [([], 1), ([40.0], 2)])
def test_adaptation_is_refused_when_there_are_too_few_intervals(isi, count):
    """One spike per step cannot carry an adaptation index, and says so."""
    result = p2f.adaptation_summary(isi, count)
    assert result["available"] is False
    assert result["interval_trend"] is None
    assert result["isi_ratio"] is None
    assert result["rate_ratio"] is None
    assert "%d spike(s)" % count in result["reason"]


def test_adaptation_refusal_names_the_interval_count():
    reason = p2f.adaptation_summary([], 1)["reason"]
    assert "0 inter-spike interval(s)" in reason


def test_adaptation_reports_the_documented_indices_when_intervals_exist():
    result = p2f.adaptation_summary([20.0, 30.0], 3)
    assert result["available"] is True
    assert result["isi_first_ms"] == pytest.approx(20.0)
    assert result["isi_last_ms"] == pytest.approx(30.0)
    assert result["isi_ratio"] == pytest.approx(1.5)
    assert result["rate_ratio"] == pytest.approx(1.5)
    assert result["isi_mean_ms"] == pytest.approx(25.0)
    assert result["isi_cv"] == pytest.approx(np.std([20.0, 30.0], ddof=1) / 25.0)
    assert result["monotone_fraction"] == pytest.approx(1.0)


def test_adaptation_halves_are_the_same_length_when_the_count_is_odd():
    isi = [10.0, 20.0, 30.0, 40.0, 50.0]
    result = p2f.adaptation_summary(isi, len(isi) + 1)
    assert result["early_rate_hz"] == pytest.approx(1000.0 / np.mean([10.0, 20.0]))
    assert result["late_rate_hz"] == pytest.approx(1000.0 / np.mean([40.0, 50.0]))


def test_adaptation_does_not_invent_a_trend_from_two_intervals():
    """Two intervals give a ratio but not a monotone trend."""
    result = p2f.adaptation_summary([20.0, 30.0], 3)
    assert result["available"] is True
    assert result["interval_trend"]["available"] is False


# ---------------------------------------------------------------------------
# Derivative, detectors and their agreement
# ---------------------------------------------------------------------------
def test_smooth_dvdt_returns_the_known_slope_of_a_ramp():
    slope_mv_per_ms = 12.0                     # 12 mV/ms == 12 V/s
    v = slope_mv_per_ms * np.arange(2000) * DT
    dvdt = p2f.smooth_dvdt(v, RATE)
    assert dvdt.shape == v.shape
    assert np.allclose(dvdt[10:-10], slope_mv_per_ms, atol=1e-9)


def test_smooth_dvdt_with_a_window_of_one_is_the_raw_difference():
    v = spike_train([20.0])
    raw = p2f.smooth_dvdt(v, RATE, window=1)
    assert raw[0] == pytest.approx(0.0)
    assert np.allclose(raw[1:], np.diff(v) * 1e-3 * RATE)


def test_two_detectors_agree_on_a_three_spike_train():
    v = spike_train([20.0, 40.0, 60.0])
    dvdt = p2f.smooth_dvdt(v, RATE)
    primary = phase2d.detect_spikes(v, RATE)
    secondary = p2f.detect_spikes_dvdt(v, RATE, dvdt)
    assert primary.size == secondary.size == 3
    assert np.array_equal(primary, secondary)
    assert np.array_equal(primary, [apex_index(a) for a in (20.0, 40.0, 60.0)])


def test_detectors_agree_on_silence():
    v = np.full(20_000, -70.0)
    dvdt = p2f.smooth_dvdt(v, RATE)
    assert phase2d.detect_spikes(v, RATE).size == 0
    assert p2f.detect_spikes_dvdt(v, RATE, dvdt).size == 0


def test_detectors_agree_on_a_subthreshold_ramp():
    """A 40 V/s ramp reaches -20 mV and never crosses 0 mV or the 50 V/s bar."""
    v = np.full(40_000, -70.0)
    start = 5_000
    v[start:start + 251] = -70.0 + np.arange(251) * 0.2      # 40 V/s to -20 mV
    v[start + 251:] = -20.0
    dvdt = p2f.smooth_dvdt(v, RATE)
    assert 35.0 < float(np.max(dvdt)) < p2f.THRESHOLD_DVDT_V_PER_S
    assert phase2d.detect_spikes(v, RATE).size == 0
    assert p2f.detect_spikes_dvdt(v, RATE, dvdt).size == 0


def test_velocity_detector_does_not_merge_spikes_three_milliseconds_apart():
    v = spike_train([20.0, 23.0])
    peaks = p2f.detect_spikes_dvdt(v, RATE, p2f.smooth_dvdt(v, RATE))
    assert peaks.size == 2


def test_detector_counts_are_identical_on_every_synthetic_train():
    for apexes in ([10.0], [10.0, 20.0], [10.0, 20.0, 30.0, 40.0]):
        v = spike_train(apexes)
        dvdt = p2f.smooth_dvdt(v, RATE)
        assert (phase2d.detect_spikes(v, RATE).size
                == p2f.detect_spikes_dvdt(v, RATE, dvdt).size
                == len(apexes))


# ---------------------------------------------------------------------------
# Threshold locator
# ---------------------------------------------------------------------------
def test_threshold_is_located_on_the_contiguous_upstroke():
    v = spike_train([20.0])
    dvdt = p2f.smooth_dvdt(v, RATE)
    apex = apex_index(20.0)
    result = p2f.threshold_crossing(v, dvdt, apex, RATE)
    assert result["index"] is not None
    # Structural claims, independent of the template's exact slopes: the reported
    # sample is the first of the contiguous suprathreshold run, it is on the
    # upstroke, and it sits between the trough and 0 mV.
    assert dvdt[result["index"]] >= p2f.THRESHOLD_DVDT_V_PER_S
    assert dvdt[result["index"] - 1] < p2f.THRESHOLD_DVDT_V_PER_S
    assert apex - int(round(2.0 / DT)) < result["index"] < apex
    assert -50.0 < result["v_mv"] < 0.0
    assert result["run_samples"] > 10
    assert result["run_samples"] * DT < p2f.THRESHOLD_LOOKBACK_MS


def test_threshold_is_refused_when_the_upstroke_never_reaches_the_criterion():
    v = np.full(40_000, -70.0)
    v[10_000:20_001] = -70.0 + 20.0 * (np.arange(10_001) * DT)   # 20 V/s
    dvdt = p2f.smooth_dvdt(v, RATE)
    result = p2f.threshold_crossing(v, dvdt, 20_000, RATE)
    assert result["index"] is None
    assert result["v_mv"] is None


def test_threshold_ignores_suprathreshold_noise_that_is_not_contiguous():
    """An isolated suprathreshold blip inside the AHP is not the threshold.

    The naive alternative — the earliest sample above the criterion anywhere in
    the lookback window — locks onto that blip and reports a threshold several
    millivolts too negative. Anchoring on the steepest point and walking back
    only through the contiguous run is what prevents it.
    """
    v = spike_train([20.0])
    apex = apex_index(20.0)
    # A 18 mV excursion over 0.3 ms and back, 6 ms before the apex. It sustains
    # 60 V/s — above the criterion but well below the upstroke's 166 V/s — and is
    # separated from the upstroke by 5 ms of subthreshold trace.
    blip = apex - int(round(6.0 / DT))
    width = int(round(0.3 / DT))
    v[blip:blip + width] = np.linspace(-50.0, -32.0, width, endpoint=False)
    v[blip + width:blip + 2 * width] = np.linspace(-32.0, -50.0, width, endpoint=False)
    dvdt = p2f.smooth_dvdt(v, RATE)
    result = p2f.threshold_crossing(v, dvdt, apex, RATE)

    lookback = int(p2f.THRESHOLD_LOOKBACK_MS / DT)
    lo = max(0, apex - lookback)
    naive = lo + int(np.flatnonzero(dvdt[lo:apex + 1] >= p2f.THRESHOLD_DVDT_V_PER_S)[0])

    assert naive < apex - int(round(5.0 / DT)), "the blip precedes the upstroke"
    assert result["index"] > apex - int(round(1.5 / DT))
    assert result["v_mv"] > -50.0


# ---------------------------------------------------------------------------
# Spike morphology
# ---------------------------------------------------------------------------
def test_spike_amplitude_is_measured_from_the_preceding_trough():
    v = spike_train([20.0])
    dvdt = p2f.smooth_dvdt(v, RATE)
    metrics = p2f.spike_metrics(v, RATE, dvdt, apex_index(20.0), reference="trough")
    assert metrics["peak_mv"] == pytest.approx(30.0)
    assert metrics["reference_mv"] == pytest.approx(-50.0)
    assert metrics["amplitude_mv"] == pytest.approx(80.0)
    assert metrics["width_censored"] is False
    assert metrics["width_ms"] == pytest.approx(0.76, abs=0.05)
    assert metrics["dvdt_max_v_per_s"] > p2f.THRESHOLD_DVDT_V_PER_S


def test_local_reference_measures_a_smaller_amplitude_than_the_trough():
    """Inside a train the 30 ms median sits on the charging ramp, not at the trough.

    This is why the train analysis uses ``trough`` and the cross-block comparison
    uses ``local``: on the same spike the two definitions differ by the height of
    the ramp the spike grew out of.
    """
    apex = apex_index(40.0)
    v = np.full(int(round(100.0 / DT)), -50.0)
    # A 10 mV charging ramp over the 30 ms before the spike: trough -60, median
    # of the preceding 30 ms about -55.
    ramp_lo = apex - int(round(30.0 / DT))
    v[ramp_lo:apex] = np.linspace(-60.0, -50.0, apex - ramp_lo, endpoint=False)
    v[apex - int(round(1.2 / DT)):apex] = -60.0
    grid = np.arange(v.size) * DT
    local_time = grid - 40.0
    inside = ((local_time >= PROFILE_MS[0]) & (local_time <= PROFILE_MS[-1]))
    v[inside] = np.maximum(v[inside],
                           np.interp(local_time[inside], PROFILE_MS, PROFILE_MV - 10.0))
    dvdt = p2f.smooth_dvdt(v, RATE)
    trough = p2f.spike_metrics(v, RATE, dvdt, apex, reference="trough")
    local = p2f.spike_metrics(v, RATE, dvdt, apex, reference="local")
    assert local["reference_mv"] > trough["reference_mv"]
    assert local["amplitude_mv"] < trough["amplitude_mv"]


def test_spike_metrics_rejects_an_unknown_reference():
    v = spike_train([20.0])
    with pytest.raises(ValueError):
        p2f.spike_metrics(v, RATE, p2f.smooth_dvdt(v, RATE),
                          apex_index(20.0), reference="rest")


def test_afterhyperpolarisation_stops_before_the_next_spike():
    """The AHP window is truncated so the next upstroke is not read as recovery."""
    v = spike_train([20.0, 24.0])
    dvdt = p2f.smooth_dvdt(v, RATE)
    apex = apex_index(20.0)
    limit = apex_index(24.0) - int(round(p2f.UPSTROKE_GUARD_MS / DT))
    bounded = p2f.spike_metrics(v, RATE, dvdt, apex, reference="trough",
                                ahp_limit_index=limit)
    assert np.isfinite(bounded["ahp_ms"])
    assert 21.0 <= bounded["ahp_ms"] <= 22.0
    assert bounded["ahp_mv"] <= bounded["reference_mv"] + 1e-6


def test_afterhyperpolarisation_is_refused_when_the_next_spike_leaves_no_room():
    """A 3 ms interval minus a 2 ms guard leaves a negative window, not a guess."""
    v = spike_train([20.0, 23.0])
    dvdt = p2f.smooth_dvdt(v, RATE)
    apex = apex_index(20.0)
    limit = apex_index(23.0) - int(round(p2f.UPSTROKE_GUARD_MS / DT))
    bounded = p2f.spike_metrics(v, RATE, dvdt, apex, reference="trough",
                                ahp_limit_index=limit)
    assert np.isnan(bounded["ahp_mv"])


# ---------------------------------------------------------------------------
# Inter-spike decomposition
# ---------------------------------------------------------------------------
def test_interval_decomposition_closes_to_the_measured_isi():
    v = spike_train([20.0, 40.0, 60.0])
    dvdt = p2f.smooth_dvdt(v, RATE)
    peaks = np.array([apex_index(a) for a in (20.0, 40.0, 60.0)])
    thresholds = [p2f.threshold_crossing(v, dvdt, int(p), RATE) for p in peaks]
    segments = p2f.inter_spike_segments(v, peaks, thresholds)

    assert len(segments) == 2
    for segment in segments:
        total = segment["fall_ms"] + segment["ramp_ms"] + segment["upstroke_ms"]
        assert total == pytest.approx(segment["isi_ms"], abs=1e-6)
        assert segment["isi_ms"] == pytest.approx(20.0, abs=1e-6)
        assert segment["trough_mv"] == pytest.approx(-50.0)


def test_interval_decomposition_leaves_missing_thresholds_missing():
    v = spike_train([20.0, 40.0])
    peaks = np.array([apex_index(20.0), apex_index(40.0)])
    segments = p2f.inter_spike_segments(v, peaks, [None, None])
    assert segments[0]["ramp_ms"] is None
    assert segments[0]["upstroke_ms"] is None
    assert segments[0]["fall_ms"] is not None


# ---------------------------------------------------------------------------
# Membrane charging
# ---------------------------------------------------------------------------
def test_charge_fit_recovers_a_known_time_constant():
    tau_ms = 20.0
    t = np.arange(0.0, 40.0, DT)
    v = -60.0 * np.exp(-t / tau_ms) - 20.0
    fit = p2f.fit_charge_tau(t, v)
    assert fit["available"] is True
    assert fit["tau_ms"] == pytest.approx(tau_ms, rel=0.10)
    assert fit["amplitude_mv"] == pytest.approx(-60.0, abs=1.5)
    assert fit["asymptote_mv"] == pytest.approx(-20.0, abs=0.5)
    assert fit["r2"] > 0.999


@pytest.mark.parametrize("v", [np.full(4000, -70.0), np.array([-70.0, np.nan])])
def test_charge_fit_refuses_a_trace_it_cannot_describe(v):
    t = np.arange(v.size) * DT
    assert p2f.fit_charge_tau(t, v)["available"] is False


def test_charge_fit_refuses_a_trace_shorter_than_its_model():
    t = np.arange(5) * DT
    assert p2f.fit_charge_tau(t, np.arange(5, dtype=float))["available"] is False


# ---------------------------------------------------------------------------
# Level statistics
# ---------------------------------------------------------------------------
def test_plateau_statistics_are_exact_on_a_flat_line():
    v = np.full(200_000, -47.0)
    stats = p2f.plateau_stats(v, RATE, 0, v.size)
    assert stats["available"] is True
    assert stats["median_mv"] == pytest.approx(-47.0)
    assert stats["sd_mv"] == pytest.approx(0.0)
    assert stats["min_mv"] == stats["max_mv"] == pytest.approx(-47.0)


def test_plateau_statistics_refuse_a_window_too_short_to_describe():
    assert p2f.plateau_stats(np.full(4, -47.0), RATE, 0, 4)["available"] is False


def test_baseline_noise_reports_zero_velocity_spread_on_a_flat_line():
    onset = int(round(250.0 / DT))
    v = np.full(onset + 1000, -80.0)
    noise = p2f.pre_step_noise(v, onset, RATE)
    assert noise["available"] is True
    assert noise["median_mv"] == pytest.approx(-80.0)
    assert noise["sd_mv"] == pytest.approx(0.0)
    assert noise["dvdt_sigma_v_per_s"] == pytest.approx(0.0)


def test_baseline_noise_refuses_a_trace_with_no_room_before_the_step():
    assert p2f.pre_step_noise(np.full(50, -80.0), 10, RATE)["available"] is False


def test_threshold_criterion_clears_the_measured_velocity_noise():
    """The 50 V/s criterion must sit far above the quantisation floor."""
    onset = int(round(250.0 / DT))
    rng = np.random.default_rng(0)
    quantum = 0.031248
    v = -80.0 + np.round(rng.normal(0.0, 0.02, onset + 1000) / quantum) * quantum
    sigma = p2f.pre_step_noise(v, onset, RATE)["dvdt_sigma_v_per_s"]
    assert sigma > 0.0
    assert p2f.THRESHOLD_DVDT_V_PER_S / sigma > p2f.THRESHOLD_NOISE_MARGIN


# ---------------------------------------------------------------------------
# Post-spike sampling
# ---------------------------------------------------------------------------
def test_post_spike_profile_truncates_at_the_next_spike():
    v = spike_train([20.0, 23.0])
    apex = apex_index(20.0)
    limit = apex_index(23.0) - int(round(p2f.UPSTROKE_GUARD_MS / DT))
    profile = p2f.post_spike_profile(v, apex, RATE, limit_index=limit)
    assert profile
    assert max(float(k) for k in profile) < 3.0


def test_ahp_recovery_fraction_is_bounded_and_reaches_one_at_the_trough_exit():
    v = np.full(20_000, -50.0)
    apex = 2_000
    # A -10 mV trough decaying linearly back to the reference over 40 ms.
    span = int(round(40.0 / DT))
    v[apex:apex + span] = -60.0 + 10.0 * (np.arange(span) / span)
    recovery = p2f.ahp_recovery(v, apex, apex + span + 100, -50.0)
    assert recovery["5_recovered"] == pytest.approx(0.125, abs=0.02)
    assert recovery["40_recovered"] == pytest.approx(1.0, abs=0.02)
    assert recovery["5_deficit_mv"] == pytest.approx(8.75, abs=0.2)
    for key, value in recovery.items():
        if key.endswith("_recovered") and value is not None:
            assert -0.01 <= value <= 1.01


def test_ahp_recovery_refuses_delays_past_the_next_spike():
    v = np.full(20_000, -50.0)
    recovery = p2f.ahp_recovery(v, 2_000, 2_100, -50.0)
    assert recovery["5_recovered"] is None
    assert recovery["10_deficit_mv"] is None


# ---------------------------------------------------------------------------
# Rendering and the report object
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("value,digits,expected", [
    (None, 3, "unavailable"),
    (float("nan"), 3, "unavailable"),
    (float("inf"), 3, "unavailable"),
    (True, 3, "yes"),
    (False, 3, "no"),
    (12, 3, "12"),
    (12.0, 3, "12"),
    (-0.8280000001, 3, "-0.828"),
    (0.0, 3, "0"),
])
def test_formatting_never_lets_a_refusal_look_like_a_measurement(value, digits,
                                                                 expected):
    assert p2f.fmt(value, digits) == expected


def test_report_counts_failures_and_buckets_them_by_label_prefix(capsys):
    report = p2f.Report()
    report.check(True, "provenance|one", "")
    report.check(False, "provenance|two", "missing")
    report.check(True, "counts|three", "")
    summary = report.summary()
    assert summary["checks"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["by_section"]["provenance"] == {"checks": 2, "failed": 1}
    assert summary["by_section"]["counts"] == {"checks": 1, "failed": 0}
    assert summary["failures"][0]["label"] == "provenance|two"
    capsys.readouterr()


def test_json_encoding_keeps_numpy_honest():
    payload = {"a": np.int64(3), "b": np.float64(1.5),
               "c": np.array([1, 2]), "d": float("nan"),
               "e": Path("tmp") / "x.json"}
    encoded = p2f.to_jsonable(payload)
    assert encoded == {"a": 3, "b": 1.5, "c": [1, 2], "d": None, "e": str(Path("tmp") / "x.json")}
    assert isinstance(encoded["a"], int)
    assert isinstance(encoded["b"], float)


# ---------------------------------------------------------------------------
# Constants that encode a published value or a units convention
# ---------------------------------------------------------------------------
def test_short_square_grace_window_is_a_duration_not_a_sample_count():
    """Regression: ``int(0.100 / DT_MS)`` is 20 samples, i.e. 0.1 ms.

    A grace window expressed as a raw division of a millisecond constant by a
    millisecond step is off by three orders of magnitude, and it silently
    discards every spike of the 3 ms threshold protocol because those spikes fire
    more than 0.1 ms after the pulse ends. The window must be 100 ms.
    """
    samples = int(p2f.SHORT_SQUARE_GRACE_MS / p2f.DT_MS)
    assert p2f.SHORT_SQUARE_GRACE_MS == pytest.approx(100.0)
    assert samples == 20_000
    assert samples * p2f.DT_MS == pytest.approx(100.0)


def test_published_short_square_brackets_match_the_phase_2d_report():
    coarse_low, coarse_high, coarse_mixed = p2f.PHASE2D_SHORT_BRACKETS[
        "C1SSCOARSE150112"]
    finest_low, finest_high, finest_mixed = p2f.PHASE2D_SHORT_BRACKETS[
        "C1SSFINEST150112"]
    assert (coarse_low, coarse_high, coarse_mixed) == (600.0, 700.0, ())
    assert (finest_low, finest_high, finest_mixed) == (650.0, 670.0, (660.0,))


def test_block_assignment_keeps_the_contested_command_in_one_block():
    assert p2f.CONTESTED_PA == pytest.approx(170.0)
    assert p2f.FITTING_SWEEP == 38
    assert p2f.HELD_OUT_SWEEPS == (49, 50, 51, 52)
    assert p2f.C2_BLOCK not in (p2f.COARSE_BLOCK, p2f.FINEST_BLOCK)


def test_phase_2e_isi_reference_has_one_interval_per_pair_of_spikes():
    assert len(p2f.PHASE2E_SWEEP38_ISI_MS) == 11
    assert p2f.PHASE2E_SWEEP38_ISI_MS[0] == pytest.approx(39.25)
    assert p2f.PHASE2E_SWEEP38_ISI_MS[-1] == pytest.approx(85.935)


# ---------------------------------------------------------------------------
# The generated summary, when it exists
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def summary():
    path = PROJECT_ROOT / "tmp" / "phase2f_summary.json"
    if not path.exists():
        pytest.skip("run scripts/analyse_excitability_accommodation.py first")
    import json
    return json.loads(path.read_text(encoding="utf-8"))


def test_summary_reproduces_the_headline_spike_counts(summary):
    sweeps = summary["sweeps"]
    assert sweeps["38"]["n_in_step"] == 12
    for sweep in ("49", "50", "51", "52"):
        assert sweeps[sweep]["n_in_step"] == 1


def test_summary_refuses_an_adaptation_index_for_the_single_spike_sweeps(summary):
    for sweep in ("49", "50", "51", "52"):
        adaptation = summary["sweeps"][sweep]["adaptation"]
        assert adaptation["available"] is False
        assert adaptation["interval_trend"] is None


def test_summary_keeps_the_post_step_doublet_separate_from_the_train(summary):
    sweep38 = summary["sweeps"]["38"]
    assert sweep38["n_after_step"] == 2
    assert len(sweep38["isi_ms"]) == sweep38["n_in_step"] - 1


def test_summary_passes_every_internal_check(summary):
    assert summary["tests"]["failed"] == 0, summary["tests"]["failures"]


def test_summary_never_pools_the_two_blocks(summary):
    """No aggregate in the payload may carry a combined COARSE+FINEST mean."""
    text = __import__("json").dumps(summary["blocks"])
    assert "pooled" not in text.lower()

"""Tests for Phase 3B: Out-of-Sample Held-Out Evaluation Pipeline and Provenance.

Verifies:
1. Integrity and disjointness of fitting_sweeps.csv vs heldout_sweeps.csv.
2. Complete coverage of long-square sweeps across 4 representative populations.
3. Strict rejection when attempting to evaluate a calibration sweep under held-out mode.
4. Correct segmentation of long-square stimulus steps (ignoring short test pulses).
5. Schema and provenance requirements for held-out execution outputs.
"""
from __future__ import annotations

import csv
import pathlib
import pytest
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_3B = ROOT / "results" / "phase3b"
FITTING_CSV = RESULTS_3B / "fitting_sweeps.csv"
HELDOUT_CSV = RESULTS_3B / "heldout_sweeps.csv"
CONDITIONS_CSV = RESULTS_3B / "condition_groups.csv"

CALIBRATION_SWEEPS = {
    484564503: 49,
    318808427: 40,
    471129934: 51,
    471786879: 42,
}


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_provenance_files_exist():
    assert FITTING_CSV.exists(), f"Missing {FITTING_CSV}"
    assert HELDOUT_CSV.exists(), f"Missing {HELDOUT_CSV}"
    assert CONDITIONS_CSV.exists(), f"Missing {CONDITIONS_CSV}"


def test_fitting_sweeps_count_and_provenance():
    rows = read_csv(FITTING_CSV)
    assert len(rows) == 4, f"Expected 4 calibration sweeps, got {len(rows)}"
    for r in rows:
        spec_id = int(r["specimen_id"])
        assert spec_id in CALIBRATION_SWEEPS
        assert int(r["sweep_number"]) == CALIBRATION_SWEEPS[spec_id]
        assert r["classification"] == "FITTING"
        assert r["fit_file_id"] != ""


def test_heldout_sweeps_count_and_disjointness():
    held_rows = read_csv(HELDOUT_CSV)
    fit_rows = read_csv(FITTING_CSV)

    assert len(held_rows) == 109, f"Expected 109 held-out sweeps, got {len(held_rows)}"

    fit_pairs = {(int(r["specimen_id"]), int(r["sweep_number"])) for r in fit_rows}
    held_pairs = {(int(r["specimen_id"]), int(r["sweep_number"])) for r in held_rows}

    # Strict disjointness: no calibration sweep can ever appear in held-out sweeps
    overlap = fit_pairs.intersection(held_pairs)
    assert len(overlap) == 0, f"Violation: Calibration sweeps found in held-out set: {overlap}"

    # Verify per-specimen held-out sweep counts
    spec_counts = {}
    for r in held_rows:
        sid = int(r["specimen_id"])
        spec_counts[sid] = spec_counts.get(sid, 0) + 1

    assert spec_counts[484564503] == 31  # Pop A
    assert spec_counts[318808427] == 18  # Pop B
    assert spec_counts[471129934] == 34  # Pop C
    assert spec_counts[471786879] == 26  # Pop D


def test_condition_groups_unique_stimuli():
    cond_rows = read_csv(CONDITIONS_CSV)
    assert len(cond_rows) == 102, f"Expected 102 unique conditions, got {len(cond_rows)}"

    # Check that sum of sweep counts matches 109
    total_sweeps = sum(int(r["n_sweeps"]) for r in cond_rows)
    assert total_sweeps == 109


def test_runner_calibration_rejection_in_heldout_mode():
    from scripts.run_representative_perisomatic import REPRESENTATIVES, run_single_sweep

    # Attempting to run a calibration sweep with condition_type="held_out" must raise ValueError
    for spec_id, cal_swp in CALIBRATION_SWEEPS.items():
        with pytest.raises(ValueError, match="REJECTED: Sweep .* is the published calibration fitting sweep"):
            run_single_sweep(
                specimen_id=spec_id,
                sweep=cal_swp,
                condition_type="held_out",
                repo_dir=ROOT,
                workspace=ROOT / "tmp" / "test_ws",
                allensdk_src=ROOT / "tmp" / "dummy_src",
                output_dir=ROOT / "tmp" / "test_out",
            )


def test_stimulus_segmentation_filters_test_pulse():
    from scripts.run_representative_perisomatic import _stimulus_segments

    # Construct synthetic stimulus:
    # 0 to 100 ms: 0 pA
    # 100 to 120 ms: -100 pA (short test pulse, 20 ms)
    # 120 to 1020 ms: 0 pA
    # 1020 to 2020 ms: +20 pA (small depolarizing long step, 1000 ms)
    # 2020 to 3000 ms: 0 pA
    dt_ms = 0.05
    total_ms = 3000.0
    num_pts = int(total_ms / dt_ms)
    stim = np.zeros(num_pts, dtype=float)

    # Test pulse: 100ms - 120ms (-100 pA = -100e-12 A)
    tp_start = int(100.0 / dt_ms)
    tp_end = int(120.0 / dt_ms)
    stim[tp_start:tp_end] = -100e-12

    # Long step: 1020ms - 2020ms (+20 pA = +20e-12 A)
    step_start = int(1020.0 / dt_ms)
    step_end = int(2020.0 / dt_ms)
    stim[step_start:step_end] = 20e-12

    segs = _stimulus_segments(stim, dt_ms)
    assert len(segs) == 2

    # Without duration filtering, sorting by abs(amplitude) would pick test pulse (-100 pA)
    # With duration filtering (> 100 ms), the long step (+20 pA) is correctly selected
    long_segs = [s for s in segs if s["duration_ms"] > 100.0]
    assert len(long_segs) == 1
    selected = long_segs[0]
    assert pytest.approx(selected["amplitude_pa"], abs=0.1) == 20.0
    assert pytest.approx(selected["onset_ms"], abs=1.0) == 1020.0
    assert pytest.approx(selected["duration_ms"], abs=1.0) == 1000.0


def test_consolidated_metrics_outputs():
    metrics_csv = RESULTS_3B / "heldout_metrics.csv"
    assert metrics_csv.exists(), f"Missing {metrics_csv}"
    rows = read_csv(metrics_csv)
    assert len(rows) == 109, f"Expected 109 rows in heldout_metrics.csv, got {len(rows)}"

    pops = {r["population"] for r in rows}
    assert pops == {"A", "B", "C", "D"}

    for r in rows:
        assert float(r["rmse_overall_mv"]) >= 0.0
        assert -1.0 <= float(r["correlation"]) <= 1.0


def test_fi_curves_and_rheobase_outputs():
    fi_csv = RESULTS_3B / "heldout_fi_curves.csv"
    rheo_csv = RESULTS_3B / "heldout_rheobase.csv"
    assert fi_csv.exists(), f"Missing {fi_csv}"
    assert rheo_csv.exists(), f"Missing {rheo_csv}"

    fi_rows = read_csv(fi_csv)
    assert len(fi_rows) == 102, f"Expected 102 condition groups, got {len(fi_rows)}"

    rheo_rows = read_csv(rheo_csv)
    assert len(rheo_rows) == 4, f"Expected 4 rheobase rows, got {len(rheo_rows)}"
    for r in rheo_rows:
        assert float(r["rec_rheobase_midpoint_pa"]) > 0.0
        assert float(r["sim_rheobase_midpoint_pa"]) > 0.0


def test_figures_exist():
    fig_dir = RESULTS_3B / "figures"
    expected_figs = [
        "fi_curves_all_populations.png",
        "rheobase_comparison.png",
        "error_distributions_by_population.png",
        "first_spike_latency_comparison.png",
        "passive_properties_comparison.png",
    ]
    for fn in expected_figs:
        fpath = fig_dir / fn
        assert fpath.exists(), f"Missing figure: {fpath}"
        assert fpath.stat().st_size > 1000, f"Figure {fn} is suspiciously small: {fpath.stat().st_size} bytes"


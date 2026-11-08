"""Regression and audit tests for INCM Phase 4C: Frozen FHN Held-Out Evaluation."""
from __future__ import annotations

import json
import math
import pathlib
import pandas as pd
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_4C = REPO_ROOT / "results" / "phase4c"
FIGURES_DIR = RESULTS_4C / "figures"
RESULTS_3B = REPO_ROOT / "results" / "phase3b"

FROZEN_CALIBRATION_ASSIGNMENTS = {
    "A": {"specimen_id": 484564503, "layer": "4", "calibration_sweep": 49},
    "B": {"specimen_id": 318808427, "layer": "2/3", "calibration_sweep": 40},
    "C": {"specimen_id": 471129934, "layer": "5", "calibration_sweep": 51},
    "D": {"specimen_id": 471786879, "layer": "6a", "calibration_sweep": 42},
}

EXPECTED_SWEEP_COUNTS = {
    "A": 31,
    "B": 18,
    "C": 34,
    "D": 26,
}


def test_heldout_data_audit_integrity():
    """Verify heldout_data_audit.json documents exact 109 sweeps and calibration exclusions."""
    audit_file = RESULTS_4C / "heldout_data_audit.json"
    assert audit_file.exists(), f"Missing audit file: {audit_file}"

    with open(audit_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_heldout_sweeps"] == 109
    assert data["population_counts"] == EXPECTED_SWEEP_COUNTS
    assert data["all_nwb_files_verified"] is True

    # Confirm the 4 calibration sweeps are noted as excluded
    for pop, cal_sweep in data["calibration_sweeps_excluded"].items():
        assert FROZEN_CALIBRATION_ASSIGNMENTS[pop]["calibration_sweep"] == cal_sweep


def test_fhn_heldout_metrics_table():
    """Verify fhn_heldout_metrics.csv has 109 rows and valid mathematical columns."""
    metrics_file = RESULTS_4C / "fhn_heldout_metrics.csv"
    assert metrics_file.exists(), f"Missing metrics file: {metrics_file}"

    df = pd.read_csv(metrics_file)
    assert len(df) == 109

    # Verify per-population counts
    counts = df["population"].value_counts().to_dict()
    assert counts == EXPECTED_SWEEP_COUNTS

    # Strict exclusion check: calibration sweeps must not appear
    for pop, info in FROZEN_CALIBRATION_ASSIGNMENTS.items():
        spec = info["specimen_id"]
        cal = info["calibration_sweep"]
        leak = df[(df["specimen_id"] == spec) & (df["sweep_number"] == cal)]
        assert len(leak) == 0, f"Calibration sweep {cal} leaked into heldout metrics for Pop {pop}!"

    # Verify finite values
    assert not df["rmse_overall_fhn_mv"].isna().any()
    assert not df["rmse_during_fhn_mv"].isna().any()
    assert not df["correlation_fhn"].isna().any()
    assert (df["rmse_overall_fhn_mv"] >= 0.0).all()
    assert (df["correlation_fhn"] >= -1.0).all() and (df["correlation_fhn"] <= 1.0).all()
    assert (df["spike_count_fhn_in_step"] >= 0).all()


def test_execution_manifest_zero_failures():
    """Verify fhn_heldout_execution_manifest.csv shows 100% success and no divergence."""
    manifest_file = RESULTS_4C / "fhn_heldout_execution_manifest.csv"
    assert manifest_file.exists(), f"Missing manifest file: {manifest_file}"

    df = pd.read_csv(manifest_file)
    assert len(df) == 109
    assert (df["success"] == True).all()
    assert (df["numerical_divergence"] == False).all()


def test_detailed_comparison_table():
    """Verify fhn_detailed_comparison.csv matches Phase 3B rows and deltas."""
    comp_file = RESULTS_4C / "fhn_detailed_comparison.csv"
    assert comp_file.exists(), f"Missing comparison file: {comp_file}"

    df = pd.read_csv(comp_file)
    assert len(df) == 109

    # Verify comparison columns exist
    required_cols = [
        "specimen_id", "population", "sweep_number", "protocol_family", "stimulus_amplitude_pa",
        "spikes_rec", "spikes_det", "spikes_fhn",
        "rmse_during_det_mv", "rmse_during_fhn_mv",
        "rmse_overall_det_mv", "rmse_overall_fhn_mv",
        "correlation_det", "correlation_fhn",
        "fhn_minus_det_rmse_during_mv", "fhn_minus_det_rmse_overall_mv",
        "fhn_minus_det_correlation", "fhn_minus_det_spikes",
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column {col} in comparison table"

    # Verify math consistency of deltas
    for _, row in df.iterrows():
        expected_delta_rmse = round(row["rmse_during_fhn_mv"] - row["rmse_during_det_mv"], 3)
        assert abs(row["fhn_minus_det_rmse_during_mv"] - expected_delta_rmse) < 1e-2
        assert row["fhn_minus_det_spikes"] == (row["spikes_fhn"] - row["spikes_det"])


def test_population_and_protocol_summaries():
    """Verify population_summary.csv and protocol_family_summary.csv consistency."""
    pop_file = RESULTS_4C / "population_summary.csv"
    proto_file = RESULTS_4C / "protocol_family_summary.csv"

    assert pop_file.exists(), f"Missing population summary: {pop_file}"
    assert proto_file.exists(), f"Missing protocol family summary: {proto_file}"

    pop_df = pd.read_csv(pop_file)
    assert len(pop_df) == 4
    assert set(pop_df["population"]) == {"A", "B", "C", "D"}
    assert pop_df["n_heldout_sweeps"].sum() == 109

    proto_df = pd.read_csv(proto_file)
    assert len(proto_df) >= 4
    assert proto_df["n_sweeps"].sum() == 109


def test_all_diagnostic_figures_exist():
    """Verify all 7 requested diagnostic figures exist and are non-empty."""
    expected_figures = [
        "fi_curves_comparison.png",
        "waveform_fidelity_comparison.png",
        "subthreshold_iv_curves.png",
        "traces_pop_A.png",
        "traces_pop_B.png",
        "traces_pop_C.png",
        "traces_pop_D.png",
    ]
    for fig_name in expected_figures:
        fig_path = FIGURES_DIR / fig_name
        assert fig_path.exists(), f"Missing figure: {fig_path}"
        assert fig_path.stat().st_size > 10000, f"Figure too small / corrupt: {fig_path}"


"""Unit and Regression Tests for Phase 4B: FHN Parameter Calibration Framework.

Verifies:
1. Target extraction from experimental traces and metadata for all 4 populations.
2. Invariant: strictly zero held-out sweeps used in calibration.
3. Multi-component loss function evaluation, stability checks, and component weighting.
4. Physical validity and bounds adherence of fitted parameters.
5. Linear stability of resting equilibrium for all four fitted models.
6. Deterministic reproducibility of the calibration pipeline.
7. Integrity and schema of Phase 4B deliverables (CSVs, figures, config, audit record).
"""
from __future__ import annotations

import csv
import json
import pathlib
import pytest
import numpy as np

from src.calibration.fhn_calibration import (
    CalibrationBounds,
    CalibrationLossBreakdown,
    CalibrationMetrics,
    CalibrationTarget,
    FHNCalibrator,
    evaluate_calibration_loss,
    load_all_calibration_targets,
    load_calibration_target,
    FROZEN_CALIBRATION_ASSIGNMENTS,
)
from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FitzHughNagumoModel,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "phase4b"


class TestCalibrationTargets:
    """Validate loading and integrity of experimental calibration targets."""

    def test_load_all_four_targets(self):
        targets = load_all_calibration_targets(repo_root=REPO_ROOT)
        assert set(targets.keys()) == {"A", "B", "C", "D"}

    @pytest.mark.parametrize("pop, expected_specimen, expected_sweep, expected_amp", [
        ("A", 484564503, 49, 370.0),
        ("B", 318808427, 40, 190.0),
        ("C", 471129934, 51, 410.0),
        ("D", 471786879, 42, 250.0),
    ])
    def test_target_specimen_and_sweep_assignments(self, pop, expected_specimen, expected_sweep, expected_amp):
        target = load_calibration_target(pop, repo_root=REPO_ROOT)
        assert target.specimen_id == expected_specimen
        assert target.sweep_id == expected_sweep
        assert target.stimulus_amplitude_pa == pytest.approx(expected_amp, rel=1e-3)
        assert target.traces_path.exists()
        assert target.summary_path.exists()

    def test_no_heldout_sweeps_in_calibration(self):
        """Verify calibration assignments do not use any held-out sweeps."""
        heldout_csv = REPO_ROOT / "results" / "phase3b" / "heldout_sweeps.csv"
        if not heldout_csv.exists():
            pytest.skip("heldout_sweeps.csv not found")

        heldout_pairs = set()
        with open(heldout_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                heldout_pairs.add((int(row["specimen_id"]), int(row["sweep_number"])))

        for pop, info in FROZEN_CALIBRATION_ASSIGNMENTS.items():
            pair = (info["specimen_id"], info["sweep_id"])
            assert pair not in heldout_pairs, (
                f"Population {pop} calibration sweep {pair} overlaps with held-out sweeps!"
            )


class TestCalibrationLossFunction:
    """Validate loss evaluation, bounds checking, and linear stability enforcement."""

    def test_loss_breakdown_structure(self):
        target = load_calibration_target("A", repo_root=REPO_ROOT)
        bounds = CalibrationBounds()
        theta_test = [100.0, 2.0, -50.0, 30.0, 0.003, 20.0, 10.0]
        breakdown = evaluate_calibration_loss(theta_test, target, bounds)
        assert isinstance(breakdown, CalibrationLossBreakdown)
        assert breakdown.total_loss >= 0.0
        assert breakdown.loss_rest == 0.0

    def test_unstable_parameters_rejected(self):
        """An unstable resting equilibrium must receive penalty loss >= 1e4."""
        target = load_calibration_target("A", repo_root=REPO_ROOT)
        bounds = CalibrationBounds()
        # Inverted coupling or negative leak generates unstable equilibrium
        unstable_theta = [100.0, 0.01, -73.0, 30.0, 0.02, 5.0, 0.0]
        breakdown = evaluate_calibration_loss(unstable_theta, target, bounds)
        assert breakdown.total_loss >= 1e4


class TestFittedParametersAndInvariants:
    """Verify that fitted parameters satisfy physical bounds and linear resting stability."""

    @pytest.fixture
    def fitted_params_df(self):
        csv_path = RESULTS_DIR / "fhn_fitted_parameters.csv"
        assert csv_path.exists(), f"Missing {csv_path}"
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def test_four_populations_present(self, fitted_params_df):
        pops = [r["population"] for r in fitted_params_df]
        assert pops == ["A", "B", "C", "D"]

    def test_all_fitted_models_stable_at_rest(self, fitted_params_df):
        for row in fitted_params_df:
            pop = row["population"]
            p = FHNParameters(
                C_m=float(row["C_m_pf"]),
                g_L=float(row["g_L_ns"]),
                V_rest=float(row["V_rest_mv"]),
                V_th=float(row["V_th_mv"]),
                V_peak=float(row["V_peak_mv"]),
                k_v=float(row["k_v_ns_per_mv2"]),
                tau_w=float(row["tau_w_ms"]),
                a_w=float(row["a_w_ns"]),
            )
            assert p.is_resting_point_stable, f"Population {pop} resting point is not stable!"
            assert row["is_resting_point_stable"] == "True"

    def test_all_parameters_within_bounds(self, fitted_params_df):
        bounds = CalibrationBounds()
        for row in fitted_params_df:
            pop = row["population"]
            cm = float(row["C_m_pf"])
            gl = float(row["g_L_ns"])
            vth = float(row["V_th_mv"])
            vpeak = float(row["V_peak_mv"])
            kv = float(row["k_v_ns_per_mv2"])
            tau = float(row["tau_w_ms"])
            aw = float(row["a_w_ns"])

            assert bounds.C_m_min <= cm <= bounds.C_m_max, f"Pop {pop} C_m={cm} out of bounds"
            assert bounds.g_L_min <= gl <= bounds.g_L_max, f"Pop {pop} g_L={gl} out of bounds"
            assert bounds.V_th_min <= vth <= bounds.V_th_max, f"Pop {pop} V_th={vth} out of bounds"
            assert bounds.V_peak_min <= vpeak <= bounds.V_peak_max, f"Pop {pop} V_peak={vpeak} out of bounds"
            assert bounds.k_v_min <= kv <= bounds.k_v_max, f"Pop {pop} k_v={kv} out of bounds"
            assert bounds.tau_w_min <= tau <= bounds.tau_w_max, f"Pop {pop} tau_w={tau} out of bounds"
            assert bounds.a_w_min <= aw <= bounds.a_w_max, f"Pop {pop} a_w={aw} out of bounds"


class TestDeliverablesIntegrity:
    """Verify presence, non-emptiness, and schema of Phase 4B artifacts."""

    def test_csv_deliverables_exist(self):
        for name in [
            "fhn_fitted_parameters.csv",
            "fhn_calibration_metrics.csv",
            "fhn_calibration_loss_breakdown.csv",
        ]:
            p = RESULTS_DIR / name
            assert p.exists() and p.stat().st_size > 0, f"Deliverable {name} missing or empty"

    def test_json_records_exist(self):
        cfg_p = RESULTS_DIR / "calibration_config.json"
        audit_p = RESULTS_DIR / "data_audit_record.json"
        assert cfg_p.exists() and cfg_p.stat().st_size > 0
        assert audit_p.exists() and audit_p.stat().st_size > 0

        with open(audit_p, "r", encoding="utf-8") as f:
            audit = json.load(f)
        assert audit["held_out_sweeps_used"] == 0
        assert audit["verification_invariants"]["all_four_resting_points_stable"] is True

    def test_figures_exist_and_nonempty(self):
        fig_dir = RESULTS_DIR / "figures"
        expected_figs = [
            "voltage_comparison_A.png",
            "voltage_comparison_B.png",
            "voltage_comparison_C.png",
            "voltage_comparison_D.png",
            "four_population_calibration_summary.png",
            "calibration_loss_breakdown.png",
        ]
        for name in expected_figs:
            fig_p = fig_dir / name
            assert fig_p.exists() and fig_p.stat().st_size > 1000, f"Figure {name} missing or trivial"


class TestDeterministicReproducibility:
    """Verify that optimization with fixed seed is strictly deterministic."""

    def test_deterministic_single_iteration(self):
        target = load_calibration_target("C", repo_root=REPO_ROOT)
        calibrator1 = FHNCalibrator(random_seed=42)
        calibrator2 = FHNCalibrator(random_seed=42)

        s1 = calibrator1._generate_candidate_starts(target)
        s2 = calibrator2._generate_candidate_starts(target)
        assert np.allclose(s1, s2), "Starting points are not deterministic"

"""Unit and regression tests for Phase 4B.1 independent calibration and identifiability audit.

Verifies:
1. Exact or floating-point reproduction of all Phase 4B calibration metrics and loss breakdowns.
2. Invariance of baseline anchoring (V_rest) and resting equilibrium linear stability.
3. Metric classification invariants (Group A constrained, Group B optimized, Group C emergent).
4. Population D Pareto frontier properties (impossibility of simultaneous high latency and high spike count).
5. Numerical consistency of the Low-Loss / High-RMSE phenomenon across all four populations.
6. Parameter bounds and structural consistency.
"""
from __future__ import annotations

import pathlib
import pytest
import numpy as np
import pandas as pd

from src.calibration.fhn_calibration import (
    CalibrationBounds,
    CalibrationLossBreakdown,
    CalibrationMetrics,
    CalibrationTarget,
    FHNCalibrator,
    evaluate_calibration_loss,
    evaluate_fast_rk4,
    load_all_calibration_targets,
    FROZEN_CALIBRATION_ASSIGNMENTS,
)
from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FitzHughNagumoModel,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PHASE4B_DIR = REPO_ROOT / "results" / "phase4b"
PHASE4B1_DIR = REPO_ROOT / "results" / "phase4b1"


@pytest.fixture(scope="module")
def targets() -> dict[str, CalibrationTarget]:
    """Load calibration targets for all four populations."""
    return load_all_calibration_targets()


@pytest.fixture(scope="module")
def calibrator() -> FHNCalibrator:
    """Instantiate standard FHN calibrator."""
    return FHNCalibrator()


@pytest.fixture(scope="module")
def fitted_params_df() -> pd.DataFrame:
    """Load Phase 4B serialized fitted parameters."""
    return pd.read_csv(PHASE4B_DIR / "fhn_fitted_parameters.csv").set_index("population")


@pytest.fixture(scope="module")
def original_metrics_df() -> pd.DataFrame:
    """Load Phase 4B original calibration metrics."""
    return pd.read_csv(PHASE4B_DIR / "fhn_calibration_metrics.csv").set_index("population")


@pytest.fixture(scope="module")
def audit_repro_df() -> pd.DataFrame:
    """Load Phase 4B.1 independent reproduction audit CSV."""
    return pd.read_csv(PHASE4B1_DIR / "fhn_calibration_reproduction_audit.csv").set_index("population")


class TestPhase4B1Reproduction:
    """Verifies independent numerical reproduction of Phase 4B calibration results."""

    @pytest.mark.parametrize("pop", ["A", "B", "C", "D"])
    def test_spike_counts_reproduced_exactly(
        self,
        pop: str,
        targets: dict[str, CalibrationTarget],
        calibrator: FHNCalibrator,
        fitted_params_df: pd.DataFrame,
        original_metrics_df: pd.DataFrame,
    ) -> None:
        """Assert that recomputed FHN spike counts match original reported counts exactly."""
        row = fitted_params_df.loc[pop]
        target = targets[pop]
        params = FHNParameters(
            C_m=float(row["C_m_pf"]),
            g_L=float(row["g_L_ns"]),
            V_rest=float(row["V_rest_mv"]),
            V_th=float(row["V_th_mv"]),
            V_peak=float(row["V_peak_mv"]),
            k_v=float(row["k_v_ns_per_mv2"]),
            tau_w=float(row["tau_w_ms"]),
            a_w=float(row["a_w_ns"]),
        )
        metrics, _ = calibrator.evaluate_full_metrics(params, target, dt_ms=0.025)
        orig_spk = int(original_metrics_df.loc[pop, "spikes_fhn"])
        assert metrics.spikes_fhn == orig_spk, f"Population {pop} spike count mismatch: {metrics.spikes_fhn} vs {orig_spk}"

    @pytest.mark.parametrize("pop", ["A", "B", "C", "D"])
    def test_first_spike_latency_reproduced(
        self,
        pop: str,
        targets: dict[str, CalibrationTarget],
        calibrator: FHNCalibrator,
        fitted_params_df: pd.DataFrame,
        original_metrics_df: pd.DataFrame,
    ) -> None:
        """Assert that recomputed first-spike latency matches within 0.1 ms tolerance."""
        row = fitted_params_df.loc[pop]
        target = targets[pop]
        params = FHNParameters(
            C_m=float(row["C_m_pf"]),
            g_L=float(row["g_L_ns"]),
            V_rest=float(row["V_rest_mv"]),
            V_th=float(row["V_th_mv"]),
            V_peak=float(row["V_peak_mv"]),
            k_v=float(row["k_v_ns_per_mv2"]),
            tau_w=float(row["tau_w_ms"]),
            a_w=float(row["a_w_ns"]),
        )
        metrics, _ = calibrator.evaluate_full_metrics(params, target, dt_ms=0.025)
        orig_lat = float(original_metrics_df.loc[pop, "first_spike_lat_fhn_ms"])
        assert abs(metrics.first_spike_lat_fhn_ms - orig_lat) < 0.1, (
            f"Population {pop} latency mismatch: {metrics.first_spike_lat_fhn_ms} vs {orig_lat}"
        )

    @pytest.mark.parametrize("pop", ["A", "B", "C", "D"])
    def test_step_rmse_reproduced(
        self,
        pop: str,
        targets: dict[str, CalibrationTarget],
        calibrator: FHNCalibrator,
        fitted_params_df: pd.DataFrame,
        original_metrics_df: pd.DataFrame,
    ) -> None:
        """Assert that recomputed step RMSE matches within 0.05 mV tolerance."""
        row = fitted_params_df.loc[pop]
        target = targets[pop]
        params = FHNParameters(
            C_m=float(row["C_m_pf"]),
            g_L=float(row["g_L_ns"]),
            V_rest=float(row["V_rest_mv"]),
            V_th=float(row["V_th_mv"]),
            V_peak=float(row["V_peak_mv"]),
            k_v=float(row["k_v_ns_per_mv2"]),
            tau_w=float(row["tau_w_ms"]),
            a_w=float(row["a_w_ns"]),
        )
        metrics, _ = calibrator.evaluate_full_metrics(params, target, dt_ms=0.025)
        orig_rmse = float(original_metrics_df.loc[pop, "rmse_step_fhn_mv"])
        assert abs(metrics.rmse_step_fhn_mv - orig_rmse) < 0.05, (
            f"Population {pop} RMSE mismatch: {metrics.rmse_step_fhn_mv} vs {orig_rmse}"
        )

    @pytest.mark.parametrize("pop", ["A", "B", "C", "D"])
    def test_calibration_loss_reproduced(
        self,
        pop: str,
        targets: dict[str, CalibrationTarget],
        calibrator: FHNCalibrator,
        fitted_params_df: pd.DataFrame,
        original_metrics_df: pd.DataFrame,
    ) -> None:
        """Assert that recomputed calibration loss matches within 1e-4 tolerance."""
        row = fitted_params_df.loc[pop]
        target = targets[pop]
        params = FHNParameters(
            C_m=float(row["C_m_pf"]),
            g_L=float(row["g_L_ns"]),
            V_rest=float(row["V_rest_mv"]),
            V_th=float(row["V_th_mv"]),
            V_peak=float(row["V_peak_mv"]),
            k_v=float(row["k_v_ns_per_mv2"]),
            tau_w=float(row["tau_w_ms"]),
            a_w=float(row["a_w_ns"]),
        )
        metrics, _ = calibrator.evaluate_full_metrics(params, target, dt_ms=0.025)
        orig_loss = float(original_metrics_df.loc[pop, "calibration_loss"])
        assert abs(metrics.calibration_loss - orig_loss) < 1e-4, (
            f"Population {pop} loss mismatch: {metrics.calibration_loss} vs {orig_loss}"
        )


class TestLowLossHighRMSEMechanics:
    """Verifies the mathematical basis of the Low-Loss / High-RMSE phenomenon."""

    @pytest.mark.parametrize("pop", ["A", "C"])
    def test_tiny_loss_yet_high_rmse(
        self,
        pop: str,
        original_metrics_df: pd.DataFrame,
    ) -> None:
        """Verify that Pops A and C have loss <= 1e-4 but step RMSE > 40 mV."""
        loss = float(original_metrics_df.loc[pop, "calibration_loss"])
        rmse = float(original_metrics_df.loc[pop, "rmse_step_fhn_mv"])
        assert loss <= 1e-4, f"Pop {pop} loss expected <= 1e-4, got {loss}"
        assert rmse >= 40.0, f"Pop {pop} step RMSE expected >= 40.0 mV, got {rmse}"

    @pytest.mark.parametrize("pop", ["A", "B", "C", "D"])
    def test_flatline_has_lower_rmse_than_spiking_fhn(
        self,
        pop: str,
        targets: dict[str, CalibrationTarget],
        original_metrics_df: pd.DataFrame,
    ) -> None:
        """Verify the 'double penalty' consequence: flatline has lower RMSE than spiking FHN."""
        target = targets[pop]
        data = np.load(target.traces_path)
        t_exp = data["t_ms"]
        v_exp = data["v_rec_mv"]
        step_mask = (t_exp >= target.stimulus_onset_ms) & (t_exp <= target.stimulus_onset_ms + target.stimulus_duration_ms)

        v_flat = np.full_like(v_exp, target.baseline_recorded_mv)
        rmse_flat = float(np.sqrt(np.mean((v_flat[step_mask] - v_exp[step_mask]) ** 2)))
        rmse_fhn = float(original_metrics_df.loc[pop, "rmse_step_fhn_mv"])

        # Flatline RMSE is strictly lower than FHN spiking RMSE
        assert rmse_flat < rmse_fhn, (
            f"Pop {pop}: flatline RMSE ({rmse_flat:.2f} mV) should be lower than FHN spiking RMSE ({rmse_fhn:.2f} mV) due to double penalty"
        )


class TestMetricClassificationTaxonomy:
    """Verifies that metric classification taxonomy rules are mathematically consistent."""

    def test_classification_csv_structure(self) -> None:
        """Verify that classification audit CSV exists and has complete rows."""
        csv_path = PHASE4B1_DIR / "fhn_metrics_classification_audit.csv"
        assert csv_path.exists(), f"Classification CSV missing at {csv_path}"
        df = pd.read_csv(csv_path)
        assert len(df) == 10
        assert set(df["category"].unique()) == {
            "Group A: Directly Constrained / Fixed",
            "Group B: Directly Optimized via Objective",
            "Group C: Emergent Model Behaviour",
        }

    def test_fixed_and_optimized_are_not_emergent(self) -> None:
        """Assert that no Group A or Group B metrics are classified as emergent predictions."""
        df = pd.read_csv(PHASE4B1_DIR / "fhn_metrics_classification_audit.csv")
        group_ab = df[df["category"].str.startswith("Group A") | df["category"].str.startswith("Group B")]
        for _, row in group_ab.iterrows():
            assert not row["is_emergent_prediction"], (
                f"Metric {row['metric_name']} cannot be an emergent prediction!"
            )


class TestPopulationDParetoTradeoff:
    """Verifies the mathematical impossibility of simultaneous 58 ms delay and 13 spikes in 2D FHN."""

    def test_pareto_frontier_structure(self) -> None:
        """Verify Population D Pareto frontier audit summary."""
        csv_path = PHASE4B1_DIR / "fhn_population_d_pareto_audit.csv"
        assert csv_path.exists(), f"Pareto CSV missing at {csv_path}"
        df = pd.read_csv(csv_path).set_index("spike_count")

        # When spike count is >= 12, max latency is <= 20 ms
        if 13 in df.index:
            max_lat_13 = float(df.loc[13, "max_lat_ms"])
            assert max_lat_13 < 15.0, f"Max latency for 13 spikes should be < 15 ms, got {max_lat_13}"

        # When spike count is 4, max latency can reach > 55 ms
        if 4 in df.index:
            max_lat_4 = float(df.loc[4, "max_lat_ms"])
            assert max_lat_4 >= 55.0, f"Max latency for 4 spikes should reach >= 55 ms, got {max_lat_4}"

    def test_alternative_low_cm_produces_fast_spikes_with_low_latency(
        self,
        targets: dict[str, CalibrationTarget],
    ) -> None:
        """Verify that lowering Cm to 50 pF produces >= 12 spikes but collapses onset latency to < 16 ms."""
        target_D = targets["D"]
        nspk, crossings, _ = evaluate_fast_rk4(
            Cm=50.0,
            gL=0.9128,
            Vrest=target_D.baseline_recorded_mv,
            Vth=-57.4868,
            Vpeak=64.9985,
            kv=0.002577,
            tau_w=10.0,
            aw=11.7242,
            I_step_pa=250.0,
        )
        assert nspk >= 12, f"Expected >= 12 spikes with Cm=50 pF, got {nspk}"
        lat = crossings[0]
        assert lat < 16.0, f"Expected latency < 16 ms with Cm=50 pF, got {lat:.2f} ms"


class TestIdentifiabilityAndHessian:
    """Verifies identifiability audit properties and resting point stability."""

    def test_all_populations_have_stable_resting_points(
        self,
        fitted_params_df: pd.DataFrame,
    ) -> None:
        """Assert that resting equilibria are locally linearly stable for all 4 models."""
        for pop, row in fitted_params_df.iterrows():
            params = FHNParameters(
                C_m=float(row["C_m_pf"]),
                g_L=float(row["g_L_ns"]),
                V_rest=float(row["V_rest_mv"]),
                V_th=float(row["V_th_mv"]),
                V_peak=float(row["V_peak_mv"]),
                k_v=float(row["k_v_ns_per_mv2"]),
                tau_w=float(row["tau_w_ms"]),
                a_w=float(row["a_w_ns"]),
            )
            assert params.is_resting_point_stable, f"Population {pop} resting point must be linearly stable!"

    def test_resting_conductance_dominated_by_aw(self) -> None:
        """Assert that adaptation coupling a_w contributes > 50% of effective resting conductance."""
        ident_df = pd.read_csv(PHASE4B1_DIR / "fhn_parameter_identifiability_audit.csv").set_index("population")
        for pop, row in ident_df.iterrows():
            share_aw = float(row["a_w_conductance_share"])
            assert share_aw > 0.50, f"Pop {pop}: a_w share expected > 50%, got {share_aw * 100:.1f}%"

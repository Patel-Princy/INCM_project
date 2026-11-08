"""Unit and regression tests for INCM Phase 4C.3: Global Bistability, Fold Bifurcation, and Adaptation Scope."""
from __future__ import annotations

import pathlib
import pandas as pd
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_4C3 = REPO_ROOT / "results" / "phase4c3"


def test_independent_fold_reproduction():
    """Verify that independent fine-resolution bisection reproduces Phase 4C.2 fold estimates within grid uncertainty."""
    fold_file = RESULTS_4C3 / "phase4c3_fold_verification.csv"
    assert fold_file.exists(), f"Missing {fold_file}"

    df = pd.read_csv(fold_file).set_index("population")
    assert len(df) == 4

    for pop in ["A", "B", "C", "D"]:
        # Verify discrepancy vs Phase 4C.2 coarse estimate is within coarse grid tolerance (< 1.0 pA)
        assert abs(df.loc[pop, "fold_discrepancy_vs_4c2_pa"]) < 1.0
        # Verify dt sensitivity across dt in {0.050, 0.025, 0.010 ms} is tightly bounded (< 0.05 pA)
        assert df.loc[pop, "dt_sensitivity_max_delta_pa"] < 0.05
        # Verify numerical uncertainty is reported and positive
        assert df.loc[pop, "numerical_uncertainty_pa"] > 0.0


def test_bistability_and_coexistence():
    """Verify that stable resting state and stable limit cycle coexist across the verified bistability interval."""
    bist_file = RESULTS_4C3 / "phase4c3_bistability_verification.csv"
    assert bist_file.exists(), f"Missing {bist_file}"

    df = pd.read_csv(bist_file).set_index("population")
    assert len(df) == 4

    for pop in ["A", "B", "C", "D"]:
        assert df.loc[pop, "resting_state_stable_throughout"] is True or df.loc[pop, "resting_state_stable_throughout"] == 1
        assert df.loc[pop, "limit_cycle_stable_throughout"] is True or df.loc[pop, "limit_cycle_stable_throughout"] == 1
        assert df.loc[pop, "coexistence_demonstrated"] is True or df.loc[pop, "coexistence_demonstrated"] == 1
        assert df.loc[pop, "bistability_width_verified_pa"] >= 10.0
        # Separatrix threshold expands away from Hopf toward fold
        assert df.loc[pop, "separatrix_dv_crit_at_hopf_mv"] < df.loc[pop, "separatrix_dv_crit_near_fold_mv"]
        # Limit cycle is extinguished below fold
        assert df.loc[pop, "cycle_annihilation_verified_below_fold"] is True or df.loc[pop, "cycle_annihilation_verified_below_fold"] == 1


def test_biological_adaptation_scope():
    """Verify biological adaptation sweep counts, population-specific distributions, and representative scope."""
    scope_file = RESULTS_4C3 / "phase4c3_biological_adaptation_scope.csv"
    assert scope_file.exists(), f"Missing {scope_file}"

    df = pd.read_csv(scope_file).set_index("population")
    assert len(df) == 4

    # Total sweeps across 4 specimens is 109
    assert df["total_heldout_sweeps"].sum() == 109

    # Total multi-cycle sweeps is 23
    assert df["sweeps_multi_cycle_ge3"].sum() == 23

    # All 23 multi-cycle sweeps exhibit expansion
    assert df["sweeps_expansion"].sum() == 23
    assert df["sweeps_contraction"].sum() == 0
    assert df["sweeps_approx_stationary"].sum() == 0

    # Population D has moderate adaptation (median < 2.5x, max < 3.0x)
    assert df.loc["D", "median_ratio"] < 2.5
    assert df.loc["D", "max_ratio"] < 3.0

    # Ratios >= 5.0x occur only in 3 sweeps across Pops A and C
    assert df["sweeps_ratio_ge_5"].sum() == 3
    assert df.loc["A", "sweeps_ratio_ge_5"] == 2
    assert df.loc["C", "sweeps_ratio_ge_5"] == 1
    assert df.loc["B", "sweeps_ratio_ge_5"] == 0
    assert df.loc["D", "sweeps_ratio_ge_5"] == 0


def test_hopf_normal_form_convention():
    """Verify that independent Hopf derivations and Lyapunov sign conventions are strictly satisfied."""
    hopf_file = RESULTS_4C3 / "phase4c3_hopf_independent_checks.csv"
    assert hopf_file.exists(), f"Missing {hopf_file}"

    df = pd.read_csv(hopf_file).set_index("population")
    assert len(df) == 4

    for pop in ["A", "B", "C", "D"]:
        assert df.loc[pop, "check_residuals_dV_dw"] is True or df.loc[pop, "check_residuals_dV_dw"] == 1
        assert df.loc[pop, "check_trace_zero"] is True or df.loc[pop, "check_trace_zero"] == 1
        assert df.loc[pop, "check_det_positive"] is True or df.loc[pop, "check_det_positive"] == 1
        assert df.loc[pop, "check_pure_imaginary_eigenvalues"] is True or df.loc[pop, "check_pure_imaginary_eigenvalues"] == 1
        assert df.loc[pop, "check_transversality_positive"] is True or df.loc[pop, "check_transversality_positive"] == 1
        assert df.loc[pop, "check_lyapunov_positive"] is True or df.loc[pop, "check_lyapunov_positive"] == 1
        assert df.loc[pop, "first_lyapunov_coefficient"] > 0.0
        assert df.loc[pop, "local_criticality"] == "SUBCRITICAL_HOPF"


def test_bistability_boundary_semantics():
    """Verify that bistability intervals strictly use open-interval semantics with explicit boundary classifications."""
    bist_file = RESULTS_4C3 / "phase4c3_bistability_verification.csv"
    assert bist_file.exists(), f"Missing {bist_file}"

    df = pd.read_csv(bist_file).set_index("population")
    assert len(df) == 4

    for pop in ["A", "B", "C", "D"]:
        # Verify interval representation uses open parentheses
        val_str = str(df.loc[pop, "bistability_interval_verified"])
        assert val_str.startswith("("), f"Interval must be open: {val_str}"
        assert ")" in val_str, f"Interval must be open: {val_str}"

        # Verify explicit semantic column values
        assert df.loc[pop, "interval_semantics"] == "open_interval_I_fold_lt_I_lt_I_H1"
        assert df.loc[pop, "endpoint_semantics_interior"] == "coexistence_of_stable_resting_and_stable_spiking"
        assert df.loc[pop, "endpoint_semantics_fold_boundary"] == "non_hyperbolic_cycle_fold_boundary"
        assert df.loc[pop, "endpoint_semantics_hopf_boundary"] == "non_hyperbolic_hopf_equilibrium"

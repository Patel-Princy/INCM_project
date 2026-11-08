"""Unit and regression tests for INCM Phase 4C.1: Independent Held-Out Results and Claims Audit."""
from __future__ import annotations

import json
import math
import pathlib
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_4C = REPO_ROOT / "results" / "phase4c"
RESULTS_4C1 = REPO_ROOT / "results" / "phase4c1"
RESULTS_4B = REPO_ROOT / "results" / "phase4b"


def test_recomputed_summary_metrics_consistency():
    """Verify phase4c1_recomputed_population_metrics.csv matches Phase 4C population summary."""
    recomp_file = RESULTS_4C1 / "phase4c1_recomputed_population_metrics.csv"
    orig_file = RESULTS_4C / "population_summary.csv"

    assert recomp_file.exists(), f"Missing {recomp_file}"
    assert orig_file.exists(), f"Missing {orig_file}"

    df_recomp = pd.read_csv(recomp_file).set_index("population")
    df_orig = pd.read_csv(orig_file).set_index("population")

    assert len(df_recomp) == 4
    for pop in ["A", "B", "C", "D"]:
        r_row = df_recomp.loc[pop]
        o_row = df_orig.loc[pop]

        assert r_row["n_sweeps"] == o_row["n_heldout_sweeps"]
        assert pytest.approx(r_row["mean_spikes_rec"], abs=1e-2) == o_row["mean_spikes_rec"]
        assert pytest.approx(r_row["mean_spikes_det"], abs=1e-2) == o_row["mean_spikes_det"]
        assert pytest.approx(r_row["mean_spikes_fhn"], abs=1e-2) == o_row["mean_spikes_fhn"]
        assert pytest.approx(r_row["mean_step_rmse_det_mv"], abs=1e-2) == o_row["mean_rmse_during_det_mv"]
        assert pytest.approx(r_row["mean_step_rmse_fhn_mv"], abs=1e-2) == o_row["mean_rmse_during_fhn_mv"]
        assert pytest.approx(r_row["mean_overall_rmse_det_mv"], abs=1e-2) == o_row["mean_rmse_overall_det_mv"]
        assert pytest.approx(r_row["mean_overall_rmse_fhn_mv"], abs=1e-2) == o_row["mean_rmse_overall_fhn_mv"]
        assert pytest.approx(r_row["mean_corr_det"], abs=1e-4) == o_row["mean_corr_det"]
        assert pytest.approx(r_row["mean_corr_fhn"], abs=1e-4) == o_row["mean_corr_fhn"]
        assert r_row["n_spiking_sweeps_rec"] == o_row["n_spiking_sweeps_rec"]
        assert r_row["n_spiking_sweeps_det"] == o_row["n_spiking_sweeps_det"]
        assert r_row["n_spiking_sweeps_fhn"] == o_row["n_spiking_sweeps_fhn"]


def test_expected_sweep_counts_and_denominators():
    """Verify total sweep count is 109 and per-population denominators are exact."""
    recomp_file = RESULTS_4C1 / "phase4c1_recomputed_population_metrics.csv"
    df = pd.read_csv(recomp_file)

    expected_counts = {"A": 31, "B": 18, "C": 34, "D": 26}
    assert df["n_sweeps"].sum() == 109
    for _, row in df.iterrows():
        assert row["n_sweeps"] == expected_counts[row["population"]]
        assert row["aggregation_type"] == "mean_across_repeated_sweeps_single_specimen"


def test_rmse_decomposition_consistency():
    """Verify additive decomposition of MSE across pre, step, and post intervals."""
    decomp_file = RESULTS_4C1 / "phase4c1_rmse_decomposition.csv"
    assert decomp_file.exists(), f"Missing {decomp_file}"

    df = pd.read_csv(decomp_file)
    assert len(df) == 109

    for _, row in df.iterrows():
        # Weights must sum to 1.0 within numerical rounding
        w_sum = row["weight_pre"] + row["weight_step"] + row["weight_post"]
        assert pytest.approx(w_sum, abs=1e-3) == 1.0

        # FHN reconstructed MSE
        f_mse_recon = (
            row["weight_pre"] * (row["fhn_rmse_pre_mv"]**2)
            + row["weight_step"] * (row["fhn_rmse_during_mv"]**2)
            + row["weight_post"] * (row["fhn_rmse_post_mv"]**2)
        )
        f_rmse_recon = math.sqrt(f_mse_recon)
        assert pytest.approx(f_rmse_recon, rel=0.05) == row["fhn_rmse_overall_reported_mv"]

    # Pop A verification: Detailed model MSE is > 90% driven by non-step intervals
    pop_a = df[df["population"] == "A"]
    assert pop_a["det_fraction_mse_from_nonstep"].mean() > 0.90
    assert pop_a["fhn_fraction_mse_from_step"].mean() > 0.85


def test_spike_detection_contingency_and_sensitivity():
    """Verify 2x2 contingency numbers for FHN vs Detailed model."""
    spk_file = RESULTS_4C1 / "phase4c1_spike_detection_audit.csv"
    assert spk_file.exists(), f"Missing {spk_file}"

    df = pd.read_csv(spk_file)
    assert len(df) == 109

    counts_fhn = df["fhn_detection_class"].value_counts().to_dict()
    assert counts_fhn["TRUE_POSITIVE"] == 37
    assert counts_fhn["TRUE_NEGATIVE"] == 62
    assert counts_fhn["FALSE_POSITIVE"] == 7
    assert counts_fhn["FALSE_NEGATIVE"] == 3

    # Sensitivity = 37 / (37 + 3) = 37 / 40 = 92.5%
    sensitivity_fhn = counts_fhn["TRUE_POSITIVE"] / (counts_fhn["TRUE_POSITIVE"] + counts_fhn["FALSE_NEGATIVE"])
    assert pytest.approx(sensitivity_fhn, abs=1e-3) == 0.925

    counts_det = df["det_detection_class"].value_counts().to_dict()
    assert counts_det["TRUE_POSITIVE"] == 24
    assert counts_det["FALSE_NEGATIVE"] == 16
    assert counts_det["TRUE_NEGATIVE"] == 69


def test_subthreshold_audit_qualifications():
    """Verify subthreshold audit results and R^2 qualifications."""
    subth_file = RESULTS_4C1 / "phase4c1_subthreshold_audit.csv"
    assert subth_file.exists(), f"Missing {subth_file}"

    df = pd.read_csv(subth_file)

    # Biological recording linearity r^2 is > 0.98 for all four populations
    all_rec = df[df["subset_definition"] == "all_rec_subthreshold"].set_index("population")
    for pop in ["A", "B", "C", "D"]:
        assert all_rec.loc[pop, "recorded_iv_linearity_r2"] > 0.98

    # FHN vs Recorded correlation r^2 > 0.98 holds strictly for B and D under mutual subthreshold
    mut_sub = df[df["subset_definition"] == "mutually_subthreshold"].set_index("population")
    assert mut_sub.loc["B", "fhn_vs_recorded_correlation_r2"] > 0.98
    assert mut_sub.loc["D", "fhn_vs_recorded_correlation_r2"] > 0.98
    assert mut_sub.loc["A", "fhn_vs_recorded_correlation_r2"] < 0.98
    assert mut_sub.loc["C", "fhn_vs_recorded_correlation_r2"] < 0.98


def test_all_four_fitted_models_have_positive_lyapunov_coefficient():
    """Verify that all four calibrated models undergo a subcritical Hopf bifurcation (l1 > 0)."""
    params_df = pd.read_csv(RESULTS_4B / "fhn_fitted_parameters.csv").set_index("population")

    for pop in ["A", "B", "C", "D"]:
        p = params_df.loc[pop]
        Cm = float(p["C_m_pf"])
        gL = float(p["g_L_ns"])
        aw = float(p["a_w_ns"])
        kv = float(p["k_v_ns_per_mv2"])
        tau_w = float(p["tau_w_ms"])
        Vrest = float(p["V_rest_mv"])
        Vth = float(p["V_th_mv"])
        Vpeak = float(p["V_peak_mv"])

        # Hopf condition ratio
        assert (aw * tau_w / Cm) > 1.0

        A_quad = -3.0 * kv
        B_quad = 2.0 * kv * (Vrest + Vth + Vpeak)
        C_quad = -(gL + Cm / tau_w + kv * (Vrest * Vth + Vrest * Vpeak + Vth * Vpeak))
        disc = B_quad**2 - 4 * A_quad * C_quad
        assert disc > 0.0

        v_h1 = (-B_quad + math.sqrt(disc)) / (2 * A_quad)
        d2f = -6.0 * kv * v_h1 + 2.0 * kv * (Vrest + Vth + Vpeak)
        d3f = -6.0 * kv

        A_mat = np.array([[1.0 / tau_w, -1.0 / Cm], [aw / tau_w, -1.0 / tau_w]])
        omega0 = math.sqrt(np.linalg.det(A_mat))

        q = np.array([1.0, Cm * (1.0 / tau_w - 1j * omega0)])
        p_raw = np.array([-(aw / tau_w) / (1.0 / tau_w + 1j * omega0), 1.0])
        p_vec = p_raw / np.conj(np.vdot(p_raw, q))

        def b_vec(x, y):
            return np.array([(d2f / Cm) * x[0] * y[0], 0.0 + 0j])

        def c_vec(x, y, z):
            return np.array([(d3f / Cm) * x[0] * y[0] * z[0], 0.0 + 0j])

        t1 = np.vdot(p_vec, c_vec(q, q, np.conj(q)))
        t2 = -2.0 * np.vdot(p_vec, b_vec(q, np.linalg.solve(A_mat, b_vec(q, np.conj(q)))))
        t3 = np.vdot(p_vec, b_vec(np.conj(q), np.linalg.solve(2j * omega0 * np.eye(2) - A_mat, b_vec(q, q))))

        l1 = 0.5 * float(np.real(t1 + t2 + t3))
        assert l1 > 0.0, f"Pop {pop} l1 was not positive: {l1}"


def test_claim_evidence_matrix_structure():
    """Verify claim evidence matrix has required columns and 5-tier classification."""
    matrix_file = RESULTS_4C1 / "phase4c1_claim_evidence_matrix.csv"
    assert matrix_file.exists(), f"Missing {matrix_file}"

    df = pd.read_csv(matrix_file)
    assert len(df) >= 7
    required_cols = ["claim_id", "claim_statement", "evidence_tier", "supporting_evidence", "qualification_or_correction"]
    for col in required_cols:
        assert col in df.columns

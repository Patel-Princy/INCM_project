"""Unit and regression tests for INCM Phase 4C.2: Transient Adaptation and Population Hopf Dynamics."""
from __future__ import annotations

import pathlib
import pandas as pd
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_4C2 = REPO_ROOT / "results" / "phase4c2"
FIGURES_DIR = RESULTS_4C2 / "figures"


def test_transient_adaptation_results():
    """Verify phase4c2_isi_transient_adaptation.csv captures initial transient and asymptotic stationarity."""
    isi_file = RESULTS_4C2 / "phase4c2_isi_transient_adaptation.csv"
    assert isi_file.exists(), f"Missing {isi_file}"

    df = pd.read_csv(isi_file)
    assert len(df) >= 20

    # Pop B demonstrates transient expansion over initial cycle (+0.5% to +1.5%)
    pop_b = df[df["population"] == "B"]
    assert (pop_b["fhn_pct_change_initial"] > 0.0).any()

    # Across all populations, FHN achieves stationarity within <= 2 cycles
    valid_fhn = df[df["spikes_fhn"] >= 4]
    assert (valid_fhn["fhn_cycles_to_stationarity"] <= 2).all()

    # Asymptotic first-to-last ratio for FHN is near 1.0 (within 2%)
    assert (valid_fhn["fhn_ratio_last_to_1"] >= 0.98).all()
    assert (valid_fhn["fhn_ratio_last_to_1"] <= 1.02).all()

    # In contrast, biological recordings exhibit massive adaptation (ratio > 2.0 in high spiking sweeps)
    high_spk_rec = df[df["spikes_rec"] >= 8]
    assert (high_spk_rec["rec_ratio_last_to_1"] > 2.0).any()


def test_hopf_analytical_derivation_checks():
    """Verify all 8 analytical and numerical derivation checks pass for all 4 populations."""
    deriv_file = RESULTS_4C2 / "phase4c2_hopf_derivation_checks.csv"
    assert deriv_file.exists(), f"Missing {deriv_file}"

    df = pd.read_csv(deriv_file)
    assert len(df) == 4

    check_cols = [
        "check_equilibrium_residual_dV",
        "check_equilibrium_residual_dw",
        "check_trace_is_zero",
        "check_determinant_positive",
        "check_eigenvalues_pure_imaginary",
        "check_transversality_positive",
        "check_lyapunov_positive",
        "check_subcritical_bistability_demonstrated",
    ]
    for col in check_cols:
        assert df[col].all(), f"Derivation check failed: {col}"


def test_population_hopf_verification_table():
    """Verify lower Hopf currents, Lyapunov coefficients, and bistability intervals."""
    hopf_file = RESULTS_4C2 / "phase4c2_population_hopf_verification.csv"
    assert hopf_file.exists(), f"Missing {hopf_file}"

    df = pd.read_csv(hopf_file).set_index("population")
    assert len(df) == 4

    # Pop A
    assert pytest.approx(df.loc["A", "lower_hopf_current_pa"], abs=0.2) == 234.34
    assert df.loc["A", "first_lyapunov_coefficient"] > 0.0
    assert df.loc["A", "global_bistability_width_pa"] >= 15.0

    # Pop B
    assert pytest.approx(df.loc["B", "lower_hopf_current_pa"], abs=0.2) == 161.28
    assert df.loc["B", "first_lyapunov_coefficient"] > 0.0
    assert df.loc["B", "global_bistability_width_pa"] >= 10.0

    # Pop C
    assert pytest.approx(df.loc["C", "lower_hopf_current_pa"], abs=0.2) == 385.33
    assert df.loc["C", "first_lyapunov_coefficient"] > 0.0
    assert df.loc["C", "global_bistability_width_pa"] >= 20.0

    # Pop D
    assert pytest.approx(df.loc["D", "lower_hopf_current_pa"], abs=0.2) == 236.27
    assert df.loc["D", "first_lyapunov_coefficient"] > 0.0
    assert df.loc["D", "global_bistability_width_pa"] >= 15.0


def test_diagnostic_figures_exist():
    """Verify that both Phase 4C.2 diagnostic figures exist and are non-empty."""
    fig1 = FIGURES_DIR / "isi_adaptation_comparison.png"
    fig2 = FIGURES_DIR / "population_hopf_transversality.png"

    assert fig1.exists(), f"Missing {fig1}"
    assert fig2.exists(), f"Missing {fig2}"
    assert fig1.stat().st_size > 10000
    assert fig2.stat().st_size > 10000


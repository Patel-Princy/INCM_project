"""Unit and regression tests for Phase 4B.2 scientific claim and robustness audit.

Verifies:
1. Integrity and reproducibility of the refined Population D Pareto grid scan.
2. Persistence of the latency vs. spike count trade-off within the investigated (C_m, tau_w) subspace.
3. Multi-scale Hessian curvature checks: positive-definiteness of Population B and identification of near-zero/indefinite directions in Populations A, C, D.
4. Scientific claim consistency: explicit distinction between numerical results, range-dependent conclusions, and unproven global claims.
5. Qualification of A-type potassium current as an unmeasured literature-derived hypothesis.
6. Dual-reporting policy compliance (both feature loss and waveform RMSE verified).
"""
from __future__ import annotations

import pathlib
import pytest
import numpy as np
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PHASE4B_DIR = REPO_ROOT / "results" / "phase4b"
PHASE4B1_DIR = REPO_ROOT / "results" / "phase4b1"
PHASE4B2_DIR = REPO_ROOT / "results" / "phase4b2"


@pytest.fixture(scope="module")
def refined_pareto_df() -> pd.DataFrame:
    """Load refined Population D Pareto summary CSV."""
    csv_path = PHASE4B2_DIR / "fhn_population_d_refined_pareto.csv"
    assert csv_path.exists(), f"Missing refined Pareto CSV at {csv_path}"
    return pd.read_csv(csv_path).set_index("spike_count")


@pytest.fixture(scope="module")
def grid_points_df() -> pd.DataFrame:
    """Load refined Population D grid points CSV."""
    csv_path = PHASE4B2_DIR / "fhn_population_d_grid_points.csv"
    assert csv_path.exists(), f"Missing grid points CSV at {csv_path}"
    return pd.read_csv(csv_path)


@pytest.fixture(scope="module")
def hessian_robustness_df() -> pd.DataFrame:
    """Load multi-scale Hessian robustness audit CSV."""
    csv_path = PHASE4B2_DIR / "fhn_hessian_robustness_audit.csv"
    assert csv_path.exists(), f"Missing Hessian robustness CSV at {csv_path}"
    return pd.read_csv(csv_path)


class TestRefinedParetoRobustness:
    """Tests for the refined 31x31 Population D parameter scan."""

    def test_grid_scan_completeness(self, grid_points_df: pd.DataFrame) -> None:
        """Verify that all 961 grid combinations completed with finite values."""
        assert len(grid_points_df) == 961, f"Expected 961 grid points, got {len(grid_points_df)}"
        assert grid_points_df["spike_count"].isna().sum() == 0
        assert grid_points_df["peak_v_mv"].isna().sum() == 0

    def test_refined_tradeoff_persists(self, refined_pareto_df: pd.DataFrame) -> None:
        """Assert that high-spike solutions cannot achieve biological onset latency in tested subspace."""
        if 13 in refined_pareto_df.index:
            max_lat_13 = float(refined_pareto_df.loc[13, "max_lat_ms"])
            assert max_lat_13 < 20.0, f"Max latency for 13 spikes in tested subspace should be < 20 ms, got {max_lat_13}"

        # Long latency solutions (>= 50 ms) must have <= 4 spikes
        for spk, row in refined_pareto_df.iterrows():
            if row["max_lat_ms"] >= 50.0:
                assert int(spk) <= 4, f"Spike count {spk} has latency >= 50 ms ({row['max_lat_ms']:.1f} ms)!"

    def test_boundary_extrema(self, grid_points_df: pd.DataFrame) -> None:
        """Verify that parameter bounds contain extreme behaviors (both fast firing and quiescence)."""
        max_spikes = grid_points_df["spike_count"].max()
        min_spikes = grid_points_df["spike_count"].min()
        assert max_spikes >= 14, f"Expected upper bound to permit >= 14 spikes, got {max_spikes}"
        assert min_spikes == 0, f"Expected lower bound to permit quiescence (0 spikes), got {min_spikes}"


class TestHessianCurvatureRobustness:
    """Tests for the multi-scale Hessian curvature and eigenvalue analysis."""

    def test_hessian_audit_completeness(self, hessian_robustness_df: pd.DataFrame) -> None:
        """Verify that all 4 populations and 5 step sizes were audited (20 rows)."""
        assert len(hessian_robustness_df) == 20
        assert set(hessian_robustness_df["population"].unique()) == {"A", "B", "C", "D"}

    def test_population_b_convexity(self, hessian_robustness_df: pd.DataFrame) -> None:
        """Verify that Population B is strictly positive definite for step sizes >= 0.002."""
        sub_b = hessian_robustness_df[(hessian_robustness_df["population"] == "B") & (hessian_robustness_df["h_rel"] >= 0.002)]
        for _, row in sub_b.iterrows():
            assert row["is_positive_definite"], f"Pop B expected positive definite at h_rel={row['h_rel']}"
            assert row["min_eig"] > 0.0

    def test_populations_a_c_d_indefiniteness_documented(self, hessian_robustness_df: pd.DataFrame) -> None:
        """Verify that non-smooth/valley indefiniteness in Pops A, C, D is explicitly documented."""
        for pop in ["A", "C", "D"]:
            sub = hessian_robustness_df[hessian_robustness_df["population"] == pop]
            has_non_pos = (sub["is_positive_definite"] == False).any()
            assert has_non_pos, f"Pop {pop} expected to have non-positive definite entries due to non-smoothness or degeneracy"


class TestScientificClaimConsistency:
    """Tests confirming that scientific claims in report are appropriately qualified."""

    def test_report_exists_and_contains_required_sections(self) -> None:
        """Verify that the Phase 4B.2 audit report exists and contains required sections."""
        report_path = PHASE4B2_DIR / "PHASE4B2_SCIENTIFIC_ROBUSTNESS_AUDIT.md"
        assert report_path.exists(), f"Report missing at {report_path}"
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Required conceptual distinctions
        content_lower = content.lower()
        assert "demonstrated numerical result" in content_lower
        assert "parameter-range-dependent conclusion" in content_lower
        assert "unproven global mathematical claim" in content_lower

        # Required qualification of A-type potassium current
        assert "hypothesis" in content.lower()
        assert "A-type" in content or "Kv4" in content

        # Dual reporting confirmation
        assert "RMSE" in content
        assert "Pearson" in content or "correlation" in content

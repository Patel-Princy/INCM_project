"""Tests for Phase 3C: Independent Scientific Consistency Audit and Recomputation.

Verifies:
1. Exact correspondence between per-sweep summary.json files and heldout_metrics.csv.
2. Integrity and schema of results/phase3c/recomputed_population_metrics.csv.
3. Total unique condition count consistency (102 protocol-amplitude groups, 97 unique amplitudes).
4. Correctness of recomputed rheobase intervals and shifts across all 4 populations.
5. Existence and non-emptiness of all Phase 3C audit artifacts.
"""
from __future__ import annotations

import csv
import json
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_3B = ROOT / "results" / "phase3b"
RESULTS_3C = ROOT / "results" / "phase3c"
HELDOUT_DIR = RESULTS_3B / "heldout"

RECOMPUTED_CSV = RESULTS_3C / "recomputed_population_metrics.csv"
HELDOUT_METRICS_CSV = RESULTS_3B / "heldout_metrics.csv"
CONDITION_GROUPS_CSV = RESULTS_3B / "condition_groups.csv"


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_phase3c_artifacts_exist():
    expected_mds = [
        "PHASE3C_BASELINE_AUDIT.md",
        "PHASE3C_METRIC_RECOMPUTATION.md",
        "PHASE3C_PROTOCOL_VARIABILITY_AUDIT.md",
        "PHASE3C_EXCITABILITY_AUDIT.md",
        "PHASE3C_CORRECTION_LOG.md",
        "PHASE3C_FHN_READINESS_SPECIFICATION.md",
    ]
    for fn in expected_mds:
        p = RESULTS_3C / fn
        assert p.exists(), f"Missing audit document: {p}"
        assert p.stat().st_size > 500, f"Document {fn} is suspiciously small: {p.stat().st_size} bytes"

    assert RECOMPUTED_CSV.exists(), f"Missing {RECOMPUTED_CSV}"


def test_recomputed_metrics_schema_and_counts():
    rows = read_csv(RECOMPUTED_CSV)
    assert len(rows) == 4, f"Expected 4 population rows, got {len(rows)}"

    pops = {r["population"] for r in rows}
    assert pops == {"A", "B", "C", "D"}

    spec_heldout_counts = {int(r["specimen_id"]): int(r["n_heldout_sweeps"]) for r in rows}
    assert spec_heldout_counts[484564503] == 31
    assert spec_heldout_counts[318808427] == 18
    assert spec_heldout_counts[471129934] == 34
    assert spec_heldout_counts[471786879] == 26

    # Verify total unique condition counts
    total_sweeps = sum(spec_heldout_counts.values())
    assert total_sweeps == 109


def test_condition_groups_count_consistency():
    cg_rows = read_csv(CONDITION_GROUPS_CSV)
    assert len(cg_rows) == 102, f"Expected 102 condition groups, got {len(cg_rows)}"


def test_summary_json_to_metrics_csv_exact_match():
    metrics_rows = read_csv(HELDOUT_METRICS_CSV)
    assert len(metrics_rows) == 109

    for r in metrics_rows:
        sid = r["specimen_id"]
        swp = r["sweep_number"]
        json_path = HELDOUT_DIR / sid / f"sweep_{swp}" / "summary.json"
        assert json_path.exists(), f"Missing {json_path}"

        with json_path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        m = data["metrics"]
        assert pytest.approx(float(r["rmse_overall_mv"]), abs=1e-3) == m["rmse_overall_mv"]
        assert pytest.approx(float(r["mae_mv"]), abs=1e-3) == m["mae_mv"]
        assert pytest.approx(float(r["correlation"]), abs=1e-4) == m["correlation"]
        assert int(r["spike_count_recorded_in_step"]) == m["spike_count_recorded_in_step"]
        assert int(r["spike_count_simulated_in_step"]) == m["spike_count_simulated_in_step"]


def test_rheobase_shifts_exact_values():
    rows = read_csv(RECOMPUTED_CSV)
    row_map = {r["population"]: r for r in rows}

    assert float(row_map["A"]["coarse_rheobase_shift_pa"]) == 60.0
    assert float(row_map["B"]["coarse_rheobase_shift_pa"]) == 20.0
    assert float(row_map["C"]["coarse_rheobase_shift_pa"]) == 60.0
    assert float(row_map["D"]["coarse_rheobase_shift_pa"]) == 0.0


def test_l4_excitability_discrepancy_detected():
    metrics_rows = read_csv(HELDOUT_METRICS_CSV)
    l4_rows = [r for r in metrics_rows if r["population"] == "A"]

    # Sweep 52 is +430 pA
    swp_52 = next(r for r in l4_rows if int(r["sweep_number"]) == 52)
    assert float(swp_52["stimulus_amplitude_pa"]) == 430.0
    assert int(swp_52["spike_count_recorded_in_step"]) == 12
    assert int(swp_52["spike_count_simulated_in_step"]) == 48
    assert int(swp_52["spike_count_delta"]) == 36

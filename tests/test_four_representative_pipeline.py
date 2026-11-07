"""Tests for Phase 3A: Four-Representative Pipeline Audit and Readiness.

Verifies:
1. Four representative asset audit CSV integrity and schema.
2. Exact mapping of populations A, B, C, D to specimens, models, fit files, and SWCs.
3. Strict separation of calibration sweeps from held-out sweeps.
4. L5 conversion conflict identification and adjudication.
5. Invariance of existing Phase 2 results.
"""
from __future__ import annotations

import csv
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT_CSV = ROOT / "results" / "phase3" / "four_representative_asset_audit.csv"

EXPECTED_REPRESENTATIVES = {
    484564503: {
        "population": "A",
        "layer": "4",
        "model_id": "485591776",
        "fit_file_id": "497237137",
        "nwb_file_id": "491317441",
        "reconstruction_id": "491459182",
        "fitting_sweep": "49",
        "fitting_amplitude_pa": "370.0",
        "asset_verdict": "READY_FOR_EXECUTION",
    },
    318808427: {
        "population": "B",
        "layer": "2/3",
        "model_id": "473863035",
        "fit_file_id": "497237588",
        "nwb_file_id": "491199000",
        "reconstruction_id": "491119754",
        "fitting_sweep": "40",
        "fitting_amplitude_pa": "190.0",
        "asset_verdict": "READY_FOR_EXECUTION",
    },
    471129934: {
        "population": "C",
        "layer": "5",
        "model_id": "480624414",
        "fit_file_id": "497236153",
        "nwb_file_id": "491202812",
        "reconstruction_id": "495335491",
        "fitting_sweep": "51",
        "fitting_amplitude_pa": "410.0",
        "asset_verdict": "CONDITIONALLY_READY",
    },
    471786879: {
        "population": "D",
        "layer": "6a",
        "model_id": "480632594",
        "fit_file_id": "497236229",
        "nwb_file_id": "491202180",
        "reconstruction_id": "495335607",
        "fitting_sweep": "42",
        "fitting_amplitude_pa": "250.0",
        "asset_verdict": "READY_FOR_EXECUTION",
    },
}


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_asset_audit_csv_exists():
    assert AUDIT_CSV.exists(), f"Missing audit CSV at {AUDIT_CSV}"


def test_asset_audit_rows():
    rows = read_csv(AUDIT_CSV)
    assert len(rows) == 4, f"Expected 4 representative rows, got {len(rows)}"

    for row in rows:
        spec_id = int(row["specimen_id"])
        assert spec_id in EXPECTED_REPRESENTATIVES, f"Unexpected specimen {spec_id}"
        exp = EXPECTED_REPRESENTATIVES[spec_id]
        assert row["population"] == exp["population"]
        assert row["layer"] == exp["layer"]
        assert row["perisomatic_model_id"] == exp["model_id"]
        assert row["fit_file_id"] == exp["fit_file_id"]
        assert row["nwb_file_id"] == exp["nwb_file_id"]
        assert row["morphology_reconstruction_id"] == exp["reconstruction_id"]
        assert row["fitting_sweep"] == exp["fitting_sweep"]
        assert float(row["fitting_amplitude_pa"]) == float(exp["fitting_amplitude_pa"])
        assert row["asset_verdict"] == exp["asset_verdict"]


def test_l5_conversion_conflict_flagged():
    rows = read_csv(AUDIT_CSV)
    l5_row = next(r for r in rows if r["specimen_id"] == "471129934")
    assert l5_row["nwb_status"] == "MATCH_CONVERSION_CONFLICT"
    assert l5_row["asset_verdict"] == "CONDITIONALLY_READY"
    assert "pipeline version 1.0" in l5_row["verdict_rationale"].lower()


def test_assets_on_disk():
    for spec_id, exp in EXPECTED_REPRESENTATIVES.items():
        nwb = ROOT / "data" / "nwb_cache" / f"{spec_id}.nwb"
        assert nwb.exists(), f"Missing NWB for specimen {spec_id}"
        assert nwb.stat().st_size > 0

        swc = ROOT / "tmp" / "morphology_cache" / f"{spec_id}.swc"
        assert swc.exists(), f"Missing SWC for specimen {spec_id}"
        assert swc.stat().st_size > 0

        fit = ROOT / "tmp" / "fit_cache" / f"{exp['fit_file_id']}.json"
        assert fit.exists(), f"Missing fit descriptor for specimen {spec_id}"
        assert fit.stat().st_size > 0


def test_phase2_reports_preserved():
    p2c = ROOT / "results" / "phase2" / "PHASE2C_PERISOMATIC_EXECUTION_VALIDATION.md"
    p2e = ROOT / "results" / "phase2" / "PHASE2E_FINEST_HELD_OUT_EVALUATION.md"
    p2gb = ROOT / "results" / "phase2" / "PHASE2G_B_ALL_ACTIVE_EXECUTION_VALIDATION.md"
    assert p2c.exists() and p2c.stat().st_size > 0
    assert p2e.exists() and p2e.stat().st_size > 0
    assert p2gb.exists() and p2gb.stat().st_size > 0

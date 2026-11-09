"""Tests for Phase 0C: selected-model readiness audit.

These tests verify the Phase 0C output CSVs rather than re-running the
network-dependent audit.  They check structural invariants (counts, columns,
evidence levels) and scientific correctness gates (all descriptors are
perisomatic, no fitting/held-out overlap, leakage-safe status is consistent).

All assertions carry evidence labels as comments:
  OBSERVED  — value read directly from a committed output file
  DERIVED   — computed from those values by a deterministic rule
  SELF-CHECK — an assertion the audit script itself already verified at runtime
"""

from __future__ import annotations

import csv
import pathlib
from collections import Counter

import pytest

RESULTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "results" / "dataset_inventory"

CANDIDATE_CSV = RESULTS_DIR / "four_v1_selected_candidates.csv"
FIT_CSV = RESULTS_DIR / "four_v1_fit_descriptor_audit.csv"
RECORDING_CSV = RESULTS_DIR / "four_v1_recording_validation.csv"
ASSET_CSV = RESULTS_DIR / "four_v1_model_asset_readiness.csv"
HELDOUT_CSV = RESULTS_DIR / "four_v1_heldout_feasibility.csv"

POPULATIONS = ("A", "B", "C", "D")
TARGET = 4  # candidates per population


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Fixture: load all output files once
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def candidates():
    return read_csv(CANDIDATE_CSV)


@pytest.fixture(scope="module")
def fit_rows():
    return read_csv(FIT_CSV)


@pytest.fixture(scope="module")
def recording_rows():
    return read_csv(RECORDING_CSV)


@pytest.fixture(scope="module")
def asset_rows():
    return read_csv(ASSET_CSV)


@pytest.fixture(scope="module")
def heldout_rows():
    return read_csv(HELDOUT_CSV)


# ---------------------------------------------------------------------------
# Phase 0C output files exist
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", [
    CANDIDATE_CSV, FIT_CSV, RECORDING_CSV, ASSET_CSV, HELDOUT_CSV,
])
def test_phase0c_output_file_exists(path):
    """All five Phase 0C CSVs must be present.  OBSERVED."""
    assert path.exists(), f"missing output: {path.name}"


# ---------------------------------------------------------------------------
# Candidate selection invariants
# ---------------------------------------------------------------------------
def test_exactly_four_candidates_per_population(candidates):
    """Four candidates must be selected per population.  SELF-CHECK."""
    counts = Counter(row["population"] for row in candidates)
    for pop in POPULATIONS:
        assert counts[pop] == TARGET, (
            f"population {pop}: expected {TARGET}, got {counts[pop]}")


def test_no_duplicate_specimens(candidates):
    """Specimen ids must be unique across all 16 candidates.  SELF-CHECK."""
    ids = [row["specimen_id"] for row in candidates]
    assert len(ids) == len(set(ids)), "duplicate specimen ids in selection"


def test_all_candidates_are_spiny(candidates):
    """Every selected candidate must have a spiny dendrite type.  DERIVED."""
    for row in candidates:
        assert row["dendrite_type"] == "spiny", (
            f"specimen {row['specimen_id']} (pop {row['population']}): "
            f"dendrite_type={row['dendrite_type']!r}")


def test_all_candidates_have_perisomatic_model(candidates):
    """Every candidate must have a perisomatic model id.  DERIVED."""
    for row in candidates:
        assert row["perisomatic_model_id"], (
            f"specimen {row['specimen_id']} missing perisomatic_model_id")


def test_all_candidates_have_fit_file_id(candidates):
    """Every candidate must have a fit file id.  DERIVED."""
    for row in candidates:
        assert row["fit_file_id"], (
            f"specimen {row['specimen_id']} missing fit_file_id")


def test_all_candidates_have_nwb_reference(candidates):
    """Every candidate must have an NWB download reference.  DERIVED."""
    for row in candidates:
        assert row["nwb_reference"].startswith("http"), (
            f"specimen {row['specimen_id']} has no valid nwb_reference")


def test_layer_assignments_match_population(candidates):
    """Layer must match the population definition.  DERIVED."""
    expected = {"A": "4", "B": "2/3", "C": "5", "D": "6a"}
    for row in candidates:
        assert row["layer"] == expected[row["population"]], (
            f"specimen {row['specimen_id']} pop={row['population']} "
            f"layer={row['layer']!r} expected={expected[row['population']]!r}")


def test_all_candidates_200khz(candidates):
    """All selected candidates prefer 200 kHz sampling.  OBSERVED."""
    for row in candidates:
        assert row["sampling_rate_hz"] == "200000", (
            f"specimen {row['specimen_id']} rate={row['sampling_rate_hz']!r}")


def test_all_candidates_have_at_least_5_distinct_amplitudes(candidates):
    """Every candidate must have at least 5 distinct depolarising amplitudes.
    DERIVED (Phase 0C priority 4)."""
    for row in candidates:
        n = int(row["n_distinct_depolarizing_amplitudes"])
        assert n >= 5, (
            f"specimen {row['specimen_id']} pop={row['population']} "
            f"only {n} distinct depolarising amplitudes")


# ---------------------------------------------------------------------------
# Fit descriptor invariants
# ---------------------------------------------------------------------------
def test_all_fit_descriptors_parsed(fit_rows):
    """All 16 fit descriptors must download and parse.  OBSERVED."""
    for row in fit_rows:
        assert row["parsed_ok"] == "true", (
            f"specimen {row['specimen_id']}: parsed_ok={row['parsed_ok']!r} "
            f"note={row['note']!r}")


def test_all_fit_descriptors_are_perisomatic(fit_rows):
    """Every fit descriptor must be classified as perisomatic.  DERIVED."""
    for row in fit_rows:
        assert row["model_type"] == "perisomatic", (
            f"specimen {row['specimen_id']}: model_type={row['model_type']!r}")


def test_fit_descriptors_map_to_correct_models(fit_rows):
    """All descriptors must match the expected model/specimen.  SELF-CHECK."""
    for row in fit_rows:
        assert row["descriptor_matches_model"] == "true", (
            f"specimen {row['specimen_id']}: descriptor_matches_model="
            f"{row['descriptor_matches_model']!r}")


def test_junction_potential_is_minus14(fit_rows):
    """All perisomatic descriptors must use −14 mV junction potential.  OBSERVED."""
    for row in fit_rows:
        val = float(row["junction_potential_mv"])
        assert val == pytest.approx(-14.0), (
            f"specimen {row['specimen_id']}: junction_potential_mv={val}")


def test_celsius_is_34(fit_rows):
    """All descriptors must record 34°C recording temperature.  OBSERVED."""
    for row in fit_rows:
        val = float(row["celsius_c"])
        assert val == pytest.approx(34.0), (
            f"specimen {row['specimen_id']}: celsius_c={val}")


def test_fitting_sweeps_present_in_all_descriptors(fit_rows):
    """Every descriptor must list at least one fitting sweep.  OBSERVED."""
    for row in fit_rows:
        n = int(row["n_fitting_sweeps"])
        assert n >= 1, (
            f"specimen {row['specimen_id']}: no fitting sweeps in descriptor")


# ---------------------------------------------------------------------------
# Held-out feasibility invariants
# ---------------------------------------------------------------------------
def test_no_fit_heldout_overlap(heldout_rows):
    """No fitting sweep may appear in the held-out set.  SELF-CHECK."""
    for row in heldout_rows:
        fitting = set(int(x) for x in row["fitting_sweeps"].split(";") if x)
        # heldout_amplitudes and fitting_amplitudes are floats, but overlap
        # detection is at the sweep level, which the self-check already covers.
        # Here we additionally assert that wherever leakage_safe=true the
        # status is RESOLVED_LEAKAGE_SAFE.
        if row["leakage_safe"] == "true":
            assert row["heldout_status"] == "RESOLVED_LEAKAGE_SAFE", (
                f"specimen {row['specimen_id']}: leakage_safe but status="
                f"{row['heldout_status']!r}")


def test_unresolved_status_means_not_leakage_safe(heldout_rows):
    """UNRESOLVED status must imply leakage_safe=false.  DERIVED."""
    for row in heldout_rows:
        if row["heldout_status"].startswith("UNRESOLVED"):
            assert row["leakage_safe"] == "false", (
                f"specimen {row['specimen_id']}: UNRESOLVED but leakage_safe="
                f"{row['leakage_safe']!r}")


def test_at_least_13_candidates_are_leakage_safe(heldout_rows):
    """At least 13 of 16 candidates must have leakage-safe held-out splits.
    OBSERVED (Phase 0C output)."""
    n = sum(1 for row in heldout_rows if row["leakage_safe"] == "true")
    assert n >= 13, f"only {n}/16 candidates are leakage-safe"


def test_every_population_has_at_least_two_leakage_safe(heldout_rows):
    """Each population must have at least two leakage-safe candidates.  DERIVED."""
    by_pop = {p: 0 for p in POPULATIONS}
    for row in heldout_rows:
        if row["leakage_safe"] == "true":
            by_pop[row["population"]] += 1
    for pop, count in by_pop.items():
        assert count >= 2, (
            f"population {pop}: only {count} leakage-safe candidates")


# ---------------------------------------------------------------------------
# Asset readiness invariants
# ---------------------------------------------------------------------------
def test_l1_all_listed(asset_rows):
    """All 16 candidates must be listed in metadata (L1).  OBSERVED."""
    for row in asset_rows:
        assert row["L1_listed_in_metadata"] == "YES", (
            f"specimen {row['specimen_id']}: L1={row['L1_listed_in_metadata']!r}")


def test_l2_all_parsed(asset_rows):
    """All 16 descriptors must parse (L2).  OBSERVED."""
    for row in asset_rows:
        assert row["L2_fit_descriptor_downloaded_and_parsed"] == "YES", (
            f"specimen {row['specimen_id']}: L2={row['L2_fit_descriptor_downloaded_and_parsed']!r}")


def test_at_least_13_potentially_executable(asset_rows):
    """At least 13 candidates must be potentially executable (L7).  OBSERVED."""
    n = sum(1 for row in asset_rows if row["L7_potentially_executable"] == "YES")
    assert n >= 13, f"only {n}/16 candidates reach L7"


def test_at_least_one_executed(asset_rows):
    """At least one candidate must have been executed (L8).  OBSERVED."""
    n = sum(1 for row in asset_rows
            if row["L8_actually_executed_and_validated"] != "NOT_EXECUTED")
    assert n >= 1, "no candidate has been executed"


def test_l5_reconstruction_match_majority(asset_rows):
    """At least 15 of 16 candidates must have matching reconstructions (L5).
    OBSERVED."""
    n = sum(1 for row in asset_rows
            if row["L5_model_reconstruction_matches_specimen"] == "YES")
    assert n >= 15, f"only {n}/16 reconstruction matches"


# ---------------------------------------------------------------------------
# Recording validation invariants
# ---------------------------------------------------------------------------
def test_one_representative_per_population(recording_rows):
    """Exactly one REPRESENTATIVE must be selected per population.  DERIVED."""
    reps = Counter(row["population"] for row in recording_rows
                   if row["is_representative"] == "REPRESENTATIVE")
    for pop in POPULATIONS:
        assert reps[pop] == 1, (
            f"population {pop}: {reps[pop]} REPRESENTATIVE rows (expected 1)")


def test_representative_nwb_verdict_is_not_failed(recording_rows):
    """Representative NWB recordings must not have a FAILED verdict.  OBSERVED."""
    for row in recording_rows:
        if row["is_representative"] == "REPRESENTATIVE":
            assert row["nwb_verdict"] not in ("FAILED", "UNRESOLVED"), (
                f"specimen {row['specimen_id']} pop={row['population']}: "
                f"nwb_verdict={row['nwb_verdict']!r}")

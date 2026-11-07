"""Integration checks over the generated inventory outputs (Step 8).

These tests read the CSV files produced by ``allen_inventory.py`` and verify the
audit's own quality requirements independently of the script's internal checks.
They need no network access; they are skipped when the outputs have not been
generated yet.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

import allen_inventory as inv

ALLOWED_ELIGIBILITY = {"PASS", "CONDITIONAL", "FAIL", "UNKNOWN"}
ALLOWED_MODEL_CLASSES = {"biophysical_perisomatic", "biophysical_all_active",
                         "biophysical_other", "glif", "unknown"}
ALLOWED_CLAMP_MODES = {"current_clamp", "voltage_clamp", ""}
ALLOWED_CATEGORIES = {"long_square", "short_square", "ramp", "noise", "other"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def cells() -> list[dict[str, str]]:
    if not inv.CELL_INVENTORY_CSV.exists():
        pytest.skip("cell_inventory.csv not generated yet")
    return read_csv(inv.CELL_INVENTORY_CSV)


@pytest.fixture(scope="module")
def models() -> list[dict[str, str]]:
    if not inv.MODEL_INVENTORY_CSV.exists():
        pytest.skip("model_inventory.csv not generated yet")
    return read_csv(inv.MODEL_INVENTORY_CSV)


@pytest.fixture(scope="module")
def regions() -> list[dict[str, str]]:
    if not inv.REGION_SUMMARY_CSV.exists():
        pytest.skip("region_summary.csv not generated yet")
    return read_csv(inv.REGION_SUMMARY_CSV)


@pytest.fixture(scope="module")
def sweeps() -> list[dict[str, str]]:
    if not inv.SWEEP_INVENTORY_CSV.exists():
        pytest.skip("sweep_inventory.csv not generated yet")
    return read_csv(inv.SWEEP_INVENTORY_CSV)


# --------------------------------------------------------------------------
# Files exist, open, and carry the documented schema
# --------------------------------------------------------------------------
def test_all_four_inventories_exist_and_open():
    for path in (inv.CELL_INVENTORY_CSV, inv.REGION_SUMMARY_CSV,
                 inv.SWEEP_INVENTORY_CSV, inv.MODEL_INVENTORY_CSV):
        assert path.exists(), f"missing output: {path}"
        rows = read_csv(path)
        assert rows, f"{path.name} has no data rows"


def test_cell_inventory_columns_match_schema(cells):
    assert list(cells[0].keys()) == inv.CELL_COLUMNS


def test_model_inventory_columns_match_schema(models):
    assert list(models[0].keys()) == inv.MODEL_COLUMNS


def test_region_summary_columns_match_schema(regions):
    assert list(regions[0].keys()) == inv.REGION_COLUMNS


def test_sweep_inventory_columns_match_schema(sweeps):
    assert list(sweeps[0].keys()) == inv.SWEEP_COLUMNS


# --------------------------------------------------------------------------
# Uniqueness / key separation
# --------------------------------------------------------------------------
def test_specimen_ids_are_unique(cells):
    ids = [row["specimen_id"] for row in cells]
    duplicates = len(ids) - len(set(ids))
    assert duplicates == 0, f"{duplicates} duplicated specimen_id rows"


def test_model_ids_are_unique(models):
    ids = [row["model_id"] for row in models]
    duplicates = len(ids) - len(set(ids))
    assert duplicates == 0, f"{duplicates} duplicated model_id rows"


def test_model_ids_are_disjoint_from_specimen_ids(cells, models):
    specimen_ids = {row["specimen_id"] for row in cells}
    model_ids = {row["model_id"] for row in models}
    assert not (specimen_ids & model_ids)


def test_sweep_rows_are_unique_per_specimen_and_number(sweeps):
    keys = [(row["specimen_id"], row["sweep_number"]) for row in sweeps]
    duplicates = len(keys) - len(set(keys))
    assert duplicates == 0, f"{duplicates} duplicated (specimen_id, sweep_number) rows"


def test_every_model_references_an_inventoried_specimen(cells, models):
    specimen_ids = {row["specimen_id"] for row in cells}
    orphans = [row["model_id"] for row in models if row["specimen_id"] not in specimen_ids]
    assert not orphans


def test_every_sweep_references_an_inventoried_specimen(cells, sweeps):
    specimen_ids = {row["specimen_id"] for row in cells}
    orphans = {row["specimen_id"] for row in sweeps if row["specimen_id"] not in specimen_ids}
    assert not orphans


# --------------------------------------------------------------------------
# Region counts reconcile with the specimen inventory
# --------------------------------------------------------------------------
def test_region_summary_specimen_counts_match_cell_inventory(cells, regions):
    layer_rows = [row for row in regions if row["cortical_layer"]]
    assert sum(int(row["n_specimens"]) for row in layer_rows) == len(cells)


def test_region_summary_eligibility_counts_match_cell_inventory(cells, regions):
    layer_rows = [row for row in regions if row["cortical_layer"]]
    for status, column in (("PASS", "n_pass"), ("CONDITIONAL", "n_conditional"),
                           ("FAIL", "n_fail"), ("UNKNOWN", "n_unknown")):
        from_cells = sum(1 for cell in cells if cell["eligibility"] == status)
        from_regions = sum(int(row[column]) for row in layer_rows)
        assert from_cells == from_regions, f"{status}: cells={from_cells} regions={from_regions}"


def test_region_summary_biophysical_counts_match_cell_inventory(cells, regions):
    layer_rows = [row for row in regions if row["cortical_layer"]]
    for column, cell_column in (("n_with_perisomatic", "n_biophysical_perisomatic"),
                                ("n_with_all_active", "n_biophysical_all_active"),
                                ("n_with_any_biophysical", "n_biophysical_models")):
        from_cells = sum(1 for cell in cells if int(cell[cell_column] or 0) > 0)
        from_regions = sum(int(row[column]) for row in layer_rows)
        assert from_cells == from_regions, column


def test_absent_regions_are_reported_with_zero_specimens(regions):
    absent = [row for row in regions if row["status"] != "present"]
    for row in absent:
        assert int(row["n_specimens"]) == 0
        assert row["note"], "an absent/unknown region must carry an explanatory note"


def test_region_level_rows_with_no_cells_explain_why(regions):
    """A whole-region row with zero specimens must say whether that is confirmed.

    This distinguishes `MOp` (structure present, zero cells returned) from `ALM`
    (acronym absent from the ontology) and from a region the audit never checked.
    """
    empty = [row for row in regions if not row["cortical_layer"]]
    assert empty, "expected at least one region-level row"
    for row in empty:
        assert int(row["n_specimens"]) == 0
        assert row["note"].strip(), (
            f"region {row['region_acronym']} has zero specimens but no explanatory note")
        assert row["status"] in {"present", "absent_from_ontology", "unknown"}


def test_zero_specimen_region_note_is_not_confused_with_ontology_absence(regions):
    """`present` with zero cells and `absent_from_ontology` need different wording."""
    present_empty = [row for row in regions
                     if row["status"] == "present" and not row["cortical_layer"]]
    absent = [row for row in regions if row["status"] == "absent_from_ontology"]
    for row in present_empty:
        assert "zero cell specimens" in row["note"]
    for row in absent:
        assert "zero rows" in row["note"]
        assert "zero cell specimens" not in row["note"]


# --------------------------------------------------------------------------
# GLIF separation
# --------------------------------------------------------------------------
def test_glif_models_are_never_flagged_biophysical(models):
    offenders = [row["model_id"] for row in models
                 if row["model_class"] == "glif" and row["is_biophysical"] == "True"]
    assert not offenders


def test_biophysical_models_are_never_flagged_glif(models):
    offenders = [row["model_id"] for row in models
                 if row["model_class"].startswith("biophysical")
                 and row["is_biophysical"] != "True"]
    assert not offenders


def test_model_classes_are_from_the_verified_vocabulary(models):
    assert {row["model_class"] for row in models} <= ALLOWED_MODEL_CLASSES


def test_glif_templates_carry_glif_names(models):
    for row in models:
        if row["model_class"] == "glif":
            assert "LIF" in row["template_name"] or "Integrate" in row["template_name"]


def test_cell_biophysical_counts_equal_perisomatic_plus_all_active(cells):
    for cell in cells:
        assert int(cell["n_biophysical_models"]) == \
            int(cell["n_biophysical_perisomatic"]) + int(cell["n_biophysical_all_active"])


def test_cells_with_biophysical_model_reference_one(cells):
    for cell in cells:
        if int(cell["n_biophysical_models"]) > 0:
            assert cell["biophysical_model_id"], cell["specimen_id"]
            assert cell["biophysical_classes"]


# --------------------------------------------------------------------------
# Missing values preserved, nothing fabricated
# --------------------------------------------------------------------------
@pytest.mark.parametrize("path_attr", ["CELL_INVENTORY_CSV", "REGION_SUMMARY_CSV",
                                       "MODEL_INVENTORY_CSV", "SWEEP_INVENTORY_CSV"])
def test_no_placeholder_text_written_for_missing_values(path_attr):
    """Missing metadata must be an empty cell, never 'nan'/'None'/'null'."""
    path = getattr(inv, path_attr)
    if not path.exists():
        pytest.skip(f"{path.name} not generated yet")
    placeholders = {"nan", "none", "null", "<na>"}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            for column, value in row.items():
                assert value.strip().lower() not in placeholders, \
                    f"{path.name}:{column} holds placeholder '{value}'"


def test_eligibility_values_are_from_the_allowed_vocabulary(cells):
    assert {row["eligibility"] for row in cells} <= ALLOWED_ELIGIBILITY


def test_every_cell_has_a_classification(cells):
    assert all(row["eligibility"] for row in cells)


def test_fail_cells_always_state_a_confirmed_absence(cells):
    """FAIL must be justified by a confirmed absence, never by missing data."""
    for cell in cells:
        if cell["eligibility"] == "FAIL":
            reasons = cell["eligibility_concerns"].lower()
            assert ("confirmed" in reasons or "no electrophysiology" in reasons
                    or "zero current-clamp" in reasons or "not mus musculus" in reasons
                    or "could not be identified" in reasons), cell["specimen_id"]


def test_pass_cells_meet_every_documented_criterion(cells):
    for cell in cells:
        if cell["eligibility"] != "PASS":
            continue
        assert cell["species"] == "Mus musculus"
        assert cell["region_acronym"]
        assert cell["ephys_result_id"]
        assert cell["ephys_failed"] == "False"
        assert int(cell["n_long_square_cc"]) >= inv.DEFAULT_MIN_LONG_SQUARE
        assert int(cell["n_long_square_depolarizing_cc"]) >= \
            inv.DEFAULT_MIN_DEPOLARIZING_LONG_SQUARE
        assert int(cell["n_biophysical_models"]) > 0
        assert cell["biophysical_model_download_url"]
        assert cell["nwb_download_url"]


def test_pass_and_conditional_cells_are_flagged_for_validation(cells):
    for cell in cells:
        if cell["eligibility"] in ("PASS", "CONDITIONAL"):
            if cell["nwb_download_url"]:
                assert cell["needs_nwb_validation"] == "True"


# --------------------------------------------------------------------------
# Sweep inventory sanity
# --------------------------------------------------------------------------
def test_sweep_categories_and_clamp_modes_are_valid(sweeps):
    assert {row["stimulus_category"] for row in sweeps} <= ALLOWED_CATEGORIES
    assert {row["clamp_mode"] for row in sweeps} <= ALLOWED_CLAMP_MODES


def test_current_clamp_long_square_counts_reconcile(cells, sweeps):
    recomputed: dict[str, int] = {}
    for row in sweeps:
        if row["stimulus_category"] == "long_square" and row["clamp_mode"] == "current_clamp":
            key = row["specimen_id"]
            recomputed[key] = recomputed.get(key, 0) + 1
    for cell in cells:
        expected = int(cell["n_long_square_cc"] or 0)
        assert recomputed.get(cell["specimen_id"], 0) == expected, cell["specimen_id"]


def test_stimulus_names_are_recorded_verbatim(sweeps):
    for row in sweeps:
        assert row["stimulus_name"], "stimulus_name must never be blanked out"


# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------
def test_provenance_manifest_covers_generated_outputs():
    if not inv.MANIFEST_PATH.exists():
        pytest.skip("manifest not written yet")
    import json
    manifest = json.loads(inv.MANIFEST_PATH.read_text(encoding="utf-8"))
    for path in (inv.CELL_INVENTORY_CSV, inv.REGION_SUMMARY_CSV,
                 inv.SWEEP_INVENTORY_CSV, inv.MODEL_INVENTORY_CSV):
        if path.exists():
            assert path.relative_to(inv.PROJECT_ROOT).as_posix() in manifest["files"]


def test_report_and_summary_exist_and_agree_on_totals(cells):
    if not inv.REPORT_MD.exists() or not inv.SUMMARY_JSON.exists():
        pytest.skip("report not generated yet")
    import json
    summary = json.loads(inv.SUMMARY_JSON.read_text(encoding="utf-8"))
    assert summary["totals"]["specimens_retrieved"] == len(cells)
    report = inv.REPORT_MD.read_text(encoding="utf-8")
    assert f"**{len(cells)}**" in report


# --------------------------------------------------------------------------
# Database-wide coverage (Step 2b) -- the motor-absence evidence
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def coverage() -> dict:
    if not inv.COVERAGE_JSON.exists():
        pytest.skip("database_structure_coverage.json not generated "
                    "(run without --skip-coverage)")
    import json
    return json.loads(inv.COVERAGE_JSON.read_text(encoding="utf-8"))


def test_coverage_scan_completed_without_api_errors(coverage):
    assert coverage["complete"] is True, (
        f"coverage scan incomplete: {coverage.get('totals')}")


def test_coverage_totals_reconcile_with_structure_table(coverage):
    structures = coverage["structures"]
    totals = coverage["totals"]
    assert totals["cells"] == sum(row["cells"] for row in structures)
    assert totals["mouse_cells"] == sum(row["mouse_cells"] for row in structures)
    assert totals["cells"] == totals["mouse_cells"] + totals["human_or_other_cells"]
    assert totals["biophysical_models"] == sum(row["biophysical_models"] for row in structures)
    assert totals["biophysical_models"] == (totals["biophysical_perisomatic"]
                                            + totals["biophysical_all_active"])
    assert coverage["cell_specimens_retrieved"] == totals["cells"]


def test_coverage_candidate_specimens_are_a_subset_of_the_database(coverage, cells):
    """The candidate inventory must never claim more cells than the database holds."""
    assert len(cells) <= coverage["totals"]["cells"]


def test_every_motor_structure_checked_has_zero_cell_specimens(coverage):
    """The motor absence must be a confirmed zero, never an unresolved query."""
    motor = [row for row in coverage["region_level_cell_counts"]
             if row["role"] in ("motor", "control")]
    assert motor, "no motor/control structures were checked"
    for row in motor:
        if row["ontology_status"] == "present":
            assert row["cell_specimens_at_this_level"] == 0, (
                f"{row['structure_acronym']} unexpectedly holds cells")
        else:
            assert row["cell_specimens_at_this_level"] is None
            assert row["note"], (
                f"{row['structure_acronym']} is not in the ontology but carries no note")


def test_sensory_parent_level_zero_is_the_query_pattern_control(coverage):
    """Sensory parents hold 0 cells while their layers hold many.

    This is what proves the motor zeros are not a level-of-attachment artefact.
    """
    rows = {row["structure_acronym"]: row for row in coverage["region_level_cell_counts"]}
    for parent in ("VISp", "VISl", "VISal"):
        if parent in rows:
            assert rows[parent]["cell_specimens_at_this_level"] == 0
    layers = [row for row in coverage["region_level_cell_counts"]
              if row["role"] == "sensory" and row["checked_because"].startswith("layer of")]
    assert sum(int(row["cell_specimens_at_this_level"] or 0) for row in layers) > 0


def test_no_mouse_motor_structure_carries_a_biophysical_model(coverage):
    totals = coverage["totals"]
    mouse_motor = [row for row in coverage["structures"]
                   if row["mouse_cells"] and "motor" in str(row["name"]).lower()]
    for row in mouse_motor:
        assert row["biophysical_models"] == 0, (
            f"{row['acronym']} is a mouse motor structure with biophysical models")
    assert totals["structures_with_four_plus_mouse_biophysical"] >= 0


def test_summary_records_motor_confirmed_empty_flag(coverage):
    if not inv.SUMMARY_JSON.exists():
        pytest.skip("summary not generated yet")
    import json
    summary = json.loads(inv.SUMMARY_JSON.read_text(encoding="utf-8"))
    best = summary["best_supported"]
    motor_cells = sum(int(counts.get("n_specimens") or 0)
                      for _name, counts in best["motor_ranking"])
    assert best["motor_confirmed_empty"] == (motor_cells == 0)
    assert best["comparison_feasible"] is bool(best["sensory"] and best["motor"])


# --------------------------------------------------------------------------
# Identifier rendering
# --------------------------------------------------------------------------
ID_COLUMNS = {
    "cell_inventory.csv": ("specimen_id", "structure_id", "donor_id", "ephys_result_id",
                           "nwb_file_id", "reconstruction_id", "biophysical_model_id",
                           "cell_reporter_id", "organism_id"),
    "model_inventory.csv": ("model_id", "specimen_id", "neuronal_model_template_id",
                            "neuron_reconstruction_id", "well_known_file_id",
                            "well_known_file_type_id"),
    "sweep_inventory.csv": ("specimen_id", "sweep_id"),
    "region_summary.csv": ("structure_id",),
}


def test_identifier_columns_are_integers_never_floats(cells, models, regions, sweeps):
    """No identifier may be written as ``486509232.0``.

    A sparse column silently widens to float64 in pandas, which would corrupt
    every id in it and break joins between the inventories.
    """
    datasets = {"cell_inventory.csv": cells, "model_inventory.csv": models,
                "region_summary.csv": regions, "sweep_inventory.csv": sweeps}
    offenders = []
    for name, columns in ID_COLUMNS.items():
        for column in columns:
            for row in datasets[name]:
                value = row.get(column, "")
                if value and ("." in value or "e" in value.lower()):
                    offenders.append(f"{name}:{column}={value}")
                    break
    assert not offenders, f"float-rendered identifiers: {offenders[:10]}"


def test_specimen_ids_read_back_as_integers(cells):
    for row in cells:
        assert row["specimen_id"].isdigit(), row["specimen_id"]

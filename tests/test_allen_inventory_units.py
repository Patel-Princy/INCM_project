"""Offline unit tests for the Allen inventory audit logic.

No network access is required: every test exercises a pure function with
hand-built records that mirror the *verified* Allen RMA v2 response shapes
recorded in ``src/data_audit/api_schema_probe.py``.
"""
from __future__ import annotations

import csv

import pytest

import allen_inventory as inv


# --------------------------------------------------------------------------
# Fixtures mirroring verified API shapes
# --------------------------------------------------------------------------
TEMPLATES = {
    329230710: {"name": "Biophysical - perisomatic",
                "description": "Biophysical Neuronal Model Template"},
    491455321: {"name": "Biophysical - all active",
                "description": "Biophysical Neuronal Model Template"},
    395310469: {"name": "1 Leaky Integrate and Fire (LIF)",
                "description": "Generalized Leaky Integrate-and-Fire Model Template"},
    471355161: {"name": "4 LIF-R + Afterspike Currents (LIF-R-ASC)",
                "description": "Generalized Leaky Integrate-and-Fire Model Template"},
}

THRESHOLDS = {"min_long_square": 6, "min_depolarizing_long_square": 3}


def make_cell(**overrides):
    cell = {
        "specimen_id": 485909730,
        "organism_id": inv.ORGANISM_MOUSE,
        "species": "Mus musculus",
        "region_acronym": "VISp",
        "region_name": "Primary visual area",
        "cortical_layer": "5",
        "ephys_result_id": 485909728,
        "ephys_failed": False,
        "n_long_square_cc": 12,
        "n_long_square_depolarizing_cc": 6,
        "n_biophysical_models": 1,
        "n_biophysical_perisomatic": 1,
        "n_biophysical_all_active": 0,
        "n_glif_models": 0,
        "biophysical_classes": "perisomatic",
        "biophysical_model_download_url": "http://api.brain-map.org/api/v2/"
                                          "well_known_file_download/501606122",
        "nwb_download_url": "http://api.brain-map.org/api/v2/"
                            "well_known_file_download/491316386",
    }
    cell.update(overrides)
    return cell


def make_sweep(specimen_id=485909730, sweep_number=40, name="Long Square",
               units="Amps", amplitude=250.0):
    return {
        "id": 1, "specimen_id": specimen_id, "sweep_number": sweep_number,
        "stimulus_name": name, "stimulus_description": "C1LSCOARSE150216[0]",
        "stimulus_units": units, "stimulus_absolute_amplitude": amplitude,
        "stimulus_relative_amplitude": 2.5, "stimulus_duration": 1.0,
        "stimulus_start_time": 1.02, "num_spikes": 5,
    }


def make_model(model_id, specimen_id, template_id, name="m"):
    return {"id": model_id, "specimen_id": specimen_id, "name": name,
            "neuronal_model_template_id": template_id,
            "neuron_reconstruction_id": None}


# --------------------------------------------------------------------------
# Template classification: GLIF must never count as biophysical
# --------------------------------------------------------------------------
@pytest.mark.parametrize("template_id,expected", [
    (329230710, "biophysical_perisomatic"),
    (491455321, "biophysical_all_active"),
    (395310469, "glif"),
    (471355161, "glif"),
])
def test_classify_template_known_ids(template_id, expected):
    assert inv.classify_template(TEMPLATES, template_id)[0] == expected


def test_glif_is_not_biophysical():
    for template_id in (395310469, 471355161):
        model_class, _ = inv.classify_template(TEMPLATES, template_id)
        assert model_class == "glif"
        assert not model_class.startswith("biophysical")


def test_unknown_template_is_not_silently_biophysical():
    assert inv.classify_template(TEMPLATES, 999999)[0] == "unknown"
    assert inv.classify_template(TEMPLATES, None)[0] == "unknown"


def test_build_model_records_flags_glif_correctly():
    models = [make_model(10, 1, 329230710, "Biophysical - perisomatic_x"),
              make_model(20, 1, 395310469, "1 Leaky Integrate and Fire (LIF)_x")]
    rows = inv.build_model_records({1: {"region_acronym": "VISp", "cortical_layer": "5",
                                        "species": "Mus musculus"}},
                                   TEMPLATES, models, {}, source="test")
    by_id = {row["model_id"]: row for row in rows}
    assert by_id[10]["is_biophysical"] is True
    assert by_id[10]["model_class"] == "biophysical_perisomatic"
    assert by_id[20]["is_biophysical"] is False
    assert by_id[20]["model_class"] == "glif"


def test_model_records_separate_model_id_from_specimen_id():
    rows = inv.build_model_records({}, TEMPLATES,
                                   [make_model(486509232, 485909730, 329230710)],
                                   {}, source="test")
    assert rows[0]["model_id"] == 486509232
    assert rows[0]["specimen_id"] == 485909730
    assert rows[0]["model_id"] != rows[0]["specimen_id"]


def test_unresolved_model_reference_is_recorded_not_dropped():
    rows = inv.build_model_records({}, TEMPLATES,
                                   [make_model(10, 1, 329230710)], {}, source="test")
    assert rows[0]["availability_status"] == \
        "metadata_present_download_reference_unresolved"
    assert rows[0]["download_url"] == ""


def test_resolved_model_reference_records_official_download_url():
    reference = {10: {"well_known_file_id": "501606122",
                      "well_known_file_type_id": "329230374",
                      "path": "/external/x/485909730_fit.json",
                      "download_url": "http://api.brain-map.org/api/v2/"
                                      "well_known_file_download/501606122"}}
    rows = inv.build_model_records({}, TEMPLATES, [make_model(10, 1, 329230710)],
                                   reference, source="test")
    assert rows[0]["availability_status"] == \
        "metadata_present_download_reference_resolved"
    assert rows[0]["download_url"].startswith("http://api.brain-map.org/")


# --------------------------------------------------------------------------
# Specimen tag / transgenic line parsing
# --------------------------------------------------------------------------
def test_tag_value_extracts_dendrite_and_apical_status():
    tags = [{"id": 470927414, "name": "apical - intact"},
            {"id": 470928297, "name": "dendrite type - spiny"}]
    assert inv.tag_value(tags, "dendrite type - ") == "spiny"
    assert inv.tag_value(tags, "apical - ") == "intact"


def test_tag_value_missing_returns_empty_not_false():
    assert inv.tag_value([{"name": "apical - intact"}], "dendrite type - ") == ""
    assert inv.tag_value(None, "apical - ") == ""
    assert inv.tag_value([], "apical - ") == ""


def test_transgenic_line_names_splits_driver_and_reporter():
    donor = {"full_genotype": "Cux2-CreERT2/wt;Ai14(RCL-tdT)/wt",
             "transgenic_lines": [
                 {"name": "Ai14(RCL-tdT)", "transgenic_line_type_name": "reporter"},
                 {"name": "Cux2-CreERT2", "transgenic_line_type_name": "driver"}]}
    drivers, reporters, genotype = inv.transgenic_line_names(donor)
    assert drivers == "Cux2-CreERT2"
    assert reporters == "Ai14(RCL-tdT)"
    assert genotype == "Cux2-CreERT2/wt;Ai14(RCL-tdT)/wt"


def test_transgenic_line_names_handles_absent_donor():
    assert inv.transgenic_line_names(None) == ("", "", "")
    assert inv.transgenic_line_names({}) == ("", "", "")


# --------------------------------------------------------------------------
# Region / layer derivation
# --------------------------------------------------------------------------
def test_split_region_layer_uses_parent_acronym():
    structure = {"acronym": "VISp5", "parent_structure_id": 385}
    assert inv.split_region_layer(structure, {385: "VISp"}) == ("VISp", "5")


def test_split_region_layer_handles_two_three_and_sublayers():
    parents = {385: "VISp", 985: "MOp"}
    assert inv.split_region_layer({"acronym": "VISp2/3", "parent_structure_id": 385},
                                  parents) == ("VISp", "2/3")
    assert inv.split_region_layer({"acronym": "MOp6a", "parent_structure_id": 985},
                                  parents) == ("MOp", "6a")


def test_split_region_layer_unknown_parent_is_preserved_not_invented():
    """An unresolvable parent must yield an unknown region, never a guess.

    The raw structure acronym is preserved separately in the ``structure_acronym``
    column of the cell inventory, so nothing is lost by leaving the region empty.
    """
    region, layer = inv.split_region_layer({"acronym": "VISp5", "parent_structure_id": 1}, {})
    assert region == ""
    assert layer == ""


def test_split_region_layer_partial_prefix_match_is_not_split():
    """A layer acronym that does not start with the parent acronym is not guessed at."""
    assert inv.split_region_layer({"acronym": "VISp5", "parent_structure_id": 385},
                                  {385: "VISl"}) == ("VISl", "")


# --------------------------------------------------------------------------
# NWB reference selection
# --------------------------------------------------------------------------
def test_nwb_reference_prefers_compressed_download_file():
    ephys = {"id": 1, "failed": False, "well_known_files": [
        {"id": 11, "well_known_file_type_id": inv.WKFT_NWB_UNCOMPRESSED,
         "download_link": "/api/v2/well_known_file_download/11", "path": "a.nwb"},
        {"id": 22, "well_known_file_type_id": inv.WKFT_NWB_DOWNLOAD,
         "download_link": "/api/v2/well_known_file_download/22", "path": "b.nwb"},
    ]}
    file_id, _path, url = inv.nwb_reference(ephys)
    assert file_id == "22"
    assert url == "http://api.brain-map.org/api/v2/well_known_file_download/22"


def test_nwb_reference_absent_returns_empty():
    assert inv.nwb_reference(None) == ("", "", "")
    assert inv.nwb_reference({"id": 1, "well_known_files": []}) == ("", "", "")
    assert inv.nwb_reference({"id": 1}) == ("", "", "")


# --------------------------------------------------------------------------
# Eligibility classification
# --------------------------------------------------------------------------
def test_pass_when_all_metadata_criteria_confirmed():
    status, satisfied, concerns = inv.classify_eligibility(make_cell(), THRESHOLDS, set())
    assert status == "PASS"
    assert any("Long Square" in item for item in satisfied)
    # Phase 0 downloads nothing, so a PASS must still say validation is pending.
    assert any("metadata-level only" in item for item in concerns)


def test_conditional_when_long_square_sweeps_below_threshold():
    status, _s, concerns = inv.classify_eligibility(
        make_cell(n_long_square_cc=3, n_long_square_depolarizing_cc=2), THRESHOLDS, set())
    assert status == "CONDITIONAL"
    assert any("threshold" in item for item in concerns)


def test_conditional_when_only_glif_models_present():
    status, _s, concerns = inv.classify_eligibility(
        make_cell(n_biophysical_models=0, n_biophysical_perisomatic=0,
                  n_glif_models=2, biophysical_classes="",
                  biophysical_model_download_url=""), THRESHOLDS, set())
    assert status == "CONDITIONAL"
    assert any("GLIF only" in item for item in concerns)


def test_conditional_when_model_reference_unresolved():
    status, _s, concerns = inv.classify_eligibility(
        make_cell(biophysical_model_download_url=""), THRESHOLDS, set())
    assert status == "CONDITIONAL"
    assert any("no download reference resolved" in item for item in concerns)


def test_fail_on_confirmed_absent_ephys_result():
    status, _s, concerns = inv.classify_eligibility(
        make_cell(ephys_result_id=None, ephys_available=False), THRESHOLDS, set())
    assert status == "FAIL"
    assert any("confirmed absent" in item for item in concerns)


def test_fail_on_confirmed_failed_ephys_result():
    status, _s, concerns = inv.classify_eligibility(
        make_cell(ephys_failed=True), THRESHOLDS, set())
    assert status == "FAIL"
    assert any("failed == true" in item for item in concerns)


def test_fail_on_zero_current_clamp_long_square():
    status, _s, concerns = inv.classify_eligibility(
        make_cell(n_long_square_cc=0, n_long_square_depolarizing_cc=0), THRESHOLDS, set())
    assert status == "FAIL"
    assert any("zero current-clamp Long Square" in item for item in concerns)


def test_fail_on_non_mouse_species():
    status, _s, concerns = inv.classify_eligibility(
        make_cell(organism_id=1, species="Homo sapiens"), THRESHOLDS, set())
    assert status == "FAIL"
    assert any("not Mus musculus" in item for item in concerns)


def test_unknown_on_api_failure_is_never_fail():
    """Missing information must be recorded as UNKNOWN, not FAIL.

    When the specimen stage itself is incomplete, an absent ``ephys_result_id``
    may simply be a row we never retrieved, so it cannot be a confirmed absence.
    """
    status, _s, concerns = inv.classify_eligibility(
        make_cell(ephys_result_id=None), THRESHOLDS, {"specimens"})
    assert status == "UNKNOWN"
    assert not any("confirmed absent" in item for item in concerns)


def test_absent_ephys_result_with_complete_specimen_stage_is_a_confirmed_fail():
    """A complete specimen record with no ephys result IS a confirmed absence.

    ``ephys_sweeps`` being incomplete is irrelevant here: with no ephys result
    there are no sweeps to retrieve for this cell.
    """
    status, _s, concerns = inv.classify_eligibility(
        make_cell(ephys_result_id=None), THRESHOLDS, {"ephys_sweeps"})
    assert status == "FAIL"
    assert any("confirmed absent" in item for item in concerns)


def test_unresolvable_region_is_unknown_not_fail():
    """An unresolved target region is unavailable metadata, not a confirmed absence."""
    status, _s, concerns = inv.classify_eligibility(
        make_cell(region_acronym=""), THRESHOLDS, set())
    assert status == "UNKNOWN"
    assert any("could not be resolved" in item for item in concerns)


def test_unknown_when_specimen_stage_incomplete():
    status, _s, concerns = inv.classify_eligibility(make_cell(), THRESHOLDS, {"specimens"})
    assert status == "UNKNOWN"
    assert any("specimen metadata retrieval incomplete" in item for item in concerns)


def test_unknown_when_model_stage_incomplete():
    status, _s, _c = inv.classify_eligibility(make_cell(), THRESHOLDS, {"neuronal_models"})
    assert status == "UNKNOWN"


def test_thresholds_are_configurable():
    strict = {"min_long_square": 20, "min_depolarizing_long_square": 10}
    assert inv.classify_eligibility(make_cell(), strict, set())[0] == "CONDITIONAL"
    relaxed = {"min_long_square": 2, "min_depolarizing_long_square": 1}
    assert inv.classify_eligibility(
        make_cell(n_long_square_cc=3, n_long_square_depolarizing_cc=1), relaxed, set()
    )[0] == "PASS"


# --------------------------------------------------------------------------
# Sweep aggregation
# --------------------------------------------------------------------------
def test_sweep_records_derive_clamp_mode_and_category():
    sweeps = [make_sweep(sweep_number=1, name="Long Square", units="Amps", amplitude=250.0),
              make_sweep(sweep_number=2, name="Ramp", units="Amps", amplitude=10.0),
              make_sweep(sweep_number=3, name="Test", units="Volts", amplitude=500.0),
              make_sweep(sweep_number=4, name="Noise 1", units="Amps", amplitude=50.0)]
    rows = inv.build_sweep_records({485909730: {"region_acronym": "VISp",
                                                "cortical_layer": "5"}}, sweeps)
    assert [r["stimulus_category"] for r in rows] == ["long_square", "ramp", "other", "noise"]
    assert [r["clamp_mode"] for r in rows] == \
        ["current_clamp", "current_clamp", "voltage_clamp", "current_clamp"]


def test_unmapped_stimulus_names_are_kept_verbatim_as_other():
    rows = inv.build_sweep_records({}, [make_sweep(name="Some Brand New Protocol")])
    assert rows[0]["stimulus_name"] == "Some Brand New Protocol"
    assert rows[0]["stimulus_category"] == "other"


def test_cell_record_counts_current_clamp_long_squares_only():
    specimen = {"id": 7, "structure_id": 778, "name": "cell", "donor": {"organism_id": 2},
                "ephys_result_id": 1, "ephys_result": {"failed": False, "sampling_rate": 25000,
                                                       "well_known_files": []},
                "specimen_tags": [], "neuronal_models": [], "structure": {"acronym": "VISp5"}}
    structure_index = {778: {"region_acronym": "VISp", "region_name": "Primary visual area",
                             "region_role": "sensory", "cortical_layer": "5",
                             "structure_acronym": "VISp5",
                             "structure_name": "Primary visual area, layer 5"}}
    sweeps = {7: [
        make_sweep(7, 40, "Long Square", "Amps", 100.0),
        make_sweep(7, 41, "Long Square", "Amps", -100.0),
        make_sweep(7, 42, "Long Square", "Volts", 1.0),      # voltage clamp: excluded
        make_sweep(7, 43, "Short Square", "Amps", 2000.0),
        make_sweep(7, 0, "Test", "Volts", 1.0),
    ]}
    cells = inv.build_cell_records([specimen], structure_index, TEMPLATES, sweeps,
                                   {}, {}, {}, {}, set(), THRESHOLDS)
    cell = cells[0]
    assert cell["n_long_square"] == 3
    assert cell["n_long_square_cc"] == 2
    assert cell["n_long_square_depolarizing_cc"] == 1
    assert cell["n_long_square_hyperpolarizing_cc"] == 1
    assert cell["n_short_square_cc"] == 1
    assert cell["n_sweeps_current_clamp"] == 3
    assert cell["long_square_sweep_numbers"] == "40;41"
    assert cell["species"] == "Mus musculus"


def test_absent_tags_leave_empty_strings():
    specimen = {"id": 8, "structure_id": 778, "name": "cell", "donor": {},
                "specimen_tags": [], "neuronal_models": []}
    structure_index = {778: {"region_acronym": "VISp", "region_name": "",
                             "region_role": "sensory", "cortical_layer": "5",
                             "structure_acronym": "VISp5", "structure_name": ""}}
    cell = inv.build_cell_records([specimen], structure_index, TEMPLATES, {}, {}, {},
                                  {}, {}, set(), THRESHOLDS)[0]
    assert cell["dendrite_type"] == ""
    assert cell["apical_dendrite_status"] == ""
    assert cell["species"] == ""
    assert cell["transgenic_driver_line"] == ""


# --------------------------------------------------------------------------
# CSV writing: idempotency, missing values, no duplicates
# --------------------------------------------------------------------------
def test_write_csv_is_idempotent_and_deduplicates(tmp_path):
    path = tmp_path / "out.csv"
    rows = [{"specimen_id": 2, "x": "b"}, {"specimen_id": 1, "x": "a"},
            {"specimen_id": 1, "x": "a"}]
    columns = ["specimen_id", "x"]

    first = inv.write_csv(path, rows, columns, ["specimen_id"])
    content_1 = path.read_text(encoding="utf-8")
    second = inv.write_csv(path, rows, columns, ["specimen_id"])
    content_2 = path.read_text(encoding="utf-8")

    assert first == second == 2
    assert content_1 == content_2, "re-running must not duplicate or reorder records"
    with path.open(encoding="utf-8", newline="") as fh:
        body = list(csv.DictReader(fh))
    assert [r["specimen_id"] for r in body] == ["1", "2"]


def test_write_csv_preserves_missing_values_as_empty_cells(tmp_path):
    path = tmp_path / "out.csv"
    inv.write_csv(path, [{"a": 1, "b": None, "c": ""}, {"a": 2, "b": "x", "c": None}],
                  ["a", "b", "c"], ["a"])
    text = path.read_text(encoding="utf-8")
    assert "nan" not in text.lower()
    assert "None" not in text
    with path.open(encoding="utf-8", newline="") as fh:
        body = list(csv.DictReader(fh))
    assert body[0]["b"] == ""
    assert body[1]["c"] == ""


def test_write_csv_creates_missing_directories(tmp_path):
    path = tmp_path / "nested" / "deeper" / "out.csv"
    assert inv.write_csv(path, [{"a": 1}], ["a"], ["a"]) == 1
    assert path.exists()


def test_write_csv_renders_ids_as_integers_not_floats(tmp_path):
    """A sparse id column must not become ``486509232.0``.

    pandas widens a column to float64 as soon as one row is missing; without the
    cast, every identifier in that column is corrupted and joins break.
    """
    path = tmp_path / "ids.csv"
    inv.write_csv(path, [{"specimen_id": 485909730, "model_id": 486509232},
                         {"specimen_id": 1, "model_id": None}],
                  ["specimen_id", "model_id"], ["specimen_id"])
    with path.open(encoding="utf-8", newline="") as fh:
        body = {row["specimen_id"]: row for row in csv.DictReader(fh)}
    assert body["485909730"]["model_id"] == "486509232"
    assert body["1"]["model_id"] == ""
    assert ".0" not in path.read_text(encoding="utf-8")


def test_write_csv_keeps_genuine_floats_as_floats(tmp_path):
    """Only integral columns are cast; a real median like 16.5 must survive."""
    path = tmp_path / "floats.csv"
    inv.write_csv(path, [{"k": 1, "median": 16.5}, {"k": 2, "median": 22.0}],
                  ["k", "median"], ["k"])
    with path.open(encoding="utf-8", newline="") as fh:
        body = list(csv.DictReader(fh))
    assert body[0]["median"] == "16.5"
    assert float(body[1]["median"]) == 22.0


# --------------------------------------------------------------------------
# Region summary consistency
# --------------------------------------------------------------------------
def test_region_summary_counts_match_specimen_inventory():
    cells = [
        make_cell(specimen_id=1, region_acronym="VISp", cortical_layer="5"),
        make_cell(specimen_id=2, region_acronym="VISp", cortical_layer="5"),
        make_cell(specimen_id=3, region_acronym="MOp", cortical_layer="2/3",
                  eligibility=None),
    ]
    for cell in cells:
        cell.pop("eligibility", None)
    cells[0]["eligibility"] = "PASS"
    cells[1]["eligibility"] = "FAIL"
    cells[2]["eligibility"] = "CONDITIONAL"
    for index, cell in enumerate(cells, start=1):
        cell["organism_id"] = inv.ORGANISM_MOUSE
        cell["structure_id"] = 778 + index
        cell["structure_acronym"] = f"R{index}"
        cell["has_morphology"] = index == 1
    regions = {"VISp": {"status": "present", "role": "sensory", "member": "Member 1",
                        "structure_id": 385, "name": "Primary visual area", "layers": [],
                        "note": ""},
               "ALM": {"status": "absent_from_ontology", "role": "motor",
                       "member": "Member 2", "structure_id": None, "name": None,
                       "layers": [], "note": "confirmed absent"}}
    rows = inv.build_region_summary(cells, regions)

    visp = next(r for r in rows if r["region_acronym"] == "VISp" and r["cortical_layer"] == "5")
    assert visp["n_specimens"] == 2 == visp["n_mouse"]
    assert visp["n_pass"] == 1 and visp["n_fail"] == 1
    assert visp["n_with_morphology"] == 1

    total = sum(r["n_specimens"] for r in rows if r["cortical_layer"])
    assert total == len(cells), "region counts must match the specimen inventory"

    absent = next(r for r in rows if r["region_acronym"] == "ALM")
    assert absent["status"] == "absent_from_ontology"
    assert absent["n_specimens"] == 0
    assert absent["note"] == "confirmed absent"


def test_region_present_but_with_zero_specimens_carries_an_explanatory_note():
    """MOp exists in the ontology yet has no cells; that must be stated explicitly.

    Without a note, an empty region row is indistinguishable from a region the
    audit forgot to check.
    """
    regions = {"MOp": {"status": "present", "role": "motor", "member": "Member 2",
                       "structure_id": 985, "name": "Primary motor area",
                       "layers": [{"id": 648, "acronym": "MOp5", "layer": "5",
                                   "name": "Primary motor area, layer 5"}],
                       "note": ""}}
    rows = inv.build_region_summary([], regions)
    assert len(rows) == 1
    row = rows[0]
    assert row["region_acronym"] == "MOp"
    assert row["status"] == "present"
    assert row["n_specimens"] == 0
    assert "985" in row["note"] and "MOp5" in row["note"]
    assert "zero cell specimens" in row["note"]


def test_zero_specimen_note_only_applies_to_present_regions():
    assert inv._zero_specimen_note({"status": "absent_from_ontology"}) == ""
    assert inv._zero_specimen_note({"status": "unknown"}) == ""
    assert inv._zero_specimen_note({"status": "present", "structure_id": 1,
                                    "name": "X", "layers": []})


# --------------------------------------------------------------------------
# Model-template class derivation
# --------------------------------------------------------------------------
def test_template_ids_for_class_derives_ids_from_official_names():
    templates = {
        329230710: {"name": "Biophysical - perisomatic",
                    "description": "perisomatic biophysical model"},
        491455321: {"name": "Biophysical - all active",
                    "description": "all-active biophysical model"},
        395310469: {"name": "GLIF1 - single fixed threshold and reset",
                    "description": "Generalized Leaky Integrate-and-Fire"},
        999: {"name": "Something else", "description": "unrelated"},
    }
    assert inv.template_ids_for_class(templates, "biophysical") == [329230710, 491455321]
    assert inv.template_ids_for_class(
        templates, "generalized leaky integrate-and-fire") == [395310469]
    assert inv.template_ids_for_class(templates, "nonexistent") == []


# --------------------------------------------------------------------------
# Chunking helpers
# --------------------------------------------------------------------------
def test_chunked_covers_every_value_exactly_once():
    values = list(range(250))
    chunks = list(inv.chunked(values, 100))
    assert [len(c) for c in chunks] == [100, 100, 50]
    flat = [v for chunk in chunks for v in chunk]
    assert flat == values


def test_join_in_produces_valid_criteria_list():
    assert inv.join_in([1, 2, 3]) == "1,2,3"


def test_merge_model_sources_deduplicates_on_model_id():
    embedded = [make_model(10, 1, 329230710)]
    direct = [make_model(10, 1, 329230710), make_model(20, 1, 395310469)]
    merged = inv.merge_model_sources(embedded, direct)
    assert sorted(m["id"] for m in merged) == [10, 20]

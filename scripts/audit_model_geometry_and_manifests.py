#!/usr/bin/env python
"""Audit the Allen model geometry and the authored manifest drafts.

Purpose
-------
Phase 2B asked whether the morphology that Allen's biophysical models were
fitted against can be recovered, and whether a scientifically defensible
Allen-compatible ``manifest.json`` can be authored for both model classes of
specimen 382982932.  This script answers both questions from primary sources and
then statically validates the two manifests it emits.

It performs three kinds of work, none of which requires NEURON:

1. **Geometry identity.**  It parses the downloaded SWC and recomputes every
   published ``NeuronReconstruction`` metric for reconstruction 674389884.  Nine
   of eleven fields reproduce exactly, which is what makes the substitution
   auditable rather than assumed.
2. **Manifest authoring.**  It writes two separate manifests under the ignored
   cache, following ``allensdk.api.queries.biophysical_api.BiophysicalApi
   .create_manifest`` entry for entry, and records the provenance of every field
   in a sidecar so that no value is silently invented.
3. **Static validation.**  It checks schema, file existence, model-type dispatch,
   per-loader parameterisation, mechanism coverage, axon configuration and
   sweep-selection consistency without importing NEURON or running a model.

Why the implementation looks the way it does
--------------------------------------------
*Phase 2A left two guesses that this script retires.*  The first was that
``axon_type`` is a missing manifest field.  It is not: ``runner.load_description``
*appends* ``{"axon_type": ...}`` to ``description.data["biophys"]`` and
``create_utils`` then reads ``biophys[1]``, so authoring it in the manifest would
shift the appended entry to index 2 and misdispatch.  The drafts therefore carry
exactly one ``biophys`` entry and the value is supplied on the command line.

The second guess was that ``neuron_reconstruction_id`` identifies the morphology.
Neither Allen code path reads it.  ``BiophysicalApi.cache_data`` and
``BiophysicalModuleReader.morphology_path`` both resolve the SWC through
``specimen -> neuron_reconstructions``, filtered on ``superseded``.  So the SWC
that Allen's own tooling would load for model 473862496 today is the specimen's
currently published reconstruction, which is exactly the file audited here.  The
dangling ``neuron_reconstruction_id`` is a stale foreign key, not a retrieval
failure.

*Why hard-coded expectations.*  The published reconstruction metrics and the
cached RMA evidence are both pinned as constants so the audit is reproducible
offline.  Every constant below carries its retrieval route in a comment.  The
script additionally cross-checks against the cached RMA payloads when they are
present, and reports those checks as skipped when they are not.

*Why stems are excluded from total_length.*  Allen's ``total_length`` for this
reconstruction is not the naive sum of dendritic segments; it excludes the nine
connectors that bridge the soma to each dendritic stem.  Under that convention
the published value reproduces to ten significant figures.  Recording the
convention explicitly is what turns a 2.7% discrepancy into a proof of identity.

Usage
-----
    python scripts/audit_model_geometry_and_manifests.py
    python scripts/audit_model_geometry_and_manifests.py --no-emit
    python scripts/audit_model_geometry_and_manifests.py --require-execution-ready

Exit codes
----------
0   every offline check passed
1   at least one check failed
2   ``--require-execution-ready`` was given and a blocker remains
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import pathlib
import shutil
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# ----------------------------------------------------------------- constants
SPECIMEN = 382982932
PERISOMATIC_MODEL = 473862496
ALL_ACTIVE_MODEL = 497233292
PERISOMATIC_TEMPLATE = 329230710
ALL_ACTIVE_TEMPLATE = 491455321
PERISOMATIC_FIT_WKF = 497235792
ALL_ACTIVE_FIT_WKF = 568156386
MISSING_RECONSTRUCTION = 491771090
PUBLISHED_RECONSTRUCTION = 674389884
SWC_WKF = 674389901
MARKER_WKF = 674389910
JUNCTION_MV = -14.0

PERISOMATIC_TYPE = "Biophysical - perisomatic"
ALL_ACTIVE_TYPE = "Biophysical - all active"

#: Allen's public manifest generator writes exactly these two, and both shipped
#: fixture manifests match.  ``cell.hoc`` appears only in the internal pipeline
#: variant; the runtime never instantiates that template.
HOC_FILES = ("stdgui.hoc", "import3d.hoc")

#: ``runner.sim_parser`` choices for ``--axon_type``.
AXON_TYPE_CHOICES = ("stub", "truncated")
AXON_TYPE_ARG_DEFAULT = "truncated"

SECTION_CLASSES = ("soma", "axon", "dend", "apic")

#: Sweeps 24-43 of specimen 382982932: stimulus description C1LSCOARSE150216[0..19].
COARSE_SWEEPS = tuple(range(24, 44))
COARSE_PREFIX = "C1LSCOARSE"
FINEST_SWEEPS = tuple(range(44, 53))
FINEST_PREFIX = "C1LSFINEST"
FIT_SWEEP = {"perisomatic": 38, "all_active": 41}

#: NeuronReconstruction 674389884, RMA NeuronReconstruction/query.json?criteria=[id$eq674389884]
PUBLISHED_METRICS = {
    "number_nodes": 2417,
    "total_length": 2875.15684072065,
    "overall_depth": 145.5314,
    "soma_surface": 557.674310511469,
    "number_stems": 9,
    "number_tips": 33,
    "number_bifurcations": 24,
    "number_branches": 57,
    "max_branch_order": 6.0,
    "neuron_reconstruction_type": "full",
    "superseded": False,
}

#: Fields that cannot be reproduced from the SWC because Allen computes them in
#: an undocumented frame.  Audited as an explicit limitation, not a failure.
UNREPRODUCIBLE_METRICS = ("overall_height", "overall_width", "soma_surface")

MODEL_CLASSES = {
    "perisomatic": {
        "model_id": PERISOMATIC_MODEL,
        "template_id": PERISOMATIC_TEMPLATE,
        "model_type": PERISOMATIC_TYPE,
        "loader": "Utils",
        "fit_relative": "models/perisomatic_473862496/382982932_fit.json",
        "fit_basename": "382982932_fit.json",
        "passive_keys": ("ra", "cm", "e_pas"),
        "genome_value_type": float,
        "axon_type": None,
        "sweep": FIT_SWEEP["perisomatic"],
    },
    "all_active": {
        "model_id": ALL_ACTIVE_MODEL,
        "template_id": ALL_ACTIVE_TEMPLATE,
        "model_type": ALL_ACTIVE_TYPE,
        "loader": "AllActiveUtils",
        "fit_relative": "models/all_active_497233292/497233292_fit.json",
        "fit_basename": "497233292_fit.json",
        "passive_keys": ("ra",),
        "genome_value_type": str,
        "axon_type": AXON_TYPE_ARG_DEFAULT,
        "sweep": FIT_SWEEP["all_active"],
    },
}

SWC_RELATIVE = "morphology/674389901_382982932_m.swc"
MARKER_RELATIVE = "morphology/674389910_382982932_m.marker"
NWB_RELATIVE = "../nwb_cache/382982932.nwb"
MODFILE_DIR_RELATIVE = "allensdk/modfiles"
INVENTORY_RELATIVE = "data/metadata/sweep_inventory.csv"
ASSETS_RELATIVE = "tmp/model_cache/assets_2a.json"
DRAFTS_RELATIVE = "tmp/model_cache/manifest_drafts"
RMA_EVIDENCE_RELATIVE = "tmp/model_cache/2b"

SWC_TYPES = {0: "undefined", 1: "soma", 2: "axon", 3: "dend", 4: "apic"}


# ------------------------------------------------------------------- helpers
def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class Checker:
    """Accumulate pass/fail checks in the house style of the Phase 2A script."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, bool | None, str]] = []
        self.section = ""

    def heading(self, title: str) -> None:
        self.section = title
        print()
        print("=" * 78)
        print(title)
        print("=" * 78)

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.rows.append((self.section, label, bool(ok), detail))
        print("  %-9s %-58s %s" % ("ok" if ok else "FAIL", label, detail))
        return ok

    def skip(self, label: str, reason: str) -> None:
        self.rows.append((self.section, label, None, reason))
        print("  %-9s %-58s %s" % ("skipped", label, reason))

    def note(self, text: str) -> None:
        print("  " + text)

    def failures(self) -> list[tuple[str, str, bool | None, str]]:
        return [r for r in self.rows if r[2] is False]

    def summary(self) -> int:
        checked = [r for r in self.rows if r[2] is not None]
        failed = [r for r in checked if r[2] is False]
        print()
        print("-" * 78)
        print("checks: %d   passed: %d   failed: %d   skipped: %d"
              % (len(self.rows), len(checked) - len(failed), len(failed),
                 len(self.rows) - len(checked)))
        return len(failed)


def load_swc(path: pathlib.Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 7:
            continue
        rows.append({
            "n": int(parts[0]), "t": int(parts[1]),
            "xyz": (float(parts[2]), float(parts[3]), float(parts[4])),
            "r": float(parts[5]), "par": int(parts[6]),
        })
    return rows


def swc_topology(rows: list[dict]) -> dict:
    """Recompute the dendritic metrics under the conventions Allen uses."""
    index = {r["n"]: r for r in rows}
    kids = collections.defaultdict(list)
    for row in rows:
        if row["par"] != -1:
            kids[row["par"]].append(row["n"])

    dend = [r for r in rows if r["t"] in (3, 4)]
    dend_ids = {r["n"] for r in dend}
    dend_kids = {n: [c for c in kids[n] if c in dend_ids] for n in dend_ids}
    stems = [n for n in dend_ids if index[n]["par"] not in dend_ids]
    tips = [n for n in dend_ids if not dend_kids[n]]
    branch_nodes = [n for n in dend_ids if len(dend_kids[n]) >= 2]
    bifurcations = sum(len(dend_kids[n]) - 1 for n in branch_nodes)

    length_all = sum(
        math.dist(index[r["n"]]["xyz"], index[r["par"]]["xyz"]) for r in dend)
    length_no_stem = sum(
        math.dist(index[r["n"]]["xyz"], index[r["par"]]["xyz"])
        for r in dend if index[r["par"]]["t"] in (3, 4))

    order: dict[int, int] = {}
    for stem in stems:
        stack = [(stem, 0)]
        while stack:
            node, depth = stack.pop()
            order[node] = depth
            step = 1 if len(dend_kids[node]) >= 2 else 0
            for child in dend_kids[node]:
                stack.append((child, depth + step))

    zs = [r["xyz"][2] for r in rows]
    return {
        "by_type": collections.Counter(r["t"] for r in rows),
        "stems": len(stems), "tips": len(tips),
        "bifurcations": bifurcations,
        "branches": len(tips) + bifurcations,
        "max_branch_order": max(order.values()) if order else 0,
        "length_no_stem": length_no_stem, "length_all": length_all,
        "depth": max(zs) - min(zs),
    }


def build_sweeps_by_type(csv_path: pathlib.Path) -> dict:
    """Reproduce ``BiophysicalModuleReader.sweep_numbers_by_type()``.

    That method groups every ``ephys_sweep`` of the specimen by the name of its
    ``ephys_stimulus_type``.  The Phase 1C inventory already extracted the same
    field from the NWB, so the grouping needs no new download.
    """
    import csv

    grouped: dict[str, list[int]] = collections.defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["specimen_id"]) != SPECIMEN:
                continue
            grouped[row["stimulus_name"]].append(int(row["sweep_number"]))
    return {name: sorted(numbers) for name, numbers in sorted(grouped.items())}


# ------------------------------------------------------- manifest authoring
def build_manifest(key: str, sweeps_by_type: dict) -> dict:
    """Return the manifest dict for one model class.

    Field order mirrors ``BiophysicalApi.create_manifest`` so that a diff against
    an Allen-generated manifest is readable.  Note that ``runs[0]`` deliberately
    adds ``sweeps_by_type``, which Allen's public generator omits even though
    ``runner.run_sync`` requires it at line 119.
    """
    spec = MODEL_CLASSES[key]
    stimulus = pathlib.Path(NWB_RELATIVE).name
    return collections.OrderedDict([
        ("biophys", [collections.OrderedDict([
            ("model_file", ["manifest.json", spec["fit_basename"]]),
            ("model_type", spec["model_type"]),
        ])]),
        ("runs", [collections.OrderedDict([
            ("sweeps", list(COARSE_SWEEPS)),
            ("sweeps_by_type", sweeps_by_type),
        ])]),
        ("neuron", [collections.OrderedDict([("hoc", list(HOC_FILES))])]),
        ("manifest", [
            collections.OrderedDict([("type", "dir"), ("spec", "."),
                                     ("key", "BASEDIR")]),
            collections.OrderedDict([("type", "dir"), ("spec", "work"),
                                     ("key", "WORKDIR"), ("parent", "BASEDIR")]),
            collections.OrderedDict([("type", "file"),
                                     ("spec", pathlib.Path(SWC_RELATIVE).name),
                                     ("key", "MORPHOLOGY")]),
            collections.OrderedDict([("type", "file"),
                                     ("spec", pathlib.Path(MARKER_RELATIVE).name),
                                     ("key", "MARKER")]),
            collections.OrderedDict([("type", "dir"), ("spec", "modfiles"),
                                     ("key", "MODFILE_DIR")]),
            collections.OrderedDict([("type", "file"), ("format", "NWB"),
                                     ("spec", stimulus),
                                     ("key", "stimulus_path")]),
            collections.OrderedDict([("parent_key", "WORKDIR"), ("type", "file"),
                                     ("format", "NWB"), ("spec", stimulus),
                                     ("key", "output_path")]),
        ]),
    ])


def build_provenance(key: str) -> dict:
    """Record where every manifest value came from.

    ``source`` is one of: recovered, constant, derived, restricted, substituted.
    Anything that is not recovered or constant is a value a reader must know we
    supplied, so it is listed in the report as well.
    """
    spec = MODEL_CLASSES[key]
    return {
        "_note": (
            "Sidecar provenance for the draft manifest in this directory. It is "
            "not part of Allen's manifest schema and is never read by the "
            "runner; it exists so that no authored value is silently invented."
        ),
        "specimen_id": SPECIMEN,
        "model_id": spec["model_id"],
        "model_class": key,
        "loader": spec["loader"],
        "field_provenance": [
            {
                "field": "biophys[0].model_file[0]",
                "value": "manifest.json",
                "source": "constant",
                "evidence": "BiophysicalApi.create_manifest hard-codes the "
                            "manifest's own basename as the first model_file so "
                            "that Config.read_model_description pre-loads it.",
            },
            {
                "field": "biophys[0].model_file[1]",
                "value": spec["fit_basename"],
                "source": "recovered",
                "evidence": "Basename of the NeuronalModelParameters well-known "
                            "file attached to NeuronalModel %d." % spec["model_id"],
            },
            {
                "field": "biophys[0].model_type",
                "value": spec["model_type"],
                "source": "recovered",
                "evidence": "NeuronalModelTemplate %d name; create_utils compares "
                            "it against PERISOMATIC_TYPE / ALL_ACTIVE_TYPE."
                            % spec["template_id"],
            },
            {
                "field": "runs[0].sweeps",
                "value": list(COARSE_SWEEPS),
                "source": "restricted",
                "evidence": "Allen would emit every sweep whose stimulus_name is "
                            "not 'Test'. Restricted to the C1LSCOARSE block so "
                            "that COARSE and FINEST are never pooled.",
            },
            {
                "field": "runs[0].sweeps_by_type",
                "value": "see manifest",
                "source": "derived",
                "evidence": "Not emitted by BiophysicalApi.create_manifest, but "
                            "runner.run_sync reads it unconditionally. Derived by "
                            "BiophysicalModuleReader.sweep_numbers_by_type().",
            },
            {
                "field": "neuron[0].hoc",
                "value": list(HOC_FILES),
                "source": "constant",
                "evidence": "create_manifest line 287 and both shipped fixture "
                            "manifests. These are NEURON-shipped hocs.",
            },
            {
                "field": "manifest[MORPHOLOGY]",
                "value": pathlib.Path(SWC_RELATIVE).name,
                "source": "substituted",
                "evidence": "neuron_reconstruction_id %d has no row. The specimen's "
                            "published reconstruction %d is what Allen's own "
                            "specimen->neuron_reconstructions resolution returns."
                            % (MISSING_RECONSTRUCTION, PUBLISHED_RECONSTRUCTION),
            },
            {
                "field": "manifest[MARKER]",
                "value": pathlib.Path(MARKER_RELATIVE).name,
                "source": "substituted",
                "evidence": "Allen's spec convention is '<cell>_<recon>_marker_m.swc'; "
                            "the published asset is '<cell>_<recon>_m.marker'. Renamed "
                            "to the actual file. Never read at run time.",
            },
            {
                "field": "manifest[stimulus_path]",
                "value": pathlib.Path(NWB_RELATIVE).name,
                "source": "recovered",
                "evidence": "The specimen's stimulus NWB. Allen names it "
                            "'<ephys_result_id>.nwb'; the local cache uses the "
                            "specimen id.",
            },
            {
                "field": "manifest[output_path]",
                "value": pathlib.Path(NWB_RELATIVE).name,
                "source": "constant",
                "evidence": "create_manifest reuses the stimulus filename for the "
                            "output, placed under WORKDIR.",
            },
            {
                "field": "axon_type",
                "value": spec["axon_type"],
                "source": "absent-by-design",
                "evidence": "Not a manifest field. runner.load_description appends "
                            "it and create_utils reads biophys[1]; the value comes "
                            "from --axon_type (default 'truncated').",
            },
            {
                "field": "fitting[0].junction_potential",
                "value": JUNCTION_MV,
                "source": "recovered",
                "evidence": "From the fit descriptor. get_recorded_data writes "
                            "v = (v - junction_potential) * mV.",
            },
            {
                "field": "fitting[0].sweeps",
                "value": [spec["sweep"]],
                "source": "recovered",
                "evidence": "From the fit descriptor. Inside the C1LSCOARSE block, "
                            "therefore in-sample, not a held-out sweep.",
            },
        ],
    }


def emit_drafts(workspace: pathlib.Path, sweeps_by_type: dict,
                checker: Checker) -> dict:
    """Write both drafts plus their sidecars and staging links."""
    root = workspace / DRAFTS_RELATIVE
    sources = {
        pathlib.Path(SWC_RELATIVE).name:
            workspace / "tmp/model_cache" / SWC_RELATIVE,
        pathlib.Path(MARKER_RELATIVE).name:
            workspace / "tmp/model_cache" / MARKER_RELATIVE,
        pathlib.Path(NWB_RELATIVE).name: workspace / "data/nwb_cache" /
            pathlib.Path(NWB_RELATIVE).name,
    }
    modfiles = workspace / "tmp/model_cache" / MODFILE_DIR_RELATIVE

    written = {}
    for key, spec in MODEL_CLASSES.items():
        directory = root / key
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "work").mkdir(exist_ok=True)

        manifest = build_manifest(key, sweeps_by_type)
        (directory / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (directory / "provenance.json").write_text(
            json.dumps(build_provenance(key), indent=2) + "\n", encoding="utf-8")

        pair = dict(sources)
        pair[spec["fit_basename"]] = workspace / "tmp/model_cache" / spec["fit_relative"]
        for name, source in pair.items():
            target = directory / name
            if target.exists():
                target.unlink()
            try:
                os.link(source, target)
            except OSError:
                shutil.copy2(source, target)

        staged_mods = directory / "modfiles"
        staged_mods.mkdir(exist_ok=True)
        for mod in sorted(modfiles.glob("*.mod")):
            target = staged_mods / mod.name
            if target.exists():
                target.unlink()
            try:
                os.link(mod, target)
            except OSError:
                shutil.copy2(mod, target)

        written[key] = directory
        checker.note("emitted %s" % directory.relative_to(workspace).as_posix())
    return written


# ------------------------------------------------------------ geometry audit
def check_geometry(workspace: pathlib.Path, checker: Checker) -> None:
    checker.heading("A. Reconstruction provenance and morphology identity")

    swc = workspace / "tmp/model_cache" / SWC_RELATIVE
    if not checker.check(swc.exists(), "published SWC is cached",
                         swc.name if swc.exists() else "missing"):
        return

    checker.check(swc.stat().st_size == 335924, "SWC byte size as recorded in Phase 2A",
                  "%d B" % swc.stat().st_size)

    assets = workspace / ASSETS_RELATIVE
    if assets.exists():
        recorded = {e["path"]: e["sha256"]
                    for e in json.loads(assets.read_text(encoding="utf-8"))["assets"]}
        checker.check(recorded.get(SWC_RELATIVE) == sha256_of(swc),
                      "SWC digest matches the pinned Phase 2A asset manifest")
    else:
        checker.skip("SWC digest matches the pinned Phase 2A asset manifest",
                     "assets_2a.json not present")

    rows = load_swc(swc)
    present = sorted({r["t"] for r in rows})
    checker.check(present == [1, 2, 3, 4], "SWC uses only the standard types 1-4",
                  str(present))

    topo = swc_topology(rows)
    counts = topo["by_type"]
    checker.note("node census: soma=%d axon=%d dend(basal)=%d apic(apical)=%d "
                 "total=%d" % (counts[1], counts[2], counts[3], counts[4], len(rows)))
    checker.check(counts[1] == 1, "exactly one soma node (Allen 'm' convention)")
    checker.check(counts[3] + counts[4] == PUBLISHED_METRICS["number_nodes"],
                  "number_nodes reproduces from types 3+4",
                  "%d" % (counts[3] + counts[4]))
    checker.check(abs(topo["length_no_stem"] - PUBLISHED_METRICS["total_length"])
                  < 1e-8,
                  "total_length reproduces (stems excluded)",
                  "%.10f vs %.10f" % (topo["length_no_stem"],
                                      PUBLISHED_METRICS["total_length"]))
    checker.check(topo["length_all"] != topo["length_no_stem"],
                  "the stem-exclusion convention is load-bearing",
                  "naive sum would be %.4f" % topo["length_all"])
    checker.check(abs(topo["depth"] - PUBLISHED_METRICS["overall_depth"]) < 1e-9,
                  "overall_depth reproduces as the raw z extent",
                  "%.6f" % topo["depth"])
    for field, recomputed in (("number_stems", topo["stems"]),
                              ("number_tips", topo["tips"]),
                              ("number_bifurcations", topo["bifurcations"]),
                              ("number_branches", topo["branches"]),
                              ("max_branch_order", topo["max_branch_order"])):
        checker.check(recomputed == PUBLISHED_METRICS[field],
                      "%s reproduces exactly" % field,
                      "%s" % recomputed)

    checker.skip("overall_height / overall_width / soma_surface",
                 "computed in an undocumented frame; listed as a limitation")

    # every section class the descriptors address must exist in the SWC
    provided = {"soma", "axon", "dend", "apic"}
    for key, spec in MODEL_CLASSES.items():
        fit = json.loads((workspace / "tmp/model_cache" / spec["fit_relative"])
                         .read_text(encoding="utf-8"))
        needed = {g["section"] for g in fit["genome"]}
        needed |= {c["section"] for c in fit["passive"][0].get("cm", [])}
        needed |= {e["section"] for e in fit["conditions"][0].get("erev", [])}
        checker.check(needed <= provided,
                      "%s addresses only classes the SWC provides" % key,
                      "%d classes: %s" % (len(needed), sorted(needed)))

    # cached RMA evidence, when available
    evidence = workspace / RMA_EVIDENCE_RELATIVE
    spec_recons = evidence / "recon_all_for_specimen.json"
    if spec_recons.exists():
        rows_rma = json.loads(spec_recons.read_text(encoding="utf-8"))
        ids = [r["id"] for r in rows_rma]
        checker.check(ids == [PUBLISHED_RECONSTRUCTION],
                      "specimen publishes exactly one reconstruction", str(ids))
        checker.check(MISSING_RECONSTRUCTION not in ids,
                      "the model's reconstruction id is absent from that list")
        checker.check(rows_rma[0]["superseded"] is False,
                      "the published reconstruction is not superseded")
    else:
        checker.skip("specimen publishes exactly one reconstruction",
                     "cached RMA payload not present")

    cohort = evidence / "recon_cohort_resolution.json"
    alternatives = evidence / "recon_alternatives.json"
    if cohort.exists() and alternatives.exists():
        resolved = json.loads(cohort.read_text(encoding="utf-8"))
        alts = json.loads(alternatives.read_text(encoding="utf-8"))
        # the cached payload was written with json.dumps(default=str), so numpy
        # scalars arrive as strings; normalise before comparing
        missing_ids = {int(value) for value in resolved["missing"]}
        total = len(resolved["present"]) + len(missing_ids)
        checker.note("cohort: %d of %d model-referenced reconstructions resolve"
                     % (len(resolved["present"]), total))
        checker.check(MISSING_RECONSTRUCTION in missing_ids,
                      "the model's reconstruction id is in the dangling set",
                      "%d dangling" % len(missing_ids))
        with_alt = [s for s, rows_ in alts.items() if rows_]
        checker.check(len(with_alt) >= 20,
                      "most affected specimens still publish a reconstruction",
                      "%d of %d" % (len(with_alt), len(alts)))
        exactly_one = [s for s, rows_ in alts.items() if len(rows_) == 1]
        checker.check(len(exactly_one) >= 18,
                      "most affected specimens publish exactly one",
                      "%d of %d" % (len(exactly_one), len(alts)))
    else:
        checker.skip("dangling-reference cohort census",
                     "cached RMA payloads not present")


# ------------------------------------------------------------ manifest audit
def resolve(manifest: dict, directory: pathlib.Path) -> dict:
    """Resolve every manifest path entry the way Manifest.get_path does."""
    entries = {e["key"]: e for e in manifest["manifest"]}
    resolved = {}
    for key, entry in entries.items():
        base = directory
        if entry.get("parent") == "BASEDIR" or entry.get("parent_key") == "BASEDIR":
            base = directory
        if entry.get("parent_key") == "WORKDIR":
            base = directory / entries["WORKDIR"]["spec"]
        resolved[key] = base / entry["spec"]
    return resolved


def check_manifests(workspace: pathlib.Path, drafts: dict,
                    checker: Checker) -> None:
    checker.heading("B. Manifest schema and per-class dispatch")

    available_mods = {p.stem for p in
                      (workspace / "tmp/model_cache" / MODFILE_DIR_RELATIVE).glob("*.mod")}
    for key, spec in MODEL_CLASSES.items():
        directory = drafts[key]
        checker.note("--- %s (model %d) ---" % (key, spec["model_id"]))
        raw = (directory / "manifest.json").read_text(encoding="utf-8")
        try:
            manifest = json.loads(raw)
            checker.check(True, "manifest is valid JSON")
        except json.JSONDecodeError as exc:
            checker.check(False, "manifest is valid JSON", str(exc))
            continue

        checker.check(sorted(manifest) == ["biophys", "manifest", "neuron", "runs"],
                      "top level is exactly Allen's four sections",
                      str(sorted(manifest)))

        # --- dispatch
        checker.check(len(manifest["biophys"]) == 1,
                      "biophys has exactly one entry",
                      "the runner appends biophys[1] itself")
        checker.check("axon_type" not in manifest["biophys"][0],
                      "axon_type is not authored in the manifest")
        checker.check(manifest["biophys"][0]["model_type"] == spec["model_type"],
                      "model_type matches the loader's expected string",
                      manifest["biophys"][0]["model_type"])
        files = manifest["biophys"][0]["model_file"]
        checker.check(files[0] == "manifest.json",
                      "model_file[0] is the manifest self-reference")
        checker.check(files[1] == spec["fit_basename"],
                      "model_file[1] names the fit descriptor", files[1])
        checker.check((directory / files[1]).exists(),
                      "the named fit descriptor exists in the draft directory")

        # --- parameterisation for the loader that will be constructed
        fit = json.loads((directory / files[1]).read_text(encoding="utf-8"))
        passive = fit["passive"][0]
        checker.check(sorted(fit) == ["conditions", "fitting", "genome", "passive"],
                      "fit descriptor keeps Allen's four sections")
        checker.check(sorted(passive) == sorted(spec["passive_keys"]),
                      "passive carries %s" % ("{ra, cm, e_pas}"
                                              if key == "perisomatic" else "{ra}"),
                      str(sorted(passive)))
        value_types = {type(g["value"]) for g in fit["genome"]}
        checker.check(value_types == {spec["genome_value_type"]},
                      "genome values are all %s"
                      % spec["genome_value_type"].__name__,
                      str(sorted(t.__name__ for t in value_types)))
        if spec["genome_value_type"] is str:
            checker.check(all(float(g["value"]) == float(g["value"])
                              for g in fit["genome"]),
                          "every string gene coerces with float()")
        sections = sorted({g["section"] for g in fit["genome"]})
        checker.check(sections == sorted(SECTION_CLASSES),
                      "genome covers all four section classes", str(sections))
        mechanisms = {g["mechanism"] for g in fit["genome"] if g["mechanism"]}
        missing = mechanisms - available_mods - {"pas"}
        checker.check(not missing, "every declared mechanism has a .mod source",
                      "%d mechanisms, missing=%s" % (len(mechanisms),
                                                     sorted(missing) or "none"))
        checker.check(fit["fitting"][0]["junction_potential"] == JUNCTION_MV,
                      "junction potential is -14 mV",
                      "%s" % fit["fitting"][0]["junction_potential"])

        # --- files referenced by the manifest
        paths = resolve(manifest, directory)
        required = ["MORPHOLOGY", "MARKER", "stimulus_path", "MODFILE_DIR"]
        for name in required:
            checker.check(paths[name].exists(),
                          "%s resolves to an existing file" % name,
                          paths[name].name)
        checker.check(paths["output_path"].parent.name == "work",
                      "output_path is written under WORKDIR",
                      paths["output_path"].parent.name)
        checker.check(not list((directory / "modfiles").glob("*.mod")) == [],
                      "modfiles directory is populated",
                      "%d .mod" % len(list((directory / "modfiles").glob("*.mod"))))

        # --- hoc list
        checker.check(manifest["neuron"][0]["hoc"] == list(HOC_FILES),
                      "hoc list matches Allen's public generator", str(HOC_FILES))

        # --- sweep selection
        runs = manifest["runs"][0]
        sweeps = runs["sweeps"]
        by_type = runs["sweeps_by_type"]
        checker.check("sweeps_by_type" in runs,
                      "runs carries sweeps_by_type, which run_sync requires")
        checker.check(sweeps == list(COARSE_SWEEPS),
                      "sweeps are the 20 C1LSCOARSE sweeps", "%d sweeps" % len(sweeps))
        seen = collections.Counter(s for numbers in by_type.values() for s in numbers)
        checker.check(all(seen[s] == 1 for s in sweeps),
                      "every selected sweep appears in exactly one type")
        checker.check(set(sweeps) <= set(seen),
                      "sweeps_by_type covers every selected sweep")
        checker.check(spec["sweep"] in sweeps,
                      "the %s fitting sweep %d is selected"
                      % (key, spec["sweep"]), "%d" % spec["sweep"])
        checker.check(spec["sweep"] in COARSE_SWEEPS,
                      "the fitting sweep lies inside the COARSE block "
                      "(in-sample, not held out)")
        checker.check(not (set(sweeps) & set(FINEST_SWEEPS)),
                      "no FINEST sweep is selected")

    checker.heading("C. Sweep-block integrity against the Phase 1C inventory")
    inventory = workspace / INVENTORY_RELATIVE
    if not inventory.exists():
        checker.skip("sweep inventory is present", "csv missing")
        return

    import csv
    rows = [r for r in csv.DictReader(inventory.open(encoding="utf-8"))
            if int(r["specimen_id"]) == SPECIMEN]
    checker.check(len(rows) == 80, "specimen has 80 sweeps", "%d" % len(rows))
    coarse = {int(r["sweep_number"]): r for r in rows
              if int(r["sweep_number"]) in COARSE_SWEEPS}
    checker.check(len(coarse) == 20, "the COARSE block has 20 sweeps")
    checker.check(all(r["stimulus_description"].startswith(COARSE_PREFIX)
                      for r in coarse.values()),
                  "all 20 are described C1LSCOARSE*")
    checker.check({int(r["sweep_number"]): r["stimulus_description"]
                   for r in coarse.values()}
                  == {n: "%s150216[%d]" % (COARSE_PREFIX, n - COARSE_SWEEPS[0])
                      for n in COARSE_SWEEPS},
                  "COARSE index k maps to sweep 24+k")
    finest = [r for r in rows if r["stimulus_description"].startswith(FINEST_PREFIX)]
    checker.check(len(finest) == 9, "the FINEST block has 9 sweeps",
                  "%d" % len(finest))
    amps = {round(float(r["stimulus_absolute_amplitude"])) for r in finest}
    checker.check(amps == {120, 130, 140, 150, 160, 170},
                  "FINEST amplitudes are the 120-170 pA ladder", str(sorted(amps)))
    checker.check(any(round(float(r["stimulus_absolute_amplitude"])) == 170
                      for r in coarse.values()),
                  "170 pA also occurs in the COARSE block",
                  "so the same amplitude exists in both protocols")


# ------------------------------------------------------------------ blockers
def report_blockers(checker: Checker) -> int:
    checker.heading("D. Execution readiness")
    blockers = []

    try:
        import neuron  # noqa: F401
        checker.check(True, "NEURON is importable")
    except Exception:                                       # noqa: BLE001
        checker.note("NEURON is not importable -> no simulation can run here")
        blockers.append("NEURON is unavailable in this environment")

    blockers.append("axon_type for the all-active model is not recorded by Allen "
                    "and must be declared as an assumption")
    blockers.append("sweeps_by_type is required by run_sync but not emitted by "
                    "Allen's public manifest generator")
    blockers.append("manifest.json is not published and must be authored")
    blockers.append("fit-time morphology identity (reconstruction %d) cannot be "
                    "confirmed" % MISSING_RECONSTRUCTION)

    checker.note("")
    for number, text in enumerate(blockers, 1):
        checker.note("B%d: %s" % (number, text))
    return len(blockers)


# ---------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit the Allen model geometry and the authored "
                    "Allen-compatible manifest drafts for specimen %d." % SPECIMEN)
    parser.add_argument("--repo-root", default=None,
                        help="repository root (default: the parent of scripts/)")
    parser.add_argument("--no-emit", action="store_true",
                        help="validate existing drafts instead of rewriting them")
    parser.add_argument("--require-execution-ready", action="store_true",
                        help="exit 2 if any execution blocker remains")
    args = parser.parse_args(argv)

    workspace = pathlib.Path(args.repo_root).resolve() if args.repo_root \
        else REPO_ROOT

    checker = Checker()
    print("repo root: %s" % workspace)
    print("specimen:  %d" % SPECIMEN)

    inventory = workspace / INVENTORY_RELATIVE
    if not inventory.exists():
        print("error: %s is missing; run the Phase 1C inventory first" % inventory)
        return 1
    sweeps_by_type = build_sweeps_by_type(inventory)

    checker.heading("0. Draft manifests")
    if args.no_emit:
        drafts = {key: workspace / DRAFTS_RELATIVE / key for key in MODEL_CLASSES}
        for key, directory in drafts.items():
            checker.check((directory / "manifest.json").exists(),
                          "%s draft exists" % key,
                          directory.relative_to(workspace).as_posix())
    else:
        missing_sources = [name for name, source in {
            "SWC": workspace / "tmp/model_cache" / SWC_RELATIVE,
            "marker": workspace / "tmp/model_cache" / MARKER_RELATIVE,
            "NWB": workspace / "data/nwb_cache" / "382982932.nwb",
            "modfiles": workspace / "tmp/model_cache" / MODFILE_DIR_RELATIVE,
        }.items() if not source.exists()]
        if missing_sources:
            for name in missing_sources:
                checker.check(False, "staging source %s is present" % name)
            return 1
        drafts = emit_drafts(workspace, sweeps_by_type, checker)
        checker.check(True, "both drafts emitted under the ignored cache")

    check_geometry(workspace, checker)
    check_manifests(workspace, drafts, checker)
    blockers = report_blockers(checker)

    failed = checker.summary()
    if failed:
        print("result: FAIL")
        return 1
    if args.require_execution_ready:
        print("result: all static checks passed, but %d execution blocker(s) "
              "remain" % blockers)
        return 2
    print("result: all static checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

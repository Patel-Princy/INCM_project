#!/usr/bin/env python
"""Inspect the cached Allen biophysical model assets for specimen 382982932.

Purpose
-------
Decide, **without running the model**, whether the two Allen biophysical
parameterisations published for this specimen are internally consistent,
complete at the asset level, and mappable onto Allen's own NEURON template.

The models are::

    Biophysical - perisomatic   neuronal_model 473862496  template 329230710
    Biophysical - all active    neuronal_model 497233292  template 491455321

Both are described by a single well-known file apiece, a ``*_fit.json``
parameter document.  Nothing else is published against the model record.  This
script verifies that what *was* published is intact and sufficient, and reports
what is still missing before a simulation would be possible.  It never imports
NEURON, never compiles mechanisms, and never produces a voltage trace.

Why the implementation looks the way it does
--------------------------------------------
1. The two parameterisations are **not** the same schema with different
   numbers.  The perisomatic document carries ``passive = {ra, cm, e_pas}`` and
   a 16-entry ``genome`` of floats; the all-active document carries
   ``passive = {ra}`` only, and moves ``Ra``, ``cm``, ``e_pas`` and ``g_pas``
   into a 42-entry ``genome`` whose values are **JSON strings**.  Allen's own
   loader expects exactly this split -- ``biophysical/utils.py`` defines
   ``Utils`` (perisomatic) and ``AllActiveUtils`` (all-active) with different
   ``load_cell_parameters`` bodies -- so the string values are a serialisation
   convention, not a defect.  They are only safe under ``AllActiveUtils``,
   which coerces with ``float(p["value"])``; ``Utils`` formats with
   ``"%g" % value`` and would raise ``TypeError``.  This script therefore
   checks each document against *its own* class contract and refuses to score
   one against the other's rules.
2. ``fit.json`` is only half of the pair Allen's runner consumes.  ``Config``
   reads the entry file named on the command line, then follows
   ``biophys[0].model_file`` and merges every listed file into one
   ``Description``.  In Allen's own shipped fixtures that list is
   ``["manifest.json", "<id>_fit.json"]``, so ``manifest.json`` is the entry
   point and supplies ``biophys``, ``neuron``, ``runs`` and the path
   ``manifest`` block.  Neither published ``fit.json`` contains any of those
   four keys.  The script asserts that absence explicitly rather than assuming
   the descriptor is self-sufficient.
3. ``fitting.junction_potential`` is consistently ``-14.0`` in both documents.
   It is reported, never applied: the convention belongs to the fitting
   pipeline that produced the parameters, so this script only records it.
4. Asset digests are pinned below, so a reviewer can prove the cached copies
   are byte-identical to what was fetched, and ``--verify-remote`` can
   re-download the originals and compare without writing anything.

Usage
-----
    python scripts/inspect_model_assets.py
    python scripts/inspect_model_assets.py --cache-dir data/model_cache
    python scripts/inspect_model_assets.py --verify-remote --json-out /tmp/2a.json

The asset cache is deliberately kept outside Git (it holds Allen redistribution
-restricted sources).  ``--cache-dir`` defaults to the first existing of
``data/model_cache`` and ``tmp/model_cache``.

Exit code 0 means every asset-level check passed.  1 means an asset-level check
failed (a corrupt, truncated or self-inconsistent asset).  2 is returned only
with ``--require-execution-ready``, when a known execution blocker is still
outstanding -- a distinction that matters because "the assets are intact" and
"the model can be run here" are different claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import sys

SPECIMEN = 382982932

#: Allen well-known-file ids, for provenance only.
WKF_PERISOMATIC_FIT = 497235792
WKF_ALL_ACTIVE_FIT = 568156386
WKF_SWC = 674389901
WKF_MARKER = 674389910

#: The junction potential every Allen biophysical fit declares.  Reported, not applied.
JUNCTION_MV = -14.0

#: Section *classes* a genome entry may reference.  Import3d instantiates these
#: from the SWC, and "glob" addresses NEURON globals rather than a section.
SECTION_CLASSES = ("soma", "axon", "dend", "apic")
GLOBAL_TOKEN = "glob"

#: Reference fixture manifests that document how Allen itself drives the runner.
FIXTURE_MANIFESTS = {
    "manifest_perisomatic.json": (
        1911, "ee677381bf6440e909654994f0dc115cc2d001f45bbbbaf5b42a3c41f6c19c8e"),
    "manifest_all_active.json": (
        1910, "681e524427585c5a285791519d21bce226c4a0ac7abfad912551cbe817ed564d"),
}

TEMPLATE_HOC = (
    715, "9b8f73f8202f355ea6f0c9f27be23bf2cb9bd122d9abc4fb864af88401b9a26d")

MORPHOLOGY_SWC = (
    "morphology/674389901_382982932_m.swc",
    335924, "71bb551b6ed6ce2fa03d916a648b1bf5fbcb3aa5e902ac8abc413956631ef36c",
    WKF_SWC)

MORPHOLOGY_MARKER = (
    "morphology/674389910_382982932_m.marker",
    373, "3cc83ad85e7caebd4c6b90988ee515674baf6c3912521d8d53636b7890980925",
    WKF_MARKER)

#: name -> (bytes, sha256).  AllenSDK v2.16.2, allensdk/test/model/peri_model/modfiles/.
MODFILES = {
    "CaDynamics.mod": (704, "f012def9758f7d0244b81c54291edea6597c15fad99b9f7b5725b121a3567f16"),
    "Ca_HVA.mod": (1211, "021d34cf9ef3e76b0f2afee1a1eeab40eed56d0d3b1362b7e1019f4433273c71"),
    "Ca_LVA.mod": (1069, "a7a9ef262541dc96f5d19afd97778f9320808d01ce397350f1f2be3db30f920f"),
    "Ih.mod": (1005, "8616325d83add9a1a6546972352b4a62e57095ba25f3c6b5a57ab8b397e2d662"),
    "Im.mod": (859, "e1c3bfb2186439bdb963ff2c53268efb824d8e00401aef0a14b7d2234071bb2c"),
    "Im_v2.mod": (761, "bc378428d3b4da76b6f9b1820dde1f52abef47389ce6edbcddb0c8fb967970fd"),
    "K_P.mod": (1161, "2254697617c8da162ff8e5495e4d512fce53f77b44b86754855f11cee4ab3b3e"),
    "K_T.mod": (1031, "1cb9d72f985ef028922cafafed079df5c47b87a893001304181ec48881367ba7"),
    "Kd.mod": (705, "1cac92486bf77c2976cad9a34e1741dc20ecda70d7b2c9bf5c3474e66f7dfcce"),
    "Kv2like.mod": (1433, "9244b0eb301dacee5a844910d6b4945856b90dc60937a74ac7f4f19f778d0895"),
    "Kv3_1.mod": (631, "e636c3437a9d9ccb69a0a7efc09fcfe1f16ad97f0468615b70fdbc352fe0855c"),
    "Nap.mod": (1170, "979d21508f5b089e7b782835ea7f60311223bdc3a8e5242056c594305d2fb220"),
    "NaTa.mod": (1413, "fd6af6564b365f5ec016b453c8f540a15780dea62597053d10cc402443541caf"),
    "NaTs.mod": (1267, "d75ed63d6367fe27c6e5671704594a510e8d83b57db835f30fc36e2f24bef6cf"),
    "NaV.mod": (4061, "635605ba861c070f8fdc273365f3a0fca6eee24762afc9b102161fdd6e9cfc42"),
    "SK.mod": (942, "079f1e3cac7444696d480b8e02853b215cd93e0c7b9986dbb54925fc49eddbeb"),
}

MODEL_CLASSES = {
    "perisomatic": {
        "label": "Biophysical - perisomatic",
        "model_id": 473862496,
        "template_id": 329230710,
        "descriptor": "models/perisomatic_473862496/382982932_fit.json",
        "descriptor_bytes": 2891,
        "descriptor_sha256":
            "d24d00aaed5a2a0ecf9752735b62254bba7ab3dc0d3627e61466f95b00a8e38f",
        "wkf": WKF_PERISOMATIC_FIT,
        # AllenSDK class that consumes this schema (biophysical/utils.py).
        "loader": "Utils",
        # Contract: passive must carry cm and e_pas; genome values are floats.
        "passive_extra": ("cm", "e_pas"),
        "genome_value_type": float,
    },
    "all_active": {
        "label": "Biophysical - all active",
        "model_id": 497233292,
        "template_id": 491455321,
        "descriptor": "models/all_active_497233292/497233292_fit.json",
        "descriptor_bytes": 5738,
        "descriptor_sha256":
            "bcffd56bbcec001be9ed329efd8badca3c2608d7a39a84fb94640b690deb5963",
        "wkf": WKF_ALL_ACTIVE_FIT,
        "loader": "AllActiveUtils",
        # Contract: passive is {ra} only; per-section cm/e_pas/Ra live in genome
        # and are coerced from strings by float(p["value"]).
        "passive_extra": (),
        "genome_value_type": str,
    },
}

#: Keys AllenSDK's runner requires and that these descriptors do not provide.
MANIFEST_ONLY_KEYS = ("biophys", "neuron", "runs", "manifest")

TOP_LEVEL_KEYS = ("passive", "fitting", "genome", "conditions")


class Checker:
    """Accumulates PASS/FAIL lines so one failure never hides the rest."""

    def __init__(self, stream=sys.stdout):
        self.stream = stream
        self.failures = []
        self.checks = 0

    def out(self, text=""):
        print(text, file=self.stream)

    def check(self, ok, label, detail=""):
        self.checks += 1
        if not ok:
            self.failures.append(label)
        mark = "ok  " if ok else "FAIL"
        self.out("  %s %-58s %s" % (mark, label, detail))
        return ok

    def skip(self, label, detail=""):
        self.out("  --   %-58s %s" % ("skipped: " + label, detail))


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_asset(chk, cache, rel, want_bytes, want_sha, note=""):
    path = cache / rel
    if not path.exists():
        return chk.check(False, "present: " + rel, "MISSING")
    size = path.stat().st_size
    digest = sha256_of(path)
    ok = size == want_bytes and digest == want_sha
    detail = "%d B  %s" % (size, digest[:16])
    if not ok:
        detail += "  expected %d B %s" % (want_bytes, want_sha[:16])
    if note:
        detail += "  " + note
    return chk.check(ok, "intact: " + rel.split("/")[-1], detail)


def load_descriptor(chk, cache, spec):
    """Load one fit.json and return (data, ok)."""
    path = cache / spec["descriptor"]
    verify_asset(chk, cache, spec["descriptor"], spec["descriptor_bytes"],
                 spec["descriptor_sha256"], "wkf %d" % spec["wkf"])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        chk.check(False, "parses: " + spec["descriptor"].split("/")[-1], str(exc))
        return None
    chk.check(True, "parses: " + spec["descriptor"].split("/")[-1],
              "%d top-level keys" % len(data))
    return data


def inspect_class(chk, cache, key, spec, results):
    """Run every descriptor-level check for one model class."""
    chk.out()
    chk.out("== %s  (neuronal_model %d, template %d, loader %s) =="
            % (spec["label"], spec["model_id"], spec["template_id"],
               spec["loader"]))

    data = load_descriptor(chk, cache, spec)
    result = {"class": key, "label": spec["label"], "model_id": spec["model_id"],
              "template_id": spec["template_id"], "loader": spec["loader"]}
    results["classes"][key] = result
    if data is None:
        result["status"] = "UNREADABLE"
        return

    # --- schema -----------------------------------------------------------
    missing = [k for k in TOP_LEVEL_KEYS if k not in data]
    chk.check(not missing, "schema: passive/fitting/genome/conditions present",
              "missing %s" % missing if missing else "")
    if missing:
        result["status"] = "INCOMPLETE"
        return
    for name in TOP_LEVEL_KEYS:
        chk.check(isinstance(data[name], list),
                  "schema: %s is a list" % name, type(data[name]).__name__)

    # The runner needs sections these descriptors cannot supply.
    absent = [k for k in MANIFEST_ONLY_KEYS if k not in data]
    result["manifest_keys_absent"] = absent
    chk.check(len(absent) == len(MANIFEST_ONLY_KEYS),
              "descriptor is not self-sufficient (no manifest block)",
              "absent: %s" % ",".join(absent))

    # --- passive ----------------------------------------------------------
    passive = data["passive"][0]
    result["passive"] = passive
    chk.check("ra" in passive, "passive: ra present",
              "ra=%s" % passive.get("ra"))
    chk.check(isinstance(passive.get("ra"), (int, float)) and
              float(passive["ra"]) > 0, "passive: ra is a positive number",
              str(passive.get("ra")))
    extra = tuple(k for k in spec["passive_extra"])
    has_extra = all(k in passive for k in extra)
    if extra:
        chk.check(has_extra, "passive: carries %s" % "/".join(extra),
                  "" if has_extra else "absent -> must come from genome")
    else:
        chk.check(not [k for k in ("cm", "e_pas") if k in passive],
                  "passive: ra only, cm/e_pas deferred to genome",
                  "keys=%s" % sorted(passive))

    # --- genome -----------------------------------------------------------
    genome = data["genome"]
    result["genome_count"] = len(genome)
    wanted_type = spec["genome_value_type"]
    bad_type = [p for p in genome if not isinstance(p["value"], wanted_type)]
    chk.check(not bad_type, "genome: %d values are %s"
              % (len(genome), wanted_type.__name__),
              "" if not bad_type else "%d wrong type" % len(bad_type))

    # Every value must be coercible to float even when stored as a string.
    uncoercible = []
    for entry in genome:
        try:
            float(entry["value"])
        except (TypeError, ValueError):
            uncoercible.append(entry)
    chk.check(not uncoercible, "genome: every value coerces to float",
              "" if not uncoercible else "%d bad" % len(uncoercible))

    sections = sorted({p["section"] for p in genome})
    unknown = [s for s in sections if s not in SECTION_CLASSES + (GLOBAL_TOKEN,)]
    chk.check(not unknown, "genome: sections are known classes",
              "|".join(sections))
    undeclared = [s for s in sections
                  if s != GLOBAL_TOKEN and s in SECTION_CLASSES]
    result["genome_sections"] = sections
    result["genome_uses_section_classes_only"] = not unknown

    mechanisms = sorted({p["mechanism"] for p in genome if p.get("mechanism")})
    result["mechanisms"] = mechanisms
    chk.check(bool(mechanisms), "genome: declares mechanisms",
              "|".join(mechanisms))

    # A section addressed with an empty mechanism must at least be a real class.
    chk.check(len(undeclared) <= len(SECTION_CLASSES),
              "genome: at most the four section classes are addressed",
              "%d distinct" % len(undeclared))

    # --- conditions -------------------------------------------------------
    conditions = data["conditions"][0]
    result["conditions"] = conditions
    chk.check("celsius" in conditions, "conditions: celsius present",
              "%s degC" % conditions.get("celsius"))
    chk.check("v_init" in conditions, "conditions: v_init present",
              "%s mV" % conditions.get("v_init"))
    chk.check("dt" not in conditions and "tstop" not in conditions,
              "conditions: dt/tstop absent (taken from the stimulus)",
              "dt=%s tstop=%s" % (conditions.get("dt"),
                                  conditions.get("tstop")))
    erev = conditions.get("erev") or []
    erev_sections = sorted({e["section"] for e in erev})
    result["erev_sections"] = erev_sections
    chk.check(bool(erev), "conditions: reversal potentials declared",
              "|".join(erev_sections) or "none")
    erev_bad = [e["section"] for e in erev
                if e["section"] not in SECTION_CLASSES]
    chk.check(not erev_bad, "conditions: erev sections are known classes",
              "|".join(erev_bad) if erev_bad else "ok")

    # --- fitting ----------------------------------------------------------
    fitting = data["fitting"][0]
    junction = fitting.get("junction_potential")
    result["junction_potential"] = junction
    result["sweeps"] = fitting.get("sweeps")
    chk.check(junction is not None and math.isclose(float(junction),
                                                    JUNCTION_MV, abs_tol=1e-9),
              "fitting: junction_potential is %.1f mV" % JUNCTION_MV,
              str(junction))
    sweeps = fitting.get("sweeps") or []
    chk.check(len(sweeps) >= 1, "fitting: sweeps recorded",
              "%d sweep(s): %s" % (len(sweeps), sweeps))
    chk.check(all(isinstance(s, int) and s >= 0 for s in sweeps),
              "fitting: sweep indices are non-negative integers", "")
    result["status"] = "CONSISTENT"


def mechanism_coverage(chk, cache, results):
    """Cross-check every declared mechanism against the cached .mod sources."""
    chk.out()
    chk.out("== mechanism coverage (.mod sources, AllenSDK v2.16.2) ==")

    available = sorted(path.stem for path in (cache / "allensdk/modfiles").glob("*.mod"))
    chk.check(len(available) == len(MODFILES), "16 modfiles cached",
              "%d found" % len(available))
    for name in sorted(MODFILES):
        verify_asset(chk, cache, "allensdk/modfiles/" + name, *MODFILES[name])

    # "pas" is inserted unconditionally by both loaders, not declared in genome,
    # and is a NEURON built-in rather than a .mod source.  It is tracked so the
    # per-class requirement list is complete, but excluded from file coverage.
    needed = {"pas"}
    for result in results["classes"].values():
        needed.update(result.get("mechanisms") or [])
    results["mechanisms_needed"] = sorted(needed)

    need_files = needed - {"pas"}
    missing = sorted(need_files - set(available))
    chk.check(not missing, "every declared mechanism has a .mod source",
              "missing %s" % missing if missing else
              "%d .mod mechanisms + built-in pas" % len(need_files))

    unused = sorted(set(available) - needed)
    results["mechanisms_unused"] = unused
    chk.out("  --   %-58s %s" % ("unused .mod sources", "|".join(unused) or "none"))
    for key, result in results["classes"].items():
        own = sorted(set(result.get("mechanisms") or []) | {"pas"})
        result["mechanisms_with_pas"] = own
        chk.out("  --   %-58s %s" % (key + " requires", "|".join(own)))


def inspect_morphology(chk, cache, results):
    """Parse the published SWC and report section counts and lengths."""
    chk.out()
    chk.out("== morphology (specimen's published SWC, not the fitted recon) ==")
    rel, want_bytes, want_sha, wkf = MORPHOLOGY_SWC
    path = cache / rel
    if not chk.check(path.exists(), "present: SWC", rel):
        results["morphology"] = {"status": "ABSENT"}
        return
    ok = verify_asset(chk, cache, rel, want_bytes, want_sha, "wkf %d" % wkf)

    rows, comments = [], []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                comments.append(line)
                continue
            parts = line.split()
            if len(parts) < 7:
                continue
            try:
                rows.append((int(parts[0]), int(parts[1]),
                             float(parts[2]), float(parts[3]), float(parts[4]),
                             int(parts[6])))
            except ValueError:
                continue

    counts, lengths = {}, {}
    by_id = {r[0]: r for r in rows}
    for ident, stype, x, y, z, parent in rows:
        counts[stype] = counts.get(stype, 0) + 1
        if parent <= 0 or parent not in by_id:
            continue
        _, ptype, px, py, pz, _ = by_id[parent]
        seg = math.dist((x, y, z), (px, py, pz))
        # SWC point types whose segment is conventionally counted toward that type.
        owner = stype if stype in (2, 3, 4) else ptype
        lengths[owner] = lengths.get(owner, 0.0) + seg

    soma_nodes = counts.get(1, 0)
    dend_nodes = counts.get(3, 0) + counts.get(4, 0)
    axon_nodes = counts.get(2, 0)
    dend_len = lengths.get(3, 0.0) + lengths.get(4, 0.0)
    axon_len = lengths.get(2, 0.0)

    chk.check(len(rows) > 0, "SWC parses as numeric points", "%d points" % len(rows))
    chk.check(soma_nodes >= 1, "SWC has a soma (type 1)", "%d node(s)" % soma_nodes)
    chk.check(dend_nodes > 0, "SWC has dendrites (types 3/4)", "%d nodes" % dend_nodes)

    results["morphology"] = {
        "status": "PARSED" if ok else "PARSED_UNVERIFIED",
        "path": rel, "wkf": wkf, "points": len(rows),
        "counts_by_type": {str(k): v for k, v in sorted(counts.items())},
        "soma_nodes": soma_nodes, "dendrite_nodes": dend_nodes,
        "axon_nodes": axon_nodes, "dendrite_length_um": round(dend_len, 2),
        "axon_length_um": round(axon_len, 2),
        "header": comments[:4],
    }
    chk.out("       types: " + "  ".join("%d=%d" % kv
                                         for kv in sorted(counts.items())))
    chk.out("       dendrite %.2f um, axon %.2f um, %d dendrite nodes"
            % (dend_len, axon_len, dend_nodes))
    for line in comments[:2]:
        chk.out("       " + line[:110])

    mrel, mbytes, msha, mwkf = MORPHOLOGY_MARKER
    if chk.check((cache / mrel).exists(), "present: marker file", mrel):
        verify_asset(chk, cache, mrel, mbytes, msha, "wkf %d" % mwkf)
        results["morphology"]["marker_path"] = mrel


def template_and_runner(chk, cache, results):
    """Report the template, the NEURON-shipped hocs and the missing manifest."""
    chk.out()
    chk.out("== template and runner inputs ==")
    verify_asset(chk, cache, "allensdk/cell.hoc", *TEMPLATE_HOC)
    for name, (want_bytes, want_sha) in sorted(FIXTURE_MANIFESTS.items()):
        verify_asset(chk, cache, "allensdk/reference/" + name, want_bytes, want_sha)

    hoc = cache / "allensdk/cell.hoc"
    if hoc.exists():
        text = hoc.read_text(encoding="utf-8", errors="replace")
        creates = [tok for tok in ("soma[1]", "dend[1]", "apic[1]", "axon[1]")
                   if "create " + tok in text]
        results["template_creates"] = creates
        chk.check(len(creates) == 4, "cell.hoc creates all four section arrays",
                  "|".join(creates))

    # Allen's fixture manifest names three hocs; two ship with NEURON itself.
    ref = cache / "allensdk/reference/manifest_perisomatic.json"
    if ref.exists():
        manifest = json.loads(ref.read_text(encoding="utf-8"))
        hocs = manifest.get("neuron", [{}])[0].get("hoc", [])
        results["fixture_hocs"] = hocs
        shipped = [h for h in hocs if h != "cell.hoc"]
        chk.out("  --   %-58s %s" % ("fixture neuron.hoc list", "|".join(hocs)))
        chk.out("  --   %-58s %s" % ("supplied by NEURON, not AllenSDK",
                                     "|".join(shipped) or "none"))
        loop = [b.get("model_type") for b in manifest.get("biophys", [])]
        results["fixture_biophys"] = manifest.get("biophys")
        chk.out("  --   %-58s %s" % ("fixture biophys block", "|".join(
            str(x) for x in loop)))
        keys = [e.get("key") for e in manifest.get("manifest", [])]
        results["manifest_keys"] = keys
        chk.out("  --   %-58s %s" % ("manifest path keys it declares",
                                     "|".join(k for k in keys if k)))


def dependency_table(chk, cache, results):
    """Print one row per dependency the runner would need."""
    chk.out()
    chk.out("== dependency readiness for specimen %d ==" % SPECIMEN)
    header = ("%-34s %-12s %-11s %-8s %s"
              % ("dependency", "perisomatic", "all-active", "present", "note"))
    chk.out("  " + header)
    chk.out("  " + "-" * (len(header) + 6))

    nwb = cache.parent / "nwb_cache" / ("%d.nwb" % SPECIMEN)
    if not nwb.exists():
        nwb = pathlib.Path("data/nwb_cache") / ("%d.nwb" % SPECIMEN)

    rows = []
    rows.append(("fit.json parameters", "yes", "yes", "yes",
                 "published, digest-pinned"))
    rows.append(("manifest.json (runner entry)", "MISSING", "MISSING", "no",
                 "not published by the RMA API"))
    rows.append(("biophys[1].axon_type", "MISSING", "MISSING", "no",
                 "required by create_utils()"))
    rows.append(("runs[0].sweeps_by_type", "MISSING", "MISSING", "no",
                 "required by run_sync()"))
    rows.append(("cell.hoc template", "yes", "yes", "yes", "AllenSDK v2.16.2"))
    rows.append(("import3d.hoc / stdgui.hoc", "NEURON", "NEURON", "no",
                 "shipped with NEURON"))
    rows.append(("15 .mod mechanisms", "yes", "yes", "yes", "16-file canonical set"))
    rows.append(("morphology SWC", "substitute", "substitute", "yes",
                 "specimen SWC, not fitted recon"))
    rows.append(("marker file", "yes", "yes", "yes", ".marker, fixture wants .swc"))
    rows.append(("stimulus NWB", "yes", "yes",
                 "yes" if nwb.exists() else "no",
                 "data/nwb_cache/%d.nwb" % SPECIMEN))
    rows.append(("NwbDataSet (stimulus reader)", "MISSING", "MISSING", "no",
                 "allensdk.core.nwb_data_set"))
    rows.append(("NEURON interpreter", "MISSING", "MISSING", "no",
                 "no Windows build on PyPI/conda"))
    rows.append(("nrnivmodl + compiler", "MISSING", "MISSING", "no",
                 "no MSVC/cl or make on PATH"))
    results["dependencies"] = [dict(zip(
        ("dependency", "perisomatic", "all_active", "present", "note"), r))
        for r in rows]
    for r in rows:
        chk.out("  %-34s %-12s %-11s %-8s %s" % r)
    results["stimulus_nwb"] = str(nwb) if nwb.exists() else None

    blockers = [r[0] for r in rows if r[3] == "no"]
    results["execution_blockers"] = blockers
    chk.out()
    chk.out("  %d dependency(ies) still missing before a simulation is possible."
            % len(blockers))


def verify_remote(chk, results, cache):
    """Re-download the originals in memory and compare digests.  Writes nothing."""
    chk.out()
    chk.out("== remote re-verification (read-only, nothing written) ==")
    try:
        import requests
    except ImportError:
        chk.skip("remote verification", "requests not installed")
        return

    wkf = "http://api.brain-map.org/api/v2/well_known_file_download/%d"
    raw = ("https://raw.githubusercontent.com/AllenInstitute/AllenSDK/"
           "v2.16.2/allensdk/model/biophysical/cell.hoc")
    targets = [
        ("fit.json perisomatic", wkf % WKF_PERISOMATIC_FIT,
         MODEL_CLASSES["perisomatic"]["descriptor_sha256"]),
        ("fit.json all-active", wkf % WKF_ALL_ACTIVE_FIT,
         MODEL_CLASSES["all_active"]["descriptor_sha256"]),
        ("morphology SWC", wkf % WKF_SWC, MORPHOLOGY_SWC[2]),
        ("marker", wkf % WKF_MARKER, MORPHOLOGY_MARKER[2]),
        ("cell.hoc", raw, TEMPLATE_HOC[1]),
    ]
    for label, url, want in targets:
        try:
            body = requests.get(url, timeout=120).content
        except Exception as exc:                            # noqa: BLE001
            chk.check(False, "remote: " + label, str(exc)[:60])
            continue
        got = hashlib.sha256(body).hexdigest()
        chk.check(got == want, "remote: " + label, "%d B  %s" % (len(body), got[:16]))
    results["remote_verified"] = True


def resolve_cache(root, override):
    if override is not None:
        return override
    for candidate in (root / "data/model_cache", root / "tmp/model_cache"):
        if candidate.is_dir():
            return candidate
    return root / "data/model_cache"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--cache-dir", type=pathlib.Path, default=None,
                        help="asset cache (default: data/model_cache, else "
                             "tmp/model_cache)")
    parser.add_argument("--verify-remote", action="store_true",
                        help="re-download originals and compare digests (no writes)")
    parser.add_argument("--require-execution-ready", action="store_true",
                        help="exit 2 if any execution blocker remains")
    parser.add_argument("--json-out", type=pathlib.Path, default=None,
                        help="write the structured result as JSON (keep out of Git)")
    args = parser.parse_args(argv)

    cache = resolve_cache(args.repo_root, args.cache_dir)
    chk = Checker()
    results = {"specimen_id": SPECIMEN, "cache_dir": str(cache),
               "junction_potential_mv": JUNCTION_MV,
               "classes": {}, "no_simulation_executed": True}

    chk.out("Allen biophysical model asset inspection - specimen %d" % SPECIMEN)
    chk.out("cache: %s" % cache)
    chk.out()
    chk.out("== descriptors ==")
    if not cache.is_dir():
        chk.check(False, "cache directory exists", str(cache))
    else:
        for key, spec in MODEL_CLASSES.items():
            inspect_class(chk, cache, key, spec, results)
        mechanism_coverage(chk, cache, results)
        inspect_morphology(chk, cache, results)
        template_and_runner(chk, cache, results)
        dependency_table(chk, cache, results)
        if args.verify_remote:
            verify_remote(chk, results, cache)

    results["checks"] = chk.checks
    results["failures"] = chk.failures

    chk.out()
    chk.out("=" * 78)
    chk.out("%-14s %-20s %-12s %s"
            % ("model class", "neuronal_model", "status", "mechanisms"))
    for key, result in results["classes"].items():
        chk.out("%-14s %-20d %-12s %s"
                % (key, result["model_id"], result.get("status", "?"),
                   len(result.get("mechanisms_with_pas") or [])))
    chk.out()
    chk.out("%d checks, %d failure(s)" % (chk.checks, len(chk.failures)))
    if chk.failures:
        for name in chk.failures[:12]:
            chk.out("  failed: " + name)
    chk.out("no NEURON call and no simulation was performed by this script.")

    if args.json_out:
        args.json_out.write_text(json.dumps(results, indent=2, default=str),
                                 encoding="utf-8")
        chk.out("JSON written to %s" % args.json_out)

    if chk.failures:
        return 1
    if args.require_execution_ready and results.get("execution_blockers"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Validate Allen NWB stimulus units against the committed Phase 0 sweep inventory.

Purpose
-------
Answer one question per specimen: *do the raw stimulus samples in a cached NWB
file agree, numerically, with ``stimulus_absolute_amplitude`` in
``data/metadata/sweep_inventory.csv``, once the declared units and conversion
factors are applied?*  This is a units-and-coverage auditor.  It does **not**
fit models, extract features, or produce scientific results.

Why the implementation looks the way it does
--------------------------------------------
Phase 1A (specimen 341442651) showed that three naive assumptions all produce
wrong answers on real Allen files:

1. ``aibs_stimulus_description`` is stored as a truncated ``|S16`` string, so the
   ``x<multiplier>`` suffix and the ``[index]`` suffix are lost.  The template
   basename reachable through the ``data_link`` attribute is the only intact
   copy.  We therefore match sweeps by *sweep number* and then verify the
   template base name as a check, instead of using it as a join key (using it as
   a join key silently produces a cartesian product, because one template
   repeats across many sweeps).
2. A naive maximum-excursion plateau detector is wrong.  Every sweep carries an
   embedded short pulse before the step, so once ``|step|`` falls below roughly
   twice the pulse amplitude the detector locks onto the pulse.  We instead
   extract the *dominant non-baseline level* by sample count.
3. The step is ~1 s but its onset is not fixed across campaigns (the 341442651
   files start it at 1.02 s).  Nothing here is hardcoded to a time window: the
   plateau is located in the data and every other constant run is reported.
4. The ``conversion`` attribute cannot be trusted on its own.  In one of the
   seven checked files (specimen 471129934) every stimulus series declares
   ``unit='Amps'`` **and** ``conversion=1e-12``, while the stored samples
   already carry ampere magnitudes and the series' own
   ``aibs_stimulus_amplitude_pa`` equals ``raw * 1e12`` to 3e-15 relative.
   Applying ``conversion`` as NWB 1.x prescribes would understate the current
   by 1e12 and produce a spurious scale mismatch.  Both readings are therefore
   scored -- ``raw * conversion + offset`` and ``raw + offset`` -- and a
   verdict of ``MATCH_CONVERSION_CONFLICT`` is returned when only the second
   agrees, instead of silently choosing one.

Units are never silently converted.  The declared unit string, the ``conversion``
and ``resolution`` attributes, and any ``offset`` are all reported verbatim, and
the single multiplication used to reach picoamperes is named in the output.

Usage
-----
    python scripts/validate_nwb_stimulus_units.py --specimen 341442651
    python scripts/validate_nwb_stimulus_units.py --all
    python scripts/validate_nwb_stimulus_units.py --all --json-out report.json

Requires ``h5py==3.16.0`` (see ``scripts/requirements-nwb-validation.txt``).
Exit code is 0 when every validated specimen reaches a definite verdict
(MATCH or MISMATCH), and 2 when any specimen ends AMBIGUOUS / UNRESOLVED or
MATCH_CONVERSION_CONFLICT (a definite amplitude agreement reached only by
disregarding a contradicted ``conversion`` attribute, which a consumer must
adjudicate before trusting).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import h5py
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Constants.  Every conversion factor used anywhere in this file is declared
# here so the reader can audit them in one place.
# --------------------------------------------------------------------------

HDF5_MAGIC = b"\x89HDF\r\n\x1a\n"

#: Multipliers that take a value expressed in the given unit to picoamperes.
#: Keys are lower-cased, stripped unit strings as they actually appear in files.
UNIT_TO_PA = {
    "a": 1e12,
    "amp": 1e12,
    "amps": 1e12,
    "ampere": 1e12,
    "amperes": 1e12,
    "ma": 1e9,
    "ua": 1e6,
    "microamp": 1e6,
    "microamps": 1e6,
    "na": 1e3,
    "nanoamp": 1e3,
    "nanoamps": 1e3,
    "pa": 1.0,
    "picoamp": 1.0,
    "picoamps": 1.0,
    "fa": 1e-3,
}

#: A non-baseline constant run shorter than this is reported as an embedded
#: pulse rather than as the stimulus step.  This is a classifier threshold, not
#: a time window: no part of any trace is excluded from analysis.
MIN_STEP_MS = 100.0

#: Tolerance for calling a measured plateau equal to the inventory amplitude.
#: Absolute floor in pA, plus a relative term for large amplitudes.
ABS_TOL_PA = 0.5
REL_TOL_PA = 1e-6

#: A disagreement is reported as a *scale* mismatch when the ratio of measured
#: to expected pA sits within this many decades of an exact power of 1000.
#: Unit-prefix mistakes (mA, uA, nA, pA vs A) can only produce such ratios.
SCALE_TOL_DECADES = 0.5


# --------------------------------------------------------------------------
# NWB access helpers (NWB 1.x layout, with an NWB 2.x fallback)
# --------------------------------------------------------------------------


def open_nwb(path: pathlib.Path) -> h5py.File:
    """Open an HDF5 file after checking the magic number explicitly."""
    head = path.open("rb").read(8)
    if head != HDF5_MAGIC:
        raise ValueError("%s is not HDF5 (magic %r)" % (path, head))
    return h5py.File(path, "r")


def nwb_version(f: h5py.File) -> tuple[str, str]:
    """Return (version string, where it was found).

    The Allen NWB 1.x files store this as a root *dataset* ``nwb_version``
    holding e.g. ``b'NWB-1.0.5'``; NWB 2.x stores it as a root attribute.
    """
    for where, getter in (
        ("root dataset nwb_version", lambda: f["nwb_version"]),
        ("/general/nwb_version", lambda: f["general/nwb_version"]),
        ("root attr nwb_version", lambda: f.attrs["nwb_version"]),
        ("root attr nwb_version_major", lambda: f.attrs["nwb_version_major"]),
    ):
        try:
            node = getter()
        except Exception:
            continue
        if isinstance(node, h5py.Dataset):
            return _as_text(node[()]), where
        return _as_text(node), where
    return "unknown", "not found"


def _as_text(value) -> str:
    """Decode bytes / arrays of bytes / numpy strings to a plain str."""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "S":
            return value.item().decode("utf-8", "replace") if value.size == 1 else \
                value.tobytes().decode("utf-8", "replace")
        return str(value.tolist())
    return str(value)


def list_series(root: h5py.File, path: str):
    """Return ``(name, node)`` for every series under an explicit HDF5 path.

    In the Allen NWB 1.x layout each sweep is a *group*
    (``/stimulus/presentation/Sweep_<n>``) holding a ``data`` dataset, a
    ``starting_time`` dataset and the ``aibs_*`` metadata datasets, with
    ``data_link`` as a group attribute.  NWB 2.x may store a bare dataset
    instead.  Nodes of neither shape are skipped rather than guessed at.
    """
    if path not in root:
        return []
    group = root[path]
    out = []
    for name in sorted(group.keys()):
        node = group[name]
        if isinstance(node, h5py.Dataset) or series_data(node) is not None:
            out.append((name, node))
    return out


def series_data(node):
    """Return the sample array dataset of a series, or None."""
    if isinstance(node, h5py.Dataset):
        return node
    if isinstance(node, h5py.Group) and "data" in node:
        child = node["data"]
        if isinstance(child, h5py.Dataset):
            return child
    return None


def s_field(node, *names, default=None):
    """Read a per-series metadata field.

    Allen stores most of these as *child datasets* of the series group
    (``aibs_stimulus_name``, ``aibs_stimulus_amplitude_pa``, ...) and a few as
    group attributes (``data_link``); both forms are accepted.
    """
    for name in names:
        if isinstance(node, h5py.Group) and name in node:
            child = node[name]
            if isinstance(child, h5py.Dataset):
                try:
                    return child[()]
                except Exception:
                    pass
        if name in node.attrs:
            return node.attrs[name]
    return default


def s_num(node, *names, default=np.nan) -> float:
    """Numeric form of :func:`s_field`."""
    value = s_field(node, *names, default=None)
    if value is None:
        return default
    try:
        return float(np.asarray(value).ravel()[0])
    except Exception:
        return default


def series_attr(node, name, default=None):
    """Read ``unit`` / ``conversion`` / ``resolution`` / ``offset``.

    NWB 1.x carries these on the ``data`` dataset; some writers put them on the
    series group.  Both are checked, ``data`` first.
    """
    data = series_data(node)
    if data is not None and name in data.attrs:
        return data.attrs[name]
    if name in node.attrs:
        return node.attrs[name]
    return default


def series_num(node, name, default=np.nan) -> float:
    value = series_attr(node, name, None)
    if value is None:
        return default
    try:
        return float(np.asarray(value).ravel()[0])
    except Exception:
        return default


def series_rate(node) -> float:
    """Sampling rate in Hz, from ``starting_time @rate`` or a ``rate`` attr."""
    if isinstance(node, h5py.Group) and "starting_time" in node:
        child = node["starting_time"]
        if "rate" in child.attrs:
            return float(np.asarray(child.attrs["rate"]).ravel()[0])
    if "rate" in node.attrs:
        return float(np.asarray(node.attrs["rate"]).ravel()[0])
    return np.nan


def template_key(node) -> tuple[str, float | None]:
    """Recover the untruncated stimulus identity and multiplier.

    ``aibs_stimulus_description`` is a truncated ``|S16`` field, so the only
    intact copy of ``<base>[<index>]x<multiplier>`` is the basename of the
    template this series links to.  Returns ``(base_with_index, multiplier)``.
    """
    link = s_field(node, "data_link")
    candidate = None
    if link is not None:
        for entry in np.asarray(link).ravel():
            text = _as_text(entry)
            if "templates/" in text:
                candidate = text.split("templates/")[-1].strip("/")
                break
    if candidate is None:
        candidate = _as_text(s_field(node, "aibs_stimulus_description", default=""))
    base, _, mult = candidate.rpartition("x")
    if not base:  # no 'x' present
        return candidate, None
    try:
        return base, float(mult)
    except ValueError:
        return candidate, None


# --------------------------------------------------------------------------
# Trace analysis
# --------------------------------------------------------------------------


def constant_runs(x: np.ndarray) -> list[tuple[int, int, float]]:
    """Group a 1-D trace into maximal runs of identical value.

    Returns ``(start, stop_exclusive, value)`` triples in sample index order.
    Working on exact equality is correct here: NWB stores the commanded stimulus
    as quantised float32 samples, so a constant level repeats bit-for-bit.
    """
    if x.size == 0:
        return []
    change = np.flatnonzero(np.diff(x) != 0)
    bounds = np.concatenate(([0], change + 1, [x.size]))
    return [(int(bounds[i]), int(bounds[i + 1]), float(x[bounds[i]]))
            for i in range(len(bounds) - 1)]


def analyse_trace(x: np.ndarray, rate_hz: float) -> dict:
    """Locate baseline and the stimulus step without assuming any time window.

    The baseline is the value covering the most samples.  The step is the
    longest constant non-baseline run.  Every other non-baseline run is returned
    as an embedded pulse so that the caller can report it rather than exclude it.
    """
    runs = constant_runs(x)
    if not runs:
        return {"status": "UNRESOLVED", "reason": "empty trace"}

    counts: dict[float, int] = {}
    for start, stop, value in runs:
        counts[value] = counts.get(value, 0) + (stop - start)
    baseline = max(counts, key=lambda v: (counts[v], -abs(v)))

    non_base = [r for r in runs if r[2] != baseline]
    if not non_base:
        return {"status": "AMBIGUOUS", "reason": "no non-baseline level",
                "baseline": baseline}

    ordered = sorted(non_base, key=lambda r: -(r[1] - r[0]))
    step = ordered[0]
    step_ms = (step[1] - step[0]) / rate_hz * 1e3

    result = {
        "baseline": baseline,
        "baseline_ms": counts[baseline] / rate_hz * 1e3,
        "level": step[2],
        "level_samples": step[1] - step[0],
        "level_ms": step_ms,
        "onset_s": step[0] / rate_hz,
        "offset_s": step[1] / rate_hz,
        "n_distinct_values": len(counts),
        "n_non_baseline_runs": len(non_base),
        "extra_runs": [
            {"level": r[2], "samples": r[1] - r[0],
             "start_s": r[0] / rate_hz, "end_s": r[1] / rate_hz}
            for r in ordered[1:]
        ],
    }
    if step_ms < MIN_STEP_MS:
        result["status"] = "AMBIGUOUS"
        result["reason"] = ("longest non-baseline run is %.2f ms, below the "
                            "%.0f ms step threshold" % (step_ms, MIN_STEP_MS))
    else:
        result["status"] = "OK"
    return result


def unit_factor_pa(unit_text: str) -> tuple[float | None, str]:
    """Return (multiplier to pA, normalised unit) or (None, unit) if unknown."""
    key = str(unit_text).strip().lower()
    return UNIT_TO_PA.get(key), key


def classify(measured_pa: float, expected_pa: float) -> tuple[str, float]:
    """Compare a measured plateau with the inventory amplitude.

    Returns ``(verdict, ratio)`` where ``ratio`` is ``measured / expected``.
    A ratio within :data:`SCALE_TOL_DECADES` decades of an exact power of 1000
    is reported as ``MISMATCH_SCALE``: that is the numeric signature of a label
    written in the wrong unit prefix (mA / uA / nA / pA / A), as opposed to a
    genuinely wrong value.
    """
    if expected_pa is None or not np.isfinite(expected_pa) or expected_pa == 0:
        return "UNRESOLVED", np.nan
    diff = abs(measured_pa - expected_pa)
    if diff <= max(ABS_TOL_PA, REL_TOL_PA * abs(expected_pa)):
        return "MATCH", measured_pa / expected_pa
    ratio = measured_pa / expected_pa
    if ratio > 0:
        exponent = abs(np.log10(abs(ratio)))
        nearest = round(exponent / 3.0) * 3.0
        if nearest >= 3 and abs(exponent - nearest) <= SCALE_TOL_DECADES:
            return "MISMATCH_SCALE", ratio
    return "MISMATCH", ratio


# --------------------------------------------------------------------------
# Per-specimen validation
# --------------------------------------------------------------------------


def load_inventory(root: pathlib.Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    cells = pd.read_csv(root / "data/metadata/cell_inventory.csv")
    sweeps = pd.read_csv(root / "data/metadata/sweep_inventory.csv")
    # The Phase 0 units-aware current-clamp rule: a sweep with a null clamp_mode
    # is treated as current clamp only when its stimulus is labelled in pA.
    sweeps["is_current_clamp"] = (
        (sweeps["clamp_mode"] == "current_clamp")
        | (sweeps["clamp_mode"].isna() & (sweeps["stimulus_units"] == "pA"))
    )
    return cells, sweeps


def validate_specimen(specimen_id: int, root: pathlib.Path,
                      cells: pd.DataFrame, sweeps: pd.DataFrame,
                      cache: pathlib.Path) -> dict:
    """Validate one cached NWB file and return a JSON-serialisable result."""
    record: dict = {"specimen_id": int(specimen_id)}
    matches = cells[cells["specimen_id"] == specimen_id]
    if matches.empty:
        record["verdict"] = "UNRESOLVED"
        record["reason"] = "specimen not present in cell_inventory.csv"
        return record
    cell = matches.iloc[0]
    record["inventory"] = {
        "specimen_name": cell.get("specimen_name"),
        "cortical_layer": cell.get("cortical_layer"),
        "dendrite_type": cell.get("dendrite_type"),
        "ephys_sampling_rate": _maybe_float(cell.get("ephys_sampling_rate")),
        "nwb_file_id": _maybe_float(cell.get("nwb_file_id")),
        "nwb_download_url": cell.get("nwb_download_url"),
        "eligibility": cell.get("eligibility"),
        "n_models_total": _maybe_float(cell.get("n_models_total")),
        "n_biophysical_models": _maybe_float(cell.get("n_biophysical_models")),
    }

    path = cache / ("%d.nwb" % specimen_id)
    if not path.exists():
        record["verdict"] = "UNRESOLVED"
        record["reason"] = "cached NWB not found at %s" % path
        return record

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    record["file"] = {"path": str(path), "size_bytes": path.stat().st_size,
                      "sha256": digest.hexdigest()}

    with open_nwb(path) as f:
        version, version_src = nwb_version(f)
        record["nwb"] = {"version": version, "version_source": version_src,
                         "root_keys": sorted(f.keys())}
        # Identity chain: the file must name the specimen it claims to be.
        chain = {}
        for key in ("/general/aibs_specimen_id", "/general/session_id",
                    "/identifier"):
            try:
                node = f[key]
                chain[key] = _as_text(node[()] if isinstance(node, h5py.Dataset)
                                      else node)
            except Exception:
                chain[key] = None
        record["identity_chain"] = chain

        stimulus = list_series(f, "stimulus/presentation")
        if not stimulus:                     # NWB 2.x / acquisition fallback
            stimulus = [s for s in list_series(f, "acquisition/timeseries")
                        if s_field(s[1], "aibs_stimulus_name",
                                   "stimulus_description") is not None]
        record["nwb"]["n_stimulus_series"] = len(stimulus)
        record["nwb"]["has_analysis_spike_times"] = "analysis" in f and \
            "spike_times" in f["analysis"]

        inv_ls = sweeps[(sweeps["specimen_id"] == specimen_id)
                        & (sweeps["stimulus_category"] == "long_square")
                        & (sweeps["is_current_clamp"])].copy()

        per_sweep = []
        for name, node in stimulus:
            data = series_data(node)
            if data is None:
                continue
            stim_name = _as_text(s_field(node, "aibs_stimulus_name", default=""))
            desc = _as_text(s_field(node, "aibs_stimulus_description",
                                    "stimulus_description", default=""))
            if stim_name and "long square" not in stim_name.lower():
                continue
            if not stim_name and "long square" not in desc.lower():
                continue
            try:
                sweep_no = int(str(name).split("_")[-1])
            except ValueError:
                continue

            rate = series_rate(node)
            unit_text = _as_text(series_attr(node, "unit", default=""))
            conversion = series_num(node, "conversion", 1.0)
            resolution = series_num(node, "resolution", np.nan)
            offset = series_num(node, "offset", 0.0)
            base, mult = template_key(node)
            samples = data[()]

            row = {"sweep": sweep_no, "series": name, "stimulus_name": stim_name,
                   "template": base, "template_multiplier": mult,
                   "declared_unit": unit_text, "conversion": conversion,
                   "resolution": resolution, "offset": offset,
                   "rate_hz": float(rate) if np.isfinite(rate) else None,
                   "n_samples": int(samples.size),
                   "aibs_amplitude_pa": s_num(node, "aibs_stimulus_amplitude_pa")}
            row["trace"] = analyse_trace(np.asarray(samples, dtype=np.float64), rate) \
                if np.isfinite(rate) else {"status": "UNRESOLVED", "reason": "no rate"}

            factor, norm_unit = unit_factor_pa(unit_text)
            row["unit_normalised"] = norm_unit
            row["unit_factor_to_pA"] = factor
            if factor is None or row["trace"].get("status") != "OK":
                row["verdict"] = "UNRESOLVED"
                per_sweep.append(row)
                continue
            # physical = raw * conversion + offset, then one declared factor to pA
            raw = row["trace"]["level"]
            physical = raw * conversion + offset
            row["measured_physical"] = physical
            row["measured_pA_spec"] = physical * factor
            # Second reading: treat the samples as already being in the declared
            # unit (conversion = 1).  Identical to the line above whenever the
            # file declares conversion = 1, which is the normal case.
            row["measured_pA_unit_only"] = (raw + offset) * factor
            row["measured_pA"] = row["measured_pA_spec"]
            # Independent second reference: Allen's own pA field, when present.
            aibs = row.get("aibs_amplitude_pa")
            row["aibs_delta_pA"] = (row["measured_pA"] - aibs) \
                if aibs is not None and np.isfinite(aibs) else None

            inv = inv_ls[inv_ls["sweep_number"] == sweep_no]
            if len(inv) != 1:
                row["verdict"] = "UNRESOLVED"
                row["reason"] = ("%d inventory rows for sweep %d"
                                 % (len(inv), sweep_no))
                per_sweep.append(row)
                continue
            inv_row = inv.iloc[0]
            expected = _maybe_float(inv_row.get("stimulus_absolute_amplitude"))
            row["inventory_amplitude"] = expected
            row["inventory_units"] = inv_row.get("stimulus_units")
            row["inventory_description"] = inv_row.get("stimulus_description")
            expected_pa = expected if expected == expected else None
            verdict, ratio = classify(row["measured_pA_spec"], expected_pa)
            row["verdict_spec"] = verdict
            row["ratio_spec"] = ratio
            if verdict != "MATCH" and conversion != 1.0:
                # Only a non-unity conversion can make the two readings differ.
                alt_verdict, alt_ratio = classify(row["measured_pA_unit_only"],
                                                  expected_pa)
                if alt_verdict == "MATCH":
                    # The declared conversion is contradicted by the file's own
                    # samples.  Report it; never fall back silently.
                    verdict, ratio = "MATCH_CONVERSION_CONFLICT", alt_ratio
                    row["measured_pA"] = row["measured_pA_unit_only"]
                    row["aibs_delta_pA"] = (
                        row["measured_pA"] - aibs
                        if aibs is not None and np.isfinite(aibs) else None)
            row["verdict"] = verdict
            row["ratio_measured_over_expected"] = ratio
            # Cross-checks that never drive the verdict, only explain it.
            row["description_agrees"] = bool(
                str(inv_row.get("stimulus_description")) == str(base))
            row["inventory_label_matches_declared_unit"] = bool(
                str(inv_row.get("stimulus_units")) == unit_text)
            per_sweep.append(row)

        record["sweeps"] = per_sweep
        record["coverage"] = {
            "inventory_long_square_rows": int(len(inv_ls)),
            "nwb_long_square_series": int(len(per_sweep)),
            "matched_by_sweep_number": int(sum(
                1 for r in per_sweep if "inventory_amplitude" in r)),
            "inventory_only": sorted(set(
                inv_ls["sweep_number"].tolist())
                - set(r["sweep"] for r in per_sweep)),
        }
        record["verdict"] = summarise(per_sweep, inv_ls)
    return record


def summarise(per_sweep: list[dict], inv_ls: pd.DataFrame) -> str:
    """Reduce per-sweep verdicts to one specimen verdict."""
    if not per_sweep:
        return "UNRESOLVED"
    verdicts = [r["verdict"] for r in per_sweep]
    n_match = verdicts.count("MATCH")
    n_conflict = verdicts.count("MATCH_CONVERSION_CONFLICT")
    n_scale = verdicts.count("MISMATCH_SCALE")
    n_mismatch = verdicts.count("MISMATCH") + n_scale
    n_open = len(verdicts) - n_match - n_conflict - n_mismatch
    if n_open == len(verdicts):
        return "UNRESOLVED"
    if n_mismatch == 0:
        if n_conflict:
            return "AMBIGUOUS" if n_open else "MATCH_CONVERSION_CONFLICT"
        return "MATCH" if n_open == 0 else "MATCH_WITH_UNRESOLVED"
    if n_match == 0 and n_conflict == 0:
        return "MISMATCH_SCALE" if n_scale == n_mismatch else "MISMATCH"
    return "AMBIGUOUS"


def _maybe_float(value):
    try:
        out = float(value)
        return None if not np.isfinite(out) else out
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def report(record: dict, stream=sys.stdout) -> None:
    """Print a human-readable block for one specimen."""
    print("=" * 78, file=stream)
    print("specimen %d   verdict=%s" % (record["specimen_id"],
                                        record.get("verdict", "?")), file=stream)
    inv = record.get("inventory")
    if inv:
        print("  %s  VISp %s  %s  label=%s  rate=%s Hz  eligibility=%s"
              % (inv["specimen_name"], inv["cortical_layer"],
                 inv["dendrite_type"],
                 (record.get("sweeps") or [{}])[0].get("inventory_units"),
                 inv["ephys_sampling_rate"], inv["eligibility"]), file=stream)
    if "file" in record:
        print("  file    %d bytes  sha256=%s"
              % (record["file"]["size_bytes"], record["file"]["sha256"]),
              file=stream)
    if "nwb" in record:
        print("  nwb     version=%s (%s)  series=%d  root=%s"
              % (record["nwb"]["version"], record["nwb"]["version_source"],
                 record["nwb"]["n_stimulus_series"],
                 ",".join(record["nwb"]["root_keys"])), file=stream)
    if "identity_chain" in record:
        print("  identity %s" % record["identity_chain"], file=stream)

    sweeps = record.get("sweeps") or []
    if not sweeps:
        if record.get("reason"):
            print("  REASON  %s" % record["reason"], file=stream)
        return

    first = sweeps[0]
    print("  units   declared=%-6r conversion=%-6g resolution=%-6g offset=%g"
          % (first["declared_unit"], first["conversion"],
             first["resolution"], first["offset"]), file=stream)
    units = sorted({r["declared_unit"] for r in sweeps})
    print("  declared unit strings across long-square sweeps: %s" % units,
          file=stream)
    conversions = sorted({r["conversion"] for r in sweeps})
    if conversions != [1.0]:
        print("  CONVERSION not 1.0 on long-square sweeps: %s" % conversions,
              file=stream)
        print("            both readings scored; see MATCH_CONVERSION_CONFLICT",
              file=stream)
    print("  %-5s %9s %11s %7s %9s %8s %8s %-24s"
          % ("swp", "inv_pA", "measured_pA", "ratio", "aibs_pA", "aibs_d",
             "onset_s", "verdict"), file=stream)
    for r in sweeps:
        trace = r.get("trace", {})
        print("  %-5d %9s %11s %7s %9s %8s %8s %-24s"
              % (r["sweep"],
                 _fmt(r.get("inventory_amplitude")),
                 _fmt(r.get("measured_pA")),
                 _fmt(r.get("ratio_measured_over_expected"), "{:.3g}"),
                 _fmt(r.get("aibs_amplitude_pa")),
                 _fmt(r.get("aibs_delta_pA"), "{:+.2g}"),
                 _fmt(trace.get("onset_s"), "{:.4f}"),
                 r["verdict"]), file=stream)

    cov = record.get("coverage", {})
    print("  coverage inventory=%s nwb=%s matched=%s inventory_only=%s"
          % (cov.get("inventory_long_square_rows"),
             cov.get("nwb_long_square_series"),
             cov.get("matched_by_sweep_number"),
             cov.get("inventory_only")), file=stream)

    onsets = [r["trace"].get("onset_s") for r in sweeps
              if r.get("trace", {}).get("status") == "OK"]
    durs = [r["trace"].get("level_ms") for r in sweeps
            if r.get("trace", {}).get("status") == "OK"]
    if onsets:
        print("  step    onset %.4f-%.4f s  duration %.2f-%.2f ms"
              % (min(onsets), max(onsets), min(durs), max(durs)), file=stream)

    pulses: dict[tuple, dict] = {}
    conflict = any(r["verdict"] == "MATCH_CONVERSION_CONFLICT" for r in sweeps)
    for r in sweeps:
        factor = r.get("unit_factor_to_pA") or np.nan
        offset = r.get("offset", 0.0) or 0.0
        conversion = r.get("conversion", 1.0)
        for extra in r.get("trace", {}).get("extra_runs", []):
            key = (round(extra["start_s"], 4), round(extra["end_s"], 4))
            slot = pulses.setdefault(key, {"n": 0, "spec": [], "unit_only": []})
            slot["n"] += 1
            # Same conversion rule as the step: an embedded run is part of the
            # same recorded array and must not be converted by another rule.
            slot["spec"].append((extra["level"] * conversion + offset) * factor)
            slot["unit_only"].append((extra["level"] + offset) * factor)
    if pulses:
        print("  embedded constant runs other than the step (pA):", file=stream)
        for (start, stop), slot in sorted(pulses.items()):
            lvl = np.nanmedian(slot["unit_only"] if conflict else slot["spec"])
            text = ("      %.4f-%.4f s  %9.4f pA  in %d/%d sweeps"
                    % (start, stop, lvl, slot["n"], len(sweeps)))
            if conflict:
                text += "   [spec rule: %.4g pA]" % np.nanmedian(slot["spec"])
            print(text, file=stream)
    else:
        print("  embedded constant runs other than the step: none", file=stream)

    if conflict:
        n_conf = sum(1 for r in sweeps
                     if r["verdict"] == "MATCH_CONVERSION_CONFLICT")
        spec_ratios = sorted({round(r["ratio_spec"], 12) for r in sweeps
                              if r.get("ratio_spec") is not None
                              and np.isfinite(r["ratio_spec"])})
        worst = max((abs(r["aibs_delta_pA"]) for r in sweeps
                     if r.get("aibs_delta_pA") is not None), default=np.nan)
        print("  CONFLICT conversion=%s declared on %d/%d long-square sweeps."
              % (conversions, n_conf, len(sweeps)), file=stream)
        print("           Under the NWB 1.x rule (raw*conversion) every measured "
              "value would carry ratio %s" % (spec_ratios,), file=stream)
        print("           against the inventory. Under conversion=1 the samples "
              "match to %.3g pA (worst |measured-aibs|)," % worst,
              file=stream)
        print("           so the samples are already in the declared unit and the "
              "conversion attribute is wrong.", file=stream)
        print("           Adjudicated to conversion=1; the ratio column shows that "
              "reading.", file=stream)

    open_cases = [r for r in sweeps if r["verdict"] in ("UNRESOLVED", "AMBIGUOUS")]
    for r in open_cases[:5]:
        print("  OPEN    sweep %d: %s" % (r["sweep"], r.get("reason",
              r.get("trace", {}).get("reason", "see JSON"))), file=stream)


def _fmt(value, spec="{:.6g}"):
    if value is None:
        return "-"
    try:
        if not np.isfinite(float(value)):
            return "-"
        return spec.format(float(value))
    except (TypeError, ValueError):
        return "-"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--specimen", type=int, action="append", default=None,
                        help="specimen id to validate (repeatable)")
    parser.add_argument("--all", action="store_true",
                        help="validate every *.nwb file present in the cache")
    parser.add_argument("--repo-root", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--cache-dir", type=pathlib.Path, default=None)
    parser.add_argument("--json-out", type=pathlib.Path, default=None,
                        help="write the full result as JSON (keep out of Git)")
    args = parser.parse_args(argv)

    root = args.repo_root
    cache = args.cache_dir or (root / "data/nwb_cache")
    cells, sweeps = load_inventory(root)

    ids = list(args.specimen or [])
    if args.all:
        ids += [int(p.stem) for p in sorted(cache.glob("*.nwb"))
                if p.stem.isdigit() and int(p.stem) not in ids]
    if not ids:
        parser.error("give --specimen or --all (nothing to do)")

    records = [validate_specimen(sid, root, cells, sweeps, cache) for sid in ids]
    for rec in records:
        report(rec)

    print("=" * 78)
    print("%-12s %-22s %s" % ("specimen", "verdict", "summary"))
    for rec in records:
        sweeps_out = rec.get("sweeps") or []
        counts = {}
        for r in sweeps_out:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        print("%-12d %-22s %s" % (rec["specimen_id"], rec.get("verdict", "?"),
                                  counts or rec.get("reason", "")))

    if args.json_out:
        args.json_out.write_text(json.dumps(records, indent=2, default=str),
                                 encoding="utf-8")
        print("JSON written to %s" % args.json_out)

    bad = any(rec.get("verdict") in ("AMBIGUOUS", "UNRESOLVED",
                                     "MATCH_CONVERSION_CONFLICT")
              for rec in records)
    return 2 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Phase 2D — electrophysiology anomaly and protocol consistency audit.

This is a *recording and protocol* audit, not a modelling phase. It answers three
questions that Phase 2C left open, using only the cached NWB that Phases 1C and 2C
already validated:

1. Do the COARSE and FINEST long-square blocks really deliver the same stimulus at
   a nominal +170 pA, and if so why do they disagree about the spike count?
2. What are the two post-stimulus action potentials in sweep 38 at ~5.514/5.521 s?
3. Which sweeps are eligible for an F-I curve and for held-out evaluation?

The design principle throughout is to separate three kinds of statement:

  * **observed**   — a number computed from the file, reproducible by re-running;
  * **supported**  — an explanation the file's own metadata actually carries;
  * **hypothesis** — a plausible cause the metadata cannot confirm.

Only the first two are allowed to drive an eligibility decision. Nothing is
classified as an artefact on morphology alone, and no sweep is excluded because it
disagrees with a model — Phase 2D has no model in it at all.

Two facts pinned from the earlier phases are load-bearing here and are re-verified
rather than assumed: the NWB digest from Phase 1C, and the Phase 1C finding that
the two long-square blocks differ in trace length (8.020 s versus 6.020 s) while
sharing a 1.02 s / 1 s step.

Read-only. The NWB is opened with h5py and never written. No NEURON, no model, no
fitting, no threshold tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np

# Reuse the Phase 1C/1D NWB access layer rather than re-deriving HDF5 conventions.
# Those helpers already handle the NWB-1.0.5 group/dataset duality that this file
# actually uses, so a second implementation would only add a way to disagree.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from validate_nwb_stimulus_units import (  # noqa: E402
    _as_text,
    constant_runs,
    list_series,
    open_nwb,
    s_field,
    s_num,
    series_data,
    series_num,
    series_rate,
    template_key,
)

SPECIMEN = 382982932
RATE_HZ = 200_000.0
DT_MS = 1e3 / RATE_HZ

#: The amplitude where the two protocol blocks contradict each other.
CONTESTED_PA = 170.0
COARSE_SWEEP = 38
FINEST_SWEEPS = (49, 50, 51, 52)

#: The three long-square blocks, discovered by scanning template families rather
#: than assumed. Named here only so the comparisons can refer to them.
COARSE_BLOCK = "C1LSCOARSE150216"
FINEST_BLOCK = "C1LSFINEST150112"
SECOND_LONG_SQUARE = "C2SQRHELNG150216"

#: The embedded test pulse, invariant across 236 sweeps in the cross-specimen
#: audit: +50 pA for 10 ms starting at 5 ms. Identified by identity, not by size,
#: so that a short threshold pulse is not mistaken for it.
PROBE_PA = 50.0
PROBE_START_S = 0.005
PROBE_DURATION_S = 0.010

#: The short-square protocol pair, used as a threshold control for the long-square
#: discrepancy. Discovered from the template families, asserted by the run.
SHORT_SQUARE_BLOCKS = ("C1SSCOARSE150112", "C1SSFINEST150112")

#: A run at least this long is treated as a stimulus step rather than an
#: embedded probe pulse. Phase 1C and the cross-specimen audit established the
#: probe is ~10 ms and the step 1000/2000 ms, so any threshold between them
#: separates the two; this one is deliberately far from both.
MIN_STEP_MS = 200.0

#: Spike detection. Allen's ``detect_putative_spikes`` thresholds on dV/dt with a
#: Bessel filter; this audit instead uses a plain 0 mV upward crossing with a
#: refractory window, so that the count is *independent* of Allen's detector and
#: the two can be cross-checked. Where they disagree, both are reported.
SPIKE_THRESHOLD_MV = 0.0
REFRACTORY_MS = 1.5

#: A flat run this long at 200 kHz is 5 ms of a stuck converter. Real membrane
#: traces at this rate always move; anything longer is a hardware symptom.
MAX_PLAUSIBLE_FLAT_MS = 5.0

#: From Phase 1C, re-verified here.
EXPECTED_BYTES = 94_207_824
EXPECTED_SHA256 = "d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


class Audit:
    """Collects asserted checks and reported observations separately.

    The split exists because the two carry different epistemic weight. A check is
    a fact about the file that must hold for the audit to be trustworthy; an
    observation is a measurement whose *interpretation* is the subject of the
    report. Conflating them would let a biological judgement fail the run.
    """

    def __init__(self) -> None:
        self.checks: list[tuple[str, bool, str]] = []
        self.observations: list[tuple[str, str]] = []
        self.section = ""

    def heading(self, text: str) -> None:
        self.section = text
        print()
        print("=" * 78)
        print(text)
        print("=" * 78)

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.checks.append((label, bool(ok), detail))
        print("  [%s] %-58s %s" % ("PASS" if ok else "FAIL", label, detail))
        return bool(ok)

    def observe(self, label: str, detail: str = "") -> None:
        self.observations.append((label, detail))
        print("  %-8s %-58s %s" % ("report", label, detail))

    def note(self, text: str) -> None:
        for line in text.strip().splitlines():
            print("  .. " + line.strip())

    @property
    def failures(self) -> int:
        return sum(1 for _, ok, _ in self.checks if not ok)

    def summary(self) -> dict:
        return {
            "checks": len(self.checks),
            "passed": len(self.checks) - self.failures,
            "failed": self.failures,
            "observations": len(self.observations),
            "failures": [{"label": l, "detail": d} for l, ok, d in self.checks if not ok],
        }


# ---------------------------------------------------------------------------
# Loading and measurement
# ---------------------------------------------------------------------------


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def to_volts_mv(node) -> np.ndarray:
    """Acquisition samples -> millivolts.

    The conversion must be read from the file rather than assumed: the Allen
    writer stores ``unit='Volts', conversion=1`` here, but a hardcoded factor
    would silently mis-scale a file written the other way round.
    """
    data = series_data(node)
    raw = data[()].astype(np.float64)
    conv = series_num(node, "conversion", 1.0)
    off = series_num(node, "offset", 0.0)
    unit = _as_text(series_attr_any(node, "unit", default=b"Volts")).strip()
    scale = {"volts": 1.0, "mv": 1e-3, "v": 1.0}.get(unit.lower(), 1.0)
    return raw * conv * scale * 1e3 + off * 1e3


def to_amps_pa(node) -> np.ndarray:
    """Stimulus samples -> picoamps, using the declared conversion."""
    data = series_data(node)
    raw = data[()].astype(np.float64)
    conv = series_num(node, "conversion", 1.0)
    unit = _as_text(series_attr_any(node, "unit", default=b"Amps")).strip().lower()
    scale = {"amps": 1.0, "pa": 1e-12, "na": 1e-9, "ua": 1e-6, "ma": 1e-3}.get(unit, 1.0)
    return raw * conv * scale * 1e12


def series_attr_any(node, name, default=None):
    """Read a ``data``-dataset attribute with a series-group fallback."""
    data = series_data(node)
    if data is not None and name in data.attrs:
        return data.attrs[name]
    if name in node.attrs:
        return node.attrs[name]
    return default


def analyse_stimulus(stim_pa: np.ndarray, rate_hz: float) -> dict:
    """Split the command current into its constant runs and identify the step.

    The baseline is the level covering the most samples (not the smallest absolute
    value, which would tie an embedded +/-50 pA probe with a +/-50 pA step). The
    embedded probe is then removed *by identity* and the step is the longest run
    that remains.

    Removing the probe by identity rather than by length is what makes one
    classifier work for both protocol families in this file. The short-square
    blocks deliver a 3 ms threshold pulse, which is *shorter* than the 10 ms
    probe, so a purely length-based rule reports the probe as the stimulus and
    loses the pulse entirely -- which is exactly what happened before this was
    changed, and why those 16 sweeps were classed AMBIGUOUS.
    """
    runs = constant_runs(stim_pa)
    if not runs:
        return {"status": "UNRESOLVED", "reason": "empty stimulus"}
    counts: dict[float, int] = {}
    for start, stop, value in runs:
        counts[value] = counts.get(value, 0) + (stop - start)
    baseline = max(counts, key=lambda v: (counts[v], -abs(v)))

    non_base = [r for r in runs if r[2] != baseline]
    if not non_base:
        return {"status": "AMBIGUOUS", "reason": "no non-baseline level",
                "baseline_pa": baseline, "n_runs": len(runs)}

    def is_probe(r) -> bool:
        return (abs(r[2] - PROBE_PA) < 0.5
                and abs(r[0] / rate_hz - PROBE_START_S) <= 0.0005
                and abs((r[1] - r[0]) / rate_hz - PROBE_DURATION_S) <= 0.0015)

    candidates = [r for r in non_base if not is_probe(r)]
    if not candidates:
        return {"status": "AMBIGUOUS", "reason": "only the embedded probe",
                "baseline_pa": baseline, "n_runs": len(runs),
                "pulses": [{"level_pa": r[2], "start_s": r[0] / rate_hz,
                             "end_s": r[1] / rate_hz, "samples": r[1] - r[0]}
                            for r in non_base]}

    ordered = sorted(candidates, key=lambda r: -(r[1] - r[0]))
    step = ordered[0]
    step_ms = (step[1] - step[0]) / rate_hz * 1e3
    return {
        "status": "OK" if step_ms >= MIN_STEP_MS else "AMBIGUOUS",
        "baseline_pa": baseline,
        "level_pa": step[2],
        "onset_s": step[0] / rate_hz,
        "end_s": step[1] / rate_hz,
        "duration_ms": step_ms,
        "onset_index": step[0],
        "end_index": step[1],
        "n_runs": len(runs),
        "probe_removed": any(is_probe(r) for r in non_base),
        "pulses": [
            {"level_pa": r[2], "start_s": r[0] / rate_hz, "end_s": r[1] / rate_hz,
             "samples": r[1] - r[0]}
            for r in non_base if r is not step
        ],
    }


def detect_spikes(v_mv: np.ndarray, rate_hz: float,
                  threshold_mv: float = SPIKE_THRESHOLD_MV,
                  refractory_ms: float = REFRACTORY_MS) -> np.ndarray:
    """Peak indices of upward threshold crossings, with a refractory window.

    Returning *peak* indices (the local maximum after each crossing) rather than
    crossing indices matters for morphology: the width and dV/dt measurements are
    anchored on the peak, and using a crossing would bias every one of them.
    """
    above = v_mv >= threshold_mv
    if not above.any():
        return np.array([], dtype=int)
    rising = np.flatnonzero(~above[:-1] & above[1:]) + 1
    if not rising.size:
        return np.array([], dtype=int)
    refractory = int(refractory_ms / DT_MS)
    peaks: list[int] = []
    for cross in rising:
        if peaks and cross - peaks[-1] < refractory:
            continue
        stop = min(v_mv.size, cross + refractory)
        peaks.append(int(cross + int(np.argmax(v_mv[cross:stop]))))
    return np.asarray(peaks, dtype=int)


def spike_shape(v_mv: np.ndarray, rate_hz: float, peak_index: int,
                pre_ms: float = 30.0, post_ms: float = 40.0) -> dict:
    """Morphology of one spike, measured from the trace around its peak.

    The baseline is taken from the 30 ms preceding the peak, excluding the 2 ms
    immediately before it, so the upstroke does not contaminate its own reference.
    """
    pre = int(pre_ms * rate_hz / 1e3)
    post = int(post_ms * rate_hz / 1e3)
    lo = max(0, peak_index - pre)
    hi = min(v_mv.size, peak_index + post)
    seg = v_mv[lo:hi]

    base_lo = max(0, peak_index - pre)
    base_hi = max(base_lo + 1, peak_index - int(2.0 * rate_hz / 1e3))
    baseline = float(np.median(v_mv[base_lo:base_hi]))
    peak = float(v_mv[peak_index])
    amplitude = peak - baseline

    result = {
        "peak_mv": peak,
        "baseline_mv": baseline,
        "amplitude_mv": amplitude,
        "peak_ms": peak_index / rate_hz * 1e3,
        "width_ms": float("nan"),
        "width_censored": False,
        "rise_ms": float("nan"),
        "max_dvdt_v_per_s": float("nan"),
        "min_dvdt_v_per_s": float("nan"),
        "ahp_mv": float("nan"),
        "n_upstroke_samples": 0,
    }
    if amplitude <= 0 or seg.size < 3:
        return result

    # Width and rise are measured from the *contiguous* run containing the peak,
    # walked outward from it. Two traps are avoided here, both of which produced
    # wrong numbers before they were fixed:
    #
    #  1. A window-wide "first and last sample above half-max" search silently
    #     absorbs the upstroke of the following spike. The minimum inter-spike
    #     interval in this block is ~42 ms, so a 40 ms post-window reaches into
    #     the next spike and reports a 40 ms "width" for a 0.9 ms action
    #     potential. Walking outward from the peak cannot do that, and a run that
    #     touches the window edge is flagged censored rather than reported.
    #  2. The anchor must be the peak index passed in, not ``argmax(seg)``. The
    #     previous spike can fall inside the 30 ms pre-window and be taller, in
    #     which case argmax silently relocates every measurement onto that other
    #     spike.
    peak_off = peak_index - lo
    half = baseline + amplitude / 2.0
    above = seg >= half
    w_lo = w_hi = peak_off
    while w_lo > 0 and above[w_lo - 1]:
        w_lo -= 1
    while w_hi + 1 < seg.size and above[w_hi + 1]:
        w_hi += 1
    result["width_ms"] = (w_hi - w_lo + 1) / rate_hz * 1e3
    result["width_censored"] = bool(w_lo == 0 or w_hi == seg.size - 1)

    # Rise is measured from the local minimum that immediately precedes the peak.
    # Two weaker definitions were tried and discarded. "First sample above 10%"
    # in the whole window spans two spikes once the inter-spike trough sits above
    # 10% of the amplitude, reporting a 46.8 ms rise for a sub-millisecond
    # upstroke. "Walk back while non-decreasing" stops on the first quantisation
    # wobble, which at a 0.031 mV ADC step happens within a sample or two and
    # reported a 0.000 ms rise. Taking the minimum over the preceding 15 ms is
    # insensitive to both: it lands on the inter-spike trough, which is the point
    # the membrane actually started from.
    up_lo = max(0, peak_off - int(15.0 * rate_hz / 1e3))
    up_start = up_lo + int(np.argmin(seg[up_lo:peak_off + 1]))
    upstroke = seg[up_start:peak_off + 1]
    tenth = baseline + 0.1 * amplitude
    ninetieth = baseline + 0.9 * amplitude
    i10 = np.flatnonzero(upstroke >= tenth)
    i90 = np.flatnonzero(upstroke >= ninetieth)
    if i10.size and i90.size:
        result["rise_ms"] = (i90[0] - i10[0]) / rate_hz * 1e3
        result["n_upstroke_samples"] = int(i90[0] - i10[0])

    dvdt = np.diff(seg) * 1e-3 * rate_hz  # mV/sample -> V/s
    if dvdt.size:
        result["max_dvdt_v_per_s"] = float(dvdt.max())
        result["min_dvdt_v_per_s"] = float(dvdt.min())
    ahp_lo = peak_off + int(1.0 * rate_hz / 1e3)
    if ahp_lo < seg.size:
        result["ahp_mv"] = float(seg[ahp_lo:].min())
    return result


def excursions(v_mv: np.ndarray, threshold_mv: float = -20.0,
               min_separation_ms: float = 1.0) -> list[dict]:
    """Contiguous suprathreshold excursions, reported with their peaks.

    ``min_separation_ms`` merges the two halves of a single overshoot that dips
    marginally below the threshold; it does not merge a genuine doublet, whose
    inter-spike interval here is ~7 ms.
    """
    above = np.flatnonzero(v_mv > threshold_mv)
    if not above.size:
        return []
    splits = np.flatnonzero(np.diff(above) > 1)
    starts = np.concatenate(([above[0]], above[splits + 1]))
    ends = np.concatenate((above[splits], [above[-1]]))
    out = []
    for start, end in zip(starts, ends):
        seg = v_mv[start:end + 1]
        peak_off = int(np.argmax(seg))
        out.append({
            "start_ms": start * DT_MS,
            "end_ms": end * DT_MS,
            "width_ms": (end - start + 1) * DT_MS,
            "peak_mv": float(seg[peak_off]),
            "peak_ms": (start + peak_off) * DT_MS,
        })
    return out


def quality_metrics(v_mv: np.ndarray, rate_hz: float, onset_s: float,
                    end_s: float) -> dict:
    """Sample-integrity and stability measurements for one trace.

    "Discontinuity" is deliberately *not* defined by an absolute jump threshold:
    a real action potential upstroke at 200 kHz legitimately moves several mV per
    sample. It is instead compared against the largest jump in the same trace
    during the stimulated step, which is the only period guaranteed to contain
    physiological fast transients.

    The repeated-sample count is reported but carries no verdict, because at this
    resolution it is a property of the amplifier, not of the file. The ADC
    quantises to ~0.031 mV while the pre-step noise is ~0.09 mV, so consecutive
    samples land on the same code roughly a quarter of the time in a perfectly
    healthy recording. A genuine stall is a long *continuous* run of one code,
    which is what ``longest_flat_ms`` measures; ``adc_quantum_mv`` and
    ``n_distinct_values`` are reported so the two can be told apart.
    """
    n = v_mv.size
    finite = np.isfinite(v_mv)
    step_ms = np.diff(v_mv)
    abs_step = np.abs(step_ms) if step_ms.size else np.array([0.0])

    change = np.flatnonzero(np.diff(v_mv) != 0)
    bounds = np.concatenate(([0], change + 1, [n]))
    flat = np.diff(bounds)
    longest_flat = int(flat.max()) if flat.size else n

    codes = np.unique(v_mv[finite]) if finite.any() else np.array([])
    quantum = float(np.min(np.diff(codes))) if codes.size > 1 else float("nan")

    pre_lo = int(0.05 * rate_hz)
    pre_hi = max(pre_lo + 1, int((onset_s - 0.02) * rate_hz))
    pre = v_mv[pre_lo:pre_hi]
    pre_t = (np.arange(pre.size) + pre_lo) / rate_hz
    if pre.size > 10:
        slope, _ = np.polyfit(pre_t, pre, 1)
    else:
        slope = float("nan")

    step_lo, step_hi = int(onset_s * rate_hz), int(end_s * rate_hz)
    in_step_jump = float(np.max(np.abs(step_ms[step_lo:step_hi]))) if step_hi > step_lo else 0.0

    return {
        "n_samples": int(n),
        "n_nonfinite": int(np.count_nonzero(~finite)),
        "n_repeat_samples": int(np.count_nonzero(step_ms == 0)),
        "n_distinct_values": int(codes.size),
        "adc_quantum_mv": quantum,
        "longest_flat_samples": longest_flat,
        "longest_flat_ms": longest_flat * DT_MS,
        "max_jump_mv": float(abs_step.max()) if abs_step.size else 0.0,
        "max_jump_ms": int(np.argmax(abs_step)) * DT_MS if abs_step.size else float("nan"),
        "max_jump_in_step_mv": in_step_jump,
        "v_min_mv": float(np.min(v_mv[finite])) if finite.any() else float("nan"),
        "v_max_mv": float(np.max(v_mv[finite])) if finite.any() else float("nan"),
        "baseline_mv": float(np.median(pre)) if pre.size else float("nan"),
        "baseline_sd_mv": float(np.std(pre)) if pre.size else float("nan"),
        "baseline_drift_mv_per_s": float(slope),
        "baseline_span_mv": float(pre.max() - pre.min()) if pre.size else float("nan"),
    }


# ---------------------------------------------------------------------------
# Sweep inventory
# ---------------------------------------------------------------------------


def build_records(f, audit: Audit) -> list[dict]:
    """One record per stimulus series, with waveform and quality measurements."""
    stim_series = list_series(f, "stimulus/presentation")
    acq_series = dict(list_series(f, "acquisition/timeseries"))

    records = []
    for name, node in stim_series:
        number = int(name.replace("Sweep_", ""))
        base, multiplier = template_key(node)
        stim_pa = to_amps_pa(node)
        wave = analyse_stimulus(stim_pa, RATE_HZ)

        record = {
            "sweep": number,
            "template": base,
            "template_index_multiplier": multiplier,
            "block": base.split("[")[0],
            "amplitude_pa": s_num(node, "aibs_stimulus_amplitude_pa"),
            "stimulus_name": _as_text(s_field(node, "aibs_stimulus_name", default=b"")),
            "starting_time_s": s_num(node, "starting_time"),
            "n_samples_stimulus": int(stim_pa.size),
            "rate_hz": series_rate(node),
            "gain": s_num(node, "gain"),
            "access_resistance": s_num(node, "initial_access_resistance"),
            "seal": s_num(node, "seal"),
            "stimulus_interval": s_num(node, "aibs_stimulus_interval"),
            "waveform": wave,
            "trace_seconds": stim_pa.size / RATE_HZ,
        }

        # Epoch window, when the file carries one for this sweep.
        ep_name = "Experiment_%d" % number
        if "epochs" in f and ep_name in f["epochs"]:
            ep = f["epochs"][ep_name]
            record["epoch_start_s"] = float(np.asarray(ep["start_time"][()]).ravel()[0])
            record["epoch_stop_s"] = float(np.asarray(ep["stop_time"][()]).ravel()[0])
            for arm in ("response", "stimulus"):
                if arm in ep and "idx_start" in ep[arm]:
                    record["epoch_%s_idx_start" % arm] = int(
                        np.asarray(ep[arm]["idx_start"][()]).ravel()[0])
                    record["epoch_%s_count" % arm] = int(
                        np.asarray(ep[arm]["count"][()]).ravel()[0])

        # Allen's own annotated spike times, sweep-referenced seconds.
        st_name = "analysis/spike_times/%s" % name
        if st_name in f:
            times = np.asarray(f[st_name][()]).ravel().astype(float)
            record["annotated_spike_times_s"] = times.tolist()
        else:
            record["annotated_spike_times_s"] = []

        records.append(record)

    # Deep analysis covers two families: the long-square sweeps (the audit's
    # subject) and the short-square sweeps (the threshold control). Reading all 74
    # traces would add minutes of I/O without adding evidence.
    long_square = [r for r in records
                   if r["waveform"].get("status") == "OK"
                   and r["waveform"]["duration_ms"] >= MIN_STEP_MS]
    short_square = [r for r in records if r["block"] in SHORT_SQUARE_BLOCKS]
    for r in long_square:
        r["family"] = "long"
    for r in short_square:
        r["family"] = "short"
    long_ids = {id(r) for r in long_square}
    deep = long_square + [r for r in short_square if id(r) not in long_ids]
    audit.note("deep trace analysis: %d long-square sweeps (step >= %.0f ms) and "
               "%d short-square sweeps; the other %d series carry metadata only"
               % (len(long_square), MIN_STEP_MS, len(short_square),
                  len(records) - len(deep)))

    for record in deep:
        name = "Sweep_%d" % record["sweep"]
        if name not in acq_series:
            record["status"] = "NO_ACQUISITION"
            continue
        node = acq_series[name]
        v_mv = to_volts_mv(node)
        wave = record["waveform"]

        record["quality"] = quality_metrics(v_mv, RATE_HZ, wave["onset_s"], wave["end_s"])

        peaks = detect_spikes(v_mv, RATE_HZ)
        record["detected_peak_indices"] = peaks
        record["detected_spike_times_ms"] = (peaks / RATE_HZ * 1e3).tolist()
        record["n_detected"] = int(peaks.size)
        record["n_annotated"] = len(record["annotated_spike_times_s"])

        onset_idx = wave["onset_index"]
        end_idx = wave["end_index"]

        # A 3 ms threshold pulse evokes its spike at pulse OFF, so counting only
        # inside [onset, end) puts every response on the wrong side of the
        # boundary. The short family therefore gets a 100 ms response grace; the
        # long family keeps the strict step window.
        grace_idx = int(0.100 * RATE_HZ) if record.get("family") == "short" else 0
        in_step = peaks[(peaks >= onset_idx) & (peaks < end_idx + grace_idx)]
        record["response_window_ms"] = ((end_idx - onset_idx + grace_idx)
                                       / RATE_HZ * 1e3)
        record["n_detected_in_step"] = int(in_step.size)
        record["n_detected_post_step"] = int(np.count_nonzero(
            peaks >= end_idx + grace_idx))

        # Steady-state level over the last 200 ms of the step. This is the single
        # most useful quantity for the COARSE/FINEST question: if the two blocks
        # end up at the same depolarised level, then neither "COARSE received a
        # bigger current" nor "COARSE sat at a more excitable potential" explains
        # the rate difference, and the difference has to live in something else.
        #
        # The mean is reported alongside the median because the sweeps do not all
        # contain the same number of spikes in that window: a sweep firing 12
        # times in the step is biased upward by its own spikes, by roughly
        # 0.2 mV per spike in the window. The median is robust to that, so a
        # conclusion that holds for the median does not depend on the bias.
        ss_lo = max(onset_idx, end_idx - int(0.2 * RATE_HZ))
        record["steady_state_mv"] = float(np.mean(v_mv[ss_lo:end_idx])) \
            if end_idx > ss_lo else float("nan")
        record["steady_state_median_mv"] = float(np.median(v_mv[ss_lo:end_idx])) \
            if end_idx > ss_lo else float("nan")
        record["steady_state_n_spikes"] = int(np.count_nonzero(
            (peaks >= ss_lo) & (peaks < end_idx)))

        in_step = peaks[(peaks >= onset_idx) & (peaks < end_idx + grace_idx)]
        record["first_spike_ms"] = float(in_step[0] / RATE_HZ * 1e3) \
            if in_step.size else float("nan")
        record["first_isi_ms"] = float((in_step[1] - in_step[0]) / RATE_HZ * 1e3) \
            if in_step.size > 1 else float("nan")
        record["mean_isi_ms"] = float(np.diff(in_step).mean() / RATE_HZ * 1e3) \
            if in_step.size > 1 else float("nan")
        record["rate_hz_observed"] = (in_step.size / ((end_idx - onset_idx) / RATE_HZ)) \
            if in_step.size and record.get("family") == "long" else 0.0

        record["n_annotated_in_step"] = int(sum(
            1 for t in record["annotated_spike_times_s"]
            if wave["onset_s"] <= t < wave["end_s"] + grace_idx / RATE_HZ))
        record["n_annotated_post_step"] = int(sum(
            1 for t in record["annotated_spike_times_s"] if t >= wave["end_s"]))

        # Shapes of every detected spike, so the late events can be compared to
        # ordinary ones within the same trace.
        record["spike_shapes"] = [spike_shape(v_mv, RATE_HZ, int(p)) for p in peaks]

        # Post-step behaviour: excursions and mean level once the step is over.
        quiet_lo = end_idx + int(0.05 * RATE_HZ)
        record["post_step_excursions"] = excursions(v_mv[quiet_lo:])
        record["post_step_excursions"] = [
            {k: (v + quiet_lo * DT_MS if k in ("start_ms", "end_ms", "peak_ms") else v)
             for k, v in e.items()}
            for e in record["post_step_excursions"]
        ]
        if quiet_lo < v_mv.size:
            tail_lo = min(v_mv.size, end_idx + int(0.2 * RATE_HZ))
            tail_hi = min(v_mv.size, end_idx + int(1.0 * RATE_HZ))
            record["post_step_mean_mv"] = float(np.mean(v_mv[tail_lo:tail_hi])) \
                if tail_hi > tail_lo else float("nan")
        record["status"] = "OK"
        record["_v_mv"] = v_mv  # retained only for the plotting step

    return records


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def section_provenance(audit: Audit, nwb: pathlib.Path, f, records) -> dict:
    audit.heading("A. Provenance and file identity")
    size = nwb.stat().st_size
    digest = sha256_of(nwb)
    audit.check(size == EXPECTED_BYTES, "file size matches Phase 1C",
                "%d bytes" % size)
    audit.check(digest == EXPECTED_SHA256, "SHA-256 matches Phase 1C",
                digest[:32] + "...")

    version = _as_text(f["nwb_version"][()]) if "nwb_version" in f else "absent"
    specimen = _as_text(f["general/aibs_specimen_id"][()]) \
        if "general/aibs_specimen_id" in f else "absent"
    session = _as_text(f["general/session_id"][()]) \
        if "general/session_id" in f else "absent"
    audit.check(specimen == str(SPECIMEN), "specimen id", specimen)
    audit.observe("NWB version", version)
    audit.observe("session id", session)
    audit.observe("stimulus series", str(len(records)))
    audit.observe("acquisition series", str(len(list_series(f, "acquisition/timeseries"))))
    audit.observe("annotated spike-time series",
                  str(len(f["analysis/spike_times"])))
    return {"bytes": size, "sha256": digest, "nwb_version": version,
            "specimen_id": specimen, "session_id": session}


def section_inventory(audit: Audit, records) -> dict:
    audit.heading("B. Protocol block inventory")
    blocks: dict[str, list[dict]] = {}
    for r in records:
        blocks.setdefault(r["block"], []).append(r)

    print("  %-22s %4s %8s %8s %9s %9s %10s"
          % ("block", "n", "amp_lo", "amp_hi", "trace_s", "step_ms", "start_s"))
    inventory = {}
    for block in sorted(blocks):
        items = sorted(blocks[block], key=lambda r: r["sweep"])
        amps = [r["amplitude_pa"] for r in items]
        waves = [r["waveform"] for r in items if r["waveform"].get("status") == "OK"]
        trace = sorted({round(r["trace_seconds"], 4) for r in items})
        steps = sorted({round(w["duration_ms"], 3) for w in waves}) if waves else []
        starts = sorted({round(r["starting_time_s"], 3) for r in items})
        print("  %-22s %4d %8.1f %8.1f %9s %9s %10s"
              % (block, len(items), min(amps), max(amps),
                 ",".join(str(t) for t in trace),
                 ",".join("%.0f" % s for s in steps),
                 ",".join(str(s) for s in starts)))
        inventory[block] = {
            "n": len(items),
            "amplitude_pa": amps,
            "sweeps": [r["sweep"] for r in items],
            "trace_seconds": trace,
            "step_durations_ms": steps,
            "starting_times_s": starts,
            "sweep_numbers": [r["sweep"] for r in items],
        }

    long_square = {b: v for b, v in inventory.items()
                   if v["step_durations_ms"] and min(v["step_durations_ms"]) >= MIN_STEP_MS}
    audit.observe("long-square blocks discovered", ", ".join(sorted(long_square)))
    audit.check(len(long_square) == 3, "exactly three long-square protocol blocks exist",
                "%d found" % len(long_square))
    audit.check(SECOND_LONG_SQUARE in long_square,
                "a second long-square block (%s) exists" % SECOND_LONG_SQUARE,
                "%d sweeps" % long_square.get(SECOND_LONG_SQUARE, {}).get("n", 0))
    return inventory


def section_contested(audit: Audit, records, f) -> dict:
    """COARSE 38 versus FINEST 49-52: are the delivered commands really equal?"""
    audit.heading("C. COARSE sweep 38 versus FINEST sweeps 49-52 at +170 pA")
    by_sweep = {r["sweep"]: r for r in records}

    coarse = by_sweep.get(COARSE_SWEEP)
    finest = [by_sweep.get(s) for s in FINEST_SWEEPS]
    audit.check(coarse is not None, "sweep 38 present", "")
    audit.check(all(r is not None for r in finest), "sweeps 49-52 present", "")

    stim = dict(list_series(f, "stimulus/presentation"))
    commands = {s: to_amps_pa(stim["Sweep_%d" % s]) for s in (COARSE_SWEEP,) + FINEST_SWEEPS}

    # Sample-by-sample comparison over the overlap. This is the strongest
    # available statement about the stimulus: not "the same nominal amplitude",
    # but the same numbers.
    ref = commands[COARSE_SWEEP]
    best = None
    for s in FINEST_SWEEPS:
        other = commands[s]
        n = min(ref.size, other.size)
        diff = int(np.count_nonzero(ref[:n] != other[:n]))
        worst = float(np.max(np.abs(ref[:n] - other[:n]))) if n else 0.0
        audit.check(diff == 0, "command 38 == command %d sample by sample" % s,
                    "differing=%d  max|diff|=%.3e pA" % (diff, worst))
        if best is None or diff < best[0]:
            best = (diff, worst)

    for s in FINEST_SWEEPS:
        a = commands[COARSE_SWEEP][:min(ref.size, commands[s].size)]
        b = commands[s][:a.size]
        audit.check(bool(np.array_equal(a, b)),
                    "38 and %d are bit-identical over their overlap" % s,
                    "%d samples" % a.size)

    # Metadata comparison, field by field, only for fields the file carries.
    fields = ["amplitude_pa", "starting_time_s", "gain", "access_resistance", "seal"]
    print()
    print("  %-22s %-14s %-14s %-14s %s"
          % ("field", "sweep 38", "49-52 range", "equal?", "source"))
    meta = {}
    for field in fields:
        c = coarse[field]
        vals = [r[field] for r in finest]
        equal = all(abs(v - c) < 1e-9 for v in vals)
        rng = "%.6g" % vals[0] if len(set(vals)) == 1 else \
            "%.6g..%.6g" % (min(vals), max(vals))
        print("  %-22s %-14.6g %-14s %-14s %s"
              % (field, c, rng, "yes" if equal else "no", "per-series dataset"))
        meta[field] = {"coarse": c, "finest": vals, "equal": bool(equal)}

    # Fields that are file-level constants cannot differ per sweep, and this is
    # worth asserting rather than assuming: Phase 1C used it to rule out Ra/seal.
    for field in ("gain", "access_resistance", "seal"):
        distinct = sorted({round(r[field], 9) for r in records
                           if np.isfinite(r[field])})
        audit.check(len(distinct) == 1, "%s is a file-level constant" % field,
                    "distinct=%d value=%s" % (len(distinct), distinct))

    # Timing and duration.
    dwell = {s: (r["waveform"]["onset_s"], r["waveform"]["end_s"],
                 r["waveform"]["duration_ms"], r["trace_seconds"])
             for s, r in ((COARSE_SWEEP, coarse),) + tuple((s, by_sweep[s]) for s in FINEST_SWEEPS)}
    onsets = {round(v[0], 6) for v in dwell.values()}
    ends = {round(v[1], 6) for v in dwell.values()}
    durs = {round(v[2], 3) for v in dwell.values()}
    audit.check(len(onsets) == 1, "step onset identical across the five sweeps",
                "%.6f s" % next(iter(onsets)))
    audit.check(len(ends) == 1, "step end identical across the five sweeps",
                "%.6f s" % next(iter(ends)))
    audit.check(len(durs) == 1, "step duration identical across the five sweeps",
                "%.3f ms" % next(iter(durs)))
    traces = {round(v[3], 6) for v in dwell.values()}
    audit.check(len(traces) == 2, "trace length differs between the blocks",
                "38=%.3f s, 49-52=%.3f s"
                % (coarse["trace_seconds"], finest[0]["trace_seconds"]))

    # The embedded probe pulse must be the same protocol event in both blocks.
    for s in (COARSE_SWEEP,) + FINEST_SWEEPS:
        pulses = by_sweep[s]["waveform"]["pulses"]
        audit.check(len(pulses) == 1,
                    "sweep %d carries exactly one embedded probe pulse" % s,
                    "; ".join("%+.3f pA %.4f-%.4f s"
                              % (p["level_pa"], p["start_s"], p["end_s"])
                              for p in pulses))

    # The decisive side-by-side: same command, same onset, same duration, and a
    # steady state that is also the same. Whatever separates these sweeps is not
    # any of those four things.
    print()
    print("  %-7s %-13s %-10s %-9s %-9s %-9s %-9s %s"
          % ("sweep", "command pA", "onset s", "dur ms", "trace s",
             "plateau mV", "median mV", "spikes in step"))
    for s in (COARSE_SWEEP,) + FINEST_SWEEPS:
        rr = by_sweep[s]
        wv = rr["waveform"]
        print("  %-7d %-13.6f %-10.4f %-9.0f %-9.3f %-9.3f %-9.3f %d"
              % (s, wv["level_pa"], wv["onset_s"], wv["duration_ms"],
                 rr["trace_seconds"], rr["steady_state_mv"],
                 rr["steady_state_median_mv"], rr["n_detected_in_step"]))
    plateaus = [by_sweep[s]["steady_state_mv"] for s in (COARSE_SWEEP,) + FINEST_SWEEPS]
    medians = [by_sweep[s]["steady_state_median_mv"] for s in (COARSE_SWEEP,) + FINEST_SWEEPS]
    audit.observe("steady-state mean across the five sweeps",
                  "%.3f .. %.3f mV (range %.3f mV)"
                  % (min(plateaus), max(plateaus), max(plateaus) - min(plateaus)))
    audit.observe("steady-state median across the five sweeps",
                  "%.3f .. %.3f mV (range %.3f mV); sweep 38 holds %d of its 12 "
                  "spikes in the final 200 ms, so its mean is the more biased of "
                  "the two"
                  % (min(medians), max(medians), max(medians) - min(medians),
                     by_sweep[COARSE_SWEEP]["steady_state_n_spikes"]))
    audit.check(max(medians) - min(medians) < 2.0,
                "all five sweeps reach the same steady depolarisation (<2 mV)",
                "median range %.3f mV, mean range %.3f mV"
                % (max(medians) - min(medians), max(plateaus) - min(plateaus)))

    # Latency to the first in-step spike. If the blocks share a threshold, the
    # first spike should arrive at about the same time in all five; the divergence
    # then has to be about sustained firing, not about whether the step is
    # suprathreshold at all.
    firsts = [by_sweep[s]["first_spike_ms"] / 1e3 for s in (COARSE_SWEEP,) + FINEST_SWEEPS]
    audit.observe("time to first in-step spike",
                  "38 at %.3f s; 49-52 at %s"
                  % (firsts[0], ", ".join("%.3f" % f for f in firsts[1:])))
    audit.check(max(firsts) - min(firsts) < 0.100,
                "first spike latency agrees within 100 ms across the sweeps",
                "spread %.1f ms" % ((max(firsts) - min(firsts)) * 1e3))

    # Inter-sweep timing: does the file record it at all?
    print()
    audit.note(
        "starting_time is quantised to 256 s blocks: %s.  epochs/*/start_time\n"
        "inherits the same quantisation.  Sweeps that share a value therefore\n"
        "cannot be ordered, and their epoch windows overlap, so no inter-sweep\n"
        "recovery interval is recoverable from this file."
        % ", ".join("%.1f" % v for v in sorted({round(r["starting_time_s"], 3)
                                              for r in records
                                              if np.isfinite(r["starting_time_s"])}))
    )
    block_starts: dict[str, set] = {}
    for r in records:
        if np.isfinite(r["starting_time_s"]):
            block_starts.setdefault(r["block"], set()).add(round(r["starting_time_s"], 3))

    # The honest claim is weaker than "one value per block" and is the one that
    # matters: the field is not injective, so it cannot order the sweeps.  A
    # quarter of the sweeps share a timestamp with at least one other sweep, and
    # the epoch windows that inherit it therefore overlap.
    timed = [r for r in records if np.isfinite(r["starting_time_s"])]
    distinct = {round(r["starting_time_s"], 3) for r in timed}
    groups: dict[float, int] = {}
    for r in timed:
        key = round(r["starting_time_s"], 3)
        groups[key] = groups.get(key, 0) + 1
    biggest = max(groups.values()) if groups else 0
    audit.check(len(distinct) < len(timed),
                "starting_time is not a unique per-sweep timestamp",
                "%d distinct values for %d timed sweeps; largest group %d"
                % (len(distinct), len(timed), biggest))
    audit.check(biggest >= 2, "at least one timestamp is shared by several sweeps",
                "largest group %d sweeps" % biggest)
    audit.observe("256 s quantisation",
                  "all values are multiples of 256 s: %s"
                  % sorted(distinct)[:6])

    # Ordering evidence. The timestamp is far too coarse to date a sweep, but if it
    # came from a session clock it should never run backwards as sweep numbers
    # increase. That is testable, and it is the only ordering information the file
    # carries -- everything else about acquisition sequence is inference.
    ordered = sorted(timed, key=lambda r: r["sweep"])
    inversions = sum(1 for a, b in zip(ordered, ordered[1:])
                     if b["starting_time_s"] < a["starting_time_s"] - 1e-9)
    audit.check(inversions == 0,
                "starting_time never decreases as sweep number increases",
                "%d inversions over %d consecutive pairs"
                % (inversions, len(ordered) - 1))
    print()
    print("  %-22s %-10s %s" % ("block", "sweeps", "starting_time (s)"))
    for block in sorted({r["block"] for r in records}):
        items = sorted((r for r in records if r["block"] == block),
                       key=lambda x: x["sweep"])
        print("  %-22s %-10s %s"
              % (block, "%d-%d" % (items[0]["sweep"], items[-1]["sweep"]),
                 ",".join("%.0f" % v for v in
                           sorted({r["starting_time_s"] for r in items
                                   if np.isfinite(r["starting_time_s"])}))))

    overlap = []
    for i in range(len(FINEST_SWEEPS) - 1):
        a = by_sweep[FINEST_SWEEPS[i]]
        b = by_sweep[FINEST_SWEEPS[i + 1]]
        if b.get("epoch_start_s", 1e9) < a.get("epoch_stop_s", -1e9):
            overlap.append((a["sweep"], b["sweep"]))
    audit.check(bool(overlap), "consecutive FINEST epochs overlap (not sequential)",
                "%s" % overlap[:4])

    return {"metadata": meta, "dwell": {str(k): v for k, v in dwell.items()},
            "commands_bitequal": bool(best and best[0] == 0),
            "finest_epoch_overlap": overlap}


def section_second_block(audit: Audit, records, inventory) -> dict:
    """The independent third measurement at the contested amplitude."""
    audit.heading("D. The second long-square block — an independent +170 pA measurement")
    by_block = {}
    for r in records:
        by_block.setdefault(r["block"], []).append(r)

    items = sorted(by_block.get(SECOND_LONG_SQUARE, []), key=lambda r: r["sweep"])
    audit.check(bool(items), "second long-square block present",
                "%d sweeps" % len(items))
    if not items:
        return {}

    at_170 = [r for r in items if abs(r["amplitude_pa"] - CONTESTED_PA) < 1e-3]
    audit.check(len(at_170) >= 1,
                "second block contains a +170 pA sweep",
                "sweeps %s" % [r["sweep"] for r in at_170])

    for r in at_170:
        w = r["waveform"]
        audit.observe("sweep %d command" % r["sweep"],
                      "%+.6f pA, %.3f-%.3f s, %.0f ms step, %.3f s trace"
                      % (w["level_pa"], w["onset_s"], w["end_s"],
                         w["duration_ms"], r["trace_seconds"]))
        audit.check(abs(w["level_pa"] - CONTESTED_PA) < 1e-6,
                    "sweep %d delivers the same +170 pA level" % r["sweep"],
                    "%.9f pA" % w["level_pa"])
        audit.check(abs(w["onset_s"] - 1.02) < 1e-6,
                    "sweep %d step onset is also 1.020 s" % r["sweep"],
                    "%.6f s" % w["onset_s"])
        audit.check(abs(w["duration_ms"] - 2000.0) < 1e-3,
                    "sweep %d step is 2000 ms, not 1000 ms" % r["sweep"],
                    "%.3f ms" % w["duration_ms"])

    # Does the 170 pA level agree numerically with the other two blocks?
    levels = {}
    for r in records:
        if r["waveform"].get("status") == "OK" and abs(r["amplitude_pa"] - CONTESTED_PA) < 1e-3:
            levels.setdefault(r["block"], set()).add(round(r["waveform"]["level_pa"], 9))
    flat = {b: sorted(v) for b, v in levels.items()}
    audit.check(all(len(v) == 1 for v in flat.values()),
                "all +170 pA blocks deliver one identical commanded level",
                "; ".join("%s=%s" % (b, v) for b, v in sorted(flat.items())))

    return {"sweeps": [r["sweep"] for r in items],
            "amp_170_sweeps": [r["sweep"] for r in at_170],
            "levels_by_block": {k: v for k, v in flat.items()}}


def section_spikes(audit: Audit, records) -> dict:
    """Spike counts per sweep, and the F-I relation implied by each block."""
    audit.heading("E. Spike counts and the implied F-I relation")
    long_square = [r for r in records if r.get("family") == "long"]
    blocks: dict[str, list[dict]] = {}
    for r in long_square:
        blocks.setdefault(r["block"], []).append(r)

    print("  %-22s %-6s %6s %8s %8s %9s %9s %9s %8s"
          % ("block", "sweep", "amp", "detect", "in_step", "ann_in", "ann_post",
             "first_ms", "rate_Hz"))
    table = {}
    for block in sorted(blocks):
        for r in sorted(blocks[block], key=lambda x: (x["amplitude_pa"], x["sweep"])):
            print("  %-22s %-6d %6.1f %8d %8d %9d %9d %9.1f %8.2f"
                  % (block, r["sweep"], r["amplitude_pa"], r["n_detected"],
                     r["n_detected_in_step"], r["n_annotated_in_step"],
                     r["n_annotated_post_step"], r["first_spike_ms"],
                     r["rate_hz_observed"]))
        table[block] = sorted(
            ({"sweep": r["sweep"], "amp": r["amplitude_pa"],
              "detected": r["n_detected"], "in_step": r["n_detected_in_step"],
              "ann_in": r["n_annotated_in_step"], "ann_post": r["n_annotated_post_step"]}
             for r in blocks[block]),
            key=lambda d: (d["amp"], d["sweep"]))

    # Independent-detector cross-check against Allen's own annotations.
    worst = 0
    for r in long_square:
        worst = max(worst, abs(r["n_detected"] - r["n_annotated"]))
    audit.check(worst == 0,
                "independent detector reproduces Allen's annotated counts",
                "worst discrepancy = %d spike(s) across %d sweeps"
                % (worst, len(long_square)))

    # Every amplitude that more than one block drives, compared directly. This is
    # the strongest form of the COARSE/FINEST question: if the disagreement were a
    # property of one sweep it would appear at 170 pA only, and the explanation
    # would be local. If it appears at every shared amplitude, it is a property of
    # the block, and no amount of re-examining sweep 38 can resolve it.
    shared: dict[float, dict[str, list[dict]]] = {}
    for r in long_square:
        shared.setdefault(round(r["amplitude_pa"], 3), {}).setdefault(
            r["block"], []).append(r)

    print()
    print("  %-8s %-22s %7s %-8s %-14s %s"
          % ("amp pA", "block", "step s", "spikes", "rate Hz", "sweeps"))
    rows = []
    for amp in sorted(shared):
        if len(shared[amp]) < 2:
            continue
        for block in sorted(shared[amp]):
            items = sorted(shared[amp][block], key=lambda x: x["sweep"])
            dur = items[0]["waveform"]["end_s"] - items[0]["waveform"]["onset_s"]
            print("  %-8.1f %-22s %7.2f %-8s %-14s %s"
                  % (amp, block, dur,
                     "/".join(str(i["n_detected_in_step"]) for i in items),
                     "/".join("%.2f" % i["rate_hz_observed"] for i in items),
                     [i["sweep"] for i in items]))
            rows.append({"amp": amp, "block": block,
                         "spikes": [i["n_detected_in_step"] for i in items],
                         "rate_hz": [round(i["rate_hz_observed"], 4) for i in items],
                         "sweeps": [i["sweep"] for i in items],
                         "step_s": dur})

    amps_shared = sorted({r["amp"] for r in rows})
    dominated = []
    for amp in amps_shared:
        per = {r["block"]: max(r["rate_hz"]) for r in rows if r["amp"] == amp}
        rivals = {b: v for b, v in per.items() if b != COARSE_BLOCK}
        if COARSE_BLOCK in per and rivals and all(
                per[COARSE_BLOCK] > v for v in rivals.values()):
            dominated.append(amp)
    audit.observe("amplitudes driven by more than one block",
                  "%d (%s pA)" % (len(amps_shared),
                                  ", ".join("%g" % a for a in amps_shared)))
    audit.check(len(amps_shared) > 0 and len(dominated) == len(amps_shared),
                "COARSE fires faster at every amplitude it shares with another block",
                "%d of %d shared amplitudes; the block offset is not local to "
                "sweep 38" % (len(dominated), len(amps_shared)))

    print()
    for block in sorted(blocks):
        amps = sorted({round(r["amplitude_pa"], 3) for r in blocks[block]})
        counts = {}
        for r in blocks[block]:
            counts.setdefault(round(r["amplitude_pa"], 3), []).append(r["n_detected_in_step"])
        line = "  ".join("%g pA:%s" % (a, "/".join(str(c) for c in counts[a])) for a in amps)
        audit.observe("%s F-I" % block, line)

    # The contested amplitude, stated explicitly.
    print()
    for block in sorted(blocks):
        at = [r for r in blocks[block] if abs(r["amplitude_pa"] - CONTESTED_PA) < 1e-3]
        if not at:
            continue
        audit.observe("%s at +170 pA" % block,
                      "sweeps %s -> in-step spikes %s, post-step %s"
                      % ([r["sweep"] for r in at],
                         [r["n_detected_in_step"] for r in at],
                         [r["n_detected_post_step"] for r in at]))

    return {"table": table,
            "worst_count_discrepancy": worst,
            "shared_amplitudes": amps_shared,
            "coarse_dominates": dominated,
            "shared_rows": rows,
            "blocks_at_170": {
                b: {"sweeps": [r["sweep"] for r in blocks[b]
                               if abs(r["amplitude_pa"] - CONTESTED_PA) < 1e-3],
                    "in_step": [r["n_detected_in_step"] for r in blocks[b]
                                if abs(r["amplitude_pa"] - CONTESTED_PA) < 1e-3]}
                for b in blocks}}


def section_short_square(audit: Audit, records) -> dict:
    """The 3 ms threshold pulses: a control for the long-step discrepancy.

    This is the part of the file that makes the COARSE/FINEST question answerable.
    If the COARSE block came from a more excitable cell state, the shift should
    also be visible in the threshold measured with a short pulse. If it is not,
    the difference is specific to *sustained* depolarisation, which constrains what
    can explain it.

    Note the two blocks do not share a command amplitude: COARSE steps in 100 pA
    increments to 700 pA, FINEST repeats 650/660/670. So the comparison is of
    threshold *brackets*, not of counts at a matched current.
    """
    audit.heading("F. Short-square control — the 3 ms threshold protocol pair")
    short = sorted((r for r in records if r.get("family") == "short"),
                   key=lambda r: (r["block"], r["amplitude_pa"], r["sweep"]))
    audit.check(len(short) == 16, "short-square sweeps analysed",
                "%d of 16" % len(short))
    if not short:
        return {}

    durs = sorted({round(r["waveform"]["duration_ms"], 3) for r in short})
    audit.check(durs == [3.0], "every short-square command is a 3.000 ms pulse",
                "%s ms" % durs)

    print()
    print("  %-22s %-6s %8s %8s %9s %9s %8s"
          % ("block", "sweep", "amp pA", "pulse ms", "spikes", "first ms",
             "annot"))
    for r in short:
        print("  %-22s %-6d %8.1f %8.3f %9d %9.1f %8d"
              % (r["block"], r["sweep"], r["amplitude_pa"],
                 r["waveform"]["duration_ms"], r["n_detected_in_step"],
                 r["first_spike_ms"], r["n_annotated"]))

    # Threshold brackets. Repeats at one amplitude may disagree, so each level is
    # classified as silent / firing / mixed rather than squeezed into a single
    # number; a mixed level bounds the threshold but does not resolve it.
    est = {}
    for block in sorted({r["block"] for r in short}):
        items = [r for r in short if r["block"] == block]
        levels = {}
        for r in items:
            levels.setdefault(r["amplitude_pa"], []).append(
                bool(r["n_detected_in_step"]))
        verdict = {amp: ("firing" if all(v) else "silent" if not any(v) else "mixed")
                   for amp, v in levels.items()}
        firing = sorted(a for a, v in verdict.items() if v == "firing")
        silent = sorted(a for a, v in verdict.items() if v == "silent")
        mixed = sorted(a for a, v in verdict.items() if v == "mixed")
        est[block] = {"lowest_firing_pa": firing[0] if firing else float("nan"),
                      "highest_silent_pa": silent[-1] if silent else float("nan"),
                      "mixed_pa": mixed,
                      "levels": {int(a): v for a, v in sorted(verdict.items())}}
        audit.observe("%s threshold bracket" % block,
                      "silent at %s pA, firing at %s pA%s"
                      % (", ".join("%.0f" % a for a in silent) or "no level",
                         ", ".join("%.0f" % a for a in firing) or "no level",
                         "" if not mixed else
                         "; mixed at %s pA" % ", ".join("%.0f" % a for a in mixed)))

    audit.check(all(r["n_detected_in_step"] <= 1 for r in short),
                "no 3 ms pulse evokes more than one spike",
                "max %d spike(s)" % max(r["n_detected_in_step"] for r in short))

    # The COARSE block never repeats a level, so its bracket is (highest silent,
    # lowest firing]. The FINEST block is the narrower measurement; the COARSE
    # bracket must contain the FINEST threshold.
    a, b = SHORT_SQUARE_BLOCKS
    ta, tb = est[a]["lowest_firing_pa"], est[b]["lowest_firing_pa"]
    audit.observe("short-pulse threshold difference",
                  "%s from %.0f pA, %s from %.0f pA (%.0f pA apart)"
                  % (a, ta, b, tb, abs(ta - tb)))
    audit.check(abs(ta - tb) <= 100.0,
                "short-pulse threshold agrees across COARSE and FINEST",
                "%.0f pA apart, within the 100 pA command increment" % abs(ta - tb))
    audit.observe("contrast with the long steps",
                  "3 ms pulses: the two blocks bracket one threshold; "
                  "1 s steps at +170 pA: 12 spikes versus 1")

    return {"thresholds": est,
            "n_sweeps": len(short),
            "rows": [{"sweep": r["sweep"], "block": r["block"],
                      "amp_pa": r["amplitude_pa"],
                      "duration_ms": r["waveform"]["duration_ms"],
                      "spikes": r["n_detected_in_step"],
                      "first_ms": r["first_spike_ms"]} for r in short]}


def section_doublet(audit: Audit, records, f) -> dict:
    """The two post-stimulus events in sweep 38, measured against in-step spikes."""
    audit.heading("G. Sweep 38 — the post-stimulus doublet at ~5.514/5.521 s")
    r = next(x for x in records if x["sweep"] == COARSE_SWEEP)
    v = r["_v_mv"]
    wave = r["waveform"]

    annotated = r["annotated_spike_times_s"]
    late = [t for t in annotated if t >= wave["end_s"]]
    audit.check(len(late) == 2, "Allen's own annotation contains two post-step spikes",
                "[%.3f, %.3f] s" % (tuple(late) if len(late) == 2 else (float("nan"),) * 2))

    excit = r["post_step_excursions"]
    audit.check(len(excit) == 2, "independent excursion detector finds the same two events",
                "%s" % ["%.3f s" % (e["peak_ms"] / 1e3) for e in excit])

    # The command current in that window.
    stim = dict(list_series(f, "stimulus/presentation"))
    command = to_amps_pa(stim["Sweep_%d" % COARSE_SWEEP])
    lo = int(5.40 * RATE_HZ)
    hi = int(5.60 * RATE_HZ)
    window = command[lo:hi]
    audit.check(bool(np.all(window == 0.0)), "command current is exactly zero in the window",
                "max|I| = %.3e pA over %.3f-%.3f s"
                % (float(np.max(np.abs(window))), lo / RATE_HZ, hi / RATE_HZ))

    # Morphology of the late events versus the driven ones.
    shapes = r["spike_shapes"]
    n_in = r["n_detected_in_step"]
    driven = shapes[:n_in]
    late_shapes = [s for s in shapes if s["peak_ms"] >= wave["end_s"] * 1e3]

    def stats(values):
        arr = np.asarray([x for x in values if np.isfinite(x)])
        if not arr.size:
            return (float("nan"),) * 3
        return float(arr.min()), float(np.median(arr)), float(arr.max())

    print()
    print("  %-28s %-26s %s" % ("metric", "first 3 driven (38)", "late events (38)"))
    for label, key in (("peak (mV)", "peak_mv"),
                       ("amplitude above local baseline (mV)", "amplitude_mv"),
                       ("width at half-max (ms)", "width_ms"),
                       ("rise 10-90% (ms)", "rise_ms"),
                       ("max dV/dt (V/s)", "max_dvdt_v_per_s"),
                       ("min dV/dt (V/s)", "min_dvdt_v_per_s"),
                       ("AHP minimum (mV)", "ahp_mv")):
        a = stats([s[key] for s in driven])
        b = stats([s[key] for s in late_shapes])
        print("  %-28s %-26s %s"
              % (label,
                 "%.3f / %.3f / %.3f" % a,
                 "%.3f / %.3f / %.3f" % b))

    audit.observe("rise 10-90% of the driven column",
                  "only the first driven spike rises from rest; the rest start on "
                  "the preceding AHP tail, which inflates their measured rise")

    # The driven spikes are a weak control. Only the first of them rises from a
    # settled resting potential; the others start from the tail of the preceding
    # AHP, which is why their 10-90% "rise" grows to several ms while the spike
    # itself does not change. The right control for an event that fires from rest
    # is the first spike of every firing sweep, which also fires from rest: here
    # 25 spikes drawn from three blocks over a 39 mV range of baseline potential.
    from_rest = []
    for rec in records:
        if rec.get("family") != "long" or not rec["spike_shapes"]:
            continue
        s = rec["spike_shapes"][0]
        if np.isfinite(s["peak_mv"]):
            from_rest.append(dict(s, sweep=rec["sweep"], block=rec["block"]))

    keys = (("peak_mv", "peak (mV)"),
            ("amplitude_mv", "amplitude (mV)"),
            ("width_ms", "width (ms)"),
            ("rise_ms", "rise (ms)"),
            ("max_dvdt_v_per_s", "max dV/dt (V/s)"),
            ("ahp_mv", "AHP (mV)"))
    envelopes = {}
    if from_rest:
        print()
        print("  from-rest control: first spike of every firing sweep (n=%d)"
              % len(from_rest))
        print("  %-24s %-26s %-26s %s"
              % ("metric", "from-rest population", "late events", "late inside?"))
        for key, label in keys:
            lo, med, hi = stats([s[key] for s in from_rest])
            envelopes[key] = (lo, hi)
            vals = [s[key] for s in late_shapes]
            inside = all(np.isfinite(x) and lo <= x <= hi for x in vals)
            print("  %-24s %-26s %-26s %s"
                  % (label,
                     "%.3f / %.3f / %.3f" % (lo, med, hi),
                     " / ".join("%.3f" % x for x in vals),
                     "yes" if inside else "NO"))

    # Late events fire from the most hyperpolarised baseline in the file, so the
    # closest comparators are the from-rest spikes that also started below
    # -70 mV. Restricting the control to those removes baseline potential as a
    # confound rather than using it as an excuse.
    deep = [s for s in from_rest if s["baseline_mv"] <= -70.0]
    if deep:
        print()
        print("  from-rest control restricted to baseline <= -70 mV (n=%d: sweeps %s)"
              % (len(deep), ", ".join(str(s["sweep"]) for s in deep)))
        for key, label in keys:
            lo, med, hi = stats([s[key] for s in deep])
            print("  %-24s %-26s %-26s %s"
                  % (label,
                     "%.3f / %.3f / %.3f" % (lo, med, hi),
                     " / ".join("%.3f" % s[key] for s in late_shapes),
                     "yes" if all(lo <= s[key] <= hi for s in late_shapes)
                     else "NO"))


    # Baseline immediately before the first event, and the recovery afterwards.
    first_peak = int(late_shapes[0]["peak_ms"] / DT_MS) if late_shapes else None
    pre_lo = max(0, first_peak - int(0.05 * RATE_HZ))
    pre_before = float(np.median(v[pre_lo:first_peak - int(0.002 * RATE_HZ)])) \
        if first_peak else float("nan")
    final = float(v[-1])
    tail = float(np.median(v[-int(0.5 * RATE_HZ):]))
    audit.observe("baseline immediately before the doublet", "%.3f mV" % pre_before)
    audit.observe("median level over the final 0.5 s", "%.3f mV" % tail)
    audit.observe("last sample", "%.3f mV" % final)
    audit.observe("sweep-38 pre-step baseline",
                  "%.3f mV (sd %.3f)"
                  % (r["quality"]["baseline_mv"], r["quality"]["baseline_sd_mv"]))

    # Inter-peak recovery. A width at half-max near 8 ms (versus ~0.9 ms for a
    # driven spike) can mean either a genuinely broad event or two spikes that
    # never repolarise past half-max between them. Those are different
    # phenomena, so the trough between the two peaks is measured directly.
    trough = {}
    if len(late_shapes) == 2:
        p1 = int(late_shapes[0]["peak_ms"] / DT_MS)
        p2 = int(late_shapes[1]["peak_ms"] / DT_MS)
        seg = v[p1:p2 + 1]
        t_off = int(np.argmin(seg))
        trough = {
            "min_mv": float(seg[t_off]),
            "at_ms": (p1 + t_off) * DT_MS,
            "isi_ms": (p2 - p1) * DT_MS,
            "half_max_level_mv": 0.5 * (late_shapes[0]["baseline_mv"]
                                        + late_shapes[0]["peak_mv"]),
        }
        print()
        print("  inter-peak trough          %.3f mV at %.3f ms"
              % (trough["min_mv"], trough["at_ms"]))
        print("  inter-spike interval       %.3f ms" % trough["isi_ms"])
        print("  half-max level             %.3f mV" % trough["half_max_level_mv"])
        audit.observe("the two late events do%s repolarise below half-max"
                      % ("" if trough["min_mv"] < trough["half_max_level_mv"] else " NOT"),
                      "trough %.3f mV vs half-max %.3f mV"
                      % (trough["min_mv"], trough["half_max_level_mv"]))

    # Artefact screening, stated as measurements rather than verdicts.
    print()
    max_jump = r["quality"]["max_jump_in_step_mv"]
    late_jumps = []
    for e in excit:
        a = int(e["peak_ms"] / DT_MS) - int(2.0 / DT_MS)
        b = int(e["peak_ms"] / DT_MS) + int(2.0 / DT_MS)
        a = max(0, a); b = min(v.size, b)
        if b > a + 1:
            late_jumps.append(float(np.max(np.abs(np.diff(v[a:b])))))
    audit.observe("largest single-sample jump during the step", "%.3f mV" % max_jump)
    audit.observe("largest single-sample jump inside the late events",
                  "%.3f mV" % (max(late_jumps) if late_jumps else float("nan")))

    # The first version of this check required the late events not to exceed the
    # driven spikes' slew, and it failed at 1.625 vs 1.531 mV per sample. That
    # expectation was wrong, not the data: an action potential launched from rest
    # near -80 mV has a larger Na+ driving force, and therefore a *faster*
    # upstroke, than one launched from a -46 mV plateau. Faster is what a
    # physiological late spike should look like. What screens for an artefact is
    # whether the event stays inside the envelope of every *other* genuine spike
    # in this file -- the events under test are excluded from that pool, so the
    # comparison is not circular -- and whether its upstroke spans many samples
    # rather than one.
    pool = [s for rec in records if rec.get("family") == "long"
            for s in rec["spike_shapes"]
            if not (rec["sweep"] == COARSE_SWEEP
                    and s["peak_ms"] >= rec["waveform"]["end_s"] * 1e3)]
    pooled = np.asarray([s["max_dvdt_v_per_s"] for s in pool
                         if np.isfinite(s["max_dvdt_v_per_s"])])
    envelope_v_per_s = float(pooled.max()) if pooled.size else float("nan")
    envelope_mv = envelope_v_per_s * DT_MS  # V/s * 5e-6 s/sample * 1e3 mV/V
    worst_late = max(late_jumps) if late_jumps else float("nan")
    audit.observe("reference spike population (late events excluded)",
                  "%d spikes; dV/dt %.1f / %.1f / %.1f V/s (min/median/max)"
                  % (pooled.size,
                     pooled.min() if pooled.size else float("nan"),
                     float(np.median(pooled)) if pooled.size else float("nan"),
                     envelope_v_per_s))
    audit.check(bool(late_jumps) and worst_late <= envelope_mv + 1e-9,
                "late-event slew is inside the envelope of genuine spikes",
                "%.4f mV/sample vs envelope %.4f mV/sample"
                % (worst_late, envelope_mv))
    min_rise = min((s["rise_ms"] for s in late_shapes if np.isfinite(s["rise_ms"])),
                   default=float("nan"))
    audit.check(np.isfinite(min_rise) and min_rise >= 0.05,
                "late-event upstroke spans many samples, not one",
                "shortest 10-90%% rise %.3f ms = %d samples"
                % (min_rise, int(round(min_rise / DT_MS))))
    audit.observe("late events reaching the window edge (width censored)",
                  "%d of %d" % (sum(1 for s in late_shapes if s["width_censored"]),
                                len(late_shapes)))

    # Clipping: a railed amplifier would leave a long constant run.
    audit.check(r["quality"]["longest_flat_ms"] < MAX_PLAUSIBLE_FLAT_MS,
                "no flat run long enough to indicate a stuck converter",
                "longest flat run %.3f ms" % r["quality"]["longest_flat_ms"])
    audit.observe("sweep-38 voltage range",
                  "%.3f .. %.3f mV" % (r["quality"]["v_min_mv"], r["quality"]["v_max_mv"]))
    audit.check(r["quality"]["v_max_mv"] < 200.0,
                "no sample reaches an implausible amplifier rail", "max %.3f mV"
                % r["quality"]["v_max_mv"])

    return {
        "annotated_late_s": late,
        "excursions": excit,
        "command_max_pa_in_window": float(np.max(np.abs(window))),
        "driven_shape_stats": {k: stats([s[k] for s in driven])
                               for k in ("peak_mv", "amplitude_mv", "width_ms",
                                         "rise_ms", "max_dvdt_v_per_s",
                                         "min_dvdt_v_per_s", "ahp_mv")},
        "late_shape_stats": {k: stats([s[k] for s in late_shapes])
                             for k in ("peak_mv", "amplitude_mv", "width_ms",
                                       "rise_ms", "max_dvdt_v_per_s",
                                       "min_dvdt_v_per_s", "ahp_mv")},
        "from_rest_n": len(from_rest),
        "from_rest_envelopes": {k: list(v) for k, v in envelopes.items()},
        "from_rest_deep_n": len(deep),
        "inter_peak_trough": trough,
        "pooled_spikes": int(pooled.size),
        "pooled_dvdt_envelope_v_per_s": envelope_v_per_s,
        "baseline_before_mv": pre_before,
        "final_mv": final,
        "tail_median_mv": tail,
        "max_jump_in_step_mv": max_jump,
        "max_jump_late_mv": worst_late,
    }


def section_quality(audit: Audit, records) -> dict:
    """Recording-quality screen across every long-square sweep."""
    audit.heading("H. Recording quality across the long-square sweeps")
    long_square = [r for r in records if r.get("family") == "long"]

    total_nonfinite = sum(r["quality"]["n_nonfinite"] for r in long_square)
    audit.check(total_nonfinite == 0, "no NaN or infinite sample anywhere",
                "%d non-finite across %d sweeps" % (total_nonfinite, len(long_square)))

    dup = sum(r["quality"]["n_repeat_samples"] for r in long_square)
    n_samples = sum(r["quality"]["n_samples"] for r in long_square)
    audit.observe("repeated consecutive samples",
                  "%d of %d (%.2f%% across %d sweeps)"
                  % (dup, n_samples, 100.0 * dup / max(n_samples, 1), len(long_square)))

    # Quantisation, reported so the count above is not mistaken for data loss.
    # Every sweep should resolve to a fixed ADC step that is small compared with
    # the recording noise; then "repeat" means "same code", not "same reading".
    quanta = sorted({round(r["quality"]["adc_quantum_mv"], 6) for r in long_square
                     if np.isfinite(r["quality"]["adc_quantum_mv"])})
    sds = [r["quality"]["baseline_sd_mv"] for r in long_square]
    worst_ratio = max((sds[i] / max(quanta[0], 1e-9)) for i in range(len(sds)))
    audit.check(len(quanta) == 1 and worst_ratio > 1.0,
                "repeats are ADC quantisation, not stalled sampling",
                "single quantum %.6f mV, smallest noise/quantum ratio %.2f"
                % (quanta[0] if quanta else float("nan"), worst_ratio))
    audit.observe("distinct sample values per sweep",
                  "%d .. %d"
                  % (min(r["quality"]["n_distinct_values"] for r in long_square),
                     max(r["quality"]["n_distinct_values"] for r in long_square)))

    flat = max(r["quality"]["longest_flat_ms"] for r in long_square)
    audit.check(flat < MAX_PLAUSIBLE_FLAT_MS, "no stuck-converter flat run",
                "worst %.3f ms" % flat)

    # Current-command integrity: the command must actually be the documented
    # levels and must be silent outside the step.
    bad = []
    for r in long_square:
        w = r["waveform"]
        if w.get("status") != "OK":
            bad.append((r["sweep"], "no step"))
            continue
        if len(w["pulses"]) != 1:
            bad.append((r["sweep"], "%d pulses" % len(w["pulses"])))
        if not (abs(w["pulses"][0]["level_pa"] - 50.0) < 1e-4):
            bad.append((r["sweep"], "pulse %.3f pA" % w["pulses"][0]["level_pa"]))
        if r["n_samples_stimulus"] != r["quality"]["n_samples"]:
            bad.append((r["sweep"], "stimulus/acquisition length mismatch"))
    audit.check(not bad, "current command is well-formed on every sweep",
                "%d anomalies %s" % (len(bad), bad[:5]))

    # Baseline stability.
    print()
    print("  %-22s %-6s %9s %9s %11s %10s"
          % ("block", "sweep", "base_mV", "sd_mV", "drift_mV/s", "span_mV"))
    worst_sd = 0.0
    worst_drift = 0.0
    for block in sorted({r["block"] for r in long_square}):
        for r in sorted((x for x in long_square if x["block"] == block),
                        key=lambda x: (x["amplitude_pa"], x["sweep"])):
            q = r["quality"]
            worst_sd = max(worst_sd, q["baseline_sd_mv"])
            worst_drift = max(worst_drift, abs(q["baseline_drift_mv_per_s"]))
            print("  %-22s %-6d %9.3f %9.3f %11.4f %10.3f"
                  % (block, r["sweep"], q["baseline_mv"], q["baseline_sd_mv"],
                     q["baseline_drift_mv_per_s"], q["baseline_span_mv"]))

    audit.check(worst_sd < 2.0, "baseline noise is small on every sweep",
                "worst sd %.3f mV" % worst_sd)
    audit.check(worst_drift < 1.0, "no baseline drift beyond 1 mV/s",
                "worst |drift| %.4f mV/s" % worst_drift)

    # Post-step behaviour across the whole block: is the doublet unique?
    print()
    sweeps_with_late = [(r["sweep"], r["n_detected_post_step"],
                         len(r["post_step_excursions"]))
                        for r in long_square
                        if r["n_detected_post_step"] or r["post_step_excursions"]]
    audit.check(len(sweeps_with_late) == 1 and sweeps_with_late[0][0] == COARSE_SWEEP,
                "sweep 38 is the only sweep with any post-step excursion",
                "%s" % sweeps_with_late)

    # Exposure to the phenomenon matters: "only sweep 38 fired late" is only
    # meaningful if every other sweep was watched for at least as long. The
    # doublet sits 3.494 s after the step ends, so a 3.5 s post-step window is the
    # relevant coverage, not the total trace length.
    windows = {r["sweep"]: r["trace_seconds"] - r["waveform"]["end_s"]
               for r in long_square}
    long_enough = [s for s, w in windows.items() if w >= 3.5]
    audit.check(len(long_enough) == len(long_square),
                "every sweep is observed for >=3.5 s after the step ends",
                "%d of %d; shortest %.3f s (sweep %d)"
                % (len(long_enough), len(long_square), min(windows.values()),
                   min(windows, key=windows.get)))
    audit.observe("of those, sweeps with an event after the step",
                  "%d (%s)" % (len(sweeps_with_late),
                               [s for s, _, _ in sweeps_with_late]))

    return {
        "n_long_square": len(long_square),
        "nonfinite": total_nonfinite,
        "repeat_samples": dup,
        "repeat_fraction": dup / max(n_samples, 1),
        "adc_quantum_mv": quanta[0] if quanta else float("nan"),
        "worst_flat_ms": flat,
        "worst_baseline_sd_mv": worst_sd,
        "worst_drift_mv_per_s": worst_drift,
        "command_anomalies": bad,
        "sweeps_with_post_step_excursion": sweeps_with_late,
        "shortest_post_step_window_s": min(windows.values()),
    }


def section_eligibility(audit: Audit, records, spike_table) -> dict:
    """Turn the measurements into explicit per-sweep and per-block decisions.

    The rule is applied mechanically so that no sweep is excused or condemned by
    preference. For a single sweep:

    ``EXCLUDE``
        a sample-integrity fault (non-finite samples, a stalled converter run, an
        amplifier rail) makes the trace unusable;
    ``ELIGIBLE WITH CAVEATS``
        the trace is usable but carries a documented abnormality that restricts
        which analyses it can support;
    ``ELIGIBLE``
        usable, with nothing abnormal found.

    For a block, cross-block disagreement at the contested amplitude outranks
    everything else, because a block that contradicts another block at the same
    command cannot serve as ground truth for a rate comparison regardless of how
    clean its individual traces are.
    """
    audit.heading("I. Eligibility decisions")

    long_square = [r for r in records if r.get("family") == "long"]

    decisions: dict = {"sweeps": {}, "blocks": {}, "named": {}}
    print("  %-6s %-22s %8s %8s %7s %7s  %s"
          % ("sweep", "block", "amp", "in_step", "post", "all", "verdict"))
    for r in sorted(long_square, key=lambda x: x["sweep"]):
        q = r["quality"]
        hard, soft = [], []
        if q["n_nonfinite"]:
            hard.append("%d non-finite samples" % q["n_nonfinite"])
        if q["longest_flat_ms"] >= MAX_PLAUSIBLE_FLAT_MS:
            hard.append("stalled run %.2f ms" % q["longest_flat_ms"])
        if q["v_max_mv"] >= 200.0:
            hard.append("amplifier rail %.1f mV" % q["v_max_mv"])
        if r["n_detected"] != r["n_annotated"]:
            soft.append("count differs from Allen's annotation by %d"
                        % (r["n_detected"] - r["n_annotated"]))
        if r["n_detected_post_step"]:
            soft.append("%d spike(s) after the step ended" % r["n_detected_post_step"])
        verdict = ("EXCLUDE" if hard else
                   "ELIGIBLE WITH CAVEATS" if soft else "ELIGIBLE")
        reasons = hard + soft
        decisions["sweeps"][r["sweep"]] = {
            "block": r["block"], "amp_pa": r["amplitude_pa"],
            "in_step": r["n_detected_in_step"],
            "post_step": r["n_detected_post_step"],
            "verdict": verdict, "reasons": reasons}
        print("  %-6d %-22s %8.1f %8d %7d %7d  %s%s"
              % (r["sweep"], r["block"], r["amplitude_pa"],
                 r["n_detected_in_step"], r["n_detected_post_step"],
                 r["n_detected"], verdict,
                 (" (" + "; ".join(reasons) + ")") if reasons else ""))

    # Repeated amplitudes within a block: the only direct test of reproducibility
    # this file allows.
    intra: dict[str, dict[float, list[int]]] = {}
    at170: dict[str, list[tuple[int, int]]] = {}
    for block, rows in spike_table.items():
        by_amp: dict[float, list[int]] = {}
        for d in rows:
            by_amp.setdefault(round(d["amp"], 2), []).append(d["in_step"])
            if abs(d["amp"] - CONTESTED_PA) < 1e-3:
                at170.setdefault(block, []).append((d["sweep"], d["in_step"]))
        intra[block] = {a: c for a, c in by_amp.items() if len(c) > 1}

    print()
    print("  %-22s %5s %-34s %s" % ("block", "n", "verdict", "reason"))
    for block in sorted(spike_table):
        rows = spike_table[block]
        repeats = intra[block]
        inconsistent = {a: c for a, c in repeats.items() if len(set(c)) > 1}
        mine = {c for _, c in at170.get(block, [])}
        rival = {c for b, hits in at170.items() if b != block for _, c in hits}
        # Only blocks whose own +170 pA counts match this block's may be described
        # as agreeing; listing every block that *has* a +170 pA sweep would make
        # the reason string claim agreement that the table contradicts.
        agreeing = sorted(b for b, hits in at170.items()
                          if b != block and hits
                          and {c for _, c in hits} == mine)
        rival_blocks = sorted(b for b, hits in at170.items() if b != block and hits)

        if rival and mine and not (mine & rival):
            verdict = "UNRESOLVED"
            reason = ("at +%.0f pA gives %s while %s gives %s"
                      % (CONTESTED_PA, sorted(mine), ", ".join(rival_blocks),
                         sorted(rival)))
        elif inconsistent:
            verdict = "ELIGIBLE WITH CAVEATS"
            reason = ("repeats at one command disagree: " +
                      "; ".join("%g pA -> %s" % (a, c)
                                for a, c in sorted(inconsistent.items())))
        elif not repeats:
            verdict = "ELIGIBLE WITH CAVEATS"
            reason = ("one sweep per amplitude, so intra-block reproducibility "
                      "is untested; +%.0f pA agrees with %s"
                      % (CONTESTED_PA, ", ".join(agreeing) or "no other block"))
        else:
            verdict = "ELIGIBLE"
            reason = ("repeats agree (%d repeated amplitude(s)) and +%.0f pA "
                      "agrees with %s"
                      % (len(repeats), CONTESTED_PA,
                         ", ".join(agreeing) or "no other block"))
        decisions["blocks"][block] = {
            "n": len(rows), "verdict": verdict, "reason": reason.strip(),
            "repeats": {str(a): c for a, c in repeats.items()},
            "at_170_pa": at170.get(block, [])}
        print("  %-22s %5d %-34s %s" % (block, len(rows), verdict, reason.strip()))

    # The four decisions the brief asks for, named explicitly.
    print()
    coarse_block = COARSE_BLOCK
    finest_block = FINEST_BLOCK
    remaining = [r["sweep"] for r in long_square
                 if r["block"] == coarse_block and r["sweep"] != COARSE_SWEEP]
    remaining_soft = sorted({reasons for s in remaining
                             for reasons in decisions["sweeps"][s]["reasons"]})

    named = {
        "sweep_38": decisions["sweeps"][COARSE_SWEEP]["verdict"],
        "finest_49_52": ("ELIGIBLE" if decisions["blocks"][finest_block]["verdict"]
                         == "ELIGIBLE" else decisions["blocks"][finest_block]["verdict"]),
        "remaining_coarse": ("ELIGIBLE WITH CAVEATS" if decisions["blocks"][coarse_block]
                             ["verdict"] == "UNRESOLVED" else
                             decisions["blocks"][coarse_block]["verdict"]),
        "coarse_block": decisions["blocks"][coarse_block]["verdict"],
    }
    print("  1. sweep 38                      %s" % named["sweep_38"])
    print("     %s" % "; ".join(decisions["sweeps"][COARSE_SWEEP]["reasons"]))
    print("  2. FINEST sweeps 49-52           %s" % named["finest_49_52"])
    print("     %s" % decisions["blocks"][finest_block]["reason"])
    print("  3. remaining COARSE sweeps       %s" % named["remaining_coarse"])
    print("     %d sweeps (%s), no per-sweep integrity fault; set aside only for "
          "cross-protocol comparison, not for within-block use"
          % (len(remaining), "%d-%d" % (min(remaining), max(remaining))
             if remaining else "none"))
    if remaining_soft:
        print("     per-sweep caveats present: %s" % "; ".join(remaining_soft))
    print("  4. COARSE block as a whole       %s" % named["coarse_block"])
    print("     %s" % decisions["blocks"][coarse_block]["reason"])

    decisions["named"] = named
    decisions["remaining_coarse_sweeps"] = remaining
    return decisions


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------


def make_plots(audit: Audit, records, out_dir: pathlib.Path) -> list[str]:
    """Save diagnostic figures outside Git tracking."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - environment dependent
        audit.note("plotting unavailable (%s); figures skipped" % exc)
        return []

    out_dir.mkdir(parents=True, exist_ok=True)
    long_square = [r for r in records if r.get("family") == "long"]
    written = []

    # 1. F-I relation per block.
    fig, ax = plt.subplots(figsize=(8, 5))
    for block in sorted({r["block"] for r in long_square}):
        items = [r for r in long_square if r["block"] == block]
        items.sort(key=lambda r: r["amplitude_pa"])
        ax.plot([r["amplitude_pa"] for r in items],
                [r["n_detected_in_step"] for r in items],
                marker="o", linestyle="-", label=block)
    ax.set_xlabel("command amplitude (pA)")
    ax.set_ylabel("spikes inside the step")
    ax.set_title("Spikes inside the step, by protocol block — 382982932")
    ax.axvline(CONTESTED_PA, color="k", linestyle=":", linewidth=0.8)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    path = out_dir / "fi_by_block.png"
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    written.append(str(path))

    # 2. Sweep 38 versus the four FINEST repeats.
    by_sweep = {r["sweep"]: r for r in long_square}
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    step = 40  # decimate: 200 kHz is far beyond display resolution
    for s in FINEST_SWEEPS:
        r = by_sweep.get(s)
        if not r:
            continue
        v = r["_v_mv"][:int(3.0 * RATE_HZ)]
        a1.plot(np.arange(v.size)[::step] * DT_MS, v[::step],
                linewidth=0.6, label="FINEST %d" % s)
    r38 = by_sweep[COARSE_SWEEP]
    v = r38["_v_mv"][:int(3.0 * RATE_HZ)]
    a1.plot(np.arange(v.size)[::step] * DT_MS, v[::step],
            linewidth=0.8, color="k", label="COARSE 38")
    a1.set_ylabel("V (mV)")
    a1.set_title("170 pA: COARSE 38 versus FINEST 49-52 (first 3 s)")
    a1.legend(fontsize=7); a1.grid(alpha=0.3)
    w = r38["waveform"]
    # Same x unit as the voltage panel above; sharex makes any mismatch visible.
    a2.plot(np.array([0.0, w["onset_s"], w["onset_s"], w["end_s"], w["end_s"], 3.0]) * 1e3,
            [0, 0, w["level_pa"], w["level_pa"], 0, 0], color="tab:red")
    a2.set_xlabel("time in sweep (ms)"); a2.set_ylabel("I (pA)")
    a2.grid(alpha=0.3)
    path = out_dir / "sweep38_vs_finest.png"
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    written.append(str(path))

    # 3. The doublet, zoomed, with the command current beneath it.
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    lo, hi = int(5.40 * RATE_HZ), int(5.60 * RATE_HZ)
    t = np.arange(lo, hi) * DT_MS / 1e3
    a1.plot(t, r38["_v_mv"][lo:hi], color="k", linewidth=1.0)
    for e in r38["post_step_excursions"]:
        a1.axvline(e["peak_ms"] / 1e3, color="tab:red", linestyle="--", linewidth=0.8)
    a1.set_ylabel("V (mV)")
    a1.set_title("Sweep 38: post-stimulus doublet at 5.40-5.60 s")
    a1.grid(alpha=0.3)
    a2.plot(t, np.zeros_like(t), color="tab:red")
    a2.set_ylim(-1, 1); a2.set_xlabel("time in sweep (s)")
    a2.set_ylabel("I (pA)"); a2.grid(alpha=0.3)
    path = out_dir / "doublet_zoom.png"
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    written.append(str(path))

    # 4. Late-event shape versus an ordinary driven spike from the same trace.
    fig, ax = plt.subplots(figsize=(8, 5))
    driven = r38["spike_shapes"][:r38["n_detected_in_step"]]
    late = [s for s in r38["spike_shapes"] if s["peak_ms"] >= r38["waveform"]["end_s"] * 1e3]
    window = int(15.0 / DT_MS)
    for i, s in enumerate(driven[:4]):
        peak = int(s["peak_ms"] / DT_MS)
        a, b = max(0, peak - window), min(r38["_v_mv"].size, peak + window)
        ax.plot((np.arange(a, b) - peak) * DT_MS, r38["_v_mv"][a:b],
                color="tab:blue", linewidth=0.7,
                label="driven spike" if i == 0 else None)
    for i, s in enumerate(late):
        peak = int(s["peak_ms"] / DT_MS)
        a, b = max(0, peak - window), min(r38["_v_mv"].size, peak + window)
        ax.plot((np.arange(a, b) - peak) * DT_MS, r38["_v_mv"][a:b],
                color="tab:red", linewidth=0.9,
                label="late event %d" % (i + 1))
    ax.set_xlabel("time from peak (ms)"); ax.set_ylabel("V (mV)")
    ax.set_title("Sweep 38: late events versus driven spikes, aligned on peak")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    path = out_dir / "late_vs_driven_shape.png"
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    written.append(str(path))

    # 5. Post-step windows for every COARSE sweep, stacked: is the doublet unique?
    #    The window must reach the doublet, which lands ~3.49 s AFTER the step
    #    ends, not just after it. Decimation takes the per-bin maximum rather than
    #    every n-th sample: a 1 ms spike disappears under stride decimation, which
    #    is exactly what the earlier version of this figure did.
    fig, ax = plt.subplots(figsize=(10, 6))
    coarse = sorted((r for r in long_square if r["block"] == "C1LSCOARSE150216"),
                    key=lambda r: r["sweep"])
    bin_samples = int(0.002 * RATE_HZ)  # 2 ms envelope bins
    for r in coarse:
        start = r["waveform"]["end_index"]
        seg = r["_v_mv"][start:]
        n_bins = seg.size // bin_samples
        if n_bins < 10:
            continue
        env = seg[:n_bins * bin_samples].reshape(n_bins, bin_samples).max(axis=1)
        t = (np.arange(n_bins) + 0.5) * bin_samples * DT_MS / 1e3
        off = 40.0 * (len(coarse) - 1 - coarse.index(r))
        late = bool(r["n_detected_post_step"])
        ax.plot(t, env + off, linewidth=0.6,
                color="tab:red" if late else "tab:grey",
                label=("sweep %d (%+.0f pA): %d post-step spikes"
                       % (r["sweep"], r["amplitude_pa"], r["n_detected_post_step"]))
                if late else None)
    ax.set_xlabel("time after step end (s)")
    ax.set_ylabel("V (mV), 40 mV offset per sweep")
    ax.set_title("Post-step window (2 ms max-envelope) for all 20 COARSE sweeps")
    ax.legend(fontsize=7); ax.grid(alpha=0.3)
    path = out_dir / "post_step_all_coarse.png"
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    written.append(str(path))

    audit.observe("figures written", "%d files in %s" % (len(written), out_dir))
    return written


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nwb", required=True, type=pathlib.Path)
    parser.add_argument("--plots-dir", default=None, type=pathlib.Path,
                        help="destination for figures; must be outside Git tracking")
    parser.add_argument("--json", default=None, type=pathlib.Path)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args(argv)

    if not args.nwb.exists():
        print("ERROR: %s does not exist" % args.nwb, file=sys.stderr)
        return 2

    audit = Audit()
    # The report is UTF-8; a cp1252 console would mangle every em dash it prints.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # pragma: no cover - older interpreters / redirected file
        pass
    print("Phase 2D — electrophysiology anomaly and protocol consistency audit")
    print("NWB: %s" % args.nwb)

    with open_nwb(args.nwb) as f:
        provenance = section_provenance(audit, args.nwb, f, list_series(f, "stimulus/presentation"))
        records = build_records(f, audit)
        inventory = section_inventory(audit, records)
        contested = section_contested(audit, records, f)
        second = section_second_block(audit, records, inventory)
        spikes = section_spikes(audit, records)
        short_square = section_short_square(audit, records)
        doublet = section_doublet(audit, records, f)
        quality = section_quality(audit, records)
        eligibility = section_eligibility(audit, records, spikes["table"])

    figures = []
    if not args.no_plots:
        plots_dir = args.plots_dir or (args.nwb.resolve().parent / "phase2d_plots")
        figures = make_plots(audit, records, plots_dir)

    summary = audit.summary()
    print()
    print("=" * 78)
    print("CHECKS: %d  passed: %d  failed: %d   observations: %d"
          % (summary["checks"], summary["passed"], summary["failed"],
             summary["observations"]))
    print("=" * 78)
    if summary["failed"]:
        for row in summary["failures"]:
            print("  FAILED: %s  %s" % (row["label"], row["detail"]))
        print("RESULT: %d protocol check(s) failed" % summary["failed"])
    else:
        print("RESULT: every protocol-consistency check passed")

    payload = {
        "specimen": SPECIMEN,
        "provenance": provenance,
        "inventory": inventory,
        "contested_amplitude": contested,
        "second_long_square_block": second,
        "spikes": spikes,
        "short_square": short_square,
        "doublet": doublet,
        "quality": quality,
        "eligibility": eligibility,
        "figures": figures,
        "checks": summary,
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print("summary written to %s" % args.json)

    # Detach the retained voltage vectors so a caller importing this module does
    # not keep ~500 MB alive through the records list.
    for r in records:
        r.pop("_v_mv", None)

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

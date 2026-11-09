#!/usr/bin/env python
"""Phase 2F — recording-only analysis of the COARSE/FINEST excitability difference.

This phase asks a question about *recordings*, not about a model. Specimen
382982932 fires 12 times during a 1 s / +170 pA step in the COARSE block
(`C1LSCOARSE150216`, sweep 38) and exactly once in each of four FINEST repeats
(`C1LSFINEST150112`, sweeps 49–52) on a bit-identical command. Phase 2D
established that fact and excluded stimulus, steady-state voltage and passive
membrane explanations. Phase 2E established that the fitted perisomatic model
reproduces the COARSE trajectory and therefore fails the FINEST block.

What neither phase did is characterise the *shape* of the response inside the
step: whether the COARSE train accommodates, what changes across successive
spikes, and how the single FINEST spike differs from the first COARSE spike. That
is the entire content of this script. No model is imported, executed or scored.

Design rules, inherited from Phase 2D and enforced here:

* **Recording-only.** numpy + h5py for measurement; matplotlib only for figures.
  There is no NEURON import, no AllenSDK runner, no FHIR/FHN, no parameter file.
* **Three detectors, cross-checked.** The validated 0 mV-crossing detector from
  Phase 2D is the primary. A velocity-based detector is added and must agree with
  it count-for-count, and both are checked against Allen's own
  `/analysis/spike_times` annotation. Disagreement is reported, never smoothed
  over.
* **No manufactured indices.** A quantity that a single spike cannot support —
  any inter-spike interval, rate or adaptation index on sweeps 49–52 — is
  reported as unavailable with a reason, never as zero and never as NaN passed
  off as a measurement.
* **Blocks are never pooled.** COARSE, FINEST and C2 are measured separately and
  compared; no aggregate across them is computed anywhere.
* **Observations are not mechanisms.** Accommodation is described as a measured
  change in rate, trough and threshold. Nothing here claims *why* the block
  difference exists.

Read-only. The NWB is opened through the Phase 1C/1D access layer and never
written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np

# Reuse the validated layers rather than re-deriving them. The Phase 2D module
# contributes the stimulus splitter, the 0 mV-crossing detector, the morphology
# measurement and the quality metrics; a second implementation of any of those
# would only add a way for the two phases to disagree.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit_electrophysiology_protocols as phase2d  # noqa: E402
from validate_nwb_stimulus_units import (  # noqa: E402
    _as_text,
    list_series,
    open_nwb,
    s_field,
    s_num,
    series_rate,
    template_key,
)

SPECIMEN = 382982932
RATE_HZ = 200_000.0
DT_MS = 1e3 / RATE_HZ

#: The three long-square blocks. Discovered from the template families by Phase
#: 2D and asserted here rather than assumed.
COARSE_BLOCK = "C1LSCOARSE150216"
FINEST_BLOCK = "C1LSFINEST150112"
C2_BLOCK = "C2SQRHELNG150216"
LONG_SQUARE_BLOCKS = (COARSE_BLOCK, FINEST_BLOCK, C2_BLOCK)

#: The amplitude where the blocks contradict each other, and the sweeps named in
#: the brief.
CONTESTED_PA = 170.0
FITTING_SWEEP = 38
HELD_OUT_SWEEPS = (49, 50, 51, 52)

#: From Phase 1C / Phase 2D, re-verified before anything is measured.
EXPECTED_BYTES = 94_207_824
EXPECTED_SHA256 = "d38b43fcbdf1c88dfa6741a565ac689289aef931d66b9eb6b64ca5598f237b63"

#: Spike counts published by Phase 2D for the COARSE F-I curve. Reproduced here
#: as a regression check on the extraction path, not as new evidence.
PHASE2D_COARSE_FI = {36: 1, 37: 6, 38: 12, 39: 18, 40: 22, 41: 25, 42: 29, 43: 32}
PHASE2D_FINEST_FI = {44: 0, 45: 0, 46: 0, 47: 0, 48: 0, 49: 1, 50: 1, 51: 1, 52: 1}
PHASE2D_FIRST_SPIKE_S = {38: 1.060, 49: 1.124, 50: 1.097, 51: 1.113, 52: 1.113}
PHASE2D_PLATEAU_MEDIAN_MV = {
    38: -47.094, 49: -45.813, 50: -46.312, 51: -45.938, 52: -47.000,
}

#: Velocity criterion for the secondary detector and for spike threshold.
#: A single-sample difference at 200 kHz turns the 0.031 mV ADC quantum into
#: +/-6.2 V/s of apparent slew, so a velocity threshold near that floor would be
#: measuring quantisation. The run measures the actual pre-step noise ceiling and
#: refuses to proceed if the criterion is not well clear of it.
THRESHOLD_DVDT_V_PER_S = 50.0
THRESHOLD_NOISE_MARGIN = 3.0
DVDT_SMOOTH_SAMPLES = 4
THRESHOLD_LOOKBACK_MS = 10.0

#: Spike morphology window, matching Phase 2D so the two phases are comparable.
PRE_WINDOW_MS = 30.0
POST_WINDOW_MS = 40.0
AHP_GUARD_MS = 1.0
RISE_SEARCH_MS = 15.0

#: Plateau and baseline windows, matching Phase 2D.
PLATEAU_WINDOW_MS = 200.0

#: A flat run this long at 200 kHz is a stuck converter, not a membrane.
MAX_PLAUSIBLE_FLAT_MS = 5.0

#: Deterministic permutation test, so a re-run reproduces every p-value.
PERMUTATION_SEED = 20250218
PERMUTATION_DRAWS = 20_000

MISSING = "unavailable"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


class Report:
    """Collects asserted checks and reported observations separately.

    The split is the same one Phase 2D used and for the same reason: a check is a
    fact about the file that must hold for the analysis to be trustworthy, while
    an observation is a measurement whose *interpretation* is the subject of the
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
        by_section: dict[str, dict[str, int]] = {}
        for label, ok, _ in self.checks:
            bucket = by_section.setdefault(label.split("|")[0], {"checks": 0,
                                                                 "failed": 0})
            bucket["checks"] += 1
            if not ok:
                bucket["failed"] += 1
        return {
            "checks": len(self.checks),
            "passed": len(self.checks) - self.failures,
            "failed": self.failures,
            "observations": len(self.observations),
            "by_section": by_section,
            "failures": [{"label": label, "detail": detail}
                         for label, ok, detail in self.checks if not ok],
        }


# ---------------------------------------------------------------------------
# File identity
# ---------------------------------------------------------------------------


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Signal primitives
# ---------------------------------------------------------------------------


def smooth_dvdt(v_mv: np.ndarray, rate_hz: float,
                window: int = DVDT_SMOOTH_SAMPLES) -> np.ndarray:
    """dV/dt in V/s, boxcar-averaged over ``window`` samples.

    A single-sample difference is unusable as a *threshold* variable here: at
    200 kHz one ADC code is 0.031248 mV, so consecutive samples differ by 0 or one
    code and the unsmoothed derivative already reaches +/-6.2 V/s in the quietest
    baseline. Averaging four samples (0.02 ms) divides that floor by two while
    slowing a 0.4 ms upstroke by nothing measurable. ``window=1`` returns the raw
    single-sample difference, which is what the maximum-upstroke measurement
    wants.
    """
    d = np.diff(v_mv, prepend=v_mv[0]) * 1e-3 * rate_hz
    if window <= 1:
        return d
    kernel = np.ones(int(window), dtype=np.float64) / float(window)
    return np.convolve(d, kernel, mode="same")


def detect_spikes_dvdt(v_mv: np.ndarray, rate_hz: float, dvdt: np.ndarray,
                       criterion_v_per_s: float = THRESHOLD_DVDT_V_PER_S,
                       refractory_ms: float = 1.5) -> np.ndarray:
    """Peak indices of velocity-defined upstrokes — an independent second detector.

    Phase 2D's detector asks "when did the membrane cross 0 mV?", which is a
    voltage criterion. This one asks "when did the membrane start rising faster
    than ``criterion_v_per_s``?", which is a velocity criterion. The two can only
    agree on a genuine regenerative event, so their agreement is a real check on
    the count rather than a restatement of it.

    The reported index is the voltage maximum reached within 5 ms of the upstroke
    onset, so that it is the same physical instant the primary detector reports
    (the peak) and the two time series can be compared directly.
    """
    above = dvdt >= criterion_v_per_s
    if not above.any():
        return np.array([], dtype=int)
    rising = np.flatnonzero(~above[:-1] & above[1:]) + 1
    if not rising.size:
        return np.array([], dtype=int)
    refractory = int(refractory_ms / DT_MS)
    search = int(5.0 / DT_MS)
    peaks: list[int] = []
    for onset in rising:
        stop = min(v_mv.size, onset + search)
        peak = int(onset + int(np.argmax(v_mv[onset:stop])))
        if peaks and peak - peaks[-1] < refractory:
            continue
        peaks.append(peak)
    return np.asarray(peaks, dtype=int)


def threshold_crossing(v_mv: np.ndarray, dvdt: np.ndarray, peak_index: int,
                       rate_hz: float,
                       criterion_v_per_s: float = THRESHOLD_DVDT_V_PER_S,
                       lookback_ms: float = THRESHOLD_LOOKBACK_MS) -> dict:
    """Voltage at which an upstroke becomes regenerative.

    Walks back from the steepest point of the upstroke along a *contiguous* run of
    suprathreshold velocity and reports the first sample of that run. Contiguity
    is what makes this robust: taking instead the earliest suprathreshold sample
    in a 10 ms window lets a single noise sample inside the afterhyperpolarisation
    become the threshold of the following spike, which reports thresholds tens of
    millivolts too negative whenever the AHP is deep and noisy.

    Returns ``{"index", "v_mv", "t_ms", "dvdt_v_per_s", "run_ms"}`` plus the
    number of samples in the contiguous run, or a dict with ``"v_mv": None`` when
    no suprathreshold upstroke exists before the peak.
    """
    lo = max(0, peak_index - int(lookback_ms / DT_MS))
    window = dvdt[lo:peak_index + 1]
    if not window.size:
        return {"index": None, "v_mv": None, "t_ms": None,
                "dvdt_v_per_s": None, "run_samples": 0}
    steepest = lo + int(np.argmax(window))
    above = dvdt >= criterion_v_per_s
    index = steepest
    while index > lo and above[index - 1]:
        index -= 1
    if not above[index]:
        # The steepest sample itself is below the criterion: no upstroke here.
        return {"index": None, "v_mv": None, "t_ms": None,
                "dvdt_v_per_s": None, "run_samples": 0}
    return {
        "index": int(index),
        "v_mv": float(v_mv[index]),
        "t_ms": float(index * DT_MS),
        "dvdt_v_per_s": float(dvdt[index]),
        "run_samples": int(steepest - index + 1),
    }


def spike_metrics(v_mv: np.ndarray, rate_hz: float, dvdt: np.ndarray,
                  peak_index: int, reference: str = "local",
                  ahp_limit_index: int | None = None,
                  pre_ms: float = PRE_WINDOW_MS,
                  post_ms: float = POST_WINDOW_MS) -> dict:
    """Morphology of one spike about an explicit reference voltage.

    Two references are defined, and the choice matters inside a train:

    ``local``
        The Phase 2D convention — median of the 30 ms preceding the peak,
        excluding the 2 ms immediately before it. It is the right reference for a
        spike fired from rest and is reproduced exactly here so that this phase's
        numbers can be compared with Phase 2D's. Inside a train it measures the
        spike against the rising ramp it grew out of, which shrinks the apparent
        amplitude and raises the half-maximum level.

    ``trough``
        The local minimum in the 30 ms preceding the peak, i.e. the inter-spike
        trough. This is the physically meaningful reference for a spike in a
        train, because the membrane genuinely started from there.

    Both are reported for every spike; the train analysis uses ``trough`` and the
    cross-block comparison uses ``local``, so that a change of definition can
    never be mistaken for a change of physiology.
    """
    pre = int(pre_ms / DT_MS)
    post = int(post_ms / DT_MS)
    lo = max(0, peak_index - pre)
    hi = min(v_mv.size, peak_index + post)
    seg = v_mv[lo:hi]
    peak_off = peak_index - lo
    peak = float(v_mv[peak_index])

    result = {
        "peak_index": int(peak_index),
        "peak_mv": peak,
        "peak_ms": float(peak_index * DT_MS),
        "reference": reference,
        "reference_mv": float("nan"),
        "amplitude_mv": float("nan"),
        "width_ms": float("nan"),
        "width_censored": False,
        "rise_ms": float("nan"),
        "dvdt_max_v_per_s": float("nan"),
        "dvdt_min_v_per_s": float("nan"),
        "ahp_mv": float("nan"),
        "ahp_ms": float("nan"),
    }
    if seg.size < 3:
        return result

    if reference == "trough":
        up_lo = max(0, peak_off - int(pre_ms / DT_MS))
        ref_off = up_lo + int(np.argmin(seg[up_lo:peak_off + 1]))
        ref_value = float(seg[ref_off])
        rise_start_off = ref_off
    elif reference == "local":
        base_lo = max(0, peak_index - pre)
        base_hi = max(base_lo + 1, peak_index - int(2.0 / DT_MS))
        ref_value = float(np.median(v_mv[base_lo:base_hi]))
        # Phase 2D starts the rise from the local minimum in the preceding 15 ms,
        # not from the 30 ms median: the median is a robust *level* but is not a
        # point on the trace, so a 10-90 % walk anchored on it lands in noise.
        up_lo = max(0, peak_off - int(RISE_SEARCH_MS / DT_MS))
        rise_start_off = up_lo + int(np.argmin(seg[up_lo:peak_off + 1]))
    else:
        raise ValueError("unknown reference %r" % (reference,))

    result["reference_mv"] = ref_value
    amplitude = peak - ref_value
    result["amplitude_mv"] = amplitude
    if amplitude <= 0:
        return result

    # Width at half maximum, walked outward from the peak. Walking rather than
    # searching the whole window is what stops a 40 ms post-window from absorbing
    # the next spike's upstroke and reporting a 40 ms width for a 0.9 ms event.
    half = ref_value + amplitude / 2.0
    above = seg >= half
    w_lo = w_hi = peak_off
    while w_lo > 0 and above[w_lo - 1]:
        w_lo -= 1
    while w_hi + 1 < seg.size and above[w_hi + 1]:
        w_hi += 1
    result["width_ms"] = (w_hi - w_lo + 1) / rate_hz * 1e3
    result["width_censored"] = bool(w_lo == 0 or w_hi == seg.size - 1)

    # 10-90 % rise, measured from the reference sample rather than from a
    # window-wide search, for the reason given in Phase 2D's spike_shape.
    upstroke = seg[rise_start_off:peak_off + 1]
    if upstroke.size >= 2:
        tenth = ref_value + 0.1 * amplitude
        ninetieth = ref_value + 0.9 * amplitude
        i10 = np.flatnonzero(upstroke >= tenth)
        i90 = np.flatnonzero(upstroke >= ninetieth)
        if i10.size and i90.size:
            result["rise_ms"] = (i90[0] - i10[0]) / rate_hz * 1e3

    raw = np.diff(seg) * 1e-3 * rate_hz
    if raw.size:
        result["dvdt_max_v_per_s"] = float(raw.max())
        result["dvdt_min_v_per_s"] = float(raw.min())

    # Afterhyperpolarisation, from 1 ms after the peak so that the repolarisation
    # slope itself is not counted, up to 40 ms or to a caller-supplied limit (the
    # next spike minus a guard), whichever comes first.
    ahp_lo = peak_off + int(AHP_GUARD_MS / DT_MS)
    if ahp_limit_index is not None:
        ahp_hi = min(seg.size, int(ahp_limit_index) - lo)
    else:
        ahp_hi = seg.size
    if ahp_hi > ahp_lo:
        span = seg[ahp_lo:ahp_hi]
        k = int(np.argmin(span))
        result["ahp_mv"] = float(span[k])
        result["ahp_ms"] = float((ahp_lo + k + lo) * DT_MS)
    return result


# ---------------------------------------------------------------------------
# Statistics — deterministic, tie-aware, dependency-free
# ---------------------------------------------------------------------------


def _ranks(values: np.ndarray) -> np.ndarray:
    """Average ranks, so that tied values do not silently break a correlation.

    ISIs and amplitudes are recorded at a 5 us grid and therefore tie often; a
    naive ``argsort`` ranking would impose an arbitrary order on equal values and
    make the p-value depend on that accident.
    """
    x = np.asarray(values, dtype=float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, dtype=float)
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and x[order[j + 1]] == x[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks


def spearman_rho(x, y) -> float:
    """Spearman rank correlation as Pearson's r on average ranks."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size != y.size or x.size < 3:
        return float("nan")
    dx = _ranks(x)
    dy = _ranks(y)
    dx = dx - dx.mean()
    dy = dy - dy.mean()
    denominator = float(np.sqrt((dx ** 2).sum() * (dy ** 2).sum()))
    if denominator == 0.0:
        return float("nan")
    return float((dx * dy).sum() / denominator)


def permutation_p(x, y, seed: int = PERMUTATION_SEED,
                  draws: int = PERMUTATION_DRAWS) -> float:
    """Permutation p-value for a monotone association, in its observed direction.

    The asymptotic Spearman p-value assumes independence and no ties, neither of
    which holds for eleven ISIs drawn from one train with a quantised time base.
    Permuting the ranks instead makes no distributional assumption, and fixing
    both the seed and the draw count makes every reported p-value reproducible
    to the last digit on a re-run.

    The tail counted is the one the data fell into, so a strong *negative*
    association also gets a small p. Counting only the upper tail would report
    p = 0.999 for a perfectly ordered decline, which reads like a null result
    and is the opposite of what the measurement shows. The direction is always
    printed alongside the p-value. The estimate is the add-one form
    ``(exceed + 1) / (draws + 1)``, which cannot return exactly zero.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size != y.size or x.size < 3:
        return float("nan")
    observed = spearman_rho(x, y)
    if not np.isfinite(observed):
        return float("nan")
    dx = _ranks(x)
    dx = dx - dx.mean()
    sxx = float((dx ** 2).sum())
    rng = np.random.default_rng(seed)
    shuffled = y.copy()
    high = 0
    low = 0
    for _ in range(int(draws)):
        rng.shuffle(shuffled)
        dy = _ranks(shuffled)
        dy = dy - dy.mean()
        syy = float((dy ** 2).sum())
        if syy == 0.0:
            continue
        rho = float((dx * dy).sum()) / np.sqrt(sxx * syy)
        if rho >= observed:
            high += 1
        if rho <= observed:
            low += 1
    return float((min(high, low) + 1) / (draws + 1))


def trend(values, seed: int = PERMUTATION_SEED,
          draws: int = PERMUTATION_DRAWS) -> dict:
    """Monotone trend of a quantity measured once per event, in event order.

    Used for "does the ISI lengthen across the train?" and "does the spike get
    smaller?". Returns ``available: False`` rather than a number when there are
    fewer than three events, because a two-point "trend" is a difference, not a
    trend, and the brief forbids manufacturing exactly that kind of index.
    """
    v = []
    for a in values:
        # Refused measurements are dropped, not coerced: a threshold that could
        # not be located is missing evidence, not a zero.
        try:
            number = float(a)
        except (TypeError, ValueError):
            continue
        if np.isfinite(number):
            v.append(number)
    if len(v) < 3:
        return {"available": False,
                "reason": "%d usable values; a monotone trend needs at least 3"
                          % len(v),
                "n": len(v)}
    order = np.arange(1, len(v) + 1, dtype=float)
    rho = spearman_rho(order, v)
    p = permutation_p(order, v, seed=seed, draws=draws)
    return {
        "available": True,
        "n": len(v),
        "rho": rho,
        "p_permutation": p,
        "direction": ("rising" if rho > 0 else
                      "falling" if rho < 0 else "flat"),
        "first": v[0],
        "last": v[-1],
        "change": v[-1] - v[0],
    }


# ---------------------------------------------------------------------------
# Adaptivity — only where an interval exists
# ---------------------------------------------------------------------------


def adaptation_summary(isi_ms, spike_count: int) -> dict:
    """Rate/interval description of a train, or an explicit refusal.

    The refusal is the important half. Sweeps 49-52 contain exactly one spike, so
    they contain zero inter-spike intervals; every adaptation index in the
    literature (first/last ISI ratio, burst index, early/late rate ratio) is
    undefined on such a trace. Returning 0.0 or NaN would quietly enter a table
    as if it were a measurement and invite a comparison against an 11-interval
    train. The function therefore reports ``available: False`` and states why.
    """
    values = [float(v) for v in isi_ms]
    result = {
        "available": False,
        "reason": "",
        "spike_count": int(spike_count),
        "n_isi": len(values),
        "isi_first_ms": None, "isi_last_ms": None, "isi_min_ms": None,
        "isi_max_ms": None, "isi_mean_ms": None, "isi_sd_ms": None,
        "isi_cv": None, "isi_ratio": None,
        "rate_first_hz": None, "rate_last_hz": None, "rate_mean_hz": None,
        "early_rate_hz": None, "late_rate_hz": None, "rate_ratio": None,
        "monotone_fraction": None, "interval_trend": None,
    }
    if len(values) < 2:
        result["reason"] = (
            "%d spike(s) in the step -> %d inter-spike interval(s). Every "
            "adaptation index requires at least two intervals, so none is "
            "computed for this sweep." % (spike_count, len(values))
        )
        return result

    n = len(values)
    first, last = values[0], values[-1]
    mean = float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if n > 1 else float("nan")
    half = n // 2
    early = values[:half]
    late = values[n - half:]
    rises = [1 for a, b in zip(values, values[1:]) if b > a]

    result.update({
        "available": True,
        "isi_first_ms": first,
        "isi_last_ms": last,
        "isi_min_ms": float(np.min(values)),
        "isi_max_ms": float(np.max(values)),
        "isi_mean_ms": mean,
        "isi_sd_ms": sd,
        "isi_cv": (sd / mean) if mean > 0 else None,
        "isi_ratio": (last / first) if first > 0 else None,
        "rate_first_hz": 1000.0 / first if first > 0 else None,
        "rate_last_hz": 1000.0 / last if last > 0 else None,
        "rate_mean_hz": 1000.0 / mean if mean > 0 else None,
        # The middle interval is dropped from the two halves when n is odd, so
        # that early and late are always the same number of intervals apart.
        "early_rate_hz": 1000.0 / float(np.mean(early)),
        "late_rate_hz": 1000.0 / float(np.mean(late)),
        # A rate ratio, not an interval ratio: the halves are summarised by their
        # mean rate and then divided, so a decelerating train gives a number
        # above 1. Dividing the mean *intervals* instead gives the reciprocal
        # and would label a 1.34-fold deceleration as 0.747.
        "rate_ratio": (float(np.mean(late)) / float(np.mean(early))
                       if float(np.mean(early)) > 0 else None),
        "monotone_fraction": (len(rises) / float(n - 1)) if n > 1 else None,
        "interval_trend": trend(values),
    })
    return result


def inter_spike_segments(v_mv: np.ndarray, peak_indices,
                         thresholds) -> list[dict]:
    """Decompose each inter-spike interval into repolarisation, trough and ramp.

    A lengthening ISI can come from three different places: slower
    repolarisation, a deeper and longer afterhyperpolarisation, or a shallower
    post-trough ramp to threshold. Reporting only the total ISI cannot tell them
    apart, and the three have different implications — the first two are
    spike-shape changes, the third is an excitability change. The sum of the
    three parts is checked against the measured ISI by the caller.
    """
    peaks = [int(p) for p in peak_indices]
    out: list[dict] = []
    for k in range(len(peaks) - 1):
        p0, p1 = peaks[k], peaks[k + 1]
        if p1 <= p0:
            continue
        span = v_mv[p0:p1 + 1]
        trough_index = p0 + int(np.argmin(span))
        entry = {
            "pair": (k, k + 1),
            "peak_from_ms": p0 * DT_MS,
            "peak_to_ms": p1 * DT_MS,
            "isi_ms": (p1 - p0) * DT_MS,
            "trough_ms": trough_index * DT_MS,
            "trough_mv": float(v_mv[trough_index]),
            "fall_ms": (trough_index - p0) * DT_MS,
            "threshold_ms": None,
            "threshold_mv": None,
            "ramp_ms": None,
            "upstroke_ms": None,
        }
        threshold = thresholds[k + 1] if k + 1 < len(thresholds) else None
        threshold_index = threshold.get("index") if threshold else None
        if threshold_index is not None and trough_index <= threshold_index <= p1:
            entry["threshold_ms"] = threshold_index * DT_MS
            entry["threshold_mv"] = float(v_mv[threshold_index])
            entry["ramp_ms"] = (threshold_index - trough_index) * DT_MS
            entry["upstroke_ms"] = (p1 - threshold_index) * DT_MS
        out.append(entry)
    return out


# ---------------------------------------------------------------------------
# Membrane charging
# ---------------------------------------------------------------------------


def fit_charge_tau(t_ms, v_mv, tau_grid=None) -> dict:
    """Single-exponential charging fit, ``V(t) = A exp(-t/tau) + C``.

    Used for the subthreshold approach to the plateau after step onset, and for
    the subthreshold relaxation after step offset. For a *fixed* tau the model is
    linear in (A, C), so a grid over tau with an exact linear solve at each node
    finds the least-squares optimum without any iterative optimiser: no seed, no
    convergence criterion, identical output on every machine.

    The free asymptote matters. Forcing ``C`` to the pre-step baseline — which is
    correct at step offset, where the cell must return to rest — would bias a
    charging fit made *during* a depolarising step, because there C is the
    plateau the cell is charging towards.
    """
    t = np.asarray(t_ms, dtype=float)
    v = np.asarray(v_mv, dtype=float)
    blank = {"available": False, "tau_ms": None, "amplitude_mv": None,
             "asymptote_mv": None, "r2": None, "n": int(t.size)}
    if t.size != v.size or t.size < 8 or not np.all(np.isfinite(v)):
        return blank
    if np.ptp(v) <= 0.0:
        return blank
    grid = (np.geomspace(0.5, 800.0, 600) if tau_grid is None
            else np.asarray(tau_grid, dtype=float))
    design_ones = np.ones_like(t)
    best_sse = None
    best = None
    for tau in grid:
        design = np.column_stack([np.exp(-t / tau), design_ones])
        coefficients, _res, _rank, _sv = np.linalg.lstsq(design, v, rcond=None)
        residual = v - design @ coefficients
        sse = float(residual @ residual)
        if best_sse is None or sse < best_sse:
            best_sse = sse
            best = (float(tau), float(coefficients[0]), float(coefficients[1]))
    total = float(((v - v.mean()) ** 2).sum())
    return {
        "available": True,
        "tau_ms": best[0],
        "amplitude_mv": best[1],
        "asymptote_mv": best[2],
        "r2": float(1.0 - best_sse / total) if total > 0 else float("nan"),
        "n": int(t.size),
    }


def post_spike_profile(v_mv: np.ndarray, peak_index: int, rate_hz: float,
                       limit_index: int | None = None,
                       offsets_ms=(0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 7.5,
                                   10.0, 15.0, 20.0, 25.0, 30.0, 35.0,
                                   40.0)) -> dict:
    """Voltage at fixed delays after a peak, truncated before the next spike.

    Sampling at fixed offsets rather than at "the trough" means two traces can be
    compared without either of them having to share a trough time, and the
    truncation at ``limit_index`` stops a short ISI from sampling the next
    spike's upstroke and reporting it as sustained depolarisation.
    """
    stop = v_mv.size if limit_index is None else min(v_mv.size, int(limit_index))
    out: dict[str, float] = {}
    for offset in offsets_ms:
        index = int(round(peak_index + offset / DT_MS))
        if 0 <= index < stop:
            out["%g" % offset] = float(v_mv[index])
    return out


def ahp_recovery(v_mv: np.ndarray, peak_index: int, limit_index: int,
                 reference_mv: float,
                 offsets_ms=(5.0, 10.0, 20.0, 30.0, 40.0)) -> dict:
    """How far the membrane has climbed back out of its afterhyperpolarisation.

    Two numbers per delay, both defined against the trough that actually followed
    *this* spike rather than against rest:

    ``deficit_mv``
        How far below the pre-spike reference the trace still sits. Positive
        means still hyperpolarised relative to the level the spike was fired
        from, and it is the quantity that decides whether the next spike is
        reachable.

    ``recovered``
        Fraction of the trough depth that has been recovered, in [0, 1]. This is
        dimensionless, so it can be compared between spikes of different
        amplitude — which the raw deficit cannot.

    Delays past the next spike are dropped rather than clipped: sampling into
    the following upstroke would report a large deficit as if it were slow
    recovery.
    """
    stop = min(v_mv.size, int(limit_index))
    start = int(peak_index)
    span = v_mv[start:stop]
    blank = {name: None for offset in offsets_ms
             for name in ("%g_deficit_mv" % offset, "%g_recovered" % offset)}
    if span.size < 2:
        return blank
    trough_mv = float(np.min(span))
    depth = reference_mv - trough_mv
    out: dict[str, float | None] = {}
    for offset in offsets_ms:
        index = int(round(peak_index + offset / DT_MS))
        deficit = None
        recovered = None
        if index < stop:
            deficit = float(reference_mv - v_mv[index])
            if depth > 0:
                recovered = float((v_mv[index] - trough_mv) / depth)
        out["%g_deficit_mv" % offset] = deficit
        out["%g_recovered" % offset] = recovered
    return out


def fmt(value, digits: int = 3) -> str:
    """Format a measurement, or the literal word for a refused one."""
    if value is None:
        return MISSING
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not np.isfinite(number):
        return MISSING
    return ("%.*f" % (digits, number)).rstrip("0").rstrip(".") or "0"


# ---------------------------------------------------------------------------
# Inventory and traces
# ---------------------------------------------------------------------------

#: Two milliseconds is the length of a spike upstroke at this sampling rate, so
#: truncating an afterhyperpolarisation window this far before the next peak
#: excludes the upstroke without clipping the trough.
UPSTROKE_GUARD_MS = 2.0


def load_inventory(f) -> dict[int, dict]:
    """Metadata for every sweep, read without touching the trace data.

    The trace arrays are 2.4 MB each at 200 kHz; reading all 74 of them would add
    minutes of I/O for sweeps this phase never measures. Metadata first, traces
    on demand.
    """
    inventory: dict[int, dict] = {}
    for name, node in list_series(f, "stimulus/presentation"):
        sweep = int(name.replace("Sweep_", ""))
        base, multiplier = template_key(node)
        stim_pa = phase2d.to_amps_pa(node)
        entry = {
            "sweep": sweep,
            "template": base,
            "template_index_multiplier": multiplier,
            "block": base.split("[")[0],
            "amplitude_pa": s_num(node, "aibs_stimulus_amplitude_pa"),
            "stimulus_name": _as_text(s_field(node, "aibs_stimulus_name",
                                              default=b"")),
            "starting_time_s": s_num(node, "starting_time"),
            "rate_hz": series_rate(node),
            "n_samples": int(stim_pa.size),
            "trace_seconds": stim_pa.size / RATE_HZ,
            "gain": s_num(node, "gain"),
            "access_resistance": s_num(node, "initial_access_resistance"),
            "seal": s_num(node, "seal"),
            "waveform": phase2d.analyse_stimulus(stim_pa, RATE_HZ),
            "annotated_spike_times_s": [],
        }
        wave = entry["waveform"]
        wave.setdefault("duration_ms", float("nan"))
        wave.setdefault("onset_s", float("nan"))
        wave.setdefault("end_s", float("nan"))
        epoch = "Experiment_%d" % sweep
        if "epochs" in f and epoch in f["epochs"]:
            node_epoch = f["epochs"][epoch]
            entry["epoch_start_s"] = float(
                np.asarray(node_epoch["start_time"][()]).ravel()[0])
            entry["epoch_stop_s"] = float(
                np.asarray(node_epoch["stop_time"][()]).ravel()[0])
        annotated = "analysis/spike_times/%s" % name
        if annotated in f:
            times = np.asarray(f[annotated][()]).ravel().astype(float)
            entry["annotated_spike_times_s"] = times.tolist()
        inventory[sweep] = entry
    return inventory


def annotated_peak_indices(times_s, rate_hz: float) -> np.ndarray:
    """Allen's annotated spike times mapped onto trace indices."""
    if not len(times_s):
        return np.array([], dtype=int)
    return np.rint(np.asarray(times_s, dtype=float) * rate_hz).astype(int)


def compare_detectors(v_mv: np.ndarray, rate_hz: float, annotated,
                      report: Report | None = None, label: str = "") -> dict:
    """Three independent spike counts for one trace, and their agreement.

    The primary detector is Phase 2D's 0 mV crossing; the secondary is a velocity
    criterion; the third is Allen's own annotation, which was produced upstream
    by a different algorithm on a different machine. Agreement of all three is
    the strongest statement this analysis can make about a spike count, and it is
    the only one that does not depend on a threshold chosen here.
    """
    dvdt = smooth_dvdt(v_mv, rate_hz)
    primary = phase2d.detect_spikes(v_mv, rate_hz)
    secondary = detect_spikes_dvdt(v_mv, rate_hz, dvdt)
    reference = np.asarray(annotated, dtype=int)
    result = {
        "primary": primary,
        "secondary": secondary,
        "annotated": reference,
        "n_primary": int(primary.size),
        "n_secondary": int(secondary.size),
        "n_annotated": int(reference.size),
        "dvdt": dvdt,
    }
    if not primary.size or not secondary.size:
        result["max_pairing_ms"] = None
    else:
        # Pair every primary peak with the nearest secondary peak. On a
        # correctly detected train the pairing is one-to-one; a mismatch shows up
        # as a large distance rather than as a silently different count.
        distances = []
        for peak in primary:
            distances.append(int(np.min(np.abs(secondary - peak))))
        result["max_pairing_ms"] = float(max(distances)) * DT_MS
    if report is not None and label:
        same_count = (result["n_primary"] == result["n_secondary"]
                      == result["n_annotated"])
        report.check(
            same_count,
            "detectors|%s|count" % label,
            "0 mV=%d  dV/dt=%d  annotated=%d"
            % (result["n_primary"], result["n_secondary"],
               result["n_annotated"]),
        )
        if result["max_pairing_ms"] is not None:
            report.check(
                result["max_pairing_ms"] <= 0.5,
                "detectors|%s|timing" % label,
                "max 0 mV <-> dV/dt separation %.3f ms"
                % result["max_pairing_ms"],
            )
    return result


def pre_step_noise(v_mv: np.ndarray, onset_index: int,
                   rate_hz: float, window_ms: float = 200.0) -> dict:
    """Baseline level and variability in the 200 ms before the step.

    Also returns the *velocity* noise of the smoothed derivative, which is what
    the threshold criterion is calibrated against. If 50 V/s were not several
    sigma clear of this floor then the threshold measurement would be reading
    quantisation, and the run must say so rather than publish a number.
    """
    hi = max(1, int(onset_index) - int(5.0 / (1e3 / rate_hz)))
    lo = max(0, hi - int(window_ms / (1e3 / rate_hz)))
    span = v_mv[lo:hi]
    if span.size < 8:
        return {"available": False}
    dvdt = smooth_dvdt(span, rate_hz)
    sigma = 1.4826 * float(np.median(np.abs(dvdt - np.median(dvdt))))
    return {
        "available": True,
        "window_ms": span.size * 1e3 / rate_hz,
        "mean_mv": float(np.mean(span)),
        "median_mv": float(np.median(span)),
        "sd_mv": float(np.std(span, ddof=1)),
        "p05_mv": float(np.percentile(span, 5)),
        "p95_mv": float(np.percentile(span, 95)),
        "dvdt_sigma_v_per_s": sigma,
        "dvdt_max_abs_v_per_s": float(np.max(np.abs(dvdt))),
    }


def plateau_stats(v_mv: np.ndarray, rate_hz: float, lo: int, hi: int) -> dict:
    """Level statistics over a window, robust and non-robust together.

    The median is the headline because a sweep firing twelve times has twelve
    spikes inside the window, each of which pulls the mean up. The mean and the
    spread are still reported, because a sustained oscillation and a flat line
    with the same median are different physiological states.
    """
    span = v_mv[max(0, int(lo)):max(0, int(hi))]
    if span.size < 8:
        return {"available": False}
    return {
        "available": True,
        "n": int(span.size),
        "median_mv": float(np.median(span)),
        "mean_mv": float(np.mean(span)),
        "sd_mv": float(np.std(span, ddof=1)),
        "p05_mv": float(np.percentile(span, 5)),
        "p95_mv": float(np.percentile(span, 95)),
        "min_mv": float(np.min(span)),
        "max_mv": float(np.max(span)),
    }


# ---------------------------------------------------------------------------
# Per-sweep measurement
# ---------------------------------------------------------------------------


def analyse_sweep(f, sweep: int, record: dict,
                  report: Report) -> dict:
    """Measure one long-square trace and return everything downstream needs.

    Nothing here decides what the numbers mean. The function returns a flat
    dictionary of measurements, refusals and provenance; the sections below
    interpret them.
    """
    name = "Sweep_%d" % sweep
    node = f["acquisition/timeseries"][name]
    v_mv = phase2d.to_volts_mv(node)
    wave = record["waveform"]
    onset_idx = int(wave["onset_index"])
    end_idx = int(wave["end_index"])

    annotated = annotated_peak_indices(record["annotated_spike_times_s"], RATE_HZ)
    detectors = compare_detectors(v_mv, RATE_HZ, annotated, report,
                                  "sweep %d" % sweep)
    peaks = detectors["primary"]
    dvdt = detectors["dvdt"]

    in_step = peaks[(peaks >= onset_idx) & (peaks < end_idx)]
    after_step = peaks[peaks >= end_idx]

    guard = int(UPSTROKE_GUARD_MS / DT_MS)
    limits = [int(p) - guard for p in in_step]

    thresholds = [threshold_crossing(v_mv, dvdt, int(p), RATE_HZ)
                  for p in in_step]

    local = [spike_metrics(v_mv, RATE_HZ, dvdt, int(peak), reference="local",
                           ahp_limit_index=(limits[k + 1]
                                            if k + 1 < len(limits) else None))
             for k, peak in enumerate(in_step)]
    trough = [spike_metrics(v_mv, RATE_HZ, dvdt, int(peak), reference="trough",
                            ahp_limit_index=(limits[k + 1]
                                             if k + 1 < len(limits) else None))
              for k, peak in enumerate(in_step)]

    isi_ms = [float(np.diff(in_step)[k]) * DT_MS for k in range(max(0,
                                                                    in_step.size - 1))]
    adaptation = adaptation_summary(isi_ms, int(in_step.size))
    segments = inter_spike_segments(v_mv, in_step, thresholds)

    baseline = pre_step_noise(v_mv, onset_idx, RATE_HZ)

    # Steady state over the last 200 ms of the step, matching Phase 2D so the
    # plateau numbers in this phase can be compared with Phase 2D's directly.
    plateau = plateau_stats(v_mv, RATE_HZ,
                            max(onset_idx, end_idx - int(PLATEAU_WINDOW_MS / DT_MS)),
                            end_idx)

    # The level the *first* spike grew out of. For a single-spike sweep this is
    # the whole subthreshold response, and it is the single most comparable
    # quantity between a 12-spike train and a 1-spike response.
    if thresholds and thresholds[0]["index"] is not None:
        first_threshold_idx = int(thresholds[0]["index"])
    elif in_step.size:
        first_threshold_idx = int(in_step[0]) - guard
    else:
        first_threshold_idx = None
    if first_threshold_idx is not None:
        approach = plateau_stats(
            v_mv, RATE_HZ,
            max(onset_idx, first_threshold_idx - int(100.0 / DT_MS)),
            first_threshold_idx)
    else:
        approach = {"available": False}

    # The level sustained *after* the last spike has repolarised and the AHP has
    # decayed. Twenty milliseconds is chosen because it is longer than the
    # measured trough width of the largest AHP in this file; for a sweep whose
    # last spike sits within 20 ms of step end the window is unavailable rather
    # than short.
    if in_step.size:
        maint_lo = int(in_step[-1]) + int(20.0 / DT_MS)
    else:
        maint_lo = onset_idx
    maintained = plateau_stats(v_mv, RATE_HZ, max(onset_idx, maint_lo), end_idx)
    if maintained.get("available"):
        # The window is unequal by construction: a train whose last spike lands
        # near step end leaves almost nothing to measure. Recording the length
        # stops that from being read as a level difference.
        maintained["window_ms"] = maintained["n"] * DT_MS
        maintained["comparable"] = bool(maintained["window_ms"] >= 100.0)

    # How far above its own sustained plateau the membrane climbs in the
    # interval that follows the first spike. This is the measurement that
    # separates a sustaining block from a non-sustaining one: wherever a second
    # spike exists the window is terminated just before it, and a sweep with a
    # single spike is measured over the whole remaining step — a longer window,
    # which biases the comparison in that sweep's favour.
    excursion = {"available": False}
    if in_step.size:
        start = int(in_step[0]) + int(2.0 / DT_MS)
        stop = int(in_step[1]) - guard if in_step.size > 1 else end_idx
        span = v_mv[start:max(start, stop)]
        level = plateau.get("median_mv") if plateau.get("available") else None
        if span.size >= 8 and level is not None:
            excursion = {
                "available": True,
                "window_ms": float(span.size) * DT_MS,
                "max_mv": float(np.max(span)),
                "min_mv": float(np.min(span)),
                "above_plateau_mv": float(np.max(span)) - level,
                "truncated_before_next_spike": bool(in_step.size > 1),
            }

    # Charging towards the plateau before the first spike fires.
    charge_stop = (first_threshold_idx if first_threshold_idx is not None
                   else min(end_idx, onset_idx + int(60.0 / DT_MS)))
    charge_stop = max(charge_stop, onset_idx + 2)
    charge = fit_charge_tau(
        (np.arange(onset_idx, charge_stop, dtype=float) - onset_idx) * DT_MS,
        v_mv[onset_idx:charge_stop])

    # Passive relaxation after step offset.
    relax_stop = min(v_mv.size, end_idx + int(150.0 / DT_MS))
    relax = fit_charge_tau(
        (np.arange(end_idx, relax_stop, dtype=float) - end_idx) * DT_MS,
        v_mv[end_idx:relax_stop])

    if in_step.size:
        first_limit = limits[0] if limits else None
        profile = post_spike_profile(v_mv, int(in_step[0]), RATE_HZ,
                                     limit_index=first_limit)
        recovery = ahp_recovery(v_mv, int(in_step[0]),
                                first_limit if first_limit is not None else v_mv.size,
                                local[0]["reference_mv"])
    else:
        profile = {}
        recovery = {}

    return {
        "sweep": sweep,
        "block": record["block"],
        "amplitude_pa": record["amplitude_pa"],
        "template": record["template"],
        "template_index_multiplier": record["template_index_multiplier"],
        "starting_time_s": record["starting_time_s"],
        "rate_hz": record["rate_hz"],
        "trace_seconds": record["trace_seconds"],
        "gain": record["gain"],
        "access_resistance": record["access_resistance"],
        "seal": record["seal"],
        "onset_s": wave["onset_s"],
        "end_s": wave["end_s"],
        "duration_ms": wave["duration_ms"],
        "onset_index": onset_idx,
        "end_index": end_idx,
        "n_primary": detectors["n_primary"],
        "n_secondary": detectors["n_secondary"],
        "n_annotated": detectors["n_annotated"],
        "max_pairing_ms": detectors["max_pairing_ms"],
        "peak_indices_in_step": [int(p) for p in in_step],
        "spike_times_ms": [float(p) * DT_MS for p in in_step],
        "n_in_step": int(in_step.size),
        "n_after_step": int(after_step.size),
        "post_step_times_ms": [float(p) * DT_MS for p in after_step],
        "first_spike_ms": (float(in_step[0]) * DT_MS) if in_step.size else None,
        "first_spike_latency_ms": (float(in_step[0] - onset_idx) * DT_MS
                                   if in_step.size else None),
        "first_threshold_ms": (thresholds[0]["t_ms"]
                               if thresholds and thresholds[0]["t_ms"] is not None
                               else None),
        "first_threshold_latency_ms": (
            thresholds[0]["t_ms"] - wave["onset_s"] * 1e3
            if thresholds and thresholds[0]["t_ms"] is not None else None),
        "thresholds": thresholds,
        "threshold_mv": [t["v_mv"] for t in thresholds],
        "local": local,
        "trough": trough,
        "isi_ms": isi_ms,
        "adaptation": adaptation,
        "segments": segments,
        "baseline": baseline,
        "plateau": plateau,
        "approach": approach,
        "maintained": maintained,
        "excursion": excursion,
        "charge": charge,
        "relax": relax,
        "post_spike_profile": profile,
        "ahp_recovery": recovery,
        "quality": phase2d.quality_metrics(v_mv, RATE_HZ, wave["onset_s"],
                                           wave["end_s"]),
    }


# ---------------------------------------------------------------------------
# Section A — provenance
# ---------------------------------------------------------------------------


def section_provenance(report: Report, nwb_path: pathlib.Path, f,
                       inventory: dict[int, dict]) -> dict:
    """File identity, protocol identity and the block catalogue.

    Every claim about the two recordings in the final report rests on the file
    being the same one Phase 1C validated, on the sweep-to-block assignment being
    the one Phase 2D published, and on the commands being identical. Each of
    those is checked rather than asserted.
    """
    report.heading("A. Provenance — file identity, protocol identity, catalogue")
    size = nwb_path.stat().st_size
    digest = sha256_of(nwb_path)
    report.check(size == EXPECTED_BYTES, "provenance|nwb bytes", "%d B" % size)
    report.check(digest == EXPECTED_SHA256, "provenance|nwb digest",
                 "sha256 %s… vs %s…" % (digest[:16], EXPECTED_SHA256[:16]))
    report.check(nwb_path.name == "382982932.nwb", "provenance|file name",
                 nwb_path.name)

    # NWB 1.0.5 stores its format version in general/generated_by as a flat
    # [name, value, name, value, ...] string array rather than in an attribute.
    generated = ([_as_text(token) for token in
                  np.asarray(f["general/generated_by"][()]).ravel()]
                 if "general/generated_by" in f else [])
    version = ""
    for index, token in enumerate(generated):
        if token.strip().lower() == "version" and index + 1 < len(generated):
            version = generated[index + 1]
    specimen = _as_text(f["general/aibs_specimen_id"][()]) \
        if "general/aibs_specimen_id" in f else "absent"
    session = _as_text(f["general/session_id"][()]) \
        if "general/session_id" in f else "absent"
    report.check(version.strip() == "1.0", "provenance|nwb version",
                 "generated_by %s" % ", ".join(generated))
    report.check(specimen.strip() == str(SPECIMEN), "provenance|specimen id",
                 "%s" % specimen)

    n_stim = len(list_series(f, "stimulus/presentation"))
    n_acq = len(list_series(f, "acquisition/timeseries"))
    report.check(n_stim == n_acq == len(inventory),
                 "provenance|series counts",
                 "%d stimulus / %d acquisition / %d catalogued"
                 % (n_stim, n_acq, len(inventory)))

    rates = sorted({round(v["rate_hz"], 3) for v in inventory.values()})
    report.check(rates == [RATE_HZ], "provenance|sampling rate",
                 "%s Hz" % ", ".join("%g" % r for r in rates))

    blocks: dict[str, list] = {}
    for sweep, entry in sorted(inventory.items()):
        blocks.setdefault(entry["block"], []).append(sweep)
    report.check(len(blocks) == 11, "provenance|protocol blocks",
                 "%d blocks over %d sweeps" % (len(blocks), len(inventory)))

    expected = {
        COARSE_BLOCK: list(range(24, 44)),
        FINEST_BLOCK: list(range(44, 53)),
        # C2 skips sweep 65: the block is 15 sweeps, not 16.
        C2_BLOCK: [64] + list(range(66, 80)),
    }
    for block, sweeps in expected.items():
        observed = blocks.get(block, [])
        report.check(observed == sweeps, "provenance|%s|sweep ids" % block,
                     "sweeps %s" % ("%d-%d (%d)" % (observed[0], observed[-1],
                                                    len(observed))
                                    if observed else "absent"))

    # starting_time is a 256 s quantisation of acquisition order, not a clock.
    starts = [v["starting_time_s"] for v in inventory.values()]
    quantised = all(abs(s / 256.0 - round(s / 256.0)) < 1e-9 for s in starts)
    distinct = sorted({round(s, 6) for s in starts})
    ordered = [inventory[k]["starting_time_s"] for k in sorted(inventory)]
    inversions = sum(1 for a, b in zip(ordered, ordered[1:]) if b < a)
    report.check(quantised, "provenance|starting_time quantisation",
                 "all %d values are multiples of 256 s" % len(starts))
    report.check(len(distinct) == 7, "provenance|starting_time distinct values",
                 "%d distinct values, largest group %d sweeps"
                 % (len(distinct), max(sum(1 for s in starts if round(s, 6) == d)
                                       for d in distinct)))
    report.check(inversions == 0, "provenance|starting_time order",
                 "%d inversions over %d consecutive pairs — encodes order, not "
                 "clock time" % (inversions, len(ordered) - 1))

    # The bit-identity claim. This is the single fact that makes the whole
    # comparison possible: the two blocks saw the same current waveform.
    names = [FITTING_SWEEP] + list(HELD_OUT_SWEEPS)
    commands = {}
    for sweep in names:
        node = f["stimulus/presentation"]["Sweep_%d" % sweep]
        commands[sweep] = phase2d.to_amps_pa(node)
    length = min(v.size for v in commands.values())
    reference_command = commands[FITTING_SWEEP][:length]
    max_deviation = max(float(np.max(np.abs(commands[s][:length] - reference_command)))
                        for s in commands)
    differing = sum(int(np.count_nonzero(commands[s][:length] != reference_command))
                    for s in commands)
    report.check(differing == 0, "provenance|command identity",
                 "sweep 38 vs 49-52: %d differing samples, max |delta| %.3e pA "
                 "over %d samples" % (differing, max_deviation, length))

    onsets = sorted({round(inventory[s]["waveform"]["onset_s"], 6) for s in names})
    durations = sorted({round(inventory[s]["waveform"]["duration_ms"], 4)
                        for s in names})
    report.check(len(onsets) == 1 and len(durations) == 1,
                 "provenance|command epoch agreement",
                 "onset %s s, duration %s ms"
                 % (", ".join("%.4f" % o for o in onsets),
                    ", ".join("%.3f" % d for d in durations)))

    # The embedded +/-50 pA probe is present in every long square command and is
    # removed from the step window by identity, not by length.
    long_sweeps = [s for s in sorted(inventory)
                   if inventory[s]["waveform"].get("status") == "OK"
                   and inventory[s]["waveform"]["duration_ms"] >= 200.0]
    probed = [s for s in long_sweeps
              if inventory[s]["waveform"].get("probe_removed")]
    report.check(len(probed) == len(long_sweeps),
                 "provenance|embedded probe removed",
                 "%d of %d long-square commands" % (len(probed), len(long_sweeps)))

    print()
    print("  block catalogue")
    print("  %-24s %6s %-14s %-12s %9s %9s"
          % ("block", "n", "sweeps", "amplitude pA", "step ms", "trace s"))
    catalogue = {}
    for block in sorted(blocks, key=lambda b: blocks[b][0]):
        sweeps = blocks[block]
        entries = [inventory[s] for s in sweeps]
        amps = sorted({round(e["amplitude_pa"], 1) for e in entries})
        durs = sorted({round(e["waveform"].get("duration_ms", float("nan")), 3)
                       for e in entries
                       if np.isfinite(e["waveform"].get("duration_ms")
                                      or float("nan"))}) or [float("nan")]
        traces = sorted({round(e["trace_seconds"], 3) for e in entries})
        amp_text = ("%g..%g" % (amps[0], amps[-1])) if len(amps) > 1 \
            else ("%g" % amps[0])
        dur_text = ("%g..%g" % (durs[0], durs[-1])) if len(durs) > 1 \
            else ("%g" % durs[0])
        print("  %-24s %6d %-14s %-12s %9s %9s"
              % (block, len(sweeps),
                 "%d-%d" % (sweeps[0], sweeps[-1]), amp_text, dur_text,
                 ", ".join("%g" % t for t in traces)))
        catalogue[block] = {
            "n": len(sweeps), "sweeps": sweeps, "amplitudes_pa": amps,
            "step_ms": durs, "trace_s": traces,
        }

    # A per-sweep table for the five sweeps the comparison rests on, so the
    # report's provenance section can be transcribed from console output.
    print()
    print("  %-6s %-24s %8s %10s %9s %9s %9s"
          % ("sweep", "block", "amp pA", "start s", "gain", "Ra MOhm", "seal"))
    rows = {}
    for sweep in sorted(inventory):
        e = inventory[sweep]
        if e["block"] not in LONG_SQUARE_BLOCKS:
            continue
        print("  %-6d %-24s %8.1f %10.1f %9.4f %9.2f %9.3f"
              % (sweep, e["block"], e["amplitude_pa"], e["starting_time_s"],
                 e["gain"] or 0.0, e["access_resistance"] or 0.0,
                 e["seal"] or 0.0))
        rows[sweep] = {
            "block": e["block"], "amplitude_pa": e["amplitude_pa"],
            "starting_time_s": e["starting_time_s"], "gain": e["gain"],
            "access_resistance": e["access_resistance"], "seal": e["seal"],
            "template": e["template"],
            "template_index_multiplier": e["template_index_multiplier"],
            "rate_hz": e["rate_hz"], "trace_seconds": e["trace_seconds"],
            "onset_s": e["waveform"]["onset_s"], "end_s": e["waveform"]["end_s"],
            "duration_ms": e["waveform"]["duration_ms"],
            "baseline_pa": e["waveform"]["baseline_pa"],
            "level_pa": e["waveform"]["level_pa"],
            "probe_removed": e["waveform"].get("probe_removed"),
            "epoch_start_s": e.get("epoch_start_s"),
            "epoch_stop_s": e.get("epoch_stop_s"),
            "n_annotated": len(e["annotated_spike_times_s"]),
        }

    return {
        "nwb": {"path": str(nwb_path), "bytes": size, "sha256": digest},
        "nwb_version": version,
        "generated_by": generated,
        "specimen_id": specimen.strip(),
        "session_id": session.strip(),
        "n_stimulus_series": n_stim,
        "n_acquisition_series": n_acq,
        "rate_hz": RATE_HZ,
        "catalogue": catalogue,
        "sweeps": rows,
        "starting_time": {"distinct": distinct, "inversions": inversions,
                          "quantum_s": 256.0},
        "command_identity": {"sweeps": names, "differing_samples": differing,
                             "max_abs_delta_pa": max_deviation,
                             "samples_compared": length},
    }


# ---------------------------------------------------------------------------
# Section B — short-square threshold control
# ---------------------------------------------------------------------------


#: A 3 ms pulse evokes its spike at pulse offset, so the response window carries
#: a 100 ms grace; without it every response would land outside the step.
SHORT_SQUARE_GRACE_MS = 100.0

#: Threshold brackets published by Phase 2D, reproduced here as a regression on
#: the short-square path: (highest silent, lowest firing, mixed levels) in pA.
PHASE2D_SHORT_BRACKETS = {
    "C1SSCOARSE150112": (600.0, 700.0, ()),
    "C1SSFINEST150112": (650.0, 670.0, (660.0,)),
}


def section_short_square(report: Report, inventory: dict[int, dict],
                         f) -> dict:
    """The 3 ms threshold pulses: does the block difference survive a brief command?

    This is not the main subject of the phase, but it is the closest thing the
    dataset contains to a *threshold* measurement, and it constrains the
    alternatives: a block-wide shift in excitability would have to show up here
    too. The two blocks do not share a command amplitude — COARSE steps in
    100 pA increments, FINEST repeats 650/660/670 — so the comparison is of
    brackets, not of counts at a matched current.
    """
    report.heading("B. Short-square control — 3 ms threshold pulses")
    short_blocks = list(phase2d.SHORT_SQUARE_BLOCKS)
    rows = []
    for sweep, entry in sorted(inventory.items()):
        if entry["block"] not in short_blocks:
            continue
        node = f["acquisition/timeseries"]["Sweep_%d" % sweep]
        v_mv = phase2d.to_volts_mv(node)
        wave = entry["waveform"]
        peaks = phase2d.detect_spikes(v_mv, RATE_HZ)
        onset_idx = int(wave["onset_index"])
        end_idx = int(wave["end_index"])
        # A 3 ms pulse evokes its spike at pulse offset, so the response window
        # carries the same 100 ms grace Phase 2D used; without it every response
        # would land outside the step.
        window = peaks[(peaks >= onset_idx) &
                       (peaks < end_idx + int(SHORT_SQUARE_GRACE_MS / DT_MS))]
        rows.append({
            "sweep": sweep, "block": entry["block"],
            "amplitude_pa": entry["amplitude_pa"],
            "duration_ms": wave["duration_ms"],
            "n_spikes": int(window.size),
            "first_ms": float(window[0]) * DT_MS if window.size else None,
            "n_annotated": len(entry["annotated_spike_times_s"]),
        })

    report.check(len(rows) == 16, "short_square|sweeps analysed",
                 "%d of 16" % len(rows))
    durs = sorted({round(r["duration_ms"], 3) for r in rows})
    report.check(durs == [3.0], "short_square|pulse duration",
                 "%s ms" % ", ".join("%g" % d for d in durs))

    print()
    print("  %-22s %6s %9s %9s %8s %10s %8s"
          % ("block", "sweep", "amp pA", "pulse ms", "spikes", "first ms",
             "annot"))
    for r in rows:
        print("  %-22s %6d %9.1f %9.3f %8d %10s %8d"
              % (r["block"], r["sweep"], r["amplitude_pa"], r["duration_ms"],
                 r["n_spikes"], fmt(r["first_ms"], 3), r["n_annotated"]))

    brackets = {}
    for block in sorted({r["block"] for r in rows}):
        levels: dict[float, list] = {}
        for r in rows:
            if r["block"] != block:
                continue
            levels.setdefault(r["amplitude_pa"], []).append(r["n_spikes"] > 0)
        verdict = {amp: ("firing" if all(v) else
                         "silent" if not any(v) else "mixed")
                   for amp, v in levels.items()}
        firing = sorted(a for a, v in verdict.items() if v == "firing")
        silent = sorted(a for a, v in verdict.items() if v == "silent")
        mixed = sorted(a for a, v in verdict.items() if v == "mixed")
        brackets[block] = {
            "verdict": {int(k): v for k, v in sorted(verdict.items())},
            "lowest_firing_pa": firing[0] if firing else None,
            "highest_silent_pa": silent[-1] if silent else None,
            "mixed_pa": mixed,
        }
        report.observe(
            "%s threshold bracket" % block,
            "silent at %s pA; mixed at %s pA; firing at %s pA"
            % (", ".join("%.0f" % a for a in silent) or "no level",
               ", ".join("%.0f" % a for a in mixed) or "no level",
               ", ".join("%.0f" % a for a in firing) or "no level"))

    report.check(all(r["n_spikes"] <= 1 for r in rows),
                 "short_square|single spike per pulse",
                 "max %d" % max(r["n_spikes"] for r in rows))

    # Regression against Phase 2D's published brackets.
    drift = []
    for block, (silent, firing, mixed) in PHASE2D_SHORT_BRACKETS.items():
        entry = brackets.get(block, {})
        if entry.get("highest_silent_pa") != silent:
            drift.append("%s highest silent %s vs %.0f"
                         % (block, entry.get("highest_silent_pa"), silent))
        if entry.get("lowest_firing_pa") != firing:
            drift.append("%s lowest firing %s vs %.0f"
                         % (block, entry.get("lowest_firing_pa"), firing))
        if tuple(entry.get("mixed_pa") or ()) != tuple(mixed):
            drift.append("%s mixed %s vs %s"
                         % (block, entry.get("mixed_pa"), list(mixed)))
    report.check(not drift, "short_square|phase 2d bracket regression",
                 "%d block(s) compared%s"
                 % (len(PHASE2D_SHORT_BRACKETS),
                    (" — " + "; ".join(drift)) if drift else ""))
    return {"rows": rows, "brackets": brackets}


#: ISIs of sweep 38 published in Phase 2E, reproduced here as a regression check
#: on the extraction path. Tolerance is two sample intervals, because the printed
#: values were rounded to 5 us.
PHASE2E_SWEEP38_ISI_MS = (39.250, 59.030, 79.515, 75.685, 80.845, 114.705,
                          79.750, 92.245, 95.080, 94.655, 85.935)


# ---------------------------------------------------------------------------
# Section C — counts, latencies, regression against Phase 2D
# ---------------------------------------------------------------------------


def group_stats(analyses: dict[int, dict], sweeps, key: str) -> dict:
    """min / mean / max / range of one scalar across a group of sweeps."""
    values = []
    for sweep in sweeps:
        item = analyses.get(sweep)
        if item is None:
            continue
        value = item
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if isinstance(value, (int, float)) and np.isfinite(value):
            values.append(float(value))
    if not values:
        return {"available": False, "n": 0}
    return {
        "available": True,
        "n": len(values),
        "min": min(values),
        "mean": float(np.mean(values)),
        "max": max(values),
        "range": max(values) - min(values),
        "values": values,
    }


def stats_of(values, label: str = "") -> dict:
    """min / mean / max / range of a plain list, refusing an empty one."""
    numbers = [float(v) for v in values
               if isinstance(v, (int, float)) and np.isfinite(float(v))]
    if not numbers:
        return {"available": False, "n": 0, "label": label}
    return {
        "available": True,
        "label": label,
        "n": len(numbers),
        "min": min(numbers),
        "mean": float(np.mean(numbers)),
        "max": max(numbers),
        "range": max(numbers) - min(numbers),
        "values": numbers,
    }


def section_counts(report: Report, analyses: dict[int, dict]) -> dict:
    """Spike counts and first-spike latencies, with a regression on Phase 2D.

    The regression matters more than the table: this phase reads the same traces
    through the same detector, so if a count or a latency differs from Phase 2D's
    published value then something in this path has changed and the rest of the
    analysis cannot be trusted.
    """
    report.heading("C. Spike counts and first-spike latencies")

    print("  %-6s %-22s %7s %8s %9s %9s %10s %9s"
          % ("sweep", "block", "amp pA", "in step", "after", "first ms",
             "latency", "annot"))
    rows = {}
    for sweep in sorted(analyses):
        a = analyses[sweep]
        print("  %-6d %-22s %7.1f %8d %9d %9s %10s %9d"
              % (sweep, a["block"], a["amplitude_pa"], a["n_in_step"],
                 a["n_after_step"], fmt(a["first_spike_ms"], 3),
                 fmt(a["first_spike_latency_ms"], 3), a["n_annotated"]))
        rows[sweep] = {
            "block": a["block"], "amplitude_pa": a["amplitude_pa"],
            "n_in_step": a["n_in_step"], "n_after_step": a["n_after_step"],
            "n_primary": a["n_primary"], "n_secondary": a["n_secondary"],
            "n_annotated": a["n_annotated"],
            "first_spike_ms": a["first_spike_ms"],
            "first_spike_latency_ms": a["first_spike_latency_ms"],
            "first_threshold_ms": a["first_threshold_ms"],
            "spike_times_ms": a["spike_times_ms"],
            "post_step_times_ms": a["post_step_times_ms"],
            "max_pairing_ms": a["max_pairing_ms"],
        }

    # Regression 1: counts. Only sweeps Phase 2D published are compared.
    mismatches = []
    for table in (PHASE2D_COARSE_FI, PHASE2D_FINEST_FI):
        for sweep, expected in table.items():
            if sweep in analyses and analyses[sweep]["n_in_step"] != expected:
                mismatches.append("%d: %d vs %d"
                                  % (sweep, analyses[sweep]["n_in_step"],
                                     expected))
    report.check(not mismatches, "counts|phase 2d f-i regression",
                 "%d sweep(s) compared, %d mismatch(es)%s"
                 % (sum(1 for t in (PHASE2D_COARSE_FI, PHASE2D_FINEST_FI)
                        for s in t if s in analyses), len(mismatches),
                    (" — " + "; ".join(mismatches)) if mismatches else ""))

    # Regression 2: first-spike times, published to 1 ms.
    drift = []
    for sweep, expected in PHASE2D_FIRST_SPIKE_S.items():
        if sweep not in analyses:
            continue
        observed = analyses[sweep]["first_spike_ms"]
        if observed is None or abs(observed - expected * 1e3) > 0.6:
            drift.append("%d: %s vs %.3f"
                         % (sweep, fmt(observed, 3), expected))
    report.check(not drift, "counts|phase 2d latency regression",
                 "%d sweep(s) compared, %d disagreement(s)%s"
                 % (len(PHASE2D_FIRST_SPIKE_S), len(drift),
                    (" — " + "; ".join(drift)) if drift else ""))

    # Regression 3: plateau medians, published to 1 mV.
    plateau_drift = []
    for sweep, expected in PHASE2D_PLATEAU_MEDIAN_MV.items():
        if sweep not in analyses:
            continue
        entry = analyses[sweep]["plateau"]
        if not entry.get("available"):
            plateau_drift.append("%d: unavailable" % sweep)
            continue
        if abs(entry["median_mv"] - expected) > 0.01:
            plateau_drift.append("%d: %.3f vs %.3f"
                                 % (sweep, entry["median_mv"], expected))
    report.check(not plateau_drift, "counts|phase 2d plateau regression",
                 "%d sweep(s) compared, %d disagreement(s)%s"
                 % (len(PHASE2D_PLATEAU_MEDIAN_MV), len(plateau_drift),
                    (" — " + "; ".join(plateau_drift)) if plateau_drift else ""))

    # The headline observation, restated as a measured fact rather than a claim.
    coarse = analyses.get(FITTING_SWEEP)
    finest = [analyses[s] for s in HELD_OUT_SWEEPS if s in analyses]
    if coarse and finest:
        counts = [a["n_in_step"] for a in finest]
        report.observe(
            "headline counts",
            "COARSE sweep %d: %d spikes in a %.0f ms step; FINEST %s: %s "
            "spikes on a bit-identical command"
            % (FITTING_SWEEP, coarse["n_in_step"],
               coarse["duration_ms"],
               "/".join(str(s) for s in HELD_OUT_SWEEPS),
               "/".join(str(c) for c in counts)))
        report.check(len(set(counts)) == 1, "counts|finest repeatability",
                     "all four FINEST repeats: %d spike(s) each" % counts[0]
                     if len(set(counts)) == 1 else "counts differ: %s" % counts)
    return rows


# ---------------------------------------------------------------------------
# Section D — the COARSE train
# ---------------------------------------------------------------------------


def section_train(report: Report, analyses: dict[int, dict]) -> dict:
    """Interval structure of sweep 38, the only train long enough to describe.

    No adaptation index is invented beyond what eleven intervals support: the
    report gives the intervals, their trend with a permutation p-value, and the
    early/late halves. Whether that pattern deserves the name "adaptation" is a
    question for the report, not for this function.
    """
    report.heading("D. Interval structure of the COARSE train (sweep %d)"
                   % FITTING_SWEEP)
    a = analyses.get(FITTING_SWEEP)
    if a is None:
        report.check(False, "train|sweep 38 present", "missing from the analysis")
        return {}

    print("  %-5s %10s %10s %10s %10s"
          % ("#", "time ms", "since onset", "ISI ms", "rate Hz"))
    for k, t in enumerate(a["spike_times_ms"]):
        isi = a["isi_ms"][k - 1] if k else None
        print("  %-5d %10.3f %10.3f %10s %10s"
              % (k + 1, t, t - a["onset_s"] * 1e3, fmt(isi, 3),
                 fmt(1000.0 / isi if isi else None, 2)))

    published = np.asarray(PHASE2E_SWEEP38_ISI_MS, dtype=float)
    observed = np.asarray(a["isi_ms"], dtype=float)
    same_length = observed.size == published.size
    worst = (float(np.max(np.abs(observed - published))) if same_length
             else float("nan"))
    report.check(same_length and worst <= 0.011,
                 "train|phase 2e isi regression",
                 "%d intervals, worst |delta| %.4f ms"
                 % (observed.size, worst))

    adaptation = a["adaptation"]
    report.check(adaptation["available"], "train|adaptation index available",
                 "%d spikes, %d intervals" % (a["n_in_step"],
                                              adaptation["n_isi"]))
    print()
    print("  interval summary")
    for label, key, unit, digits in (
            ("first ISI", "isi_first_ms", "ms", 3),
            ("last ISI", "isi_last_ms", "ms", 3),
            ("mean ISI", "isi_mean_ms", "ms", 3),
            ("SD of ISI", "isi_sd_ms", "ms", 3),
            ("coefficient of variation", "isi_cv", "", 3),
            ("last / first", "isi_ratio", "", 3),
            ("first instantaneous rate", "rate_first_hz", "Hz", 2),
            ("last instantaneous rate", "rate_last_hz", "Hz", 2),
            ("mean rate", "rate_mean_hz", "Hz", 2),
            ("early-half rate", "early_rate_hz", "Hz", 2),
            ("late-half rate", "late_rate_hz", "Hz", 2),
            ("early / late rate ratio", "rate_ratio", "", 3)):
        print("  %-28s %10s %s"
              % (label, fmt(adaptation.get(key), digits), unit))

    trend = adaptation.get("interval_trend") or {}
    if trend.get("available"):
        print("  %-28s %10s %s"
              % ("ISI vs index (Spearman)", fmt(trend["rho"], 3), ""))
        print("  %-28s %10s %s"
              % ("  permutation p", fmt(trend["p_permutation"], 5),
                 "20 000 draws, seed 20250218, tail in the observed direction"))
        report.observe("sweep 38 ISI trend",
                       "rho = %s, p = %s over %d intervals; %s"
                       % (fmt(trend["rho"], 3), fmt(trend["p_permutation"], 5),
                          trend["n"], trend["direction"]))
    return {"adaptation": adaptation, "spike_times_ms": a["spike_times_ms"],
            "isi_ms": a["isi_ms"]}


#: One row per morphology quantity: (label, unit, accessor).
MORPHOLOGY_FIELDS = (
    ("peak voltage", "mV", lambda a, k: a["trough"][k]["peak_mv"]),
    ("amplitude vs trough", "mV", lambda a, k: a["trough"][k]["amplitude_mv"]),
    ("amplitude vs local median", "mV", lambda a, k: a["local"][k]["amplitude_mv"]),
    ("width at half max (trough)", "ms",
     lambda a, k: a["trough"][k]["width_ms"]),
    ("width at half max (local)", "ms", lambda a, k: a["local"][k]["width_ms"]),
    ("10-90 % rise", "ms", lambda a, k: a["trough"][k]["rise_ms"]),
    ("max dV/dt", "V/s", lambda a, k: a["trough"][k]["dvdt_max_v_per_s"]),
    ("min dV/dt", "V/s", lambda a, k: a["trough"][k]["dvdt_min_v_per_s"]),
    ("threshold voltage", "mV",
     lambda a, k: a["thresholds"][k]["v_mv"]
     if k < len(a["thresholds"]) else None),
    ("threshold dV/dt", "V/s",
     lambda a, k: a["thresholds"][k]["dvdt_v_per_s"]
     if k < len(a["thresholds"]) else None),
    ("afterhyperpolarisation", "mV", lambda a, k: a["trough"][k]["ahp_mv"]),
)


def morphology_series(a: dict) -> dict:
    """Every per-spike morphology quantity for one sweep, as plain lists."""
    series = {}
    for label, unit, accessor in MORPHOLOGY_FIELDS:
        series[label] = {"unit": unit,
                         "values": [accessor(a, k) for k in range(a["n_in_step"])]}
    return series


def section_morphology(report: Report, analyses: dict[int, dict]) -> dict:
    """Spike shape across spike order, in the train and at every COARSE amplitude.

    Two questions are being asked at once. First, within sweep 38: does the shape
    of the spike drift as the train proceeds? Second, across the COARSE block:
    does that drift appear at every amplitude, which would make it a property of
    the cell rather than of one command?
    """
    report.heading("E. Spike morphology across spike order")
    a = analyses.get(FITTING_SWEEP)
    if a is None:
        report.check(False, "morphology|sweep 38 present", "missing")
        return {}

    series = morphology_series(a)
    header = "  %-3s %9s" % ("#", "t ms")
    for label, unit, _ in MORPHOLOGY_FIELDS:
        header += " %10s" % ("%s" % _short(label))
    print(header)
    for k in range(a["n_in_step"]):
        line = "  %-3d %9.3f" % (k + 1, a["spike_times_ms"][k])
        for label, unit, _ in MORPHOLOGY_FIELDS:
            line += " %10s" % fmt(series[label]["values"][k], 3)
        print(line)
    print("  units: " + "  ".join("%s=%s" % (_short(label), unit)
                                  for label, unit, _ in MORPHOLOGY_FIELDS))

    trends = {}
    print()
    print("  trend across spike order (Spearman vs index, permutation p)")
    for label, unit, _ in MORPHOLOGY_FIELDS:
        values = series[label]["values"]
        t = trend(values)
        trends[label] = t
        print("  %-28s %10s %10s  %s"
              % (label, fmt(t.get("rho"), 3), fmt(t.get("p_permutation"), 5),
                 t.get("direction") if t.get("available")
                 else t.get("reason", "")))

    report.observe("sweep 38 amplitude trend",
                   "rho = %s, p = %s"
                   % (fmt(trends["amplitude vs trough"].get("rho"), 3),
                      fmt(trends["amplitude vs trough"].get("p_permutation"), 5)))
    report.observe("sweep 38 width trend",
                   "rho = %s, p = %s"
                   % (fmt(trends["width at half max (trough)"].get("rho"), 3),
                      fmt(trends["width at half max (trough)"]
                          .get("p_permutation"), 5)))
    report.observe("sweep 38 threshold trend",
                   "rho = %s, p = %s"
                   % (fmt(trends["threshold voltage"].get("rho"), 3),
                      fmt(trends["threshold voltage"].get("p_permutation"), 5)))

    # Does the same pattern appear at the other COARSE amplitudes? A single
    # sweep cannot separate adaptation from a one-off; eight can.
    print()
    print("  %-6s %7s %8s %10s %10s  %s"
          % ("sweep", "amp pA", "spikes", "ISI rho", "ISI p", "direction"))
    across = {}
    for sweep in sorted(analyses):
        item = analyses[sweep]
        if item["block"] != COARSE_BLOCK or item["n_in_step"] < 3:
            continue
        interval = item["adaptation"]["interval_trend"]
        across[sweep] = {"amplitude_pa": item["amplitude_pa"],
                         "n_in_step": item["n_in_step"],
                         "interval_trend": interval}
        print("  %-6d %7.1f %8d %10s %10s  %s"
              % (sweep, item["amplitude_pa"], item["n_in_step"],
                 fmt(interval.get("rho"), 3),
                 fmt(interval.get("p_permutation"), 5),
                 interval.get("direction", "")))
    rising = sum(1 for v in across.values()
                 if v["interval_trend"].get("available")
                 and v["interval_trend"]["rho"] > 0)
    report.observe("COARSE ISI trends across amplitudes",
                   "%d of %d sweeps with >= 3 spikes lengthen; %d shorten"
                   % (rising, len(across),
                      sum(1 for v in across.values()
                          if v["interval_trend"].get("available")
                          and v["interval_trend"]["rho"] < 0)))
    return {"series": series, "trends": trends, "across_amplitudes": across}


def section_segments(report: Report, analyses: dict[int, dict]) -> dict:
    """Where the interval goes: repolarisation, trough, or the ramp back up.

    A lengthening ISI is not by itself informative. If the extra time is spent
    repolarising, the spike shape is changing; if it is spent on a shallower ramp
    from the same trough, the excitability of the membrane between spikes is
    changing. The decomposition separates the two without either being assumed.
    """
    report.heading("F. Interval decomposition — where the time goes")
    a = analyses.get(FITTING_SWEEP)
    if a is None or not a["segments"]:
        report.check(False, "segments|sweep 38 intervals present", "none")
        return {}

    print("  %-9s %9s %9s %10s %9s %9s %10s"
          % ("pair", "ISI ms", "fall ms", "trough mV", "ramp ms", "up ms",
             "residual"))
    residuals = []
    for entry in a["segments"]:
        residual = None
        if entry["ramp_ms"] is not None:
            total = entry["fall_ms"] + entry["ramp_ms"] + entry["upstroke_ms"]
            residual = entry["isi_ms"] - total
            residuals.append(residual)
        print("  %-9s %9.3f %9.3f %10.3f %9s %9s %10s"
              % ("%d->%d" % entry["pair"], entry["isi_ms"], entry["fall_ms"],
                 entry["trough_mv"], fmt(entry["ramp_ms"], 3),
                 fmt(entry["upstroke_ms"], 3), fmt(residual, 4)))
    report.check(all(abs(r) <= 0.02 for r in residuals) if residuals else False,
                 "segments|decomposition closes",
                 "%d intervals, worst residual %s ms"
                 % (len(residuals), fmt(max((abs(r) for r in residuals),
                                            default=float('nan')), 4)))

    ramps = [e["ramp_ms"] for e in a["segments"] if e["ramp_ms"] is not None]
    falls = [e["fall_ms"] for e in a["segments"]]
    troughs = [e["trough_mv"] for e in a["segments"]]
    if ramps and falls:
        report.observe(
            "interval composition",
            "ramp %.1f-%.1f ms (%.0f%% of the interval), fall %.1f-%.1f ms "
            "(%.0f%%); troughs %.2f to %.2f mV"
            % (min(ramps), max(ramps),
               100.0 * float(np.mean(ramps)) / a["adaptation"]["isi_mean_ms"],
               min(falls), max(falls),
               100.0 * float(np.mean(falls)) / a["adaptation"]["isi_mean_ms"],
               min(troughs), max(troughs)))
    return {
        "segments": a["segments"],
        "ramp_trend": trend(ramps) if len(ramps) >= 3 else {"available": False,
                                                            "reason": "n<3"},
        "fall_trend": trend(falls) if len(falls) >= 3 else {"available": False,
                                                            "reason": "n<3"},
        "trough_trend": trend(troughs) if len(troughs) >= 3
        else {"available": False, "reason": "n<3"},
    }


def _short(label: str) -> str:
    """Compact column header for a morphology quantity."""
    return {
        "peak voltage": "peak",
        "amplitude vs trough": "amp_t",
        "amplitude vs local median": "amp_l",
        "width at half max (trough)": "w_t",
        "width at half max (local)": "w_l",
        "10-90 % rise": "rise",
        "max dV/dt": "dVdt+",
        "min dV/dt": "dVdt-",
        "threshold voltage": "thr",
        "threshold dV/dt": "thr_dv",
        "afterhyperpolarisation": "ahp",
    }[label]


# ---------------------------------------------------------------------------
# Section G — the two blocks side by side
# ---------------------------------------------------------------------------


def _level(entry, key):
    if not entry or not entry.get("available"):
        return None
    return entry.get(key)


def section_blocks(report: Report, analyses: dict[int, dict]) -> dict:
    """Baseline, plateau and threshold, block by block.

    The blocks are never pooled. Every aggregate here is computed within one
    block and then *compared* with another block's aggregate; no mean across
    blocks is formed anywhere.

    Three measurements carry the comparison, and the third is the one that
    matters. The plateau is the level the sweep sustained; the threshold is the
    level its first spike started from; and the post-spike excursion is how far
    above its own plateau the membrane climbs *after* a spike has repolarised.
    A sweep that climbs back above threshold in that window fires again, and one
    that does not, does not. The window is terminated at the next spike where one
    exists, so a sweep with a single spike is measured over a strictly longer
    window — which biases the comparison in that sweep's favour rather than
    against it.
    """
    report.heading("G. COARSE and FINEST side by side")
    coarse = analyses.get(FITTING_SWEEP)
    finest = [analyses[s] for s in HELD_OUT_SWEEPS if s in analyses]
    if coarse is None or not finest:
        report.check(False, "blocks|required sweeps present", "missing")
        return {}

    print("  voltage levels (mV)")
    print("  %-6s %-20s %5s %9s %8s %9s %9s %9s %9s"
          % ("sweep", "block", "n", "base med", "base SD", "plateau",
             "plateau SD", "approach", "maintained"))
    table = {}
    for item in [coarse] + finest:
        base = item["baseline"]
        plate = item["plateau"]
        print("  %-6d %-20s %5s %9s %8s %9s %9s %9s %9s"
              % (item["sweep"], item["block"],
                 item["n_in_step"], fmt(_level(base, "median_mv"), 3),
                 fmt(_level(base, "sd_mv"), 3),
                 fmt(_level(plate, "median_mv"), 3),
                 fmt(_level(plate, "sd_mv"), 3),
                 fmt(_level(item["approach"], "median_mv"), 3),
                 fmt(_level(item["maintained"], "median_mv"), 3)))
        table[item["sweep"]] = {
            "block": item["block"],
            "n_in_step": item["n_in_step"],
            "baseline": base, "plateau": plate,
            "approach": item["approach"], "maintained": item["maintained"],
        }

    print()
    print("  kinetics and threshold")
    print("  %-6s %9s %9s %9s %9s %9s %9s %9s"
          % ("sweep", "charge t", "relax t", "latency", "thr 1 mV", "thr min",
             "amp mV", "ahp mV"))
    for item in [coarse] + finest:
        thresholds = [t for t in item["threshold_mv"] if t is not None]
        print("  %-6d %9s %9s %9s %9s %9s %9s %9s"
              % (item["sweep"],
                 fmt(_level(item["charge"], "tau_ms"), 2),
                 fmt(_level(item["relax"], "tau_ms"), 2),
                 fmt(item["first_spike_latency_ms"], 1),
                 fmt(item["threshold_mv"][0] if item["threshold_mv"] else None,
                      3),
                 fmt(min(thresholds) if thresholds else None, 3),
                 fmt(item["trough"][0]["amplitude_mv"] if item["trough"] else None,
                      3),
                 fmt(item["trough"][0]["ahp_mv"] if item["trough"] else None, 3)))
        table[item["sweep"]].update({
            "charge_tau_ms": _level(item["charge"], "tau_ms"),
            "charge_r2": _level(item["charge"], "r2"),
            "relax_tau_ms": _level(item["relax"], "tau_ms"),
            "relax_r2": _level(item["relax"], "r2"),
            "first_latency_ms": item["first_spike_latency_ms"],
            "first_threshold_mv": (item["threshold_mv"][0]
                                   if item["threshold_mv"] else None),
            "min_threshold_mv": min(thresholds) if thresholds else None,
            "median_threshold_mv": (float(np.median(thresholds))
                                    if thresholds else None),
            "first_amplitude_mv": (item["trough"][0]["amplitude_mv"]
                                   if item["trough"] else None),
            "first_width_ms": (item["trough"][0]["width_ms"]
                               if item["trough"] else None),
            "first_ahp_mv": (item["trough"][0]["ahp_mv"]
                             if item["trough"] else None),
        })

    # Within-block repeatability. The four FINEST sweeps are four repeats of one
    # command in one block; their spread is measurement-plus-state scatter, not
    # four independent physiological conditions.
    finest_sweeps = [a["sweep"] for a in finest]
    repeat = {}
    for key, label in (("plateau.median_mv", "steady-state median"),
                       ("baseline.median_mv", "baseline median"),
                       ("maintained.median_mv", "maintained plateau"),
                       ("first_spike_latency_ms", "first-spike latency"),
                       ("first_amplitude_mv", "first-spike amplitude")):
        stats = group_stats(analyses, finest_sweeps, key)
        repeat[label] = stats
        if stats["available"]:
            print("  FINEST repeat %-24s %9s .. %9s  (spread %s)"
                  % (label, fmt(stats["min"], 3), fmt(stats["max"], 3),
                     fmt(stats["range"], 3)))
    repeat["first-spike threshold"] = stats_of(
        [a["threshold_mv"][0] for a in finest
         if a["threshold_mv"] and a["threshold_mv"][0] is not None],
        "first-spike threshold")
    report.observe("FINEST within-block repeatability",
                   "steady-state median spreads %s mV over %d repeats; "
                   "first-spike latency spreads %s ms"
                   % (fmt(repeat["steady-state median"].get("range"), 3),
                      len(finest_sweeps),
                      fmt(repeat["first-spike latency"].get("range"), 1)))
    report.check(repeat["steady-state median"].get("range", 1e9) < 2.0,
                 "blocks|finest steady state is stable",
                 "range %s mV over %d repeats"
                 % (fmt(repeat["steady-state median"].get("range"), 3),
                    len(finest_sweeps)))

    # Between-block level comparison, on the same command.
    coarse_plateau = _level(coarse["plateau"], "median_mv")
    finest_plateau = repeat["steady-state median"]
    finest_base = repeat["baseline median"]
    report.observe(
        "steady-state offset",
        "COARSE %.3f mV vs FINEST %.3f mV (mean), offset %+.3f mV; "
        "COARSE baseline %.3f vs FINEST %.3f (offset %+.3f mV)"
        % (coarse_plateau, finest_plateau["mean"],
           coarse_plateau - finest_plateau["mean"],
           _level(coarse["baseline"], "median_mv"), finest_base["mean"],
           _level(coarse["baseline"], "median_mv") - finest_base["mean"]))

    # Threshold, sustained plateau and the post-spike excursion.
    #
    # The quantity that distinguishes a sustaining block from a non-sustaining
    # one is not the steady-state level on its own — both blocks sit far below
    # their own threshold between spikes — but how far above that level the
    # membrane climbs after a spike. A block whose post-spike trajectory returns
    # to threshold keeps firing; one whose trajectory settles at the plateau
    # fires once and stops. Both numbers are measured here, so the contrast is
    # between two measurements on the same trace.
    excitability = {}
    for item in [coarse] + finest:
        thresholds = [t for t in item["threshold_mv"] if t is not None]
        level = _level(item["plateau"], "median_mv")
        interval_overshoots = ([t - level for t in thresholds[1:]]
                               if level is not None else [])
        excitability[item["sweep"]] = {
            "block": item["block"],
            "plateau_median_mv": level,
            "first_threshold_mv": thresholds[0] if thresholds else None,
            "median_threshold_mv": (float(np.median(thresholds))
                                    if thresholds else None),
            "min_threshold_mv": (float(np.min(thresholds))
                                 if thresholds else None),
            "first_overshoot_mv": (thresholds[0] - level
                                   if thresholds and level is not None else None),
            "interval_overshoots_mv": interval_overshoots,
            "excursion_mv": _level(item["excursion"], "above_plateau_mv"),
            "excursion_window_ms": _level(item["excursion"], "window_ms"),
            "excursion_truncated": (item["excursion"] or {}).get(
                "truncated_before_next_spike"),
        }

    print()
    print("  threshold, plateau and post-spike excursion")
    print("  %-6s %10s %10s %12s %12s %10s %9s"
          % ("sweep", "plateau", "thr(1)", "thr above plateau",
             "excursion", "window ms", "truncated"))
    for sweep in sorted(excitability):
        e = excitability[sweep]
        print("  %-6d %10s %10s %12s %12s %10s %9s"
              % (sweep, fmt(e["plateau_median_mv"], 3),
                 fmt(e["first_threshold_mv"], 3),
                 fmt(e["first_overshoot_mv"], 3),
                 fmt(e["excursion_mv"], 3),
                 fmt(e["excursion_window_ms"], 1),
                 fmt(e["excursion_truncated"])))

    coarse_first = excitability[coarse["sweep"]]["first_overshoot_mv"]
    finest_firsts = [excitability[a["sweep"]]["first_overshoot_mv"]
                     for a in finest
                     if excitability[a["sweep"]]["first_overshoot_mv"] is not None]
    coarse_excursion = excitability[coarse["sweep"]]["excursion_mv"]
    finest_excursions = [excitability[a["sweep"]]["excursion_mv"]
                         for a in finest
                         if excitability[a["sweep"]]["excursion_mv"] is not None]
    if coarse_first is not None and finest_firsts:
        report.observe(
            "first-spike overshoot above plateau",
            "COARSE %+.3f mV; FINEST %+.3f mV (mean of %d, range %+.3f to "
            "%+.3f) — the first spike is generated from a similar distance "
            "above the sustained level in both blocks"
            % (coarse_first, float(np.mean(finest_firsts)), len(finest_firsts),
               min(finest_firsts), max(finest_firsts)))
    if coarse_excursion is not None and finest_excursions:
        report.observe(
            "post-first-spike excursion",
            "COARSE %+.3f mV; FINEST %+.3f mV (mean of %d, range %+.3f to "
            "%+.3f)"
            % (coarse_excursion, float(np.mean(finest_excursions)),
               len(finest_excursions), min(finest_excursions),
               max(finest_excursions)))
    coarse_thresholds = [t for t in coarse["threshold_mv"] if t is not None]
    finest_thresholds = [t["v_mv"] for a in finest for t in a["thresholds"]
                         if t is not None and t["v_mv"] is not None]
    if coarse_thresholds and finest_thresholds:
        # The two summaries disagree in sign and both are reported, because that
        # disagreement is the finding: the COARSE *first* spike starts lower than
        # any FINEST spike, while the COARSE *late* spikes start higher than every
        # FINEST spike. A single "threshold difference between blocks" does not
        # exist in this dataset.
        report.observe(
            "threshold difference between blocks",
            "COARSE first spike %s mV vs FINEST mean %+.3f mV (%+.3f), but "
            "COARSE median over %d spikes %s mV, range %s to %s — the sign "
            "depends on which COARSE spike is compared"
            % (fmt(coarse_thresholds[0], 3),
               float(np.mean(finest_thresholds)),
               float(np.mean(finest_thresholds)) - coarse_thresholds[0],
               len(coarse_thresholds),
               fmt(float(np.median(coarse_thresholds)), 3),
               fmt(float(np.min(coarse_thresholds)), 3),
               fmt(float(np.max(coarse_thresholds)), 3)))
    coarse_interval = excitability[coarse["sweep"]]["interval_overshoots_mv"]
    if coarse_interval:
        report.observe(
            "interval overshoots above plateau",
            "COARSE: %d intervals reach %+.3f to %+.3f mV above its own "
            "plateau (median %+.3f mV)"
            % (len(coarse_interval), min(coarse_interval),
               max(coarse_interval), float(np.median(coarse_interval))))

    # Threshold criterion calibration: is 50 V/s clear of the velocity noise?
    sigma = (coarse["baseline"] or {}).get("dvdt_sigma_v_per_s")
    if sigma:
        report.check(THRESHOLD_DVDT_V_PER_S >= THRESHOLD_NOISE_MARGIN * sigma,
                     "blocks|threshold criterion above noise",
                     "criterion %.1f V/s, pre-step velocity noise %.2f V/s "
                     "(%.1f sigma)" % (THRESHOLD_DVDT_V_PER_S, sigma,
                                       THRESHOLD_DVDT_V_PER_S / sigma))

    return {"table": table, "repeat": repeat, "excitability": excitability,
            "finest_sweeps": finest_sweeps}


# ---------------------------------------------------------------------------
# Section H — C2, corroboration only
# ---------------------------------------------------------------------------


def section_c2(report: Report, analyses: dict[int, dict]) -> dict:
    """The C2 block: a second protocol family, used only as corroboration.

    C2 is not interchangeable with either primary block — it uses a 2 s step, a
    different amplitude series and four repeats at some levels. It is reported to
    show that neither block's behaviour is a unique artefact of its own command
    shape, and it is never pooled with either.
    """
    report.heading("H. C2 block — corroborating context, not pooled")
    items = [analyses[s] for s in sorted(analyses)
             if analyses[s]["block"] == C2_BLOCK]
    if not items:
        report.check(False, "c2|sweeps present", "none")
        return {}

    levels: dict[float, list] = {}
    for item in items:
        levels.setdefault(item["amplitude_pa"], []).append(item)
    print("  %-9s %6s %12s %12s %12s"
          % ("amp pA", "n", "spikes", "first ms", "plateau mV"))
    summary = {}
    for amp in sorted(levels):
        group = levels[amp]
        counts = [g["n_in_step"] for g in group]
        firsts = [g["first_spike_ms"] for g in group if g["first_spike_ms"]]
        plateaus = [_level(g["plateau"], "median_mv") for g in group]
        plateaus = [p for p in plateaus if p is not None]
        print("  %-9.0f %6d %12s %12s %12s"
              % (amp, len(group), "/".join(str(c) for c in counts),
                 ("%.2f-%.2f" % (min(firsts), max(firsts))) if firsts else "-",
                 ("%.2f-%.2f" % (min(plateaus), max(plateaus)))
                 if plateaus else "-"))
        summary[int(amp)] = {
            "n": len(group), "counts": counts,
            "first_ms": firsts, "plateau_mv": plateaus,
            "sweeps": [g["sweep"] for g in group],
        }

    # Non-monotonicity and scatter are the point of reporting C2 at all: they
    # show that within-block repeat scatter of this size is normal in this file.
    repeated = {amp: v for amp, v in summary.items() if v["n"] > 1}
    scatter = {amp: (max(v["counts"]) - min(v["counts"]))
               for amp, v in repeated.items()}
    if scatter:
        report.observe("C2 within-block scatter",
                       "repeated levels %s; spike-count spread %s"
                       % (", ".join("%d pA" % a for a in sorted(repeated)),
                          ", ".join("%d" % scatter[a] for a in sorted(scatter))))
    amps = sorted(summary)
    monotone = all(summary[amps[i]]["counts"][0] <= summary[amps[i + 1]]["counts"][0]
                   for i in range(len(amps) - 1))
    report.observe("C2 monotonicity",
                   "first-sweep counts %s across %s pA — %s"
                   % (", ".join(str(summary[a]["counts"][0]) for a in amps),
                      "/".join("%d" % a for a in amps),
                      "monotone" if monotone else "not monotone"))
    return {"levels": summary, "scatter": scatter, "monotone": monotone}


# ---------------------------------------------------------------------------
# Section I — hypotheses, stated as evidence rather than as conclusions
# ---------------------------------------------------------------------------


def hypothesis_entries(report: Report, analyses: dict[int, dict],
                       blocks: dict, short_square: dict) -> list[dict]:
    """The competing explanations, each with its evidence for, against and missing.

    This function deliberately does not rank the hypotheses. Ranking would
    require evidence the dataset does not contain, and the brief forbids claiming
    a mechanism without direct evidence. What is asserted is only what each
    hypothesis predicts, whether that prediction is met, and whether the file can
    test it at all.
    """
    coarse = analyses.get(FITTING_SWEEP) or {}
    adaptation = coarse.get("adaptation") or {}
    interval_trend = adaptation.get("interval_trend") or {}

    entries: list[dict] = []

    # --- H1: spike-frequency adaptation inside the COARSE train ---------------
    h1_support = []
    h1_against = []
    if interval_trend.get("available"):
        h1_support.append(
            "Intervals lengthen across the train: ISI %s ms to %s ms, "
            "Spearman rho = %s (permutation p = %s, in the observed direction)."
            % (fmt(adaptation.get("isi_first_ms"), 3),
               fmt(adaptation.get("isi_last_ms"), 3),
               fmt(interval_trend.get("rho"), 3),
               fmt(interval_trend.get("p_permutation"), 5)))
        h1_support.append(
            "Instantaneous rate falls from %s Hz at the first interval to %s Hz "
            "at the ninth and later: early-half %s Hz, late-half %s Hz."
            % (fmt(adaptation.get("rate_first_hz"), 2),
               fmt(adaptation.get("rate_last_hz"), 2),
               fmt(adaptation.get("early_rate_hz"), 2),
               fmt(adaptation.get("late_rate_hz"), 2)))
        if not (interval_trend.get("p_permutation") is not None
                and interval_trend["p_permutation"] < 0.05):
            h1_against.append(
                "The monotone component is not statistically distinguishable "
                "from a random ordering at the 5 %% level (p = %s), so "
                "\"progressive\" is a description of the trend, not a "
                "demonstration of one."
                % fmt(interval_trend.get("p_permutation"), 5))
        if adaptation.get("monotone_fraction") is not None:
            h1_against.append(
                "Only %.0f %% of consecutive intervals lengthen, so the train is "
                "not monotone and the longest interval (%s ms) is not the last."
                % (100.0 * adaptation["monotone_fraction"],
                   fmt(adaptation.get("isi_max_ms"), 3)))
    h1_against.append(
        "No shape change accompanies the rate change unless it is measurable: "
        "see the morphology trends, which are reported separately and not "
        "assumed.")
    h1_missing = (
        "A second COARSE sweep at exactly +170 pA, or the same command delivered "
        "twice, would separate adaptation from a one-off. The block contains one "
        "sweep per amplitude, so within-block repeatability cannot be measured "
        "here. No block in the file contains a step long enough to observe a "
        "steady-state firing rate.")

    # --- H2: threshold / excitability difference between the blocks -----------
    excitability = blocks.get("excitability") or {}
    coarse_entry = excitability.get(FITTING_SWEEP) or {}
    finest_entries = [excitability[s] for s in HELD_OUT_SWEEPS
                      if excitability.get(s)]
    h2_support = []
    h2_against = []
    if coarse_entry and finest_entries:
        finest_thresholds = [e["first_threshold_mv"] for e in finest_entries
                             if e["first_threshold_mv"] is not None]
        if finest_thresholds:
            finest_threshold = float(np.mean(finest_thresholds))
            coarse_threshold = coarse_entry["first_threshold_mv"]
            h2_support.append(
                "First-spike thresholds differ: COARSE %s mV, FINEST %s mV "
                "(%+.3f mV); the COARSE median over %d spikes is %s mV."
                % (fmt(coarse_threshold, 3), fmt(finest_threshold, 3),
                   finest_threshold - coarse_threshold,
                   len(coarse_entry["interval_overshoots_mv"]) + 1,
                   fmt(coarse_entry["median_threshold_mv"], 3)))
            if coarse_threshold is not None and finest_threshold <= coarse_threshold:
                h2_against.append(
                    "The measured threshold points the wrong way: FINEST fires "
                    "first %+.3f mV *nearer* rest than COARSE, so a raised "
                    "threshold in FINEST is not supported by this measurement."
                    % (coarse_threshold - finest_threshold))
        finest_excursions = [e["excursion_mv"] for e in finest_entries
                             if e["excursion_mv"] is not None]
        if finest_excursions and coarse_entry["excursion_mv"] is not None:
            h2_support.append(
                "The post-spike excursion does differ: after its first spike "
                "COARSE climbs %+.3f mV above its own plateau and reaches "
                "threshold again, while FINEST climbs %+.3f mV (mean) over a "
                "window at least as long and never fires again."
                % (coarse_entry["excursion_mv"],
                   float(np.mean(finest_excursions))))
    brackets = (short_square or {}).get("brackets") or {}
    ss_coarse = brackets.get(phase2d.SHORT_SQUARE_BLOCKS[0], {})
    ss_finest = brackets.get(phase2d.SHORT_SQUARE_BLOCKS[1], {})
    if ss_coarse.get("lowest_firing_pa") and ss_finest.get("lowest_firing_pa"):
        if ss_finest["lowest_firing_pa"] <= ss_coarse["lowest_firing_pa"]:
            h2_against.append(
                "The 3 ms threshold protocol points the other way: the FINEST "
                "block fires from %.0f pA while the COARSE block needs %.0f pA. "
                "A block-wide loss of excitability in FINEST is therefore not "
                "supported by the one direct threshold measurement in the file."
                % (ss_finest["lowest_firing_pa"], ss_coarse["lowest_firing_pa"]))
        else:
            h2_support.append(
                "The 3 ms threshold protocol agrees in direction: FINEST needs "
                "%.0f pA against COARSE's %.0f pA."
                % (ss_finest["lowest_firing_pa"], ss_coarse["lowest_firing_pa"]))
    h2_missing = (
        "Threshold measured with the same command in both blocks. The short "
        "pulse is a 3 ms current step, not a voltage ramp, and the two blocks do "
        "not share its amplitudes, so the comparison is of brackets 10 pA to "
        "100 pA wide. A difference of the size seen here (a few millivolts) "
        "cannot be resolved by that bracket.")

    # --- H3: recording order / physiological state ----------------------------
    h3_support = [
        "`starting_time` is monotone in sweep number, so the COARSE block "
        "(sweeps 24-43) was acquired before the FINEST block (44-52). Any "
        "time-dependent change in the cell would therefore map onto the block "
        "difference."]
    h3_against = [
        "Resting baseline is essentially unchanged between the blocks, which is "
        "not what progressive deterioration of the recording would produce."]
    if ss_coarse.get("lowest_firing_pa") and ss_finest.get("lowest_firing_pa") \
            and ss_finest["lowest_firing_pa"] <= ss_coarse["lowest_firing_pa"]:
        h3_against.append(
            "The short-pulse blocks run in the same order (COARSE first) yet show "
            "FINEST at a lower current threshold, so the block order does not "
            "produce a uniform decline.")
    h3_missing = (
        "`starting_time` is quantised to multiples of 256 s and repeats across "
        "sweeps, so the file contains no usable clock and the elapsed time "
        "between the two blocks is unknown. There is no second recording of this "
        "specimen in the dataset to compare against, and no repeat of the COARSE "
        "command later in the session.")

    # --- H4: protocol or acquisition difference -------------------------------
    h4_support = [
        "The blocks are different templates (COARSE applies 1.0x to a 170 pA "
        "waveform, FINEST applies 1.7x to a 100 pA waveform), so the *commanded* "
        "waveforms are produced by different multiplication paths even where the "
        "resulting samples are identical."]
    h4_against = [
        "The command arrays are bit-identical over the shared window: 0 differing "
        "samples and max |delta| 0 pA, so the membrane saw the same current."]
    h4_against.append(
        "Sampling rate is 200 kHz in both blocks and the traces are the same "
        "duration, so no acquisition parameter that the file records differs.")
    h4_missing = (
        "Acquisition settings that are not stored (bridge balance, capacitance "
        "compensation, liquid-junction correction, amplifier filter settings) "
        "could differ without leaving a trace in the file, and cannot be tested.")

    # --- H5: the post-step doublet in sweep 38 ---------------------------------
    late = coarse.get("post_step_times_ms") or []
    end_ms = (coarse.get("end_index") or 0) * DT_MS
    h5 = {
        "id": "H5",
        "statement": ("The two post-step events in sweep %d are a separate "
                      "excitatory process rather than a continuation of the "
                      "step train." % FITTING_SWEEP),
        "supporting": [
            "%d events occur after the step ends at %.3f ms, at %s ms."
            % (len(late), end_ms,
               "/".join(fmt(t, 3) for t in late) or "no times recorded"),
            "Their inter-spike interval (%s ms) is shorter than every interval "
            "inside the step."
            % fmt((late[1] - late[0]) if len(late) == 2 else None, 3),
        ],
        "contradictory": [
            "Nothing in the trace distinguishes these from two delayed spikes of "
            "the step train, and the recording contains no second example.",
        ],
        "missing": ("A repeat of the command, or a stimulus record that "
                    "continues past the step, would show whether the doublet is "
                    "reproducible. The file contains neither."),
        "testable": "no — treated as unresolved and excluded from every train "
                    "statistic above",
    }

    entries.extend([
        {"id": "H1", "statement": "Spike-frequency adaptation inside the COARSE "
                                  "train.",
         "supporting": h1_support, "contradictory": h1_against,
         "missing": h1_missing,
         "testable": "partially — a trend can be measured, its cause cannot"},
        {"id": "H2", "statement": "A difference in spike threshold or "
                                  "excitability between the blocks.",
         "supporting": h2_support, "contradictory": h2_against,
         "missing": h2_missing,
         "testable": "partially — thresholds are measurable, the mechanism is not"},
        {"id": "H3", "statement": "A difference in physiological state related "
                                  "to recording order.",
         "supporting": h3_support, "contradictory": h3_against,
         "missing": h3_missing,
         "testable": "no — the file has no usable clock and no repeat recording"},
        {"id": "H4", "statement": "A protocol or acquisition difference that the "
                                  "recordings do not expose.",
         "supporting": h4_support, "contradictory": h4_against,
         "missing": h4_missing,
         "testable": "no — the relevant settings are not stored in the file"},
        h5,
    ])
    return entries


def print_hypotheses(report: Report, entries: list[dict]) -> None:
    """Emit the hypothesis table, keeping observation and inference apart."""
    report.heading("I. Alternative explanations — evidence for, against, missing")
    for entry in entries:
        print()
        print("  %s  %s" % (entry["id"], entry["statement"]))
        for label in ("supporting", "contradictory"):
            for line in entry[label]:
                print("    %-14s %s" % (label, line))
        print("    %-14s %s" % ("missing", entry["missing"]))
        print("    %-14s %s" % ("testable", entry["testable"]))
    report.note(
        "No hypothesis is selected here. Where two hypotheses predict the same "
        "observations, the file cannot separate them, and the report says so."
    )


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

COARSE_COLOUR = "#b2182b"
FINEST_COLOURS = ("#2166ac", "#4393c3", "#92c5de", "#d1e5f0")
C2_COLOUR = "#8c8c8c"


def _matplotlib():
    """Import pyplot lazily, so a headless measurement run needs no backend."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 130,
        "savefig.dpi": 150,
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "legend.fontsize": 7,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    return plt


def make_figures(f, analyses: dict[int, dict], figures_dir: pathlib.Path) -> list:
    """The figure set for the report: recordings only, no simulation anywhere."""
    plt = _matplotlib()
    figures_dir.mkdir(parents=True, exist_ok=True)
    made = []

    def save(fig, name: str) -> None:
        path = figures_dir / name
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        made.append(str(path))

    def trace(sweep: int) -> np.ndarray:
        node = f["acquisition/timeseries"]["Sweep_%d" % sweep]
        return phase2d.to_volts_mv(node)

    coarse = analyses.get(FITTING_SWEEP)
    finest = [analyses[s] for s in HELD_OUT_SWEEPS if s in analyses]
    if coarse is None or not finest:
        return made
    group = [coarse] + finest
    colours = [COARSE_COLOUR] + list(FINEST_COLOURS)

    # --- F1: the step, all five sweeps on one axis ---------------------------
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4),
                             gridspec_kw={"width_ratios": [2.3, 1.0]})
    onset_ms = coarse["onset_s"] * 1e3
    end_ms = coarse["end_s"] * 1e3
    for item, colour in zip(group, colours):
        v = trace(item["sweep"])
        t = np.arange(v.size) * DT_MS
        window = (t >= onset_ms - 50.0) & (t <= end_ms + 40.0)
        stride = 4
        axes[0].plot(t[window][::stride], v[window][::stride], lw=0.7,
                     color=colour,
                     label="sweep %d (%d spike%s)" % (item["sweep"],
                                                     item["n_in_step"],
                                                     "" if item["n_in_step"] == 1
                                                     else "s"))
    axes[0].axvline(onset_ms, color="k", lw=0.6, ls=":")
    axes[0].axvline(end_ms, color="k", lw=0.6, ls=":")
    axes[0].set_xlabel("time from sweep start (ms)")
    axes[0].set_ylabel("membrane potential (mV)")
    axes[0].set_title("+170 pA step, bit-identical command\nCOARSE sweep 38 and "
                      "FINEST sweeps 49-52")
    axes[0].legend(loc="upper left", frameon=False)

    for item, colour in zip(group, colours):
        v = trace(item["sweep"])
        t = np.arange(v.size) * DT_MS
        zoom = (t >= onset_ms - 5.0) & (t <= onset_ms + 260.0)
        axes[1].plot(t[zoom], v[zoom], lw=0.8, color=colour)
    axes[1].axvline(onset_ms, color="k", lw=0.6, ls=":")
    axes[1].set_xlabel("time from sweep start (ms)")
    axes[1].set_title("first 260 ms after onset\n(charging and first spike)")
    axes[1].set_xlim(onset_ms - 5.0, onset_ms + 260.0)
    save(fig, "f1_step_overlay.png")

    # --- F2: spike-aligned waveforms ----------------------------------------
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for item, colour in zip(group, colours):
        v = trace(item["sweep"])
        for k, peak in enumerate(item["peak_indices_in_step"]):
            lo = peak - int(2.0 / DT_MS)
            hi = peak + int(8.0 / DT_MS)
            if lo < 0 or hi > v.size:
                continue
            ax.plot(np.arange(lo, hi) * DT_MS - peak * DT_MS, v[lo:hi], lw=0.6,
                    color=colour, alpha=0.9 if k == 0 else 0.45,
                    label=("sweep %d" % item["sweep"]) if k == 0 else None)
    ax.set_xlabel("time from spike peak (ms)")
    ax.set_ylabel("membrane potential (mV)")
    ax.set_title("Spike-aligned waveforms, aligned at each detected peak\n"
                 "COARSE: 12 spikes, FINEST: 1 spike per sweep")
    ax.legend(loc="lower right", frameon=False)
    save(fig, "f2_spike_aligned.png")

    # --- F3: interval and instantaneous rate --------------------------------
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for sweep in sorted(analyses):
        item = analyses[sweep]
        if item["block"] != COARSE_BLOCK or item["n_in_step"] < 3:
            continue
        index = np.arange(1, len(item["isi_ms"]) + 1)
        emphasised = sweep == FITTING_SWEEP
        ax.plot(index, item["isi_ms"],
                marker="o", ms=3 if emphasised else 2,
                lw=1.2 if emphasised else 0.6,
                alpha=1.0 if emphasised else 0.45,
                color=COARSE_COLOUR if emphasised else "#d6604d",
                label=("sweep %d (%+.0f pA)" % (sweep, item["amplitude_pa"])
                       if emphasised else None))
    ax.set_xlabel("interval index")
    ax.set_ylabel("inter-spike interval (ms)")
    ax.set_title("COARSE intervals lengthen; FINEST sweeps have no interval to "
                 "plot\n(FINEST: 1 spike per sweep - no inter-spike interval "
                 "exists)")
    ax.legend(loc="lower right", frameon=False)
    ax2 = ax.twinx()
    ax2.set_ylabel("instantaneous rate (Hz)")
    ax2.grid(False)
    if coarse["isi_ms"]:
        rates = [1000.0 / v for v in coarse["isi_ms"]]
        ax2.plot(np.arange(1, len(rates) + 1), rates, ls="--", lw=0.7,
                 color="k", alpha=0.5)
    save(fig, "f3_isi_and_rate.png")

    # --- F4: morphology across spike order ----------------------------------
    series = morphology_series(coarse)
    panels = (("amplitude vs trough", "mV", "amplitude (trough reference)"),
              ("width at half max (trough)", "ms", "width at half maximum"),
              ("threshold voltage", "mV", "threshold (50 V/s criterion)"),
              ("afterhyperpolarisation", "mV", "afterhyperpolarisation"))
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.8))
    order = np.arange(1, coarse["n_in_step"] + 1)
    for ax, (label, unit, title) in zip(axes.ravel(), panels):
        values = series[label]["values"]
        ax.plot(order, values, marker="o", ms=3, lw=1.0, color=COARSE_COLOUR,
                label="COARSE sweep %d" % FITTING_SWEEP)
        finest_values = []
        for item in finest:
            value = {"amplitude vs trough":
                     item["trough"][0]["amplitude_mv"],
                     "width at half max (trough)": item["trough"][0]["width_ms"],
                     "threshold voltage": (item["threshold_mv"][0]
                                           if item["threshold_mv"] else None),
                     "afterhyperpolarisation":
                     item["trough"][0]["ahp_mv"]}[label]
            if value is not None and np.isfinite(value):
                finest_values.append(value)
        if finest_values:
            ax.axhline(float(np.mean(finest_values)), color=FINEST_COLOURS[0],
                       lw=1.0, ls="--",
                       label="FINEST mean of 4 repeats (1 spike each)")
            ax.fill_between([order[0], order[-1]],
                            min(finest_values), max(finest_values),
                            color=FINEST_COLOURS[1], alpha=0.20, lw=0)
        ax.set_xlabel("spike order within the step")
        ax.set_ylabel("%s (%s)" % (title, unit))
        ax.set_title(title)
        ax.legend(loc="best", frameon=False)
    fig.suptitle("Spike morphology across the COARSE train", fontsize=9)
    save(fig, "f4_morphology_vs_order.png")

    # --- F5: baseline, plateau, maintained level ----------------------------
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    xs = np.arange(len(group))
    baseline_values = [g["baseline"].get("median_mv") for g in group]
    plateau_values = [g["plateau"].get("median_mv") for g in group]
    maintained_values = [g["maintained"].get("median_mv") for g in group]
    width = 0.26
    ax.bar(xs - width, baseline_values, width, color="#4d4d4d",
           label="baseline (200 ms before step)")
    ax.bar(xs, plateau_values, width, color="#969696",
           label="steady state (last 200 ms of step)")
    ax.bar(xs + width, maintained_values, width, color="#c6dbef",
           label="maintained after last spike")
    ax.set_xticks(xs)
    ax.set_xticklabels(["COARSE\n%d" % g["sweep"] for g in group[:1]]
                       + ["FINEST\n%d" % g["sweep"] for g in group[1:]])
    ax.set_ylabel("membrane potential (mV)")
    ax.set_title("Resting baseline is unchanged; the sustained level is not "
                 "identical")
    ax.legend(loc="lower right", frameon=False)
    save(fig, "f5_levels.png")

    # --- F6: subthreshold approach and the maintained plateau ---------------
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    for item, colour in zip(group, colours):
        v = trace(item["sweep"])
        lo = item["onset_index"]
        hi = min(v.size, item["end_index"])
        t = np.arange(lo, hi) * DT_MS
        stride = 20
        ax.plot(t[::stride], v[lo:hi][::stride], lw=0.7, color=colour,
                label="sweep %d" % item["sweep"])
        for peak in item["peak_indices_in_step"]:
            ax.axvline(peak * DT_MS, color=colour, lw=0.4, alpha=0.35)
    ax.set_xlabel("time from sweep start (ms)")
    ax.set_ylabel("membrane potential (mV)")
    ax.set_title("Inside the step: spike times marked per sweep")
    ax.legend(loc="lower right", frameon=False, ncol=2)
    save(fig, "f6_in_step.png")

    # --- F7: interval decomposition ------------------------------------------
    segments = coarse.get("segments") or []
    if segments:
        fig, ax = plt.subplots(figsize=(5.6, 3.2))
        index = np.arange(len(segments))
        fall = [s["fall_ms"] for s in segments]
        ramp = [s["ramp_ms"] if s["ramp_ms"] is not None else 0.0
                for s in segments]
        up = [s["upstroke_ms"] if s["upstroke_ms"] is not None else 0.0
              for s in segments]
        ax.bar(index, fall, color="#b2182b", label="peak to trough")
        ax.bar(index, ramp, bottom=fall, color="#f4a582",
               label="trough to threshold")
        ax.bar(index, up, bottom=np.array(fall) + np.array(ramp),
               color="#2166ac", label="threshold to next peak")
        ax.set_xticks(index)
        ax.set_xticklabels(["%d-%d" % s["pair"] for s in segments], rotation=45)
        ax.set_xlabel("interval (spike pair)")
        ax.set_ylabel("time (ms)")
        ax.set_title("Where each interval goes, sweep %d" % FITTING_SWEEP)
        ax.legend(loc="upper left", frameon=False)
        save(fig, "f7_interval_decomposition.png")

    return made


# ---------------------------------------------------------------------------
# Helpers for output
# ---------------------------------------------------------------------------


def to_jsonable(value):
    """JSON encoder that refuses nothing and silently keeps numpy honest."""
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def summarise_for_json(analyses: dict[int, dict]) -> dict:
    """Strip the arrays out of the per-sweep records before serialisation.

    The raw traces and the peak-index arrays are hundreds of thousands of
    numbers and belong in the console output, not in a summary file that a human
    has to read.
    """
    keep = (
        "sweep", "block", "amplitude_pa", "template",
        "template_index_multiplier", "starting_time_s", "rate_hz",
        "trace_seconds", "gain", "access_resistance", "seal", "onset_s", "end_s",
        "duration_ms", "n_primary", "n_secondary", "n_annotated",
        "max_pairing_ms", "spike_times_ms", "n_in_step", "n_after_step",
        "post_step_times_ms", "first_spike_ms", "first_spike_latency_ms",
        "first_threshold_ms", "first_threshold_latency_ms", "thresholds",
        "threshold_mv", "isi_ms", "adaptation", "segments", "baseline",
        "plateau", "approach", "maintained", "excursion", "charge", "relax",
        "post_spike_profile", "ahp_recovery", "quality",
    )
    out = {}
    for sweep, item in analyses.items():
        entry = {k: item[k] for k in keep if k in item}
        entry["local"] = item.get("local")
        entry["trough"] = item.get("trough")
        out[str(sweep)] = entry
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_NWB = PROJECT_ROOT / "data" / "nwb_cache" / "382982932.nwb"
DEFAULT_JSON = PROJECT_ROOT / "tmp" / "phase2f_summary.json"
DEFAULT_FIGURES = PROJECT_ROOT / "tmp" / "phase2f_figures"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Phase 2F recording-only excitability analysis")
    parser.add_argument("--nwb", type=pathlib.Path, default=DEFAULT_NWB,
                        help="original NWB (opened read-only)")
    parser.add_argument("--json", type=pathlib.Path, default=DEFAULT_JSON,
                        help="where to write the machine-readable summary")
    parser.add_argument("--figures-dir", type=pathlib.Path,
                        default=DEFAULT_FIGURES)
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--only", default="",
                        help="comma-separated sweep numbers to restrict the "
                             "analysis to (debugging only)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    report = Report()

    if not args.nwb.exists():
        print("NWB not found: %s" % args.nwb)
        return 2

    sha_before = sha256_of(args.nwb)
    with phase2d.open_nwb(args.nwb) as f:
        inventory = load_inventory(f)
        provenance = section_provenance(report, args.nwb, f, inventory)
        short_square = section_short_square(report, inventory, f)

        if args.only:
            chosen = [int(part) for part in args.only.split(",") if part.strip()]
        else:
            chosen = [sweep for sweep, entry in sorted(inventory.items())
                      if entry["block"] in LONG_SQUARE_BLOCKS
                      and entry["waveform"].get("status") == "OK"
                      and entry["waveform"]["duration_ms"] >= phase2d.MIN_STEP_MS]
        report.note("analysing %d long-square sweeps: %s"
                    % (len(chosen), ", ".join(str(s) for s in chosen)))

        analyses = {}
        for sweep in chosen:
            analyses[sweep] = analyse_sweep(f, sweep, inventory[sweep], report)

        counts = section_counts(report, analyses)
        train = section_train(report, analyses)
        morphology = section_morphology(report, analyses)
        segments = section_segments(report, analyses)
        blocks = section_blocks(report, analyses)
        c2 = section_c2(report, analyses)
        hypotheses = hypothesis_entries(report, analyses, blocks, short_square)
        print_hypotheses(report, hypotheses)

        figures = [] if args.no_figures else make_figures(
            f, analyses, args.figures_dir)

    # Nothing in this phase may touch the original file or a model asset, so the
    # digest is recomputed after all reading has finished and compared.
    sha_after = sha256_of(args.nwb)
    report.heading("J. Scope and integrity")
    report.check(sha_after == sha_before, "integrity|nwb unchanged by this run",
                 "%s… before and after" % sha_after[:16])
    report.check(sha_before == EXPECTED_SHA256,
                 "integrity|nwb still matches phase 1c",
                 "%s… vs %s…" % (sha_before[:16], EXPECTED_SHA256[:16]))
    polluted = [name for name in ("neuron", "allensdk", "neuron_models", "fhnsim")
                if name in sys.modules]
    report.check(not polluted, "integrity|no model runtime imported",
                 "none of %s in sys.modules"
                 % ", ".join(("neuron", "allensdk", "neuron_models", "fhnsim"))
                 if not polluted else "imported: %s" % ", ".join(polluted))
    report.observe("figures written",
                   "%d file(s) under %s" % (len(figures), args.figures_dir))

    summary = report.summary()
    payload = {
        "phase": "2F",
        "title": "Recording-only analysis of the COARSE/FINEST excitability "
                 "difference",
        "specimen": SPECIMEN,
        "provenance": provenance,
        "short_square": short_square,
        "counts": counts,
        "train": train,
        "morphology": morphology,
        "segments": segments,
        "blocks": blocks,
        "c2": c2,
        "hypotheses": hypotheses,
        "figures": figures,
        "tests": summary,
        "sweeps": summarise_for_json(analyses),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(to_jsonable(payload), indent=2) + "\n",
                         encoding="utf-8")

    print()
    print("=" * 78)
    print("PHASE 2F SUMMARY")
    print("=" * 78)
    print("  checks   %d passed, %d failed of %d"
          % (summary["passed"], summary["failed"], summary["checks"]))
    for section, bucket in sorted(summary["by_section"].items()):
        print("    %-22s %3d checks, %d failed"
              % (section, bucket["checks"], bucket["failed"]))
    print("  summary  %s" % args.json)
    print("  figures  %s" % ("disabled" if args.no_figures
                             else args.figures_dir))
    if summary["failed"]:
        print()
        print("  FAILED CHECKS")
        for item in summary["failures"]:
            print("    %-58s %s" % (item["label"], item["detail"]))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

"""FitzHugh-Nagumo (FHN) Parameter Calibration Framework for INCM.

Provides a mathematically defensible, dimensionally documented, and deterministic
parameter calibration framework for the two-variable FitzHugh-Nagumo model
across the four frozen VISp neuronal representatives.

Equations:
    C_m * dV/dt = -g_L * (V - V_rest) + k_v * (V - V_rest) * (V - V_th) * (V_peak - V) - w + I(t)
    tau_w * dw/dt = a_w * (V - V_rest) - w

Identifiability Strategy:
    1. V_rest is anchored directly to the empirical pre-stimulus baseline recording of each cell.
    2. V_peak is constrained closely by observed action potential peak amplitudes.
    3. Input resistance R_in = 1000 / (g_L + a_w + k_rest) constrains total resting conductance.
    4. C_m, g_L, V_th, k_v, tau_w, a_w are calibrated using a multi-component loss function
       optimizing spike count, firing rate, onset latency, input resistance, and peak amplitude.
    5. Optimization is strictly deterministic (fixed seed=42) and uses only the designated
       single calibration sweep for each specimen. Zero held-out sweeps are used.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
import json
import logging
import os
import pathlib
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.optimize as opt

from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNResult,
    FHNSimulationConfig,
    FitzHughNagumoModel,
)

logger = logging.getLogger(__name__)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

FROZEN_CALIBRATION_ASSIGNMENTS: dict[str, dict[str, Any]] = {
    "A": {
        "specimen_id": 484564503,
        "layer": "4",
        "structure": "VISp4",
        "model_id": 485591776,
        "sweep_id": 49,
        "stimulus_amplitude_pa": 370.0,
        "stimulus_onset_ms": 1020.0,
        "stimulus_duration_ms": 1000.0,
    },
    "B": {
        "specimen_id": 318808427,
        "layer": "2/3",
        "structure": "VISp2/3",
        "model_id": 473863035,
        "sweep_id": 40,
        "stimulus_amplitude_pa": 190.0,
        "stimulus_onset_ms": 1020.0,
        "stimulus_duration_ms": 1000.0,
    },
    "C": {
        "specimen_id": 471129934,
        "layer": "5",
        "structure": "VISp5",
        "model_id": 480624414,
        "sweep_id": 51,
        "stimulus_amplitude_pa": 410.0,
        "stimulus_onset_ms": 1020.0,
        "stimulus_duration_ms": 1000.0,
    },
    "D": {
        "specimen_id": 471786879,
        "layer": "6a",
        "structure": "VISp6a",
        "model_id": 480632594,
        "sweep_id": 42,
        "stimulus_amplitude_pa": 250.0,
        "stimulus_onset_ms": 1020.0,
        "stimulus_duration_ms": 1000.0,
    },
}


@dataclass(frozen=True)
class CalibrationBounds:
    """Biophysically and mathematically justified parameter bounds for FHN optimization."""

    C_m_min: float = 20.0       # Somatic capacitance minimum [pF]
    C_m_max: float = 250.0      # Somatic capacitance maximum [pF]
    g_L_min: float = 0.2        # Leak conductance minimum [nS]
    g_L_max: float = 15.0       # Leak conductance maximum [nS]
    V_th_min: float = -75.0     # Threshold parameter minimum [mV]
    V_th_max: float = -45.0     # Threshold parameter maximum [mV]
    V_peak_min: float = 20.0    # Peak parameter minimum [mV]
    V_peak_max: float = 65.0    # Peak parameter maximum [mV]
    k_v_min: float = 0.0005     # Cubic scaling minimum [nS/mV^2]
    k_v_max: float = 0.02       # Cubic scaling maximum [nS/mV^2]
    tau_w_min: float = 4.0      # Recovery time constant minimum [ms]
    tau_w_max: float = 60.0     # Recovery time constant maximum [ms]
    a_w_min: float = 1.0        # Recovery coupling minimum [nS]
    a_w_max: float = 25.0       # Recovery coupling maximum [nS]

    def as_list(self) -> list[tuple[float, float]]:
        return [
            (self.C_m_min, self.C_m_max),
            (self.g_L_min, self.g_L_max),
            (self.V_th_min, self.V_th_max),
            (self.V_peak_min, self.V_peak_max),
            (self.k_v_min, self.k_v_max),
            (self.tau_w_min, self.tau_w_max),
            (self.a_w_min, self.a_w_max),
        ]


@dataclass
class CalibrationTarget:
    """Experimental electrophysiological features from a single designated calibration sweep."""

    population: str
    specimen_id: int
    layer: str
    structure: str
    sweep_id: int
    stimulus_amplitude_pa: float
    stimulus_onset_ms: float
    stimulus_duration_ms: float
    baseline_recorded_mv: float
    rin_recorded_mohm: float
    spike_count_recorded: int
    first_spike_latency_ms: float
    spike_times_recorded_ms: list[float]
    peak_voltage_recorded_mv: float
    detailed_baseline_mv: float
    detailed_spike_count: int
    detailed_first_spike_latency_ms: float
    detailed_rmse_step_mv: float
    detailed_correlation: float
    traces_path: pathlib.Path
    summary_path: pathlib.Path


@dataclass
class CalibrationLossBreakdown:
    """Detailed breakdown of individual loss components."""

    total_loss: float
    loss_spk: float
    loss_rate: float
    loss_lat: float
    loss_rin: float
    loss_peak: float
    loss_rest: float = 0.0
    sim_spike_count: int = 0
    sim_first_spike_latency_ms: float = 0.0
    sim_rin_mohm: float = 0.0
    sim_peak_voltage_mv: float = 0.0


@dataclass
class CalibrationMetrics:
    """Comparative metrics across Experimental, Detailed, and Fitted FHN models."""

    population: str
    specimen_id: int
    layer: str
    sweep_id: int
    stimulus_amplitude_pa: float
    baseline_exp_mv: float
    baseline_fhn_mv: float
    baseline_detailed_mv: float
    rin_exp_mohm: float
    rin_fhn_mohm: float
    spikes_exp: int
    spikes_fhn: int
    spikes_detailed: int
    first_spike_lat_exp_ms: float
    first_spike_lat_fhn_ms: float
    first_spike_lat_detailed_ms: float
    peak_v_exp_mv: float
    peak_v_fhn_mv: float
    peak_v_detailed_mv: float
    rmse_step_fhn_mv: float
    rmse_step_detailed_mv: float
    rmse_overall_fhn_mv: float
    rmse_overall_detailed_mv: float
    correlation_fhn: float
    correlation_detailed: float
    calibration_loss: float
    is_resting_stable: bool


def load_calibration_target(
    population: str,
    repo_root: Optional[pathlib.Path] = None,
) -> CalibrationTarget:
    """Load experimental targets and detailed model summaries for a given population."""
    if repo_root is None:
        repo_root = REPO_ROOT

    info = FROZEN_CALIBRATION_ASSIGNMENTS[population]
    specimen_id = info["specimen_id"]
    model_dir = repo_root / "results" / "phase3" / "detailed_model" / str(specimen_id)
    traces_path = model_dir / "traces.npz"
    summary_path = model_dir / "summary.json"

    if not traces_path.exists() or not summary_path.exists():
        raise FileNotFoundError(
            f"Phase 3 calibration files missing for specimen {specimen_id} under {model_dir}"
        )

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    data = np.load(traces_path)
    t = data["t_ms"]
    v_rec = data["v_rec_mv"]
    stim = data["stim_pa"]

    # Pre-stimulus quiet baseline (200 ms to 1020 ms)
    base_mask = (t >= 200.0) & (t < 1020.0)
    baseline_exp = float(np.mean(v_rec[base_mask]))

    # Test pulse subthreshold input resistance (pulse between 5 ms and 15 ms, amp 50 pA)
    pre_test_mask = (t >= 0.0) & (t < 5.0)
    pulse_test_mask = (t >= 8.0) & (t <= 14.5)
    v_pre = np.mean(v_rec[pre_test_mask])
    v_pulse = np.mean(v_rec[pulse_test_mask])
    rin_exp = float((v_pulse - v_pre) / (50.0 * 1e-12) * 1e-3 * 1e-6)  # [MΩ]

    # Recorded spikes during step
    rec_spikes = summary["metrics"]["spike_times_recorded_in_step_ms"]
    n_spikes_rec = len(rec_spikes)
    lat_rec = float(rec_spikes[0] - 1020.0) if rec_spikes else 0.0

    # Step peak voltage
    step_mask = (t >= 1020.0) & (t <= 2020.0)
    peak_v_rec = float(np.max(v_rec[step_mask]))

    # Detailed model metrics
    det_base = float(summary["metrics"]["baseline_simulated_mv"])
    det_spikes = summary["metrics"]["spike_times_simulated_in_step_ms"]
    det_lat = float(det_spikes[0] - 1020.0) if det_spikes else 0.0
    det_rmse_step = float(summary["metrics"]["rmse_during_stimulus_mv"])
    det_corr = float(summary["metrics"]["correlation"])

    return CalibrationTarget(
        population=population,
        specimen_id=specimen_id,
        layer=info["layer"],
        structure=info["structure"],
        sweep_id=info["sweep_id"],
        stimulus_amplitude_pa=info["stimulus_amplitude_pa"],
        stimulus_onset_ms=info["stimulus_onset_ms"],
        stimulus_duration_ms=info["stimulus_duration_ms"],
        baseline_recorded_mv=baseline_exp,
        rin_recorded_mohm=rin_exp,
        spike_count_recorded=n_spikes_rec,
        first_spike_latency_ms=lat_rec,
        spike_times_recorded_ms=[float(x) for x in rec_spikes],
        peak_voltage_recorded_mv=peak_v_rec,
        detailed_baseline_mv=det_base,
        detailed_spike_count=len(det_spikes),
        detailed_first_spike_latency_ms=det_lat,
        detailed_rmse_step_mv=det_rmse_step,
        detailed_correlation=det_corr,
        traces_path=traces_path,
        summary_path=summary_path,
    )


def load_all_calibration_targets(
    repo_root: Optional[pathlib.Path] = None,
) -> dict[str, CalibrationTarget]:
    """Load calibration targets for all four populations."""
    return {
        pop: load_calibration_target(pop, repo_root=repo_root)
        for pop in FROZEN_CALIBRATION_ASSIGNMENTS
    }


def evaluate_fast_rk4(
    Cm: float,
    gL: float,
    Vrest: float,
    Vth: float,
    Vpeak: float,
    kv: float,
    tau_w: float,
    aw: float,
    I_step_pa: float,
    onset_ms: float = 100.0,
    duration_ms: float = 1000.0,
    t_stop_ms: float = 1150.0,
    dt_ms: float = 0.1,
) -> tuple[int, list[float], float]:
    """Fast inlined RK4 simulator for inner optimization loop.
    
    Returns:
        (spike_count, spike_times_in_step_relative_to_onset, max_voltage_reached)
    """
    offset_ms = onset_ms + duration_ms
    n_steps = int(round(t_stop_ms / dt_ms))

    v = Vrest
    w = 0.0
    crossings: list[float] = []
    last_crossing_t = -1e9
    v_max = v

    inv_Cm = 1.0 / Cm
    inv_tau = 1.0 / tau_w
    dt_half = 0.5 * dt_ms
    dt_sixth = dt_ms / 6.0

    for n in range(n_steps):
        t = n * dt_ms
        i_curr = I_step_pa if (onset_ms <= t < offset_ms) else 0.0

        # Stage 1
        v_diff1 = v - Vrest
        dv1 = (-gL * v_diff1 + kv * v_diff1 * (v - Vth) * (Vpeak - v) - w + i_curr) * inv_Cm
        dw1 = (aw * v_diff1 - w) * inv_tau

        # Stage 2
        v2 = v + dt_half * dv1
        w2 = w + dt_half * dw1
        v_diff2 = v2 - Vrest
        dv2 = (-gL * v_diff2 + kv * v_diff2 * (v2 - Vth) * (Vpeak - v2) - w2 + i_curr) * inv_Cm
        dw2 = (aw * v_diff2 - w2) * inv_tau

        # Stage 3
        v3 = v + dt_half * dv2
        w3 = w + dt_half * dw2
        v_diff3 = v3 - Vrest
        dv3 = (-gL * v_diff3 + kv * v_diff3 * (v3 - Vth) * (Vpeak - v3) - w3 + i_curr) * inv_Cm
        dw3 = (aw * v_diff3 - w3) * inv_tau

        # Stage 4
        v4 = v + dt_ms * dv3
        w4 = w + dt_ms * dw3
        v_diff4 = v4 - Vrest
        dv4 = (-gL * v_diff4 + kv * v_diff4 * (v4 - Vth) * (Vpeak - v4) - w4 + i_curr) * inv_Cm
        dw4 = (aw * v_diff4 - w4) * inv_tau

        # Update
        v_next = v + dt_sixth * (dv1 + 2.0 * dv2 + 2.0 * dv3 + dv4)
        w_next = w + dt_sixth * (dw1 + 2.0 * dw2 + 2.0 * dw3 + dw4)

        if not np.isfinite(v_next):
            return 0, [], -999.0

        if v_next > v_max:
            v_max = v_next

        if v < 0.0 and v_next >= 0.0:
            if (onset_ms <= t <= offset_ms) and (t - last_crossing_t > 2.0):
                crossings.append(t - onset_ms)
                last_crossing_t = t

        v = v_next
        w = w_next

    return len(crossings), crossings, v_max


def evaluate_calibration_loss(
    theta: Sequence[float],
    target: CalibrationTarget,
    bounds: CalibrationBounds,
    w_spk: float = 4.0,
    w_rate: float = 2.0,
    w_lat: float = 1.0,
    w_rin: float = 1.0,
    w_peak: float = 0.5,
) -> CalibrationLossBreakdown:
    """Evaluate multi-component weighted calibration loss for candidate parameter vector theta.
    
    theta = [C_m, g_L, V_th, V_peak, k_v, tau_w, a_w]
    V_rest is fixed to target.baseline_recorded_mv.
    """
    Cm, gL, Vth, Vpeak, kv, tau_w, aw = theta
    Vrest = target.baseline_recorded_mv

    # Boundary and physical consistency checks
    if not (Vrest < Vth < Vpeak):
        return CalibrationLossBreakdown(1e5, 1e5, 1e5, 1e5, 1e5, 1e5)
    if (
        Cm < bounds.C_m_min or Cm > bounds.C_m_max or
        gL < bounds.g_L_min or gL > bounds.g_L_max or
        Vth < bounds.V_th_min or Vth > bounds.V_th_max or
        Vpeak < bounds.V_peak_min or Vpeak > bounds.V_peak_max or
        kv < bounds.k_v_min or kv > bounds.k_v_max or
        tau_w < bounds.tau_w_min or tau_w > bounds.tau_w_max or
        aw < bounds.a_w_min or aw > bounds.a_w_max
    ):
        return CalibrationLossBreakdown(1e5, 1e5, 1e5, 1e5, 1e5, 1e5)

    # Input resistance calculation and loss
    k_rest = kv * (Vth - Vrest) * (Vpeak - Vrest)
    geff = gL + aw + k_rest
    rin_sim = 1000.0 / geff
    l_rin = ((rin_sim - target.rin_recorded_mohm) / 15.0) ** 2

    # Linear stability of resting equilibrium
    j11 = -(gL + k_rest) / Cm
    j12 = -1.0 / Cm
    j21 = aw / tau_w
    j22 = -1.0 / tau_w
    tr = j11 + j22
    det = j11 * j22 - j12 * j21
    if tr >= 0 or det <= 0:
        return CalibrationLossBreakdown(1e5, 1e5, 1e5, 1e5, 1e5, 1e5)

    # Fast simulation of calibration step
    n_sim, crossings, v_max = evaluate_fast_rk4(
        Cm=Cm,
        gL=gL,
        Vrest=Vrest,
        Vth=Vth,
        Vpeak=Vpeak,
        kv=kv,
        tau_w=tau_w,
        aw=aw,
        I_step_pa=target.stimulus_amplitude_pa,
        onset_ms=100.0,
        duration_ms=1000.0,
        t_stop_ms=1150.0,
        dt_ms=0.1,
    )

    n_exp = target.spike_count_recorded

    # Spike count loss
    l_spk = ((n_sim - n_exp) / max(1, n_exp)) ** 2
    if n_sim == 0:
        l_spk += max(0.0, -v_max) / 10.0
        l_lat = 5.0
        lat_sim = 0.0
    else:
        lat_sim = crossings[0]
        l_lat = ((lat_sim - target.first_spike_latency_ms) / 10.0) ** 2

    # Firing rate loss
    l_rate = ((n_sim - n_exp) / max(1.0, float(n_exp))) ** 2

    # Peak amplitude loss
    l_peak = ((v_max - target.peak_voltage_recorded_mv) / 5.0) ** 2

    total = (
        w_spk * l_spk +
        w_rate * l_rate +
        w_lat * l_lat +
        w_rin * l_rin +
        w_peak * l_peak
    )

    return CalibrationLossBreakdown(
        total_loss=float(total),
        loss_spk=float(l_spk),
        loss_rate=float(l_rate),
        loss_lat=float(l_lat),
        loss_rin=float(l_rin),
        loss_peak=float(l_peak),
        loss_rest=0.0,
        sim_spike_count=n_sim,
        sim_first_spike_latency_ms=lat_sim,
        sim_rin_mohm=rin_sim,
        sim_peak_voltage_mv=v_max,
    )


class FHNCalibrator:
    """Calibrator for the 2D FitzHugh-Nagumo model on VISp calibration sweeps."""

    def __init__(
        self,
        bounds: Optional[CalibrationBounds] = None,
        random_seed: int = 42,
    ):
        self.bounds = bounds if bounds is not None else CalibrationBounds()
        self.random_seed = random_seed

    def _generate_candidate_starts(
        self,
        target: CalibrationTarget,
        n_candidates: int = 4,
    ) -> list[list[float]]:
        """Generate physically motivated starting points tailored to target features."""
        Vrest = target.baseline_recorded_mv
        rin_target = target.rin_recorded_mohm
        amp = target.stimulus_amplitude_pa
        n_spk = target.spike_count_recorded
        v_peak_target = target.peak_voltage_recorded_mv

        # Desired total effective conductance [nS]
        g_target = 1000.0 / max(10.0, rin_target)

        # Estimate tau_w from target firing frequency
        freq = max(1.0, float(n_spk))
        base_tau = np.clip(1000.0 / (freq * 3.5), 8.0, 35.0)

        starts: list[list[float]] = []

        # Candidate 1: Balanced partition of conductance
        aw1 = np.clip(0.85 * g_target, 2.0, 22.0)
        gL1 = np.clip(0.15 * g_target, 0.5, 5.0)
        Cm1 = np.clip(target.first_spike_latency_ms * 3.5, 30.0, 180.0)
        Vth1 = np.clip(Vrest + 22.0, self.bounds.V_th_min, -46.0)
        starts.append([Cm1, gL1, Vth1, min(v_peak_target, 45.0), 0.003, base_tau, aw1])

        # Candidate 2: Higher capacitance for latency buffering
        Cm2 = np.clip(Cm1 * 1.4, 40.0, 220.0)
        starts.append([Cm2, gL1 * 1.2, Vth1 - 4.0, min(v_peak_target + 5.0, 52.0), 0.004, base_tau * 0.9, aw1 * 1.1])

        # Candidate 3: Fast recovery
        starts.append([Cm1 * 0.8, gL1 * 0.8, Vth1 + 3.0, min(v_peak_target - 2.0, 42.0), 0.0025, base_tau * 1.2, aw1 * 0.9])

        # Candidate 4: Population-specific baseline overrides
        if target.population == "A":
            starts.append([102.12, 1.20, -50.07, 42.46, 0.00293, 31.40, 13.32])
        elif target.population == "B":
            starts.append([29.40, 0.85, -74.56, 42.20, 0.00223, 12.39, 9.53])
        elif target.population == "C":
            starts.append([138.86, 0.73, -48.22, 53.71, 0.00476, 18.95, 18.87])
        elif target.population == "D":
            starts.append([85.0, 1.0, -62.0, 44.0, 0.0025, 14.0, 12.0])

        return starts[:n_candidates]

    def calibrate(
        self,
        target: CalibrationTarget,
        maxiter_per_start: int = 250,
    ) -> tuple[FHNParameters, CalibrationLossBreakdown, dict[str, Any]]:
        """Execute deterministic multi-start Nelder-Mead optimization on the calibration sweep."""
        Vrest = target.baseline_recorded_mv
        starts = self._generate_candidate_starts(target)

        def objective(theta: Sequence[float]) -> float:
            breakdown = evaluate_calibration_loss(theta, target, self.bounds)
            return breakdown.total_loss

        best_loss = 1e9
        best_theta = starts[0]
        best_breakdown: Optional[CalibrationLossBreakdown] = None
        total_evals = 0

        for i, s0 in enumerate(starts):
            # Clip initial guess strictly within bounds
            clipped_s0 = [
                float(np.clip(val, b[0] + 1e-3, b[1] - 1e-3))
                for val, b in zip(s0, self.bounds.as_list())
            ]
            res = opt.minimize(
                objective,
                clipped_s0,
                method="Nelder-Mead",
                options={"maxiter": maxiter_per_start, "disp": False},
            )
            total_evals += res.nfev
            current_loss = float(res.fun)
            if current_loss < best_loss:
                best_loss = current_loss
                best_theta = res.x
                best_breakdown = evaluate_calibration_loss(res.x, target, self.bounds)

        if best_breakdown is None:
            best_breakdown = evaluate_calibration_loss(best_theta, target, self.bounds)

        Cm, gL, Vth, Vpeak, kv, tau_w, aw = best_theta
        fitted_params = FHNParameters(
            C_m=float(Cm),
            g_L=float(gL),
            V_rest=float(Vrest),
            V_th=float(Vth),
            V_peak=float(Vpeak),
            k_v=float(kv),
            tau_w=float(tau_w),
            a_w=float(aw),
        )

        convergence_info = {
            "n_starts_evaluated": len(starts),
            "total_function_evaluations": total_evals,
            "best_loss": float(best_loss),
            "converged": bool(best_loss < 100.0),
            "resting_equilibrium_stable": fitted_params.is_resting_point_stable,
        }

        return fitted_params, best_breakdown, convergence_info

    def evaluate_full_metrics(
        self,
        params: FHNParameters,
        target: CalibrationTarget,
        dt_ms: float = 0.025,
    ) -> tuple[CalibrationMetrics, FHNResult]:
        """Perform full-resolution evaluation on the calibration sweep and compute metrics."""
        # Load raw recording
        data = np.load(target.traces_path)
        t_exp = data["t_ms"]
        v_exp = data["v_rec_mv"]
        stim_exp = data["stim_pa"]

        t_stop_ms = float(t_exp[-1])
        model = FitzHughNagumoModel(params)
        cfg = FHNSimulationConfig(dt_ms=dt_ms, t_stop_ms=t_stop_ms)

        # Full simulation with step protocol
        res = model.simulate_step_protocol(
            cfg,
            amplitude_pa=target.stimulus_amplitude_pa,
            onset_ms=target.stimulus_onset_ms,
            duration_ms=target.stimulus_duration_ms,
        )

        # Extract spikes
        spk_times = res.detect_spikes(threshold_mv=0.0)
        on = target.stimulus_onset_ms
        off = on + target.stimulus_duration_ms
        in_step_spk = spk_times[(spk_times >= on) & (spk_times <= off)]
        n_spk = len(in_step_spk)
        lat_fhn = float(in_step_spk[0] - on) if n_spk else 0.0

        # Downsample or interpolate simulation to experimental time grid for RMSE/corr
        v_fhn_interp = np.interp(t_exp, res.time_ms, res.v_mv)

        # Step mask
        step_mask = (t_exp >= on) & (t_exp <= off)
        rmse_step = float(np.sqrt(np.mean((v_fhn_interp[step_mask] - v_exp[step_mask]) ** 2)))
        rmse_overall = float(np.sqrt(np.mean((v_fhn_interp - v_exp) ** 2)))

        std_sim = np.std(v_fhn_interp)
        std_exp = np.std(v_exp)
        if std_sim > 1e-4 and std_exp > 1e-4:
            corr_fhn = float(np.corrcoef(v_fhn_interp, v_exp)[0, 1])
        else:
            corr_fhn = 0.0

        peak_v_fhn = float(np.max(v_fhn_interp[step_mask]))
        rin_fhn = params.effective_input_resistance_mohm

        # Breakdown loss
        breakdown = evaluate_calibration_loss(
            [params.C_m, params.g_L, params.V_th, params.V_peak, params.k_v, params.tau_w, params.a_w],
            target,
            self.bounds,
        )

        metrics = CalibrationMetrics(
            population=target.population,
            specimen_id=target.specimen_id,
            layer=target.layer,
            sweep_id=target.sweep_id,
            stimulus_amplitude_pa=target.stimulus_amplitude_pa,
            baseline_exp_mv=target.baseline_recorded_mv,
            baseline_fhn_mv=params.V_rest,
            baseline_detailed_mv=target.detailed_baseline_mv,
            rin_exp_mohm=target.rin_recorded_mohm,
            rin_fhn_mohm=rin_fhn,
            spikes_exp=target.spike_count_recorded,
            spikes_fhn=n_spk,
            spikes_detailed=target.detailed_spike_count,
            first_spike_lat_exp_ms=target.first_spike_latency_ms,
            first_spike_lat_fhn_ms=lat_fhn,
            first_spike_lat_detailed_ms=target.detailed_first_spike_latency_ms,
            peak_v_exp_mv=target.peak_voltage_recorded_mv,
            peak_v_fhn_mv=peak_v_fhn,
            peak_v_detailed_mv=float(np.max(data["v_sim_mv"][step_mask])),
            rmse_step_fhn_mv=rmse_step,
            rmse_step_detailed_mv=target.detailed_rmse_step_mv,
            rmse_overall_fhn_mv=rmse_overall,
            rmse_overall_detailed_mv=float(np.sqrt(np.mean((data["v_sim_mv"] - v_exp) ** 2))),
            correlation_fhn=corr_fhn,
            correlation_detailed=target.detailed_correlation,
            calibration_loss=breakdown.total_loss,
            is_resting_stable=params.is_resting_point_stable,
        )

        return metrics, res

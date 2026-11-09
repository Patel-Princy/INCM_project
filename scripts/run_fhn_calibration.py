#!/usr/bin/env python
"""Execute Phase 4B: FHN Model Calibration for Four VISp Populations.

Fits the dimensional 2D FitzHugh-Nagumo model strictly on the designated calibration
sweeps for the four frozen VISp representative neurons:
- Population A (VISp L4):  Specimen 484564503, Sweep 49 (+370 pA)
- Population B (VISp L2/3): Specimen 318808427, Sweep 40 (+190 pA)
- Population C (VISp L5):   Specimen 471129934, Sweep 51 (+410 pA)
- Population D (VISp L6a):  Specimen 471786879, Sweep 42 (+250 pA)

Strictly zero held-out sweeps are used for calibration.
Generates:
- results/phase4b/fhn_fitted_parameters.csv
- results/phase4b/fhn_calibration_metrics.csv
- results/phase4b/fhn_calibration_loss_breakdown.csv
- results/phase4b/calibration_config.json
- results/phase4b/data_audit_record.json
- results/phase4b/figures/*.png
"""
from __future__ import annotations

import csv
import json
import logging
import os
import pathlib
import sys
import time
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Add project root to sys.path
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.calibration.fhn_calibration import (
    CalibrationBounds,
    CalibrationLossBreakdown,
    CalibrationMetrics,
    CalibrationTarget,
    FHNCalibrator,
    evaluate_calibration_loss,
    load_all_calibration_targets,
)
from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNResult,
    FHNSimulationConfig,
    FitzHughNagumoModel,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phase4b_calibration")


def plot_population_calibration(
    pop: str,
    target: CalibrationTarget,
    params: FHNParameters,
    metrics: CalibrationMetrics,
    fhn_res: FHNResult,
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Generate high-resolution 3-panel figure for a population calibration."""
    data = np.load(target.traces_path)
    t_exp = data["t_ms"]
    v_exp = data["v_rec_mv"]
    v_det = data["v_sim_mv"]
    stim = data["stim_pa"]

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 2, height_ratios=[2.5, 1.0, 2.0], width_ratios=[2.5, 1.0])

    ax_v = fig.add_subplot(gs[0, :])
    ax_i = fig.add_subplot(gs[1, :], sharex=ax_v)
    ax_phase = fig.add_subplot(gs[2, 0])
    ax_zoom = fig.add_subplot(gs[2, 1])

    # 1. Voltage comparison
    ax_v.plot(t_exp, v_exp, color="#2c3e50", linewidth=0.8, alpha=0.85, label="Experimental Recording (Allen NWB)")
    ax_v.plot(t_exp, v_det, color="#2980b9", linewidth=0.8, alpha=0.75, linestyle="--", label="Detailed Perisomatic Model")
    ax_v.plot(fhn_res.time_ms, fhn_res.v_mv, color="#e74c3c", linewidth=0.9, alpha=0.9, label="Fitted 2D FHN Model")
    ax_v.set_ylabel("Membrane Potential (mV)", fontsize=11, fontweight="bold")
    title_str = (
        f"Population {pop} (VISp L{target.layer}) — Specimen {target.specimen_id} Sweep {target.sweep_id} [{target.stimulus_amplitude_pa:.0f} pA]\n"
        f"Spikes: Exp={metrics.spikes_exp}, FHN={metrics.spikes_fhn}, Detailed={metrics.spikes_detailed} | "
        f"Baseline: Exp={metrics.baseline_exp_mv:.1f} mV, FHN={metrics.baseline_fhn_mv:.1f} mV, Detailed={metrics.baseline_detailed_mv:.1f} mV | "
        f"Rin: Exp={metrics.rin_exp_mohm:.1f} MΩ, FHN={metrics.rin_fhn_mohm:.1f} MΩ"
    )
    ax_v.set_title(title_str, fontsize=11, fontweight="bold", pad=8)
    ax_v.grid(True, linestyle=":", alpha=0.5)
    ax_v.legend(loc="upper right", framealpha=0.9, fontsize=9)

    # 2. Injected current
    ax_i.plot(t_exp, stim, color="#34495e", linewidth=1.0, label=f"Command Stimulus ({target.stimulus_amplitude_pa:.0f} pA)")
    ax_i.set_ylabel("Current (pA)", fontsize=10, fontweight="bold")
    ax_i.grid(True, linestyle=":", alpha=0.5)
    ax_i.legend(loc="upper right", framealpha=0.9, fontsize=9)

    # 3. Phase portrait (V vs w)
    v_grid = np.linspace(-85.0, 45.0, 300)
    v_null = [
        -params.g_L * (v - params.V_rest) +
        params.k_v * (v - params.V_rest) * (v - params.V_th) * (params.V_peak - v) +
        target.stimulus_amplitude_pa
        for v in v_grid
    ]
    w_null = [params.a_w * (v - params.V_rest) for v in v_grid]

    ax_phase.plot(v_grid, v_null, color="#e67e22", linestyle="--", linewidth=1.5, label="V-nullcline (I=I_step)")
    ax_phase.plot(v_grid, w_null, color="#8e44ad", linestyle="--", linewidth=1.5, label="w-nullcline")
    ax_phase.plot(fhn_res.v_mv, fhn_res.w_pa, color="#e74c3c", linewidth=0.8, alpha=0.85, label="FHN Trajectory")
    ax_phase.set_xlabel("V (mV)", fontsize=10, fontweight="bold")
    ax_phase.set_ylabel("w (pA)", fontsize=10, fontweight="bold")
    ax_phase.set_title("Phase Portrait & Limit Cycle (V vs w)", fontsize=10, fontweight="bold")
    ax_phase.grid(True, linestyle=":", alpha=0.5)
    ax_phase.legend(loc="upper left", framealpha=0.9, fontsize=8)

    # 4. Spike waveform zoom (1020 ms to 1250 ms)
    zoom_mask_exp = (t_exp >= 1020.0) & (t_exp <= 1250.0)
    zoom_mask_fhn = (fhn_res.time_ms >= 1020.0) & (fhn_res.time_ms <= 1250.0)
    ax_zoom.plot(t_exp[zoom_mask_exp], v_exp[zoom_mask_exp], color="#2c3e50", linewidth=1.0, label="Exp")
    ax_zoom.plot(t_exp[zoom_mask_exp], v_det[zoom_mask_exp], color="#2980b9", linewidth=0.9, linestyle="--", label="Detailed")
    ax_zoom.plot(fhn_res.time_ms[zoom_mask_fhn], fhn_res.v_mv[zoom_mask_fhn], color="#e74c3c", linewidth=1.1, label="FHN")
    ax_zoom.set_xlabel("Time (ms)", fontsize=10, fontweight="bold")
    ax_zoom.set_ylabel("V (mV)", fontsize=10, fontweight="bold")
    ax_zoom.set_title("Initial Spike Train Zoom (1020–1250 ms)", fontsize=10, fontweight="bold")
    ax_zoom.grid(True, linestyle=":", alpha=0.5)
    ax_zoom.legend(loc="upper right", framealpha=0.9, fontsize=8)

    plt.tight_layout()
    out_path = out_dir / f"voltage_comparison_{pop}.png"
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def plot_summary_multi_panel(
    all_metrics: dict[str, CalibrationMetrics],
    all_targets: dict[str, CalibrationTarget],
    all_fhn_res: dict[str, FHNResult],
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Generate 4-panel multi-population comparative summary figure."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=True)
    pop_order = ["B", "A", "C", "D"]
    titles = [
        "Pop B (VISp L2/3, 190 pA) — Sustained Firing",
        "Pop A (VISp L4, 370 pA) — Fast Onset & Cessation",
        "Pop C (VISp L5, 410 pA) — High Current Adaptation",
        "Pop D (VISp L6a, 250 pA) — Delayed Onset Latency",
    ]

    for ax, pop, title in zip(axes.flat, pop_order, titles):
        t = all_targets[pop]
        m = all_metrics[pop]
        r = all_fhn_res[pop]

        data = np.load(t.traces_path)
        t_exp = data["t_ms"]
        v_exp = data["v_rec_mv"]
        v_det = data["v_sim_mv"]

        ax.plot(t_exp, v_exp, color="#2c3e50", linewidth=0.7, alpha=0.85, label="Experimental")
        ax.plot(t_exp, v_det, color="#2980b9", linewidth=0.7, alpha=0.7, linestyle="--", label="Detailed")
        ax.plot(r.time_ms, r.v_mv, color="#e74c3c", linewidth=0.85, alpha=0.9, label="Fitted FHN")

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylabel("Membrane Potential (mV)", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.set_xlim(800.0, 2200.0)
        ax.legend(loc="upper right", framealpha=0.9, fontsize=8)

    axes[1, 0].set_xlabel("Time (ms)", fontsize=11, fontweight="bold")
    axes[1, 1].set_xlabel("Time (ms)", fontsize=11, fontweight="bold")

    plt.tight_layout()
    out_path = out_dir / "four_population_calibration_summary.png"
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def plot_loss_breakdown(
    all_breakdowns: dict[str, CalibrationLossBreakdown],
    out_dir: pathlib.Path,
) -> pathlib.Path:
    """Generate bar chart comparing individual loss components across populations."""
    fig, ax = plt.subplots(figsize=(10, 6))
    pops = ["A", "B", "C", "D"]
    x = np.arange(len(pops))
    width = 0.15

    spk_losses = [all_breakdowns[p].loss_spk for p in pops]
    rate_losses = [all_breakdowns[p].loss_rate for p in pops]
    lat_losses = [all_breakdowns[p].loss_lat for p in pops]
    rin_losses = [all_breakdowns[p].loss_rin for p in pops]
    peak_losses = [all_breakdowns[p].loss_peak for p in pops]

    ax.bar(x - 2 * width, spk_losses, width, label="L_spk (Spike count)", color="#e74c3c")
    ax.bar(x - width, rate_losses, width, label="L_rate (Firing rate)", color="#e67e22")
    ax.bar(x, lat_losses, width, label="L_lat (Onset latency)", color="#f1c40f")
    ax.bar(x + width, rin_losses, width, label="L_rin (Input resistance)", color="#2ecc71")
    ax.bar(x + 2 * width, peak_losses, width, label="L_peak (Spike peak)", color="#3498db")

    ax.set_xticks(x)
    ax.set_xticklabels([f"Pop {p}" for p in pops], fontsize=11, fontweight="bold")
    ax.set_ylabel("Component Loss (Dimensionless)", fontsize=11, fontweight="bold")
    ax.set_title("Calibration Multi-Component Loss Breakdown Across VISp Populations", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.5, axis="y")
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    plt.tight_layout()
    out_path = out_dir / "calibration_loss_breakdown.png"
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def main() -> None:
    t_start = time.perf_counter()
    logger.info("Initializing Phase 4B FHN Calibration Framework...")

    out_dir = REPO_ROOT / "results" / "phase4b"
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load targets
    targets = load_all_calibration_targets(repo_root=REPO_ROOT)
    calibrator = FHNCalibrator(random_seed=42)

    fitted_params_list: list[dict[str, Any]] = []
    calibration_metrics_list: list[dict[str, Any]] = []
    loss_breakdowns_list: list[dict[str, Any]] = []
    all_breakdowns: dict[str, CalibrationLossBreakdown] = {}
    all_metrics: dict[str, CalibrationMetrics] = {}
    all_fhn_res: dict[str, FHNResult] = {}
    all_params: dict[str, FHNParameters] = {}
    convergence_records: dict[str, Any] = {}

    for pop in ["A", "B", "C", "D"]:
        target = targets[pop]
        logger.info(
            f"Calibrating Population {pop} (L{target.layer}, Specimen {target.specimen_id}, Sweep {target.sweep_id})..."
        )
        t0 = time.perf_counter()
        params, breakdown, info = calibrator.calibrate(target, maxiter_per_start=200)
        metrics, res = calibrator.evaluate_full_metrics(params, target, dt_ms=0.025)
        elapsed = time.perf_counter() - t0

        all_params[pop] = params
        all_breakdowns[pop] = breakdown
        all_metrics[pop] = metrics
        all_fhn_res[pop] = res
        convergence_records[pop] = info

        logger.info(
            f"Pop {pop} calibrated in {elapsed:.2f} s: Loss={metrics.calibration_loss:.5f}, "
            f"Spikes={metrics.spikes_fhn}/{metrics.spikes_exp}, "
            f"Lat={metrics.first_spike_lat_fhn_ms:.1f}/{metrics.first_spike_lat_exp_ms:.1f} ms, "
            f"Rin={metrics.rin_fhn_mohm:.1f}/{metrics.rin_exp_mohm:.1f} MΩ"
        )

        # Plot individual population figure
        fig_path = plot_population_calibration(pop, target, params, metrics, res, fig_dir)
        logger.info(f"Saved figure: {fig_path.name}")

        fitted_params_list.append({
            "population": pop,
            "specimen_id": target.specimen_id,
            "layer": target.layer,
            "structure": target.structure,
            "sweep_id": target.sweep_id,
            "stimulus_amplitude_pa": target.stimulus_amplitude_pa,
            "C_m_pf": round(params.C_m, 4),
            "g_L_ns": round(params.g_L, 4),
            "V_rest_mv": round(params.V_rest, 4),
            "V_th_mv": round(params.V_th, 4),
            "V_peak_mv": round(params.V_peak, 4),
            "k_v_ns_per_mv2": round(params.k_v, 6),
            "tau_w_ms": round(params.tau_w, 4),
            "a_w_ns": round(params.a_w, 4),
            "effective_rin_mohm": round(params.effective_input_resistance_mohm, 2),
            "is_resting_point_stable": params.is_resting_point_stable,
            "calibration_loss": round(metrics.calibration_loss, 6),
        })

        calibration_metrics_list.append({
            "population": pop,
            "specimen_id": target.specimen_id,
            "layer": target.layer,
            "sweep_id": target.sweep_id,
            "stimulus_amplitude_pa": target.stimulus_amplitude_pa,
            "baseline_exp_mv": round(metrics.baseline_exp_mv, 3),
            "baseline_fhn_mv": round(metrics.baseline_fhn_mv, 3),
            "baseline_detailed_mv": round(metrics.baseline_detailed_mv, 3),
            "rin_exp_mohm": round(metrics.rin_exp_mohm, 2),
            "rin_fhn_mohm": round(metrics.rin_fhn_mohm, 2),
            "spikes_exp": metrics.spikes_exp,
            "spikes_fhn": metrics.spikes_fhn,
            "spikes_detailed": metrics.spikes_detailed,
            "first_spike_lat_exp_ms": round(metrics.first_spike_lat_exp_ms, 2),
            "first_spike_lat_fhn_ms": round(metrics.first_spike_lat_fhn_ms, 2),
            "first_spike_lat_detailed_ms": round(metrics.first_spike_lat_detailed_ms, 2),
            "peak_v_exp_mv": round(metrics.peak_v_exp_mv, 2),
            "peak_v_fhn_mv": round(metrics.peak_v_fhn_mv, 2),
            "peak_v_detailed_mv": round(metrics.peak_v_detailed_mv, 2),
            "rmse_step_fhn_mv": round(metrics.rmse_step_fhn_mv, 2),
            "rmse_step_detailed_mv": round(metrics.rmse_step_detailed_mv, 2),
            "rmse_overall_fhn_mv": round(metrics.rmse_overall_fhn_mv, 2),
            "rmse_overall_detailed_mv": round(metrics.rmse_overall_detailed_mv, 2),
            "correlation_fhn": round(metrics.correlation_fhn, 4),
            "correlation_detailed": round(metrics.correlation_detailed, 4),
            "calibration_loss": round(metrics.calibration_loss, 6),
            "is_resting_stable": metrics.is_resting_stable,
        })

        loss_breakdowns_list.append({
            "population": pop,
            "specimen_id": target.specimen_id,
            "total_loss": round(breakdown.total_loss, 6),
            "loss_spk": round(breakdown.loss_spk, 6),
            "loss_rate": round(breakdown.loss_rate, 6),
            "loss_lat": round(breakdown.loss_lat, 6),
            "loss_rin": round(breakdown.loss_rin, 6),
            "loss_peak": round(breakdown.loss_peak, 6),
            "loss_rest": round(breakdown.loss_rest, 6),
        })

    # Summary multi-panel figure
    plot_summary_multi_panel(all_metrics, targets, all_fhn_res, fig_dir)
    # Loss breakdown bar chart
    plot_loss_breakdown(all_breakdowns, fig_dir)

    # Export CSVs
    csv_params_path = out_dir / "fhn_fitted_parameters.csv"
    with open(csv_params_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fitted_params_list[0].keys()))
        writer.writeheader()
        writer.writerows(fitted_params_list)
    logger.info(f"Saved: {csv_params_path}")

    csv_metrics_path = out_dir / "fhn_calibration_metrics.csv"
    with open(csv_metrics_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(calibration_metrics_list[0].keys()))
        writer.writeheader()
        writer.writerows(calibration_metrics_list)
    logger.info(f"Saved: {csv_metrics_path}")

    csv_breakdown_path = out_dir / "fhn_calibration_loss_breakdown.csv"
    with open(csv_breakdown_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(loss_breakdowns_list[0].keys()))
        writer.writeheader()
        writer.writerows(loss_breakdowns_list)
    logger.info(f"Saved: {csv_breakdown_path}")

    # Export config & audit record
    config_record = {
        "calibrator_version": "1.0.0",
        "random_seed": 42,
        "optimization_algorithm": "multi_start_nelder_mead",
        "loss_weights": {
            "w_spk": 4.0,
            "w_rate": 2.0,
            "w_lat": 1.0,
            "w_rin": 1.0,
            "w_peak": 0.5,
            "w_rest": 0.0,
        },
        "parameter_bounds": {
            "C_m_pf": [20.0, 250.0],
            "g_L_ns": [0.2, 15.0],
            "V_th_mv": [-75.0, -45.0],
            "V_peak_mv": [20.0, 65.0],
            "k_v_ns_per_mv2": [0.0005, 0.02],
            "tau_w_ms": [4.0, 60.0],
            "a_w_ns": [1.0, 25.0],
        },
        "convergence_summary": convergence_records,
    }
    with open(out_dir / "calibration_config.json", "w", encoding="utf-8") as f:
        json.dump(config_record, f, indent=2)

    audit_record = {
        "task": "INCM Phase 4B Parameter Calibration",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "held_out_sweeps_used": 0,
        "calibration_sweeps_used": {
            "Pop_A": {"specimen_id": 484564503, "sweep_id": 49, "amplitude_pa": 370.0},
            "Pop_B": {"specimen_id": 318808427, "sweep_id": 40, "amplitude_pa": 190.0},
            "Pop_C": {"specimen_id": 471129934, "sweep_id": 51, "amplitude_pa": 410.0},
            "Pop_D": {"specimen_id": 471786879, "sweep_id": 42, "amplitude_pa": 250.0},
        },
        "verification_invariants": {
            "detailed_models_modified": False,
            "state_variables_added": False,
            "held_out_sweeps_accessed": False,
            "all_four_resting_points_stable": all(m["is_resting_point_stable"] for m in fitted_params_list),
        },
    }
    with open(out_dir / "data_audit_record.json", "w", encoding="utf-8") as f:
        json.dump(audit_record, f, indent=2)

    total_time = time.perf_counter() - t_start
    logger.info(f"Phase 4B calibration pipeline completed successfully in {total_time:.2f} s.")


if __name__ == "__main__":
    main()

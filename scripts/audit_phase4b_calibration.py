"""Independent Calibration Quality and Identifiability Audit Script for INCM Phase 4B.1.

Audits the Phase 4B calibration results for the four frozen VISp neuronal representatives:
1. Independently reproduces all metrics and losses from raw recorded sweeps and serialized parameters.
2. Investigates and formalizes the low-loss / high-RMSE discrepancy.
3. Classifies constrained vs emergent electrophysiological metrics.
4. Performs a deep-dive investigation into Population D (L6a) spiking mismatch and maps the 2D Pareto frontier.
5. Evaluates local parameter sensitivities, Hessian curvature, condition numbers, and identifiability.
6. Emits structured CSV audit tables and publication-quality diagnostic figures.

Strict constraints:
- Zero access to 109 held-out sweeps.
- Zero modifications to frozen detailed models.
- Preserves Phase 4B baseline parameter sets bit-for-bit.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import os
import pathlib
import sys
from typing import Any, Dict, List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.calibration.fhn_calibration import (
    CalibrationBounds,
    CalibrationLossBreakdown,
    CalibrationMetrics,
    CalibrationTarget,
    FHNCalibrator,
    evaluate_calibration_loss,
    evaluate_fast_rk4,
    load_all_calibration_targets,
    FROZEN_CALIBRATION_ASSIGNMENTS,
)
from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNResult,
    FHNSimulationConfig,
    FitzHughNagumoModel,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase4B1Audit")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PHASE4B_DIR = REPO_ROOT / "results" / "phase4b"
PHASE4B1_DIR = REPO_ROOT / "results" / "phase4b1"
FIGURES_DIR = PHASE4B1_DIR / "figures"


def ensure_directories() -> None:
    """Ensure output directories exist."""
    PHASE4B1_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def audit_independent_reproduction(
    targets: dict[str, CalibrationTarget],
    calibrator: FHNCalibrator,
) -> pd.DataFrame:
    """Independently reproduce all Phase 4B metrics and compare against serialized CSVs."""
    logger.info("Step 1: Auditing independent reproduction of Phase 4B calibration results...")
    params_path = PHASE4B_DIR / "fhn_fitted_parameters.csv"
    orig_metrics_path = PHASE4B_DIR / "fhn_calibration_metrics.csv"
    orig_loss_path = PHASE4B_DIR / "fhn_calibration_loss_breakdown.csv"

    params_df = pd.read_csv(params_path).set_index("population")
    orig_metrics_df = pd.read_csv(orig_metrics_path).set_index("population")
    orig_loss_df = pd.read_csv(orig_loss_path).set_index("population")

    reproduction_rows = []

    for pop in ["A", "B", "C", "D"]:
        target = targets[pop]
        row = params_df.loc[pop]
        orig_m = orig_metrics_df.loc[pop]
        orig_l = orig_loss_df.loc[pop]

        fhn_params = FHNParameters(
            C_m=float(row["C_m_pf"]),
            g_L=float(row["g_L_ns"]),
            V_rest=float(row["V_rest_mv"]),
            V_th=float(row["V_th_mv"]),
            V_peak=float(row["V_peak_mv"]),
            k_v=float(row["k_v_ns_per_mv2"]),
            tau_w=float(row["tau_w_ms"]),
            a_w=float(row["a_w_ns"]),
        )

        # Full resolution RK4 evaluation
        metrics, res = calibrator.evaluate_full_metrics(fhn_params, target, dt_ms=0.025)

        # Compute differences
        diff_spk = metrics.spikes_fhn - int(orig_m["spikes_fhn"])
        diff_lat = metrics.first_spike_lat_fhn_ms - float(orig_m["first_spike_lat_fhn_ms"])
        diff_rmse_step = metrics.rmse_step_fhn_mv - float(orig_m["rmse_step_fhn_mv"])
        diff_rmse_all = metrics.rmse_overall_fhn_mv - float(orig_m["rmse_overall_fhn_mv"])
        diff_corr = metrics.correlation_fhn - float(orig_m["correlation_fhn"])
        diff_loss = metrics.calibration_loss - float(orig_m["calibration_loss"])
        diff_rin = metrics.rin_fhn_mohm - float(orig_m["rin_fhn_mohm"])

        reproduction_rows.append({
            "population": pop,
            "specimen_id": target.specimen_id,
            "layer": target.layer,
            "sweep_id": target.sweep_id,
            "orig_spikes_fhn": int(orig_m["spikes_fhn"]),
            "recomputed_spikes_fhn": metrics.spikes_fhn,
            "spikes_match": (diff_spk == 0),
            "orig_lat_fhn_ms": float(orig_m["first_spike_lat_fhn_ms"]),
            "recomputed_lat_fhn_ms": round(metrics.first_spike_lat_fhn_ms, 2),
            "lat_diff_ms": round(diff_lat, 4),
            "orig_rmse_step_mv": float(orig_m["rmse_step_fhn_mv"]),
            "recomputed_rmse_step_mv": round(metrics.rmse_step_fhn_mv, 2),
            "rmse_step_diff_mv": round(diff_rmse_step, 4),
            "orig_corr": float(orig_m["correlation_fhn"]),
            "recomputed_corr": round(metrics.correlation_fhn, 4),
            "corr_diff": round(diff_corr, 4),
            "orig_rin_mohm": float(orig_m["rin_fhn_mohm"]),
            "recomputed_rin_mohm": round(metrics.rin_fhn_mohm, 2),
            "rin_diff_mohm": round(diff_rin, 4),
            "orig_loss": float(orig_m["calibration_loss"]),
            "recomputed_loss": metrics.calibration_loss,
            "loss_diff": round(diff_loss, 6),
            "reproduction_verified": (abs(diff_loss) < 1e-4 and diff_spk == 0),
        })

    repro_df = pd.DataFrame(reproduction_rows)
    repro_csv = PHASE4B1_DIR / "fhn_calibration_reproduction_audit.csv"
    repro_df.to_csv(repro_csv, index=False)
    logger.info(f"Saved independent reproduction audit to {repro_csv}")
    return repro_df


def audit_low_loss_high_rmse(
    targets: dict[str, CalibrationTarget],
    calibrator: FHNCalibrator,
) -> dict[str, Any]:
    """Analyze why feature loss is near zero while point-by-point RMSE exceeds 40 mV."""
    logger.info("Step 2: Auditing Low-Loss / High-RMSE discrepancy and double-penalty mechanics...")
    params_df = pd.read_csv(PHASE4B_DIR / "fhn_fitted_parameters.csv").set_index("population")

    discrepancy_results = {}

    for pop in ["A", "B", "C", "D"]:
        target = targets[pop]
        row = params_df.loc[pop]
        fhn_params = FHNParameters(
            C_m=float(row["C_m_pf"]),
            g_L=float(row["g_L_ns"]),
            V_rest=float(row["V_rest_mv"]),
            V_th=float(row["V_th_mv"]),
            V_peak=float(row["V_peak_mv"]),
            k_v=float(row["k_v_ns_per_mv2"]),
            tau_w=float(row["tau_w_ms"]),
            a_w=float(row["a_w_ns"]),
        )

        data = np.load(target.traces_path)
        t_exp = data["t_ms"]
        v_exp = data["v_rec_mv"]
        step_mask = (t_exp >= target.stimulus_onset_ms) & (t_exp <= target.stimulus_onset_ms + target.stimulus_duration_ms)

        # 1. Full FHN simulation
        metrics, res = calibrator.evaluate_full_metrics(fhn_params, target, dt_ms=0.025)
        v_fhn_interp = np.interp(t_exp, res.time_ms, res.v_mv)

        # 2. Passive flatline at V_rest
        v_flat = np.full_like(v_exp, target.baseline_recorded_mv)
        rmse_flat_step = float(np.sqrt(np.mean((v_flat[step_mask] - v_exp[step_mask]) ** 2)))

        # 3. Subthreshold vs spike error decomposition
        # Biological spike threshold mask: where biological v_exp >= -30 mV
        spike_mask_exp = step_mask & (v_exp >= -30.0)
        subth_mask_exp = step_mask & (v_exp < -30.0)

        # Mean squared error in spike regions vs subthreshold regions
        mse_spike_region = float(np.mean((v_fhn_interp[spike_mask_exp] - v_exp[spike_mask_exp]) ** 2)) if np.any(spike_mask_exp) else 0.0
        mse_subth_region = float(np.mean((v_fhn_interp[subth_mask_exp] - v_exp[subth_mask_exp]) ** 2)) if np.any(subth_mask_exp) else 0.0
        mse_total_step = float(np.mean((v_fhn_interp[step_mask] - v_exp[step_mask]) ** 2))

        # Action potential width comparison (half-width at 0 mV or mid-height)
        # Detailed vs FHN spike widths
        discrepancy_results[pop] = {
            "calibration_loss": metrics.calibration_loss,
            "rmse_step_fhn_mv": metrics.rmse_step_fhn_mv,
            "rmse_step_detailed_mv": target.detailed_rmse_step_mv,
            "rmse_step_flatline_mv": round(rmse_flat_step, 2),
            "mse_spike_region_mv2": round(mse_spike_region, 2),
            "mse_subth_region_mv2": round(mse_subth_region, 2),
            "mse_total_step_mv2": round(mse_total_step, 2),
            "spike_time_fraction_pct": round(100.0 * np.sum(spike_mask_exp) / np.sum(step_mask), 2),
            "correlation_fhn": metrics.correlation_fhn,
            "correlation_detailed": target.detailed_correlation,
        }

    return discrepancy_results


def audit_metric_classification() -> pd.DataFrame:
    """Systematic classification of all reported electrophysiological quantities."""
    logger.info("Step 3: Auditing metric classification (Constrained vs Emergent)...")

    classifications = [
        {
            "category": "Group A: Directly Constrained / Fixed",
            "metric_name": "V_rest (Resting Potential)",
            "mathematical_definition": "V_rest = mean(v_rec[200 <= t < 1020])",
            "mechanism_in_pipeline": "Fixed identically to pre-stimulus experimental baseline before optimization.",
            "is_emergent_prediction": False,
            "scientific_justification": "Anchors baseline leak reversal to empirical recording, eliminating baseline float.",
        },
        {
            "category": "Group A: Directly Constrained / Fixed",
            "metric_name": "R_in (Input Resistance)",
            "mathematical_definition": "R_in = 1000 / (g_L + a_w + k_rest)",
            "mechanism_in_pipeline": "Explicitly penalized in loss via L_rin = ((R_in - R_exp)/15)^2.",
            "is_emergent_prediction": False,
            "scientific_justification": "Enforces subthreshold cellular impedance matching via analytical conductance sum.",
        },
        {
            "category": "Group A: Directly Constrained / Fixed",
            "metric_name": "V_peak (Peak Action Potential)",
            "mathematical_definition": "max(V(t)) over stimulus step",
            "mechanism_in_pipeline": "Penalized via L_peak = ((V_max - V_peak_exp)/5)^2 and bounded in [20, 65] mV.",
            "is_emergent_prediction": False,
            "scientific_justification": "Constrains maximum depolarizing excursion of the cubic unpinning term.",
        },
        {
            "category": "Group B: Directly Optimized via Objective",
            "metric_name": "N_spk (Spike Count)",
            "mathematical_definition": "sum_{spikes}(onset <= t <= offset)",
            "mechanism_in_pipeline": "Penalized with primary loss weight w_spk = 4.0 via L_spk = ((N_sim - N_exp)/N_exp)^2.",
            "is_emergent_prediction": False,
            "scientific_justification": "Primary calibration target for reproducing suprathreshold excitability.",
        },
        {
            "category": "Group B: Directly Optimized via Objective",
            "metric_name": "f_step (Mean Firing Rate)",
            "mathematical_definition": "N_spk / T_step (Hz)",
            "mechanism_in_pipeline": "Penalized with weight w_rate = 2.0 via L_rate.",
            "is_emergent_prediction": False,
            "scientific_justification": "Coupled directly to spike count over the 1000 ms calibration step duration.",
        },
        {
            "category": "Group B: Directly Optimized via Objective",
            "metric_name": "t_first (First-Spike Latency)",
            "mathematical_definition": "t_spike_1 - t_stim_onset (ms)",
            "mechanism_in_pipeline": "Penalized with weight w_lat = 1.0 via L_lat = ((t_lat - t_lat_exp)/10)^2.",
            "is_emergent_prediction": False,
            "scientific_justification": "Direct target ensuring the onset timing of repetitive firing is calibrated.",
        },
        {
            "category": "Group C: Emergent Model Behaviour",
            "metric_name": "Resting Equilibrium Linear Stability",
            "mathematical_definition": "tr(J_rest) < 0 and det(J_rest) > 0",
            "mechanism_in_pipeline": "Evaluated on Jacobians at V_rest; models with tr >= 0 or det <= 0 rejected with L=1e5.",
            "is_emergent_prediction": True,
            "scientific_justification": "Resting point stability under large nonlinear perturbation is emergent from phase portrait geometry.",
        },
        {
            "category": "Group C: Emergent Model Behaviour",
            "metric_name": "Continuous Trajectory Pearson Correlation (r)",
            "mathematical_definition": "cov(v_fhn, v_rec) / (std(v_fhn)*std(v_rec))",
            "mechanism_in_pipeline": "NOT included in loss function; computed post hoc on full interpolated traces.",
            "is_emergent_prediction": True,
            "scientific_justification": "Measures overall phase coherence and waveform shape alignment without direct fitting.",
        },
        {
            "category": "Group C: Emergent Model Behaviour",
            "metric_name": "Inter-Spike Interval Progression & Adaptation",
            "mathematical_definition": "ISI_k = t_{k+1} - t_k across the 1000 ms step",
            "mechanism_in_pipeline": "NOT constrained; single recovery variable w imposes strictly periodic limit-cycle firing.",
            "is_emergent_prediction": True,
            "scientific_justification": "Reflects planar dynamical constraint: 2D FHN lacks spike-frequency adaptation.",
        },
        {
            "category": "Group C: Emergent Model Behaviour",
            "metric_name": "Subthreshold Charging Trajectory",
            "mathematical_definition": "dV/dt below threshold governed by effective membrane time constant tau_m",
            "mechanism_in_pipeline": "Trajectory emerges from C_m, g_L, and a_w interaction without point-by-point tracking.",
            "is_emergent_prediction": True,
            "scientific_justification": "Emerges naturally from capacitive charging and slow recovery variable engagement.",
        },
    ]

    class_df = pd.DataFrame(classifications)
    out_csv = PHASE4B1_DIR / "fhn_metrics_classification_audit.csv"
    class_df.to_csv(out_csv, index=False)
    logger.info(f"Saved metric classification audit to {out_csv}")
    return class_df


def audit_population_d_pareto(
    target_D: CalibrationTarget,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Deep-dive investigation into Population D (L6a) Pareto frontier between latency and spike count."""
    logger.info("Step 4: Mapping Population D (L6a) Pareto frontier over (C_m, tau_w)...")

    # Fixed parameters from Population D baseline
    gL = 0.9128
    Vrest = target_D.baseline_recorded_mv
    Vth = -57.4868
    Vpeak = 64.9985
    kv = 0.002577
    aw = 11.7242
    I_step = target_D.stimulus_amplitude_pa  # 250 pA

    cm_vals = np.linspace(40.0, 240.0, 25)
    tau_vals = np.linspace(8.0, 60.0, 25)

    grid_results = []
    for cm in cm_vals:
        for tau in tau_vals:
            nspk, crossings, vmax = evaluate_fast_rk4(
                Cm=cm,
                gL=gL,
                Vrest=Vrest,
                Vth=Vth,
                Vpeak=Vpeak,
                kv=kv,
                tau_w=tau,
                aw=aw,
                I_step_pa=I_step,
            )
            lat = crossings[0] if nspk > 0 else math.nan
            grid_results.append({
                "C_m_pf": round(cm, 2),
                "tau_w_ms": round(tau, 2),
                "spike_count": nspk,
                "first_spike_lat_ms": round(lat, 2) if not math.isnan(lat) else -1.0,
                "peak_v_mv": round(vmax, 2),
            })

    grid_df = pd.DataFrame(grid_results)
    valid_df = grid_df[grid_df["spike_count"] > 0]

    # Compute Pareto frontier: for each spike count, what is max and min latency?
    pareto_summary = valid_df.groupby("spike_count")["first_spike_lat_ms"].agg(
        min_lat_ms="min",
        max_lat_ms="max",
        mean_lat_ms="mean",
        sample_count="count",
    ).reset_index()

    pareto_csv = PHASE4B1_DIR / "fhn_population_d_pareto_audit.csv"
    pareto_summary.to_csv(pareto_csv, index=False)
    logger.info(f"Saved Population D Pareto frontier audit to {pareto_csv}")

    return grid_df, pareto_summary


def audit_parameter_identifiability(
    targets: dict[str, CalibrationTarget],
) -> pd.DataFrame:
    """Audit local parameter sensitivities, Hessian condition numbers, and identifiability."""
    logger.info("Step 5: Auditing parameter sensitivity, Hessian conditioning, and identifiability...")
    bounds = CalibrationBounds()
    params_df = pd.read_csv(PHASE4B_DIR / "fhn_fitted_parameters.csv").set_index("population")
    param_names = ["C_m_pf", "g_L_ns", "V_th_mv", "V_peak_mv", "k_v_ns_per_mv2", "tau_w_ms", "a_w_ns"]
    bounds_list = bounds.as_list()

    identifiability_rows = []

    for pop in ["A", "B", "C", "D"]:
        target = targets[pop]
        row = params_df.loc[pop]
        theta_opt = np.array([float(row[p]) for p in param_names], dtype=float)

        base_loss = evaluate_calibration_loss(theta_opt, target, bounds).total_loss

        # 1. Dimensionless relative sensitivities: (d L / L) / (d theta / theta)
        # Using 1% perturbation clamped within parameter bounds
        sensitivities = {}
        for i, p in enumerate(param_names):
            delta = 0.01 * abs(theta_opt[i])
            th_p = theta_opt.copy()
            th_m = theta_opt.copy()
            th_p[i] = min(th_p[i] + delta, bounds_list[i][1] - 1e-4)
            th_m[i] = max(th_m[i] - delta, bounds_list[i][0] + 1e-4)

            lp = evaluate_calibration_loss(th_p, target, bounds).total_loss
            lm = evaluate_calibration_loss(th_m, target, bounds).total_loss

            denom = (th_p[i] - th_m[i]) / theta_opt[i]
            d_rel = (lp - lm) / denom if abs(denom) > 1e-9 else 0.0
            sensitivities[f"sens_{p}"] = float(d_rel)

        # 2. Numerical Hessian of dimension 7x7 using scaled step sizes
        H = np.zeros((7, 7))
        h_steps = [0.005 * abs(theta_opt[i]) for i in range(7)]

        for i in range(7):
            th_ip = theta_opt.copy()
            th_im = theta_opt.copy()
            th_ip[i] = min(th_ip[i] + h_steps[i], bounds_list[i][1] - 1e-4)
            th_im[i] = max(th_im[i] - h_steps[i], bounds_list[i][0] + 1e-4)

            l_ip = evaluate_calibration_loss(th_ip, target, bounds).total_loss
            l_im = evaluate_calibration_loss(th_im, target, bounds).total_loss

            step_i = (th_ip[i] - th_im[i]) * 0.5

            # Diagonal element: (f(x+h) - 2f(x) + f(x-h)) / h^2
            H[i, i] = (l_ip - 2.0 * base_loss + l_im) / (step_i ** 2) if step_i > 0 else 0.0

            for j in range(i + 1, 7):
                th_pp = theta_opt.copy()
                th_pm = theta_opt.copy()
                th_mp = theta_opt.copy()
                th_mm = theta_opt.copy()

                th_pp[i] = min(th_pp[i] + h_steps[i], bounds_list[i][1] - 1e-4)
                th_pp[j] = min(th_pp[j] + h_steps[j], bounds_list[j][1] - 1e-4)

                th_pm[i] = min(th_pm[i] + h_steps[i], bounds_list[i][1] - 1e-4)
                th_pm[j] = max(th_pm[j] - h_steps[j], bounds_list[j][0] + 1e-4)

                th_mp[i] = max(th_mp[i] - h_steps[i], bounds_list[i][0] + 1e-4)
                th_mp[j] = min(th_mp[j] + h_steps[j], bounds_list[j][1] - 1e-4)

                th_mm[i] = max(th_mm[i] - h_steps[i], bounds_list[i][0] + 1e-4)
                th_mm[j] = max(th_mm[j] - h_steps[j], bounds_list[j][0] + 1e-4)

                l_pp = evaluate_calibration_loss(th_pp, target, bounds).total_loss
                l_pm = evaluate_calibration_loss(th_pm, target, bounds).total_loss
                l_mp = evaluate_calibration_loss(th_mp, target, bounds).total_loss
                l_mm = evaluate_calibration_loss(th_mm, target, bounds).total_loss

                step_j = h_steps[j]
                h_ij = (l_pp - l_pm - l_mp + l_mm) / (4.0 * step_i * step_j)
                H[i, j] = h_ij
                H[j, i] = h_ij

        # Compute eigenvalues of normalized Hessian: H_norm = D * H * D where D_ii = theta_i
        D = np.diag(theta_opt)
        H_norm = D @ H @ D
        eigvals = np.linalg.eigvalsh(H_norm)
        eigvals_sorted = np.sort(np.abs(eigvals))

        min_eig = float(eigvals_sorted[0])
        max_eig = float(eigvals_sorted[-1])
        cond_number = float(max_eig / max(min_eig, 1e-12))

        # Check resting conductance degeneracy: g_L vs a_w correlation in R_in
        # R_in = 1000 / (g_L + a_w + k_rest)
        k_rest = row["k_v_ns_per_mv2"] * (row["V_th_mv"] - row["V_rest_mv"]) * (row["V_peak_mv"] - row["V_rest_mv"])
        g_eff = row["g_L_ns"] + row["a_w_ns"] + k_rest
        frac_gl = row["g_L_ns"] / g_eff
        frac_aw = row["a_w_ns"] / g_eff
        frac_krest = k_rest / g_eff

        row_dict = {
            "population": pop,
            "specimen_id": target.specimen_id,
            "layer": target.layer,
            "base_loss": base_loss,
            "max_normalized_curvature": max_eig,
            "min_normalized_curvature": min_eig,
            "hessian_condition_number": cond_number,
            "g_L_conductance_share": round(frac_gl, 4),
            "a_w_conductance_share": round(frac_aw, 4),
            "k_rest_conductance_share": round(frac_krest, 4),
            "effective_conductance_ns": round(g_eff, 4),
        }
        row_dict.update(sensitivities)
        identifiability_rows.append(row_dict)

    ident_df = pd.DataFrame(identifiability_rows)
    ident_csv = PHASE4B1_DIR / "fhn_parameter_identifiability_audit.csv"
    ident_df.to_csv(ident_csv, index=False)
    logger.info(f"Saved identifiability audit to {ident_csv}")
    return ident_df


def generate_diagnostic_figures(
    targets: dict[str, CalibrationTarget],
    calibrator: FHNCalibrator,
    grid_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    discrepancy_results: dict[str, Any],
) -> None:
    """Generate high-resolution diagnostic figures for the audit report."""
    logger.info("Step 6: Generating diagnostic audit figures...")

    # Figure 1: Population D Pareto Frontier & Trace Trade-off
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Pareto Scatter & Curve
    valid_grid = grid_df[grid_df["spike_count"] > 0]
    sc = ax1.scatter(
        valid_grid["first_spike_lat_ms"],
        valid_grid["spike_count"],
        c=valid_grid["C_m_pf"],
        cmap="viridis",
        alpha=0.65,
        s=40,
        edgecolors="none",
        label="FHN Grid Points",
    )
    cbar = plt.colorbar(sc, ax=ax1)
    cbar.set_label("Membrane Capacitance $C_m$ [pF]")

    # Target point
    target_D = targets["D"]
    ax1.plot(
        target_D.first_spike_latency_ms,
        target_D.spike_count_recorded,
        "r*",
        markersize=16,
        label=f"Biological Target (L6a: {target_D.spike_count_recorded} spk, {target_D.first_spike_latency_ms:.1f} ms)",
    )

    # Fitted FHN point
    ax1.plot(
        59.90,
        4,
        "s",
        color="crimson",
        markersize=10,
        label="Phase 4B Fitted FHN (4 spk, 59.9 ms)",
    )

    # Fast-firing alternative point
    ax1.plot(
        13.6,
        14,
        "o",
        color="darkorange",
        markersize=9,
        label="Alternative Low-$C_m$ FHN (14 spk, 13.6 ms)",
    )

    ax1.set_xlabel("First-Spike Latency [ms]", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Spike Count across 1000 ms Step", fontsize=11, fontweight="bold")
    ax1.set_title("A. Population D (L6a) Pareto Frontier: Latency vs Spikes", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=9)

    # Right: Time Domain Trace Comparison
    data_D = np.load(target_D.traces_path)
    t_exp = data_D["t_ms"]
    v_rec = data_D["v_rec_mv"]

    # Load fitted FHN
    params_df = pd.read_csv(PHASE4B_DIR / "fhn_fitted_parameters.csv").set_index("population")
    row_D = params_df.loc["D"]
    params_fitted_D = FHNParameters(
        C_m=float(row_D["C_m_pf"]),
        g_L=float(row_D["g_L_ns"]),
        V_rest=float(row_D["V_rest_mv"]),
        V_th=float(row_D["V_th_mv"]),
        V_peak=float(row_D["V_peak_mv"]),
        k_v=float(row_D["k_v_ns_per_mv2"]),
        tau_w=float(row_D["tau_w_ms"]),
        a_w=float(row_D["a_w_ns"]),
    )
    _, res_fitted = calibrator.evaluate_full_metrics(params_fitted_D, target_D, dt_ms=0.025)

    # Low-Cm alternative model
    params_fast_D = FHNParameters(
        C_m=50.0,
        g_L=float(row_D["g_L_ns"]),
        V_rest=float(row_D["V_rest_mv"]),
        V_th=float(row_D["V_th_mv"]),
        V_peak=float(row_D["V_peak_mv"]),
        k_v=float(row_D["k_v_ns_per_mv2"]),
        tau_w=10.0,
        a_w=float(row_D["a_w_ns"]),
    )
    _, res_fast = calibrator.evaluate_full_metrics(params_fast_D, target_D, dt_ms=0.025)

    ax2.plot(t_exp, v_rec, color="black", lw=1.2, label=f"Recording (13 spk, lat={target_D.first_spike_latency_ms:.1f} ms)")
    ax2.plot(res_fitted.time_ms, res_fitted.v_mv, color="crimson", lw=1.3, label="Fitted FHN (4 spk, lat=59.9 ms)")
    ax2.plot(res_fast.time_ms, res_fast.v_mv, color="darkorange", lw=1.1, linestyle="--", label="Low-$C_m$ FHN (14 spk, lat=13.6 ms)")

    ax2.set_xlim(950.0, 2050.0)
    ax2.set_ylim(-90.0, 60.0)
    ax2.set_xlabel("Time [ms]", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Membrane Potential [mV]", fontsize=11, fontweight="bold")
    ax2.set_title("B. Irreducible Trade-off in 2D Planar Dynamics", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", fontsize=8.5)

    plt.tight_layout()
    fig1_path = FIGURES_DIR / "pareto_frontier_population_d.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 1 to {fig1_path}")

    # Figure 2: Loss vs RMSE Discrepancy & Double-Penalty Effect
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))

    # Left: Bar chart comparing Step RMSE vs Flatline RMSE vs Detailed Model RMSE
    pops = ["A (L4)", "B (L2/3)", "C (L5)", "D (L6a)"]
    x = np.arange(len(pops))
    width = 0.25

    rmse_fhn = [discrepancy_results[p]["rmse_step_fhn_mv"] for p in ["A", "B", "C", "D"]]
    rmse_det = [discrepancy_results[p]["rmse_step_detailed_mv"] for p in ["A", "B", "C", "D"]]
    rmse_flat = [discrepancy_results[p]["rmse_step_flatline_mv"] for p in ["A", "B", "C", "D"]]

    ax1.bar(x - width, rmse_fhn, width, label="Fitted FHN Step RMSE", color="#d95f02", alpha=0.85)
    ax1.bar(x, rmse_det, width, label="Detailed Model Step RMSE", color="#1b9e77", alpha=0.85)
    ax1.bar(x + width, rmse_flat, width, label="Passive Flatline RMSE (0 Spikes)", color="#7570b3", alpha=0.85)

    ax1.set_ylabel("Step Voltage RMSE [mV]", fontsize=11, fontweight="bold")
    ax1.set_title("A. Voltage Step RMSE vs Inactive Flatline", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(pops, fontweight="bold")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=9)

    # Right: Action Potential Point-by-Point Double Penalty Illustration (Pop A)
    target_A = targets["A"]
    data_A = np.load(target_A.traces_path)
    t_A = data_A["t_ms"]
    v_rec_A = data_A["v_rec_mv"]

    row_A = params_df.loc["A"]
    params_A = FHNParameters(
        C_m=float(row_A["C_m_pf"]),
        g_L=float(row_A["g_L_ns"]),
        V_rest=float(row_A["V_rest_mv"]),
        V_th=float(row_A["V_th_mv"]),
        V_peak=float(row_A["V_peak_mv"]),
        k_v=float(row_A["k_v_ns_per_mv2"]),
        tau_w=float(row_A["tau_w_ms"]),
        a_w=float(row_A["a_w_ns"]),
    )
    _, res_A = calibrator.evaluate_full_metrics(params_A, target_A, dt_ms=0.025)
    v_fhn_A = np.interp(t_A, res_A.time_ms, res_A.v_mv)

    # Zoom in on first 2 action potentials (1020 ms to 1250 ms)
    zoom_mask = (t_A >= 1020.0) & (t_A <= 1250.0)
    ax2.plot(t_A[zoom_mask], v_rec_A[zoom_mask], color="black", lw=1.5, label="Experimental Recording")
    ax2.plot(t_A[zoom_mask], v_fhn_A[zoom_mask], color="#d95f02", lw=1.5, label="Fitted FHN Trajectory")

    # Fill squared error between them
    sq_err = (v_fhn_A[zoom_mask] - v_rec_A[zoom_mask]) ** 2
    ax2_twin = ax2.twinx()
    ax2_twin.fill_between(t_A[zoom_mask], 0, sq_err, color="crimson", alpha=0.25, label="$(V_{FHN} - V_{rec})^2$")
    ax2_twin.set_ylabel("Point-by-Point Squared Error $[mV^2]$", color="crimson", fontsize=10, fontweight="bold")
    ax2_twin.set_ylim(0, 12000)

    ax2.set_xlabel("Time [ms]", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Membrane Potential [mV]", fontsize=11, fontweight="bold")
    ax2.set_title("B. Spike Broadening & 'Double Penalty' Mechanism (Pop A)", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left", fontsize=8.5)

    plt.tight_layout()
    fig2_path = FIGURES_DIR / "loss_vs_rmse_discrepancy.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 2 to {fig2_path}")

    # Figure 3: Identifiability & Conductance Contributions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))

    # Left: Resting Conductance Breakdown (g_L vs a_w vs k_rest)
    ident_df = pd.read_csv(PHASE4B1_DIR / "fhn_parameter_identifiability_audit.csv").set_index("population")
    gl_shares = ident_df["g_L_conductance_share"].values * 100
    aw_shares = ident_df["a_w_conductance_share"].values * 100
    krest_shares = ident_df["k_rest_conductance_share"].values * 100

    ax1.bar(pops, gl_shares, label="Leak Conductance ($g_L$)", color="#386cb0", alpha=0.85)
    ax1.bar(pops, aw_shares, bottom=gl_shares, label="Adaptation Coupling ($a_w$)", color="#fdb462", alpha=0.85)
    ax1.bar(pops, krest_shares, bottom=gl_shares + aw_shares, label="Resting Cubic Influx ($k_{rest}$)", color="#7fc97f", alpha=0.85)

    ax1.set_ylabel("Percentage of Total Resting Conductance $g_{eff}$ [%]", fontsize=10, fontweight="bold")
    ax1.set_title("A. Resting Conductance Partition ($R_{in}$ Identifiability)", fontsize=12, fontweight="bold")
    ax1.set_ylim(0, 105)
    ax1.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=9)

    # Right: Hessian Condition Number across Populations
    cond_nums = ident_df["hessian_condition_number"].values
    ax2.semilogy(pops, cond_nums, marker="o", color="#e7298a", lw=2, markersize=8)
    for i, c in enumerate(cond_nums):
        ax2.annotate(f"$\\kappa = {c:.1e}$", (pops[i], c), textcoords="offset points", xytext=(0, 10), ha="center", fontweight="bold")

    ax2.set_ylabel("Hessian Condition Number $\\kappa = \\lambda_{max}/\\lambda_{min}$", fontsize=10, fontweight="bold")
    ax2.set_title("B. Local Hessian Conditioning & Valley Ill-Conditioning", fontsize=12, fontweight="bold")
    ax2.set_ylim(1e2, 1e8)
    ax2.grid(True, which="both", linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig3_path = FIGURES_DIR / "parameter_identifiability_hessian.png"
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 3 to {fig3_path}")


def main() -> None:
    """Execute complete Phase 4B.1 independent calibration audit."""
    logger.info("=== Starting INCM Phase 4B.1: Independent Calibration Quality and Identifiability Audit ===")
    ensure_directories()

    targets = load_all_calibration_targets()
    calibrator = FHNCalibrator()

    # Step 1: Reproduction Audit
    repro_df = audit_independent_reproduction(targets, calibrator)

    # Step 2: Low-Loss / High-RMSE Discrepancy
    discrepancy_results = audit_low_loss_high_rmse(targets, calibrator)

    # Step 3: Metric Classification
    class_df = audit_metric_classification()

    # Step 4: Population D Pareto Frontier
    grid_df, pareto_df = audit_population_d_pareto(targets["D"])

    # Step 5: Parameter Sensitivity and Identifiability
    ident_df = audit_parameter_identifiability(targets)

    # Step 6: Diagnostic Figures
    generate_diagnostic_figures(targets, calibrator, grid_df, pareto_df, discrepancy_results)

    logger.info("=== Phase 4B.1 Audit Computations Completed Successfully ===")


if __name__ == "__main__":
    main()

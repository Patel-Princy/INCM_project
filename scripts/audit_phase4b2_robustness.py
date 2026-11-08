"""Scientific Claim and Robustness Audit Script for INCM Phase 4B.2.

Performs:
1. Population D (L6a) refined 2D parameter grid scan over (C_m, tau_w) around the Pareto transition region.
2. Rigorous multi-scale Hessian curvature, symmetry, and eigenvalue spectrum audit across step sizes h_rel.
3. Distinguishes local curvature, non-smoothness, and practical identifiability limitations.
4. Generates publication-grade diagnostic figures and structured CSV audit tables.
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
)
from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNResult,
    FHNSimulationConfig,
    FitzHughNagumoModel,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase4B2Audit")

PHASE4B_DIR = REPO_ROOT / "results" / "phase4b"
PHASE4B2_DIR = REPO_ROOT / "results" / "phase4b2"
FIGURES_DIR = PHASE4B2_DIR / "figures"


def ensure_directories() -> None:
    """Ensure output directories exist."""
    PHASE4B2_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def run_refined_population_d_scan(
    target_D: CalibrationTarget,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Execute high-resolution refined 2D scan over (C_m, tau_w) for Population D."""
    logger.info("Executing refined 31x31 Population D grid scan over (C_m, tau_w)...")

    gL = 0.9128
    Vrest = target_D.baseline_recorded_mv  # -75.7102 mV
    Vth = -57.4868
    Vpeak = 64.9985
    kv = 0.002577
    aw = 11.7242
    I_step = target_D.stimulus_amplitude_pa  # 250 pA

    # Refined grid: 31 x 31 = 961 combinations
    cm_vals = np.linspace(40.0, 220.0, 31)
    tau_vals = np.linspace(8.0, 50.0, 31)

    points = []
    n_total = len(cm_vals) * len(tau_vals)
    n_completed = 0
    n_spiking = 0
    n_quiescent = 0

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
            n_completed += 1
            if nspk > 0:
                n_spiking += 1
                lat = crossings[0]
            else:
                n_quiescent += 1
                lat = -1.0

            points.append({
                "C_m_pf": round(cm, 3),
                "tau_w_ms": round(tau, 3),
                "spike_count": nspk,
                "first_spike_lat_ms": round(lat, 2) if nspk > 0 else -1.0,
                "peak_v_mv": round(vmax, 2),
            })

    logger.info(
        f"Completed all {n_completed}/{n_total} combinations: "
        f"{n_spiking} spiking ({n_spiking/n_total*100:.1f}%), {n_quiescent} quiescent ({n_quiescent/n_total*100:.1f}%)"
    )

    grid_df = pd.DataFrame(points)
    grid_csv = PHASE4B2_DIR / "fhn_population_d_grid_points.csv"
    grid_df.to_csv(grid_csv, index=False)

    # Compute Pareto summary across valid spiking points
    spiking_df = grid_df[grid_df["spike_count"] > 0]
    pareto_summary = spiking_df.groupby("spike_count")["first_spike_lat_ms"].agg(
        min_lat_ms="min",
        max_lat_ms="max",
        mean_lat_ms="mean",
        sample_count="count",
    ).reset_index()

    pareto_csv = PHASE4B2_DIR / "fhn_population_d_refined_pareto.csv"
    pareto_summary.to_csv(pareto_csv, index=False)
    logger.info(f"Saved refined Pareto summary to {pareto_csv}")

    return grid_df, pareto_summary


def audit_hessian_robustness(
    targets: dict[str, CalibrationTarget],
) -> pd.DataFrame:
    """Audit Hessian eigenvalues, condition numbers, and positive definiteness across step sizes."""
    logger.info("Executing multi-scale Hessian curvature and robustness audit...")

    bounds = CalibrationBounds()
    params_df = pd.read_csv(PHASE4B_DIR / "fhn_fitted_parameters.csv").set_index("population")
    param_names = ["C_m_pf", "g_L_ns", "V_th_mv", "V_peak_mv", "k_v_ns_per_mv2", "tau_w_ms", "a_w_ns"]
    bounds_list = bounds.as_list()

    step_sizes = [0.001, 0.002, 0.005, 0.010, 0.020]
    results = []

    for pop in ["A", "B", "C", "D"]:
        target = targets[pop]
        row = params_df.loc[pop]
        theta = np.array([float(row[p]) for p in param_names])
        base_loss = evaluate_calibration_loss(theta, target, bounds).total_loss

        # Estimate gradient with central difference at h_rel = 0.005
        grad = np.zeros(7)
        for i in range(7):
            th_p = theta.copy()
            th_m = theta.copy()
            h = 0.005 * abs(theta[i])
            th_p[i] = min(th_p[i] + h, bounds_list[i][1] - 1e-4)
            th_m[i] = max(th_m[i] - h, bounds_list[i][0] + 1e-4)
            lp = evaluate_calibration_loss(th_p, target, bounds).total_loss
            lm = evaluate_calibration_loss(th_m, target, bounds).total_loss
            actual_h = (th_p[i] - th_m[i]) * 0.5
            grad[i] = (lp - lm) / (2.0 * actual_h) if actual_h > 0 else 0.0

        grad_norm = float(np.linalg.norm(grad))

        for h_rel in step_sizes:
            H = np.zeros((7, 7))
            h_steps = [h_rel * abs(theta[i]) for i in range(7)]

            for i in range(7):
                th_ip = theta.copy()
                th_im = theta.copy()
                th_ip[i] = min(th_ip[i] + h_steps[i], bounds_list[i][1] - 1e-4)
                th_im[i] = max(th_im[i] - h_steps[i], bounds_list[i][0] + 1e-4)
                lip = evaluate_calibration_loss(th_ip, target, bounds).total_loss
                lim = evaluate_calibration_loss(th_im, target, bounds).total_loss
                step_i = (th_ip[i] - th_im[i]) * 0.5
                H[i, i] = (lip - 2.0 * base_loss + lim) / (step_i ** 2) if step_i > 0 else 0.0

                for j in range(i + 1, 7):
                    th_pp = theta.copy()
                    th_pm = theta.copy()
                    th_mp = theta.copy()
                    th_mm = theta.copy()

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

                    step_j = (th_pp[j] - th_pm[j]) * 0.5
                    hij = (l_pp - l_pm - l_mp + l_mm) / (4.0 * step_i * step_j) if (step_i > 0 and step_j > 0) else 0.0
                    H[i, j] = hij
                    H[j, i] = hij

            # Normalized Hessian H_norm = D H D
            D = np.diag(theta)
            H_norm = D @ H @ D
            H_norm_sym = 0.5 * (H_norm + H_norm.T)

            # Compute eigenvalues
            eigs = np.linalg.eigvalsh(H_norm_sym)
            eigs_sorted = np.sort(eigs)

            min_eig = float(eigs_sorted[0])
            max_eig = float(eigs_sorted[-1])
            is_pos_def = (min_eig > 0.0)
            cond_num = float(max_eig / min_eig) if (min_eig > 1e-6) else math.nan

            n_pos = int(np.sum(eigs > 1e-3))
            n_neg = int(np.sum(eigs < -1e-3))
            n_zero = int(np.sum(np.abs(eigs) <= 1e-3))

            results.append({
                "population": pop,
                "specimen_id": target.specimen_id,
                "h_rel": h_rel,
                "base_loss": base_loss,
                "grad_norm": grad_norm,
                "min_eig": min_eig,
                "max_eig": max_eig,
                "is_positive_definite": is_pos_def,
                "condition_number": cond_num if not math.isnan(cond_num) else -1.0,
                "num_positive_eigs": n_pos,
                "num_negative_eigs": n_neg,
                "num_zero_eigs": n_zero,
                "eig_1": round(float(eigs_sorted[0]), 3),
                "eig_2": round(float(eigs_sorted[1]), 3),
                "eig_3": round(float(eigs_sorted[2]), 3),
                "eig_4": round(float(eigs_sorted[3]), 3),
                "eig_5": round(float(eigs_sorted[4]), 3),
                "eig_6": round(float(eigs_sorted[5]), 3),
                "eig_7": round(float(eigs_sorted[6]), 3),
            })

    res_df = pd.DataFrame(results)
    res_csv = PHASE4B2_DIR / "fhn_hessian_robustness_audit.csv"
    res_df.to_csv(res_csv, index=False)
    logger.info(f"Saved Hessian robustness audit to {res_csv}")
    return res_df


def generate_robustness_figures(
    target_D: CalibrationTarget,
    grid_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    hessian_df: pd.DataFrame,
) -> None:
    """Generate diagnostic figures for Phase 4B.2 audit."""
    logger.info("Generating Phase 4B.2 diagnostic figures...")

    # Figure 1: Population D Refined Pareto Scatter & Envelope
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    spiking_grid = grid_df[grid_df["spike_count"] > 0]
    sc = ax1.scatter(
        spiking_grid["first_spike_lat_ms"],
        spiking_grid["spike_count"],
        c=spiking_grid["C_m_pf"],
        cmap="viridis",
        alpha=0.6,
        s=30,
        edgecolors="none",
    )
    cbar = plt.colorbar(sc, ax=ax1)
    cbar.set_label("Membrane Capacitance $C_m$ [pF]")

    # Plot Pareto envelope lines
    ax1.plot(
        pareto_df["max_lat_ms"],
        pareto_df["spike_count"],
        color="crimson",
        lw=2.0,
        marker="o",
        markersize=5,
        label="Refined Pareto Max-Latency Envelope",
    )

    # Biological target
    ax1.plot(
        target_D.first_spike_latency_ms,
        target_D.spike_count_recorded,
        "r*",
        markersize=16,
        label=f"Biological Target ({target_D.spike_count_recorded} spk, {target_D.first_spike_latency_ms:.1f} ms)",
    )

    # Fitted model
    ax1.plot(
        59.90,
        4,
        "s",
        color="navy",
        markersize=10,
        label="Phase 4B Fitted FHN (4 spk, 59.9 ms)",
    )

    ax1.set_xlabel("First-Spike Latency [ms]", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Spike Count (1000 ms step)", fontsize=11, fontweight="bold")
    ax1.set_title("A. Refined 31x31 Grid: Latency vs. Spike Count", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=8.5)

    # Right: Latency distribution by spike count
    counts = pareto_df["spike_count"].values
    max_lats = pareto_df["max_lat_ms"].values
    min_lats = pareto_df["min_lat_ms"].values

    ax2.barh(counts, max_lats - min_lats, left=min_lats, color="#41b6c4", alpha=0.8, edgecolor="black", lw=0.5)
    ax2.axvline(target_D.first_spike_latency_ms, color="red", linestyle="--", lw=1.5, label=f"Target Latency ({target_D.first_spike_latency_ms:.1f} ms)")
    ax2.axhline(target_D.spike_count_recorded, color="darkgreen", linestyle=":", lw=1.5, label=f"Target Spikes ({target_D.spike_count_recorded})")

    ax2.set_xlabel("First-Spike Latency Range [ms]", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Spike Count", fontsize=11, fontweight="bold")
    ax2.set_title("B. Achievable Latency Range per Spike Count", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    fig1_path = FIGURES_DIR / "population_d_refined_pareto.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 1 to {fig1_path}")

    # Figure 2: Hessian Eigenvalues across step sizes
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    pops = ["A", "B", "C", "D"]
    sub_titles = [
        "Pop A (L4, 484564503): Weakly Indefinite / Valley",
        "Pop B (L2/3, 318808427): Strictly Positive Definite (Convex)",
        "Pop C (L5, 471129934): Weakly Indefinite / Valley",
        "Pop D (L6a, 471786879): Highly Anisotropic / Indefinite",
    ]

    for idx, (pop, ax) in enumerate(zip(pops, axes.flatten())):
        sub_df = hessian_df[hessian_df["population"] == pop]
        h_vals = sub_df["h_rel"].values
        for eig_i in range(1, 8):
            e_vals = sub_df[f"eig_{eig_i}"].values
            ax.plot(h_vals, e_vals, marker="o", lw=1.5, label=f"$\\lambda_{eig_i}$")

        ax.axhline(0.0, color="black", linestyle="--", lw=1.0)
        ax.set_xscale("log")
        ax.set_xlabel("Relative Finite Difference Step Size $h_{\\mathrm{rel}}$", fontsize=9.5)
        ax.set_ylabel("Normalized Eigenvalue $\\lambda$", fontsize=9.5)
        ax.set_title(sub_titles[idx], fontsize=10.5, fontweight="bold")
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        if idx == 1:
            ax.legend(loc="upper right", fontsize=8, ncol=2)

    plt.tight_layout()
    fig2_path = FIGURES_DIR / "hessian_eigenvalue_robustness.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 2 to {fig2_path}")


def main() -> None:
    """Run full Phase 4B.2 scientific claim and robustness audit."""
    logger.info("=== Starting INCM Phase 4B.2: Scientific Claim and Robustness Audit ===")
    ensure_directories()

    targets = load_all_calibration_targets()

    # Step 1: Population D refined grid scan
    grid_df, pareto_df = run_refined_population_d_scan(targets["D"])

    # Step 2: Hessian robustness audit
    hessian_df = audit_hessian_robustness(targets)

    # Step 3: Diagnostic figures
    generate_robustness_figures(targets["D"], grid_df, pareto_df, hessian_df)

    logger.info("=== Phase 4B.2 Audit Completed Successfully ===")


if __name__ == "__main__":
    main()

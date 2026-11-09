"""Generate Phase 4A Numerical Validation Figures for FitzHugh-Nagumo Model.

Produces:
1. hyperpolarizing_step_response.png
2. depolarizing_step_response.png
3. trajectories_v_and_w.png
4. phase_plane_nullclines.png
5. timestep_convergence.png
"""
from __future__ import annotations

import os
import tempfile

# Configure writable matplotlib cache
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()

from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNSimulationConfig,
    FitzHughNagumoModel,
)

OUTPUT_DIR = Path("results/phase4a/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def plot_hyperpolarizing_step():
    """Figure 1: Hyperpolarizing current step response."""
    params = FHNParameters(
        C_m=100.0, g_L=4.0, a_w=1.0, k_v=0.002, V_rest=-75.0, V_th=-50.0, V_peak=20.0, tau_w=20.0
    )
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=500.0)

    res = model.simulate_step_protocol(config, amplitude_pa=-60.0, onset_ms=50.0, duration_ms=300.0)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 7), sharex=True, dpi=300)

    # Injected current
    ax1.plot(res.time_ms, res.i_stim_pa, color="#1f77b4", lw=1.8, label="Injected Current")
    ax1.set_ylabel("Current (pA)")
    ax1.set_title("Hyperpolarizing Step Response (Subthreshold Passive Relaxation)")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    # Membrane voltage
    ax2.plot(res.time_ms, res.v_mv, color="#d62728", lw=1.8, label="V(t)")
    ax2.axhline(params.V_rest, color="gray", linestyle=":", label=f"V_rest ({params.V_rest} mV)")
    ax2.set_ylabel("Membrane (mV)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")

    # Recovery current
    ax3.plot(res.time_ms, res.w_pa, color="#2ca02c", lw=1.8, label="w(t) Recovery")
    ax3.axhline(0.0, color="gray", linestyle=":", label="w = 0 pA")
    ax3.set_xlabel("Time (ms)")
    ax3.set_ylabel("Recovery (pA)")
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="upper right")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "hyperpolarizing_step_response.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_depolarizing_step():
    """Figure 2: Depolarizing suprathreshold step response."""
    params = FHNParameters(
        C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0
    )
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=600.0)

    res = model.simulate_step_protocol(config, amplitude_pa=220.0, onset_ms=50.0, duration_ms=500.0)
    spikes = res.detect_spikes(threshold_mv=0.0)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 7.5), sharex=True, dpi=300)

    # Injected current
    ax1.plot(res.time_ms, res.i_stim_pa, color="#1f77b4", lw=1.8, label="Injected Current (+220 pA)")
    ax1.set_ylabel("Current (pA)")
    ax1.set_title("Depolarizing Suprathreshold Step Response (Repetitive Spiking)")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    # Membrane voltage
    ax2.plot(res.time_ms, res.v_mv, color="#d62728", lw=1.6, label="V(t)")
    ax2.axhline(0.0, color="gray", linestyle=":", label="0 mV Threshold")
    for spk in spikes:
        ax2.axvline(spk, color="orange", linestyle="--", alpha=0.6)
    ax2.set_ylabel("Membrane (mV)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")

    # Recovery current
    ax3.plot(res.time_ms, res.w_pa, color="#2ca02c", lw=1.6, label="w(t) Recovery")
    ax3.set_xlabel("Time (ms)")
    ax3.set_ylabel("Recovery (pA)")
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="upper right")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "depolarizing_step_response.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_trajectories_v_and_w():
    """Figure 3: Combined V(t) and w(t) multi-condition comparison."""
    params = FHNParameters(
        C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0
    )
    model = FitzHughNagumoModel(params)
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=400.0)

    # Subthreshold (+100 pA) vs Suprathreshold (+220 pA)
    res_sub = model.simulate_step_protocol(config, amplitude_pa=100.0, onset_ms=50.0, duration_ms=300.0)
    res_supra = model.simulate_step_protocol(config, amplitude_pa=220.0, onset_ms=50.0, duration_ms=300.0)

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True, dpi=300)

    # Subthreshold V
    axes[0, 0].plot(res_sub.time_ms, res_sub.v_mv, color="#1f77b4", lw=1.8)
    axes[0, 0].set_ylabel("V (mV)")
    axes[0, 0].set_title("Subthreshold (+100 pA): Membrane Voltage")
    axes[0, 0].grid(True, linestyle="--", alpha=0.5)

    # Subthreshold w
    axes[1, 0].plot(res_sub.time_ms, res_sub.w_pa, color="#1f77b4", lw=1.8)
    axes[1, 0].set_ylabel("w (pA)")
    axes[1, 0].set_xlabel("Time (ms)")
    axes[1, 0].set_title("Subthreshold (+100 pA): Recovery Current")
    axes[1, 0].grid(True, linestyle="--", alpha=0.5)

    # Suprathreshold V
    axes[0, 1].plot(res_supra.time_ms, res_supra.v_mv, color="#d62728", lw=1.6)
    axes[0, 1].set_ylabel("V (mV)")
    axes[0, 1].set_title("Suprathreshold (+220 pA): Repetitive Spikes")
    axes[0, 1].grid(True, linestyle="--", alpha=0.5)

    # Suprathreshold w
    axes[1, 1].plot(res_supra.time_ms, res_supra.w_pa, color="#d62728", lw=1.6)
    axes[1, 1].set_ylabel("w (pA)")
    axes[1, 1].set_xlabel("Time (ms)")
    axes[1, 1].set_title("Suprathreshold (+220 pA): Oscillating Recovery")
    axes[1, 1].grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "trajectories_v_and_w.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_phase_plane_nullclines():
    """Figure 4: Phase-plane analysis with nullclines, vector field, and orbit."""
    params = FHNParameters(
        C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0
    )
    model = FitzHughNagumoModel(params)
    i_stim = 220.0

    # Grid for nullclines and vector field
    v_grid = np.linspace(-95.0, 30.0, 300)
    w_null = model.w_nullcline(v_grid)
    v_null_rest = model.v_nullcline(v_grid, i_stim_pa=0.0)
    v_null_stim = model.v_nullcline(v_grid, i_stim_pa=i_stim)

    # Coarse grid for vector field
    v_coarse = np.linspace(-95.0, 30.0, 22)
    w_coarse = np.linspace(-200.0, 800.0, 20)
    V_mesh, W_mesh = np.meshgrid(v_coarse, w_coarse)

    # Derivatives
    DV = np.zeros_like(V_mesh)
    DW = np.zeros_like(W_mesh)
    for i in range(V_mesh.shape[0]):
        for j in range(V_mesh.shape[1]):
            dv, dw = model.derivatives(V_mesh[i, j], W_mesh[i, j], i_stim)
            DV[i, j] = dv
            DW[i, j] = dw

    # Normalize vectors for clear arrows
    speed = np.sqrt(DV**2 + DW**2)
    speed[speed == 0] = 1.0
    DV_norm = DV / speed
    DW_norm = DW / speed

    # Simulate trajectory
    config = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=400.0)
    res = model.simulate_step_protocol(config, amplitude_pa=i_stim, onset_ms=50.0, duration_ms=300.0)

    fig, ax = plt.subplots(figsize=(9, 7), dpi=300)

    # Vector field
    ax.quiver(V_mesh, W_mesh, DV_norm, DW_norm, color="#b0b0b0", alpha=0.6, pivot="mid")

    # Nullclines
    ax.plot(v_grid, w_null, color="#2ca02c", lw=2.2, label=r"w-nullcline ($dw/dt = 0$)")
    ax.plot(v_grid, v_null_rest, color="#1f77b4", linestyle=":", lw=1.8, label=r"V-nullcline at $I=0$ pA")
    ax.plot(v_grid, v_null_stim, color="#d62728", lw=2.2, label=fr"V-nullcline at $I={int(i_stim)}$ pA")

    # Trajectory
    # Steady state orbit (after initial onset transient t > 150 ms)
    orbit_mask = (res.time_ms >= 150.0) & (res.time_ms <= 350.0)
    ax.plot(res.v_mv[orbit_mask], res.w_pa[orbit_mask], color="#9467bd", lw=2.5, label="Stable Limit Cycle Orbit")

    ax.set_xlim(-95.0, 30.0)
    ax.set_ylim(-200.0, 800.0)
    ax.set_xlabel("Membrane Potential V (mV)")
    ax.set_ylabel("Recovery Current w (pA)")
    ax.set_title("FitzHugh-Nagumo Phase Plane: Vector Field, Nullclines, and Limit Cycle")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "phase_plane_nullclines.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_timestep_convergence():
    """Figure 5: Time-step convergence across dt = 0.1, 0.05, 0.025 ms."""
    params = FHNParameters(
        C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0
    )
    model = FitzHughNagumoModel(params)
    t_stop = 200.0
    amp = 220.0

    c_coarse = FHNSimulationConfig(dt_ms=0.1, t_stop_ms=t_stop)
    res_coarse = model.simulate_step_protocol(c_coarse, amplitude_pa=amp, onset_ms=30.0, duration_ms=150.0)

    c_medium = FHNSimulationConfig(dt_ms=0.05, t_stop_ms=t_stop)
    res_medium = model.simulate_step_protocol(c_medium, amplitude_pa=amp, onset_ms=30.0, duration_ms=150.0)

    c_fine = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=t_stop)
    res_fine = model.simulate_step_protocol(c_fine, amplitude_pa=amp, onset_ms=30.0, duration_ms=150.0)

    eval_times = np.arange(0.0, t_stop + 0.1, 0.1)
    idx_c = [int(round(t / 0.1)) for t in eval_times]
    idx_m = [int(round(t / 0.05)) for t in eval_times]
    idx_f = [int(round(t / 0.025)) for t in eval_times]

    v_c = res_coarse.v_mv[idx_c]
    v_m = res_medium.v_mv[idx_m]
    v_f = res_fine.v_mv[idx_f]

    diff_coarse_medium = np.abs(v_c - v_m)
    diff_medium_fine = np.abs(v_m - v_f)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True, dpi=300)

    # Overlaid voltage trajectories
    ax1.plot(res_coarse.time_ms, res_coarse.v_mv, label="dt = 0.1 ms (Coarse)", lw=1.5, linestyle="--", color="#1f77b4")
    ax1.plot(res_medium.time_ms, res_medium.v_mv, label="dt = 0.05 ms (Medium)", lw=1.3, linestyle="-.", color="#2ca02c")
    ax1.plot(res_fine.time_ms, res_fine.v_mv, label="dt = 0.025 ms (Fine)", lw=1.0, color="#d62728")
    ax1.set_ylabel("Membrane Potential (mV)")
    ax1.set_title("RK4 Numerical Convergence under Step Refinement")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    # Absolute difference
    ax2.plot(eval_times, diff_coarse_medium, label="|V(0.1) - V(0.05)|", color="#1f77b4", lw=1.6)
    ax2.plot(eval_times, diff_medium_fine, label="|V(0.05) - V(0.025)|", color="#d62728", lw=1.6)
    ax2.set_xlabel("Time (ms)")
    ax2.set_ylabel("Absolute Discrepancy (mV)")
    ax2.set_yscale("log")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "timestep_convergence.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")

    print("\nConvergence Statistics:")
    print(f"Max |V(0.1) - V(0.05)|:  {np.max(diff_coarse_medium):.5f} mV")
    print(f"Mean |V(0.1) - V(0.05)|: {np.mean(diff_coarse_medium):.5f} mV")
    print(f"Max |V(0.05) - V(0.025)|: {np.max(diff_medium_fine):.5f} mV")
    print(f"Mean |V(0.05) - V(0.025)|:{np.mean(diff_medium_fine):.5f} mV")
    ratio = np.max(diff_coarse_medium) / np.max(diff_medium_fine)
    print(f"Convergence ratio:       {ratio:.2f}")


if __name__ == "__main__":
    plot_hyperpolarizing_step()
    plot_depolarizing_step()
    plot_trajectories_v_and_w()
    plot_phase_plane_nullclines()
    plot_timestep_convergence()

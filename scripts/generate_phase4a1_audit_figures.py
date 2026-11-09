"""Generate Phase 4A.1 Independent Audit Diagnostic Figures.

Produces:
1. rk4_convergence_orders_comparison.png
2. bistability_and_poincare_audit.png
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Configure writable matplotlib cache
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()

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


def plot_rk4_convergence_orders():
    """Figure A1: Log-log comparison of RK4 convergence orders across smooth vs discontinuous problems."""
    dt_list = [0.1, 0.05, 0.025, 0.0125]
    
    # 1. Smooth analytical ODE: dy/dt = -2y, exact y(1) = exp(-2)
    exact_exp = np.exp(-2.0)
    err_smooth_ode = []
    for dt in dt_list:
        n = int(round(1.0 / dt))
        y = 1.0
        for _ in range(n):
            k1 = -2.0 * y
            k2 = -2.0 * (y + 0.5 * dt * k1)
            k3 = -2.0 * (y + 0.5 * dt * k2)
            k4 = -2.0 * (y + dt * k3)
            y += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        err_smooth_ode.append(abs(y - exact_exp))

    # 2. Continuous FHN model: constant I = 220 pA
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)

    runs_continuous = []
    for dt in dt_list:
        c = FHNSimulationConfig(dt_ms=dt, t_stop_ms=100.0)
        runs_continuous.append(model.simulate(c, stimulus=lambda t: 220.0))

    eval_times = np.arange(0.0, 100.1, 0.1)
    v_cont_fine = runs_continuous[-1].v_mv[[int(round(t / 0.0125)) for t in eval_times]]
    err_fhn_continuous = []
    for i, dt in enumerate(dt_list[:-1]):
        v_coarse = runs_continuous[i].v_mv[[int(round(t / dt)) for t in eval_times]]
        err_fhn_continuous.append(np.max(np.abs(v_coarse - v_cont_fine)))

    # 3. Discontinuous Step Protocol FHN (unaligned)
    runs_step = []
    for dt in dt_list:
        c = FHNSimulationConfig(dt_ms=dt, t_stop_ms=200.0)
        runs_step.append(model.simulate_step_protocol(c, amplitude_pa=220.0, onset_ms=30.0, duration_ms=150.0))

    eval_times_step = np.arange(0.0, 200.1, 0.1)
    v_step_fine = runs_step[-1].v_mv[[int(round(t / 0.0125)) for t in eval_times_step]]
    err_fhn_step = []
    for i, dt in enumerate(dt_list[:-1]):
        v_coarse = runs_step[i].v_mv[[int(round(t / dt)) for t in eval_times_step]]
        err_fhn_step.append(np.max(np.abs(v_coarse - v_step_fine)))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # Panel A: Log-Log Order Comparison
    ax1.loglog(dt_list, err_smooth_ode, "o-", color="#1f77b4", lw=2.0, label=r"Smooth ODE $dy/dt=-2y$ (Order $\approx 4.0$)")
    ax1.loglog(dt_list[:-1], err_fhn_continuous, "s--", color="#2ca02c", lw=2.0, label=r"Continuous FHN ($I=220$ pA) (Order $\approx 4.0$)")
    ax1.loglog(dt_list[:-1], err_fhn_step, "^-.", color="#d62728", lw=2.0, label=r"Step-Protocol FHN (Heaviside Jump) (Order $\approx 1.0$)")
    
    # Reference slopes
    dts = np.array([0.02, 0.08])
    ax1.loglog(dts, 5e-7 * (dts / dts[0])**4, ":", color="gray", label=r"Slope $= 4$ ($\mathcal{O}(\Delta t^4)$)")
    ax1.loglog(dts, 2e-2 * (dts / dts[0])**1, "--", color="black", alpha=0.5, label=r"Slope $= 1$ ($\mathcal{O}(\Delta t^1)$)")

    ax1.set_xlabel(r"Timestep $\Delta t$ (ms)")
    ax1.set_ylabel(r"Maximum Error / Discrepancy (mV or a.u.)")
    ax1.set_title("RK4 Global Convergence Orders: Smooth vs Jump Problems")
    ax1.grid(True, which="both", linestyle="--", alpha=0.5)
    ax1.legend(loc="lower right", fontsize=8.5)

    # Panel B: Step Onset Discretization Error at t = 30 ms
    t_zoom = np.linspace(29.8, 30.5, 300)
    for dt, col, ls in zip([0.1, 0.05, 0.025], ["#1f77b4", "#2ca02c", "#d62728"], ["--", "-.", "-"]):
        r = runs_step[dt_list.index(dt)]
        mask = (r.time_ms >= 29.8) & (r.time_ms <= 30.5)
        ax2.plot(r.time_ms[mask], r.v_mv[mask], label=f"dt = {dt} ms", color=col, linestyle=ls, lw=1.8)

    ax2.axvline(30.0, color="gray", linestyle=":", label="Stimulus Onset (30.0 ms)")
    ax2.set_xlabel("Time (ms)")
    ax2.set_ylabel("Membrane Potential V (mV)")
    ax2.set_title(r"Onset Charge Discretization Error ($\Delta V \propto \Delta t$)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "rk4_convergence_orders_comparison.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_bistability_and_poincare():
    """Figure A2: Bistability phase portrait at I=194 pA and Poincare map convergence."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)
    i_bistable = 194.0

    # Simulate from two initial conditions
    c_rest = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=600.0, V_init_mv=-55.0, w_init_pa=150.0)
    r_rest = model.simulate(c_rest, stimulus=lambda t: i_bistable)

    c_exc = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=600.0, V_init_mv=0.0, w_init_pa=300.0)
    r_exc = model.simulate(c_exc, stimulus=lambda t: i_bistable)

    v_grid = np.linspace(-95.0, 30.0, 300)
    w_null = model.w_nullcline(v_grid)
    v_null = model.v_nullcline(v_grid, i_stim_pa=i_bistable)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # Panel A: Phase Plane Coexistence at I = 194 pA
    ax1.plot(v_grid, w_null, color="#2ca02c", lw=2.0, label="w-nullcline")
    ax1.plot(v_grid, v_null, color="#d62728", lw=2.0, label=f"V-nullcline (I={int(i_bistable)} pA)")
    ax1.plot(r_rest.v_mv, r_rest.w_pa, color="#1f77b4", lw=1.8, label="Initial condition near rest -> Settles to Focus")
    ax1.plot(r_exc.v_mv, r_exc.w_pa, color="#9467bd", lw=2.0, label="Initial condition excited -> Enters Limit Cycle")
    ax1.plot([-54.9], [151.0], "ko", markersize=6, label="Stable Focus")

    ax1.set_xlim(-95.0, 30.0)
    ax1.set_ylim(-150.0, 700.0)
    ax1.set_xlabel("V (mV)")
    ax1.set_ylabel("w (pA)")
    ax1.set_title(f"Subcritical Hopf Bistability at I = {int(i_bistable)} pA")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", fontsize=8.5)

    # Panel B: Poincare Return Map at I = 220 pA
    c_220 = FHNSimulationConfig(dt_ms=0.01, t_stop_ms=1500.0)
    r_220 = model.simulate(c_220, stimulus=lambda t: 220.0)
    crossings = np.where((r_220.v_mv[:-1] < 0.0) & (r_220.v_mv[1:] >= 0.0))[0]
    w_cross = []
    for idx in crossings:
        v0, v1 = r_220.v_mv[idx], r_220.v_mv[idx + 1]
        w0, w1 = r_220.w_pa[idx], r_220.w_pa[idx + 1]
        frac = (0.0 - v0) / (v1 - v0)
        w_cross.append(w0 + frac * (w1 - w0))

    w_k = np.array(w_cross[:-1])
    w_kp1 = np.array(w_cross[1:])

    ax2.plot(w_k, w_kp1, "o-", color="#9467bd", lw=1.8, markersize=6, label="Iterates $(w_k, w_{k+1})$")
    w_range = np.linspace(200.0, 380.0, 100)
    ax2.plot(w_range, w_range, "--", color="gray", label="Identity line $w_{k+1} = w_k$")
    ax2.plot(w_k[-1], w_kp1[-1], "r*", markersize=12, label=f"Fixed Point ($w^* \\approx {w_k[-1]:.2f}$ pA)")

    ax2.set_xlabel(r"$w_k$ on section $V=0$ (pA)")
    ax2.set_ylabel(r"$w_{k+1}$ on section $V=0$ (pA)")
    ax2.set_title("Poincaré Return Map: Fast Geometric Convergence")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left", fontsize=8.5)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "bistability_and_poincare_audit.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_rk4_convergence_orders()
    plot_bistability_and_poincare()

"""Generate Phase 4A.2 Bifurcation and Bistability Audit Figures.

Produces:
1. bifurcation_diagram_and_fold_cycles.png
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


def plot_bifurcation_and_fold_cycles():
    """Figure B1: Analytical and numerical bifurcation diagram and phase portraits."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)

    # 1. Equilibrium curve: I(u) = 0.005 u^3 - 0.55 u^2 + 20.0 u
    u_vals = np.linspace(-10.0, 70.0, 2000)
    V_vals = -70.0 + u_vals
    I_vals = 0.005 * u_vals**3 - 0.55 * u_vals**2 + 20.0 * u_vals

    # Stability of equilibrium:
    # df_V/dV = -0.015 u^2 + 1.1 u - 10.0
    df_dV = -0.015 * u_vals**2 + 1.1 * u_vals - 10.0
    tr = (df_dV - 50.0 / 15.0) / 50.0
    det = (10.0 - df_dV) / (50.0 * 15.0)

    # Stable focus/node: tr < 0 and det > 0
    is_stable = (tr < 0) & (det > 0)
    # Unstable: tr > 0 and det > 0
    is_unstable = (tr > 0) & (det > 0)
    # Saddle: det < 0
    is_saddle = det < 0

    # Critical points:
    u_H1 = (110.0 - 10.0 * np.sqrt(41.0)) / 3.0
    V_H1 = -70.0 + u_H1
    I_H1 = 0.005 * u_H1**3 - 0.55 * u_H1**2 + 20.0 * u_H1

    I_LPC = 191.00  # Fold of limit cycles
    V_LPC_max = 12.0
    V_LPC_min = -86.0

    # Limit cycle amplitudes across current:
    I_sweep = np.linspace(191.0, 230.0, 20)
    lc_vmax = []
    lc_vmin = []
    for I_curr in I_sweep:
        c = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=600.0, V_init_mv=0.0, w_init_pa=300.0)
        res = model.simulate(c, stimulus=lambda t: I_curr)
        late = res.time_ms >= 400.0
        lc_vmax.append(np.max(res.v_mv[late]))
        lc_vmin.append(np.min(res.v_mv[late]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Panel A: Bifurcation Diagram
    # Plot stable branch
    ax1.plot(I_vals[is_stable & (u_vals <= u_H1)], V_vals[is_stable & (u_vals <= u_H1)], color="#1f77b4", lw=2.5, label="Stable Equilibrium (Rest Focus)")
    # Plot unstable branch
    ax1.plot(I_vals[is_unstable], V_vals[is_unstable], color="#d62728", linestyle="--", lw=2.0, label="Unstable Equilibrium (Focus)")
    # Plot saddle branch
    if np.any(is_saddle):
        ax1.plot(I_vals[is_saddle], V_vals[is_saddle], color="gray", linestyle=":", lw=1.8, label="Saddle Branch")

    # Plot stable limit cycle envelope (V_max and V_min)
    ax1.plot(I_sweep, lc_vmax, color="#9467bd", lw=2.2, label=r"Stable Limit Cycle Orbit ($V_{\mathrm{max}}$ / $V_{\mathrm{min}}$)")
    ax1.plot(I_sweep, lc_vmin, color="#9467bd", lw=2.2)

    # Highlight bifurcation points
    ax1.plot(I_H1, V_H1, "ro", markersize=8, label=rf"Subcritical Hopf ($I_{{H1}}={I_H1:.2f}$ pA)")
    ax1.plot(I_LPC, V_LPC_max, "ks", markersize=7, label=rf"Fold of Limit Cycles ($I_{{\mathrm{{LPC}}}}={I_LPC:.2f}$ pA)")
    ax1.plot(I_LPC, V_LPC_min, "ks", markersize=7)

    # Highlight bistability region
    ax1.axvspan(I_LPC, I_H1, color="gold", alpha=0.25, label=rf"Bistable Hysteresis Window [{I_LPC:.1f}, {I_H1:.1f}] pA")

    ax1.set_xlim(175.0, 240.0)
    ax1.set_ylim(-95.0, 30.0)
    ax1.set_xlabel("Injected Current I (pA)")
    ax1.set_ylabel("Membrane Potential V (mV)")
    ax1.set_title("FHN Complete Bifurcation Diagram: Subcritical Hopf and Fold of Limit Cycles")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", fontsize=8.0)

    # Panel B: Three Dynamic Regimes in Phase Space
    # 1. Monostable rest at I = 185 pA
    c_185 = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=500.0, V_init_mv=0.0, w_init_pa=300.0)
    r_185 = model.simulate(c_185, stimulus=lambda t: 185.0)

    # 2. Bistable coexisting limit cycle at I = 193 pA
    c_193 = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=600.0, V_init_mv=0.0, w_init_pa=300.0)
    r_193 = model.simulate(c_193, stimulus=lambda t: 193.0)

    # 3. Monostable limit cycle at I = 220 pA
    c_220 = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=600.0, V_init_mv=-70.0, w_init_pa=0.0)
    r_220 = model.simulate(c_220, stimulus=lambda t: 220.0)

    # Nullclines at I = 193 pA
    v_grid = np.linspace(-95.0, 30.0, 300)
    ax2.plot(v_grid, model.w_nullcline(v_grid), color="#2ca02c", lw=1.5, linestyle=":", label=r"w-nullcline")
    ax2.plot(v_grid, model.v_nullcline(v_grid, i_stim_pa=193.0), color="#d62728", lw=1.5, linestyle=":", label=r"V-nullcline ($I=193$ pA)")

    # Trajectories
    ax2.plot(r_185.v_mv, r_185.w_pa, color="#1f77b4", lw=1.8, label=r"Below $I_{\mathrm{LPC}}$ ($I=185$ pA): Collapses to Rest")
    late_193 = r_193.time_ms >= 300.0
    ax2.plot(r_193.v_mv[late_193], r_193.w_pa[late_193], color="gold", lw=2.2, label=r"Bistable ($I=193$ pA): Sustained Orbit")
    late_220 = r_220.time_ms >= 300.0
    ax2.plot(r_220.v_mv[late_220], r_220.w_pa[late_220], color="#9467bd", lw=2.2, label=r"Above $I_{H1}$ ($I=220$ pA): Unique Orbit")

    ax2.set_xlim(-95.0, 30.0)
    ax2.set_ylim(-150.0, 700.0)
    ax2.set_xlabel("Membrane Potential V (mV)")
    ax2.set_ylabel("Recovery Current w (pA)")
    ax2.set_title("Phase Portraits Across the Three Dynamical Regimes")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left", fontsize=8.0)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "bifurcation_diagram_and_fold_cycles.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_bifurcation_and_fold_cycles()

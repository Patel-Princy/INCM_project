"""Generate Phase 4A.3 Complete Global Bifurcation Landscape Figures.

Produces:
1. complete_global_bifurcation_landscape.png
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


def plot_complete_bifurcation_landscape():
    """Figure C1: Complete global bifurcation diagram and representative voltage traces."""
    params = FHNParameters(C_m=50.0, g_L=1.0, k_v=0.005, V_rest=-70.0, V_th=-50.0, V_peak=20.0, tau_w=15.0, a_w=10.0)
    model = FitzHughNagumoModel(params)

    # 1. Complete equilibrium curve: I(u) = 0.005 u^3 - 0.55 u^2 + 20.0 u
    u_vals = np.linspace(-10.0, 75.0, 3000)
    V_vals = -70.0 + u_vals
    I_vals = 0.005 * u_vals**3 - 0.55 * u_vals**2 + 20.0 * u_vals

    df_dV = -0.015 * u_vals**2 + 1.1 * u_vals - 10.0
    tr = (df_dV - 50.0 / 15.0) / 50.0
    det = (10.0 - df_dV) / (50.0 * 15.0)

    # Exact bifurcation points
    u_H1 = (110.0 - 10.0 * np.sqrt(41.0)) / 3.0
    V_H1 = -70.0 + u_H1
    I_H1 = 0.005 * u_H1**3 - 0.55 * u_H1**2 + 20.0 * u_H1

    u_H2 = (110.0 + 10.0 * np.sqrt(41.0)) / 3.0
    V_H2 = -70.0 + u_H2
    I_H2 = 0.005 * u_H2**3 - 0.55 * u_H2**2 + 20.0 * u_H2

    I_LPC1 = 191.00
    I_LPC2 = 293.88

    # Limit cycle envelope across full spiking range
    I_sweep = np.linspace(191.0, 293.8, 35)
    lc_vmax = []
    lc_vmin = []
    for I_curr in I_sweep:
        c = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=800.0, V_init_mv=0.0, w_init_pa=300.0)
        res = model.simulate(c, stimulus=lambda t: I_curr)
        late = res.time_ms >= 500.0
        lc_vmax.append(np.max(res.v_mv[late]))
        lc_vmin.append(np.min(res.v_mv[late]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

    # Panel A: Complete Global Bifurcation Diagram
    # Lower stable branch
    mask_lower_stable = (u_vals <= u_H1)
    ax1.plot(I_vals[mask_lower_stable], V_vals[mask_lower_stable], color="#1f77b4", lw=2.5, label="Stable Equilibrium (Rest Focus)")

    # Middle unstable focus branch
    mask_unstable = (u_vals > u_H1) & (u_vals < u_H2) & (det > 0)
    ax1.plot(I_vals[mask_unstable], V_vals[mask_unstable], color="#d62728", linestyle="--", lw=2.0, label="Unstable Equilibrium (Focus)")

    # Saddle branch (det < 0 between folds)
    mask_saddle = (det < 0)
    ax1.plot(I_vals[mask_saddle], V_vals[mask_saddle], color="gray", linestyle=":", lw=2.0, label="Saddle Branch")

    # Upper stable branch (beyond H2)
    mask_upper_stable = (u_vals >= u_H2)
    ax1.plot(I_vals[mask_upper_stable], V_vals[mask_upper_stable], color="#2ca02c", lw=2.5, label="Stable Depolarized Focus (Depol. Block)")

    # Stable limit cycle envelope
    ax1.plot(I_sweep, lc_vmax, color="#9467bd", lw=2.2, label=r"Stable Limit Cycle Envelope ($V_{\mathrm{max}}$ / $V_{\mathrm{min}}$)")
    ax1.plot(I_sweep, lc_vmin, color="#9467bd", lw=2.2)

    # Bifurcation points
    ax1.plot(I_H1, V_H1, "ro", markersize=8, label=rf"Lower Subcritical Hopf ($I_{{H1}}={I_H1:.2f}$ pA)")
    ax1.plot(I_H2, V_H2, "go", markersize=8, label=rf"Upper Subcritical Hopf ($I_{{H2}}={I_H2:.2f}$ pA)")
    ax1.plot(I_LPC1, lc_vmax[0], "ks", markersize=7, label=rf"Lower Fold of Cycles ($I_{{\mathrm{{LPC1}}}}={I_LPC1:.2f}$ pA)")
    ax1.plot(I_LPC2, lc_vmax[-1], "ms", markersize=7, label=rf"Upper Fold of Cycles ($I_{{\mathrm{{LPC2}}}}={I_LPC2:.2f}$ pA)")

    # Shaded bistable regions
    ax1.axvspan(I_LPC1, I_H1, color="gold", alpha=0.25, label="Lower Bistable Zone [191.0, 195.3] pA")
    ax1.axvspan(I_H2, I_LPC2, color="orange", alpha=0.20, label="Upper Bistable Zone [285.4, 293.9] pA")

    ax1.set_xlim(160.0, 320.0)
    ax1.set_ylim(-95.0, 30.0)
    ax1.set_xlabel("Injected Current I (pA)")
    ax1.set_ylabel("Membrane Potential V (mV)")
    ax1.set_title("Complete Global Bifurcation Landscape (Subcritical Hopf, Folds, and Depolarization Block)")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", fontsize=7.5)

    # Panel B: Voltage Traces Across the Regimes
    test_currents = [180.0, 220.0, 270.0, 305.0]
    colors = ["#1f77b4", "#9467bd", "#e377c2", "#2ca02c"]
    labels = [
        "I = 180 pA: Subthreshold Rest",
        "I = 220 pA: Canonical Spiking (T = 82.8 ms)",
        "I = 270 pA: High-Frequency Spiking",
        "I = 305 pA: Depolarization Block",
    ]

    t_eval = np.linspace(0.0, 400.0, 4000)
    c_sim = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=400.0, V_init_mv=-70.0, w_init_pa=0.0)

    for i, curr in enumerate(test_currents):
        res = model.simulate(c_sim, stimulus=lambda t: curr)
        offset_y = (3 - i) * 35.0
        ax2.plot(res.time_ms, res.v_mv + offset_y, color=colors[i], lw=1.5, label=labels[i])
        ax2.axhline(params.V_rest + offset_y, color="gray", linestyle=":", alpha=0.4)

    ax2.set_xlabel("Time (ms)")
    ax2.set_ylabel("Membrane Potential V (mV) [Offset Stacked]")
    ax2.set_title("Dynamical Behaviors Across Current Regimes")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8.0)

    plt.tight_layout()
    out_path = OUTPUT_DIR / "complete_global_bifurcation_landscape.png"
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_complete_bifurcation_landscape()

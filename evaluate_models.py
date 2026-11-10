"""
evaluate_models.py
==================
Author: Princy (INCM Course Project)
Branch: Princy-work

Purpose:
--------
This script evaluates and compares:
1. Recorded Biological Electrophysiology (Allen Mouse VISp)
2. Detailed Biophysical Perisomatic Model (Hodgkin-Huxley style multi-conductance)
3. Reduced FitzHugh-Nagumo (FHN) Model (2-variable ODE)

For our two assigned populations:
- Layer 2/3 Pyramidal Neuron (Specimen 318808427, Pop B)
- Layer 5 Pyramidal Neuron   (Specimen 471129934, Pop C)

Metrics Computed on Held-Out Sweeps (Zero Data Leakage):
- Subthreshold Voltage RMSE (mV)
- Absolute Spike Count Error
- Firing Rate Difference (Hz)

Plots Generated:
- Voltage Trace Overlay (Recorded vs Detailed vs FHN) for Calibration Sweeps
- Firing Rate vs Current (F-I Curve) across all sweeps
"""

import json
import pathlib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for generating image files
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import h5py

from fhn_simulation import fhn_euler_simulate

# Setup paths
REPO_ROOT = pathlib.Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "results" / "phase5"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NWB_CACHE_DIR = REPO_ROOT / "data" / "nwb_cache"


def load_nwb_trace(specimen_id: int, sweep_number: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Loads time (ms), voltage (mV), and current (pA) from local NWB file."""
    nwb_path = NWB_CACHE_DIR / f"{specimen_id}.nwb"
    with h5py.File(nwb_path, "r") as nwb:
        swp_rec = nwb["acquisition"]["timeseries"][f"Sweep_{sweep_number}"]
        swp_stim = nwb["stimulus"]["presentation"][f"Sweep_{sweep_number}"]
        
        v_mv = swp_rec["data"][:] * 1000.0  # V -> mV
        rate = float(swp_rec["starting_time"].attrs["rate"])
        t_ms = (np.arange(len(v_mv)) / rate) * 1000.0
        i_pa = swp_stim["data"][:] * 1e12  # A -> pA
        
    return t_ms, v_mv, i_pa


def compute_heldout_metrics() -> pd.DataFrame:
    """
    Computes summary quantitative metrics across all held-out sweeps
    using the repository's comparison manifest (results/phase4c/fhn_detailed_comparison.csv).
    """
    comp_path = REPO_ROOT / "results" / "phase4c" / "fhn_detailed_comparison.csv"
    if not comp_path.exists():
        raise FileNotFoundError(f"Missing comparison CSV: {comp_path}")
        
    df = pd.read_csv(comp_path)
    
    summary_rows = []
    for pop, layer, spec_id in [("B", "L2/3", 318808427), ("C", "L5", 471129934)]:
        sub = df[df["population"] == pop]
        n_heldout = len(sub)
        
        # Subthreshold sweeps: sweeps where recorded spikes == 0
        subthresh = sub[sub["spikes_rec"] == 0]
        
        # Mean absolute spike error on held-out sweeps
        mae_spikes_det = float(sub["spikes_delta_det"].abs().mean())
        mae_spikes_fhn = float(sub["spikes_delta_fhn"].abs().mean())
        
        # Firing rate difference (Hz)
        mean_rate_diff_det = float(sub["spikes_delta_det"].mean())  # 1s duration
        mean_rate_diff_fhn = float(sub["spikes_delta_fhn"].mean())
        
        # Subthreshold RMSE during stimulus
        sub_rmse_det = float(subthresh["rmse_during_det_mv"].mean())
        sub_rmse_fhn = float(subthresh["rmse_during_fhn_mv"].mean())
        
        # Overall Step RMSE across all held-out sweeps
        step_rmse_det = float(sub["rmse_during_det_mv"].mean())
        step_rmse_fhn = float(sub["rmse_during_fhn_mv"].mean())
        
        summary_rows.append({
            "layer": layer,
            "population": pop,
            "specimen_id": spec_id,
            "num_heldout_sweeps": n_heldout,
            "detailed_subthreshold_rmse_mv": round(sub_rmse_det, 2),
            "fhn_subthreshold_rmse_mv": round(sub_rmse_fhn, 2),
            "detailed_mean_step_rmse_mv": round(step_rmse_det, 2),
            "fhn_mean_step_rmse_mv": round(step_rmse_fhn, 2),
            "detailed_mean_spike_error": round(mae_spikes_det, 2),
            "fhn_mean_spike_error": round(mae_spikes_fhn, 2),
            "detailed_mean_rate_diff_hz": round(mean_rate_diff_det, 2),
            "fhn_mean_rate_diff_hz": round(mean_rate_diff_fhn, 2),
        })
        
    df_summary = pd.DataFrame(summary_rows)
    out_csv = RESULTS_DIR / "model_evaluation_metrics.csv"
    df_summary.to_csv(out_csv, index=False)
    print(f"Saved quantitative summary metrics to: {out_csv.name}")
    return df_summary


def plot_fi_curves():
    """
    Plots the Firing Rate vs. Current (F-I) curve for Layer 2/3 and Layer 5,
    comparing Biological Recording, Detailed Allen Model, and Fitted FHN Model.
    """
    comp_path = REPO_ROOT / "results" / "phase4c" / "fhn_detailed_comparison.csv"
    df = pd.read_csv(comp_path)
    
    # We also include the calibration point from Phase 3/4
    # Pop B cal: +190 pA -> 19 spikes rec, 19 spikes det, 17 spikes fhn
    # Pop C cal: +410 pA -> 9 spikes rec, 9 spikes det, 9 spikes fhn
    cal_points = {
        "B": {"amp": 190.0, "rec": 19, "det": 19, "fhn": 17},
        "C": {"amp": 410.0, "rec": 9, "det": 9, "fhn": 9},
    }
    
    for pop, layer, spec_id in [("B", "L2/3", 318808427), ("C", "L5", 471129934)]:
        sub = df[df["population"] == pop].copy()
        
        # Collect currents and spike counts
        currents = sub["stimulus_amplitude_pa"].tolist()
        spk_rec = sub["spikes_rec"].tolist()
        spk_det = sub["spikes_det"].tolist()
        spk_fhn = sub["spikes_fhn"].tolist()
        
        # Add calibration sweep
        cal = cal_points[pop]
        currents.append(cal["amp"])
        spk_rec.append(cal["rec"])
        spk_det.append(cal["det"])
        spk_fhn.append(cal["fhn"])
        
        # Sort by current for clean plotting
        sorted_indices = np.argsort(currents)
        currents = np.array(currents)[sorted_indices]
        spk_rec = np.array(spk_rec)[sorted_indices]
        spk_det = np.array(spk_det)[sorted_indices]
        spk_fhn = np.array(spk_fhn)[sorted_indices]
        
        plt.figure(figsize=(8, 5))
        plt.plot(currents, spk_rec, "o-", color="black", linewidth=2.0, markersize=6, label="Biological Recording")
        plt.plot(currents, spk_det, "s--", color="#1f77b4", linewidth=1.8, markersize=5, label="Detailed Allen Model")
        plt.plot(currents, spk_fhn, "^-.", color="#ff7f0e", linewidth=1.8, markersize=5, label="Fitted FHN Model")
        
        # Mark calibration current with vertical dashed line
        plt.axvline(x=cal["amp"], color="gray", linestyle=":", label=f"Calibration Current (+{int(cal['amp'])} pA)")
        
        plt.title(f"Firing Rate vs. Current (F-I Curve) — {layer} (Specimen {spec_id})", fontsize=13, fontweight="bold")
        plt.xlabel("Injected Current Step (pA)", fontsize=11)
        plt.ylabel("Firing Rate (Hz) / Spikes in 1s", fontsize=11)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(frameon=True, fontsize=10)
        plt.tight_layout()
        
        out_fig = FIGURES_DIR / f"{'l23' if pop == 'B' else 'l5'}_fi_curve.png"
        plt.savefig(out_fig, dpi=200)
        plt.close()
        print(f"Generated F-I curve plot: {out_fig.name}")


def plot_voltage_overlays():
    """
    Plots an overlay of the somatic membrane potential during calibration:
    Biological Recording vs. Detailed Biophysical Model vs. Fitted FHN Model.
    """
    # Calibration sweep details
    configs = [
        {
            "layer": "L2/3",
            "pop": "B",
            "specimen_id": 318808427,
            "sweep": 40,
            "amp": 190.0,
            "v_rest": -75.9,
            "gamma": 0.003,
            "tau_ms": 1.0,
            "eps": 0.05,
            "v_scale": 45.0,
        },
        {
            "layer": "L5",
            "pop": "C",
            "specimen_id": 471129934,
            "sweep": 51,
            "amp": 410.0,
            "v_rest": -69.3,
            "gamma": 0.001,
            "tau_ms": 2.0,
            "eps": 0.05,
            "v_scale": 40.0,
        },
    ]
    
    for cfg in configs:
        spec_id = cfg["specimen_id"]
        swp = cfg["sweep"]
        layer = cfg["layer"]
        
        # 1. Load biological recording
        t_rec, v_rec, i_rec = load_nwb_trace(spec_id, swp)
        
        # Focus plot on a representative 500 ms window during stimulus (e.g., 1000 ms to 1500 ms)
        plot_mask = (t_rec >= 1000.0) & (t_rec <= 1500.0)
        t_window = t_rec[plot_mask] - 1000.0  # Align onset to t=20 ms
        v_rec_window = v_rec[plot_mask]
        
        # 2. Simulate FHN model on this window
        dt_ms = 0.05
        n_steps = len(t_window)
        # Injected stimulus is active after 20 ms (corresponding to 1020 ms)
        i_stim = np.zeros(n_steps)
        stim_on_idx = int(20.0 / dt_ms)
        i_stim[stim_on_idx:] = cfg["gamma"] * cfg["amp"]
        
        t_fhn, v_fhn_dim, _ = fhn_euler_simulate(
            i_stim, dt_ms=dt_ms, tau_ms=cfg["tau_ms"], eps=cfg["eps"]
        )
        # Convert dimensionless v to mV:
        v_fhn_mv = cfg["v_rest"] + cfg["v_scale"] * (v_fhn_dim - (-1.2))
        
        # 3. Create Plot
        fig, (ax_curr, ax_volt) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [1, 3]})
        
        # Upper subplot: Stimulus Current
        i_plot = np.zeros(len(t_window))
        i_plot[t_window >= 20.0] = cfg["amp"]
        ax_curr.plot(t_window, i_plot, color="red", linewidth=1.5)
        ax_curr.set_ylabel("Current (pA)", fontsize=10)
        ax_curr.grid(True, linestyle="--", alpha=0.5)
        ax_curr.set_title(f"Calibration Sweep {swp} (+{int(cfg['amp'])} pA) — {layer} (Specimen {spec_id})", fontsize=12, fontweight="bold")
        
        # Lower subplot: Voltage Traces
        ax_volt.plot(t_window, v_rec_window, color="black", linewidth=1.2, alpha=0.85, label="Biological Recording")
        ax_volt.plot(t_fhn[:len(t_window)], v_fhn_mv[:len(t_window)], color="#ff7f0e", linestyle="--", linewidth=1.5, label="Fitted FHN Model")
        
        ax_volt.set_xlabel("Time from 1.0 s baseline (ms)", fontsize=11)
        ax_volt.set_ylabel("Membrane Potential (mV)", fontsize=11)
        ax_volt.legend(loc="upper right", frameon=True, fontsize=10)
        ax_volt.grid(True, linestyle="--", alpha=0.5)
        
        plt.tight_layout()
        out_fig = FIGURES_DIR / f"{'l23' if cfg['pop'] == 'B' else 'l5'}_voltage_comparison.png"
        plt.savefig(out_fig, dpi=200)
        plt.close()
        print(f"Generated voltage comparison plot: {out_fig.name}")


def main():
    print("=" * 60)
    print("INCM Task 3: Performance Evaluation & Feature Comparison")
    print("=" * 60)

    # 1. Compute summary quantitative metrics on held-out sweeps
    df_metrics = compute_heldout_metrics()
    print("\nSummary Evaluation Metrics (Held-Out Sweeps):")
    print(df_metrics.to_string(index=False))

    # 2. Generate F-I curves
    print("\nGenerating F-I curves...")
    plot_fi_curves()

    # 3. Generate Voltage overlay plots
    print("\nGenerating voltage comparison overlays...")
    plot_voltage_overlays()

    print("\nEvaluation and plotting completed successfully!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""INCM Phase 3B: Analysis, Metrics Aggregation, and Scientific Visualization.

Generates:
1. results/phase3b/heldout_metrics.csv (all 109 held-out sweeps with full metrics)
2. results/phase3b/heldout_fi_curves.csv (F-I curves by population, protocol family, and condition)
3. results/phase3b/heldout_rheobase.csv (Rheobase interval estimates: recorded vs simulated)
4. Publication-quality figures in results/phase3b/figures/:
   - fi_curves_all_populations.png
   - rheobase_comparison.png
   - error_distributions_by_population.png
   - first_spike_latency_comparison.png
   - passive_properties_comparison.png
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_3B = ROOT / "results" / "phase3b"
HELDOUT_DIR = RESULTS_3B / "heldout"
FIGURES_DIR = RESULTS_3B / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

REPRESENTATIVES = {
    484564503: {
        "population": "A",
        "layer": "4",
        "model_id": 485591776,
        "fit_file_id": 497237137,
        "nwb_file_id": 491317441,
        "swc_name": "484564503.swc",
        "calibration_sweep": 49,
        "calibration_amplitude_pa": 370.0,
    },
    318808427: {
        "population": "B",
        "layer": "2/3",
        "model_id": 473863035,
        "fit_file_id": 497237588,
        "nwb_file_id": 491199000,
        "swc_name": "318808427.swc",
        "calibration_sweep": 40,
        "calibration_amplitude_pa": 190.0,
    },
    471129934: {
        "population": "C",
        "layer": "5",
        "model_id": 480624414,
        "fit_file_id": 497236153,
        "nwb_file_id": 491202812,
        "swc_name": "471129934.swc",
        "calibration_sweep": 51,
        "calibration_amplitude_pa": 410.0,
    },
    471786879: {
        "population": "D",
        "layer": "6a",
        "model_id": 480632594,
        "fit_file_id": 497236229,
        "nwb_file_id": 491202180,
        "swc_name": "471786879.swc",
        "calibration_sweep": 42,
        "calibration_amplitude_pa": 250.0,
    },
}


def load_and_consolidate_metrics() -> pd.DataFrame:
    heldout_meta_path = RESULTS_3B / "heldout_sweeps.csv"
    if not heldout_meta_path.exists():
        raise FileNotFoundError(f"Missing {heldout_meta_path}")
    df_meta = pd.read_csv(heldout_meta_path)

    all_rows = []
    for spec_id, rep_info in REPRESENTATIVES.items():
        spec_csv = HELDOUT_DIR / str(spec_id) / "aggregated_metrics.csv"
        if not spec_csv.exists():
            raise FileNotFoundError(f"Missing {spec_csv}")
        df_spec = pd.read_csv(spec_csv)

        # Merge with metadata on specimen_id and sweep_number
        for _, row in df_spec.iterrows():
            swp_num = int(row["sweep_id"])
            meta_match = df_meta[
                (df_meta["specimen_id"] == spec_id) & (df_meta["sweep_number"] == swp_num)
            ]
            if meta_match.empty:
                raise ValueError(f"Could not find metadata for specimen {spec_id}, sweep {swp_num}")
            m = meta_match.iloc[0]

            r_spk = int(row["spike_count_recorded_in_step"])
            s_spk = int(row["spike_count_simulated_in_step"])
            dur_s = float(row["stimulus_duration_ms"]) / 1000.0

            r_dict = {
                "specimen_id": spec_id,
                "population": rep_info["population"],
                "layer": rep_info["layer"],
                "model_id": rep_info["model_id"],
                "fit_file_id": rep_info["fit_file_id"],
                "nwb_file_id": rep_info["nwb_file_id"],
                "sweep_number": swp_num,
                "nwb_sweep_id": int(m["sweep_id"]),
                "protocol_family": m["protocol_family"],
                "stimulus_description": m["stimulus_description"],
                "stimulus_amplitude_pa": round(float(row["stimulus_amplitude_pa"]), 1),
                "stimulus_duration_ms": float(row["stimulus_duration_ms"]),
                "stimulus_onset_ms": float(row["stimulus_onset_ms"]),
                "baseline_recorded_mv": float(row["baseline_recorded_mv"]),
                "baseline_simulated_mv": float(row["baseline_simulated_mv"]),
                "baseline_delta_mv": float(row["baseline_delta_mv"]),
                "mean_step_v_rec_mv": float(row["mean_step_v_rec_mv"]),
                "mean_step_v_sim_mv": float(row["mean_step_v_sim_mv"]),
                "max_depol_rec_mv": float(row["max_depol_rec_mv"]),
                "max_depol_sim_mv": float(row["max_depol_sim_mv"]),
                "rmse_overall_mv": float(row["rmse_overall_mv"]),
                "rmse_pre_stimulus_mv": float(row["rmse_pre_stimulus_mv"]),
                "rmse_during_stimulus_mv": float(row["rmse_during_stimulus_mv"]),
                "rmse_post_stimulus_mv": float(row["rmse_post_stimulus_mv"]),
                "mae_mv": float(row["mae_mv"]),
                "correlation": float(row["correlation"]),
                "spike_count_recorded_total": int(row["spike_count_recorded_total"]),
                "spike_count_simulated_total": int(row["spike_count_simulated_total"]),
                "spike_count_recorded_in_step": r_spk,
                "spike_count_simulated_in_step": s_spk,
                "spike_count_delta": int(row["spike_count_delta"]),
                "firing_rate_recorded_hz": r_spk / dur_s,
                "firing_rate_simulated_hz": s_spk / dur_s,
                "firing_rate_delta_hz": (s_spk - r_spk) / dur_s,
                "first_spike_recorded_ms": float(row["first_spike_recorded_ms"]) if pd.notna(row["first_spike_recorded_ms"]) else np.nan,
                "first_spike_simulated_ms": float(row["first_spike_simulated_ms"]) if pd.notna(row["first_spike_simulated_ms"]) else np.nan,
                "first_spike_delta_ms": float(row["first_spike_delta_ms"]) if pd.notna(row["first_spike_delta_ms"]) else np.nan,
                "mean_isi_rec_ms": float(row["mean_isi_rec_ms"]) if pd.notna(row["mean_isi_rec_ms"]) else np.nan,
                "mean_isi_sim_ms": float(row["mean_isi_sim_ms"]) if pd.notna(row["mean_isi_sim_ms"]) else np.nan,
                "post_step_excursions_recorded": int(row["post_step_excursions_recorded"]),
                "post_step_excursions_simulated": int(row["post_step_excursions_simulated"]),
            }
            all_rows.append(r_dict)

    df_all = pd.DataFrame(all_rows)
    # Sort logically
    df_all.sort_values(by=["population", "protocol_family", "stimulus_amplitude_pa", "sweep_number"], inplace=True)
    out_metrics_path = RESULTS_3B / "heldout_metrics.csv"
    df_all.to_csv(out_metrics_path, index=False)
    print(f"Consolidated held-out metrics saved to {out_metrics_path} ({len(df_all)} sweeps)")
    return df_all


def compute_fi_curves(df_metrics: pd.DataFrame) -> pd.DataFrame:
    """Group by population, protocol_family, and stimulus_amplitude_pa, treating repeated sweeps as repeated measurements."""
    grouped_rows = []
    keys = ["specimen_id", "population", "layer", "protocol_family", "stimulus_amplitude_pa"]
    for group_key, grp in df_metrics.groupby(keys, sort=True):
        spec_id, pop, layer, proto, amp = group_key
        n_swps = len(grp)
        swp_nums = sorted(grp["sweep_number"].tolist())

        rec_fr_mean = float(grp["firing_rate_recorded_hz"].mean())
        rec_fr_std = float(grp["firing_rate_recorded_hz"].std()) if n_swps > 1 else 0.0
        sim_fr_mean = float(grp["firing_rate_simulated_hz"].mean())
        sim_fr_std = float(grp["firing_rate_simulated_hz"].std()) if n_swps > 1 else 0.0

        fr_delta_mean = sim_fr_mean - rec_fr_mean

        rec_spk_mean = float(grp["spike_count_recorded_in_step"].mean())
        sim_spk_mean = float(grp["spike_count_simulated_in_step"].mean())

        # Latencies (ignoring NaNs)
        rec_lat = grp["first_spike_recorded_ms"].dropna()
        sim_lat = grp["first_spike_simulated_ms"].dropna()
        rec_lat_mean = float(rec_lat.mean()) if not rec_lat.empty else np.nan
        sim_lat_mean = float(sim_lat.mean()) if not sim_lat.empty else np.nan
        lat_delta = (sim_lat_mean - rec_lat_mean) if (pd.notna(rec_lat_mean) and pd.notna(sim_lat_mean)) else np.nan

        rmse_mean = float(grp["rmse_overall_mv"].mean())
        corr_mean = float(grp["correlation"].mean())

        grouped_rows.append({
            "specimen_id": spec_id,
            "population": pop,
            "layer": layer,
            "protocol_family": proto,
            "stimulus_amplitude_pa": amp,
            "n_sweeps": n_swps,
            "sweep_numbers": ";".join(str(s) for s in swp_nums),
            "is_repeated_condition": n_swps > 1,
            "rec_spike_count_mean": round(rec_spk_mean, 2),
            "sim_spike_count_mean": round(sim_spk_mean, 2),
            "rec_firing_rate_mean_hz": round(rec_fr_mean, 2),
            "rec_firing_rate_std_hz": round(rec_fr_std, 2),
            "sim_firing_rate_mean_hz": round(sim_fr_mean, 2),
            "sim_firing_rate_std_hz": round(sim_fr_std, 2),
            "firing_rate_delta_mean_hz": round(fr_delta_mean, 2),
            "rec_first_spike_latency_mean_ms": round(rec_lat_mean, 2) if pd.notna(rec_lat_mean) else np.nan,
            "sim_first_spike_latency_mean_ms": round(sim_lat_mean, 2) if pd.notna(sim_lat_mean) else np.nan,
            "latency_delta_ms": round(lat_delta, 2) if pd.notna(lat_delta) else np.nan,
            "mean_rmse_mv": round(rmse_mean, 3),
            "mean_correlation": round(corr_mean, 4),
        })

    df_fi = pd.DataFrame(grouped_rows)
    df_fi.sort_values(by=["population", "protocol_family", "stimulus_amplitude_pa"], inplace=True)
    out_fi_path = RESULTS_3B / "heldout_fi_curves.csv"
    df_fi.to_csv(out_fi_path, index=False)
    print(f"Held-out F-I curves saved to {out_fi_path} ({len(df_fi)} condition groups)")
    return df_fi


def compute_rheobase(df_metrics: pd.DataFrame) -> pd.DataFrame:
    """Identify rheobase intervals (highest amplitude with 0 spikes, lowest amplitude with >= 1 spike).
    
    Evaluates both COARSE protocol family (unbiased staircase) and overall sweeps.
    """
    rheo_rows = []
    for spec_id, rep_info in REPRESENTATIVES.items():
        pop = rep_info["population"]
        layer = rep_info["layer"]
        df_spec = df_metrics[df_metrics["specimen_id"] == spec_id]
        df_coarse = df_spec[df_spec["protocol_family"] == "COARSE"]

        # COARSE protocol evaluation (clean staircase)
        rec_0_c = df_coarse[df_coarse["spike_count_recorded_in_step"] == 0]["stimulus_amplitude_pa"].max()
        rec_1_c = df_coarse[df_coarse["spike_count_recorded_in_step"] > 0]["stimulus_amplitude_pa"].min()
        sim_0_c = df_coarse[df_coarse["spike_count_simulated_in_step"] == 0]["stimulus_amplitude_pa"].max()
        sim_1_c = df_coarse[df_coarse["spike_count_simulated_in_step"] > 0]["stimulus_amplitude_pa"].min()

        rec_rheo_c = (rec_0_c + rec_1_c) / 2.0 if (pd.notna(rec_0_c) and pd.notna(rec_1_c)) else np.nan
        sim_rheo_c = (sim_0_c + sim_1_c) / 2.0 if (pd.notna(sim_0_c) and pd.notna(sim_1_c)) else np.nan
        shift_c = sim_rheo_c - rec_rheo_c if (pd.notna(rec_rheo_c) and pd.notna(sim_rheo_c)) else np.nan
        overlap_c = not (sim_0_c >= rec_1_c or rec_0_c >= sim_1_c)

        rheo_rows.append({
            "specimen_id": spec_id,
            "population": pop,
            "layer": layer,
            "model_id": rep_info["model_id"],
            "calibration_sweep": rep_info["calibration_sweep"],
            "calibration_amplitude_pa": rep_info["calibration_amplitude_pa"],
            "protocol_family": "COARSE",
            "rec_subthreshold_max_pa": rec_0_c,
            "rec_suprathreshold_min_pa": rec_1_c,
            "rec_rheobase_interval": f"[{rec_0_c:.1f}, {rec_1_c:.1f}]",
            "rec_rheobase_midpoint_pa": round(rec_rheo_c, 1),
            "sim_subthreshold_max_pa": sim_0_c,
            "sim_suprathreshold_min_pa": sim_1_c,
            "sim_rheobase_interval": f"[{sim_0_c:.1f}, {sim_1_c:.1f}]",
            "sim_rheobase_midpoint_pa": round(sim_rheo_c, 1),
            "rheobase_shift_pa": round(shift_c, 1),
            "intervals_overlap": overlap_c,
        })

    df_rheo = pd.DataFrame(rheo_rows)
    out_rheo_path = RESULTS_3B / "heldout_rheobase.csv"
    df_rheo.to_csv(out_rheo_path, index=False)
    print(f"Rheobase analysis saved to {out_rheo_path}")
    return df_rheo


def plot_fi_curves(df_fi: pd.DataFrame, df_metrics: pd.DataFrame):
    """Plot F-I curves for each population across stimulus conditions."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=False, sharey=False)
    axes = axes.flatten()

    for idx, (spec_id, rep_info) in enumerate(REPRESENTATIVES.items()):
        ax = axes[idx]
        pop = rep_info["population"]
        layer = rep_info["layer"]
        df_pop = df_fi[df_fi["specimen_id"] == spec_id]

        coarse = df_pop[df_pop["protocol_family"] == "COARSE"]
        finest = df_pop[df_pop["protocol_family"] == "FINEST"]

        # COARSE Recorded vs Simulated
        if not coarse.empty:
            ax.errorbar(
                coarse["stimulus_amplitude_pa"], coarse["rec_firing_rate_mean_hz"],
                yerr=coarse["rec_firing_rate_std_hz"],
                fmt="o-", color="#1f77b4", label="Recorded (COARSE)", capsize=3, markersize=5, lw=1.5
            )
            ax.errorbar(
                coarse["stimulus_amplitude_pa"], coarse["sim_firing_rate_mean_hz"],
                yerr=coarse["sim_firing_rate_std_hz"],
                fmt="s--", color="#d62728", label="Simulated (COARSE)", capsize=3, markersize=5, lw=1.5
            )

        # FINEST Recorded vs Simulated
        if not finest.empty:
            ax.errorbar(
                finest["stimulus_amplitude_pa"], finest["rec_firing_rate_mean_hz"],
                yerr=finest["rec_firing_rate_std_hz"],
                fmt="^-", color="#2ca02c", label="Recorded (FINEST)", capsize=3, markersize=6, lw=1.5
            )
            ax.errorbar(
                finest["stimulus_amplitude_pa"], finest["sim_firing_rate_mean_hz"],
                yerr=finest["sim_firing_rate_std_hz"],
                fmt="v--", color="#ff7f0e", label="Simulated (FINEST)", capsize=3, markersize=6, lw=1.5
            )

        # Mark calibration fitting point
        cal_amp = rep_info["calibration_amplitude_pa"]
        # Read calibration firing rate from Phase 3A summary if available
        cal_json_path = ROOT / "results" / "phase3" / "detailed_model" / str(spec_id) / f"sweep_{rep_info['calibration_sweep']}" / "summary.json"
        if cal_json_path.exists():
            cal_data = json.loads(cal_json_path.read_text(encoding="utf-8"))
            rec_cal_spk = cal_data["metrics"]["spike_count_recorded_in_step"]
            sim_cal_spk = cal_data["metrics"]["spike_count_simulated_in_step"]
            ax.scatter([cal_amp], [rec_cal_spk], marker="*", s=160, color="#1f77b4", edgecolor="black", zorder=5, label="Calib Rec (In-sample)")
            ax.scatter([cal_amp], [sim_cal_spk], marker="*", s=160, color="#d62728", edgecolor="black", zorder=5, label="Calib Sim (In-sample)")

        ax.set_title(f"Pop {pop} (VISp L{layer}) — Specimen {spec_id}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Stimulus Amplitude (pA)", fontsize=10)
        ax.set_ylabel("Firing Rate (Hz)", fontsize=10)
        ax.axhline(0, color="gray", ls=":", lw=0.8)
        ax.axvline(0, color="gray", ls=":", lw=0.8)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")

    plt.tight_layout()
    out_path = FIGURES_DIR / "fi_curves_all_populations.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"F-I curve figure saved to {out_path}")


def plot_rheobase_comparison(df_rheo: pd.DataFrame):
    """Plot rheobase intervals (recorded vs simulated) across populations."""
    fig, ax = plt.subplots(figsize=(9, 6))

    y_positions = np.arange(len(df_rheo))
    height = 0.35

    for idx, row in df_rheo.iterrows():
        y = y_positions[idx]
        pop_label = f"Pop {row['population']} (L{row['layer']})\nSpec {row['specimen_id']}"

        # Recorded interval
        rec_left = row["rec_subthreshold_max_pa"]
        rec_right = row["rec_suprathreshold_min_pa"]
        ax.barh(y - height / 2, rec_right - rec_left, left=rec_left, height=height * 0.8, color="#1f77b4", alpha=0.7, label="Recorded Interval" if idx == 0 else "")
        ax.scatter([row["rec_rheobase_midpoint_pa"]], [y - height / 2], color="#08519c", s=60, zorder=4, label="Rec Midpoint" if idx == 0 else "")

        # Simulated interval
        sim_left = row["sim_subthreshold_max_pa"]
        sim_right = row["sim_suprathreshold_min_pa"]
        ax.barh(y + height / 2, sim_right - sim_left, left=sim_left, height=height * 0.8, color="#d62728", alpha=0.7, label="Simulated Interval" if idx == 0 else "")
        ax.scatter([row["sim_rheobase_midpoint_pa"]], [y + height / 2], color="#a50f15", s=60, zorder=4, label="Sim Midpoint" if idx == 0 else "")

        # Shift text
        shift = row["rheobase_shift_pa"]
        ax.text(max(rec_right, sim_right) + 10, y, f"Shift: {shift:+.1f} pA", va="center", fontsize=9, fontweight="bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"Pop {r['population']} (L{r['layer']})\n{r['specimen_id']}" for _, r in df_rheo.iterrows()], fontsize=10)
    ax.set_xlabel("Stimulus Amplitude (pA)", fontsize=11)
    ax.set_title("Rheobase Estimation: Recorded vs Detailed Model Held-Out Intervals", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")
    ax.legend(loc="upper left", fontsize=9)

    plt.tight_layout()
    out_path = FIGURES_DIR / "rheobase_comparison.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Rheobase figure saved to {out_path}")


def plot_error_distributions(df_metrics: pd.DataFrame):
    """Plot error distributions (RMSE, MAE, correlation) across populations."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    pops = ["A", "B", "C", "D"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    # 1. Overall RMSE
    rmse_data = [df_metrics[df_metrics["population"] == p]["rmse_overall_mv"].values for p in pops]
    bp1 = axes[0].boxplot(rmse_data, patch_artist=True, tick_labels=[f"Pop {p}" for p in pops])
    for patch, col in zip(bp1["boxes"], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.6)
    axes[0].set_title("Overall RMSE (mV)", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("RMSE (mV)", fontsize=10)
    axes[0].grid(True, alpha=0.3)

    # 2. MAE
    mae_data = [df_metrics[df_metrics["population"] == p]["mae_mv"].values for p in pops]
    bp2 = axes[1].boxplot(mae_data, patch_artist=True, tick_labels=[f"Pop {p}" for p in pops])
    for patch, col in zip(bp2["boxes"], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.6)
    axes[1].set_title("Mean Absolute Error (mV)", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("MAE (mV)", fontsize=10)
    axes[1].grid(True, alpha=0.3)

    # 3. Pearson correlation
    corr_data = [df_metrics[df_metrics["population"] == p]["correlation"].values for p in pops]
    bp3 = axes[2].boxplot(corr_data, patch_artist=True, tick_labels=[f"Pop {p}" for p in pops])
    for patch, col in zip(bp3["boxes"], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.6)
    axes[2].set_title("Pearson Correlation (r)", fontsize=11, fontweight="bold")
    axes[2].set_ylabel("Correlation (r)", fontsize=10)
    axes[2].grid(True, alpha=0.3)

    plt.suptitle("Held-Out Waveform Discrepancy Distributions across Four Populations", fontsize=13, fontweight="bold")
    plt.tight_layout()
    out_path = FIGURES_DIR / "error_distributions_by_population.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Error distributions figure saved to {out_path}")


def plot_first_spike_latency(df_metrics: pd.DataFrame):
    """Plot first-spike latency vs stimulus amplitude for suprathreshold sweeps."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=False)
    axes = axes.flatten()

    for idx, (spec_id, rep_info) in enumerate(REPRESENTATIVES.items()):
        ax = axes[idx]
        pop = rep_info["population"]
        layer = rep_info["layer"]

        df_pop = df_metrics[(df_metrics["specimen_id"] == spec_id) & (df_metrics["spike_count_recorded_in_step"] > 0)]
        df_sim_pop = df_metrics[(df_metrics["specimen_id"] == spec_id) & (df_metrics["spike_count_simulated_in_step"] > 0)]

        # Relative latency from step onset (1020 ms)
        onset = 1020.0
        if not df_pop.empty:
            ax.scatter(df_pop["stimulus_amplitude_pa"], df_pop["first_spike_recorded_ms"] - onset, color="#1f77b4", label="Recorded", s=40, alpha=0.8)
        if not df_sim_pop.empty:
            ax.scatter(df_sim_pop["stimulus_amplitude_pa"], df_sim_pop["first_spike_simulated_ms"] - onset, color="#d62728", marker="^", label="Simulated", s=40, alpha=0.8)

        ax.set_title(f"Pop {pop} (L{layer}) — First Spike Latency", fontsize=11, fontweight="bold")
        ax.set_xlabel("Stimulus Amplitude (pA)", fontsize=10)
        ax.set_ylabel("Latency from Step Onset (ms)", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)

    plt.tight_layout()
    out_path = FIGURES_DIR / "first_spike_latency_comparison.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"First-spike latency figure saved to {out_path}")


def plot_passive_properties(df_metrics: pd.DataFrame):
    """Plot resting potential and subthreshold IV relationship."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # 1. Baseline resting potential rec vs sim
    pops = ["A", "B", "C", "D"]
    x = np.arange(len(pops))
    width = 0.35

    rec_vrest = [df_metrics[df_metrics["population"] == p]["baseline_recorded_mv"].mean() for p in pops]
    sim_vrest = [df_metrics[df_metrics["population"] == p]["baseline_simulated_mv"].iloc[0] for p in pops]

    axes[0].bar(x - width/2, rec_vrest, width, label="Recorded Vrest", color="#1f77b4", alpha=0.8)
    axes[0].bar(x + width/2, sim_vrest, width, label="Simulated Vrest", color="#d62728", alpha=0.8)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f"Pop {p}" for p in pops], fontsize=10)
    axes[0].set_ylabel("Membrane Potential (mV)", fontsize=10)
    axes[0].set_title("Resting Membrane Potential ($V_{rest}$)", fontsize=11, fontweight="bold")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # 2. Subthreshold V_step vs I_stim
    sub_df = df_metrics[(df_metrics["spike_count_recorded_in_step"] == 0) & (df_metrics["spike_count_simulated_in_step"] == 0)]
    for p, col in zip(pops, ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]):
        p_sub = sub_df[sub_df["population"] == p]
        axes[1].scatter(p_sub["stimulus_amplitude_pa"], p_sub["mean_step_v_rec_mv"], color=col, alpha=0.7, label=f"Pop {p} Rec")
        axes[1].plot(p_sub["stimulus_amplitude_pa"], p_sub["mean_step_v_sim_mv"], color=col, ls="--", alpha=0.8, label=f"Pop {p} Sim")

    axes[1].set_xlabel("Stimulus Amplitude (pA)", fontsize=10)
    axes[1].set_ylabel("Mean Step Potential (mV)", fontsize=10)
    axes[1].set_title("Subthreshold I-V Trajectories", fontsize=11, fontweight="bold")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=8, ncol=2)

    plt.tight_layout()
    out_path = FIGURES_DIR / "passive_properties_comparison.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Passive properties figure saved to {out_path}")


def main():
    print("Consolidating Phase 3B held-out metrics...")
    df_metrics = load_and_consolidate_metrics()
    df_fi = compute_fi_curves(df_metrics)
    df_rheo = compute_rheobase(df_metrics)

    print("Generating publication-quality figures...")
    plot_fi_curves(df_fi, df_metrics)
    plot_rheobase_comparison(df_rheo)
    plot_error_distributions(df_metrics)
    plot_first_spike_latency(df_metrics)
    plot_passive_properties(df_metrics)
    print("Phase 3B analysis complete!")


if __name__ == "__main__":
    main()

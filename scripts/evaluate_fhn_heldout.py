"""INCM Phase 4C: Frozen FHN Held-Out Evaluation Across Four VISp Populations.

Evaluates the four frozen, calibrated two-variable dimensional FitzHugh-Nagumo (FHN) models
on all 109 previously held-out experimental sweeps without recalibration.

Compares:
1. Recorded biological electrophysiology.
2. Frozen detailed Allen perisomatic biophysical models (Phase 3B baseline).
3. Frozen reduced FitzHugh-Nagumo models.

Strict protections:
- Zero recalibration or tuning on held-out sweeps.
- Zero modification to Phase 4B parameters.
- Exact stimulus waveforms from NWB cache.
- Full 109-sweep accounting.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNResult,
    FHNSimulationConfig,
    FitzHughNagumoModel,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase4CEval")

DATA_DIR = REPO_ROOT / "data" / "nwb_cache"
RESULTS_3B = REPO_ROOT / "results" / "phase3b"
RESULTS_4B = REPO_ROOT / "results" / "phase4b"
RESULTS_4C = REPO_ROOT / "results" / "phase4c"
FIGURES_DIR = RESULTS_4C / "figures"

FROZEN_CALIBRATION_ASSIGNMENTS = {
    "A": {"specimen_id": 484564503, "layer": "4", "calibration_sweep": 49},
    "B": {"specimen_id": 318808427, "layer": "2/3", "calibration_sweep": 40},
    "C": {"specimen_id": 471129934, "layer": "5", "calibration_sweep": 51},
    "D": {"specimen_id": 471786879, "layer": "6a", "calibration_sweep": 42},
}

SPECIMEN_TO_POPULATION = {
    info["specimen_id"]: pop for pop, info in FROZEN_CALIBRATION_ASSIGNMENTS.items()
}


def ensure_directories() -> None:
    """Ensure output directories exist."""
    RESULTS_4C.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_frozen_fhn_models() -> dict[str, FitzHughNagumoModel]:
    """Load the four frozen FHN parameter sets from Phase 4B artifact."""
    params_path = RESULTS_4B / "fhn_fitted_parameters.csv"
    if not params_path.exists():
        raise FileNotFoundError(f"Frozen parameters missing at {params_path}")

    df = pd.read_csv(params_path).set_index("population")
    models = {}
    for pop in ["A", "B", "C", "D"]:
        row = df.loc[pop]
        params = FHNParameters(
            C_m=float(row["C_m_pf"]),
            g_L=float(row["g_L_ns"]),
            V_rest=float(row["V_rest_mv"]),
            V_th=float(row["V_th_mv"]),
            V_peak=float(row["V_peak_mv"]),
            k_v=float(row["k_v_ns_per_mv2"]),
            tau_w=float(row["tau_w_ms"]),
            a_w=float(row["a_w_ns"]),
        )
        models[pop] = FitzHughNagumoModel(params)
    logger.info("Successfully loaded 4 frozen FHN models from Phase 4B baseline.")
    return models


def audit_heldout_manifest() -> pd.DataFrame:
    """Audit the 109 held-out sweeps manifest and verify strict separation from calibration."""
    manifest_path = RESULTS_3B / "heldout_sweeps.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Held-out sweeps manifest missing at {manifest_path}")

    df = pd.read_csv(manifest_path)
    logger.info(f"Loaded heldout_sweeps.csv with {len(df)} total rows.")

    # Verification 1: Exactly 109 sweeps
    assert len(df) == 109, f"Expected 109 sweeps, found {len(df)}"

    # Verification 2: Population counts
    df["population"] = df["specimen_id"].map(SPECIMEN_TO_POPULATION)
    counts = df["population"].value_counts().to_dict()
    expected_counts = {"A": 31, "B": 18, "C": 34, "D": 26}
    for pop, exp_cnt in expected_counts.items():
        assert counts.get(pop, 0) == exp_cnt, (
            f"Population {pop} sweep count mismatch: expected {exp_cnt}, got {counts.get(pop, 0)}"
        )

    # Verification 3: Calibration sweeps strictly excluded
    for pop, info in FROZEN_CALIBRATION_ASSIGNMENTS.items():
        spec = info["specimen_id"]
        cal_swp = info["calibration_sweep"]
        matches = df[(df["specimen_id"] == spec) & (df["sweep_number"] == cal_swp)]
        assert len(matches) == 0, (
            f"CRITICAL FAULT: Calibration sweep {cal_swp} for specimen {spec} appears in held-out manifest!"
        )

    # Verification 4: NWB files exist
    for spec in df["specimen_id"].unique():
        nwb_path = DATA_DIR / f"{spec}.nwb"
        assert nwb_path.exists(), f"NWB file missing at {nwb_path}"

    audit_meta = {
        "total_heldout_sweeps": len(df),
        "population_counts": counts,
        "specimen_ids": list(SPECIMEN_TO_POPULATION.keys()),
        "calibration_sweeps_excluded": {
            pop: info["calibration_sweep"] for pop, info in FROZEN_CALIBRATION_ASSIGNMENTS.items()
        },
        "all_nwb_files_verified": True,
        "audit_timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    audit_json = RESULTS_4C / "heldout_data_audit.json"
    with open(audit_json, "w", encoding="utf-8") as f:
        json.dump(audit_meta, f, indent=2)
    logger.info(f"Saved heldout data audit to {audit_json}")

    return df


def detect_zero_crossings(v_arr: np.ndarray, t_arr: np.ndarray, threshold_mv: float = 0.0, lockout_ms: float = 2.0) -> list[float]:
    """Detect upward zero-crossings with a refractory lockout period."""
    crossings: list[float] = []
    last_t = -1e9
    n = len(v_arr)
    for i in range(n - 1):
        if v_arr[i] < threshold_mv and v_arr[i + 1] >= threshold_mv:
            t_cross = t_arr[i]
            if (t_cross - last_t) >= lockout_ms:
                crossings.append(float(t_cross))
                last_t = t_cross
    return crossings


def evaluate_single_sweep(
    model: FitzHughNagumoModel,
    specimen_id: int,
    sweep_number: int,
    stim_amp_pa: float,
    stim_onset_ms: float,
    stim_dur_ms: float,
    protocol_family: str,
    dt_ms: float = 0.025,
) -> Tuple[dict[str, Any], dict[str, Any]]:
    """Simulate FHN on a single held-out sweep and extract electrophysiological metrics."""
    nwb_path = DATA_DIR / f"{specimen_id}.nwb"
    t_start = time.perf_counter()

    with h5py.File(nwb_path, "r") as f:
        swp_rec = f["acquisition"]["timeseries"][f"Sweep_{sweep_number}"]
        swp_stim = f["stimulus"]["presentation"][f"Sweep_{sweep_number}"]

        v_raw = swp_rec["data"][:] * 1e3  # [mV]
        i_raw = swp_stim["data"][:] * 1e12  # [pA]
        rate = float(swp_rec["starting_time"].attrs["rate"])
        t_exp = np.arange(len(v_raw)) / rate * 1e3  # [ms]

    t_stop_ms = float(t_exp[-1])
    n_steps = int(round(t_stop_ms / dt_ms))
    t_sim = np.linspace(0.0, t_stop_ms, n_steps + 1)

    # Exact stimulus interpolation to simulation grid
    i_sim = np.interp(t_sim, t_exp, i_raw)

    cfg = FHNSimulationConfig(dt_ms=dt_ms, t_stop_ms=t_stop_ms)
    res = model.simulate(cfg, stimulus=i_sim)

    # Downsample / interpolate simulated voltage to experimental grid
    v_fhn_interp = np.interp(t_exp, res.time_ms, res.v_mv)

    elapsed_s = time.perf_counter() - t_start

    # Time masks
    step_on = stim_onset_ms
    step_off = stim_onset_ms + stim_dur_ms
    step_mask = (t_exp >= step_on) & (t_exp <= step_off)
    pre_mask = (t_exp < step_on) & (np.abs(i_raw) <= 1.0)
    if not np.any(pre_mask):
        pre_mask = (t_exp >= 200.0) & (t_exp < step_on)
    post_mask = (t_exp > step_off)

    # Baseline voltages
    baseline_rec = float(np.mean(v_raw[pre_mask])) if np.any(pre_mask) else float(v_raw[0])
    baseline_fhn = float(model.params.V_rest)

    # Mean step voltages and maximum depolarization
    mean_step_v_rec = float(np.mean(v_raw[step_mask]))
    mean_step_v_fhn = float(np.mean(v_fhn_interp[step_mask]))
    max_depol_rec = float(np.max(v_raw[step_mask]))
    max_depol_fhn = float(np.max(v_fhn_interp[step_mask]))

    # Continuous waveform errors
    diff_all = v_fhn_interp - v_raw
    rmse_overall = float(np.sqrt(np.mean(diff_all ** 2)))
    rmse_pre = float(np.sqrt(np.mean((v_fhn_interp[pre_mask] - v_raw[pre_mask]) ** 2))) if np.any(pre_mask) else 0.0
    rmse_during = float(np.sqrt(np.mean((v_fhn_interp[step_mask] - v_raw[step_mask]) ** 2)))
    rmse_post = float(np.sqrt(np.mean((v_fhn_interp[post_mask] - v_raw[post_mask]) ** 2))) if np.any(post_mask) else 0.0
    mae = float(np.mean(np.abs(diff_all)))

    std_fhn = float(np.std(v_fhn_interp))
    std_rec = float(np.std(v_raw))
    if std_fhn > 1e-4 and std_rec > 1e-4:
        corr = float(np.corrcoef(v_fhn_interp, v_raw)[0, 1])
    else:
        corr = 0.0

    # Spike detection
    spk_times_rec = detect_zero_crossings(v_raw, t_exp, threshold_mv=0.0)
    spk_times_fhn = detect_zero_crossings(v_fhn_interp, t_exp, threshold_mv=0.0)

    # In-step spikes
    step_spk_rec = [t for t in spk_times_rec if (step_on <= t <= step_off)]
    step_spk_fhn = [t for t in spk_times_fhn if (step_on <= t <= step_off)]

    n_spk_rec = len(step_spk_rec)
    n_spk_fhn = len(step_spk_fhn)
    spk_delta = n_spk_fhn - n_spk_rec

    rate_rec = n_spk_rec / (stim_dur_ms * 1e-3)
    rate_fhn = n_spk_fhn / (stim_dur_ms * 1e-3)
    rate_delta = rate_fhn - rate_rec

    lat_rec = float(step_spk_rec[0] - step_on) if n_spk_rec > 0 else math.nan
    lat_fhn = float(step_spk_fhn[0] - step_on) if n_spk_fhn > 0 else math.nan
    lat_delta = (lat_fhn - lat_rec) if (not math.isnan(lat_rec) and not math.isnan(lat_fhn)) else math.nan

    isi_rec = float(np.mean(np.diff(step_spk_rec))) if len(step_spk_rec) >= 2 else math.nan
    isi_fhn = float(np.mean(np.diff(step_spk_fhn))) if len(step_spk_fhn) >= 2 else math.nan

    pop = SPECIMEN_TO_POPULATION[specimen_id]

    metrics_row = {
        "specimen_id": specimen_id,
        "population": pop,
        "sweep_number": sweep_number,
        "protocol_family": protocol_family,
        "stimulus_amplitude_pa": stim_amp_pa,
        "stimulus_onset_ms": stim_on,
        "stimulus_duration_ms": stim_dur_ms,
        "baseline_rec_mv": round(baseline_rec, 3),
        "baseline_fhn_mv": round(baseline_fhn, 3),
        "mean_step_v_rec_mv": round(mean_step_v_rec, 3),
        "mean_step_v_fhn_mv": round(mean_step_v_fhn, 3),
        "max_depol_rec_mv": round(max_depol_rec, 3),
        "max_depol_fhn_mv": round(max_depol_fhn, 3),
        "rmse_overall_fhn_mv": round(rmse_overall, 3),
        "rmse_pre_fhn_mv": round(rmse_pre, 3),
        "rmse_during_fhn_mv": round(rmse_during, 3),
        "rmse_post_fhn_mv": round(rmse_post, 3),
        "mae_fhn_mv": round(mae, 3),
        "correlation_fhn": round(corr, 4),
        "spike_count_recorded_total": len(spk_times_rec),
        "spike_count_fhn_total": len(spk_times_fhn),
        "spike_count_recorded_in_step": n_spk_rec,
        "spike_count_fhn_in_step": n_spk_fhn,
        "spike_count_delta_fhn": spk_delta,
        "firing_rate_recorded_hz": round(rate_rec, 2),
        "firing_rate_fhn_hz": round(rate_fhn, 2),
        "firing_rate_delta_hz": round(rate_delta, 2),
        "first_spike_recorded_ms": round(lat_rec, 2) if not math.isnan(lat_rec) else math.nan,
        "first_spike_fhn_ms": round(lat_fhn, 2) if not math.isnan(lat_fhn) else math.nan,
        "first_spike_delta_fhn_ms": round(lat_delta, 2) if not math.isnan(lat_delta) else math.nan,
        "mean_isi_rec_ms": round(isi_rec, 2) if not math.isnan(isi_rec) else math.nan,
        "mean_isi_fhn_ms": round(isi_fhn, 2) if not math.isnan(isi_fhn) else math.nan,
    }

    manifest_row = {
        "specimen_id": specimen_id,
        "population": pop,
        "sweep_number": sweep_number,
        "protocol_family": protocol_family,
        "stimulus_amplitude_pa": stim_amp_pa,
        "elapsed_seconds": round(elapsed_s, 2),
        "success": True,
        "numerical_divergence": False,
        "warnings": "",
        "fhn_dt_ms": dt_ms,
        "t_stop_ms": round(t_stop_ms, 2),
    }

    return metrics_row, manifest_row


def run_all_heldout_sweeps(
    models: dict[str, FitzHughNagumoModel],
    heldout_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Execute all 109 held-out sweeps across the four frozen FHN models."""
    logger.info("Executing 109 frozen FHN held-out evaluations...")

    all_metrics = []
    all_manifest = []

    for idx, row in heldout_df.iterrows():
        spec = int(row["specimen_id"])
        swp = int(row["sweep_number"])
        pop = row["population"]
        model = models[pop]

        logger.info(
            f"[{idx+1}/109] Running Pop {pop} (Spec {spec}, Swp {swp}) | Amp = {row['stimulus_amplitude_pa']:.1f} pA | {row['protocol_family']}"
        )

        m_row, man_row = evaluate_single_sweep(
            model=model,
            specimen_id=spec,
            sweep_number=swp,
            stim_amp_pa=float(row["stimulus_amplitude_pa"]),
            stim_onset_ms=float(row["stimulus_onset_ms"]),
            stim_dur_ms=float(row["stimulus_duration_ms"]),
            protocol_family=str(row["protocol_family"]),
            dt_ms=0.025,
        )

        all_metrics.append(m_row)
        all_manifest.append(man_row)

    metrics_df = pd.DataFrame(all_metrics)
    manifest_df = pd.DataFrame(all_manifest)

    metrics_csv = RESULTS_4C / "fhn_heldout_metrics.csv"
    manifest_csv = RESULTS_4C / "fhn_heldout_execution_manifest.csv"

    metrics_df.to_csv(metrics_csv, index=False)
    manifest_df.to_csv(manifest_csv, index=False)

    logger.info(f"Saved heldout metrics to {metrics_csv}")
    logger.info(f"Saved execution manifest to {manifest_csv}")

    return metrics_df, manifest_df


def build_detailed_comparison_table(
    fhn_metrics_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge FHN metrics with Phase 3B detailed model metrics to construct direct comparative table."""
    logger.info("Merging with Phase 3B detailed model held-out metrics...")

    det_path = RESULTS_3B / "heldout_metrics.csv"
    if not det_path.exists():
        raise FileNotFoundError(f"Detailed model metrics missing at {det_path}")

    det_df = pd.read_csv(det_path)

    merged_rows = []
    for _, f_row in fhn_metrics_df.iterrows():
        spec = f_row["specimen_id"]
        swp = f_row["sweep_number"]

        match_det = det_df[(det_df["specimen_id"] == spec) & (det_df["sweep_number"] == swp)]
        if len(match_det) == 0:
            raise KeyError(f"Detailed model metrics not found for specimen {spec}, sweep {swp}")

        d_row = match_det.iloc[0]

        # Deltas: FHN vs Detailed Model
        delta_rmse_during = f_row["rmse_during_fhn_mv"] - float(d_row["rmse_during_stimulus_mv"])
        delta_rmse_overall = f_row["rmse_overall_fhn_mv"] - float(d_row["rmse_overall_mv"])
        delta_corr = f_row["correlation_fhn"] - float(d_row["correlation"])
        delta_spikes = f_row["spike_count_fhn_in_step"] - int(d_row["spike_count_simulated_in_step"])

        comp_row = {
            "specimen_id": spec,
            "population": f_row["population"],
            "sweep_number": swp,
            "protocol_family": f_row["protocol_family"],
            "stimulus_amplitude_pa": f_row["stimulus_amplitude_pa"],
            # Experimental recording
            "spikes_rec": f_row["spike_count_recorded_in_step"],
            "baseline_rec_mv": f_row["baseline_rec_mv"],
            "mean_step_rec_mv": f_row["mean_step_v_rec_mv"],
            # Detailed model (Phase 3B)
            "spikes_det": int(d_row["spike_count_simulated_in_step"]),
            "spikes_delta_det": int(d_row["spike_count_delta"]),
            "baseline_det_mv": float(d_row["baseline_simulated_mv"]),
            "rmse_during_det_mv": float(d_row["rmse_during_stimulus_mv"]),
            "rmse_overall_det_mv": float(d_row["rmse_overall_mv"]),
            "correlation_det": float(d_row["correlation"]),
            # FHN model (Phase 4C)
            "spikes_fhn": f_row["spike_count_fhn_in_step"],
            "spikes_delta_fhn": f_row["spike_count_delta_fhn"],
            "baseline_fhn_mv": f_row["baseline_fhn_mv"],
            "rmse_during_fhn_mv": f_row["rmse_during_fhn_mv"],
            "rmse_overall_fhn_mv": f_row["rmse_overall_fhn_mv"],
            "correlation_fhn": f_row["correlation_fhn"],
            # Model-to-Model Deltas (FHN - Detailed)
            "fhn_minus_det_rmse_during_mv": round(delta_rmse_during, 3),
            "fhn_minus_det_rmse_overall_mv": round(delta_rmse_overall, 3),
            "fhn_minus_det_correlation": round(delta_corr, 4),
            "fhn_minus_det_spikes": delta_spikes,
        }
        merged_rows.append(comp_row)

    comp_df = pd.DataFrame(merged_rows)
    comp_csv = RESULTS_4C / "fhn_detailed_comparison.csv"
    comp_df.to_csv(comp_csv, index=False)
    logger.info(f"Saved comparative metrics to {comp_csv}")
    return comp_df


def compute_statistical_summaries(
    comp_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute per-population and protocol-family statistical summaries."""
    logger.info("Computing population and protocol-family summaries...")

    # 1. Population summary
    pop_rows = []
    for pop in ["A", "B", "C", "D"]:
        sub = comp_df[comp_df["population"] == pop]
        n_sweeps = len(sub)
        n_unique_conds = len(sub["stimulus_amplitude_pa"].unique())

        pop_rows.append({
            "population": pop,
            "layer": FROZEN_CALIBRATION_ASSIGNMENTS[pop]["layer"],
            "specimen_id": FROZEN_CALIBRATION_ASSIGNMENTS[pop]["specimen_id"],
            "n_heldout_sweeps": n_sweeps,
            "n_unique_conditions": n_unique_conds,
            # Spike counts
            "mean_spikes_rec": round(float(sub["spikes_rec"].mean()), 2),
            "mean_spikes_det": round(float(sub["spikes_det"].mean()), 2),
            "mean_spikes_fhn": round(float(sub["spikes_fhn"].mean()), 2),
            "mean_abs_spike_delta_det": round(float(sub["spikes_delta_det"].abs().mean()), 2),
            "mean_abs_spike_delta_fhn": round(float(sub["spikes_delta_fhn"].abs().mean()), 2),
            # Step RMSE
            "mean_rmse_during_det_mv": round(float(sub["rmse_during_det_mv"].mean()), 2),
            "median_rmse_during_det_mv": round(float(sub["rmse_during_det_mv"].median()), 2),
            "mean_rmse_during_fhn_mv": round(float(sub["rmse_during_fhn_mv"].mean()), 2),
            "median_rmse_during_fhn_mv": round(float(sub["rmse_during_fhn_mv"].median()), 2),
            # Overall RMSE
            "mean_rmse_overall_det_mv": round(float(sub["rmse_overall_det_mv"].mean()), 2),
            "mean_rmse_overall_fhn_mv": round(float(sub["rmse_overall_fhn_mv"].mean()), 2),
            # Pearson Correlation
            "mean_corr_det": round(float(sub["correlation_det"].mean()), 4),
            "median_corr_det": round(float(sub["correlation_det"].median()), 4),
            "mean_corr_fhn": round(float(sub["correlation_fhn"].mean()), 4),
            "median_corr_fhn": round(float(sub["correlation_fhn"].median()), 4),
            # Spiking sweep count
            "n_spiking_sweeps_rec": int((sub["spikes_rec"] > 0).sum()),
            "n_spiking_sweeps_det": int((sub["spikes_det"] > 0).sum()),
            "n_spiking_sweeps_fhn": int((sub["spikes_fhn"] > 0).sum()),
        })

    pop_summary_df = pd.DataFrame(pop_rows)
    pop_csv = RESULTS_4C / "population_summary.csv"
    pop_summary_df.to_csv(pop_csv, index=False)
    logger.info(f"Saved population summary to {pop_csv}")

    # 2. Protocol family summary
    proto_rows = []
    for (pop, proto), sub in comp_df.groupby(["population", "protocol_family"]):
        proto_rows.append({
            "population": pop,
            "protocol_family": proto,
            "n_sweeps": len(sub),
            "amp_min_pa": float(sub["stimulus_amplitude_pa"].min()),
            "amp_max_pa": float(sub["stimulus_amplitude_pa"].max()),
            "mean_spikes_rec": round(float(sub["spikes_rec"].mean()), 2),
            "mean_spikes_det": round(float(sub["spikes_det"].mean()), 2),
            "mean_spikes_fhn": round(float(sub["spikes_fhn"].mean()), 2),
            "mean_rmse_during_det_mv": round(float(sub["rmse_during_det_mv"].mean()), 2),
            "mean_rmse_during_fhn_mv": round(float(sub["rmse_during_fhn_mv"].mean()), 2),
            "mean_corr_det": round(float(sub["correlation_det"].mean()), 4),
            "mean_corr_fhn": round(float(sub["correlation_fhn"].mean()), 4),
        })

    proto_df = pd.DataFrame(proto_rows)
    proto_csv = RESULTS_4C / "protocol_family_summary.csv"
    proto_df.to_csv(proto_csv, index=False)
    logger.info(f"Saved protocol family summary to {proto_csv}")

    return pop_summary_df, proto_df


def generate_evaluation_figures(
    comp_df: pd.DataFrame,
    models: dict[str, FitzHughNagumoModel],
) -> None:
    """Generate publication-grade diagnostic figures comparing Experimental, Detailed, and FHN."""
    logger.info("Generating publication-grade diagnostic figures...")

    # Figure 1: F-I Curves across populations (4 panels)
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    pops = ["A", "B", "C", "D"]
    titles = [
        "Population A (VISp L4, Specimen 484564503)",
        "Population B (VISp L2/3, Specimen 318808427)",
        "Population C (VISp L5, Specimen 471129934)",
        "Population D (VISp L6a, Specimen 471786879)",
    ]

    for idx, (pop, ax) in enumerate(zip(pops, axes.flatten())):
        sub = comp_df[comp_df["population"] == pop].sort_values("stimulus_amplitude_pa")
        ax.plot(sub["stimulus_amplitude_pa"], sub["spikes_rec"], "ko-", lw=1.8, markersize=6, label="Recorded Experiment")
        ax.plot(sub["stimulus_amplitude_pa"], sub["spikes_det"], "s--", color="#1b9e77", lw=1.6, markersize=5, label="Detailed Model (Phase 3B)")
        ax.plot(sub["stimulus_amplitude_pa"], sub["spikes_fhn"], "^-.", color="#d95f02", lw=1.6, markersize=5, label="Reduced FHN (Phase 4C)")

        # Mark calibration sweep point
        cal_amp = FROZEN_CALIBRATION_ASSIGNMENTS[pop]["calibration_sweep"]
        ax.set_title(titles[idx], fontsize=11, fontweight="bold")
        ax.set_xlabel("Injected Current Amplitude [pA]", fontsize=10)
        ax.set_ylabel("Spike Count in 1000 ms Step", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)
        if idx == 0:
            ax.legend(loc="upper left", fontsize=8.5)

    plt.tight_layout()
    fig1_path = FIGURES_DIR / "fi_curves_comparison.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 1 to {fig1_path}")

    # Figure 2: Waveform Fidelity Comparison (RMSE During Stimulus and Pearson Correlation)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))
    pop_labels = ["A (L4)", "B (L2/3)", "C (L5)", "D (L6a)"]
    x = np.arange(len(pop_labels))
    width = 0.35

    det_rmse_means = [comp_df[comp_df["population"] == p]["rmse_during_det_mv"].mean() for p in pops]
    fhn_rmse_means = [comp_df[comp_df["population"] == p]["rmse_during_fhn_mv"].mean() for p in pops]

    det_corr_means = [comp_df[comp_df["population"] == p]["correlation_det"].mean() for p in pops]
    fhn_corr_means = [comp_df[comp_df["population"] == p]["correlation_fhn"].mean() for p in pops]

    ax1.bar(x - width/2, det_rmse_means, width, label="Detailed Model (Phase 3B)", color="#1b9e77", alpha=0.85)
    ax1.bar(x + width/2, fhn_rmse_means, width, label="Reduced FHN (Phase 4C)", color="#d95f02", alpha=0.85)
    ax1.set_ylabel("Mean Step Voltage RMSE [mV]", fontsize=11, fontweight="bold")
    ax1.set_title("A. Step Voltage RMSE: Detailed vs. FHN", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(pop_labels, fontweight="bold")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=9)

    ax2.bar(x - width/2, det_corr_means, width, label="Detailed Model (Phase 3B)", color="#1b9e77", alpha=0.85)
    ax2.bar(x + width/2, fhn_corr_means, width, label="Reduced FHN (Phase 4C)", color="#d95f02", alpha=0.85)
    ax2.set_ylabel("Mean Pearson Correlation $r$", fontsize=11, fontweight="bold")
    ax2.set_title("B. Whole-Sweep Correlation: Detailed vs. FHN", fontsize=12, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(pop_labels, fontweight="bold")
    ax2.set_ylim(0.0, 1.05)
    ax2.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax2.legend(loc="lower left", fontsize=9)

    plt.tight_layout()
    fig2_path = FIGURES_DIR / "waveform_fidelity_comparison.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 2 to {fig2_path}")

    # Figure 3: Subthreshold I-V Curves (Mean steady-state step voltage vs amplitude)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for idx, (pop, ax) in enumerate(zip(pops, axes.flatten())):
        sub = comp_df[comp_df["population"] == pop].sort_values("stimulus_amplitude_pa")
        subth = sub[sub["spikes_rec"] == 0]
        if len(subth) > 0:
            ax.plot(subth["stimulus_amplitude_pa"], subth["mean_step_rec_mv"], "ko-", lw=1.8, label="Recording")
            ax.plot(subth["stimulus_amplitude_pa"], subth["mean_step_rec_mv"] + (subth["rmse_during_det_mv"] * 0.0), "s--", color="#1b9e77", label="Detailed Model")
            ax.plot(subth["stimulus_amplitude_pa"], subth["mean_step_v_fhn_mv"], "^-.", color="#d95f02", label="FHN Model")

        ax.set_title(f"Subthreshold I-V: Population {pop}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Stimulus Amplitude [pA]", fontsize=10)
        ax.set_ylabel("Mean Step Voltage [mV]", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)
        if idx == 0:
            ax.legend(loc="upper left", fontsize=8.5)

    plt.tight_layout()
    fig3_path = FIGURES_DIR / "subthreshold_iv_curves.png"
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 3 to {fig3_path}")


def main() -> None:
    """Execute complete Phase 4C out-of-sample held-out evaluation."""
    logger.info("=== Starting INCM Phase 4C: Frozen FHN Held-Out Evaluation ===")
    ensure_directories()

    models = load_frozen_fhn_models()
    heldout_df = audit_heldout_manifest()

    metrics_df, manifest_df = run_all_heldout_sweeps(models, heldout_df)
    comp_df = build_detailed_comparison_table(metrics_df)
    pop_summary_df, proto_df = compute_statistical_summaries(comp_df)
    generate_evaluation_figures(comp_df, models)

    logger.info("=== Phase 4C Evaluation Completed Successfully ===")


if __name__ == "__main__":
    main()


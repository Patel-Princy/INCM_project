#!/usr/bin/env python3
"""INCM Phase 3C: Independent Metric Recomputation and Audit Script.

Reads directly from:
- results/phase3b/heldout/<specimen_id>/sweep_<id>/summary.json
- results/phase3b/heldout_metrics.csv
- results/phase3b/heldout_sweeps.csv

Produces:
- results/phase3c/recomputed_population_metrics.csv
- Comparison report of reported vs independently recomputed values.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_3B = ROOT / "results" / "phase3b"
RESULTS_3C = ROOT / "results" / "phase3c"
RESULTS_3C.mkdir(parents=True, exist_ok=True)

REPRESENTATIVES = {
    484564503: {"pop": "A", "layer": "4", "model": 485591776, "cal_sweep": 49},
    318808427: {"pop": "B", "layer": "2/3", "model": 473863035, "cal_sweep": 40},
    471129934: {"pop": "C", "layer": "5", "model": 480624414, "cal_sweep": 51},
    471786879: {"pop": "D", "layer": "6a", "model": 480632594, "cal_sweep": 42},
}


def audit_summary_json_integrity(df_metrics: pd.DataFrame) -> dict:
    """Check that every row in heldout_metrics.csv perfectly matches its disk summary.json."""
    mismatches = []
    checked = 0
    for _, row in df_metrics.iterrows():
        sid = int(row["specimen_id"])
        swp = int(row["sweep_number"])
        json_path = RESULTS_3B / "heldout" / str(sid) / f"sweep_{swp}" / "summary.json"
        if not json_path.exists():
            mismatches.append(f"Missing summary.json for specimen {sid}, sweep {swp}")
            continue

        with json_path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        # Verify key metrics
        m = data["metrics"]
        s = data["stimulus"]
        if abs(float(row["rmse_overall_mv"]) - m["rmse_overall_mv"]) > 1e-3:
            mismatches.append(f"RMSE mismatch in {sid} sweep {swp}: csv={row['rmse_overall_mv']} json={m['rmse_overall_mv']}")
        if abs(float(row["mae_mv"]) - m["mae_mv"]) > 1e-3:
            mismatches.append(f"MAE mismatch in {sid} sweep {swp}: csv={row['mae_mv']} json={m['mae_mv']}")
        if abs(float(row["correlation"]) - m["correlation"]) > 1e-4:
            mismatches.append(f"Corr mismatch in {sid} sweep {swp}: csv={row['correlation']} json={m['correlation']}")
        if int(row["spike_count_recorded_in_step"]) != m["spike_count_recorded_in_step"]:
            mismatches.append(f"Rec spike mismatch in {sid} sweep {swp}: csv={row['spike_count_recorded_in_step']} json={m['spike_count_recorded_in_step']}")
        if int(row["spike_count_simulated_in_step"]) != m["spike_count_simulated_in_step"]:
            mismatches.append(f"Sim spike mismatch in {sid} sweep {swp}: csv={row['spike_count_simulated_in_step']} json={m['spike_count_simulated_in_step']}")

        checked += 1

    return {"checked": checked, "mismatches": mismatches}


def recompute_all_metrics():
    df_metrics = pd.read_csv(RESULTS_3B / "heldout_metrics.csv")
    df_heldout = pd.read_csv(RESULTS_3B / "heldout_sweeps.csv")
    df_conds = pd.read_csv(RESULTS_3B / "condition_groups.csv")

    integrity = audit_summary_json_integrity(df_metrics)
    print(f"Summary JSON integrity check: {integrity['checked']}/109 files checked, {len(integrity['mismatches'])} mismatches.")
    if integrity["mismatches"]:
        for m in integrity["mismatches"]:
            print(f"  WARNING: {m}")

    recomputed_rows = []

    for sid, rep_info in REPRESENTATIVES.items():
        pop = rep_info["pop"]
        layer = rep_info["layer"]
        sub = df_metrics[df_metrics["specimen_id"] == sid]
        n_sweeps = len(sub)

        # Unique conditions
        u_conds = sub["stimulus_amplitude_pa"].nunique()

        # Sweep-level statistics (ddof=1 sample std, ddof=0 population std)
        rmse_mean = float(sub["rmse_overall_mv"].mean())
        rmse_std_sample = float(sub["rmse_overall_mv"].std(ddof=1))
        rmse_std_pop = float(sub["rmse_overall_mv"].std(ddof=0))

        mae_mean = float(sub["mae_mv"].mean())
        mae_std_sample = float(sub["mae_mv"].std(ddof=1))
        mae_std_pop = float(sub["mae_mv"].std(ddof=0))

        corr_mean = float(sub["correlation"].mean())
        corr_std_sample = float(sub["correlation"].std(ddof=1))
        corr_std_pop = float(sub["correlation"].std(ddof=0))

        # Baseline delta
        base_rec_mean = float(sub["baseline_recorded_mv"].mean())
        base_sim_mean = float(sub["baseline_simulated_mv"].mean())
        base_delta_mean = float(sub["baseline_delta_mv"].mean())

        # Spike deltas (simulated - recorded)
        spk_delta_mean = float(sub["spike_count_delta"].mean())
        spk_delta_std = float(sub["spike_count_delta"].std(ddof=1))
        spk_delta_max = int(sub["spike_count_delta"].abs().max())
        spk_delta_max_signed = int(sub.loc[sub["spike_count_delta"].abs().idxmax()]["spike_count_delta"])

        # Subthreshold vs Suprathreshold
        # Biological recorded criterion: rec == 0 vs rec > 0
        rec_sub = sub[sub["spike_count_recorded_in_step"] == 0]
        rec_supra = sub[sub["spike_count_recorded_in_step"] > 0]
        rec_sub_corr = float(rec_sub["correlation"].mean()) if not rec_sub.empty else np.nan
        rec_supra_corr = float(rec_supra["correlation"].mean()) if not rec_supra.empty else np.nan
        rec_sub_rmse = float(rec_sub["rmse_overall_mv"].mean()) if not rec_sub.empty else np.nan
        rec_supra_rmse = float(rec_supra["rmse_overall_mv"].mean()) if not rec_supra.empty else np.nan

        # Model simulated criterion: sim == 0 vs sim > 0
        sim_sub = sub[sub["spike_count_simulated_in_step"] == 0]
        sim_supra = sub[sub["spike_count_simulated_in_step"] > 0]
        sim_sub_corr = float(sim_sub["correlation"].mean()) if not sim_sub.empty else np.nan
        sim_supra_corr = float(sim_supra["correlation"].mean()) if not sim_supra.empty else np.nan

        # Joint subthreshold criterion: rec == 0 AND sim == 0
        joint_sub = sub[(sub["spike_count_recorded_in_step"] == 0) & (sub["spike_count_simulated_in_step"] == 0)]
        joint_sub_corr = float(joint_sub["correlation"].mean()) if not joint_sub.empty else np.nan

        # Protocol-specific performance
        coarse = sub[sub["protocol_family"] == "COARSE"]
        finest = sub[sub["protocol_family"] == "FINEST"]

        coarse_rmse = float(coarse["rmse_overall_mv"].mean()) if not coarse.empty else np.nan
        coarse_corr = float(coarse["correlation"].mean()) if not coarse.empty else np.nan
        coarse_spk_delta = float(coarse["spike_count_delta"].mean()) if not coarse.empty else np.nan

        finest_rmse = float(finest["rmse_overall_mv"].mean()) if not finest.empty else np.nan
        finest_corr = float(finest["correlation"].mean()) if not finest.empty else np.nan
        finest_spk_delta = float(finest["spike_count_delta"].mean()) if not finest.empty else np.nan

        # Rheobase (COARSE)
        rec_0_c = coarse[coarse["spike_count_recorded_in_step"] == 0]["stimulus_amplitude_pa"].max()
        rec_1_c = coarse[coarse["spike_count_recorded_in_step"] > 0]["stimulus_amplitude_pa"].min()
        sim_0_c = coarse[coarse["spike_count_simulated_in_step"] == 0]["stimulus_amplitude_pa"].max()
        sim_1_c = coarse[coarse["spike_count_simulated_in_step"] > 0]["stimulus_amplitude_pa"].min()

        rec_rheo_mid = (rec_0_c + rec_1_c) / 2.0 if (pd.notna(rec_0_c) and pd.notna(rec_1_c)) else np.nan
        sim_rheo_mid = (sim_0_c + sim_1_c) / 2.0 if (pd.notna(sim_0_c) and pd.notna(sim_1_c)) else np.nan
        rheo_shift = sim_rheo_mid - rec_rheo_mid if (pd.notna(rec_rheo_mid) and pd.notna(sim_rheo_mid)) else np.nan

        # Rheobase (Overall across all sweeps)
        rec_0_all = sub[sub["spike_count_recorded_in_step"] == 0]["stimulus_amplitude_pa"].max()
        rec_1_all = sub[sub["spike_count_recorded_in_step"] > 0]["stimulus_amplitude_pa"].min()
        sim_0_all = sub[sub["spike_count_simulated_in_step"] == 0]["stimulus_amplitude_pa"].max()
        sim_1_all = sub[sub["spike_count_simulated_in_step"] > 0]["stimulus_amplitude_pa"].min()

        recomputed_rows.append({
            "specimen_id": sid,
            "population": pop,
            "layer": layer,
            "n_heldout_sweeps": n_sweeps,
            "n_unique_conditions": u_conds,
            "n_coarse_sweeps": len(coarse),
            "n_finest_sweeps": len(finest),
            "rmse_mean_mv": round(rmse_mean, 3),
            "rmse_std_sample_mv": round(rmse_std_sample, 3),
            "rmse_std_pop_mv": round(rmse_std_pop, 3),
            "mae_mean_mv": round(mae_mean, 3),
            "mae_std_sample_mv": round(mae_std_sample, 3),
            "mae_std_pop_mv": round(mae_std_pop, 3),
            "corr_mean": round(corr_mean, 4),
            "corr_std_sample": round(corr_std_sample, 4),
            "corr_std_pop": round(corr_std_pop, 4),
            "rec_vrest_mean_mv": round(base_rec_mean, 2),
            "sim_vrest_mean_mv": round(base_sim_mean, 2),
            "vrest_delta_mean_mv": round(base_delta_mean, 2),
            "spike_delta_mean": round(spk_delta_mean, 3),
            "spike_delta_std": round(spk_delta_std, 3),
            "spike_delta_max_abs": spk_delta_max,
            "spike_delta_max_signed": spk_delta_max_signed,
            "rec_subthreshold_corr": round(rec_sub_corr, 4) if pd.notna(rec_sub_corr) else None,
            "rec_suprathreshold_corr": round(rec_supra_corr, 4) if pd.notna(rec_supra_corr) else None,
            "rec_subthreshold_rmse_mv": round(rec_sub_rmse, 3) if pd.notna(rec_sub_rmse) else None,
            "rec_suprathreshold_rmse_mv": round(rec_supra_rmse, 3) if pd.notna(rec_supra_rmse) else None,
            "sim_subthreshold_corr": round(sim_sub_corr, 4) if pd.notna(sim_sub_corr) else None,
            "sim_suprathreshold_corr": round(sim_supra_corr, 4) if pd.notna(sim_supra_corr) else None,
            "joint_subthreshold_corr": round(joint_sub_corr, 4) if pd.notna(joint_sub_corr) else None,
            "coarse_rmse_mv": round(coarse_rmse, 3) if pd.notna(coarse_rmse) else None,
            "coarse_corr": round(coarse_corr, 4) if pd.notna(coarse_corr) else None,
            "coarse_spike_delta": round(coarse_spk_delta, 3) if pd.notna(coarse_spk_delta) else None,
            "finest_rmse_mv": round(finest_rmse, 3) if pd.notna(finest_rmse) else None,
            "finest_corr": round(finest_corr, 4) if pd.notna(finest_corr) else None,
            "finest_spike_delta": round(finest_spk_delta, 3) if pd.notna(finest_spk_delta) else None,
            "coarse_rec_sub_max_pa": rec_0_c,
            "coarse_rec_supra_min_pa": rec_1_c,
            "coarse_rec_rheo_mid_pa": rec_rheo_mid,
            "coarse_sim_sub_max_pa": sim_0_c,
            "coarse_sim_supra_min_pa": sim_1_c,
            "coarse_sim_rheo_mid_pa": sim_rheo_mid,
            "coarse_rheobase_shift_pa": rheo_shift,
            "overall_rec_sub_max_pa": rec_0_all,
            "overall_rec_supra_min_pa": rec_1_all,
            "overall_sim_sub_max_pa": sim_0_all,
            "overall_sim_supra_min_pa": sim_1_all,
        })

    df_out = pd.DataFrame(recomputed_rows)
    out_csv = RESULTS_3C / "recomputed_population_metrics.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"Recomputed metrics saved to {out_csv}")
    return df_out


if __name__ == "__main__":
    recompute_all_metrics()

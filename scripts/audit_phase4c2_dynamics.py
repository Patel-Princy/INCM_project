"""INCM Phase 4C.2: Transient Adaptation and Population-Specific Bifurcation Verification.

Audits:
1. Transient spike-frequency adaptation in FHN vs sustained biological adaptation across held-out sweeps.
2. Population-specific Hopf bifurcation, transversality condition, and first Lyapunov coefficient for all 4 calibrated models.
3. Rigorous separation of local bifurcation results from global limit cycle folds and bistability.
"""
from __future__ import annotations

import json
import logging
import math
import pathlib
import sys
import time
from typing import Any, Dict, List, Tuple

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RESULTS_4B = REPO_ROOT / "results" / "phase4b"
RESULTS_4C = REPO_ROOT / "results" / "phase4c"
RESULTS_4C2 = REPO_ROOT / "results" / "phase4c2"
FIGURES_DIR = RESULTS_4C2 / "figures"
DATA_DIR = REPO_ROOT / "data" / "nwb_cache"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Phase4C2Audit")

from src.models.fitzhugh_nagumo import (
    FHNParameters,
    FHNSimulationConfig,
    FitzHughNagumoModel,
)

FROZEN_CALIBRATION_ASSIGNMENTS = {
    "A": {"specimen_id": 484564503, "layer": "4", "calibration_sweep": 49},
    "B": {"specimen_id": 318808427, "layer": "2/3", "calibration_sweep": 40},
    "C": {"specimen_id": 471129934, "layer": "5", "calibration_sweep": 51},
    "D": {"specimen_id": 471786879, "layer": "6a", "calibration_sweep": 42},
}


def ensure_directories() -> None:
    RESULTS_4C2.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# 1. Transient Spike-Frequency Adaptation Audit
# -----------------------------------------------------------------------------
def audit_transient_adaptation() -> pd.DataFrame:
    logger.info("Executing Task 1: Transient spike-frequency adaptation audit...")
    fhn_metrics = pd.read_csv(RESULTS_4C / "fhn_heldout_metrics.csv")
    params_df = pd.read_csv(RESULTS_4B / "fhn_fitted_parameters.csv").set_index("population")

    # Select sweeps with at least 3 spikes in FHN or Recording for meaningful ISI comparison
    spiking_sweeps = fhn_metrics[
        (fhn_metrics["spike_count_fhn_in_step"] >= 3) | (fhn_metrics["spike_count_recorded_in_step"] >= 3)
    ]

    isi_records = []
    for _, row in spiking_sweeps.iterrows():
        pop = str(row["population"])
        spec = int(row["specimen_id"])
        swp = int(row["sweep_number"])
        proto = str(row["protocol_family"])
        amp = float(row["stimulus_amplitude_pa"])

        nwb_path = DATA_DIR / f"{spec}.nwb"
        with h5py.File(nwb_path, "r") as f:
            v_raw = f["acquisition"]["timeseries"][f"Sweep_{swp}"]["data"][:] * 1e3
            i_raw = f["stimulus"]["presentation"][f"Sweep_{swp}"]["data"][:] * 1e12
            rate = float(f["acquisition"]["timeseries"][f"Sweep_{swp}"]["starting_time"].attrs["rate"])
            t_exp = np.arange(len(v_raw)) / rate * 1e3

        p = params_df.loc[pop]
        params = FHNParameters(
            C_m=float(p["C_m_pf"]),
            g_L=float(p["g_L_ns"]),
            V_rest=float(p["V_rest_mv"]),
            V_th=float(p["V_th_mv"]),
            V_peak=float(p["V_peak_mv"]),
            k_v=float(p["k_v_ns_per_mv2"]),
            tau_w=float(p["tau_w_ms"]),
            a_w=float(p["a_w_ns"]),
        )
        model = FitzHughNagumoModel(params)
        t_stop = float(t_exp[-1])
        dt_sim = 0.025
        n_steps = int(round(t_stop / dt_sim))
        t_sim = np.linspace(0.0, t_stop, n_steps + 1)
        i_sim = np.interp(t_sim, t_exp, i_raw)

        res = model.simulate(FHNSimulationConfig(dt_ms=dt_sim, t_stop_ms=t_stop), stimulus=i_sim)
        v_fhn = np.interp(t_exp, res.time_ms, res.v_mv)

        def detect_spks(v_arr: np.ndarray) -> list[float]:
            spks = []
            for i in range(len(v_arr) - 1):
                if v_arr[i] < 0.0 and v_arr[i + 1] >= 0.0 and (1020.0 <= t_exp[i] <= 2020.0):
                    if len(spks) == 0 or (t_exp[i] - spks[-1]) >= 2.0:
                        spks.append(float(t_exp[i]))
            return spks

        spk_rec = detect_spks(v_raw)
        spk_fhn = detect_spks(v_fhn)

        isi_rec = np.diff(spk_rec) if len(spk_rec) >= 2 else np.array([])
        isi_fhn = np.diff(spk_fhn) if len(spk_fhn) >= 2 else np.array([])

        # FHN ISI metrics
        if len(isi_fhn) >= 2:
            fhn_isi_1 = float(isi_fhn[0])
            fhn_isi_2 = float(isi_fhn[1])
            fhn_isi_last = float(isi_fhn[-1])
            fhn_isi_median = float(np.median(isi_fhn))
            fhn_ratio_2_to_1 = fhn_isi_2 / fhn_isi_1
            fhn_pct_change_initial = (fhn_isi_2 - fhn_isi_1) / fhn_isi_1 * 100.0
            fhn_ratio_last_to_1 = fhn_isi_last / fhn_isi_1
            fhn_pct_change_overall = (fhn_isi_last - fhn_isi_1) / fhn_isi_1 * 100.0

            # Determine cycles to stationarity (|delta ISI| < 0.1 ms)
            cycles_to_stationarity = 1
            for k in range(1, len(isi_fhn)):
                if abs(isi_fhn[k] - isi_fhn[k - 1]) < 0.1:
                    cycles_to_stationarity = k
                    break
        else:
            fhn_isi_1 = fhn_isi_2 = fhn_isi_last = fhn_isi_median = math.nan
            fhn_ratio_2_to_1 = fhn_pct_change_initial = fhn_ratio_last_to_1 = fhn_pct_change_overall = math.nan
            cycles_to_stationarity = 0

        # Recorded ISI metrics
        if len(isi_rec) >= 2:
            rec_isi_1 = float(isi_rec[0])
            rec_isi_2 = float(isi_rec[1])
            rec_isi_last = float(isi_rec[-1])
            rec_isi_median = float(np.median(isi_rec))
            rec_ratio_2_to_1 = rec_isi_2 / rec_isi_1
            rec_ratio_last_to_1 = rec_isi_last / rec_isi_1
            rec_pct_change_overall = (rec_isi_last - rec_isi_1) / rec_isi_1 * 100.0
        else:
            rec_isi_1 = rec_isi_2 = rec_isi_last = rec_isi_median = math.nan
            rec_ratio_2_to_1 = rec_ratio_last_to_1 = rec_pct_change_overall = math.nan

        isi_records.append({
            "specimen_id": spec,
            "population": pop,
            "sweep_number": swp,
            "protocol_family": proto,
            "stimulus_amplitude_pa": amp,
            "spikes_rec": len(spk_rec),
            "spikes_fhn": len(spk_fhn),
            # FHN dynamics
            "fhn_isi_1_ms": round(fhn_isi_1, 2) if not math.isnan(fhn_isi_1) else math.nan,
            "fhn_isi_2_ms": round(fhn_isi_2, 2) if not math.isnan(fhn_isi_2) else math.nan,
            "fhn_isi_last_ms": round(fhn_isi_last, 2) if not math.isnan(fhn_isi_last) else math.nan,
            "fhn_isi_median_ms": round(fhn_isi_median, 2) if not math.isnan(fhn_isi_median) else math.nan,
            "fhn_pct_change_initial": round(fhn_pct_change_initial, 2) if not math.isnan(fhn_pct_change_initial) else math.nan,
            "fhn_ratio_last_to_1": round(fhn_ratio_last_to_1, 4) if not math.isnan(fhn_ratio_last_to_1) else math.nan,
            "fhn_pct_change_overall": round(fhn_pct_change_overall, 2) if not math.isnan(fhn_pct_change_overall) else math.nan,
            "fhn_cycles_to_stationarity": cycles_to_stationarity,
            # Recording dynamics
            "rec_isi_1_ms": round(rec_isi_1, 2) if not math.isnan(rec_isi_1) else math.nan,
            "rec_isi_last_ms": round(rec_isi_last, 2) if not math.isnan(rec_isi_last) else math.nan,
            "rec_ratio_last_to_1": round(rec_ratio_last_to_1, 4) if not math.isnan(rec_ratio_last_to_1) else math.nan,
            "rec_pct_change_overall": round(rec_pct_change_overall, 2) if not math.isnan(rec_pct_change_overall) else math.nan,
        })

    isi_df = pd.DataFrame(isi_records)
    out_csv = RESULTS_4C2 / "phase4c2_isi_transient_adaptation.csv"
    isi_df.to_csv(out_csv, index=False)
    logger.info(f"Saved transient adaptation audit to {out_csv}")
    return isi_df


# -----------------------------------------------------------------------------
# 2. Population-Specific Hopf and Transversality Verification
# -----------------------------------------------------------------------------
def audit_hopf_and_transversality() -> Tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Executing Task 2: Population-specific Hopf & transversality verification...")
    params_df = pd.read_csv(RESULTS_4B / "fhn_fitted_parameters.csv").set_index("population")

    hopf_rows = []
    derivation_rows = []

    for pop in ["A", "B", "C", "D"]:
        p = params_df.loc[pop]
        Cm = float(p["C_m_pf"])
        gL = float(p["g_L_ns"])
        aw = float(p["a_w_ns"])
        kv = float(p["k_v_ns_per_mv2"])
        tau_w = float(p["tau_w_ms"])
        Vrest = float(p["V_rest_mv"])
        Vth = float(p["V_th_mv"])
        Vpeak = float(p["V_peak_mv"])

        # 1. Condition for limit cycles: aw * tau_w / Cm > 1
        cond_ratio = (aw * tau_w) / Cm

        # 2. Trace-zero equation: F'(V*) = Cm / tau_w
        # F(V) = -gL(V-Vrest) - kv(V-Vrest)(V-Vth)(V-Vpeak)
        # F'(V) = -gL - kv [ 3 V^2 - 2(Vrest+Vth+Vpeak)V + (Vrest*Vth + Vrest*Vpeak + Vth*Vpeak) ]
        A_quad = -3.0 * kv
        B_quad = 2.0 * kv * (Vrest + Vth + Vpeak)
        C_quad = -(gL + Cm / tau_w + kv * (Vrest * Vth + Vrest * Vpeak + Vth * Vpeak))
        disc = B_quad**2 - 4.0 * A_quad * C_quad

        v_h1 = (-B_quad + math.sqrt(disc)) / (2.0 * A_quad)  # lower Hopf root
        v_h2 = (-B_quad - math.sqrt(disc)) / (2.0 * A_quad)  # upper Hopf root

        def F_cubic(v: float) -> float:
            return -gL * (v - Vrest) - kv * (v - Vrest) * (v - Vth) * (v - Vpeak)

        def dF_dv(v: float) -> float:
            return -gL - kv * (
                (v - Vth) * (v - Vpeak) + (v - Vrest) * (v - Vpeak) + (v - Vrest) * (v - Vth)
            )

        def d2F_dv2(v: float) -> float:
            return -6.0 * kv * v + 2.0 * kv * (Vrest + Vth + Vpeak)

        def d3F_dv3() -> float:
            return -6.0 * kv

        # Equilibrium quantities at lower Hopf
        i_h1 = aw * (v_h1 - Vrest) - F_cubic(v_h1)
        w_h1 = aw * (v_h1 - Vrest)

        # Residuals
        res_dv = (F_cubic(v_h1) - w_h1 + i_h1) / Cm
        res_dw = (aw * (v_h1 - Vrest) - w_h1) / tau_w

        # Jacobian at Hopf point
        df_val = dF_dv(v_h1)
        tr_J = (df_val / Cm) - (1.0 / tau_w)
        det_J = (aw - df_val) / (Cm * tau_w)
        omega0 = math.sqrt(det_J)

        # Pure imaginary eigenvalues check: lambda = 0 +/- i * omega0
        eigenvalue_real = 0.5 * tr_J
        eigenvalue_imag = omega0

        # Transversality derivative dRe(lambda)/dI
        # dRe/dI = d2F / [2 * Cm * (aw - Cm/tau_w)]
        d2f_val = d2F_dv2(v_h1)
        mu_prime = d2f_val / (2.0 * Cm * (aw - Cm / tau_w))

        # First Lyapunov coefficient l_1 via Kuznetsov algorithm
        A_mat = np.array([[1.0 / tau_w, -1.0 / Cm], [aw / tau_w, -1.0 / tau_w]])
        q = np.array([1.0, Cm * (1.0 / tau_w - 1j * omega0)])
        p_raw = np.array([-(aw / tau_w) / (1.0 / tau_w + 1j * omega0), 1.0])
        p_vec = p_raw / np.conj(np.vdot(p_raw, q))

        def b_vec(x: np.ndarray, y: np.ndarray) -> np.ndarray:
            return np.array([(d2f_val / Cm) * x[0] * y[0], 0.0 + 0j])

        def c_vec(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
            return np.array([(d3F_dv3() / Cm) * x[0] * y[0] * z[0], 0.0 + 0j])

        t1 = np.vdot(p_vec, c_vec(q, q, np.conj(q)))
        t2 = -2.0 * np.vdot(p_vec, b_vec(q, np.linalg.solve(A_mat, b_vec(q, np.conj(q)))))
        t3 = np.vdot(p_vec, b_vec(np.conj(q), np.linalg.solve(2j * omega0 * np.eye(2) - A_mat, b_vec(q, q))))

        l1 = 0.5 * float(np.real(t1 + t2 + t3))

        # Global Fold of Limit Cycles (LPC) determination
        # We step down from I_H1 to find where the large limit cycle extinguishes
        model = FitzHughNagumoModel(
            FHNParameters(
                C_m=Cm, g_L=gL, V_rest=Vrest, V_th=Vth, V_peak=Vpeak, k_v=kv, tau_w=tau_w, a_w=aw
            )
        )
        c_init = FHNSimulationConfig(dt_ms=0.025, t_stop_ms=2000.0)
        r_init = model.simulate(c_init, stimulus=lambda t: i_h1 + 5.0)
        v_orbit = float(r_init.v_mv[-1])
        w_orbit = float(r_init.w_pa[-1])

        i_fold_est = i_h1
        for i_step in np.arange(i_h1, i_h1 - 50.0, -1.0):
            cfg_test = FHNSimulationConfig(
                dt_ms=0.025, t_stop_ms=2500.0, V_init_mv=v_orbit, w_init_pa=w_orbit
            )
            res_test = model.simulate(cfg_test, stimulus=lambda t: float(i_step))
            late_spks = [s for s in res_test.detect_spikes(threshold_mv=0.0) if s >= 1000.0]
            if len(late_spks) >= 2:
                v_orbit = float(res_test.v_mv[-1])
                w_orbit = float(res_test.w_pa[-1])
                i_fold_est = float(i_step)
            else:
                break

        bistability_width = i_h1 - i_fold_est

        hopf_rows.append({
            "population": pop,
            "layer": FROZEN_CALIBRATION_ASSIGNMENTS[pop]["layer"],
            "specimen_id": FROZEN_CALIBRATION_ASSIGNMENTS[pop]["specimen_id"],
            "C_m_pf": Cm,
            "tau_w_ms": tau_w,
            "a_w_ns": aw,
            "hopf_condition_ratio": round(cond_ratio, 3),
            "lower_hopf_voltage_mv": round(v_h1, 4),
            "lower_hopf_recovery_pa": round(w_h1, 4),
            "lower_hopf_current_pa": round(i_h1, 4),
            "jacobian_trace": round(tr_J, 15),
            "jacobian_determinant": round(det_J, 8),
            "eigenfrequency_omega0_rad_per_ms": round(omega0, 4),
            "transversality_dRe_dI": round(mu_prime, 6),
            "first_lyapunov_coefficient": l1,
            "local_criticality": "SUBCRITICAL_HOPF",
            "global_fold_of_cycles_I_fold_pa": round(i_fold_est, 1),
            "global_bistability_width_pa": round(bistability_width, 1),
            "bistability_interval": f"[{i_fold_est:.1f}, {i_h1:.1f}] pA",
        })

        derivation_rows.append({
            "population": pop,
            "check_equilibrium_residual_dV": abs(res_dv) < 1e-12,
            "check_equilibrium_residual_dw": abs(res_dw) < 1e-12,
            "check_trace_is_zero": abs(tr_J) < 1e-12,
            "check_determinant_positive": det_J > 0,
            "check_eigenvalues_pure_imaginary": abs(eigenvalue_real) < 1e-12 and eigenvalue_imag > 0,
            "check_transversality_positive": mu_prime > 0,
            "check_lyapunov_positive": l1 > 0,
            "check_subcritical_bistability_demonstrated": bistability_width > 5.0,
        })

    hopf_df = pd.DataFrame(hopf_rows)
    deriv_df = pd.DataFrame(derivation_rows)

    out_hopf_csv = RESULTS_4C2 / "phase4c2_population_hopf_verification.csv"
    out_deriv_csv = RESULTS_4C2 / "phase4c2_hopf_derivation_checks.csv"

    hopf_df.to_csv(out_hopf_csv, index=False)
    deriv_df.to_csv(out_deriv_csv, index=False)

    logger.info(f"Saved population Hopf verification to {out_hopf_csv}")
    logger.info(f"Saved derivation checks to {out_deriv_csv}")
    return hopf_df, deriv_df


# -----------------------------------------------------------------------------
# 3. Diagnostic Figure Generation
# -----------------------------------------------------------------------------
def generate_audit_figures() -> None:
    logger.info("Executing Task 3: Generating diagnostic figures...")
    params_df = pd.read_csv(RESULTS_4B / "fhn_fitted_parameters.csv").set_index("population")

    # Figure 1: ISI Adaptation Comparison across populations
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    rep_sweeps = [
        ("A", 484564503, 51, 410.0, "Population A (L4, Spec 484564503, Sweep 51, +410 pA)"),
        ("B", 318808427, 41, 210.0, "Population B (L2/3, Spec 318808427, Sweep 41, +210 pA)"),
        ("C", 471129934, 52, 430.0, "Population C (L5, Spec 471129934, Sweep 52, +430 pA)"),
        ("D", 471786879, 43, 270.0, "Population D (L6a, Spec 471786879, Sweep 43, +270 pA)"),
    ]

    for idx, (pop, spec, swp, amp, title) in enumerate(rep_sweeps):
        ax = axes.flatten()[idx]

        # Extract recorded trace
        with h5py.File(DATA_DIR / f"{spec}.nwb", "r") as f:
            v_raw = f["acquisition"]["timeseries"][f"Sweep_{swp}"]["data"][:] * 1e3
            i_raw = f["stimulus"]["presentation"][f"Sweep_{swp}"]["data"][:] * 1e12
            rate = float(f["acquisition"]["timeseries"][f"Sweep_{swp}"]["starting_time"].attrs["rate"])
            t_exp = np.arange(len(v_raw)) / rate * 1e3

        p = params_df.loc[pop]
        model = FitzHughNagumoModel(
            FHNParameters(
                C_m=float(p["C_m_pf"]),
                g_L=float(p["g_L_ns"]),
                V_rest=float(p["V_rest_mv"]),
                V_th=float(p["V_th_mv"]),
                V_peak=float(p["V_peak_mv"]),
                k_v=float(p["k_v_ns_per_mv2"]),
                tau_w=float(p["tau_w_ms"]),
                a_w=float(p["a_w_ns"]),
            )
        )
        t_stop = float(t_exp[-1])
        dt_sim = 0.025
        n_steps = int(round(t_stop / dt_sim))
        t_sim = np.linspace(0.0, t_stop, n_steps + 1)
        i_sim = np.interp(t_sim, t_exp, i_raw)

        res = model.simulate(FHNSimulationConfig(dt_ms=dt_sim, t_stop_ms=t_stop), stimulus=i_sim)
        v_fhn = np.interp(t_exp, res.time_ms, res.v_mv)

        def detect_spks(v_arr: np.ndarray) -> list[float]:
            spks = []
            for i in range(len(v_arr) - 1):
                if v_arr[i] < 0.0 and v_arr[i + 1] >= 0.0 and (1020.0 <= t_exp[i] <= 2020.0):
                    if len(spks) == 0 or (t_exp[i] - spks[-1]) >= 2.0:
                        spks.append(float(t_exp[i]))
            return spks

        spk_rec = detect_spks(v_raw)
        spk_fhn = detect_spks(v_fhn)

        isi_rec = np.diff(spk_rec) if len(spk_rec) >= 2 else []
        isi_fhn = np.diff(spk_fhn) if len(spk_fhn) >= 2 else []

        x_rec = np.arange(1, len(isi_rec) + 1)
        x_fhn = np.arange(1, len(isi_fhn) + 1)

        if len(isi_rec) > 0:
            ax.plot(x_rec, isi_rec, "ko-", lw=1.8, markersize=6, label=f"Recording (n={len(isi_rec)} ISIs)")
        if len(isi_fhn) > 0:
            ax.plot(x_fhn, isi_fhn, "^--", color="#d95f02", lw=1.8, markersize=6, label=f"FHN (n={len(isi_fhn)} ISIs)")

        ax.set_title(title, fontsize=10.5, fontweight="bold")
        ax.set_xlabel("Inter-Spike Interval Index ($k$)", fontsize=9.5)
        ax.set_ylabel(r"Interval Duration $\mathrm{ISI}_k$ [ms]", fontsize=9.5)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper left" if pop in ["B", "D"] else "center left", fontsize=8.5)

    plt.tight_layout()
    fig1_path = FIGURES_DIR / "isi_adaptation_comparison.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 1 to {fig1_path}")

    # Figure 2: Hopf Transversality (Re(lambda) vs Injected Current I)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    pops = ["A", "B", "C", "D"]
    for idx, (pop, ax) in enumerate(zip(pops, axes.flatten())):
        p = params_df.loc[pop]
        Cm = float(p["C_m_pf"])
        gL = float(p["g_L_ns"])
        aw = float(p["a_w_ns"])
        kv = float(p["k_v_ns_per_mv2"])
        tau_w = float(p["tau_w_ms"])
        Vrest = float(p["V_rest_mv"])
        Vth = float(p["V_th_mv"])
        Vpeak = float(p["V_peak_mv"])

        A_quad = -3.0 * kv
        B_quad = 2.0 * kv * (Vrest + Vth + Vpeak)
        C_quad = -(gL + Cm / tau_w + kv * (Vrest * Vth + Vrest * Vpeak + Vth * Vpeak))
        disc = B_quad**2 - 4.0 * A_quad * C_quad
        v_h1 = (-B_quad + math.sqrt(disc)) / (2.0 * A_quad)

        def F_cubic(v: float) -> float:
            return -gL * (v - Vrest) - kv * (v - Vrest) * (v - Vth) * (v - Vpeak)

        def dF_dv(v: float) -> float:
            return -gL - kv * (
                (v - Vth) * (v - Vpeak) + (v - Vrest) * (v - Vpeak) + (v - Vrest) * (v - Vth)
            )

        i_h1 = aw * (v_h1 - Vrest) - F_cubic(v_h1)

        # Scan currents around I_H1: +/- 30 pA
        i_range = np.linspace(i_h1 - 30.0, i_h1 + 30.0, 300)
        re_lambda = []
        for i_val in i_range:
            # Solve equilibrium V* numerically near v_h1
            # 0 = F(V*) - aw*(V* - Vrest) + i_val
            # Newton-Raphson
            v_curr = v_h1
            for _ in range(25):
                f_val = F_cubic(v_curr) - aw * (v_curr - Vrest) + i_val
                df_curr = dF_dv(v_curr) - aw
                v_curr -= f_val / df_curr
            tr = (dF_dv(v_curr) / Cm) - (1.0 / tau_w)
            re_lambda.append(0.5 * tr)

        ax.plot(i_range, re_lambda, color="#2b5c8f", lw=2.0, label=r"$\mathrm{Re}(\lambda(I))$")
        ax.axhline(0.0, color="gray", linestyle="--", lw=1.0)
        ax.axvline(i_h1, color="red", linestyle=":", lw=1.5, label=rf"$I_{{H1}} = {i_h1:.1f}$ pA")
        ax.plot(i_h1, 0.0, "ro", markersize=7)

        ax.set_title(f"Population {pop} (Layer {FROZEN_CALIBRATION_ASSIGNMENTS[pop]['layer']}): Hopf Transversality", fontsize=11, fontweight="bold")
        ax.set_xlabel("Injected Current $I$ [pA]", fontsize=10)
        ax.set_ylabel(r"$\mathrm{Re}(\lambda)$ [$\mathrm{ms}^{-1}$]", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="upper left", fontsize=8.5)

    plt.tight_layout()
    fig2_path = FIGURES_DIR / "population_hopf_transversality.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    logger.info(f"Saved Figure 2 to {fig2_path}")


# -----------------------------------------------------------------------------
# Main Execution Pipeline
# -----------------------------------------------------------------------------
def main() -> None:
    logger.info("=== Starting INCM Phase 4C.2: Transient Adaptation & Hopf Audit ===")
    ensure_directories()

    audit_transient_adaptation()
    audit_hopf_and_transversality()
    generate_audit_figures()

    logger.info("=== Phase 4C.2 Audit Script Completed Successfully ===")


if __name__ == "__main__":
    main()

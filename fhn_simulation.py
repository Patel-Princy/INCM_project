"""
fhn_simulation.py
=================
Author: Princy (INCM Course Project)
Branch: Princy-work

Purpose:
--------
This script implements, calibrates, and simulates the standard two-variable
FitzHugh-Nagumo (FHN) model for:
- Layer 2/3 Pyramidal Neuron (Specimen 318808427, Calibration Sweep 40 at +190 pA)
- Layer 5 Pyramidal Neuron   (Specimen 471129934, Calibration Sweep 51 at +410 pA)

The FitzHugh-Nagumo (FHN) System of Differential Equations:
-----------------------------------------------------------
    dv/dt = v - (v^3 / 3) - w + I
    dw/dt = eps * (v + a - b * w)

Where:
- v: Membrane voltage-like variable (fast excitation)
- w: Recovery variable (slow outward current / refractory variable)
- I: Injected external current (dimensionless, scaled from physical pA)
- eps, a, b: Model parameters controlling recovery speed and threshold excitability.

Design constraints:
- Uses simple forward Euler integration (for-loop over time).
- Fits parameters using ONLY the single designated calibration sweep for each specimen.
- Zero held-out test sweeps are seen during calibration (strictly NO data leakage).
- Evaluates the calibrated model on all held-out test sweeps.
"""

import pathlib
import numpy as np
import pandas as pd

# Repository paths
REPO_ROOT = pathlib.Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "results" / "phase5"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def fhn_euler_simulate(
    i_stim_array: np.ndarray,
    dt_ms: float = 0.05,
    tau_ms: float = 2.0,
    a: float = 0.7,
    b: float = 0.8,
    eps: float = 0.08,
    v_init: float = -1.199,
    w_init: float = -0.624,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Standard Forward Euler Numerical Solver for the 2-variable FHN model.
    
    Parameters:
    -----------
    i_stim_array : 1D numpy array of injected stimulus current over time
    dt_ms        : simulation time step in milliseconds (e.g. 0.05 ms)
    tau_ms       : characteristic time scale factor (ms per dimensionless time unit)
    a, b, eps    : standard FHN dimensionless parameters
    v_init, w_init: initial conditions at rest
    
    Returns:
    --------
    time_ms : numpy array of simulation time points in ms
    v_array : numpy array of membrane variable v(t)
    w_array : numpy array of recovery variable w(t)
    """
    num_steps = len(i_stim_array)
    time_ms = np.arange(num_steps) * dt_ms
    
    # Pre-allocate arrays for speed and simplicity
    v_array = np.zeros(num_steps)
    w_array = np.zeros(num_steps)
    
    # Set initial state
    v = v_init
    w = w_init
    
    # Scale dt by tau to convert millisecond time step into dimensionless time
    dt_dim = dt_ms / tau_ms
    
    # Forward Euler loop: simple and easy to understand
    for step in range(num_steps):
        v_array[step] = v
        w_array[step] = w
        
        # Calculate derivatives
        dv = (v - (v**3) / 3.0 - w + i_stim_array[step]) * dt_dim
        dw = eps * (v + a - b * w) * dt_dim
        
        # Update state variables
        v = v + dv
        w = w + dw
        
    return time_ms, v_array, w_array


def count_fhn_spikes(v_array: np.ndarray, threshold: float = 0.0) -> int:
    """
    Counts spikes in the dimensionless FHN voltage trace using upward threshold crossing.
    """
    spike_count = 0
    in_spike = False
    
    for val in v_array:
        if val >= threshold and not in_spike:
            spike_count += 1
            in_spike = True
        elif val < (threshold - 0.2):
            in_spike = False
            
    return spike_count


def calibrate_fhn_for_specimen(
    target_current_pa: float,
    target_spike_count: int,
    step_duration_ms: float = 1000.0,
    dt_ms: float = 0.05,
) -> dict:
    """
    Fits basic parameters (gamma gain factor, tau time constant, eps recovery rate)
    using ONLY the single designated calibration sweep for a cell.
    
    We fix standard biological FHN parameters a=0.7, b=0.8, and search over
    a discrete grid of (gamma, tau, eps) to match the exact spike count
    observed during the calibration sweep.
    """
    a = 0.7
    b = 0.8
    num_step_samples = int(step_duration_ms / dt_ms)
    
    best_params = None
    best_error = 999999
    
    # Candidate grids
    gamma_candidates = [0.001, 0.0015, 0.002, 0.0025, 0.003, 0.0035, 0.004, 0.0045, 0.005]
    eps_candidates = [0.05, 0.08, 0.10]
    tau_candidates = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    
    for gamma in gamma_candidates:
        i_dim_step = gamma * target_current_pa
        stim = np.full(num_step_samples, i_dim_step)
        
        for eps in eps_candidates:
            for tau in tau_candidates:
                _, v_sim, _ = fhn_euler_simulate(
                    stim, dt_ms=dt_ms, tau_ms=tau, a=a, b=b, eps=eps
                )
                spk = count_fhn_spikes(v_sim, threshold=0.0)
                error = abs(spk - target_spike_count)
                
                if error < best_error:
                    best_error = error
                    best_params = {
                        "a": a,
                        "b": b,
                        "eps": eps,
                        "gamma": gamma,
                        "tau_ms": tau,
                        "cal_spikes_simulated": spk,
                        "cal_spikes_target": target_spike_count,
                        "error": error,
                    }
                if best_error == 0:
                    break
            if best_error == 0:
                break
        if best_error == 0:
            break
            
    return best_params


def evaluate_fhn_on_dataset(
    df_sweeps: pd.DataFrame,
    params: dict,
    v_rest_mv: float,
    v_scale_mv: float = 30.0,
    dt_ms: float = 0.05,
) -> pd.DataFrame:
    """
    Evaluates the calibrated FHN model on all sweeps (both calibration and held-out test).
    Simulates a 1000 ms stimulus step for each sweep current, detects spikes,
    and maps dimensionless v to approximate membrane potential in mV.
    """
    results = []
    num_step_samples = int(1000.0 / dt_ms)  # 1.0 s step
    
    for _, row in df_sweeps.iterrows():
        i_pa = float(row["stimulus_current_pa"])
        rec_spikes = int(row["spike_count"])
        split = str(row["split_type"])
        sweep_num = int(row["sweep_number"])
        
        # Stimulus current scaling: only depolarizing current drives spikes
        i_dim = params["gamma"] * max(0.0, i_pa)
        stim = np.full(num_step_samples, i_dim)
        
        _, v_sim, _ = fhn_euler_simulate(
            stim,
            dt_ms=dt_ms,
            tau_ms=params["tau_ms"],
            a=params["a"],
            b=params["b"],
            eps=params["eps"],
        )
        
        fhn_spikes = count_fhn_spikes(v_sim, threshold=0.0)
        fhn_firing_rate_hz = float(fhn_spikes) / 1.0
        spike_count_error = abs(fhn_spikes - rec_spikes)
        
        # Simple voltage conversion: V(mV) = V_rest + V_scale * (v - v_rest_dim)
        # v_rest_dim is approximately -1.2
        v_sim_mv = v_rest_mv + v_scale_mv * (v_sim - (-1.2))
        mean_v_sim_mv = float(np.mean(v_sim_mv))
        
        results.append({
            "layer": row["layer"],
            "population": row["population"],
            "specimen_id": row["specimen_id"],
            "sweep_number": sweep_num,
            "split_type": split,
            "stimulus_current_pa": i_pa,
            "recorded_spikes": rec_spikes,
            "fhn_simulated_spikes": fhn_spikes,
            "spike_count_error": spike_count_error,
            "recorded_firing_rate_hz": row["firing_rate_hz"],
            "fhn_firing_rate_hz": fhn_firing_rate_hz,
            "mean_simulated_voltage_mv": round(mean_v_sim_mv, 2),
        })
        
    return pd.DataFrame(results)


def main():
    print("=" * 60)
    print("INCM Task 2: FitzHugh-Nagumo Model Calibration & Simulation")
    print("=" * 60)

    # 1. Load extracted sweeps from Task 1
    l23_sweeps_path = RESULTS_DIR / "l23_extracted_sweeps.csv"
    l5_sweeps_path = RESULTS_DIR / "l5_extracted_sweeps.csv"

    if not l23_sweeps_path.exists() or not l5_sweeps_path.exists():
        raise FileNotFoundError("Extracted sweep files missing! Please run data_loader.py first.")

    df_l23 = pd.read_csv(l23_sweeps_path)
    df_l5 = pd.read_csv(l5_sweeps_path)

    # 2. Extract Calibration Targets (Sweep 40 for L2/3, Sweep 51 for L5)
    cal_row_l23 = df_l23[df_l23["split_type"] == "CALIBRATION"].iloc[0]
    cal_row_l5 = df_l5[df_l5["split_type"] == "CALIBRATION"].iloc[0]

    print("\n--- Fitting Layer 2/3 (Specimen 318808427, Calibration Sweep 40) ---")
    print(f"Target: +{cal_row_l23['stimulus_current_pa']} pA -> {int(cal_row_l23['spike_count'])} spikes")
    params_l23 = calibrate_fhn_for_specimen(
        target_current_pa=float(cal_row_l23["stimulus_current_pa"]),
        target_spike_count=int(cal_row_l23["spike_count"]),
    )
    print(f"Fitted Parameters L2/3: gamma={params_l23['gamma']}, tau={params_l23['tau_ms']} ms, eps={params_l23['eps']}")
    print(f"Calibration Check: Simulated {params_l23['cal_spikes_simulated']} spikes (Target: {params_l23['cal_spikes_target']})")

    print("\n--- Fitting Layer 5 (Specimen 471129934, Calibration Sweep 51) ---")
    print(f"Target: +{cal_row_l5['stimulus_current_pa']} pA -> {int(cal_row_l5['spike_count'])} spikes")
    params_l5 = calibrate_fhn_for_specimen(
        target_current_pa=float(cal_row_l5["stimulus_current_pa"]),
        target_spike_count=int(cal_row_l5["spike_count"]),
    )
    print(f"Fitted Parameters L5: gamma={params_l5['gamma']}, tau={params_l5['tau_ms']} ms, eps={params_l5['eps']}")
    print(f"Calibration Check: Simulated {params_l5['cal_spikes_simulated']} spikes (Target: {params_l5['cal_spikes_target']})")

    # 3. Save Fitted Parameters to CSV
    param_records = [
        {
            "layer": "L2/3",
            "population": "B",
            "specimen_id": 318808427,
            "calibration_sweep": 40,
            "target_current_pa": 190.0,
            "a": params_l23["a"],
            "b": params_l23["b"],
            "eps": params_l23["eps"],
            "gamma_gain": params_l23["gamma"],
            "tau_ms": params_l23["tau_ms"],
            "target_spikes": params_l23["cal_spikes_target"],
            "fitted_spikes": params_l23["cal_spikes_simulated"],
        },
        {
            "layer": "L5",
            "population": "C",
            "specimen_id": 471129934,
            "calibration_sweep": 51,
            "target_current_pa": 410.0,
            "a": params_l5["a"],
            "b": params_l5["b"],
            "eps": params_l5["eps"],
            "gamma_gain": params_l5["gamma"],
            "tau_ms": params_l5["tau_ms"],
            "target_spikes": params_l5["cal_spikes_target"],
            "fitted_spikes": params_l5["cal_spikes_simulated"],
        },
    ]
    df_params = pd.DataFrame(param_records)
    params_csv = RESULTS_DIR / "fhn_fitted_parameters_student.csv"
    df_params.to_csv(params_csv, index=False)
    print(f"\nSaved fitted parameter summary to: {params_csv.name}")

    # 4. Evaluate fitted FHN model on all held-out sweeps
    print("\n--- Evaluating Calibrated FHN on Held-Out Sweeps ---")
    sim_results_l23 = evaluate_fhn_on_dataset(
        df_l23, params_l23, v_rest_mv=float(cal_row_l23["baseline_voltage_mv"])
    )
    sim_results_l5 = evaluate_fhn_on_dataset(
        df_l5, params_l5, v_rest_mv=float(cal_row_l5["baseline_voltage_mv"])
    )

    out_l23_csv = RESULTS_DIR / "l23_fhn_simulation_results.csv"
    out_l5_csv = RESULTS_DIR / "l5_fhn_simulation_results.csv"
    sim_results_l23.to_csv(out_l23_csv, index=False)
    sim_results_l5.to_csv(out_l5_csv, index=False)

    print(f"Saved {len(sim_results_l23)} evaluation records for L2/3 to: {out_l23_csv.name}")
    print(f"Saved {len(sim_results_l5)} evaluation records for L5 to: {out_l5_csv.name}")
    print("\nFHN model calibration and simulation completed successfully!")


if __name__ == "__main__":
    main()

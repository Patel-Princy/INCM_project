"""
data_loader.py
==============
Author: Princy (INCM Course Project)
Branch: Princy-work

Purpose:
--------
This script loads electrophysiology data from the Allen Cell Types Database
for two specific mouse visual cortex (VISp) pyramidal neurons:
1. Layer 2/3 (Specimen ID: 318808427, Calibration Sweep: 40 at +190 pA)
2. Layer 5   (Specimen ID: 471129934, Calibration Sweep: 51 at +410 pA)

What this script does (step-by-step for a first-year CS student):
1. Loads the current-clamp recording (.nwb) file for each specimen.
2. Extracts the voltage trace (mV), stimulus current (pA), and time array (ms).
3. Strictly isolates calibration sweeps from held-out test sweeps (NO data leakage).
4. Detects action potentials (spikes) using simple 0 mV threshold crossing.
5. Computes basic summary metrics: spike count, firing rate (Hz), and baseline voltage.
6. Saves the extracted sweep summaries to simple CSV files in results/phase5/.
"""

import os
import pathlib
import urllib.request
import numpy as np
import pandas as pd
import h5py

# Define repository directories
REPO_ROOT = pathlib.Path(__file__).resolve().parent
NWB_CACHE_DIR = REPO_ROOT / "data" / "nwb_cache"
OUTPUT_DIR = REPO_ROOT / "results" / "phase5"
HELDOUT_MANIFEST_PATH = REPO_ROOT / "results" / "phase3b" / "heldout_sweeps.csv"

# Web URLs for the raw NWB recordings on the Allen Brain Map API
NWB_DOWNLOAD_URLS = {
    318808427: "http://api.brain-map.org/api/v2/well_known_file_download/491199000",
    471129934: "http://api.brain-map.org/api/v2/well_known_file_download/491202812",
}

# Target specimen assignments
SPECIMEN_ASSIGNMENTS = {
    "L2/3": {
        "specimen_id": 318808427,
        "population": "B",
        "calibration_sweep": 40,
        "target_current_pa": 190.0,
    },
    "L5": {
        "specimen_id": 471129934,
        "population": "C",
        "calibration_sweep": 51,
        "target_current_pa": 410.0,
    },
}


def ensure_nwb_file(specimen_id: int) -> pathlib.Path:
    """
    Checks if the .nwb file exists locally in data/nwb_cache.
    If it is missing, downloads it automatically from the Allen Brain Map.
    """
    NWB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = NWB_CACHE_DIR / f"{specimen_id}.nwb"

    if not file_path.exists():
        print(f"Downloading NWB file for Specimen {specimen_id}...")
        url = NWB_DOWNLOAD_URLS[specimen_id]
        urllib.request.urlretrieve(url, file_path)
        print(f"Downloaded to {file_path}")
    else:
        print(f"Found cached NWB file for Specimen {specimen_id} ({file_path.name})")

    return file_path


def load_sweep_from_nwb(nwb_path: pathlib.Path, sweep_number: int) -> dict:
    """
    Reads a single sweep from an Allen NWB file using h5py.
    This reads the exact same HDF5 data structures that AllenSDK's NwbDataSet reads:
    - Membrane potential: converted from Volts to Millivolts (x 1,000)
    - Injected current: converted from Amperes to Picoamperes (x 1,000,000,000,000)
    - Time: calculated using sampling rate in ms
    """
    with h5py.File(nwb_path, "r") as nwb:
        # Acquisition contains recorded somatic voltage
        sweep_rec_key = f"Sweep_{sweep_number}"
        swp_rec = nwb["acquisition"]["timeseries"][sweep_rec_key]
        v_raw = swp_rec["data"][:] * 1000.0  # Convert V to mV
        
        # Sampling rate in Hz
        rate = float(swp_rec["starting_time"].attrs["rate"])
        num_samples = len(v_raw)
        
        # Time array in milliseconds
        t_arr = (np.arange(num_samples) / rate) * 1000.0

        # Stimulus presentation contains injected current
        swp_stim = nwb["stimulus"]["presentation"][sweep_rec_key]
        i_data = swp_stim["data"][:]
        
        # Note on Allen NWB units: samples are stored in Amperes (e.g. 1.9e-10 A)
        # Convert A to pA (1 A = 1e12 pA)
        i_raw = i_data * 1e12

        # Extract stimulus amplitude from attributes if available
        if "aibs_stimulus_amplitude_pa" in swp_rec:
            stim_amp_pa = float(swp_rec["aibs_stimulus_amplitude_pa"][()])
        else:
            stim_amp_pa = float(np.max(np.abs(i_raw)))

    return {
        "sweep_number": sweep_number,
        "time_ms": t_arr,
        "voltage_mv": v_raw,
        "current_pa": i_raw,
        "sampling_rate_hz": rate,
        "stimulus_amplitude_pa": stim_amp_pa,
    }


def detect_spikes_simple(v_trace: np.ndarray, t_trace: np.ndarray, threshold_mv: float = 0.0, lockout_ms: float = 2.0) -> list:
    """
    Simple first-year level spike detector:
    1. Looks for upward crossings of threshold_mv (default 0.0 mV).
    2. Imposes a 2.0 ms refractory lockout so one spike isn't counted twice.
    Returns a list of spike times (in ms).
    """
    spike_times = []
    last_spike_t = -9999.0  # Initialize far in the past

    num_points = len(v_trace)
    for i in range(num_points - 1):
        # Did the voltage cross from below threshold to above threshold?
        if v_trace[i] < threshold_mv and v_trace[i + 1] >= threshold_mv:
            current_t = t_trace[i]
            # Enforce refractory period
            if (current_t - last_spike_t) >= lockout_ms:
                spike_times.append(float(current_t))
                last_spike_t = current_t

    return spike_times


def get_heldout_sweeps_for_specimen(specimen_id: int) -> list:
    """
    Loads heldout_sweeps.csv from Phase 3B to find all pre-designated held-out test sweeps.
    This guarantees NO data leakage because the calibration sweep is strictly excluded.
    """
    if not HELDOUT_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {HELDOUT_MANIFEST_PATH}")
    
    df_manifest = pd.read_csv(HELDOUT_MANIFEST_PATH)
    specimen_rows = df_manifest[df_manifest["specimen_id"] == specimen_id]
    heldout_sweeps = specimen_rows["sweep_number"].tolist()
    return heldout_sweeps


def process_specimen(layer_name: str, config: dict) -> pd.DataFrame:
    """
    Extracts all calibration and held-out sweeps for a given specimen,
    computes spike metrics, and returns a summary DataFrame.
    """
    specimen_id = config["specimen_id"]
    pop = config["population"]
    cal_sweep = config["calibration_sweep"]
    
    # 1. Ensure NWB file is cached locally
    nwb_path = ensure_nwb_file(specimen_id)

    # 2. Get list of held-out sweeps
    heldout_sweeps = get_heldout_sweeps_for_specimen(specimen_id)
    print(f"\nProcessing {layer_name} (Specimen {specimen_id}, Pop {pop}):")
    print(f" - Calibration Sweep: {cal_sweep} (Target ~{config['target_current_pa']} pA)")
    print(f" - Number of Held-Out Sweeps: {len(heldout_sweeps)}")
    
    # Safety Check: Calibration sweep MUST NOT be in heldout sweeps
    if cal_sweep in heldout_sweeps:
        raise ValueError(f"DATA LEAKAGE DETECTED! Calibration sweep {cal_sweep} is in held-out list!")
    print(" - Data Leakage Check: PASSED (Calibration sweep strictly isolated).")

    # Combine sweeps for batch processing (marking each as CALIBRATION or TEST)
    all_sweeps = [(cal_sweep, "CALIBRATION")] + [(swp, "HELD_OUT_TEST") for swp in heldout_sweeps]

    summary_records = []

    for sweep_num, split_type in all_sweeps:
        sweep_data = load_sweep_from_nwb(nwb_path, sweep_num)
        t = sweep_data["time_ms"]
        v = sweep_data["voltage_mv"]
        i_inj = sweep_data["current_pa"]

        # Baseline resting potential: average over quiet pre-stimulus period (200 ms to 1000 ms)
        baseline_mask = (t >= 200.0) & (t < 1000.0)
        v_baseline = float(np.mean(v[baseline_mask])) if np.any(baseline_mask) else float(v[0])

        # Stimulus step window: 1020 ms to 2020 ms (1.0 s step duration)
        stim_mask = (t >= 1020.0) & (t <= 2020.0)
        mean_stim_pa = float(np.mean(i_inj[stim_mask])) if np.any(stim_mask) else 0.0

        # Detect spikes
        all_spikes = detect_spikes_simple(v, t, threshold_mv=0.0)
        # Filter spikes occurring during the stimulus step (1020 ms to 2020 ms)
        step_spikes = [spk for spk in all_spikes if (1020.0 <= spk <= 2020.0)]
        spike_count = len(step_spikes)
        firing_rate_hz = float(spike_count) / 1.0  # Since step is exactly 1 second

        # First spike latency (ms) from stimulus onset (1020 ms)
        if spike_count > 0:
            first_spike_latency_ms = float(step_spikes[0] - 1020.0)
        else:
            first_spike_latency_ms = None

        record = {
            "layer": layer_name,
            "population": pop,
            "specimen_id": specimen_id,
            "sweep_number": sweep_num,
            "split_type": split_type,
            "stimulus_current_pa": round(mean_stim_pa, 1),
            "baseline_voltage_mv": round(v_baseline, 2),
            "spike_count": spike_count,
            "firing_rate_hz": firing_rate_hz,
            "first_spike_latency_ms": round(first_spike_latency_ms, 2) if first_spike_latency_ms is not None else None,
        }
        summary_records.append(record)

    df_summary = pd.DataFrame(summary_records)
    return df_summary


def main():
    """Main execution function."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("INCM Task 1: Data Extraction & Preprocessing (L2/3 & L5)")
    print("=" * 60)

    for layer_name, config in SPECIMEN_ASSIGNMENTS.items():
        df = process_specimen(layer_name, config)
        
        # Save to CSV
        layer_file_tag = "l23" if layer_name == "L2/3" else "l5"
        output_csv = OUTPUT_DIR / f"{layer_file_tag}_extracted_sweeps.csv"
        df.to_csv(output_csv, index=False)
        print(f"Saved {len(df)} sweep records for {layer_name} to: {output_csv.name}")

    print("\nData extraction and preprocessing completed successfully!")


if __name__ == "__main__":
    main()


#!/usr/bin/env python
"""Execute and validate a representative perisomatic biophysical model against an experimental sweep.

Supports the four layer-defined VISp excitatory representatives:
- Population A (VISp L4):  specimen 484564503, model 485591776, calibration sweep 49
- Population B (VISp L2/3): specimen 318808427, model 473863035, calibration sweep 40
- Population C (VISp L5):   specimen 471129934, model 480624414, calibration sweep 51
- Population D (VISp L6a):  specimen 471786879, model 480632594, calibration sweep 42

Reuses AllenSDK v2.16.2 runner and NEURON 8.2.7 biophysical simulation engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

REPRESENTATIVES = {
    484564503: {
        "population": "A",
        "layer": "4",
        "structure": "VISp4",
        "model_id": 485591776,
        "fit_file_id": 497237137,
        "nwb_file_id": 491317441,
        "reconstruction_id": 491459182,
        "swc_name": "484564503.swc",
        "calibration_sweep": 49,
        "calibration_amplitude_pa": 370.0,
    },
    318808427: {
        "population": "B",
        "layer": "2/3",
        "structure": "VISp2/3",
        "model_id": 473863035,
        "fit_file_id": 497237588,
        "nwb_file_id": 491199000,
        "reconstruction_id": 491119754,
        "swc_name": "318808427.swc",
        "calibration_sweep": 40,
        "calibration_amplitude_pa": 190.0,
    },
    471129934: {
        "population": "C",
        "layer": "5",
        "structure": "VISp5",
        "model_id": 480624414,
        "fit_file_id": 497236153,
        "nwb_file_id": 491202812,
        "reconstruction_id": 495335491,
        "swc_name": "471129934.swc",
        "calibration_sweep": 51,
        "calibration_amplitude_pa": 410.0,
    },
    471786879: {
        "population": "D",
        "layer": "6a",
        "structure": "VISp6a",
        "model_id": 480632594,
        "fit_file_id": 497236229,
        "nwb_file_id": 491202180,
        "reconstruction_id": 495335607,
        "swc_name": "471786879.swc",
        "calibration_sweep": 42,
        "calibration_amplitude_pa": 250.0,
    },
}

MECHANISMS = (
    "CaDynamics", "Ca_HVA", "Ca_LVA", "Ih", "Im", "Im_v2",
    "K_P", "K_T", "Kd", "Kv2like", "Kv3_1", "NaTa", "NaTs", "NaV", "Nap", "SK",
)

PERISOMATIC_TYPE = "Biophysical - perisomatic"


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _stimulus_segments(stimulus: np.ndarray, dt_ms: float) -> list[dict]:
    nonzero = np.flatnonzero(np.abs(stimulus) > 1e-12)
    if not nonzero.size:
        return []
    splits = np.flatnonzero(np.diff(nonzero) > 1)
    starts = np.concatenate(([nonzero[0]], nonzero[splits + 1]))
    ends = np.concatenate((nonzero[splits], [nonzero[-1]]))
    segments = []
    for start, end in zip(starts, ends):
        span = stimulus[start:end + 1]
        segments.append({
            "start_index": int(start),
            "end_index": int(end),
            "onset_ms": float(start) * dt_ms,
            "duration_ms": float(end - start + 1) * dt_ms,
            "amplitude_pa": float(np.median(span)) * 1e12,
        })
    return segments


def _detect_spikes_threshold(v_v: np.ndarray, t_ms: np.ndarray, threshold_mv: float = 0.0, refractory_ms: float = 1.0) -> np.ndarray:
    v_mv = v_v * 1e3
    above = v_mv >= threshold_mv
    times = []
    last_t = -1e9
    for idx in range(1, above.size):
        if above[idx] and not above[idx - 1] and (t_ms[idx] - last_t) > refractory_ms:
            times.append(float(t_ms[idx]))
            last_t = t_ms[idx]
    return np.array(times, dtype=float)


def stage_model(workspace: pathlib.Path, repo_dir: pathlib.Path, specimen_id: int, sweeps: list[int]) -> dict:
    meta = REPRESENTATIVES[specimen_id]
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "work").mkdir(parents=True, exist_ok=True)

    # 1. Stimulus NWB
    src_nwb = repo_dir / "data" / "nwb_cache" / f"{specimen_id}.nwb"
    if not src_nwb.exists():
        raise FileNotFoundError(f"Source NWB file not found: {src_nwb}")
    dst_nwb = workspace / f"{specimen_id}.nwb"
    if not dst_nwb.exists():
        if hasattr(os, "symlink"):
            try:
                os.symlink(src_nwb.resolve(), dst_nwb)
            except Exception:
                shutil.copy2(src_nwb, dst_nwb)
        else:
            shutil.copy2(src_nwb, dst_nwb)

    # 2. Fit descriptor
    src_fit = repo_dir / "tmp" / "fit_cache" / f"{meta['fit_file_id']}.json"
    if not src_fit.exists():
        raise FileNotFoundError(f"Source fit descriptor not found: {src_fit}")
    dst_fit = workspace / f"{specimen_id}_fit.json"
    shutil.copy2(src_fit, dst_fit)

    # 3. Morphology SWC
    src_swc = repo_dir / "tmp" / "morphology_cache" / meta["swc_name"]
    if not src_swc.exists():
        raise FileNotFoundError(f"Source SWC morphology not found: {src_swc}")
    dst_swc = workspace / meta["swc_name"]
    shutil.copy2(src_swc, dst_swc)

    # 4. Modfiles
    src_mods = repo_dir / "tmp" / "model_cache" / "manifest_drafts" / "perisomatic" / "modfiles"
    dst_mods = workspace / "modfiles"
    if not dst_mods.exists():
        shutil.copytree(src_mods, dst_mods)

    # 5. Manifest.json
    manifest_data = {
        "biophys": [
            {
                "model_file": ["manifest.json", f"{specimen_id}_fit.json"],
                "model_type": PERISOMATIC_TYPE,
            }
        ],
        "runs": [
            {
                "sweeps": sweeps,
                "sweeps_by_type": {
                    "Long Square": sweeps
                }
            }
        ],
        "neuron": [
            {
                "hoc": ["stdgui.hoc", "import3d.hoc"]
            }
        ],
        "manifest": [
            {"type": "dir", "spec": ".", "key": "BASEDIR"},
            {"type": "dir", "spec": "work", "key": "WORKDIR", "parent": "BASEDIR"},
            {"type": "file", "spec": meta["swc_name"], "key": "MORPHOLOGY"},
            {"type": "dir", "spec": "modfiles", "key": "MODFILE_DIR"},
            {"type": "file", "format": "NWB", "spec": f"{specimen_id}.nwb", "key": "stimulus_path"},
            {"parent_key": "WORKDIR", "type": "file", "format": "NWB", "spec": f"{specimen_id}.nwb", "key": "output_path"},
        ]
    }
    manifest_path = workspace / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return {
        "nwb_sha256": sha256_of(src_nwb),
        "fit_sha256": sha256_of(src_fit),
        "swc_sha256": sha256_of(src_swc),
        "manifest_sha256": sha256_of(manifest_path),
    }


def compile_mechanisms_if_needed(workspace: pathlib.Path) -> bool:
    lib = workspace / "x86_64" / "libnrnmech.so"
    if lib.exists():
        return True
    nrnivmodl = shutil.which("nrnivmodl")
    if not nrnivmodl:
        py_bin = pathlib.Path(sys.executable)
        candidate = py_bin.with_name("nrnivmodl")
        if candidate.exists():
            nrnivmodl = str(candidate)
        else:
            print("ERROR: nrnivmodl not found", file=sys.stderr)
            return False
    cmd = [nrnivmodl, "modfiles/"]
    res = subprocess.run(cmd, cwd=str(workspace), capture_output=True, text=True)
    if res.returncode != 0:
        print("nrnivmodl failed:\n", res.stderr, file=sys.stderr)
        return False
    return lib.exists()


def run_simulation(workspace: pathlib.Path, allensdk_src: pathlib.Path, sweep: int) -> dict:
    original_cwd = os.getcwd()
    os.chdir(workspace)
    try:
        sys.path.insert(0, str(allensdk_src))
        import neuron
        from allensdk.model.biophysical import runner
        from allensdk.model.biophysical import utils as biophys_utils

        # Instrument get_recorded_data to capture raw simulation vector
        captured = {}
        original_get_data = biophys_utils.Utils.get_recorded_data

        def instrumented(self, vec):
            raw_v = np.array(vec["v"], dtype=float)
            raw_t = np.array(vec["t"], dtype=float)
            result = original_get_data(self, vec)
            captured["raw_v_mv"] = raw_v
            captured["raw_t_ms"] = raw_t
            captured["out_v"] = np.array(result["v"], dtype=float)
            captured["out_t"] = np.array(result["t"], dtype=float)
            return result

        biophys_utils.Utils.get_recorded_data = instrumented
        args = {"manifest_file": "manifest.json", "axon_type": "truncated"}
        t0 = time.time()
        runner.run(args, sweeps=[sweep], procs=1)
        elapsed = time.time() - t0
        biophys_utils.Utils.get_recorded_data = original_get_data

        return {
            "elapsed_s": elapsed,
            "neuron_version": neuron.__version__,
            "captured": captured,
        }
    finally:
        os.chdir(original_cwd)


def analyze_and_compare(specimen_id: int, sweep: int, workspace: pathlib.Path, allensdk_src: pathlib.Path, captured: dict) -> dict:
    sys.path.insert(0, str(allensdk_src))
    from allensdk.core.nwb_data_set import NwbDataSet
    from allensdk.ephys import ephys_features

    recorded_path = workspace / f"{specimen_id}.nwb"
    ds_rec = NwbDataSet(str(recorded_path))
    swp_rec = ds_rec.get_sweep(sweep)
    v_rec_v = np.asarray(swp_rec["response"], dtype=float)
    stim_rec_a = np.asarray(swp_rec["stimulus"], dtype=float)
    rate = float(swp_rec["sampling_rate"])
    dt_ms = 1000.0 / rate

    v_sim_v = captured["out_v"]
    t_ms = captured["out_t"]

    n = min(len(v_rec_v), len(v_sim_v))
    v_rec_v = v_rec_v[:n]
    v_sim_v = v_sim_v[:n]
    stim_rec_a = stim_rec_a[:n]
    t_ms = t_ms[:n]

    v_rec_mv = v_rec_v * 1e3
    v_sim_mv = v_sim_v * 1e3
    stim_pa = stim_rec_a * 1e12

    # Stimulus segmentation: filter for steps with duration > 100 ms to avoid locking onto test pulse
    segments = _stimulus_segments(stim_rec_a, dt_ms)
    long_segments = [s for s in segments if s["duration_ms"] > 100.0]
    step = long_segments[0] if long_segments else (segments[0] if segments else None)
    
    step_on_ms = step["onset_ms"] if step else 1020.0
    step_dur_ms = step["duration_ms"] if step else 1000.0
    step_off_ms = step_on_ms + step_dur_ms
    step_on_idx = step["start_index"] if step else int(step_on_ms / dt_ms)
    step_off_idx = step["end_index"] if step else int(step_off_ms / dt_ms)

    # Baseline (quiet interval before step, ignoring test pulse)
    quiet_idx = np.abs(stim_rec_a[:step_on_idx]) <= 1e-12
    if quiet_idx.any():
        baseline_rec_mv = float(np.mean(v_rec_mv[:step_on_idx][quiet_idx]))
        baseline_sim_mv = float(np.mean(v_sim_mv[:step_on_idx][quiet_idx]))
    else:
        baseline_rec_mv = float(np.mean(v_rec_mv[:step_on_idx]))
        baseline_sim_mv = float(np.mean(v_sim_mv[:step_on_idx]))

    # Mean step voltage and max depolarization
    mean_step_v_rec = float(np.mean(v_rec_mv[step_on_idx:step_off_idx]))
    mean_step_v_sim = float(np.mean(v_sim_mv[step_on_idx:step_off_idx]))
    max_depol_rec = float(np.max(v_rec_mv[step_on_idx:step_off_idx]))
    max_depol_sim = float(np.max(v_sim_mv[step_on_idx:step_off_idx]))

    # RMSE calculations
    diff_mv = v_sim_mv - v_rec_mv
    rmse_overall = float(np.sqrt(np.mean(diff_mv ** 2)))
    rmse_pre = float(np.sqrt(np.mean(diff_mv[:max(1, step_on_idx)] ** 2)))
    rmse_step = float(np.sqrt(np.mean(diff_mv[step_on_idx:step_off_idx] ** 2)))
    rmse_post = float(np.sqrt(np.mean(diff_mv[step_off_idx:] ** 2)))
    mae_mv = float(np.mean(np.abs(diff_mv)))
    
    # Correlation (handle flat traces gracefully)
    std_rec = np.std(v_rec_mv)
    std_sim = np.std(v_sim_mv)
    if std_rec > 1e-6 and std_sim > 1e-6:
        corr = float(np.corrcoef(v_sim_mv, v_rec_mv)[0, 1])
    else:
        corr = 1.0 if abs(np.mean(v_sim_mv) - np.mean(v_rec_mv)) < 1.0 else 0.0

    # Spike detection using AllenSDK ephys_features
    try:
        spikes_rec_idx = np.asarray(ephys_features.detect_putative_spikes(v_rec_mv, t_ms * 1e-3))
        spikes_rec_ms = t_ms[spikes_rec_idx[(spikes_rec_idx >= 0) & (spikes_rec_idx < n)]]
    except Exception:
        spikes_rec_ms = _detect_spikes_threshold(v_rec_v, t_ms, threshold_mv=0.0)

    try:
        spikes_sim_idx = np.asarray(ephys_features.detect_putative_spikes(v_sim_mv, t_ms * 1e-3))
        spikes_sim_ms = t_ms[spikes_sim_idx[(spikes_sim_idx >= 0) & (spikes_sim_idx < n)]]
    except Exception:
        spikes_sim_ms = _detect_spikes_threshold(v_sim_v, t_ms, threshold_mv=0.0)

    # In-step vs post-step spikes
    rec_in_step = spikes_rec_ms[(spikes_rec_ms >= step_on_ms) & (spikes_rec_ms <= step_off_ms)]
    sim_in_step = spikes_sim_ms[(spikes_sim_ms >= step_on_ms) & (spikes_sim_ms <= step_off_ms)]
    rec_post_step = spikes_rec_ms[spikes_rec_ms > step_off_ms]
    sim_post_step = spikes_sim_ms[spikes_sim_ms > step_off_ms]

    first_spike_rec_ms = float(rec_in_step[0]) if rec_in_step.size else None
    first_spike_sim_ms = float(sim_in_step[0]) if sim_in_step.size else None
    first_spike_delta_ms = (first_spike_sim_ms - first_spike_rec_ms) if (first_spike_rec_ms and first_spike_sim_ms) else None

    # Inter-spike intervals (ISI) in step
    isi_rec = np.diff(rec_in_step) if len(rec_in_step) > 1 else np.array([])
    isi_sim = np.diff(sim_in_step) if len(sim_in_step) > 1 else np.array([])
    mean_isi_rec = float(np.mean(isi_rec)) if len(isi_rec) else None
    mean_isi_sim = float(np.mean(isi_sim)) if len(isi_sim) else None

    # Excursions post-step above -20 mV
    post_rec_mv = v_rec_mv[step_off_idx:]
    post_sim_mv = v_sim_mv[step_off_idx:]
    excursions_rec = int(np.count_nonzero(np.diff((post_rec_mv >= -20.0).astype(int)) == 1))
    excursions_sim = int(np.count_nonzero(np.diff((post_sim_mv >= -20.0).astype(int)) == 1))

    return {
        "n_samples": n,
        "dt_ms": dt_ms,
        "sampling_rate_hz": rate,
        "step_amplitude_pa": step["amplitude_pa"] if step else float("nan"),
        "step_onset_ms": step_on_ms,
        "step_duration_ms": step_dur_ms,
        "baseline_recorded_mv": baseline_rec_mv,
        "baseline_simulated_mv": baseline_sim_mv,
        "baseline_delta_mv": baseline_sim_mv - baseline_rec_mv,
        "mean_step_v_rec_mv": mean_step_v_rec,
        "mean_step_v_sim_mv": mean_step_v_sim,
        "max_depol_rec_mv": max_depol_rec,
        "max_depol_sim_mv": max_depol_sim,
        "rmse_overall_mv": rmse_overall,
        "rmse_pre_stimulus_mv": rmse_pre,
        "rmse_during_stimulus_mv": rmse_step,
        "rmse_post_stimulus_mv": rmse_post,
        "mae_mv": mae_mv,
        "correlation": corr,
        "spike_count_recorded_total": len(spikes_rec_ms),
        "spike_count_simulated_total": len(spikes_sim_ms),
        "spike_count_recorded_in_step": len(rec_in_step),
        "spike_count_simulated_in_step": len(sim_in_step),
        "spike_count_recorded_post_step": len(rec_post_step),
        "spike_count_simulated_post_step": len(sim_post_step),
        "first_spike_recorded_ms": first_spike_rec_ms,
        "first_spike_simulated_ms": first_spike_sim_ms,
        "first_spike_delta_ms": first_spike_delta_ms,
        "mean_isi_rec_ms": mean_isi_rec,
        "mean_isi_sim_ms": mean_isi_sim,
        "post_step_excursions_recorded": excursions_rec,
        "post_step_excursions_simulated": excursions_sim,
        "spike_times_recorded_in_step_ms": [round(float(x), 3) for x in rec_in_step],
        "spike_times_simulated_in_step_ms": [round(float(x), 3) for x in sim_in_step],
        "v_sim_mv": v_sim_mv,
        "v_rec_mv": v_rec_mv,
        "stim_pa": stim_pa,
        "t_ms": t_ms,
    }


def plot_results(metrics: dict, output_dir: pathlib.Path, specimen_id: int, sweep: int, condition_label: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t_ms = metrics["t_ms"]
    v_rec = metrics["v_rec_mv"]
    v_sim = metrics["v_sim_mv"]
    stim = metrics["stim_pa"]
    meta = REPRESENTATIVES[specimen_id]

    fig, (ax_v, ax_i) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})

    # Voltage trace
    ax_v.plot(t_ms, v_rec, color="#2b2b2b", linewidth=0.8, alpha=0.85, label="Recorded (Allen Experiment)")
    ax_v.plot(t_ms, v_sim, color="#c0392b", linewidth=0.8, alpha=0.85, label="Simulated (Perisomatic Model)")
    ax_v.set_ylabel("Membrane Voltage (mV)", fontsize=11)
    title_str = (
        f"Population {meta['population']} (VISp L{meta['layer']}) — Specimen {specimen_id} Sweep {sweep} [{condition_label}]\n"
        f"Spikes: rec={metrics['spike_count_recorded_in_step']}, sim={metrics['spike_count_simulated_in_step']} | "
        f"Step RMSE: {metrics['rmse_during_stimulus_mv']:.2f} mV | Trace r: {metrics['correlation']:.4f}"
    )
    ax_v.set_title(title_str, fontsize=11, fontweight="bold")
    ax_v.grid(True, linestyle=":", alpha=0.5)
    ax_v.legend(loc="upper right", framealpha=0.9)

    # Stimulus current
    ax_i.plot(t_ms, stim, color="#2980b9", linewidth=0.9, label=f"Command Current ({metrics['step_amplitude_pa']:.0f} pA step)")
    ax_i.set_xlabel("Time (ms)", fontsize=11)
    ax_i.set_ylabel("Current (pA)", fontsize=11)
    ax_i.grid(True, linestyle=":", alpha=0.5)
    ax_i.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    plot_path = output_dir / "voltage_comparison.png"
    plt.savefig(plot_path, dpi=200)
    plt.close(fig)

    # Separate stimulus plot
    fig_stim, ax_stim = plt.subplots(figsize=(9, 3))
    ax_stim.plot(t_ms, stim, color="#2980b9", linewidth=1.0)
    ax_stim.set_title(f"Injected Stimulus Current — Specimen {specimen_id} Sweep {sweep}", fontsize=11)
    ax_stim.set_xlabel("Time (ms)", fontsize=10)
    ax_stim.set_ylabel("Current (pA)", fontsize=10)
    ax_stim.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_dir / "stimulus_current.png", dpi=200)
    plt.close(fig_stim)


def run_single_sweep(specimen_id: int, sweep: int, condition_type: str, repo_dir: pathlib.Path,
                     workspace: pathlib.Path, allensdk_src: pathlib.Path, output_dir: pathlib.Path,
                     save_traces: bool = False, logger: logging.Logger = None) -> dict:
    if logger is None:
        logger = logging.getLogger("runner")

    meta = REPRESENTATIVES[specimen_id]
    is_calibration = (sweep == meta["calibration_sweep"])

    # Audit Gate 3: Reject fitting sweep if requested as held-out
    if condition_type == "held_out" and is_calibration:
        raise ValueError(
            f"REJECTED: Sweep {sweep} is the published calibration fitting sweep for specimen {specimen_id}. "
            "It cannot be executed under condition_type='held_out'."
        )

    condition_label = "CALIBRATION" if is_calibration else "HELD_OUT"
    sweep_out_dir = output_dir if sweep == meta["calibration_sweep"] and "sweep_" not in output_dir.name else output_dir / f"sweep_{sweep}"
    sweep_out_dir.mkdir(parents=True, exist_ok=True)

    log_path = sweep_out_dir / "execution.log"
    logger.info("Executing specimen %d, sweep %d (%s)...", specimen_id, sweep, condition_label)
    hashes = stage_model(workspace, repo_dir, specimen_id, [sweep])

    compiled = compile_mechanisms_if_needed(workspace)
    if not compiled:
        raise RuntimeError("Mechanism compilation failed")

    sim_res = run_simulation(workspace, allensdk_src, sweep)
    captured = sim_res["captured"]
    if not captured:
        raise RuntimeError(f"Simulation of sweep {sweep} produced no captured voltage trace")

    analysis = analyze_and_compare(specimen_id, sweep, workspace, allensdk_src, captured)

    # Optional traces save
    if save_traces:
        np.savez_compressed(
            sweep_out_dir / "traces.npz",
            v_sim_v=captured["out_v"],
            v_sim_mv=analysis["v_sim_mv"],
            v_rec_mv=analysis["v_rec_mv"],
            stim_pa=analysis["stim_pa"],
            t_ms=analysis["t_ms"],
        )

    # Plot representative sweeps (calibration sweeps, or first 3 held-out sweeps, or all if requested)
    plot_results(analysis, sweep_out_dir, specimen_id, sweep, condition_label)

    summary_data = {
        "specimen_id": specimen_id,
        "population": meta["population"],
        "layer": meta["layer"],
        "structure": meta["structure"],
        "model_id": meta["model_id"],
        "fit_file_id": meta["fit_file_id"],
        "sweep_id": sweep,
        "condition_type": condition_label,
        "is_calibration": is_calibration,
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hashes": hashes,
        "environment": {
            "neuron_version": sim_res["neuron_version"],
            "python_version": sys.version.split()[0],
            "elapsed_seconds": round(sim_res["elapsed_s"], 2),
        },
        "stimulus": {
            "amplitude_pa": analysis["step_amplitude_pa"],
            "onset_ms": analysis["step_onset_ms"],
            "duration_ms": analysis["step_duration_ms"],
            "sampling_rate_hz": analysis["sampling_rate_hz"],
        },
        "metrics": {
            "baseline_recorded_mv": round(analysis["baseline_recorded_mv"], 3),
            "baseline_simulated_mv": round(analysis["baseline_simulated_mv"], 3),
            "baseline_delta_mv": round(analysis["baseline_delta_mv"], 3),
            "mean_step_v_rec_mv": round(analysis["mean_step_v_rec_mv"], 3),
            "mean_step_v_sim_mv": round(analysis["mean_step_v_sim_mv"], 3),
            "max_depol_rec_mv": round(analysis["max_depol_rec_mv"], 3),
            "max_depol_sim_mv": round(analysis["max_depol_sim_mv"], 3),
            "rmse_overall_mv": round(analysis["rmse_overall_mv"], 3),
            "rmse_pre_stimulus_mv": round(analysis["rmse_pre_stimulus_mv"], 3),
            "rmse_during_stimulus_mv": round(analysis["rmse_during_stimulus_mv"], 3),
            "rmse_post_stimulus_mv": round(analysis["rmse_post_stimulus_mv"], 3),
            "mae_mv": round(analysis["mae_mv"], 3),
            "correlation": round(analysis["correlation"], 4),
            "spike_count_recorded_total": analysis["spike_count_recorded_total"],
            "spike_count_simulated_total": analysis["spike_count_simulated_total"],
            "spike_count_recorded_in_step": analysis["spike_count_recorded_in_step"],
            "spike_count_simulated_in_step": analysis["spike_count_simulated_in_step"],
            "spike_count_delta": analysis["spike_count_simulated_in_step"] - analysis["spike_count_recorded_in_step"],
            "first_spike_recorded_ms": analysis["first_spike_recorded_ms"],
            "first_spike_simulated_ms": analysis["first_spike_simulated_ms"],
            "first_spike_delta_ms": round(analysis["first_spike_delta_ms"], 3) if analysis["first_spike_delta_ms"] is not None else None,
            "mean_isi_rec_ms": round(analysis["mean_isi_rec_ms"], 3) if analysis["mean_isi_rec_ms"] is not None else None,
            "mean_isi_sim_ms": round(analysis["mean_isi_sim_ms"], 3) if analysis["mean_isi_sim_ms"] is not None else None,
            "post_step_excursions_recorded": analysis["post_step_excursions_recorded"],
            "post_step_excursions_simulated": analysis["post_step_excursions_simulated"],
            "spike_times_recorded_in_step_ms": analysis["spike_times_recorded_in_step_ms"],
            "spike_times_simulated_in_step_ms": analysis["spike_times_simulated_in_step_ms"],
        }
    }

    summary_file = sweep_out_dir / "summary.json"
    summary_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    log_path.write_text(f"Execution completed in {sim_res['elapsed_s']:.2f} s. Summary written to {summary_file}\n", encoding="utf-8")
    logger.info("Sweep %d finished (elapsed=%.2fs, rec_spikes=%d, sim_spikes=%d, r=%.4f)",
                sweep, sim_res["elapsed_s"], analysis["spike_count_recorded_in_step"], analysis["spike_count_simulated_in_step"], analysis["correlation"])

    return summary_data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specimen-id", type=int, required=True, choices=list(REPRESENTATIVES.keys()))
    parser.add_argument("--sweep", type=int, default=None, help="Single sweep number to run")
    parser.add_argument("--sweeps", type=str, default=None, help="Comma-separated sweep numbers or 'all_heldout'")
    parser.add_argument("--condition-type", type=str, default="auto", choices=["auto", "calibration", "held_out"])
    parser.add_argument("--repo-dir", type=str, default=".")
    parser.add_argument("--workspace-dir", type=str, required=True)
    parser.add_argument("--allensdk-src", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--save-traces", action="store_true", help="Save compressed npz voltage/current traces")
    args = parser.parse_args()

    specimen_id = args.specimen_id
    meta = REPRESENTATIVES[specimen_id]
    repo_dir = pathlib.Path(args.repo_dir).resolve()
    workspace = pathlib.Path(args.workspace_dir).resolve()
    allensdk_src = pathlib.Path(args.allensdk_src).resolve()
    output_dir = pathlib.Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("runner")

    # Determine sweep list
    if args.sweeps == "all_heldout":
        held_csv = repo_dir / "results" / "phase3b" / "heldout_sweeps.csv"
        if not held_csv.exists():
            raise FileNotFoundError(f"Missing {held_csv}; run Phase 1 provenance audit first.")
        df_held = pd.read_csv(held_csv)
        spec_sweeps = df_held[df_held["specimen_id"] == specimen_id]["sweep_number"].tolist()
        sweeps_to_run = spec_sweeps
        condition_type = "held_out"
    elif args.sweeps:
        sweeps_to_run = [int(s.strip()) for s in args.sweeps.split(",")]
        condition_type = args.condition_type
    elif args.sweep is not None:
        sweeps_to_run = [args.sweep]
        condition_type = args.condition_type
    else:
        sweeps_to_run = [meta["calibration_sweep"]]
        condition_type = "calibration"

    logger.info("Executing %d sweep(s) for specimen %d: %s", len(sweeps_to_run), specimen_id, sweeps_to_run)

    results = []
    failures = []
    for swp in sweeps_to_run:
        try:
            res = run_single_sweep(
                specimen_id=specimen_id,
                sweep=swp,
                condition_type=condition_type,
                repo_dir=repo_dir,
                workspace=workspace,
                allensdk_src=allensdk_src,
                output_dir=output_dir,
                save_traces=args.save_traces,
                logger=logger
            )
            results.append(res)
        except Exception as exc:
            logger.error("Simulation failed for sweep %d: %s", swp, exc, exc_info=True)
            failures.append({"sweep": swp, "error": str(exc)})

    # If batch run, aggregate metrics CSV
    if len(results) > 1:
        agg_rows = []
        for r in results:
            row = {
                "specimen_id": r["specimen_id"],
                "population": r["population"],
                "layer": r["layer"],
                "sweep_id": r["sweep_id"],
                "condition_type": r["condition_type"],
                "stimulus_amplitude_pa": r["stimulus"]["amplitude_pa"],
                "stimulus_duration_ms": r["stimulus"]["duration_ms"],
                "stimulus_onset_ms": r["stimulus"]["onset_ms"],
            }
            row.update(r["metrics"])
            agg_rows.append(row)
        pd.DataFrame(agg_rows).to_csv(output_dir / "aggregated_metrics.csv", index=False)
        logger.info("Aggregated metrics written to %s", output_dir / "aggregated_metrics.csv")

    if failures:
        logger.warning("%d sweep(s) failed during execution", len(failures))
        (output_dir / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")
        sys.exit(1 if not results else 0)


if __name__ == "__main__":
    main()

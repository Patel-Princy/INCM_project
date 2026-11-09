import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

for swp in [45, 48, 50, 51, 52]:
    p = ROOT / "results" / "phase3b" / "heldout" / "484564503" / f"sweep_{swp}" / "summary.json"
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    m = d["metrics"]
    amp = d["stimulus"]["amplitude_pa"]
    print(f"Sweep {swp} ({amp:.1f} pA): rec_spikes={m['spike_count_recorded_in_step']}, sim_spikes={m['spike_count_simulated_in_step']}")
    print(f"   rec spike times: {m['spike_times_recorded_in_step_ms'][:4]} ... (len={len(m['spike_times_recorded_in_step_ms'])})")
    print(f"   sim spike times: {m['spike_times_simulated_in_step_ms'][:4]} ... (len={len(m['spike_times_simulated_in_step_ms'])})")
    print(f"   max depol rec: {m['max_depol_rec_mv']:.1f} mV, sim: {m['max_depol_sim_mv']:.1f} mV")
    print(f"   mean step V rec: {m['mean_step_v_rec_mv']:.1f} mV, sim: {m['mean_step_v_sim_mv']:.1f} mV")

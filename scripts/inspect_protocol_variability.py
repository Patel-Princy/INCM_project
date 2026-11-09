import json
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
df_metrics = pd.read_csv(ROOT / "results" / "phase3b" / "heldout_metrics.csv")

for sid, pop in [(471129934, "C (L5)"), (471786879, "D (L6a)")]:
    print(f"\n=================== SPECIMEN {sid} - POPULATION {pop} ===================")
    sub = df_metrics[df_metrics["specimen_id"] == sid]
    cols = ["sweep_number", "protocol_family", "stimulus_amplitude_pa", "stimulus_description", "spike_count_recorded_in_step", "spike_count_simulated_in_step"]
    
    # Chronological order by sweep_number
    sub_chrono = sub.sort_values(by="sweep_number")
    print("\n--- Chronological Sweeps near threshold / transition ---")
    threshold_sweeps = sub_chrono[(sub_chrono["stimulus_amplitude_pa"] >= 200) & (sub_chrono["stimulus_amplitude_pa"] <= 360)]
    print(threshold_sweeps[cols].to_string())

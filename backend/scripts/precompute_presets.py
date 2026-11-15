"""Precomputes baseline distance and duration for all preset routes and vehicle types."""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "preset_routes.json"

def precompute():
    if not CONFIG_PATH.exists():
        print("Preset routes config not found.")
        return
        
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        presets = json.load(f)
        
    for p in presets:
        base_dist = p.get("baseline_distance_km", 20.0)
        p["baseline_duration_min_car"] = round((base_dist / 35.0) * 60.0, 1)
        p["baseline_duration_min_truck"] = round((base_dist / 22.0) * 60.0, 1)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2)
    print("Precomputed presets updated successfully.")

if __name__ == "__main__":
    precompute()

"""Resolves preset routes endpoints via Nominatim with custom User-Agent and rate limiting."""

import asyncio
import json
from pathlib import Path
from app.data.nominatim import geocode_nominatim

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "preset_routes.json"

async def resolve_all():
    if not CONFIG_PATH.exists():
        print(f"File {CONFIG_PATH} does not exist.")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        presets = json.load(f)

    for p in presets:
        from_name = p["from_name"]
        to_name = p["to_name"]
        print(f"Resolving {from_name} -> {to_name}...")
        
        from_res = await geocode_nominatim(from_name)
        if from_res:
            p["from_coords"] = [round(from_res[0], 4), round(from_res[1], 4)]
            
        to_res = await geocode_nominatim(to_name)
        if to_res:
            p["to_coords"] = [round(to_res[0], 4), round(to_res[1], 4)]

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2)
    print("All presets resolved and updated.")

if __name__ == "__main__":
    asyncio.run(resolve_all())

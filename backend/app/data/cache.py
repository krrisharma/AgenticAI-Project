import json
import time
from pathlib import Path
from typing import Any, Optional, Tuple
from app.config import settings

class DataCache:
    """In-memory and file-backed cache with TTL support."""
    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[Tuple[Any, str, str]]:
        """Returns (data, status, as_of_iso) if valid."""
        entry = self._cache.get(key)
        if not entry:
            return None
        now = time.time()
        if now < entry["expires_at"]:
            return entry["data"], "cached", entry["as_of"]
        return None

    def set(self, key: str, data: Any, ttl_seconds: int, as_of: str):
        self._cache[key] = {
            "data": data,
            "expires_at": time.time() + ttl_seconds,
            "as_of": as_of
        }

    def load_snapshot(self, filename: str) -> Optional[dict]:
        path = settings.SNAPSHOTS_DIR / filename
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading snapshot {filename}: {e}")
        return None

    def save_snapshot(self, filename: str, data: Any):
        settings.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path = settings.SNAPSHOTS_DIR / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving snapshot {filename}: {e}")

cache = DataCache()

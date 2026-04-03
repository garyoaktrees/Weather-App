from __future__ import annotations

import json
from typing import Any

from app.core.paths import SETTINGS_FILE

DEFAULT_SETTINGS = {
    "home_location": "",
    "music_enabled": True,
    "music_volume": 35,
    "ui_mode": "modern",
    "radar_enabled": True,
    "radar_refresh_ms": 300000,
    "temperature_unit": "F",
    "ticker_speed_ms": 120,
    "description_mode": "funny",
}


def load_settings() -> dict[str, Any]:
    settings = DEFAULT_SETTINGS.copy()

    if SETTINGS_FILE.exists():
        try:
            with SETTINGS_FILE.open("r", encoding="utf-8") as file:
                saved = json.load(file)
                if isinstance(saved, dict):
                    settings.update(saved)
        except Exception:
            pass

    return settings


def save_settings(settings: dict[str, Any]) -> None:
    merged = DEFAULT_SETTINGS.copy()
    merged.update(settings)

    with SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump(merged, file, indent=4)
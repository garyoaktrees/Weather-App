from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


ROOT_DIR = project_root()

APP_DIR = ROOT_DIR / "app"
ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"

AUDIO_DIR = ASSETS_DIR / "audio"
ICONS_DIR = ASSETS_DIR / "icons"
ALERT_ICONS_DIR = ICONS_DIR / "alerts"
IMAGES_DIR = ASSETS_DIR / "images"
BACKGROUNDS_DIR = IMAGES_DIR / "backgrounds"

# ✅ THESE ARE WHAT YOU WERE MISSING
MUSIC_FILE = AUDIO_DIR / "weather_jazz.wav"
DEFAULT_BG_FILE = IMAGES_DIR / "weather_bg.jpg"
CITIES_JSON = DATA_DIR / "cities.json"

SETTINGS_FILE = ROOT_DIR / "weather_settings.json"


def ensure_directories() -> None:
    for folder in (
        ASSETS_DIR,
        DATA_DIR,
        AUDIO_DIR,
        ICONS_DIR,
        ALERT_ICONS_DIR,
        IMAGES_DIR,
        BACKGROUNDS_DIR,
    ):
        folder.mkdir(parents=True, exist_ok=True)
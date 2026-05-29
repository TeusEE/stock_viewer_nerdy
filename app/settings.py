"""User-configurable settings, persisted to ``data/settings.json``.

Currently holds the watch-mode refresh interval. Values are validated and
clamped to a sane range so a bad config can never break the app.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_SETTINGS_PATH = os.path.join(_DATA_DIR, "settings.json")

# Watch-interval bounds (seconds).
DEFAULT_WATCH_INTERVAL = 5
MIN_WATCH_INTERVAL = 1
MAX_WATCH_INTERVAL = 3600

_DEFAULTS: Dict[str, Any] = {"watch_interval": DEFAULT_WATCH_INTERVAL}


def _ensure_data_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def load_settings() -> Dict[str, Any]:
    """Return all settings merged over defaults (missing keys filled in)."""
    settings = dict(_DEFAULTS)
    if os.path.exists(_SETTINGS_PATH):
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                settings.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return settings


def save_settings(settings: Dict[str, Any]) -> None:
    """Persist the given settings dict to disk as JSON."""
    _ensure_data_dir()
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _clamp_interval(value: Any) -> int:
    """Coerce a value into a valid watch interval, falling back to default."""
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return DEFAULT_WATCH_INTERVAL
    return max(MIN_WATCH_INTERVAL, min(MAX_WATCH_INTERVAL, seconds))


def get_watch_interval() -> int:
    """Return the configured watch refresh interval in seconds."""
    return _clamp_interval(load_settings().get("watch_interval"))


def set_watch_interval(seconds: int) -> int:
    """Persist a new watch interval (clamped) and return the stored value."""
    value = _clamp_interval(seconds)
    settings = load_settings()
    settings["watch_interval"] = value
    save_settings(settings)
    return value

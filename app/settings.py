"""User-configurable settings, persisted to ``data/settings.json``.

Holds watch-mode refresh interval, news refresh interval, and max news count.
All values are validated and clamped so a bad config never breaks the app.
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

# News-interval bounds (seconds).
DEFAULT_NEWS_INTERVAL = 300
MIN_NEWS_INTERVAL = 60
MAX_NEWS_INTERVAL = 3600

# Max-news-count bounds.
DEFAULT_MAX_NEWS = 5
MIN_MAX_NEWS = 1
MAX_MAX_NEWS = 10

_DEFAULTS: Dict[str, Any] = {
    "watch_interval": DEFAULT_WATCH_INTERVAL,
    "news_interval": DEFAULT_NEWS_INTERVAL,
    "max_news": DEFAULT_MAX_NEWS,
}


def _ensure_data_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def load_settings() -> Dict[str, Any]:
    """Return all settings merged over defaults (missing keys filled in)."""
    cfg = dict(_DEFAULTS)
    if os.path.exists(_SETTINGS_PATH):
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                cfg.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save_settings(cfg: Dict[str, Any]) -> None:
    """Persist the given settings dict to disk as JSON."""
    _ensure_data_dir()
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as handle:
        json.dump(cfg, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


# ---------------------------------------------------------------------------
# Watch interval
# ---------------------------------------------------------------------------
def _clamp(value: Any, default: int, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def get_watch_interval() -> int:
    return _clamp(
        load_settings().get("watch_interval"),
        DEFAULT_WATCH_INTERVAL,
        MIN_WATCH_INTERVAL,
        MAX_WATCH_INTERVAL,
    )


def set_watch_interval(seconds: int) -> int:
    value = _clamp(seconds, DEFAULT_WATCH_INTERVAL, MIN_WATCH_INTERVAL, MAX_WATCH_INTERVAL)
    cfg = load_settings()
    cfg["watch_interval"] = value
    save_settings(cfg)
    return value


# ---------------------------------------------------------------------------
# News interval
# ---------------------------------------------------------------------------
def get_news_interval() -> int:
    return _clamp(
        load_settings().get("news_interval"),
        DEFAULT_NEWS_INTERVAL,
        MIN_NEWS_INTERVAL,
        MAX_NEWS_INTERVAL,
    )


def set_news_interval(seconds: int) -> int:
    value = _clamp(seconds, DEFAULT_NEWS_INTERVAL, MIN_NEWS_INTERVAL, MAX_NEWS_INTERVAL)
    cfg = load_settings()
    cfg["news_interval"] = value
    save_settings(cfg)
    return value


# ---------------------------------------------------------------------------
# Max news count
# ---------------------------------------------------------------------------
def get_max_news() -> int:
    return _clamp(
        load_settings().get("max_news"),
        DEFAULT_MAX_NEWS,
        MIN_MAX_NEWS,
        MAX_MAX_NEWS,
    )


def set_max_news(count: int) -> int:
    value = _clamp(count, DEFAULT_MAX_NEWS, MIN_MAX_NEWS, MAX_MAX_NEWS)
    cfg = load_settings()
    cfg["max_news"] = value
    save_settings(cfg)
    return value

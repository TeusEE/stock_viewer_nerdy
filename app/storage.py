"""Persistent storage for the watchlist.

Each watchlist entry stores both the KRX stock ``code`` and its human-readable
``name`` so the UI can show names without a network lookup. Saved as JSON in
``data/watchlist.json`` (relative to the project root).
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

# Project root = parent directory of this ``app`` package.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_WATCHLIST_PATH = os.path.join(_DATA_DIR, "watchlist.json")


def _ensure_data_dir() -> None:
    """Make sure the data directory exists before reading/writing."""
    os.makedirs(_DATA_DIR, exist_ok=True)


def load_watchlist() -> List[Dict[str, str]]:
    """Return the saved watchlist as a list of {code, name} dicts.

    Returns an empty list if the file is missing or corrupt. Legacy entries
    stored as plain strings are upgraded to {code, name} on read.
    """
    if not os.path.exists(_WATCHLIST_PATH):
        return []
    try:
        with open(_WATCHLIST_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []

    raw = data.get("watchlist", []) if isinstance(data, dict) else []
    seen = set()
    cleaned: List[Dict[str, str]] = []
    for entry in raw:
        if isinstance(entry, str):
            code, name = entry.strip(), entry.strip()
        elif isinstance(entry, dict):
            code = str(entry.get("code", "")).strip()
            name = str(entry.get("name", "")).strip() or code
        else:
            continue
        if code and code not in seen:
            seen.add(code)
            cleaned.append({"code": code, "name": name})
    return cleaned


def save_watchlist(watchlist: List[Dict[str, str]]) -> None:
    """Persist the given list of {code, name} entries to disk as JSON."""
    _ensure_data_dir()
    payload = {"watchlist": watchlist}
    with open(_WATCHLIST_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def has_code(code: str) -> bool:
    """Return True if the given code is already in the watchlist."""
    code = code.strip()
    return any(entry["code"] == code for entry in load_watchlist())


def add_stock(code: str, name: str) -> bool:
    """Add a stock to the watchlist.

    Returns True if added, False if the code already exists.
    """
    code = code.strip()
    watchlist = load_watchlist()
    if any(entry["code"] == code for entry in watchlist):
        return False
    watchlist.append({"code": code, "name": name.strip() or code})
    save_watchlist(watchlist)
    return True


def remove_stock(code: str) -> bool:
    """Remove a stock by code. Returns True if removed, False if absent."""
    code = code.strip()
    watchlist = load_watchlist()
    if not any(entry["code"] == code for entry in watchlist):
        return False
    watchlist = [entry for entry in watchlist if entry["code"] != code]
    save_watchlist(watchlist)
    return True


def update_stock(old_code: str, new_code: str, new_name: str) -> bool:
    """Replace ``old_code`` with a new stock, preserving its position.

    Returns True on success, False if ``old_code`` is not present.
    """
    old_code = old_code.strip()
    new_code = new_code.strip()
    watchlist = load_watchlist()
    if not any(entry["code"] == old_code for entry in watchlist):
        return False

    updated: List[Dict[str, str]] = []
    seen = set()
    for entry in watchlist:
        if entry["code"] == old_code:
            replacement = {"code": new_code, "name": new_name.strip() or new_code}
            if new_code not in seen:
                seen.add(new_code)
                updated.append(replacement)
        elif entry["code"] != new_code:
            seen.add(entry["code"])
            updated.append(entry)
    save_watchlist(updated)
    return True

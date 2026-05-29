"""Korean stock data retrieval via FinanceDataReader.

Provides company-name search over the KRX listing and per-stock quote
information (current price, daily change %, high, low). Network/data errors are
normalized into ``StockServiceError`` for the UI layer.
"""

from __future__ import annotations

import datetime
import os
from typing import Any, Dict, List, Optional

try:
    import FinanceDataReader as fdr
except ImportError:  # pragma: no cover - import guard for friendlier error
    fdr = None


class StockServiceError(Exception):
    """Raised when stock data cannot be retrieved."""


# Cached KRX listing (code <-> name) for the lifetime of the process, plus an
# on-disk copy so repeat launches don't re-download the whole listing.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LISTING_CACHE_PATH = os.path.join(_BASE_DIR, "data", "krx_listing.csv")
_listing_cache: Optional[List[Dict[str, str]]] = None


def _require_fdr() -> None:
    if fdr is None:
        raise StockServiceError(
            "FinanceDataReader is not installed. Run: pip install -r requirements.txt"
        )


# ---------------------------------------------------------------------------
# Listing (code <-> name)
# ---------------------------------------------------------------------------
def _load_listing() -> List[Dict[str, str]]:
    """Return the KRX listing as a list of {code, name, market} dicts.

    Uses an in-memory cache, then a same-day on-disk CSV cache, before falling
    back to downloading a fresh listing from KRX.
    """
    global _listing_cache
    if _listing_cache is not None:
        return _listing_cache

    cached = _load_listing_from_disk()
    if cached is not None:
        _listing_cache = cached
        return _listing_cache

    _require_fdr()
    try:
        frame = fdr.StockListing("KRX")
    except Exception as exc:  # noqa: BLE001 - normalize all API failures
        raise StockServiceError(str(exc)) from exc

    listing: List[Dict[str, str]] = []
    for _, row in frame.iterrows():
        code = str(row.get("Code", "")).strip()
        name = str(row.get("Name", "")).strip()
        market = str(row.get("Market", "")).strip()
        if code and name:
            listing.append({"code": code, "name": name, "market": market})

    _listing_cache = listing
    _save_listing_to_disk(listing)
    return listing


def _load_listing_from_disk() -> Optional[List[Dict[str, str]]]:
    """Load the listing CSV if it exists and was written today."""
    if not os.path.exists(_LISTING_CACHE_PATH):
        return None
    try:
        mtime = datetime.date.fromtimestamp(os.path.getmtime(_LISTING_CACHE_PATH))
        if mtime != datetime.date.today():
            return None
        import csv

        with open(_LISTING_CACHE_PATH, "r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except (OSError, ValueError, csv.Error):
        return None


def _save_listing_to_disk(listing: List[Dict[str, str]]) -> None:
    """Persist the listing to CSV (best effort; failures are ignored)."""
    try:
        import csv

        os.makedirs(os.path.dirname(_LISTING_CACHE_PATH), exist_ok=True)
        with open(_LISTING_CACHE_PATH, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["code", "name", "market"])
            writer.writeheader()
            writer.writerows(listing)
    except (OSError, ValueError):
        pass


def search_stocks(keyword: str) -> List[Dict[str, str]]:
    """Search KRX stocks whose name contains ``keyword``.

    Returns a list of ``{"code", "name", "market"}`` dicts (max 20), with exact
    and prefix matches ranked first. Raises ``StockServiceError`` on failure.
    """
    keyword = keyword.strip()
    if not keyword:
        return []

    listing = _load_listing()
    lowered = keyword.lower()

    matches = [item for item in listing if lowered in item["name"].lower()]

    def rank(item: Dict[str, str]) -> tuple:
        name = item["name"].lower()
        if name == lowered:
            return (0, len(name))
        if name.startswith(lowered):
            return (1, len(name))
        return (2, len(name))

    matches.sort(key=rank)
    return matches[:20]


def resolve_name(code: str) -> Optional[str]:
    """Return the company name for a code, or None if not found."""
    code = code.strip()
    for item in _load_listing():
        if item["code"] == code:
            return item["name"]
    return None


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------
def get_stock_info(code: str) -> Dict[str, Any]:
    """Fetch quote info for a single KRX stock code.

    Returns ``{code, price, change_percent, high, low}``. Raises
    ``StockServiceError`` for invalid codes or data/network failures.
    """
    _require_fdr()
    code = code.strip()

    start = datetime.date.today() - datetime.timedelta(days=14)
    try:
        history = fdr.DataReader(code, start)
    except Exception as exc:  # noqa: BLE001 - normalize all API failures
        raise StockServiceError(str(exc)) from exc

    if history is None or history.empty:
        raise StockServiceError(f"Invalid stock code: {code}")

    last = history.iloc[-1]
    price = _safe_float(last.get("Close"))
    high = _safe_float(last.get("High"))
    low = _safe_float(last.get("Low"))

    # Prefer the broker-provided daily change ratio; fall back to computing it
    # from the previous close.
    change_percent = _safe_float(last.get("Change"))
    if change_percent is not None:
        change_percent *= 100.0
    elif price is not None and len(history) >= 2:
        prev_close = _safe_float(history.iloc[-2].get("Close"))
        if prev_close not in (None, 0):
            change_percent = (price - prev_close) / prev_close * 100.0

    return {
        "code": code,
        "price": price,
        "change_percent": change_percent,
        "high": high,
        "low": low,
    }


def get_quotes(codes: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch quotes for many codes, tolerating per-code failures.

    Returns a dict mapping code -> quote info. Codes that fail are mapped to a
    placeholder quote with None values.
    """
    quotes: Dict[str, Dict[str, Any]] = {}
    for code in codes:
        try:
            quotes[code] = get_stock_info(code)
        except StockServiceError:
            quotes[code] = {
                "code": code,
                "price": None,
                "change_percent": None,
                "high": None,
                "low": None,
            }
    return quotes


def _safe_float(value: Any) -> Optional[float]:
    """Coerce a value to float, returning None on failure or NaN."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN check
        return None
    return number

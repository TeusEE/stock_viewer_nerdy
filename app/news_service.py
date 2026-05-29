"""News fetching from Naver Finance, Yahoo Finance, and Bloomberg.

Runs a daemon background thread that refreshes the cache every 5 minutes.
All network/parse failures are swallowed silently; the last successful cache
is preserved so the UI never crashes due to a broken news source.
"""

from __future__ import annotations

import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

try:
    import requests as _requests
except ImportError:
    _requests = None  # type: ignore[assignment]

try:
    from bs4 import BeautifulSoup as _BS
except ImportError:
    _BS = None  # type: ignore[assignment]

from . import settings as _settings

# Module-level fallback defaults (used only when settings import fails).
_DEFAULT_NEWS_INTERVAL = 300
_DEFAULT_MAX_NEWS = 5
_TIMEOUT = 10


def _news_interval() -> int:
    try:
        return _settings.get_news_interval()
    except Exception:
        return _DEFAULT_NEWS_INTERVAL


def _max_news() -> int:
    try:
        return _settings.get_max_news()
    except Exception:
        return _DEFAULT_MAX_NEWS

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://finance.naver.com/",
}


@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    published_at: str  # already formatted for display (e.g. "3분 전")


# ---------------------------------------------------------------------------
# Global in-memory cache (shared across threads via _lock)
# ---------------------------------------------------------------------------
_cache: List[NewsItem] = []
_last_fetched: float = 0.0
_loading: bool = False
_lock = threading.Lock()


def get_cached_news() -> List[NewsItem]:
    with _lock:
        return list(_cache)


def is_loading() -> bool:
    with _lock:
        return _loading


def seconds_until_next_fetch() -> int:
    elapsed = time.time() - _last_fetched
    return max(0, int(_news_interval() - elapsed))


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
def _relative_time(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    now = datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = int((now - dt).total_seconds())
    if diff < 60:
        return "방금 전"
    if diff < 3600:
        return f"{diff // 60}분 전"
    if diff < 86400:
        return f"{diff // 3600}시간 전"
    return f"{diff // 86400}일 전"


def _parse_rfc2822(s: str) -> Optional[datetime]:
    try:
        return parsedate_to_datetime(s)
    except Exception:
        return None


def _parse_naver_date(s: str) -> Optional[datetime]:
    for fmt in ("%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Naver Finance
# ---------------------------------------------------------------------------
def _fetch_naver(code: str) -> List[NewsItem]:
    if _requests is None or _BS is None:
        return []
    try:
        url = f"https://finance.naver.com/item/news.naver?code={code}"
        resp = _requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.encoding = resp.apparent_encoding or "euc-kr"
        soup = _BS(resp.text, "html.parser")

        table = soup.find("table", class_="type5")
        if table is None:
            return []

        limit = _max_news()
        items: List[NewsItem] = []
        for tr in table.find_all("tr"):
            td_title = tr.find("td", class_="title")
            td_date = tr.find("td", class_="date")
            if not td_title:
                continue
            a = td_title.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://finance.naver.com" + href
            date_str = td_date.get_text(strip=True) if td_date else ""
            dt = _parse_naver_date(date_str)
            if title:
                items.append(NewsItem(
                    title=title,
                    source="Naver Finance",
                    url=href,
                    published_at=_relative_time(dt) or date_str,
                ))
            if len(items) >= limit:
                break
        return items
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Yahoo Finance RSS
# ---------------------------------------------------------------------------
def _yahoo_suffix(code: str) -> str:
    try:
        from .stock_service import _load_listing  # noqa: PLC0415
        for item in _load_listing():
            if item["code"] == code:
                return ".KQ" if "KOSDAQ" in item.get("market", "").upper() else ".KS"
    except Exception:
        pass
    return ".KS"


def _fetch_yahoo(code: str) -> List[NewsItem]:
    if _requests is None:
        return []
    try:
        ticker = code + _yahoo_suffix(code)
        url = (
            f"https://feeds.finance.yahoo.com/rss/2.0/headline"
            f"?s={ticker}&region=US&lang=en-US"
        )
        resp = _requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        limit = _max_news()
        items: List[NewsItem] = []
        for el in channel.findall("item"):
            title_el = el.find("title")
            link_el = el.find("link")
            pub_el = el.find("pubDate")
            if title_el is None:
                continue
            title = (title_el.text or "").strip()
            link = (link_el.text or "").strip() if link_el is not None else ""
            # ElementTree tail fallback for self-closing <link/>
            if not link and link_el is not None:
                link = (link_el.tail or "").strip()
            pub = (pub_el.text or "").strip() if pub_el is not None else ""
            dt = _parse_rfc2822(pub)
            if title:
                items.append(NewsItem(
                    title=title,
                    source="Yahoo Finance",
                    url=link,
                    published_at=_relative_time(dt) or pub,
                ))
            if len(items) >= limit:
                break
        return items
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Bloomberg via Google News RSS (best-effort; Bloomberg blocks direct scraping)
# ---------------------------------------------------------------------------
def _fetch_bloomberg(name: str) -> List[NewsItem]:
    if _requests is None:
        return []
    try:
        q = quote_plus(f"{name} site:bloomberg.com")
        url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
        resp = _requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        limit = _max_news()
        items: List[NewsItem] = []
        for el in channel.findall("item"):
            title_el = el.find("title")
            link_el = el.find("link")
            pub_el = el.find("pubDate")
            if title_el is None:
                continue
            title = (title_el.text or "").strip()
            # Strip " - Bloomberg" suffix that Google News appends
            if title.endswith(" - Bloomberg"):
                title = title[: -len(" - Bloomberg")]
            link = (link_el.text or "").strip() if link_el is not None else ""
            if not link and link_el is not None:
                link = (link_el.tail or "").strip()
            pub = (pub_el.text or "").strip() if pub_el is not None else ""
            dt = _parse_rfc2822(pub)
            if title:
                items.append(NewsItem(
                    title=title,
                    source="Bloomberg",
                    url=link,
                    published_at=_relative_time(dt) or pub,
                ))
            if len(items) >= limit:
                break
        return items
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Aggregate: all sources, all watchlist entries, deduplicated, top MAX_NEWS
# ---------------------------------------------------------------------------
def _fetch_all(watchlist: List[Dict[str, str]]) -> List[NewsItem]:
    limit = _max_news()
    seen: set = set()
    result: List[NewsItem] = []

    for entry in watchlist:
        code = entry.get("code", "")
        name = entry.get("name", "")

        for fetcher, arg in (
            (_fetch_naver, code),
            (_fetch_yahoo, code),
            (_fetch_bloomberg, name),
        ):
            if len(result) >= limit:
                return result
            for item in fetcher(arg):  # type: ignore[operator]
                key = item.url or item.title
                if key and key not in seen:
                    seen.add(key)
                    result.append(item)
                    if len(result) >= limit:
                        break

    return result


# ---------------------------------------------------------------------------
# Cache refresh
# ---------------------------------------------------------------------------
def _refresh(watchlist: List[Dict[str, str]]) -> None:
    global _cache, _last_fetched, _loading
    with _lock:
        _loading = True
    items: List[NewsItem] = []
    try:
        items = _fetch_all(watchlist)
    except Exception:
        pass
    with _lock:
        if items:
            _cache = items
        _last_fetched = time.time()
        _loading = False


# ---------------------------------------------------------------------------
# Background poller
# ---------------------------------------------------------------------------
class NewsPoller:
    """Daemon thread that refreshes the news cache every NEWS_INTERVAL seconds."""

    def __init__(self, watchlist: List[Dict[str, str]]) -> None:
        self._watchlist = watchlist
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="news-poller"
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stop.is_set():
            _refresh(self._watchlist)
            self._stop.wait(_news_interval())

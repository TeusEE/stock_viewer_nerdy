"""Interactive rich-based TUI for the Korean Stock Watch app.

Running the program launches a full-screen menu where the user can add, edit,
and delete stocks, and enter a live "watch" mode. Stocks are added by searching
a company name (e.g. "삼성") and picking from suggested matches; the watchlist
and all views show the company name rather than the bare code.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

from . import settings
from . import storage
from . import utils
from .stock_service import get_quotes, get_stock_info, search_stocks, StockServiceError

_MENU = (
    "[bold rgb(255,140,0)]\\[A][/bold rgb(255,140,0)][dim] 추가   [/dim]"
    "[bold rgb(255,140,0)]\\[E][/bold rgb(255,140,0)][dim] 수정   [/dim]"
    "[bold rgb(255,140,0)]\\[D][/bold rgb(255,140,0)][dim] 삭제   [/dim]"
    "[bold rgb(255,140,0)]\\[W][/bold rgb(255,140,0)][dim] 감시   [/dim]"
    "[bold rgb(255,140,0)]\\[R][/bold rgb(255,140,0)][dim] 새로고침   [/dim]"
    "[bold rgb(255,140,0)]\\[S][/bold rgb(255,140,0)][dim] 설정   [/dim]"
    "[bold rgb(255,140,0)]\\[Q][/bold rgb(255,140,0)][dim] 종료[/dim]"
)


class App:
    """Stateful interactive application backed by the rich console."""

    def __init__(self) -> None:
        self.console = Console()
        # In-memory cache of quotes keyed by code, so menu navigation stays
        # snappy and we only hit the network when data actually changes.
        self.quotes: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Run the interactive menu loop until the user quits."""
        self.refresh_quotes()
        while True:
            self.render_screen()
            choice = (
                Prompt.ask(
                    "선택",
                    choices=["a", "e", "d", "w", "r", "s", "q"],
                    show_choices=False,
                )
                .strip()
                .lower()
            )

            if choice == "a":
                self.action_add()
            elif choice == "e":
                self.action_edit()
            elif choice == "d":
                self.action_delete()
            elif choice == "w":
                self.action_watch()
            elif choice == "r":
                self.refresh_quotes()
            elif choice == "s":
                self.action_settings()
            elif choice == "q":
                self.console.print("[dim]종료합니다.[/dim]")
                return

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def render_screen(self, *, footer: Optional[str] = None) -> None:
        """Clear the screen and draw the header, table, and menu."""
        self.console.clear()
        self.console.print(
            Panel.fit("[bold rgb(255,140,0)]주식 관심종목[/bold rgb(255,140,0)]", border_style="rgb(255,140,0)")
        )

        watchlist = storage.load_watchlist()
        if not watchlist:
            self.console.print(Rule("WATCHLIST", style="rgb(80,80,80)", align="left"))
            self.console.print("[rgb(100,100,100)]  No stocks in watchlist. Press [A] to add.[/rgb(100,100,100)]\n")
        else:
            rows = [self._row_for(entry) for entry in watchlist]
            self.console.print(utils.build_watchlist_table(rows))
            self.console.print()

        self.console.print(footer or _MENU)

    def _row_for(self, entry: Dict[str, str]) -> Dict[str, Any]:
        """Combine a watchlist entry (code, name) with its cached quote."""
        code = entry["code"]
        quote = self.quotes.get(code, {})
        return {
            "name": entry.get("name", code),
            "code": code,
            "price": quote.get("price"),
            "change_percent": quote.get("change_percent"),
            "high": quote.get("high"),
            "low": quote.get("low"),
        }

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def refresh_quotes(self) -> None:
        """Re-fetch quotes for the entire watchlist into the cache."""
        watchlist = storage.load_watchlist()
        if not watchlist:
            self.quotes = {}
            return
        self.console.print("[dim]시세를 불러오는 중...[/dim]")
        codes = [entry["code"] for entry in watchlist]
        self.quotes = get_quotes(codes)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_add(self) -> None:
        """Search by company name and add a chosen stock."""
        pick = self._search_and_pick(prompt="추가할 종목명을 입력하세요 (예: 삼성)")
        if pick is None:
            return

        code, name = pick["code"], pick["name"]
        if storage.add_stock(code, name):
            try:
                self.quotes[code] = get_stock_info(code)
            except StockServiceError:
                pass
            self._notify(f"[rgb(255,255,0)][INFO] {name} 추가 완료.[/rgb(255,255,0)]")
        else:
            self._notify("[rgb(255,255,0)][INFO] 이미 등록된 종목입니다.[/rgb(255,255,0)]")

    def action_edit(self) -> None:
        """Pick a watchlist entry and replace it with a newly searched stock."""
        old = self._pick_from_watchlist("수정할 종목 번호 선택")
        if old is None:
            return

        pick = self._search_and_pick(
            prompt=f"'{old['name']}' 대신 등록할 종목명 입력"
        )
        if pick is None:
            return
        if pick["code"] == old["code"]:
            self._notify("[rgb(255,255,0)][INFO] 변경 사항이 없습니다.[/rgb(255,255,0)]")
            return

        if storage.update_stock(old["code"], pick["code"], pick["name"]):
            self.quotes.pop(old["code"], None)
            try:
                self.quotes[pick["code"]] = get_stock_info(pick["code"])
            except StockServiceError:
                pass
            self._notify(
                f"[rgb(255,255,0)][INFO] {old['name']} → {pick['name']} 수정 완료.[/rgb(255,255,0)]"
            )
        else:
            self._notify("[bold red][ERROR] 수정에 실패했습니다.[/bold red]")

    def action_delete(self) -> None:
        """Pick a watchlist entry and remove it."""
        entry = self._pick_from_watchlist("삭제할 종목 번호 선택")
        if entry is None:
            return

        if storage.remove_stock(entry["code"]):
            self.quotes.pop(entry["code"], None)
            self._notify(f"[rgb(255,255,0)][INFO] {entry['name']} 삭제 완료.[/rgb(255,255,0)]")
        else:
            self._notify("[rgb(255,255,0)][INFO] 관심 종목에 없습니다.[/rgb(255,255,0)]")

    def action_watch(self) -> None:
        """Enter live auto-refresh mode until interrupted with Ctrl+C."""
        from . import news_service  # lazy import — avoids hard dep at startup

        watchlist = storage.load_watchlist()
        if not watchlist:
            self._notify("[rgb(255,255,0)][INFO] 관심 종목이 비어 있습니다.[/rgb(255,255,0)]")
            return

        interval = settings.get_watch_interval()
        codes = [entry["code"] for entry in watchlist]

        poller = news_service.NewsPoller(watchlist)
        poller.start()

        try:
            while True:
                self.quotes = get_quotes(codes)
                rows = [self._row_for(entry) for entry in watchlist]
                news_items = news_service.get_cached_news()
                loading = news_service.is_loading()
                secs_left = news_service.seconds_until_next_fetch()

                self.console.clear()
                self.console.print(
                    Panel.fit(
                        "[bold rgb(255,140,0)]주식 관심종목[/bold rgb(255,140,0)]"
                        "  [dim]WATCH MODE[/dim]",
                        border_style="rgb(255,140,0)",
                    )
                )
                self.console.print(utils.build_watchlist_table(rows))
                self.console.print()
                utils.render_news_section(self.console, news_items, loading)

                if loading and not news_items:
                    news_status = "NEWS LOADING..."
                elif secs_left == 0:
                    news_status = "NEWS UPDATING..."
                else:
                    news_status = f"NEWS IN {secs_left // 60:02d}:{secs_left % 60:02d}"

                self.console.print(Rule(style="rgb(60,60,60)"))
                status = Text()
                status.append(f"{interval}s REFRESH", style="rgb(255,165,0)")
                status.append("  |  ", style="dim")
                status.append(news_status, style="rgb(255,165,0)")
                status.append("  |  ", style="dim")
                status.append("Ctrl+C → MENU", style="dim")
                self.console.print(status)
                time.sleep(interval)
        except KeyboardInterrupt:
            poller.stop()
            return

    def action_settings(self) -> None:
        """Let the user view and change configurable settings."""
        self.console.print("\n[bold rgb(255,140,0)]SETTINGS[/bold rgb(255,140,0)]\n")
        self.console.print(
            f"  [bold rgb(255,140,0)][1][/bold rgb(255,140,0)] [dim]REFRESH INTERVAL  [/dim]"
            f"[bold white]{settings.get_watch_interval():>5}s[/bold white]"
            f"  [dim]({settings.MIN_WATCH_INTERVAL} ~ {settings.MAX_WATCH_INTERVAL}s)[/dim]"
        )
        self.console.print(
            f"  [bold rgb(255,140,0)][2][/bold rgb(255,140,0)] [dim]NEWS INTERVAL     [/dim]"
            f"[bold white]{settings.get_news_interval():>5}s[/bold white]"
            f"  [dim]({settings.MIN_NEWS_INTERVAL} ~ {settings.MAX_NEWS_INTERVAL}s)[/dim]"
        )
        self.console.print(
            f"  [bold rgb(255,140,0)][3][/bold rgb(255,140,0)] [dim]MAX NEWS COUNT    [/dim]"
            f"[bold white]{settings.get_max_news():>5}[/bold white]"
            f"  [dim]({settings.MIN_MAX_NEWS} ~ {settings.MAX_MAX_NEWS} items)[/dim]"
        )
        self.console.print("\n  [dim][0] CANCEL[/dim]\n")

        choice = self._ask_index("Select", max_index=3, allow_zero=True)
        if choice is None or choice == 0:
            return

        if choice == 1:
            self._change_setting(
                label="REFRESH INTERVAL",
                current=settings.get_watch_interval(),
                setter=settings.set_watch_interval,
                unit="s",
            )
        elif choice == 2:
            self._change_setting(
                label="NEWS INTERVAL",
                current=settings.get_news_interval(),
                setter=settings.set_news_interval,
                unit="s",
            )
        elif choice == 3:
            self._change_setting(
                label="MAX NEWS COUNT",
                current=settings.get_max_news(),
                setter=settings.set_max_news,
                unit=" items",
            )

    def _change_setting(self, label: str, current: int, setter: Any, unit: str) -> None:
        """Prompt for a new integer value, save it, and notify the user."""
        self.console.print(f"[dim]Current: {current}{unit}  (leave blank to cancel)[/dim]")
        raw = Prompt.ask(f"New {label}", default="").strip()
        if not raw:
            return
        try:
            value = int(raw)
        except ValueError:
            self._notify("[bold red][ERROR] Enter a number.[/bold red]")
            return
        saved = setter(value)
        if saved != value:
            self._notify(
                f"[rgb(255,255,0)][INFO] Out of range — clamped to {saved}{unit}.[/rgb(255,255,0)]"
            )
        else:
            self._notify(f"[rgb(255,255,0)][INFO] {label} set to {saved}{unit}.[/rgb(255,255,0)]")

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _search_and_pick(self, prompt: str) -> Optional[Dict[str, str]]:
        """Prompt for a name, show suggestions, return the chosen {code, name}.

        Returns None if cancelled or nothing is selected.
        """
        keyword = Prompt.ask(prompt, default="").strip()
        if not keyword:
            return None

        try:
            results = search_stocks(keyword)
        except StockServiceError:
            self._notify("[red][ERROR] 종목 정보를 불러오지 못했습니다.[/red]")
            return None

        if not results:
            self._notify(
                f"[rgb(255,255,0)][INFO] '{keyword}' 와(과) 일치하는 종목이 없습니다.[/rgb(255,255,0)]"
            )
            return None

        self.console.print()
        self.console.print(utils.build_search_table(results))
        self.console.print("[dim]  [0] CANCEL[/dim]\n")

        choice = self._ask_index(
            "번호 선택", max_index=len(results), allow_zero=True
        )
        if choice is None or choice == 0:
            return None
        chosen = results[choice - 1]
        return {"code": chosen["code"], "name": chosen["name"]}

    def _pick_from_watchlist(self, prompt: str) -> Optional[Dict[str, str]]:
        """Show the watchlist numbered and return the chosen {code, name}."""
        watchlist = storage.load_watchlist()
        if not watchlist:
            self._notify("[rgb(255,255,0)][INFO] 관심 종목이 비어 있습니다.[/rgb(255,255,0)]")
            return None

        rows = [self._row_for(entry) for entry in watchlist]
        self.console.print()
        self.console.print(utils.build_watchlist_table(rows))
        self.console.print("[dim]  [0] CANCEL[/dim]\n")

        choice = self._ask_index(prompt, max_index=len(watchlist), allow_zero=True)
        if choice is None or choice == 0:
            return None
        return watchlist[choice - 1]

    def _ask_index(
        self, prompt: str, max_index: int, allow_zero: bool = False
    ) -> Optional[int]:
        """Prompt for an integer in range, re-asking on invalid input."""
        low = 0 if allow_zero else 1
        while True:
            raw = Prompt.ask(prompt, default="0" if allow_zero else None)
            if raw is None:
                return None
            raw = raw.strip()
            if not raw:
                return 0 if allow_zero else None
            try:
                value = int(raw)
            except ValueError:
                self.console.print("[red]숫자를 입력하세요.[/red]")
                continue
            if low <= value <= max_index:
                return value
            self.console.print(
                f"[red]{low} ~ {max_index} 사이의 숫자를 입력하세요.[/red]"
            )

    def _notify(self, message: str) -> None:
        """Print a message and wait for Enter so the user can read it."""
        self.console.print(message)
        Prompt.ask("[dim]계속하려면 Enter[/dim]", default="")


def run() -> None:
    """Module-level entry point used by main.py."""
    App().run()

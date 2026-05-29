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

from . import settings
from . import storage
from . import utils
from .stock_service import get_quotes, get_stock_info, search_stocks, StockServiceError

_MENU = (
    "[bold]\\[a][/bold] 추가   "
    "[bold]\\[e][/bold] 수정   "
    "[bold]\\[d][/bold] 삭제   "
    "[bold]\\[w][/bold] 감시   "
    "[bold]\\[r][/bold] 새로고침   "
    "[bold]\\[s][/bold] 설정   "
    "[bold]\\[q][/bold] 종료"
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
            Panel.fit("[bold cyan]주식 관심종목[/bold cyan]", border_style="cyan")
        )

        watchlist = storage.load_watchlist()
        if not watchlist:
            self.console.print("[yellow][INFO] 관심 종목이 비어 있습니다.[/yellow]\n")
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
            self._notify(f"[green][INFO] {name} 추가 완료.[/green]")
        else:
            self._notify("[yellow][INFO] 이미 등록된 종목입니다.[/yellow]")

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
            self._notify("[yellow][INFO] 변경 사항이 없습니다.[/yellow]")
            return

        if storage.update_stock(old["code"], pick["code"], pick["name"]):
            self.quotes.pop(old["code"], None)
            try:
                self.quotes[pick["code"]] = get_stock_info(pick["code"])
            except StockServiceError:
                pass
            self._notify(
                f"[green][INFO] {old['name']} → {pick['name']} 수정 완료.[/green]"
            )
        else:
            self._notify("[red][ERROR] 수정에 실패했습니다.[/red]")

    def action_delete(self) -> None:
        """Pick a watchlist entry and remove it."""
        entry = self._pick_from_watchlist("삭제할 종목 번호 선택")
        if entry is None:
            return

        if storage.remove_stock(entry["code"]):
            self.quotes.pop(entry["code"], None)
            self._notify(f"[green][INFO] {entry['name']} 삭제 완료.[/green]")
        else:
            self._notify("[yellow][INFO] 관심 종목에 없습니다.[/yellow]")

    def action_watch(self) -> None:
        """Enter live auto-refresh mode until interrupted with Ctrl+C."""
        watchlist = storage.load_watchlist()
        if not watchlist:
            self._notify("[yellow][INFO] 관심 종목이 비어 있습니다.[/yellow]")
            return

        interval = settings.get_watch_interval()
        codes = [entry["code"] for entry in watchlist]
        try:
            while True:
                self.quotes = get_quotes(codes)
                rows = [self._row_for(entry) for entry in watchlist]
                self.console.clear()
                self.console.print(
                    Panel.fit(
                        "[bold cyan]주식 관심종목 (실시간 감시)[/bold cyan]",
                        border_style="cyan",
                    )
                )
                self.console.print(utils.build_watchlist_table(rows))
                self.console.print(
                    f"\n[dim]{interval}초마다 갱신됩니다. "
                    "메뉴로 돌아가려면 Ctrl+C 를 누르세요.[/dim]"
                )
                time.sleep(interval)
        except KeyboardInterrupt:
            # Normal exit path from watch mode back to the main menu.
            return

    def action_settings(self) -> None:
        """Let the user view and change configurable settings."""
        current = settings.get_watch_interval()
        self.console.print(
            f"\n[bold]설정[/bold]  현재 감시 갱신 주기: [cyan]{current}초[/cyan]"
        )
        self.console.print(
            f"[dim]({settings.MIN_WATCH_INTERVAL} ~ {settings.MAX_WATCH_INTERVAL}초, "
            "빈 값이면 변경 안 함)[/dim]"
        )

        raw = Prompt.ask("새 갱신 주기(초)", default="").strip()
        if not raw:
            return
        try:
            seconds = int(raw)
        except ValueError:
            self._notify("[red]숫자를 입력하세요.[/red]")
            return

        saved = settings.set_watch_interval(seconds)
        if saved != seconds:
            self._notify(
                f"[yellow][INFO] 허용 범위로 조정되어 {saved}초로 저장했습니다."
                "[/yellow]"
            )
        else:
            self._notify(f"[green][INFO] 감시 갱신 주기를 {saved}초로 저장했습니다.[/green]")

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
                f"[yellow][INFO] '{keyword}' 와(과) 일치하는 종목이 없습니다.[/yellow]"
            )
            return None

        self.console.print()
        self.console.print(utils.build_search_table(results))
        self.console.print("[dim]0) 취소[/dim]\n")

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
            self._notify("[yellow][INFO] 관심 종목이 비어 있습니다.[/yellow]")
            return None

        rows = [self._row_for(entry) for entry in watchlist]
        self.console.print()
        self.console.print(utils.build_watchlist_table(rows))
        self.console.print("[dim]0) 취소[/dim]\n")

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

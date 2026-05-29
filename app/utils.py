"""Formatting helpers for the rich-based Korean Stock Watch TUI."""

from __future__ import annotations

from typing import Any, Dict, List

from rich.table import Table
from rich.text import Text


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------
def format_won(value: Any) -> str:
    """Format a KRW price as a comma-grouped integer, or 'N/A' when missing."""
    if value is None:
        return "N/A"
    try:
        return f"{int(round(float(value))):,}"
    except (TypeError, ValueError):
        return "N/A"


def change_text(value: Any) -> Text:
    """Return a rich Text for a percentage change, colored by direction.

    Positive -> red, negative -> blue (Korean market convention),
    zero/missing -> dim.
    """
    if value is None:
        return Text("N/A", style="dim")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return Text("N/A", style="dim")

    label = f"{number:+.2f}%"
    if number > 0:
        return Text(label, style="bold red")
    if number < 0:
        return Text(label, style="bold blue")
    return Text(label, style="dim")


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------
def build_watchlist_table(rows: List[Dict[str, Any]]) -> Table:
    """Build a rich Table of watchlist quotes, led by the company name.

    Each row dict has keys: name, code, price, change_percent, high, low.
    """
    table = Table(
        title="관심 종목",
        title_style="bold cyan",
        header_style="bold",
        expand=False,
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("종목명", justify="left", style="bold")
    table.add_column("코드", justify="left", style="dim")
    table.add_column("현재가", justify="right")
    table.add_column("등락률", justify="right")
    table.add_column("고가", justify="right")
    table.add_column("저가", justify="right")

    for index, row in enumerate(rows, start=1):
        table.add_row(
            str(index),
            str(row.get("name", "?")),
            str(row.get("code", "")),
            format_won(row.get("price")),
            change_text(row.get("change_percent")),
            format_won(row.get("high")),
            format_won(row.get("low")),
        )
    return table


def build_search_table(results: List[Dict[str, str]]) -> Table:
    """Build a numbered rich Table of stock search suggestions."""
    table = Table(header_style="bold", expand=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("종목명", justify="left", style="bold cyan")
    table.add_column("코드", justify="left")
    table.add_column("시장", justify="left", style="dim")

    for index, item in enumerate(results, start=1):
        table.add_row(
            str(index),
            item.get("name", "?"),
            item.get("code", ""),
            item.get("market", ""),
        )
    return table

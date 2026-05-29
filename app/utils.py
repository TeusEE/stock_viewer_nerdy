"""Formatting helpers for the rich-based Korean Stock Watch TUI."""

from __future__ import annotations

from typing import Any, Dict, List

from rich.rule import Rule
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
        return Text(label, style="bold rgb(68,153,255)")
    return Text(label, style="dim")


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------
def build_watchlist_table(rows: List[Dict[str, Any]]) -> Table:
    """Build a rich Table of watchlist quotes, led by the company name.

    Each row dict has keys: name, code, price, change_percent, high, low.
    """
    table = Table(
        title="WATCHLIST",
        title_style="bold rgb(255,140,0)",
        header_style="bold rgb(255,165,0)",
        border_style="rgb(80,80,80)",
        expand=False,
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("NAME", justify="left", style="bold")
    table.add_column("CODE", justify="left", style="rgb(170,170,170)")
    table.add_column("PRICE", justify="right")
    table.add_column("CHG%", justify="right")
    table.add_column("HIGH", justify="right")
    table.add_column("LOW", justify="right")

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
    table = Table(header_style="bold rgb(255,165,0)", border_style="rgb(80,80,80)", expand=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("NAME", justify="left", style="bold rgb(255,140,0)")
    table.add_column("CODE", justify="left")
    table.add_column("MKT", justify="left", style="dim")

    for index, item in enumerate(results, start=1):
        table.add_row(
            str(index),
            item.get("name", "?"),
            item.get("code", ""),
            item.get("market", ""),
        )
    return table


# ---------------------------------------------------------------------------
# News section rendering
# ---------------------------------------------------------------------------
def render_news_section(console: Any, news_items: List[Any], loading: bool = False) -> None:
    """Print the news section (divider + items) directly to the given console."""
    console.print(Rule("[bold rgb(255,140,0)]  NEWS  [/bold rgb(255,140,0)]", style="rgb(80,80,80)"))

    if loading and not news_items:
        console.print("[dim italic]  뉴스 로딩 중...[/dim italic]")
        console.print()
        return

    if not news_items:
        console.print("[dim]  No news available.[/dim]")
        console.print()
        return

    for i, item in enumerate(news_items, 1):
        line = Text()
        line.append(f"  {i}  ", style="rgb(100,100,100)")
        line.append(item.title, style="bold white")
        line.append("   ", style="")
        line.append(item.source, style="rgb(255,165,0)")
        line.append("  ", style="")
        line.append(item.published_at, style="dim")
        console.print(line)
        if item.url:
            console.print(f"     [rgb(100,100,100)]{item.url}[/rgb(100,100,100)]")
    console.print()

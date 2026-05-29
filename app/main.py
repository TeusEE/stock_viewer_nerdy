"""Entry point for the Stock Watch interactive TUI.

Running ``run.bat`` (or ``python app/main.py``) launches a full-screen,
menu-driven application where the user can add, edit, delete, and watch
tickers. Tickers are added by searching a company name and picking from
suggested matches.
"""

from __future__ import annotations

import os
import sys

# Ensure UTF-8 output so rich's box-drawing characters and any non-ASCII text
# render on Windows consoles whose default code page (e.g. cp949) cannot encode
# them. errors="replace" guarantees we never crash on an unencodable glyph.
for _stream in (sys.stdout, sys.stderr):
    reconfigure = getattr(_stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

# Allow running this file directly (``python app/main.py``) by ensuring the
# project root is importable so the ``app`` package resolves correctly.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def main() -> int:
    """Launch the interactive TUI."""
    try:
        from app import tui  # noqa: E402 - import after sys.path adjustment
    except ImportError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        print(f"[ERROR] Missing dependency: {missing}")
        print("Run: pip install -r requirements.txt")
        return 1

    try:
        tui.run()
    except KeyboardInterrupt:
        print("\nGoodbye.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

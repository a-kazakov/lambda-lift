from __future__ import annotations

from functools import cache

from rich.console import Console


@cache
def get_console() -> Console:
    return Console()

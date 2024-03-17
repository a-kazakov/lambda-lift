from __future__ import annotations

from functools import cache
from pathlib import Path


@cache
def find_git_root(path: Path) -> Path | None:
    """
    Returns the root of the git repository that the given path is in.
    If the path is not in a git repository, returns None.
    """
    if (path / ".git").exists():
        return path
    parent = path.parent
    if parent == path:
        return None
    return find_git_root(parent)

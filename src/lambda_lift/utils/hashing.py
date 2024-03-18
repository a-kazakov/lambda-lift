from __future__ import annotations

import base64
import hashlib
from pathlib import Path


def get_file_blake2b(path: Path) -> str:
    hasher = hashlib.blake2b()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(32 * 2**10), b""):
            hasher.update(chunk)
    # It is safe to trim trailing == since digest length is constant
    # If need to restore the original digest, == need to be added back
    return base64.urlsafe_b64encode(hasher.digest()).decode().replace("=", "")


def get_string_blake2b(s: str) -> str:
    hasher = hashlib.blake2b()
    hasher.update(s.encode("utf-8"))
    return base64.urlsafe_b64encode(hasher.digest()).decode().replace("=", "")

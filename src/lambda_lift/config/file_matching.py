from __future__ import annotations

import re

TOML_FILE_NAME_RE = re.compile(r"lambda-lift(?:-(.+))?\.toml$")

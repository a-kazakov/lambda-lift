from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

from rich import markup

from lambda_lift.exceptions import UserError
from lambda_lift.utils.cli_tools import rich_print


def run_pip_install(
    *packages: str,
    python: str | None = None,
    target: Path | None,
    platform: str | None = None,
    implementation: str | None = "cp",
    only_binary: str = ":all:",
    upgrade: bool = False,
    no_deps: bool = False,
    requirement: Path | None = None,
) -> None:
    cmd = [
        *((python or sys.executable), "-m", "pip", "install"),
        *(("--target", str(target)) if target else ()),
        *(("--platform", platform) if platform else ()),
        *(("--implementation", implementation) if implementation else ()),
        *(("--only-binary", only_binary) if only_binary else ()),
        *(("--upgrade",) if upgrade else ()),
        *(("--no-deps",) if no_deps else ()),
        *(("--requirement", str(requirement)) if requirement else ()),
        *packages,
    ]
    sp = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    _, stderr = sp.communicate()
    if sp.returncode != 0:
        try:
            target_idx = cmd.index("--target")
            short_cmd = cmd[:target_idx] + cmd[target_idx + 2 :]
        except ValueError:
            short_cmd = cmd
        cmd_str = " ".join(map(shlex.quote, short_cmd))
        rich_print(
            f"[red][bold]pip install failed\n> [/bold]{markup.escape(cmd_str)}\n"
            f"[pink3]{markup.escape(stderr.decode())}"
        )
        raise UserError(f"pip install failed")


def run_pip_freeze(
    path: Path,
    *,
    python: str | None = None,
) -> list[str]:
    cmd = [(python or sys.executable), "-m", "pip", "freeze", "--path", str(path)]
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sp.communicate()
    if sp.returncode != 0:
        cmd_str = " ".join(map(shlex.quote, cmd))
        rich_print(
            f"[red][bold]pip freeze failed\n> [/bold]{markup.escape(cmd_str)}\n"
            f"[pink3]{markup.escape(stderr.decode())}",
        )
        raise UserError(f"pip freeze failed")
    return stdout.decode().splitlines()

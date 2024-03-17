from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

a_files = [
    "a.txt",
    "1/b.txt",
    "1/2/c.txt",
    "nozip.txt",
    "1/nozip.txt",
    "1/nozip/3/x.txt",
]
a_dirs = [
    "a/empty",
    "b/empty",
]

b_files = ["a.txt:v2", "1/2/c.txt", "2/nozip.txt", "3/nozip/3/x.txt", "a/empty/x"]
b_dirs = [
    "c/empty",
]


def init_path(path: Path, files: list[str], dirs: list[str]) -> None:
    for file in files:
        subpath, _, content = file.partition(":")
        file_path = path / subpath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            f"This is a file {file} with content {content}", encoding="utf-8"
        )
    for dir in dirs:
        dir_path = path / dir
        dir_path.mkdir(parents=True, exist_ok=True)


def prepare_test_archives() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        a_raw_path = temp_path / "a_raw"
        b_raw_path = temp_path / "b_raw"
        init_path(a_raw_path, a_files, a_dirs)
        init_path(b_raw_path, b_files, b_dirs)
        a_dest_path = temp_path / "a_dest"
        ab_dest_path = temp_path / "ab_dest"
        a_dest_path.mkdir(parents=True, exist_ok=True)
        ab_dest_path.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(["rsync", "-a", f"{a_raw_path}/", str(a_dest_path)])
        subprocess.check_call(["rsync", "-a", f"{a_raw_path}/", str(ab_dest_path)])
        subprocess.check_call(["rsync", "-a", f"{b_raw_path}/", str(ab_dest_path)])
        subprocess.check_call(
            [
                *("find", str(a_dest_path)),
                *("-name", "*nozip*"),
                *("-exec", "rm", "-r", "{}", "+"),
            ]
        )
        subprocess.check_call(
            [
                *("find", str(ab_dest_path)),
                *("-name", "*nozip*"),
                *("-exec", "rm", "-r", "{}", "+"),
            ]
        )
        output_path = Path(__file__).parent
        subprocess.check_call(
            ["zip", "-r", str(output_path / "a_src.zip"), "./"], cwd=a_raw_path
        )
        subprocess.check_call(
            ["zip", "-r", str(output_path / "b_src.zip"), "./"], cwd=b_raw_path
        )
        subprocess.check_call(
            ["zip", "-r", str(output_path / "a_dest.zip"), "./"], cwd=a_dest_path
        )
        subprocess.check_call(
            ["zip", "-r", str(output_path / "ab_dest.zip"), "./"], cwd=ab_dest_path
        )


if __name__ == "__main__":
    prepare_test_archives()

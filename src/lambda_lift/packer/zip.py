from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, Iterable


def zip_folder(
    source_path: Path,
    dest_path: Path,
    predicate: Callable[[Path], bool] = lambda path: True,
) -> None:
    with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for path in source_path.rglob("*"):
            if predicate(path):
                zip_file.write(path, path.relative_to(source_path))


def make_empty_zip(dest_path: Path) -> None:
    with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED):
        pass


def add_folders_to_zip(
    zip_path: Path,
    folders_to_add: Iterable[Path],
    predicate: Callable[[Path], bool] = lambda path: True,
) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        work_dir = temp_path / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        if zip_path.exists():
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                zip_file.extractall(work_dir)
        for folder in folders_to_add:
            shutil.copytree(folder, work_dir, dirs_exist_ok=True)
        zip_folder(work_dir, zip_path, predicate)

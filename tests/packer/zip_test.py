from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from lambda_lift.packer.zip import make_empty_zip, add_folders_to_zip, zip_folder


class TestZip:
    def _add_file(self, path: Path, content: str | None = None) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or path.name)

    def _describe_directory(self, path: Path) -> str:
        return "\n".join(
            sorted(
                f"{p.relative_to(path)}{'/' if p.is_dir() else ':' + json.dumps(p.read_text())}"
                for p in path.rglob("*")
            )
        )

    def test_create_empty_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "empty.zip"
            make_empty_zip(zip_path)
            assert zipfile.is_zipfile(zip_path)
            assert zipfile.ZipFile(zip_path).namelist() == []

    def test_zip_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            assets_path = Path(__file__).parent / "test_assets" / "zip"
            a_src_path = temp_path / "a_src"
            a_dest_expected_path = temp_path / "a_dest_expected"
            a_dest_actual_path = temp_path / "a_dest_actual"
            a_src_path.mkdir(parents=True, exist_ok=True)
            a_dest_expected_path.mkdir(parents=True, exist_ok=True)
            a_dest_actual_path.mkdir(parents=True, exist_ok=True)
            zipfile.ZipFile(assets_path / "a_src.zip").extractall(a_src_path)
            zipfile.ZipFile(assets_path / "a_dest.zip").extractall(a_dest_expected_path)
            zip_folder(
                source_path=a_src_path,
                dest_path=temp_path / "a.zip",
                predicate=lambda p: not any("nozip" in part for part in p.parts),
            )
            zipfile.ZipFile(temp_path / "a.zip").extractall(a_dest_actual_path)
            a_names = zipfile.ZipFile(temp_path / "a.zip").namelist()
            assert len(a_names) == len(set(a_names))
            a_expected_desc = self._describe_directory(a_dest_expected_path)
            a_actual_desc = self._describe_directory(a_dest_actual_path)
            assert a_actual_desc == a_expected_desc

    def test_add_folders_to_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            assets_path = Path(__file__).parent / "test_assets" / "zip"
            a_src_path = temp_path / "a_src"
            b_src_path = temp_path / "b_src"
            a_dest_expected_path = temp_path / "a_dest_expected"
            ab_dest_expected_path = temp_path / "ab_dest_expected"
            a_dest_actual_path = temp_path / "a_dest_actual"
            ab_dest_actual_path = temp_path / "ab_dest_actual"
            a_src_path.mkdir(parents=True, exist_ok=True)
            b_src_path.mkdir(parents=True, exist_ok=True)
            a_dest_expected_path.mkdir(parents=True, exist_ok=True)
            ab_dest_expected_path.mkdir(parents=True, exist_ok=True)
            a_dest_actual_path.mkdir(parents=True, exist_ok=True)
            ab_dest_actual_path.mkdir(parents=True, exist_ok=True)
            zipfile.ZipFile(assets_path / "a_src.zip").extractall(a_src_path)
            zipfile.ZipFile(assets_path / "b_src.zip").extractall(b_src_path)
            zipfile.ZipFile(assets_path / "a_dest.zip").extractall(a_dest_expected_path)
            zipfile.ZipFile(assets_path / "ab_dest.zip").extractall(
                ab_dest_expected_path
            )
            work_zip = temp_path / "work.zip"
            make_empty_zip(work_zip)
            add_folders_to_zip(
                zip_path=work_zip,
                folders_to_add=[a_src_path],
                predicate=lambda p: not any("nozip" in part for part in p.parts),
            )
            shutil.copy2(work_zip, temp_path / "a.zip")
            add_folders_to_zip(
                zip_path=work_zip,
                folders_to_add=[b_src_path],
                predicate=lambda p: not any("nozip" in part for part in p.parts),
            )
            shutil.copy2(work_zip, temp_path / "ab.zip")
            zipfile.ZipFile(temp_path / "a.zip").extractall(a_dest_actual_path)
            zipfile.ZipFile(temp_path / "ab.zip").extractall(ab_dest_actual_path)
            a_expected_desc = self._describe_directory(a_dest_expected_path)
            a_actual_desc = self._describe_directory(a_dest_actual_path)
            ab_expected_desc = self._describe_directory(ab_dest_expected_path)
            ab_actual_desc = self._describe_directory(ab_dest_actual_path)
            a_names = zipfile.ZipFile(temp_path / "a.zip").namelist()
            assert len(a_names) == len(set(a_names))
            ab_names = zipfile.ZipFile(temp_path / "ab.zip").namelist()
            assert len(ab_names) == len(set(ab_names))
            assert a_actual_desc == a_expected_desc
            assert ab_actual_desc == ab_expected_desc

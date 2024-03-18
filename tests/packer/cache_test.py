from __future__ import annotations

import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest

from lambda_lift.config.enums import Platform
from lambda_lift.config.single_lambda import BuildConfig
from lambda_lift.packer.cache import (
    get_dependencies_zip_path,
    check_dependencies_up_to_date,
    bump_dependencies_cache,
)


@dataclass(frozen=True)
class TestFixture:
    temp_path: Path
    config: MagicMock


@pytest.fixture(name="tf")
def test_fixture() -> Generator[TestFixture, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = MagicMock()
        config.name = "test-name"
        config.build = BuildConfig(
            source_paths=[temp_path / "src1", temp_path / "src2"],
            cache_path=temp_path / "cache",
            requirements_path=temp_path / "requirements.txt",
            destination_path=temp_path / "dest",
            platform=Platform.ARM64,
            python_executable="python3.14",
            ignore_libraries=[],
        )
        yield TestFixture(temp_path, config)


class TestCache:
    def test_get_cache_file(self, tf: TestFixture) -> None:
        deps_zip = get_dependencies_zip_path(tf.config)
        assert deps_zip == tf.temp_path / "cache" / "dependencies_test-name.zip"

    def test_cycle_empty(self, tf: TestFixture) -> None:
        tf.config.build = replace(tf.config.build, requirements_path=None)
        deps_zip = get_dependencies_zip_path(tf.config)
        assert not check_dependencies_up_to_date(tf.config)
        deps_zip.write_bytes(b"test")
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        deps_zip.write_bytes(b"test2")
        assert not check_dependencies_up_to_date(tf.config)
        deps_zip.write_bytes(b"test")
        assert check_dependencies_up_to_date(tf.config)
        deps_zip.unlink()
        assert not check_dependencies_up_to_date(tf.config)

    def test_changing_requirements(self, tf: TestFixture) -> None:
        deps_zip = get_dependencies_zip_path(tf.config)
        tf.config.build.requirements_path.write_text("initial-requirements")
        assert not check_dependencies_up_to_date(tf.config)
        deps_zip.write_bytes(b"test")
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        tf.config.build.requirements_path.write_text("changed-requirements")
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)

    def test_changing_config(self, tf: TestFixture) -> None:
        deps_zip = get_dependencies_zip_path(tf.config)
        tf.config.build.requirements_path.write_text("requirements")
        assert not check_dependencies_up_to_date(tf.config)
        deps_zip.write_bytes(b"test")
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Change source_paths
        tf.config.build = replace(tf.config.build, source_paths=list(reversed(tf.config.build.source_paths)))
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Change requirements_paths
        tf.config.build = replace(tf.config.build, requirements_path=None)
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Change destination_path
        tf.config.build = replace(tf.config.build, destination_path=tf.temp_path / "dest2")
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Change cache_path
        tf.config.build = replace(tf.config.build, cache_path=tf.temp_path / "cache2")
        deps_zip = get_dependencies_zip_path(tf.config)
        deps_zip.write_bytes(b"test")
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Change platform
        tf.config.build = replace(tf.config.build, platform=Platform.X86)
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Change python_executable
        tf.config.build = replace(tf.config.build, python_executable="python3.15")
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Change ignore_libraries
        tf.config.build = replace(tf.config.build, ignore_libraries=["lib1", "lib2"])
        assert not check_dependencies_up_to_date(tf.config)
        bump_dependencies_cache(tf.config)
        assert check_dependencies_up_to_date(tf.config)
        # Ensure reordering ignore_libraries doesn't invalidate cache
        tf.config.build = replace(tf.config.build, ignore_libraries=["lib2", "lib1"])
        assert check_dependencies_up_to_date(tf.config)

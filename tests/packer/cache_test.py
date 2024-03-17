from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest

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
        config.build.cache_path = temp_path / "cache"
        config.build.requirements_path = temp_path / "requirements.txt"
        yield TestFixture(temp_path, config)


class TestCache:
    def test_get_cache_file(self, tf: TestFixture) -> None:
        deps_zip = get_dependencies_zip_path(tf.config)
        assert deps_zip == tf.temp_path / "cache" / "dependencies_test-name.zip"

    def test_cycle_empty(self, tf: TestFixture) -> None:
        tf.config.build.requirements_path = None
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

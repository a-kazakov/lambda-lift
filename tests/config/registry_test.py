from __future__ import annotations

from pathlib import Path

import pytest

from lambda_lift.config.exceptions import NameCollisionException
from lambda_lift.config.registry import ConfigsRegistry


class TestSingleLambdaConfig:
    def _make_registry(self, name: str) -> ConfigsRegistry:
        path = Path(__file__).parent / "test_assets" / "registry" / name
        assert path.exists(), f"Path {path} does not exist"
        return ConfigsRegistry(path)

    def test_normal(self) -> None:
        registry = self._make_registry("normal")
        assert set(registry.names) == {"a", "b"}
        assert registry.get("a").build.cache_path.name == "a"
        assert registry.get("b").build.cache_path.name == "b"
        with pytest.raises(KeyError):
            registry.get("c")

    def test_name_conflict(self) -> None:
        registry = self._make_registry("name_conflict")
        with pytest.raises(NameCollisionException):
            print(list(registry.names))

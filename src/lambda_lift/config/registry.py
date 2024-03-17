from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Generator

from lambda_lift.config.exceptions import NameCollisionException
from lambda_lift.config.file_matching import TOML_FILE_NAME_RE
from lambda_lift.config.parser import SingleLambdaConfigParser
from lambda_lift.config.single_lambda import (
    SingleLambdaConfig,
)


class ConfigsRegistry:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    @property
    def _config_paths(self) -> Generator[Path, None, None]:
        for path in self.root_path.rglob("*.toml"):
            if TOML_FILE_NAME_RE.match(path.name):
                yield path

    @cached_property
    def _parsers(self) -> dict[str, SingleLambdaConfigParser]:
        result: dict[str, SingleLambdaConfigParser] = {}
        for path in self._config_paths:
            parser = SingleLambdaConfigParser(path)
            if parser.name in result:
                raise NameCollisionException(
                    f"Duplicate lambda name {parser.name} in {path} and {result[parser.name].toml_path}"
                )
            result[parser.name] = parser
        return result

    def __len__(self) -> int:
        return len(self._parsers)

    @property
    def names(self) -> Generator[str, None, None]:
        yield from self._parsers.keys()

    def get(self, name: str) -> SingleLambdaConfig:
        return self._parsers[name].parsed

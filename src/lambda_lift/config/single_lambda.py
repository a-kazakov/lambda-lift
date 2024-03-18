from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence, Collection

from lambda_lift.config.enums import Platform
from lambda_lift.config.exceptions import InvalidConfigException
from lambda_lift.utils.hashing import get_string_blake2b


@dataclass(frozen=True)
class BuildConfig:
    source_paths: Sequence[Path]
    requirements_path: Path | None
    destination_path: Path
    cache_path: Path
    platform: Platform
    python_executable: str | None
    ignore_libraries: Collection[str]

    @property
    def data_hash(self) -> str:
        jsonable_object = {
            "source_paths": [str(p) for p in self.source_paths],
            "requirements_path": str(self.requirements_path),
            "destination_path": str(self.destination_path),
            "cache_path": str(self.cache_path),
            "platform": self.platform.value,
            "python_executable": self.python_executable,
            "ignore_libraries": sorted(self.ignore_libraries),
        }
        json_value = json.dumps(jsonable_object, sort_keys=True)
        return get_string_blake2b(json_value)


@dataclass(frozen=True)
class DeploymentConfig:
    region: str
    name: str
    s3_path: tuple[str, str] | None
    aws_profile: str | None


@dataclass(frozen=True)
class SingleLambdaConfig:
    name: str
    build: BuildConfig
    deployments: Mapping[str, DeploymentConfig]
    _toml_path: Path

    def _validate_no_duplicate_lambda_names(self) -> None:
        lambda_names: dict[str, str] = {}
        for profile, deployment in self.deployments.items():
            if deployment.name in lambda_names:
                raise InvalidConfigException(
                    self._toml_path,
                    f"Duplicate lambda name {deployment.name} in deployment profiles "
                    f"{profile} and {lambda_names[deployment.name]}",
                )
            lambda_names[deployment.name] = profile

    def validate(self) -> None:
        self._validate_no_duplicate_lambda_names()

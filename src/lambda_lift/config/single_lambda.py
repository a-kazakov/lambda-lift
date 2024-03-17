from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence, Collection

from lambda_lift.config.enums import Platform
from lambda_lift.config.exceptions import InvalidConfigException


@dataclass(frozen=True)
class BuildConfig:
    source_paths: Sequence[Path]
    requirements_path: Path | None
    destination_path: Path
    cache_path: Path
    platform: Platform
    python_executable: str | None
    ignore_libraries: Collection[str]


@dataclass(frozen=True)
class DeploymentConfig:
    region: str
    name: str
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

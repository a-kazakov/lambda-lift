from __future__ import annotations

import random
import re
import string
import tomllib
from functools import cached_property
from pathlib import Path
from typing import Sequence, Any

from lambda_lift.config.enums import Platform
from lambda_lift.config.exceptions import InvalidConfigException
from lambda_lift.config.file_matching import TOML_FILE_NAME_RE
from lambda_lift.config.single_lambda import (
    SingleLambdaConfig,
    BuildConfig,
    DeploymentConfig,
)
from lambda_lift.utils.git import find_git_root


class SingleLambdaConfigParser:
    def __init__(self, toml_path: Path) -> None:
        self.toml_path = toml_path

    @cached_property
    def toml_object(self) -> dict:
        try:
            return tomllib.loads(self.toml_path.read_text())
        except tomllib.TOMLDecodeError as ex:
            raise InvalidConfigException(
                self.toml_path, f"Failed to parse TOML: {ex}"
            ) from ex

    @cached_property
    def parsed(self) -> SingleLambdaConfig:
        result = SingleLambdaConfig(
            name=self.name,
            build=self.build,
            deployments={
                profile: self.get_deployment(profile)
                for profile in self.deployment_profiles
            },
            _toml_path=self.toml_path,
        )
        result.validate()
        return result

    def get_name(self) -> str:
        if (explicit_name := self.get_toml_string("general", "name")) is not None:
            return explicit_name
        match = TOML_FILE_NAME_RE.match(self.toml_path.name)
        if match is not None:
            if (fn_name := match.group(1)) is not None:
                return fn_name
        return self.toml_path.parent.name

    @cached_property
    def name(self) -> str:
        result = self.get_name()
        allowed_name_regex = r"^[a-zA-Z0-9_\.-]+$"
        if not re.match(allowed_name_regex, result):
            raise InvalidConfigException(
                self.toml_path,
                f"Invalid lambda name {result}. Must consist of english alphanumeric "
                f"characters, underscores, hyphens and dots",
            )
        return result

    # Build

    @property
    def build(self) -> BuildConfig:
        return BuildConfig(
            source_paths=self.source_paths,
            requirements_path=self.requirements_path,
            destination_path=self.destination_path,
            cache_path=self.cache_path,
            platform=self.platform,
            python_executable=self.python_executable,
            ignore_libraries=self.ignore_libraries,
        )

    @property
    def source_paths(self) -> list[Path]:
        source_paths = self.get_toml_list_of_strings("build", "source_paths")
        if source_paths is None:
            raise InvalidConfigException(self.toml_path, "Missing source_paths")
        result = [self.resolve_path(p) for p in source_paths]
        for path in result:
            if not path.exists():
                raise InvalidConfigException(
                    self.toml_path, f"Source path {path} does not exist"
                )
            if not path.is_dir():
                raise InvalidConfigException(
                    self.toml_path, f"Source path {path} is not a directory"
                )
        if not result:
            raise InvalidConfigException(self.toml_path, "source_paths can't be empty")
        return result

    @property
    def requirements_path(self) -> Path | None:
        return self.get_toml_path("build", "requirements_path", must_exist=True)

    @property
    def destination_path(self) -> Path:
        result = self.get_toml_path("build", "destination_path", must_exist=False)
        if result is None:
            raise InvalidConfigException(self.toml_path, "Missing destination_path")
        if result.is_dir():
            raise InvalidConfigException(
                self.toml_path, f"Destination path {result} can't be a directory"
            )
        return result

    @property
    def cache_path(self) -> Path:
        result = self.get_toml_path("build", "cache_path", must_exist=False)
        if result is None:
            raise InvalidConfigException(self.toml_path, "Missing cache_path")
        if result.exists() and not result.is_dir():
            raise InvalidConfigException(
                self.toml_path, f"Cache path {result} must be a directory"
            )
        return result

    @property
    def platform(self) -> Platform:
        platform_str = self.get_toml_string("build", "platform")
        if platform_str is None:
            raise InvalidConfigException(self.toml_path, "Missing platform")
        try:
            return Platform(platform_str.lower())
        except ValueError:
            raise InvalidConfigException(
                self.toml_path, f"Unknown platform {platform_str}"
            )

    @property
    def python_executable(self) -> str | None:
        return self.get_toml_string("build", "python_executable")

    @property
    def ignore_libraries(self) -> set[str]:
        return set(self.get_toml_list_of_strings("build", "ignore_libraries") or ())

    # Deployment

    def get_deployment(self, profile: str) -> DeploymentConfig:
        return DeploymentConfig(
            region=self.get_deployment_region(profile),
            name=self.get_deployment_lambda_name(profile),
            s3_path=self.get_s3_path(profile),
            aws_profile=self.get_deployment_aws_profile(profile),
        )

    @cached_property
    def deployment_profiles(self) -> Sequence[str]:
        profiles = self.get_toml_value("deployment")
        if profiles is None:
            return ()  # No deployment profiles
        if not isinstance(profiles, dict):
            raise InvalidConfigException(self.toml_path, "Invalid deployment section")
        return list(profiles.keys())

    def get_deployment_region(self, profile: str) -> str:
        result = self.get_toml_string("deployment", profile, "region")
        if result is None:
            raise InvalidConfigException(
                self.toml_path, f"Missing region for deployment profile {profile}"
            )
        return result

    def get_deployment_lambda_name(self, profile: str) -> str:
        result = self.get_toml_string("deployment", profile, "name")
        if result is None:
            raise InvalidConfigException(
                self.toml_path, f"Missing lamdda name for deployment profile {profile}"
            )
        return result

    def get_s3_path(self, profile: str) -> tuple[str, str] | None:
        result = self.get_toml_string("deployment", profile, "s3_url")
        if result is None:
            return None
        match = re.match(r"^s3://([^/]+)(?:/(.*)|$)", result)
        if match is None:
            raise InvalidConfigException(
                self.toml_path,
                f"Invalid s3_url for deployment profile {profile}. "
                f"Expected format s3://bucket_name/path/to/deployment/directory/.",
            )
        bucket = match.group(1)
        path = match.group(2) or ""
        if path and not path.endswith("/"):
            path += "/"
        return bucket, path

    def get_deployment_aws_profile(self, profile: str) -> str | None:
        return self.get_toml_string("deployment", profile, "aws_profile")

    # TOML extraction helpers

    def resolve_path(self, value: str) -> Path:
        git_root_ph = "".join(random.choices(string.ascii_lowercase, k=20))
        value = value.format(name=self.name, git_root=git_root_ph)
        if git_root_ph in value:  # Only find git root if there was a placeholder
            git_root = find_git_root(self.toml_path)
            if git_root is None:
                raise InvalidConfigException(
                    self.toml_path, "Failed to find git root for path resolution"
                )
            value = value.replace(git_root_ph, str(git_root.absolute()))
        return self.toml_path.parent / value

    def get_toml_value(self, *path: str) -> Any | None:
        try:
            value = self.toml_object
            for key in path:
                if not isinstance(value, dict):
                    raise InvalidConfigException(
                        self.toml_path,
                        f"Unexpected file structure. Failed to obtain {'.'.join(path)}",
                    )
                value = value[key]
            return value
        except KeyError:
            return None

    def get_toml_string(self, *path: str) -> str | None:
        value = self.get_toml_value(*path)
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidConfigException(
                self.toml_path, f"Expected string at {'.'.join(path)}"
            )
        return value

    def get_toml_path(self, *path_parts: str, must_exist: bool = False) -> Path | None:
        value = self.get_toml_string(*path_parts)
        if value is None:
            return None
        path = self.resolve_path(value)
        if must_exist and not path.exists():
            raise InvalidConfigException(self.toml_path, f"Path {path} does not exist")
        return path

    def get_toml_list_of_strings(self, *path: str) -> list[str] | None:
        value = self.get_toml_value(*path)
        if value is None:
            return None
        if not isinstance(value, list):
            raise InvalidConfigException(
                self.toml_path, f"Expected list of strings at {'.'.join(path)}"
            )
        if not all(isinstance(v, str) for v in value):
            raise InvalidConfigException(
                self.toml_path, f"Expected list of strings at {'.'.join(path)}"
            )
        return value

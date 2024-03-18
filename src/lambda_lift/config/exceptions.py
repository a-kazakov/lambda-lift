from __future__ import annotations

from pathlib import Path

from lambda_lift.exceptions import UserError


class ConfigException(UserError): ...


class InvalidConfigException(ConfigException):
    def __init__(self, toml_path: Path, message: str) -> None:
        super().__init__(f"Invalid config at {toml_path}: {message}")


class NameCollisionException(ConfigException):
    def __init__(self, message: str) -> None:
        super().__init__(message)

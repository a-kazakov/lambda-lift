from __future__ import annotations

from pathlib import Path

from lambda_lift.config.single_lambda import SingleLambdaConfig
from lambda_lift.utils.hashing import get_file_blake2b


def _hash_file(path: Path | None) -> str:
    if path is None:
        return ""
    return get_file_blake2b(path)


def get_dependencies_zip_path(config: SingleLambdaConfig) -> Path:
    config.build.cache_path.mkdir(parents=True, exist_ok=True)
    return config.build.cache_path / f"dependencies_{config.name}.zip"


def check_dependencies_up_to_date(config: SingleLambdaConfig) -> bool:
    """
    Returns True if dependencies zip file exists and doesn't need to be updated.
    False otherwise.
    """
    deps_path = get_dependencies_zip_path(config)
    if not deps_path.exists():
        return False
    hash_path = config.build.cache_path / f"hashes_{config.name}.txt"
    if not hash_path.exists():
        return False
    hash_lines = hash_path.read_text().splitlines()
    if len(hash_lines) != 2:
        return False
    stored_requirements_hash, stored_zip_hash = hash_lines
    actual_requirements_hash = _hash_file(config.build.requirements_path)
    actual_zip_hash = _hash_file(deps_path)
    return (
        stored_requirements_hash == actual_requirements_hash
        and stored_zip_hash == actual_zip_hash
    )


def bump_dependencies_cache(config: SingleLambdaConfig) -> None:
    deps_zip_path = get_dependencies_zip_path(config)
    requirements_hash = _hash_file(config.build.requirements_path)
    zip_hash = _hash_file(deps_zip_path)
    hash_path = config.build.cache_path / f"hashes_{config.name}.txt"
    hash_path.write_text(f"{requirements_hash}\n{zip_hash}")

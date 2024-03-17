from __future__ import annotations

from pathlib import Path

import pytest

from lambda_lift.config.enums import Platform
from lambda_lift.config.exceptions import InvalidConfigException
from lambda_lift.config.parser import SingleLambdaConfigParser
from lambda_lift.config.single_lambda import (
    BuildConfig,
    SingleLambdaConfig,
    DeploymentConfig,
)


class TestParsing:
    def _use_toml_file(self, name: str) -> Path:
        path = Path(__file__).parent / "test_assets" / "parsing" / f"{name}.toml"
        assert path.exists(), f"TOML file {path} does not exist"
        return path

    def _make_parser(self, toml_name: str) -> SingleLambdaConfigParser:
        return SingleLambdaConfigParser(self._use_toml_file(toml_name))

    # Name

    def test_name_extraction_explicit(self) -> None:
        parser = self._make_parser("name/lambda-lift-explicit")
        assert parser.name == "test-name"

    def test_name_extraction_invalid(self) -> None:
        parser = self._make_parser("name/lambda-lift-invalid")
        with pytest.raises(InvalidConfigException):
            parser.name

    def test_name_extraction_file_name(self) -> None:
        parser = self._make_parser("name/lambda-lift-file-name")
        assert parser.name == "file-name"

    def test_name_extraction_parent_dir(self) -> None:
        parser = self._make_parser("name/nested/lambda-lift")
        assert parser.name == "nested"

    # Source paths

    def test_source_paths(self) -> None:
        parser = self._make_parser("source_paths/lambda-lift")
        a, b, c = parser.source_paths
        assert (a / "__init__.py").read_text().strip() == '"a"'
        assert (b / "__init__.py").read_text().strip() == '"b"'
        assert (c / "__init__.py").read_text().strip() == '"c"'

    # Requirements path

    def test_not_specified_requirements(self) -> None:
        parser = self._make_parser("requirements_path/lambda-lift-not-specified")
        assert parser.requirements_path is None

    def test_requirements_normal(self) -> None:
        parser = self._make_parser("requirements_path/lambda-lift-normal")
        assert parser.requirements_path.read_text().strip() == "normal-module"

    def test_requirements_not_exists(self) -> None:
        parser = self._make_parser("requirements_path/lambda-lift-not-exists")
        with pytest.raises(InvalidConfigException):
            parser.requirements_path

    def test_requirements_complex_path(self) -> None:
        parser = self._make_parser("requirements_path/lambda-lift-complex-path")
        assert parser.requirements_path.read_text().strip() == "complex-path-module"

    # Destination path

    def test_destination_path_exists(self) -> None:
        parser = self._make_parser("destination_path/lambda-lift-exists")
        assert parser.destination_path.read_text().strip() == "test-dist"

    def test_destination_path_complex(self) -> None:
        parser = self._make_parser("destination_path/lambda-lift-complex")
        assert parser.destination_path.read_text().strip() == "test-dist"

    def test_destination_path_not_exists(self) -> None:
        parser = self._make_parser("destination_path/lambda-lift-not-exists")
        assert parser.destination_path.name == "lambda.zip"

    def test_destination_path_missing(self) -> None:
        parser = self._make_parser("destination_path/lambda-lift-missing")
        with pytest.raises(InvalidConfigException):
            parser.destination_path

    def test_destination_path_dir(self) -> None:
        parser = self._make_parser("destination_path/lambda-lift-dir")
        with pytest.raises(InvalidConfigException):
            parser.destination_path

    # Cache path

    def test_cache_path_exist(self) -> None:
        parser = self._make_parser("cache_path/lambda-lift-exists")
        assert (parser.cache_path / "marker.txt").read_text().strip() == "test-cache"

    def test_cache_path_complex(self) -> None:
        parser = self._make_parser("cache_path/lambda-lift-complex")
        assert (parser.cache_path / "marker.txt").read_text().strip() == "test-cache"

    def test_cache_path_not_exists(self) -> None:
        parser = self._make_parser("cache_path/lambda-lift-not-exists")
        assert parser.cache_path.name == "non-existing-test-cache"

    def test_cache_path_missing(self) -> None:
        parser = self._make_parser("cache_path/lambda-lift-missing")
        with pytest.raises(InvalidConfigException):
            parser.cache_path

    def test_cache_path_file(self) -> None:
        parser = self._make_parser("cache_path/lambda-lift-file")
        with pytest.raises(InvalidConfigException):
            parser.cache_path

    # Platform

    def test_platform_x86(self) -> None:
        parser = self._make_parser("platform/lambda-lift-x86")
        assert parser.platform == Platform.X86

    def test_platform_arm64(self) -> None:
        parser = self._make_parser("platform/lambda-lift-arm64")
        assert parser.platform == Platform.ARM64

    def test_platform_missing(self) -> None:
        parser = self._make_parser("platform/lambda-lift-missing")
        with pytest.raises(InvalidConfigException):
            parser.platform

    def test_platform_uppercase(self) -> None:
        parser = self._make_parser("platform/lambda-lift-uppercase")
        assert parser.platform == Platform.ARM64

    def test_platform_unknown(self) -> None:
        parser = self._make_parser("platform/lambda-lift-unknown")
        with pytest.raises(InvalidConfigException):
            parser.platform

    # Python executable

    def test_python_executable_specified(self) -> None:
        parser = self._make_parser("python_executable/lambda-lift-specified")
        assert parser.python_executable == "python3.14"

    def test_python_executable_missing(self) -> None:
        parser = self._make_parser("python_executable/lambda-lift-missing")
        assert parser.python_executable is None

    # Ignore libraries

    def test_ignore_libraries_specified(self) -> None:
        parser = self._make_parser("ignore_libraries/lambda-lift-specified")
        assert parser.ignore_libraries == {"a", "b", "c"}

    def test_ignore_libraries_missing(self) -> None:
        parser = self._make_parser("ignore_libraries/lambda-lift-missing")
        assert parser.ignore_libraries == set()

    # Deployment

    def test_deployment_list_profiles(self) -> None:
        parser = self._make_parser("deployment/lambda-lift-normal")
        assert sorted(parser.deployment_profiles) == ["profile1", "profile2"]

    def test_deployment_extract_region(self) -> None:
        parser = self._make_parser("deployment/lambda-lift-normal")
        assert parser.get_deployment_region("profile1") == "us-west-1"
        assert parser.get_deployment_region("profile2") == "us-west-2"

    def test_deployment_extract_lambda_name(self) -> None:
        parser = self._make_parser("deployment/lambda-lift-normal")
        assert parser.get_deployment_lambda_name("profile1") == "lambda1"
        assert parser.get_deployment_lambda_name("profile2") == "lambda2"

    def test_deployment_extract_aws_profile(self) -> None:
        parser = self._make_parser("deployment/lambda-lift-normal")
        assert parser.get_deployment_aws_profile("profile1") is None
        assert parser.get_deployment_aws_profile("profile2") == "aws_p2"

    def test_deployment_missing_region(self) -> None:
        parser = self._make_parser("deployment/lambda-lift-missing-region")
        with pytest.raises(InvalidConfigException):
            parser.get_deployment_region("profile1")

    def test_deployment_missing_lambda_name(self) -> None:
        parser = self._make_parser("deployment/lambda-lift-missing-name")
        with pytest.raises(InvalidConfigException):
            parser.get_deployment_lambda_name("profile1")

    # General

    def test_full_file(self) -> None:
        toml_id = "general/lambda-lift-full"
        config = self._make_parser(toml_id).parsed
        base_path = self._use_toml_file(toml_id).parent
        repo_root = Path(__file__).parent.parent.parent
        expected_config = SingleLambdaConfig(
            name="sample-name",
            build=BuildConfig(
                source_paths=[base_path / "sample_src"],
                requirements_path=base_path / "requirements.txt",
                destination_path=repo_root / "temp" / "sample-name.zip",
                cache_path=repo_root / "temp" / "cache" / "sample-name",
                platform=Platform.ARM64,
                python_executable="python3.14",
                ignore_libraries={"numpy"},
            ),
            deployments={
                "dev": DeploymentConfig(
                    region="us-west-2", name="dev-lambda-name", aws_profile="dev-push"
                ),
                "prod": DeploymentConfig(
                    region="us-west-2",
                    name="prod-lambda-name",
                    aws_profile="prod-push",
                ),
            },
            _toml_path=self._use_toml_file(toml_id),
        )
        assert config == expected_config

    def test_broken_toml(self) -> None:
        parser = self._make_parser("general/lambda-lift-broken")
        with pytest.raises(InvalidConfigException):
            parser.toml_object

    # Duplicate lambdas

    def test_duplicate_lambda(self) -> None:
        parser = self._make_parser("duplicate_lambdas/lambda-lift")
        with pytest.raises(InvalidConfigException):
            parser.parsed

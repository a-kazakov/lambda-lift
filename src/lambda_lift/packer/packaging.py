from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from lambda_lift.config.enums import Platform
from lambda_lift.config.single_lambda import SingleLambdaConfig
from lambda_lift.packer.cache import (
    get_dependencies_zip_path,
    check_dependencies_up_to_date,
    bump_dependencies_cache,
)
from lambda_lift.packer.pip import run_pip_install, run_pip_freeze
from lambda_lift.packer.zip import make_empty_zip, zip_folder, add_folders_to_zip
from lambda_lift.utils.cli_tools import get_console, rich_print


def _get_pip_platform(platform: Platform) -> str:
    return {
        Platform.ARM64: "manylinux2014_aarch64",
        Platform.X86: "manylinux2014_x86_64",
    }[platform]


def _zip_predicate(path: Path) -> bool:
    return (
        not any(p.endswith(".dist-info") for p in path.parts)
        and not any(p.endswith(".pyc") for p in path.parts)
        and "__pycache__" not in path.parts
    )


def build_dependencies_zip_file(
    config: SingleLambdaConfig,
) -> None:
    if config.build.requirements_path is None:
        make_empty_zip(get_dependencies_zip_path(config))
        return
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Step 1: Install from requirements.txt
        step_1_path = temp_path / "step_1"
        step_1_path.mkdir()
        run_pip_install(
            target=step_1_path,
            platform=_get_pip_platform(config.build.platform),
            python=config.build.python_executable,
            requirement=config.build.requirements_path,
        )
        # Step 2: Obtain list of filtered packages
        filtered_packages: list[str] = []
        for pkg in run_pip_freeze(step_1_path, python=config.build.python_executable):
            if pkg.startswith("-e "):
                pkg = pkg.removeprefix("-e ")
            prefix, _, _ = pkg.partition("==")
            if prefix not in config.build.ignore_libraries:
                filtered_packages.append(pkg)
        # Step 3: Install only filtered packages
        step_3_path = temp_path / "step_3"
        step_3_path.mkdir()
        run_pip_install(
            *filtered_packages,
            target=step_3_path,
            platform=_get_pip_platform(config.build.platform),
            python=config.build.python_executable,
            no_deps=True,
        )
        # Step 4: Pack everything into a lambda zip
        zip_folder(
            source_path=step_3_path,
            dest_path=get_dependencies_zip_path(config),
            predicate=_zip_predicate,
        )


def add_source_code(config: SingleLambdaConfig) -> None:
    config.build.destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        get_dependencies_zip_path(config),
        config.build.destination_path,
    )
    add_folders_to_zip(
        zip_path=config.build.destination_path,
        folders_to_add=config.build.source_paths,
        predicate=_zip_predicate,
    )


def package_lambda(config: SingleLambdaConfig) -> None:
    with get_console().status(f"[blue]Packaging {config.name}...") as status:
        if not check_dependencies_up_to_date(config):
            base_status = status.status
            status.update(f"[blue]Packaging {config.name} (working on dependencies)...")
            build_dependencies_zip_file(config)
            bump_dependencies_cache(config)
            status.update(base_status)
        add_source_code(config)
    rich_print(f"[blue]Packaging of {config.name} completed")

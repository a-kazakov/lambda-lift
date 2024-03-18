from __future__ import annotations

import sys
import time
from pathlib import Path

import click

from lambda_lift.config.registry import ConfigsRegistry
from lambda_lift.deployment.aws import deploy_lambda
from lambda_lift.exceptions import UserError
from lambda_lift.packer.packaging import package_lambda
from lambda_lift.utils.cli_tools import get_console, rich_print


@click.command()
@click.argument("lambdas", nargs=-1, type=str)
@click.option(
    "--deploy",
    multiple=True,
    type=str,
    help="Deploy to AWS. This flag accepts a list of profiles to deploy to.",
)
@click.option(
    "--deploy-all",
    multiple=True,
    type=str,
    help="Deploy all lambdas to AWS. This flag accepts a list of profiles to deploy to.",
)
def cli_main(lambdas: list[str], deploy: list[str], deploy_all: list[str]) -> None:
    start_time = time.monotonic()
    try:
        # Validate arguments
        if not lambdas and deploy:
            raise click.BadOptionUsage("--deploy", "You must specify lambdas to deploy")
        if deploy and deploy_all:
            raise click.BadOptionUsage(
                "--deploy-all", "You cannot specify both --deploy and --deploy-all"
            )
        deploy_profiles = deploy or deploy_all
        # Load configs
        with get_console().status("[blue]Reading configs..."):
            registry = ConfigsRegistry(Path.cwd())
            rich_print(
                f"[yellow]Found {len(registry)} config{'s' if len(registry) != 1 else ''}"
            )
            for lambda_name in lambdas:
                if lambda_name not in registry.names:
                    raise click.NoSuchOption(
                        "lambdas",
                        f"No such lambda: {lambda_name}",
                        possibilities=list(registry.names),
                    )
            all_lambdas = lambdas or list(registry.names)
        # Build all lambdas
        for lambda_name in all_lambdas:
            package_lambda(registry.get(lambda_name))
        # Deploy as needed
        for profile in deploy_profiles:
            for lambda_name in all_lambdas:
                deploy_lambda(registry.get(lambda_name), profile)
        # Print stats
        elapsed_time = time.monotonic() - start_time
        rich_print(f"[green]Completed in {elapsed_time:.2f} seconds")
    except UserError as ex:
        rich_print(f"[red]{str(ex)}")
        sys.exit(2)
    except Exception:
        get_console().print_exception(show_locals=False)
        sys.exit(1)

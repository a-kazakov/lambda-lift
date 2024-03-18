from __future__ import annotations

import boto3

from lambda_lift.config.single_lambda import SingleLambdaConfig
from lambda_lift.utils.cli_tools import get_console, rich_print


def deploy_lambda(config: SingleLambdaConfig, profile: str) -> None:
    deploy_config = config.deployments.get(profile)
    with get_console().status(
        f"[purple]Deploying {config.name} ({profile}) to AWS -> {deploy_config.name}..."
    ):
        if deploy_config is None:
            rich_print(
                f"[amber]Deployment profile {profile} is not set for lambda {config.name}, skipping"
            )
            return
        client = boto3.Session(
            profile_name=deploy_config.aws_profile,
            region_name=deploy_config.region,
        ).client("lambda")
        client.update_function_code(
            FunctionName=deploy_config.name,
            ZipFile=config.build.destination_path.read_bytes(),
        )
    rich_print(f"[purple]Deployed {config.name} ({profile}) to AWS")

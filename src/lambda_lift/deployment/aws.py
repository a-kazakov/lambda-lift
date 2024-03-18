from __future__ import annotations

from pathlib import Path

import boto3
import botocore.exceptions

from lambda_lift.config.single_lambda import SingleLambdaConfig
from lambda_lift.deployment.exceptions import AwsError
from lambda_lift.utils.cli_tools import get_console, rich_print
from lambda_lift.utils.hashing import get_file_blake2b


def _deploy_lambda_via_direct(
    *,
    session: boto3.Session,
    lambda_name: str,
    zip_path: Path,
) -> None:
    client = session.client("lambda")
    try:
        client.update_function_code(
            FunctionName=lambda_name,
            ZipFile=zip_path.read_bytes(),
        )
    except botocore.exceptions.ClientError as ex:
        raise AwsError(f"Failed to deploy {lambda_name} to AWS: {ex}") from ex


def _deploy_lambda_via_s3(
    *,
    session: boto3.Session,
    lambda_name: str,
    zip_path: Path,
    s3_bucket: str,
    s3_key_prefix: str,
) -> None:
    s3_client = session.client("s3")
    file_hash = get_file_blake2b(zip_path)
    s3_key = s3_key_prefix + f"{file_hash}.zip"
    try:
        try:
            s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
        except botocore.exceptions.ClientError as ex:
            if ex.response["Error"]["Code"] != "404":
                raise
            with zip_path.open("rb") as f:
                s3_client.upload_fileobj(f, s3_bucket, s3_key)
    except botocore.exceptions.ClientError as ex:
        raise AwsError(f"Failed to upload code for {lambda_name} to S3: {ex}") from ex
    lambda_client = session.client("lambda")
    try:
        lambda_client.update_function_code(
            FunctionName=lambda_name,
            S3Bucket=s3_bucket,
            S3Key=s3_key,
        )
    except botocore.exceptions.ClientError as ex:
        raise AwsError(f"Failed to deploy {lambda_name} to AWS: {ex}") from ex


def deploy_lambda(config: SingleLambdaConfig, profile: str) -> None:
    deploy_config = config.deployments.get(profile)
    if deploy_config is None:
        rich_print(
            f"[amber]Deployment profile {profile} is not set for lambda {config.name}, skipping"
        )
        return
    with get_console().status(
        f"[purple]Deploying {config.name} ({profile}) to AWS -> {deploy_config.name}..."
    ):
        session = boto3.Session(
            profile_name=deploy_config.aws_profile,
            region_name=deploy_config.region,
        )
        if deploy_config.s3_path is not None:
            s3_bucket, s3_key_prefix = deploy_config.s3_path
            _deploy_lambda_via_s3(
                session=session,
                lambda_name=deploy_config.name,
                zip_path=config.build.destination_path,
                s3_bucket=s3_bucket,
                s3_key_prefix=s3_key_prefix,
            )
        else:
            _deploy_lambda_via_direct(
                session=session,
                lambda_name=deploy_config.name,
                zip_path=config.build.destination_path,
            )
    rich_print(
        f"[purple]Deployed {config.name} ({profile}) to AWS -> {deploy_config.name}"
    )

# Lambda lift

Lambda Lift, is a streamlined building and deployment tool designed for developers and teams managing multiple Python-based AWS Lambda functions. Lambda Lift simplifies the packaging and deployment process, making it easier for you to focus on building and improving your applications.

## Key Features

* Designed to support multiple Lambda functions in a single repository
* Utilize TOML files for easy and clear configuration of each deployed Lambda function
* Supports deployment profiles (e.g., deployment to dev/staging/prod)

## Limitations

* Works with Python-based Lambdas only
* Requires Python 3.10 or above
* Requires a Lambda to exist at the time of deployment; this tool doesn't create Lambda functions

## Getting started

Install the tool via PIP

```bash
pip install lambda-lift
```

Then use it from the command line

```bash
lambda-lift  # Build all lambdas
lambda-lift my-awesome-lambda my-another-lambda  # Build only lambda functions specified
lambda-lift my-awseome-lambda --deploy staging  # Deploy the lambda using the staging profile
lambda-lift --deploy-all prod  # Deploy all lambdas using the prod profile
```

## Configuration

The configuration is done via TOML files. The files must be named either as `lambda-lift.toml`, or `lambda-lift-<name>.toml` (`<name>` could be anything). The configuration files can be placed anywhere in the repository - for example, all toml files in one location, or each toml file in the directory of the lambda it configures.

### Toml example

```toml
[general]

# A name of your lambda to be used for selective building
# If not specified, the <name> part of the toml file name will be used
# If not specified and the toml file name doesn't have the <name> part, then the directory 
# name of the toml file will be used
name = "my-lambda"


[build]
# List all source paths that need to be included relative to the toml file
source_paths = ["src", "../common/src"]

# Path to the requirements file relative to the toml file. 
# If not specified, no requirements will be installed
requirements_path = "requirements.txt"

# Location of the resulting zip file relative to the toml file; must be specified
# git_root and name templates are available for all paths within the toml file
destination_path = "{git_root}/dist/{name}.zip"

# Location of the cache folder relative to the toml file; must be sprcified
# Cache folder speeds up updating lambdas by reusing the dependencies that haven't changed
cache_path = "deploy/prod/cache"

# The platform for which the lambda will be built. Must be either arm64 or x86, and must be specified.
platform = "arm64"

# The python executable to be used for fetching the dependencies. This parameter allows using 
# different python versions for different lambdas. If not specified, the same python executable
# that is used to run the lambda-lift will be used.
python_executable = "python3.12"

# The libraries which shouldn't be added to the resulting ZIP file
# Generally, these should be the libraries that are provided by AWS Lambda
# You can find a list of these libraries here: https://gist.github.com/gene1wood/4a052f39490fae00e0c3
# (check comments at the link)
ignore_libraries = [
    "awslambdaric",
    "boto3",
    "botocore",
    "jmespath",
    "pip",
    "python-dateutil",
    "s3transfer",
    "setuptools",
    "simplejson",
    "six",
    "urllib3",
    "numpy",
]

# Each deployment profile is a separate section in the toml file
# The name of the section is the name of the deployment profile
# The deployemnt profile is specified by the user when deploying the lambda
# For example: `lambda-lift my-lambda --deploy prod`

[deployment.prod]

# The AWS region where the lambda will be deployed. Must be specified.
region = "us-west-1"

# The name of the lambda in AWS. It must exist at the time of deployment.
# If it is not, first create it by using AWS console, AWS CLI, or a different tool
# such as Pulimi or Terraform.
name = "my-lambda-prod" 

# The name of the AWS profile to be used for deployment (optional)
aws_profile = "my-profile"

[deployment.staging]
region = "us-west-1"
name = "my-lambda-staging"
aws_profile = "my-profile"
```
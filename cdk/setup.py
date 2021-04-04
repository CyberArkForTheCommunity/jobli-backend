from setuptools import setup, find_packages
from os import getenv


def get_micro():
    build_number: str = getenv("BUILD_NUMBER", "0")
    branch_name: str = getenv("BRANCH_NAME", "None")
    micro = build_number
    if branch_name != "master" and not branch_name.startswith("release"):
        micro = f"dev{build_number}+{''.join(e for e in branch_name if e.isalnum()).lower()}"
    return micro


setup(
    name="jobli-service-cdk",
    version=f"1.0.{get_micro()}",
    description="AWS CDK stack for jobli service",
    url="https://github.com/cyberark-everest/jobli-service",
    author="Everest",
    author_email="everest@cyberark.com",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    classifiers=[
        "Development Status :: 1 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    install_requires=[
        "aws-cdk.aws-iam>=1.51.0",
        "aws-cdk.aws-kms>=1.51.0",
        "aws-cdk.aws-s3>=1.51.0",
        "aws-cdk.core>=1.51.0",
        "aws-cdk.aws-cognito>=1.51.0",
        "aws-cdk.aws_apigateway>=1.51.0",
        "infra-logging<1.2.0",
        "infra-tracing<1.3.0",
        "stack-utils<1.2.0"
    ],
    python_requires=">=3.8",
)

#!/usr/bin/env python
# pylint: disable = print-used
import os
import boto3
from jobli_service_cdk.service_stack.jobli_construct import get_stack_name


def destroy():
    """
    Asynchronously delete the stack
    """
    # if 'PROJECT_DIR' environment variable is not defined, this value will be used to search for local GIT repo
    if 'PROJECT_DIR' not in os.environ:
        project_path: str = os.path.abspath(os.path.dirname(__file__))
        os.environ['PROJECT_DIR'] = project_path
    client = boto3.client("cloudformation")
    stack_name = get_stack_name()
    print(f"Deleting stack {stack_name}")
    client.delete_stack(StackName=f"{stack_name}")


if __name__ == '__main__':
    destroy()

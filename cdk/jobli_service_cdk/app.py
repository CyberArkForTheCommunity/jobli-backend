#!/usr/bin/env python3

# pylint: disable=invalid-name,ungrouped-imports

import os
from aws_cdk import core
from boto3 import client, session
from jobli_service_cdk.service_stack.jobli_stack import JobliStack
from stack_utils.stack_name import get_stack_name
from jobli_service_cdk.service_stack.constants import BASE_NAME

account = client('sts').get_caller_identity()['Account']
region = session.Session().region_name
app = core.App()
jobli_stack = JobliStack(
    app, get_stack_name(BASE_NAME),
    env=core.Environment(account=os.environ.get("AWS_DEFAULT_ACCOUNT", account), region=os.environ.get("AWS_DEFAULT_REGION", region)))

app.synth()

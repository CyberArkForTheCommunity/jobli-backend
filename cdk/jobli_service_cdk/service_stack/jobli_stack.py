import getpass

from aws_cdk import core
from aws_cdk.core import Tags

from stack_utils.stack_name import get_stack_name
from stack_utils.stack_tags import add_stack_tags

from jobli_service_cdk.service_stack.jobli_construct import JobliServiceEnvironment, BASE_NAME

from .auth_construct import JobliAuth


class JobliStack(core.Stack):

    # pylint: disable=redefined-builtin
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        add_stack_tags(self, service='jobli-service')

        self.jobli_auth = JobliAuth(self, f"{get_stack_name(BASE_NAME)}Auth")
        self.jobli_service_env = JobliServiceEnvironment(self, "Service", self.jobli_auth.user_pool.user_pool_arn)

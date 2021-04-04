import getpass

from aws_cdk import core

from jobli_service_cdk.service_stack.jobli_construct import JobliServiceEnvironment, get_stack_name

from .auth_construct import JobliAuth


class JobliStack(core.Stack):

    # pylint: disable=redefined-builtin
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.jobli_auth = JobliAuth(self, f"{get_stack_name()}Auth")
        self.jobli_service_env = JobliServiceEnvironment(self, "Service", self.jobli_auth.user_pool.user_pool_arn)

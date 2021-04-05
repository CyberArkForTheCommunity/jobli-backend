from aws_cdk import core, aws_cognito
from aws_cdk.aws_cognito import AuthFlow, CognitoDomainOptions, StringAttribute
from jobli_service_cdk.service_stack.jobli_construct import get_stack_name

## A place holder for your cdk assets demonstrated by the cognito cdk stack


class JobliAuth(core.Construct):

    # pylint: disable=redefined-builtin,invalid-name
    def __init__(self, scope: core.Construct, id: str) -> None:
        super().__init__(scope, id)

        self.user_pool = aws_cognito.UserPool(self, "UsersPool", sign_in_aliases=aws_cognito.SignInAliases(username=True), custom_attributes={"user_type": StringAttribute(max_len=256, mutable=True)})
        cfn_user_pool: aws_cognito.CfnUserPool = self.user_pool.node.default_child
        cfn_user_pool.policies = aws_cognito.CfnUserPool.PoliciesProperty(
            password_policy=aws_cognito.CfnUserPool.PasswordPolicyProperty(minimum_length=8, require_lowercase=False, require_numbers=False,
                                                                           require_symbols=False, require_uppercase=False))
        
        self.user_pool.add_domain("JobliUserPoolDomain", cognito_domain=CognitoDomainOptions(domain_prefix=get_stack_name().lower()))
        user_pool_output = core.CfnOutput(self, id="JobliUserPoolID", value=self.user_pool.user_pool_id)
        user_pool_output.override_logical_id("JobliUserPoolID")
        user_pool_arn_output = core.CfnOutput(self, id="JobliUserPoolArn", value=self.user_pool.user_pool_arn)
        user_pool_arn_output.override_logical_id("JobliUserPoolArn")

        self.user_pool_client = aws_cognito.UserPoolClient(
            self,
            "PoolClient",
            user_pool=self.user_pool,
            auth_flows=AuthFlow(admin_user_password=False, user_password=True),
        )
        auth_client_output = core.CfnOutput(self, id="AuthClientID", value=self.user_pool_client.user_pool_client_id)
        auth_client_output.override_logical_id("AuthClientID")

import os
from aws_cdk.core import CfnParameter
from aws_cdk import core, aws_cognito
from aws_cdk.aws_cognito import  (CfnUserPool, UserPool, AuthFlow, UserPoolClient, OAuthSettings, OAuthFlows, UserPoolIdentityProviderGoogle,
                                  CognitoDomainOptions, StringAttribute, OAuthScope, UserPoolClientIdentityProvider, AttributeMapping, ProviderAttribute)
from jobli_service_cdk.service_stack.jobli_construct import get_stack_name

## A place holder for your cdk assets demonstrated by the cognito cdk stack


class JobliAuth(core.Construct):

    # pylint: disable=redefined-builtin,invalid-name
    def __init__(self, scope: core.Construct, id: str) -> None:
        super().__init__(scope, id)

        google_client_id = CfnParameter(scope, 'GoogleClientId', no_echo=True, default=os.getenv('GOOGLE_CLIENT_ID'))
        google_client_secret = CfnParameter(scope, 'GoogleClientSecret', no_echo=True, default=os.getenv('GOOGLE_CLIENT_SECRET'))

        self.user_pool = UserPool(self, "UsersPool", sign_in_aliases=aws_cognito.SignInAliases(username=True), custom_attributes={"user_type": StringAttribute(max_len=256, mutable=True)})
        cfn_user_pool: CfnUserPool = self.user_pool.node.default_child
        cfn_user_pool.policies = CfnUserPool.PoliciesProperty(
            password_policy=CfnUserPool.PasswordPolicyProperty(minimum_length=8, require_lowercase=False, require_numbers=False,
                                                                           require_symbols=False, require_uppercase=False))
        
        self.user_pool.add_domain("JobliUserPoolDomain", cognito_domain=CognitoDomainOptions(domain_prefix=get_stack_name().lower()))
        user_pool_output = core.CfnOutput(self, id="JobliUserPoolID", value=self.user_pool.user_pool_id)
        user_pool_output.override_logical_id("JobliUserPoolID")
        user_pool_arn_output = core.CfnOutput(self, id="JobliUserPoolArn", value=self.user_pool.user_pool_arn)
        user_pool_arn_output.override_logical_id("JobliUserPoolArn")

        self.user_pool_identity_provider = UserPoolIdentityProviderGoogle(self, "JobliGoogleIdentityProvider", 
                                                                            client_id=google_client_id.value_as_string,
                                                                            client_secret=google_client_secret.value_as_string,
                                                                            scopes=['profile', 'email', 'openid'], user_pool=self.user_pool,
                                                                            attribute_mapping=AttributeMapping(email=ProviderAttribute.GOOGLE_EMAIL))
        self.user_pool_client = UserPoolClient(
            self,
            "PoolClient",
            user_pool=self.user_pool,
            auth_flows=AuthFlow(admin_user_password=True, user_password=True), 
            o_auth=OAuthSettings(callback_urls=['https://google.com'], 
            flows=OAuthFlows(authorization_code_grant=True, implicit_code_grant=True), 
            scopes=[OAuthScope.PHONE, OAuthScope.EMAIL, OAuthScope.OPENID, OAuthScope.COGNITO_ADMIN]),
            supported_identity_providers=[UserPoolClientIdentityProvider.GOOGLE] 
            )
        
        self.user_pool_client.node.add_dependency(self.user_pool_identity_provider)

        auth_client_output = core.CfnOutput(self, id="AuthClientID", value=self.user_pool_client.user_pool_client_id)
        auth_client_output.override_logical_id("AuthClientID")

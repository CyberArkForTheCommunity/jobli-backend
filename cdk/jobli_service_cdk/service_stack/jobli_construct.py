import os
import sys

from jobli_service_cdk.service_stack.constants import BASE_NAME
from aws_cdk.aws_apigateway import Resource
from aws_cdk import (core, aws_iam as iam, aws_apigateway as apigw, aws_lambda as _lambda)

from stack_utils.stack_name import get_stack_name
from stack_utils.policies import get_tracing_policy
# add the root package to the path
from infra_tracing import consts

sys.path.append(os.getcwd())


class JobliServiceEnvironment(core.Construct):
    _API_HANDLER_LAMBDA_MEMORY_SIZE = 128
    _API_HANDLER_LAMBDA_TIMEOUT = 10
    _LAMBDA_ASSET_DIR = ".build/service"

    # pylint: disable=redefined-builtin,invalid-name
    def __init__(self, scope: core.Construct, id: str, user_pool_arn: str) -> None:
        super().__init__(scope, id)

        core.CfnOutput(self, id="StackName", value=get_stack_name(BASE_NAME))

        self.service_role = iam.Role(
            self, "JobliServiceRole", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"), inline_policies={
                "JobliServicePolicy":
                    iam.PolicyDocument(statements=[
                        iam.PolicyStatement(actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                                            resources=["arn:aws:logs:*:*:*"], effect=iam.Effect.ALLOW),
                        iam.PolicyStatement(actions=["ssm:Describe*", "ssm:Get*", "ssm:List*"], resources=["arn:aws:ssm:*:*:*"],
                                            effect=iam.Effect.ALLOW),
                    ]),
                "TracingPolicy":
                    get_tracing_policy()
            })
        role_output = core.CfnOutput(self, id="JobliServiceRoleArn", value=self.service_role.role_arn)
        role_output.override_logical_id("JobliServiceRoleArn")

        self.rest_api: apigw.LambdaRestApi = apigw.RestApi(self, "jobli-rest-api", rest_api_name="Jobli Rest API",
                                                           description="This service handles jobli")
        endpoint_output = core.CfnOutput(self, id="JobliApiGw", value=self.rest_api.url)
        endpoint_output.override_logical_id("JobliApiGw")
        self.api_authorizer: apigw.CfnAuthorizer = self.__create_api_authorizer(user_pool_arn=user_pool_arn, api=self.rest_api)
        jobli_resource: apigw.Resource = self.rest_api.root.add_resource("jobli")
        self.__add_create_lambda_integration(jobli_resource, user_pool_arn)
        jobli_name_resource = jobli_resource.add_resource("{name}")
        self.__add_update_lambda_integration(jobli_name_resource, user_pool_arn)
        self.__add_get_lambda_integration(jobli_name_resource, user_pool_arn)

    # pylint: disable = no-value-for-parameter
    def __add_create_lambda_integration(self, jobli: Resource, user_pool_arn: str):
        lambda_function = _lambda.Function(
            self,
            'CreateJobli',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
            handler='service.handler.create_jobli',
            role=self.service_role,
            environment={
                "JOBLI_USER_POOL_ARN": user_pool_arn,
                consts.TRACING_FILTER_KEY: "JobliService",
            },
        )
        self.__add_resource_method(
            resource=jobli,
            http_method="POST",
            integration=apigw.LambdaIntegration(handler=lambda_function),  # POST /jobli
            authorizer=self.api_authorizer,
        )

    def __add_update_lambda_integration(self, jobli_name: Resource, user_pool_arn: str):
        lambda_function = _lambda.Function(
            self,
            'UpdateJobli',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
            handler='service.handler.update_jobli',
            role=self.service_role,
            environment={
                "JOBLI_USER_POOL_ARN": user_pool_arn,
                consts.TRACING_FILTER_KEY: "JobliService",
            },
        )
        self.__add_resource_method(
            resource=jobli_name,
            http_method="PUT",
            integration=apigw.LambdaIntegration(handler=lambda_function),  # PUT /jobli/{name}
            authorizer=self.api_authorizer,
        )

    def __add_get_lambda_integration(self, jobli_name: Resource, user_pool_arn: str):
        lambda_function = _lambda.Function(
            self,
            'GetJobli',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
            handler='service.handler.get_jobli',
            role=self.service_role,
            environment={
                "JOBLI_USER_POOL_ARN": user_pool_arn,
                consts.TRACING_FILTER_KEY: "JobliService",
            },
        )
        self.__add_resource_method(
            resource=jobli_name,
            http_method="GET",
            integration=apigw.LambdaIntegration(handler=lambda_function),  # GET /jobli/{name}
            authorizer=self.api_authorizer,
        )

    def __create_api_authorizer(self, user_pool_arn: str, api: apigw.RestApi) -> apigw.CfnAuthorizer:
        authorizer = apigw.CfnAuthorizer(scope=self, name="JobliApiAuth", id="JobliApiAuth", type="COGNITO_USER_POOLS",
                                         provider_arns=[user_pool_arn], rest_api_id=api.rest_api_id,
                                         identity_source="method.request.header.Authorization")
        return authorizer

    @staticmethod
    def __add_resource_method(resource: apigw.Resource, http_method: str, integration: apigw.LambdaIntegration,
                              authorizer: apigw.CfnAuthorizer) -> None:
        method = resource.add_method(
            http_method=http_method,
            integration=integration,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )
        method_resource: apigw.Resource = method.node.find_child("Resource")
        method_resource.add_property_override("AuthorizerId", {"Ref": authorizer.logical_id})

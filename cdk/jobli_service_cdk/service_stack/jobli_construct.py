import os
import sys
from aws_cdk.aws_s3 import HttpMethods
from git import Repo

from jobli_service_cdk.service_stack.constants import BASE_NAME
from aws_cdk.aws_apigateway import Resource
from aws_cdk import (core, aws_iam as iam, aws_apigateway as apigw, aws_lambda as _lambda, aws_dynamodb)

sys.path.append(os.getcwd())


def read_git_branch() -> str:

    project_path = os.environ['PROJECT_DIR']
    # load git branch name in development environment
    repo = Repo(project_path)
    return repo.active_branch.name


def get_stack_name() -> str:
    branch_name = read_git_branch()
    # remove special characters from branch name
    branch_name = ''.join(e for e in branch_name if e.isalnum()).capitalize()
    stack_name: str = f"{BASE_NAME}{branch_name}"
    # stack_name: str = f"{getpass.getuser().capitalize().replace('.','')}{BASE_NAME}{branch_name}"
    return stack_name


class JobliServiceEnvironment(core.Construct):
    _API_HANDLER_LAMBDA_MEMORY_SIZE = 128
    _API_HANDLER_LAMBDA_TIMEOUT = 10
    _LAMBDA_ASSET_DIR = ".build/service"

    # pylint: disable=redefined-builtin,invalid-name
    def __init__(self, scope: core.Construct, id: str, user_pool_arn: str) -> None:
        super().__init__(scope, id)

        core.CfnOutput(self, id="StackName", value=get_stack_name())

        self.service_role = iam.Role(
            self, "JobliServiceRole", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"), inline_policies={
                "JobliServicePolicy":
                    iam.PolicyDocument(statements=[
                        iam.PolicyStatement(actions=["cognito-idp:AdminUpdateUserAttributes"],
                                            resources=[user_pool_arn], effect=iam.Effect.ALLOW)
                    ])
            }, managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")])

        role_output = core.CfnOutput(self, id="JobliServiceRoleArn", value=self.service_role.role_arn)
        role_output.override_logical_id("JobliServiceRoleArn")

        self.table = aws_dynamodb.Table(
            self,
            'jobli-employees',
            partition_key=aws_dynamodb.Attribute(name="id", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.RETAIN
        )
        self.table.grant_read_write_data(self.service_role)

        self.employers_table = aws_dynamodb.Table(
            self,
            'jobli-employers',
            partition_key=aws_dynamodb.Attribute(name="id", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.RETAIN
        )
        self.employers_table.grant_read_write_data(self.service_role)

        self.jobs_table = aws_dynamodb.Table(
            self,
            'jobli-jobs',
            partition_key=aws_dynamodb.Attribute(name="id", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.RETAIN
        )
        self.jobs_table.grant_read_write_data(self.service_role)

        self.rest_api: apigw.LambdaRestApi = apigw.RestApi(self, "jobli-rest-api", rest_api_name="Jobli Rest API",
                                                           description="This service handles jobli")
        endpoint_output = core.CfnOutput(self, id="JobliApiGw", value=self.rest_api.url)
        endpoint_output.override_logical_id("JobliApiGw")
        self.api_authorizer: apigw.CfnAuthorizer = self.__create_api_authorizer(user_pool_arn=user_pool_arn, api=self.rest_api)
        api_resource: apigw.Resource = self.rest_api.root.add_resource("api")
        jobli_resource: apigw.Resource = self.rest_api.root.add_resource("jobli")
        jobli_employers_resource: apigw.Resource = jobli_resource.add_resource("employers")

        # Add the employer lambdas / APIGW's
        self.__add_lambda_integration("CreateJobliEmployer", "service.lambdas.employer.create_employer.create_employer", HttpMethods.POST, jobli_employers_resource, user_pool_arn)
        self.__add_lambda_integration("GetJobliEmployers", "service.lambdas.employer.get_employers.get_employers", HttpMethods.GET, jobli_employers_resource, user_pool_arn)
        jobli_employers_by_id_resource: apigw.Resource = jobli_employers_resource.add_resource("{employer_id}")
        self.__add_lambda_integration("UpdateJobliEmployer", "service.lambdas.employer.update_employer.update_employer", HttpMethods.PUT, jobli_employers_by_id_resource, user_pool_arn)
        self.__add_lambda_integration("GetJobliEmployer", "service.lambdas.employer.get_employer_by_id.get_employer_by_id", HttpMethods.GET, jobli_employers_by_id_resource, user_pool_arn)

        self.__add_create_lambda_integration(jobli_resource, user_pool_arn)
        jobli_name_resource = jobli_resource.add_resource("{name}")
        self.__add_update_lambda_integration(jobli_name_resource, user_pool_arn)
        self.__add_get_lambda_integration(jobli_name_resource, user_pool_arn)

        # set user type method
        users_resource: apigw.Resource = api_resource.add_resource("users")
        update_type: apigw.Resource = users_resource.add_resource("type")
        self.__add_lambda_integration("SetUserType", "service.handler.set_user_type", HttpMethods.POST, update_type, user_pool_arn)

    # pylint: disable = no-value-for-parameter
    def __add_lambda_integration(self, _id: str, lambda_handler: str, http_method: HttpMethods, jobli: Resource, user_pool_arn: str):
        lambda_function = _lambda.Function(
            self,
            _id,
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
            handler=lambda_handler,
            role=self.service_role,
            environment={
                "JOBLI_USER_POOL_ARN": user_pool_arn
            },
        )
        self.__add_resource_method(
            resource=jobli,
            http_method=http_method.value,
            integration=apigw.LambdaIntegration(handler=lambda_function),  # POST /jobli
            authorizer=self.api_authorizer,
        )

    def __add_create_lambda_integration(self, jobli: Resource, user_pool_arn: str):
        lambda_function = _lambda.Function(
            self,
            'CreateJobli',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
            handler='service.handler.create_jobli',
            role=self.service_role,
            environment={
                "JOBLI_USER_POOL_ARN": user_pool_arn
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
                "JOBLI_USER_POOL_ARN": user_pool_arn
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
                "JOBLI_USER_POOL_ARN": user_pool_arn
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

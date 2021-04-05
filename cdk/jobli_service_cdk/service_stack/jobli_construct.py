import os
import sys
from git import Repo
import getpass

from jobli_service_cdk.service_stack.constants import BASE_NAME
from aws_cdk.aws_apigateway import Resource
from aws_cdk.core import Duration, CfnResource
from aws_cdk.aws_iam import Role
from aws_cdk.aws_lambda import Function
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
                        iam.PolicyStatement(actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                                            resources=["arn:aws:logs:*:*:*"], effect=iam.Effect.ALLOW)
                    ])
            })

        role_output = core.CfnOutput(self, id="JobliServiceRoleArn", value=self.service_role.role_arn)
        role_output.override_logical_id("JobliServiceRoleArn")

        self.table_job_seekers = aws_dynamodb.Table(
            self,
            'jobli-job-seeker',
            partition_key=aws_dynamodb.Attribute(name="pk", type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name="sk", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.RETAIN
        )

        self.table_job_seekers.add_global_secondary_index(partition_key=aws_dynamodb.Attribute(name='gsi1Pk', type=aws_dynamodb.AttributeType.STRING),
           sort_key=aws_dynamodb.Attribute(name='gsi1Sk', type=aws_dynamodb.AttributeType.STRING),
           index_name='GSI1')

        core.CfnOutput(self, id="JobSeekersTableName", value=self.table_job_seekers.table_name)

        self.table_job_seekers.grant_read_write_data(self.service_role)

        self.rest_api: apigw.LambdaRestApi = apigw.RestApi(self, "jobli-rest-api", rest_api_name="Jobli Rest API",
                                                           description="This service handles jobli API for job seekers and employers")


        endpoint_output = core.CfnOutput(self, id="JobliApiGw", value=self.rest_api.url)
        endpoint_output.override_logical_id("JobliApiGwURL")


        self.api_authorizer: apigw.CfnAuthorizer = self.__create_api_authorizer(user_pool_arn=user_pool_arn, api=self.rest_api)


        self._environment = {
            "STACK_NAME": get_stack_name(),
            "JOBLI_USER_POOL_ARN": user_pool_arn,
            "JOB_SEEKERS_TABLE_NAME": self.table_job_seekers.table_name
        }

        api_resource: apigw.Resource = self.rest_api.root.add_resource("api")
        seeker_resource: apigw.Resource = api_resource.add_resource("seekers")
        seeker_id_resource: apigw.Resource = seeker_resource.add_resource("{id}")
        seeker_id_profile: apigw.Resource = seeker_id_resource.add_resource("profile")

        self.__add_lambda_api(lambda_name='CreateSeekerProfile', handler_method='service.handler.create_seeker_profile',
                              resource=seeker_id_profile, http_method="POST", member_name="add_seeker_profile_api_lambda")

    def __create_api_authorizer(self, user_pool_arn: str, api: apigw.RestApi) -> apigw.CfnAuthorizer:
        authorizer = apigw.CfnAuthorizer(scope=self, name="JobliApiAuth", id="JobliApiAuth", type="COGNITO_USER_POOLS",
                                         provider_arns=[user_pool_arn], rest_api_id=api.rest_api_id,
                                         identity_source="method.request.header.Authorization")
        return authorizer

    def __add_lambda_api(self, lambda_name: str, handler_method: str, resource: Resource, http_method: str, member_name: str,
                         description: str = ''):
        new_api_lambda = \
            self.__create_lambda_function(lambda_name=f'{lambda_name}Api',
                                          handler=handler_method,
                                          role=self.service_role,
                                          environment=self._environment,
                                          description=description)

        self.__add_resource_method(resource=resource, http_method=http_method,
                                   integration=apigw.LambdaIntegration(handler=new_api_lambda))

        cfn_res: CfnResource = new_api_lambda.node.default_child
        cfn_res.override_logical_id(lambda_name)

        setattr(self, member_name, new_api_lambda)

    def __create_lambda_function(self, lambda_name: str, handler: str, role: Role, environment: dict, description: str = '',
                                 timeout: Duration = Duration.seconds(_API_HANDLER_LAMBDA_TIMEOUT)) -> Function:

        return _lambda.Function(self, lambda_name, runtime=_lambda.Runtime.PYTHON_3_8, code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
                                handler=handler, role=role, retry_attempts=0, environment=environment, timeout=timeout,
                                memory_size=self._API_HANDLER_LAMBDA_MEMORY_SIZE, description=description)

    @staticmethod
    def __add_resource_method(resource: apigw.Resource, http_method: str, integration: apigw.LambdaIntegration) -> None:
        resource.add_method(http_method=http_method, integration=integration)

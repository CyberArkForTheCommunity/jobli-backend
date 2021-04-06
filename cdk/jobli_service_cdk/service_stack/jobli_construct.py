import os
import sys
from aws_cdk.aws_s3 import HttpMethods
from git import Repo

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
                        iam.PolicyStatement(actions=["cognito-idp:AdminUpdateUserAttributes"],
                                            resources=[user_pool_arn], effect=iam.Effect.ALLOW)
                    ])
            }, managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")])

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

        job_seekers_table_output = core.CfnOutput(self, id="JobSeekersTableName", value=self.table_job_seekers.table_name)
        job_seekers_table_output.override_logical_id('JobSeekersTableName')

        self.table_job_seekers.grant_read_write_data(self.service_role)

        self.rest_api: apigw.LambdaRestApi = apigw.RestApi(self, "jobli-rest-api", rest_api_name="Jobli Rest API",
                                                           description="This service handles jobli API for job seekers and employers")


        endpoint_output = core.CfnOutput(self, id="JobliApiGw", value=self.rest_api.url)
        endpoint_output.override_logical_id("JobliApiGw")


        self.api_authorizer: apigw.CfnAuthorizer = self.__create_api_authorizer(user_pool_arn=user_pool_arn, api=self.rest_api)


        self._environment = {
            "STACK_NAME": get_stack_name(),
            "JOBLI_USER_POOL_ARN": user_pool_arn,
            "JOB_SEEKERS_TABLE_NAME": self.table_job_seekers.table_name
        }

        api_resource: apigw.Resource = self.rest_api.root.add_resource("api")
        #jobli_resource: apigw.Resource = self.rest_api.root.add_resource("jobli")
        #self.__add_create_lambda_integration(jobli_resource, user_pool_arn)
        #jobli_name_resource = jobli_resource.add_resource("{name}")
        #self.__add_update_lambda_integration(jobli_name_resource, user_pool_arn)
        #self.__add_get_lambda_integration(jobli_name_resource, user_pool_arn)

        seekers_resource: apigw.Resource = api_resource.add_resource("seekers")
        seeker_id_resource: apigw.Resource = seekers_resource.add_resource("{id}")
        seekers_id_profile: apigw.Resource = seeker_id_resource.add_resource("profile")
        seekers_id_answers: apigw.Resource = seeker_id_resource.add_resource("answers")
        self.__add_lambda_api(lambda_name='CreateOrUpdateSeekerProfileWithId',
                              handler_method='service.handler.create_or_update_seeker_profile_with_id',
                              resource=seekers_id_profile, http_method="PUT",
                              member_name="add_seeker_profile_with_id_api_lambda")

        self.__add_lambda_api(lambda_name='GetSeeekerWithId',
                              handler_method='service.handler.get_seeker_profile_with_id',
                              resource=seekers_id_profile, http_method="GET",
                              member_name="get_seeker_with_id_api_lambda")

        self.__add_lambda_api(lambda_name='AddSeeekerAnswersWithId',
                              handler_method='service.handler.add_seeker_answers_with_id',
                              resource=seekers_id_answers, http_method="POST",
                              member_name="add_seeker_answers_with_id_api_lambda")


        #Without id

        seeker_resource: apigw.Resource = api_resource.add_resource("seeker")


        seeker_id_profile: apigw.Resource = seeker_resource.add_resource("profile")
        self.__add_lambda_api(lambda_name='CreateOrUpdateSeekerProfile', handler_method='service.handler.create_or_update_seeker_profile',
                              resource=seeker_id_profile, http_method="PUT", member_name="add_seeker_profile_api_lambda")

        self.__add_lambda_api(lambda_name='GetSeeeker',
                              handler_method='service.handler.get_seeker_profile',
                              resource=seeker_id_profile, http_method="GET",
                              member_name="get_seeker_api_lambda")

        seeker_answers: apigw.Resource = seeker_resource.add_resource("answers")
        self.__add_lambda_api(lambda_name='AddSeekerAnswers', handler_method='service.handler.add_seeker_answers',
                              resource=seeker_answers, http_method="POST", member_name="add_seeker_answers_api_lambda")

        seeker_experience: apigw.Resource = seeker_resource.add_resource("experience")
        self.__add_lambda_api(lambda_name='AddSeekerExperience', handler_method='service.handler.add_seeker_experience',
                              resource=seeker_experience, http_method="POST", member_name="add_seeker_experience_api_lambda")

        seeker_languages: apigw.Resource = seeker_resource.add_resource("languages")
        self.__add_lambda_api(lambda_name='AddSeekerLanguages', handler_method='service.handler.add_seeker_languages',
                              resource=seeker_languages, http_method="POST", member_name="add_seeker_languages_api_lambda")

        seeker_summary: apigw.Resource = seeker_resource.add_resource("summary")
        self.__add_lambda_api(lambda_name='GetSeeekerSummary',
                              handler_method='service.handler.get_seeker_summary',
                              resource=seeker_summary, http_method="GET",
                              member_name="get_seeker_summary_api_lambda")

        self.__add_lambda_api(lambda_name='ListSeeekers',
                              handler_method='service.handler.list_seekers',
                              resource=seeker_resource, http_method="GET",
                              member_name="list_seekers_api_lambda")

        # seeker_resource: apigw.Resource = api_resource.add_resource("seekers")
        # seeker_id_resource: apigw.Resource = seeker_resource.add_resource("{id}")
        #
        # seeker_id_profile: apigw.Resource = seeker_id_resource.add_resource("profile")
        # self.__add_lambda_api(lambda_name='CreateSeekerProfile', handler_method='service.handler.create_seeker_profile',
        #                       resource=seeker_id_profile, http_method="POST", member_name="add_seeker_profile_api_lambda")
        #
        # seeker_id_answers: apigw.Resource = seeker_id_resource.add_resource("answers")
        # self.__add_lambda_api(lambda_name='AddSeekerAnswers', handler_method='service.handler.add_seeker_answers',
        #                       resource=seeker_id_answers, http_method="POST", member_name="add_seeker_answers_api_lambda")
        #
        # seeker_id_experience: apigw.Resource = seeker_id_resource.add_resource("experience")
        # self.__add_lambda_api(lambda_name='AddSeekerExperience', handler_method='service.handler.add_seeker_experience',
        #                       resource=seeker_id_experience, http_method="POST", member_name="add_seeker_experience_api_lambda")

        # set user type method
        users_resource: apigw.Resource = api_resource.add_resource("users")
        update_type: apigw.Resource = users_resource.add_resource("type")
        self.__add_lambda_integration("SetUserType", "service.handler.set_user_type", HttpMethods.POST, update_type,
                                      user_pool_arn)

        # pylint: disable = no-value-for-parameter

    def __add_lambda_integration(self, _id: str, lambda_handler: str, http_method: HttpMethods, jobli: Resource,
                                 user_pool_arn: str):
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
                "JOBLI_USER_POOL_ARN": user_pool_arn
            },
        )
        self.__add_resource_method(
            resource=jobli,
            http_method="POST",
            integration=apigw.LambdaIntegration(handler=lambda_function),  # POST /jobli
            authorizer=self.api_authorizer,
        )


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
                                   integration=apigw.LambdaIntegration(handler=new_api_lambda),
                                   authorizer=self.api_authorizer)

        cfn_res: CfnResource = new_api_lambda.node.default_child
        cfn_res.override_logical_id(lambda_name)

        setattr(self, member_name, new_api_lambda)

    def __create_lambda_function(self, lambda_name: str, handler: str, role: Role, environment: dict, description: str = '',
                                 timeout: Duration = Duration.seconds(_API_HANDLER_LAMBDA_TIMEOUT)) -> Function:

        return _lambda.Function(self, lambda_name, runtime=_lambda.Runtime.PYTHON_3_8, code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
                                handler=handler, role=role, retry_attempts=0, environment=environment, timeout=timeout,
                                memory_size=self._API_HANDLER_LAMBDA_MEMORY_SIZE, description=description)

    # @staticmethod
    # def __add_resource_method(resource: apigw.Resource, http_method: str, integration: apigw.LambdaIntegration,
    #                           authorizer: apigw.CfnAuthorizer) -> None:
    #     method = resource.add_method(
    #         http_method=http_method,
    #         integration=integration,
    #         authorization_type=apigw.AuthorizationType.COGNITO,
    #     )
    #     method_resource: apigw.Resource = method.node.find_child("Resource")
    #     method_resource.add_property_override("AuthorizerId", {"Ref": authorizer.logical_id})

    @staticmethod
    def __add_resource_method(resource: apigw.Resource, http_method: str, integration: apigw.LambdaIntegration,
                              authorizer: apigw.CfnAuthorizer) -> None:
        method = resource.add_method(
            http_method=http_method,
            integration=integration
        )
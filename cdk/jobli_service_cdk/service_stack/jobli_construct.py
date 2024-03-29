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
                        iam.PolicyStatement(actions=["cognito-idp:AdminUpdateUserAttributes",
                                                     "cognito-idp:AdminDeleteUserAttributes"],
                                            resources=[user_pool_arn], effect=iam.Effect.ALLOW)
                    ])
            }, managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")])

        role_output = core.CfnOutput(self, id="JobliServiceRoleArn", value=self.service_role.role_arn)
        role_output.override_logical_id("JobliServiceRoleArn")

        self.employers_table = aws_dynamodb.Table(
            self,
            'jobli-employers',
            partition_key=aws_dynamodb.Attribute(name="employer_id", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.RETAIN
        )
        self.employers_table.grant_read_write_data(self.service_role)

        self.jobs_table = aws_dynamodb.Table(
            self,
            'jobli-jobs',
            partition_key=aws_dynamodb.Attribute(name="job_id", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.RETAIN
        )
        self.jobs_table.add_global_secondary_index(
            partition_key=aws_dynamodb.Attribute(name='employer_id', type=aws_dynamodb.AttributeType.STRING),
            index_name='second-index')
        self.jobs_table.grant_read_write_data(self.service_role)

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

        self.environment = {
            "STACK_NAME": get_stack_name(),
            "JOBLI_USER_POOL_ARN": user_pool_arn,
            "JOB_SEEKERS_TABLE_NAME": self.table_job_seekers.table_name,
            "EMPLOYERS_TABLE_NAME": self.employers_table.table_name,
            "JOBS_TABLE_NAME": self.jobs_table.table_name
        }

        # Base Resources API
        api_resource: apigw.Resource = self.rest_api.root.add_resource("api")
        users_resource: apigw.Resource = api_resource.add_resource("users")
        update_type: apigw.Resource = users_resource.add_resource("type")

        # Employers API
        jobli_employers_resource: apigw.Resource = api_resource.add_resource("employers")
        jobli_employers_by_id_resource: apigw.Resource = jobli_employers_resource.add_resource("{employer_id}")
        jobli_jobs_resource: apigw.Resource = jobli_employers_by_id_resource.add_resource("jobs")
        jobli_job_id_resource: apigw.Resource = jobli_jobs_resource.add_resource("{job_id}")

        # Seekers API
        seekers_resource: apigw.Resource = api_resource.add_resource("seekers")
        seekers_id_resource: apigw.Resource = seekers_resource.add_resource("{id}")
        seekers_id_profile: apigw.Resource = seekers_id_resource.add_resource("profile")
        seekers_id_answers: apigw.Resource = seekers_id_resource.add_resource("answers")

        # Seekers REST's
        self.__add_lambda_api(lambda_name='CreateOrUpdateSeekerProfileWithId',
                              handler_method='service.handler.create_or_update_seeker_profile_with_id',
                              resource=seekers_id_profile, http_method=HttpMethods.PUT,
                              member_name="add_seeker_profile_with_id_api_lambda")

        self.__add_lambda_api(lambda_name='GetSeeekerWithId',
                              handler_method='service.handler.get_seeker_profile_with_id',
                              resource=seekers_id_profile, http_method=HttpMethods.GET,
                              member_name="get_seeker_with_id_api_lambda")

        self.__add_lambda_api(lambda_name='AddSeeekerAnswersWithId',
                              handler_method='service.handler.add_seeker_answers_with_id',
                              resource=seekers_id_answers, http_method=HttpMethods.POST,
                              member_name="add_seeker_answers_with_id_api_lambda")


        #Without id

        seeker_resource: apigw.Resource = api_resource.add_resource("seeker")

        self.__add_lambda_api(lambda_name='DeleteSeeeker',
                              handler_method='service.handler.delete_seeker',
                              resource=seeker_resource, http_method=HttpMethods.DELETE,
                              member_name="delete_seeker_api_lambda")

        seeker_profile: apigw.Resource = seeker_resource.add_resource("profile")
        self.__add_lambda_api(lambda_name='CreateOrUpdateSeekerProfile', handler_method='service.handler.create_or_update_seeker_profile',
                              resource=seeker_profile, http_method=HttpMethods.PUT, member_name="add_seeker_profile_api_lambda")

        self.__add_lambda_api(lambda_name='GetSeeeker',
                              handler_method='service.handler.get_seeker_profile',
                              resource=seeker_profile, http_method=HttpMethods.GET,
                              member_name="get_seeker_api_lambda")

        relevant_jobs: apigw.Resource = seeker_resource.add_resource("relevant-jobs")
        self.__add_lambda_api(lambda_name='GetRelevantJobs',
                              handler_method='service.handler.search_relevant_jobs',
                              resource=relevant_jobs, http_method=HttpMethods.GET,
                              member_name="search_relevant_jobs_api_lambda")

        seeker_answers: apigw.Resource = seeker_resource.add_resource("answers")
        self.__add_lambda_api(lambda_name='AddSeekerAnswers', handler_method='service.handler.add_seeker_answers',
                              resource=seeker_answers, http_method=HttpMethods.POST, member_name="add_seeker_answers_api_lambda")

        seeker_experience: apigw.Resource = seeker_resource.add_resource("experience")
        self.__add_lambda_api(lambda_name='AddSeekerExperience', handler_method='service.handler.add_seeker_experience',
                              resource=seeker_experience, http_method=HttpMethods.POST, member_name="add_seeker_experience_api_lambda")

        seeker_languages: apigw.Resource = seeker_resource.add_resource("languages")
        self.__add_lambda_api(lambda_name='AddSeekerLanguages', handler_method='service.handler.add_seeker_languages',
                              resource=seeker_languages, http_method=HttpMethods.PUT, member_name="add_seeker_languages_api_lambda")

        seeker_summary: apigw.Resource = seeker_resource.add_resource("summary")
        self.__add_lambda_api(lambda_name='GetSeeekerSummary',
                              handler_method='service.handler.get_seeker_summary',
                              resource=seeker_summary, http_method=HttpMethods.GET,
                              member_name="get_seeker_summary_api_lambda")

        relevant_seekers_resource: apigw.Resource = api_resource.add_resource("list-relevant-seekers")
        self.__add_lambda_api(lambda_name='ListRelevantSeeekers',
                              handler_method='service.handler.list_relevant_seekers',
                              resource=relevant_seekers_resource, http_method=HttpMethods.GET,
                              member_name="list_relevant_seekers_api_lambda")

        self.__add_lambda_api(lambda_name='ListSeekerExperience',
                              handler_method='service.handler.list_seeker_experience',
                              resource=seeker_experience, http_method=HttpMethods.GET,
                              member_name="list_seeker_experience_api_lambda")

        seeker_experience_id: apigw.Resource = seeker_experience.add_resource("{experience_id}")
        self.__add_lambda_api(lambda_name='GetSeekerExperienceById',
                              handler_method='service.handler.get_seeker_experience_by_id',
                              resource=seeker_experience_id, http_method=HttpMethods.GET,
                              member_name="get_seeker_experience_by_id_api_lambda")


        # Employers REST's
        self.__add_lambda_api(lambda_name='CreateJobliEmployer', handler_method='service.lambdas.employer.create_employer.create_employer',
                              resource=jobli_employers_resource, http_method=HttpMethods.POST, member_name="create_jobli_employer")
        self.__add_lambda_api(lambda_name='GetJobliEmployers', handler_method='service.lambdas.employer.get_employers.get_employers',
                              resource=jobli_employers_resource, http_method=HttpMethods.GET, member_name="get_jobli_employers")
        self.__add_lambda_api(lambda_name='UpdateJobliEmployer', handler_method='service.lambdas.employer.update_employer.update_employer',
                              resource=jobli_employers_by_id_resource, http_method=HttpMethods.PUT, member_name="update_employer")
        self.__add_lambda_api(lambda_name='GetJobliEmployer', handler_method='service.lambdas.employer.get_employer_by_id.get_employer_by_id',
                              resource=jobli_employers_by_id_resource, http_method=HttpMethods.GET, member_name="get_jobli_employer_by_id")
        self.__add_lambda_api(lambda_name='AddJobliEmployerJob', handler_method='service.lambdas.employer.add_employer_job.add_employer_job',
                              resource=jobli_jobs_resource, http_method=HttpMethods.POST, member_name="add_employer_job")
        self.__add_lambda_api(lambda_name='GetJobliEmployerJobs', handler_method='service.lambdas.employer.get_employer_jobs.get_employer_jobs',
                              resource=jobli_jobs_resource, http_method=HttpMethods.GET, member_name="get_employer_jobs")
        self.__add_lambda_api(lambda_name='GetJobliEmployerJob',
                              handler_method='service.lambdas.employer.get_employer_job_by_id.get_employer_job_by_id',
                              resource=jobli_job_id_resource, http_method=HttpMethods.GET, member_name="get_employer_jobs")
        self.__add_lambda_api(lambda_name='UpdateJobliEmployerJobAnswers',
                              handler_method='service.lambdas.employer.update_employer_job_answers.update_employer_job_answers',
                              resource=jobli_job_id_resource, http_method=HttpMethods.PUT, member_name="update_employer_job_answers")

        # User Type REST
        self.__add_lambda_api(lambda_name="SetUserType", handler_method="service.handler.set_user_type",
                              resource=update_type, http_method=HttpMethods.POST, member_name="set_user_type")

    # pylint: disable = no-value-for-parameter
    def __add_lambda_api(self, lambda_name: str, handler_method: str, resource: Resource, http_method: HttpMethods, member_name: str,
                         description: str = ''):
        new_api_lambda = \
            self.__create_lambda_function(lambda_name=f'{lambda_name}Api',
                                          handler=handler_method,
                                          role=self.service_role,
                                          environment=self.environment,
                                          description=description)

        self.__add_resource_method(resource=resource, http_method=http_method.value,
                                   integration=apigw.LambdaIntegration(handler=new_api_lambda),
                                   authorizer=self.api_authorizer)

        cfn_res: CfnResource = new_api_lambda.node.default_child
        cfn_res.override_logical_id(lambda_name)

        setattr(self, member_name, new_api_lambda)

    def __create_api_authorizer(self, user_pool_arn: str, api: apigw.RestApi) -> apigw.CfnAuthorizer:
        authorizer = apigw.CfnAuthorizer(scope=self, name="JobliApiAuth", id="JobliApiAuth", type="COGNITO_USER_POOLS",
                                         provider_arns=[user_pool_arn], rest_api_id=api.rest_api_id,
                                         identity_source="method.request.header.Authorization")
        return authorizer

    def __create_lambda_function(self, lambda_name: str, handler: str, role: Role, environment: dict, description: str = '',
                                 timeout: Duration = Duration.seconds(_API_HANDLER_LAMBDA_TIMEOUT)) -> Function:

        return _lambda.Function(self, lambda_name, runtime=_lambda.Runtime.PYTHON_3_8, code=_lambda.Code.from_asset(self._LAMBDA_ASSET_DIR),
                                handler=handler, role=role, retry_attempts=0, environment=environment, timeout=timeout,
                                memory_size=self._API_HANDLER_LAMBDA_MEMORY_SIZE, description=description)

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
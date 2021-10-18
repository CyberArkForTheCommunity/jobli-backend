import json
import uuid
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from typing import List

import boto3
from aws_lambda_context import LambdaContext
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from botocore.exceptions import ClientError
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from mypy_boto3_cognito_idp.type_defs import AttributeTypeTypeDef
from pydantic import ValidationError

from service.common.exceptions import NotFoundError
from service.common.utils import get_env_or_raise
from service.dao.job_seeker_answers_repository import job_seeker_answers_repository, SearchResult
from service.dao.job_seeker_experience_repository import job_seeker_experience_repository
from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.jobs_repository import jobs_repository
from service.dao.model.experience import Experience
from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto
from service.dtos.job_seeker_experience_dto import JobSeekerExperienceDto
from service.dtos.job_seeker_profile_dto import JobSeekerProfileDto
from service.dtos.jobli_dto import JobliDto
from service.dtos.jobli_dto import UpdateUserTypeDto
from service.lambdas.employer.constants import EmployerConstants
from service.models.employer.employer_job import JobSearchResult
from service.models.job_seeker_resource import JobSeekerResource
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.models.jobli import Jobli

logger = Logger()


# PUT /api/seeker/profile
@logger.inject_lambda_context(log_event=True)
def create_or_update_seeker_profile(event: dict, context: LambdaContext) -> dict:
    try:
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        profile_dto: JobSeekerProfileDto = JobSeekerProfileDto.parse_raw(event["body"])

        try:
            # try to update job seeker. If does not exists, create it.
            job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(user_id))
            return __update_seeker_profile(profile_dto=profile_dto, job_seeker=job_seeker)
        except NotFoundError as err:
            return __create_seeker_profile(user_id=user_id, profile_dto=profile_dto)

    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


def __create_seeker_profile(user_id: str, profile_dto: JobSeekerProfileDto) -> dict:
    # convert to model

    birth_date = datetime(year=profile_dto.birth_year, month=profile_dto.birth_month, day=profile_dto.birth_day)

    job_seeker: JobSeeker = JobSeeker(id=user_id,
                                      full_name=profile_dto.full_name,
                                      birth_date=Decimal(birth_date.timestamp() * 1000),
                                      email=profile_dto.email,
                                      address=profile_dto.address,
                                      about_me=profile_dto.about_me,
                                      hobbies=profile_dto.hobbies,
                                      job_ambitions=profile_dto.job_ambitions)

    job_seeker_repository.create(job_seeker)

    # return resource
    return _build_response(http_status=HTTPStatus.OK, body="")


def __update_seeker_profile(profile_dto: JobSeekerProfileDto, job_seeker: JobSeeker) -> dict:
    # convert to model
    job_seeker.full_name = profile_dto.full_name

    birth_date = datetime(year=profile_dto.birth_year, month=profile_dto.birth_month, day=profile_dto.birth_day)
    job_seeker.birth_date = int(birth_date.timestamp()) * 1000
    job_seeker.email = profile_dto.email
    job_seeker.address = profile_dto.address
    job_seeker.about_me = profile_dto.about_me
    job_seeker.hobbies = profile_dto.hobbies
    job_seeker.job_ambitions = profile_dto.job_ambitions

    job_seeker_repository.update(job_seeker)

    # return resource
    return _build_response(http_status=HTTPStatus.OK, body="")


# GET /api/seeker/profile
@logger.inject_lambda_context(log_event=True)
def get_seeker_profile(event: dict, context: LambdaContext) -> dict:
    try:
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        # convert to model
        job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(user_id))

        # TODO convert to resource
        job_seeker.birth_date = int(job_seeker.birth_date)
        job_seeker.version = int(job_seeker.version)
        # return resource
        return _build_response(http_status=HTTPStatus.OK, body=json.dumps(job_seeker.as_dict()))
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# GET /api/seeker/relevant-jobs
@logger.inject_lambda_context(log_event=True)
def search_relevant_jobs(event: dict, context: LambdaContext) -> dict:
    try:
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        job_seeker_answers: JobSeekerAnswers = JobSeekerAnswers(
            **job_seeker_answers_repository.get_by_seeker_id(user_id))

        answers_arr = [job_seeker_answers.a1,
                       job_seeker_answers.a2,
                       job_seeker_answers.a3,
                       job_seeker_answers.a4,
                       job_seeker_answers.a5,
                       job_seeker_answers.a6,
                       job_seeker_answers.a7,
                       job_seeker_answers.a8,
                       job_seeker_answers.a9,
                       job_seeker_answers.a10]

        search_results: List[JobSearchResult] = jobs_repository.get_jobs(answers_arr, 100)

        dynamo_resource = boto3.resource("dynamodb")
        employer_table_name = get_env_or_raise(EmployerConstants.EMPLOYERS_TABLE_NAME)

        employer_ids = [item.employer_job.employer_id for item in search_results]
        employer_ids = list(dict.fromkeys(employer_ids))

        for item in search_results:
            item.employer_job.created_time = int(item.employer_job.created_time)

        employer_keys = [{"employer_id": employer_id} for employer_id in employer_ids]

        if len(employer_keys) > 0:
            try:
                response = dynamo_resource.batch_get_item(
                    RequestItems={
                        employer_table_name: {
                            'Keys': employer_keys,
                            'ConsistentRead': True
                        }
                    },
                    ReturnConsumedCapacity='TOTAL'
                )
            except ClientError as err:
                logger.exception(err.response['Error']['Message'])
                return _build_error_response(err, HTTPStatus.INTERNAL_SERVER_ERROR)
            else:
                employers_list = response['Responses'][employer_table_name]
                employers_dict = {x['employer_id']: x for x in employers_list}
                for item in search_results:
                    item.employer = employers_dict.get(item.employer_job.employer_id)
                    item.employer['created_time'] = int(item.employer['created_time'])

        search_results = [item.dict() for item in search_results]

        # return resource
        return _build_response(http_status=HTTPStatus.OK, body=json.dumps(search_results))
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)

    except NotFoundError as err:
        return _build_error_response(err, HTTPStatus.NOT_FOUND)
    except Exception as err:
        return _build_error_response(err)


# POST /api/seekers/answers
@logger.inject_lambda_context(log_event=True)
def add_seeker_answers(event: dict, context: LambdaContext) -> dict:
    try:
        answer_dto_list: List[JobSeekerAnswerDto] = [JobSeekerAnswerDto.parse_obj(item) for item in
                                                     json.loads(event["body"])]

        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(user_id))

        job_seeker_answers: JobSeekerAnswers = JobSeekerAnswers(job_seeker_id=user_id,
                                                                job_seeker_name=job_seeker.full_name)

        job_seeker_answers.a1 = answer_dto_list[0].answer
        job_seeker_answers.a2 = answer_dto_list[1].answer
        job_seeker_answers.a3 = answer_dto_list[2].answer
        job_seeker_answers.a4 = answer_dto_list[3].answer
        job_seeker_answers.a5 = answer_dto_list[4].answer
        job_seeker_answers.a6 = answer_dto_list[5].answer
        job_seeker_answers.a7 = answer_dto_list[6].answer
        job_seeker_answers.a8 = answer_dto_list[7].answer
        job_seeker_answers.a9 = answer_dto_list[8].answer
        job_seeker_answers.a10 = answer_dto_list[9].answer

        job_seeker_answers_repository.create(job_seeker_answers=job_seeker_answers)

        # return resource
        return _build_response(http_status=HTTPStatus.CREATED, body="")
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except NotFoundError as err:
        return _build_error_response(err, HTTPStatus.NOT_FOUND)
    except Exception as err:
        return _build_error_response(err)


# POST /api/seekers/experience
@logger.inject_lambda_context(log_event=True)
def add_seeker_experience(event: dict, context: LambdaContext) -> dict:
    try:
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        experience_dto: JobSeekerExperienceDto = JobSeekerExperienceDto.parse_raw(event["body"])

        exp_dict = dict(job_seeker_id=user_id,
                        experience_id=str(uuid.uuid4()))
        exp_dict.update(experience_dto.dict())

        experience: Experience = Experience(**exp_dict)
        # workplace_name=experience_dto.workplace_name,
        # start_year=experience_dto.start_year,
        # end_year=experience_dto.end_year,
        # role=experience_dto.role,
        # role_description=experience_dto.role_description)

        # job_seeker_repository.update(job_seeker)
        experience = job_seeker_experience_repository.create(experience)

        # return resource
        return _build_response(http_status=HTTPStatus.CREATED, body=json.dumps(experience.as_dict()))
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# GET /api/seekers/experience
@logger.inject_lambda_context(log_event=True)
def list_seeker_experience(event: dict, context: LambdaContext) -> dict:
    try:

        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        result_list = [item.dict() for item in
                       job_seeker_experience_repository.get_all(user_id)]

        return _build_response(http_status=HTTPStatus.OK, body=json.dumps(result_list))
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# GET /api/seekers/experience/{experience_id}
@logger.inject_lambda_context(log_event=True)
def get_seeker_experience_by_id(event: dict, context: LambdaContext) -> dict:
    try:
        experience_id = event["pathParameters"]["experience_id"]

        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        experience: Experience = job_seeker_experience_repository.get(user_id, experience_id)

        return _build_response(http_status=HTTPStatus.CREATED, body=json.dumps(experience.as_dict()))
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except NotFoundError as err:
        return _build_error_response(err, HTTPStatus.NOT_FOUND)
    except Exception as err:
        return _build_error_response(err)


# PUT /api/seekers/languages
@logger.inject_lambda_context(log_event=True)
def add_seeker_languages(event: dict, context: LambdaContext) -> dict:
    try:
        languages_list: List[str] = json.loads(event["body"])

        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(user_id))

        job_seeker.languages = languages_list

        job_seeker_repository.update(job_seeker)

        # return resource
        return _build_response(http_status=HTTPStatus.NO_CONTENT, body="")
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# GET /api/seeker/summary
@logger.inject_lambda_context(log_event=True)
def get_seeker_summary(event: dict, context: LambdaContext) -> dict:
    try:
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]

        # convert to model
        job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(user_id))

        job_seeker_experience_list: List[Experience] = job_seeker_experience_repository.get_all(user_id)

        job_seeker_answers: JobSeekerAnswers = \
            JobSeekerAnswers(**job_seeker_answers_repository.get_by_seeker_id(user_id))

        # TODO convert to resource
        resource: JobSeekerResource = JobSeekerResource(profile=job_seeker,
                                                        experience_list=job_seeker_experience_list,
                                                        answers=job_seeker_answers)
        # return resource
        return _build_response(http_status=HTTPStatus.OK, body=resource.json())
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# GET /api/list-relevant-seekers/
@logger.inject_lambda_context(log_event=True)
def list_relevant_seekers(event: dict, context: LambdaContext) -> dict:
    try:
        answer_dto_list: List[JobSeekerAnswerDto] = [JobSeekerAnswerDto.parse_obj(item) for item in
                                                     json.loads(event["body"])]

        employer_answers: List[bool] = [answer_dto_list[0].answer, answer_dto_list[1].answer, answer_dto_list[2].answer,
                                        answer_dto_list[3].answer, answer_dto_list[4].answer, answer_dto_list[5].answer,
                                        answer_dto_list[6].answer, answer_dto_list[7].answer, answer_dto_list[8].answer,
                                        answer_dto_list[9].answer]

        # list seekers models
        results: List[SearchResult] = job_seeker_answers_repository.find_best_match_answers(employer_answers)

        # convert to seekers resources
        results_json_list: List[dict] = [result.dict() for result in results]
        # return resource
        return _build_response(http_status=HTTPStatus.OK, body=json.dumps(results_json_list))
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# region api with {id}

# PUT /api/seekers/{id}/profile
@logger.inject_lambda_context(log_event=True)
def create_or_update_seeker_profile_with_id(event: dict, context: LambdaContext) -> dict:
    try:
        job_seeker_id = event["pathParameters"]["id"]

        profile_dto: JobSeekerProfileDto = JobSeekerProfileDto.parse_raw(event["body"])

        try:
            # try to update job seeker. If does not exists, create it.
            job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(job_seeker_id))
            return __update_seeker_profile(profile_dto=profile_dto, job_seeker=job_seeker)
        except NotFoundError as err:
            return __create_seeker_profile(user_id=job_seeker_id, profile_dto=profile_dto)

    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# GET /api/seekers/{id}/profile
@logger.inject_lambda_context(log_event=True)
def get_seeker_profile_with_id(event: dict, context: LambdaContext) -> dict:
    try:
        job_seeker_id = event["pathParameters"]["id"]

        # convert to model
        job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(job_seeker_id))

        # TODO convert to resource
        job_seeker.birth_date = int(job_seeker.birth_date)
        job_seeker.version = int(job_seeker.version)
        # return resource
        return _build_response(http_status=HTTPStatus.OK, body=json.dumps(job_seeker.as_dict()))
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# POST /api/seekers/{id}/answers
@logger.inject_lambda_context(log_event=True)
def add_seeker_answers_with_id(event: dict, context: LambdaContext) -> dict:
    try:
        answer_dto_list: List[JobSeekerAnswerDto] = [JobSeekerAnswerDto.parse_obj(item) for item in
                                                     json.loads(event["body"])]

        job_seeker_id = event["pathParameters"]["id"]

        job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(job_seeker_id))

        job_seeker_answers: JobSeekerAnswers = JobSeekerAnswers(job_seeker_id=job_seeker_id,
                                                                job_seeker_name=job_seeker.full_name)

        job_seeker_answers.a1 = answer_dto_list[0].answer
        job_seeker_answers.a2 = answer_dto_list[1].answer
        job_seeker_answers.a3 = answer_dto_list[2].answer
        job_seeker_answers.a4 = answer_dto_list[3].answer
        job_seeker_answers.a5 = answer_dto_list[4].answer
        job_seeker_answers.a6 = answer_dto_list[5].answer
        job_seeker_answers.a7 = answer_dto_list[6].answer
        job_seeker_answers.a8 = answer_dto_list[7].answer
        job_seeker_answers.a9 = answer_dto_list[8].answer
        job_seeker_answers.a10 = answer_dto_list[9].answer

        job_seeker_answers_repository.create(job_seeker_answers=job_seeker_answers)

        # return resource
        return _build_response(http_status=HTTPStatus.CREATED, body="")
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except NotFoundError as err:
        return _build_error_response(err, HTTPStatus.NOT_FOUND)
    except Exception as err:
        return _build_error_response(err)


# endregion

# region template methods

# POST /api/users/type
@logger.inject_lambda_context(log_event=True)
def set_user_type(event: dict, context: LambdaContext) -> dict:
    try:
        event: APIGatewayProxyEvent = APIGatewayProxyEvent(event)
        user_id = event.request_context.authorizer.claims["sub"]
        user_name = event.request_context.authorizer.claims["cognito:username"]
        userpool_id = str(event.request_context.authorizer.claims["iss"]).split("/")[-1]
        logger.info(f"user id: {user_id}")
        user_type = UpdateUserTypeDto.parse_raw(event.body)

        client: CognitoIdentityProviderClient = boto3.client("cognito-idp")
        client.admin_update_user_attributes(UserPoolId=userpool_id, Username=user_name, UserAttributes=[
            AttributeTypeTypeDef(Name="custom:user_type", Value=user_type.user_type.value)])
        return _build_response(HTTPStatus.OK, "{}")
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# endregion


def _build_response(http_status: HTTPStatus, body: str) -> dict:
    return {'statusCode': http_status,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, 'body': body}


def _build_error_response(err, status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR) -> dict:
    logger.error(str(err))
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': str(err),
    }

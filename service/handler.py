import json
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from typing import List

import boto3
from aws_lambda_context import LambdaContext
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from mypy_boto3_cognito_idp.type_defs import AttributeTypeTypeDef
from pydantic import ValidationError

from service.common.exceptions import NotFoundError
from service.dao.job_seeker_answers_repository import job_seeker_answers_repository
from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto
from service.dtos.job_seeker_experience_dto import JobSeekerExperienceDto
from service.dtos.job_seeker_profile_dto import JobSeekerProfileDto
from service.dtos.jobli_dto import JobliDto
from service.dtos.jobli_dto import UpdateUserTypeDto
from service.models.job_seeker_resource import JobSeekerResource
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


def __create_seeker_profile(user_id: str, profile_dto: JobSeekerProfileDto) -> dict:
    # convert to model
    job_seeker: JobSeeker = JobSeeker()
    job_seeker.id = user_id
    job_seeker.full_name = profile_dto.full_name

    birth_date = datetime(year=profile_dto.birth_year, month=profile_dto.birth_month, day=profile_dto.birth_day)
    job_seeker.birth_date = Decimal(birth_date.timestamp() * 1000)
    job_seeker.email = profile_dto.email
    job_seeker.address = profile_dto.address

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

# POST /api/seekers/{id}/experience
@logger.inject_lambda_context(log_event=True)
def add_seeker_experience(event: dict, context: LambdaContext) -> dict:
    try:
        experience_dto: JobSeekerExperienceDto = JobSeekerExperienceDto.parse_raw(event["body"])

        # # convert to model
        # job_seeker: JobSeeker = JobSeeker()
        # job_seeker.id = event["pathParameters"]["id"]
        # job_seeker.full_name = profile_dto.full_name
        #
        # birth_date = datetime.datetime(year=profile_dto.birth_year, month=profile_dto.birth_month,
        #                                day=profile_dto.birth_day)
        #
        # job_seeker.birth_date = time.mktime(birth_date.timetuple())
        # job_seeker.email = profile_dto.email
        # job_seeker.address = profile_dto.address
        #
        # job_seeker_repository.update(job_seeker)

        # return resource
        return _build_response(http_status=HTTPStatus.CREATED, body="")
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# POST /api/seekers/{id}/languages
@logger.inject_lambda_context(log_event=True)
def add_seeker_languages(event: dict, context: LambdaContext) -> dict:
    try:
        languages_list: List[str] = json.loads(event["body"])

        # # convert to model
        # job_seeker: JobSeeker = JobSeeker()
        # job_seeker.id = event["pathParameters"]["id"]
        # job_seeker.full_name = profile_dto.full_name
        #
        # birth_date = datetime.datetime(year=profile_dto.birth_year, month=profile_dto.birth_month,
        #                                day=profile_dto.birth_day)
        #
        # job_seeker.birth_date = time.mktime(birth_date.timetuple())
        # job_seeker.email = profile_dto.email
        # job_seeker.address = profile_dto.address
        #
        # job_seeker_repository.update(job_seeker)

        # return resource
        return _build_response(http_status=HTTPStatus.CREATED, body="")
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# region template methods

# POST /jobli
@logger.inject_lambda_context(log_event=True)
def create_jobli(event: dict, context: LambdaContext) -> dict:
    try:
        jobli_dto: JobliDto = JobliDto.parse_raw(event["body"])
        now: Decimal = Decimal(datetime.now().timestamp())
        jobli: Jobli = Jobli(name=jobli_dto.name, created_date=now, updated_date=now)
        return _build_response(http_status=HTTPStatus.CREATED, body=jobli.json())
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# PUT /jobli/{name}
@logger.inject_lambda_context(log_event=True)
def update_jobli(event: dict, context: LambdaContext) -> dict:
    if "pathParameters" not in event or "name" not in event["pathParameters"]:
        return _build_response(HTTPStatus.BAD_REQUEST, "")

    try:
        # pylint: disable=unused-variable
        name: str = event["pathParameters"]["name"]
        jobli_dto: JobliDto = JobliDto.parse_raw(event["body"])
        now: Decimal = Decimal(datetime.now().timestamp())
        jobli: Jobli = Jobli(
            name=jobli_dto.name,
            created_date=now - 1000,  # Note 'created_date' should be read from the database
            updated_date=now)
        return _build_response(HTTPStatus.OK, jobli.json())
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# GET /jobli/{name}
@logger.inject_lambda_context(log_event=True)
def get_jobli(event: dict, context: LambdaContext) -> dict:
    if "pathParameters" not in event or "name" not in event["pathParameters"]:
        return _build_response(HTTPStatus.BAD_REQUEST, "")

    try:
        name: str = event["pathParameters"]["name"]
        #  Note: dates should be read from the database
        now: Decimal = Decimal(datetime.now().timestamp())
        item: Jobli = Jobli(name=name, created_date=now, updated_date=now)
        if item is None:
            return _build_response(HTTPStatus.NOT_FOUND, body="{ 'message': 'item was not found' }")
        body = item.json()
        return _build_response(HTTPStatus.OK, body)
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


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


def _build_response(http_status: HTTPStatus, body: str) -> dict:
    return {'statusCode': http_status, 'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, 'body': body}


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

# endregion

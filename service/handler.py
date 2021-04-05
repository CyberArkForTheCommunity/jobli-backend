import json
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from typing import List
from aws_lambda_context import LambdaContext
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import logger
from pydantic import ValidationError

from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.model.job_seeker import JobSeeker
from service.dtos.job_seeker_profile_dto import JobSeekerProfileDto
from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto
from service.dtos.job_seeker_experience_dto import JobSeekerExperienceDto
from service.dtos.jobli_dto import JobliDto
from service.models.jobli import Jobli

logger = Logger()


# POST /api/seekers/{id}/profile
@logger.inject_lambda_context(log_event=True)
def create_seeker_profile(event: dict, context: LambdaContext) -> dict:
    try:
        profile_dto: JobSeekerProfileDto = JobSeekerProfileDto.parse_raw(event["body"])

        # convert to model
        job_seeker: JobSeeker = JobSeeker()
        job_seeker.id = event["pathParameters"]["id"]
        job_seeker.full_name = profile_dto.full_name

        birth_date = datetime(year=profile_dto.birth_year, month=profile_dto.birth_month, day=profile_dto.birth_day)
        job_seeker.birth_date = Decimal(birth_date.timestamp())
        job_seeker.email = profile_dto.email
        job_seeker.address = profile_dto.address

        job_seeker_repository.create(job_seeker)

        # return resource
        return _build_response(http_status=HTTPStatus.CREATED, body="")
    except (ValidationError, TypeError) as err:
        return _build_error_response(err, HTTPStatus.BAD_REQUEST)
    except Exception as err:
        return _build_error_response(err)


# POST /api/seekers/{id}/answers
@logger.inject_lambda_context(log_event=True)
def add_seeker_answers(event: dict, context: LambdaContext) -> dict:
    try:
        answer_dto_list: List[JobSeekerAnswerDto] = [JobSeekerAnswerDto.parse_raw(item) for item in json.loads(event["body"])]

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


def _build_response(http_status: HTTPStatus, body: str) -> dict:
    return {'statusCode': http_status, 'headers': {'Content-Type': 'application/json'}, 'body': body}


def _build_error_response(err, status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR) -> dict:
    logger.error(str(err))
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': str(err),
    }

# endregion
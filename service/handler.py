from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

import json

import boto3
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from aws_lambda_powertools.logging import logger
from aws_lambda_context import LambdaContext
from mypy_boto3_cognito_idp.type_defs import AttributeTypeTypeDef
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from service.dtos.jobli_dto import JobliDto, UpdateUserTypeDto
from service.models.jobli import Jobli

logger = Logger()


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
        client.admin_update_user_attributes(UserPoolId=userpool_id, Username=user_name, UserAttributes=[AttributeTypeTypeDef(Name="custom:user_type", Value=user_type.user_type.value)])
        return _build_response(HTTPStatus.OK, "{}")
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

from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from service.common.utils import get_env_or_raise
from service.models.employer.employer import Employer
from service.lambdas.employer.constants import EmployerConstants
from aws_lambda_powertools import Logger
import boto3
import json

logger = Logger()


# GET /jobli/employers/{employer_id}
@logger.inject_lambda_context(log_event=True)
def get_employer_by_id(event: dict, context: LambdaContext) -> dict:
    try:
        if 'pathParameters' not in event or not event['pathParameters'] \
                or 'employer_id' not in event['pathParameters']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': {'Content-Type': 'application/json'},
                    'body': "Missing employer id"}
        employer_id = event['pathParameters']['employer_id']
        dynamo_resource = boto3.resource("dynamodb")
        employers_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.EMPLOYERS_TABLE_NAME))
        employer: Employer = Employer.parse_obj(employers_table.get_item(Key={"employer_id": employer_id}).get('Item', {}))
        return {'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': employer.json(exclude_none=True)}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}

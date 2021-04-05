from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer import Employer
from service.common.utils import get_env_or_raise
from service.lambdas.employer.constants import EmployerConstants
import uuid
import boto3
from datetime import datetime
from decimal import Decimal

logger = Logger()


# POST /jobli/employers
@logger.inject_lambda_context(log_event=True)
def create_employer(event: dict, context: LambdaContext) -> dict:
    try:
        if 'body' not in event or not event['body']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': {'Content-Type': 'application/json'},
                    'body': "Missing employer body to create"}
        employer: Employer = Employer.parse_raw(event['body'])
        employer.employer_id = str(uuid.uuid4())
        employer.created_time = Decimal(datetime.now().timestamp())
        dynamo_resource = boto3.resource("dynamodb")
        employers_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.EMPLOYERS_TABLE_NAME))
        employers_table.put_item(Item=employer.dict(exclude_none=True))
        return {'statusCode': HTTPStatus.CREATED,
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

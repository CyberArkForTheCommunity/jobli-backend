from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer import Employer
import uuid
import boto3
from datetime import datetime

logger = Logger()


# POST /jobli/employers
@logger.inject_lambda_context(log_event=True)
def create_employer(event: dict, context: LambdaContext) -> dict:
    try:
        employer: Employer = Employer.parse_obj(event['body'])
        employer.employer_id = str(uuid.uuid4())
        employer.created_time = datetime.now()
        dynamo_resource = boto3.resource("dynamodb")
        employers_table = dynamo_resource.Table('jobli_employers')
        employers_table.put_item(Item=employer.dict(exclude_none=True))
        return {'statusCode': HTTPStatus.CREATED,
                'headers': {'Content-Type': 'application/json'},
                'body': employer.dict()}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}

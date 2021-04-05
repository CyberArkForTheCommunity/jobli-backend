from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer import Employer
from typing import Dict
import boto3

logger = Logger()


# PUT /jobli/employers/{employer_id}
@logger.inject_lambda_context(log_event=True)
def update_employer(event: dict, context: LambdaContext) -> dict:
    try:
        if 'params' not in event or 'querystring' not in event['params'] or 'employer_id' not in event['params']['querystring']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': {'Content-Type': 'application/json'},
                    'body': "Missing employer id"}
        employer_id = event['querystring']['params']
        employer: Employer = Employer.parse_obj(event['body'])
        dynamo_client = boto3.client("dynamodb")
        employers_table = dynamo_client.Table('jobli_employers')
        # Get the existing employer to make it exists and get its current details
        stored_employer: Dict = employers_table.get_item(Key={"employer_id": employer_id})['Item']

        # Update it with the given model
        stored_employer.update(employer.dict(exclude_none=True))

        # Store it
        employers_table.update_item(Key={
                "employer_id": employer_id
            },
            UpdateExpression="set employer_email=:ee "
                             "business_name=:bn "
                             "business_address=:ba "
                             "business_website=:bw "
                             "description=:d "
                             "employer_terms=:et",
            ExpressionAttributeValues={
                ":ee": employer.employer_email,
                ":bn": employer.business_name,
                ":ba": employer.business_address,
                ":bw": employer.business_website,
                ":d": employer.description,
                ":et": employer.employer_terms
            },
            ReturnValues="UPDATED_NEW"
        )

        return {'statusCode': HTTPStatus.CREATED,
                'headers': {'Content-Type': 'application/json'},
                'body': stored_employer}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}

from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
import boto3

logger = Logger()


# GET /jobli/employers/{employer_id}
@logger.inject_lambda_context(log_event=True)
def get_employer_by_id(event: dict, context: LambdaContext) -> dict:
    try:
        if 'params' not in event or 'querystring' not in event['params'] or 'employer_id' not in event['params']['querystring']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': {'Content-Type': 'application/json'},
                    'body': "Missing employer id"}
        employer_id = event['querystring']['params']
        dynamo_resource = boto3.resource("dynamodb")
        employers_table = dynamo_resource.Table('jobli_employers')
        employer = employers_table.get_item(Key={"employer_id": employer_id}).get('Item', {})
        return {'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': employer}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
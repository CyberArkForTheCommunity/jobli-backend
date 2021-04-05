from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer_filter import EmployerFilter
from boto3.dynamodb.conditions import Key
import boto3

logger = Logger()


@logger.inject_lambda_context(log_event=True)
def get_employers(event: dict, context: LambdaContext) -> dict:
    try:
        dynamo_client = boto3.client("dynamodb")
        employers_table = dynamo_client.Table('jobli_employers')
        employer_filter: EmployerFilter = EmployerFilter.parse_obj(event)
        filter_expression = None
        result_items = None
        if employer_filter.employer_id:
            result_items = [employers_table.get_item(Key={"employer_id": employer_filter.employer_id}).get('Item', {})]
        elif employer_filter.business_name or employer_filter.city:
            if employer_filter.business_name:
                filter_expression = Key('business_name').eq(employer_filter.business_name)
            if employer_filter.city:
                filter_expression = filter_expression & Key('business_address.city').eq(employer_filter.city)
            result_items = employers_table.query(KeyConditionExpression=filter_expression).get('Items', [])
        else:
            args = {"Limit": employer_filter.limit_per_page}
            if employer_filter.last_pagination_key:
                args["ExclusiveStartKey"] = employer_filter.last_pagination_key
            result_items = employers_table.scan(**args).get("Items", [])
        return {'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': result_items}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
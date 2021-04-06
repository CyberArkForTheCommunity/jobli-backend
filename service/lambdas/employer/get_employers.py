from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer_filter import EmployerFilter
from service.models.employer.employer import Employer
from pydantic import parse_obj_as
from service.common.utils import get_env_or_raise
from service.lambdas.employer.constants import EmployerConstants
from boto3.dynamodb.conditions import Key
from typing import Optional, List
import boto3
import json

logger = Logger()


# GET /api/employers
@logger.inject_lambda_context(log_event=True)
def get_employers(event: dict, context: LambdaContext) -> dict:
    try:
        dynamo_resource = boto3.resource("dynamodb")
        employers_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.EMPLOYERS_TABLE_NAME))
        employer_filter: Optional[EmployerFilter] = None
        if 'queryStringParameters' in event and event['queryStringParameters']:
            employer_filter = EmployerFilter.parse_raw(event['queryStringParameters'])
        filter_expression = None
        result_items = None
        if employer_filter and employer_filter.employer_id:
            result_items = [Employer.parse_obj(employers_table.get_item(Key={"employer_id": employer_filter.employer_id}).get('Item', {}))]
        else:
            if employer_filter and employer_filter.business_name:
                filter_expression = Key('business_name').eq(employer_filter.business_name)
            if employer_filter and employer_filter.full_address:
                filter_expression = filter_expression & \
                                    Key('business_address.full_address').eq(employer_filter.full_address)
            limit_per_page = EmployerConstants.LIMITS_PER_EMPLOYER_PAGE
            if employer_filter and employer_filter.limit_per_page:
                limit_per_page = employer_filter.limit_per_page
            args = {"Limit": limit_per_page}
            if filter_expression:
                args["FilterExpression"] = filter_expression
            if employer_filter and employer_filter.last_pagination_key:
                args["ExclusiveStartKey"] = employer_filter.last_pagination_key
            result_items = parse_obj_as(List[Employer], employers_table.scan(**args).get("Items", []))
        return {'statusCode': HTTPStatus.OK,
                'headers': EmployerConstants.HEADERS,
                'body': json.dumps({"employers": [e.json(exclude_none=True) for e in result_items]})}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}

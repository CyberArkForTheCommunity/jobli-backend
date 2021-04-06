from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer_job_filter import EmployerJobFilter
from service.models.employer.employer_job import EmployerJob
from pydantic import parse_obj_as
from service.common.utils import get_env_or_raise
from service.lambdas.employer.constants import EmployerConstants
from boto3.dynamodb.conditions import Key
from typing import Optional, List
import boto3
import json

logger = Logger()


# GET /api/employers/{employer_id}/jobs
@logger.inject_lambda_context(log_event=True)
def get_employer_jobs(event: dict, context: LambdaContext) -> dict:
    try:
        if 'pathParameters' not in event or not event['pathParameters'] \
                or 'employer_id' not in event['pathParameters']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': {'Content-Type': 'application/json'},
                    'body': "Missing employer id"}
        employer_id = event['pathParameters']['employer_id']
        dynamo_resource = boto3.resource("dynamodb")
        jobs_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.JOBS_TABLE_NAME))
        jobs_filter: Optional[EmployerJobFilter] = None
        if 'queryStringParameters' in event and event['queryStringParameters']:
            jobs_filter = EmployerJobFilter.parse_raw(event['queryStringParameters'])
        result_items = None
        if jobs_filter and jobs_filter.job_id:
            result_items = [EmployerJob.parse_obj(jobs_table.get_item(
                Key={"job_id": jobs_filter.job_id}).get('Item', {}))]
        else:
            limit_per_page = EmployerConstants.LIMITS_PER_EMPLOYER_PAGE
            if jobs_filter and jobs_filter.limit_per_page:
                limit_per_page = jobs_filter.limit_per_page
            args = {"Limit": limit_per_page}
            if employer_id:
                args["FilterExpression"] = Key("employer_id").eq(employer_id)
            if jobs_filter and jobs_filter.last_pagination_key:
                args["ExclusiveStartKey"] = jobs_filter.last_pagination_key
            result_items = parse_obj_as(List[EmployerJob], jobs_table.scan(**args).get("Items", []))
        return {'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"jobs": [e.json(exclude_none=True) for e in result_items]})}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}

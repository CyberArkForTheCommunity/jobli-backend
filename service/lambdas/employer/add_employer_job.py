from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer_job import EmployerJob
from service.models.employer.employer import Employer
from service.common.utils import get_env_or_raise
from service.lambdas.employer.constants import EmployerConstants
import uuid
import boto3

logger = Logger()


# POST /api/employers/{employer_id}/jobs
@logger.inject_lambda_context(log_event=True)
def add_employer_job(event: dict, context: LambdaContext) -> dict:
    try:
        if 'pathParameters' not in event or not event['pathParameters'] \
                or 'employer_id' not in event['pathParameters'] or 'body' not in event or not event['body']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Missing employer job body/path params to create"}
        employer_job: EmployerJob = EmployerJob.parse_raw(event['body'])
        employer_job.job_id = str(uuid.uuid4())
        employer_job.employer_id = event["pathParameters"]["employer_id"]
        dynamo_resource = boto3.resource("dynamodb")
        employers_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.EMPLOYERS_TABLE_NAME))
        jobs_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.JOBS_TABLE_NAME))
        # Check if employer id exists, will throw exception if not
        Employer.parse_obj(employers_table.get_item(
            Key={"employer_id": employer_job.employer_id}).get('Item', {}))
        jobs_table.put_item(Item=employer_job.create_employer_job_item())
        return {'statusCode': HTTPStatus.CREATED,
                'headers': EmployerConstants.HEADERS,
                'body': employer_job.json(exclude_none=True)}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}

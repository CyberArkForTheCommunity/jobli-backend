from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from service.common.utils import get_env_or_raise
from service.models.employer.employer_job import EmployerJob
from service.lambdas.employer.constants import EmployerConstants
from aws_lambda_powertools import Logger
import boto3

logger = Logger()


# GET /api/employers/{employer_id}/jobs/{job_id}
@logger.inject_lambda_context(log_event=True)
def get_employer_job_by_id(event: dict, context: LambdaContext) -> dict:
    try:
        if 'pathParameters' not in event or not event['pathParameters'] \
                or 'employer_id' not in event['pathParameters'] or 'job_id' not in event['pathParameters']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Missing employer id"}
        employer_id = event['pathParameters']['employer_id']
        job_id = event['pathParameters']['job_id']
        dynamo_resource = boto3.resource("dynamodb")
        jobs_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.JOBS_TABLE_NAME))
        job: EmployerJob = EmployerJob.parse_obj(jobs_table.get_item(
            Key={"employer_id": employer_id, 'job_id': job_id}).get('Item', {}))
        return {'statusCode': HTTPStatus.OK,
                'headers': EmployerConstants.HEADERS,
                'body': job.json(exclude_none=True)}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}

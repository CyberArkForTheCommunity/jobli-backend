from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer_job import EmployerJob
import uuid
import boto3

logger = Logger()


@logger.inject_lambda_context(log_event=True)
def add_employer_job(event: dict, context: LambdaContext) -> dict:
    try:
        job: EmployerJob = EmployerJob.parse_obj(event)
        job.job_id = str(uuid.uuid4())
        dynamo_client = boto3.client("dynamodb")
        jobs_table = dynamo_client.Table('jobli-jobs')
        jobs_table.put_item(Item=job.dict())
        return {'statusCode': HTTPStatus.CREATED,
                'headers': {'Content-Type': 'application/json'},
                'body': job}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
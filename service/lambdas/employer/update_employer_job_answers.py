from http import HTTPStatus

from aws_lambda_context import LambdaContext
from pydantic import ValidationError
from aws_lambda_powertools import Logger
from service.models.employer.employer_job import EmployerJob
from service.common.utils import get_env_or_raise
from service.models.common import Answer
from service.lambdas.employer.constants import EmployerConstants
import boto3
from pydantic import parse_raw_as
from typing import List

logger = Logger()


# PUT /api/employers/{employer_id}/jobs/{job_id}
@logger.inject_lambda_context(log_event=True)
def update_employer_job_answers(event: dict, context: LambdaContext) -> dict:
    try:
        if 'pathParameters' not in event or not event['pathParameters'] \
                or 'employer_id' not in event['pathParameters'] or 'job_id' not in event['pathParameters'] \
                or 'body' not in event or not event['body']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': {'Content-Type': 'application/json'},
                    'body': "Missing employer job body/path params to create"}
        employer_answers: List[Answer] = parse_raw_as(List[Answer], event['body'])
        employer_id = event['pathParameters']['employer_id']
        job_id = event['pathParameters']['job_id']
        dynamo_resource = boto3.resource("dynamodb")
        jobs_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.JOBS_TABLE_NAME))

        stored_job: EmployerJob = EmployerJob.parse_obj(jobs_table.get_item(
            Key={'job_id': job_id}).get('Item', {}))
        if stored_job.employer_id != employer_id:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': {'Content-Type': 'application/json'},
                    'body': "Given employer id does not match job id"}
        stored_job.answers = employer_answers
        jobs_table.update_item(Key={
                "job_id": job_id
            },
            UpdateExpression="set answers=:a",
            ExpressionAttributeValues={
                ":a": [a.dict() for a in stored_job.answers],
            },
            ReturnValues="UPDATED_NEW"
        )
        return {'statusCode': HTTPStatus.CREATED,
                'headers': {'Content-Type': 'application/json'},
                'body': stored_job.json(exclude_none=True)}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': {'Content-Type': 'application/json'},
                'body': str(err)}

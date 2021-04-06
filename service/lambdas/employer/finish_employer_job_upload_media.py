from http import HTTPStatus

from aws_lambda_context import LambdaContext
from service.common.utils import get_env_or_raise, s3_exists
from pydantic import ValidationError
from service.lambdas.employer.constants import EmployerConstants
from service.models.employer.employer_job import EmployerJob
from aws_lambda_powertools import Logger
import boto3
import mimetypes
mimetypes.init()

logger = Logger()


# GET /jobli/employers/{employer_id}/jobs/{job_id}/media/finish
@logger.inject_lambda_context(log_event=True)
def finish_employer_job_upload_media(event: dict, context: LambdaContext) -> dict:
    try:
        if 'pathParameters' not in event or not event['pathParameters'] \
                or 'employer_id' not in event['pathParameters'] or 'job_id' not in event['pathParameters']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Missing employer/job path params"}
        if 'queryStringParameters' not in event or not event['queryStringParameters'] \
                or 'file_name' not in event['queryStringParameters']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Missing file_name in query"}
        employer_id = event['pathParameters']['employer_id']
        job_id = event['pathParameters']['job_id']
        file_name = event['queryStringParameters']['file_name']
        mime: str = mimetypes.guess_type(file_name)[0]
        if not mime or mime.split("/")[0] not in ['audio', 'video', 'image']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Filename is not of media type"}
        dynamo_resource = boto3.resource("dynamodb")
        jobs_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.JOBS_TABLE_NAME))
        job: EmployerJob = EmployerJob.parse_obj(jobs_table.get_item(
            Key={'job_id': job_id}).get('Item', {}))
        if job.employer_id != employer_id:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Invalid employer id"}
        bucket_name = get_env_or_raise(EmployerConstants.EMPLOYERS_MEDIA_BUCKET_NAME)
        if not s3_exists(bucket_name, f"{employer_id}/{job_id}/{file_name}"):
            return {'statusCode': HTTPStatus.FAILED_DEPENDENCY,
                    'headers': EmployerConstants.HEADERS,
                    'body': f"File was not uploaded yet "
                            f"[{employer_id}/{job_id}/{file_name}] on bucket [{bucket_name}]"}
        # Update the dynamo record for the job
        if not job.job_media:
            job.job_media = []
        job.job_media.append(f"s3://{bucket_name}/"
                             f"{employer_id}/{job_id}/{file_name}")
        jobs_table.update_item(Key={
                "job_id": job_id
            },
            UpdateExpression="set job_media=:jm",
            ExpressionAttributeValues={
                ":jm": job.job_media,
            },
            ReturnValues="UPDATED_NEW"
        )
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

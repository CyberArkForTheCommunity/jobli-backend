from http import HTTPStatus

from aws_lambda_context import LambdaContext
from service.common.utils import get_env_or_raise, s3_exists, s3_mkdir
from pydantic import ValidationError
from service.lambdas.employer.constants import EmployerConstants
from service.models.employer.employer_job import EmployerJob
from aws_lambda_powertools import Logger
import boto3
import mimetypes
import json
mimetypes.init()

logger = Logger()


# GET /jobli/employers/{employer_id}/jobs/{job_id}/media/start
@logger.inject_lambda_context(log_event=True)
def start_employer_job_upload_media(event: dict, context: LambdaContext) -> dict:
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
        if not s3_exists(bucket_name, f"{employer_id}"):
            s3_mkdir(bucket_name, f"{employer_id}")
        if not s3_exists(bucket_name, f"{employer_id}/{job_id}"):
            s3_mkdir(bucket_name, f"{employer_id}/{job_id}")
        s3_client = boto3.client("s3")
        fields = s3_client.generate_presigned_url('put_object',
                                                  Params={'Bucket': bucket_name,
                                                          'Key': f"{employer_id}/{job_id}/{file_name}",
                                                          'ACL': 'public-read'
                                                          },
                                                  ExpiresIn=360)
        return {'statusCode': HTTPStatus.OK,
                'headers': EmployerConstants.HEADERS,
                'body': json.dumps(fields)}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}

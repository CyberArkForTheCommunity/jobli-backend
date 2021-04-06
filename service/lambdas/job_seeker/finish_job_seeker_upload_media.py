from http import HTTPStatus

from aws_lambda_context import LambdaContext
from service.common.utils import get_env_or_raise, s3_exists
from pydantic import ValidationError
from service.lambdas.employer.constants import EmployerConstants
from service.dao.constants import EnvVarNames
from service.dao.job_seeker_repository import _JobSeekerRepository
from aws_lambda_powertools import Logger
from typing import Dict
from service.models.job_seeker_resource import JobSeeker
import mimetypes
mimetypes.init()

logger = Logger()


# GET /api/seeker/{id}/media/finish
@logger.inject_lambda_context(log_event=True)
def finish_job_seeker_upload_media(event: dict, context: LambdaContext) -> dict:
    try:
        if 'pathParameters' not in event or not event['pathParameters'] \
                or 'id' not in event['pathParameters']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Missing employer/job path params"}
        if 'queryStringParameters' not in event or not event['queryStringParameters'] \
                or 'file_name' not in event['queryStringParameters']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Missing file_name in query"}
        job_seeker_id = event['pathParameters']['id']
        file_name = event['queryStringParameters']['file_name']
        mime: str = mimetypes.guess_type(file_name)[0]
        if not mime or mime.split("/")[0] not in ['audio', 'video', 'image']:
            return {'statusCode': HTTPStatus.BAD_REQUEST,
                    'headers': EmployerConstants.HEADERS,
                    'body': "Filename is not of media type"}
        dao: _JobSeekerRepository = _JobSeekerRepository()
        job_seeker: Dict = dao.get(job_seeker_id)
        bucket_name = get_env_or_raise(EnvVarNames.JOB_SEEKERS_MEDIA_BUCKET)
        if not s3_exists(bucket_name, f"{job_seeker_id}/{file_name}"):
            return {'statusCode': HTTPStatus.FAILED_DEPENDENCY,
                    'headers': EmployerConstants.HEADERS,
                    'body': f"File was not uploaded yet "
                            f"{job_seeker_id}/{file_name}] on bucket [{bucket_name}]"}
        # Update the dynamo record for the job
        if 'media' not in job_seeker:
            job_seeker['media'] = []
        job_seeker['media'].append(f"s3://{bucket_name}/"
                                   f"{job_seeker_id}/{file_name}")
        job_seeker_model = JobSeeker.parse_obj(job_seeker)
        dao.update(job_seeker_model)
        return {'statusCode': HTTPStatus.OK,
                'headers': EmployerConstants.HEADERS,
                'body': job_seeker_model.json(exclude_none=True)}
    except (ValidationError, TypeError) as err:
        return {'statusCode': HTTPStatus.BAD_REQUEST,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}
    except Exception as err:
        return {'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                'headers': EmployerConstants.HEADERS,
                'body': str(err)}

# pylint: disable = print-used
import json
import os
from typing import List

import boto3
import pytest
import decimal
from botocore.exceptions import ClientError, ValidationError
from dotenv import load_dotenv

from service.common.exceptions import NotFoundError
from service.common.utils import get_env_or_raise
from service.dao.job_seeker_answers_repository import job_seeker_answers_repository
from service.dao.job_seeker_experience_repository import job_seeker_experience_repository
from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.jobs_repository import jobs_repository
from service.dao.model.experience import Experience
from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.lambdas.employer.constants import EmployerConstants
from service.models.employer.employer_job import JobSearchResult
from service.models.job_seeker_resource import JobSeekerResource
from tests.helpers.environment_handler import load_env_vars


@pytest.fixture(scope="module")
def endpoint_url():
    load_dotenv()
    load_env_vars()
    endpoint_url = os.environ['JOBLI_API_GW']
    return endpoint_url[:-1]

# noinspection PyPep8Naming
@pytest.mark.skip(msg="Test retrieval of relevant job for debug")
def test_job_seekers_get_relevant_jobs_debug(endpoint_url):
    assert os.environ["JOB_SEEKERS_TABLE_NAME"] is not None
    print("\nseekers_table: ", os.environ["JOB_SEEKERS_TABLE_NAME"])

    user_id = '751ef537-e95a-4217-9287-d89a8861d948'

    job_seeker_answers: JobSeekerAnswers = JobSeekerAnswers(
        **job_seeker_answers_repository.get_by_seeker_id(user_id))

    answers_arr = [job_seeker_answers.a1,
                   job_seeker_answers.a2,
                   job_seeker_answers.a3,
                   job_seeker_answers.a4,
                   job_seeker_answers.a5,
                   job_seeker_answers.a6,
                   job_seeker_answers.a7,
                   job_seeker_answers.a8,
                   job_seeker_answers.a9,
                   job_seeker_answers.a10]

    search_results: List[JobSearchResult] = jobs_repository.get_jobs(answers_arr, 100)

    for item in search_results:
        item.employer_job.created_time = int(item.employer_job.created_time)

    search_results = [item.dict() for item in search_results]


@pytest.mark.skip(msg="Test retrieval of seeker summary for debug")
def test_job_seekers_get_summary_debug(endpoint_url):
    assert os.environ["JOB_SEEKERS_TABLE_NAME"] is not None
    print("\nseekers_table: ", os.environ["JOB_SEEKERS_TABLE_NAME"])

    user_id = '751ef537-e95a-4217-9287-d89a8861d948'
# convert to model
    job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(user_id))

    job_seeker_answers: JobSeekerAnswers = \
        JobSeekerAnswers(**job_seeker_answers_repository.get_by_seeker_id(user_id))

    job_seeker_experience_list: List[Experience] = job_seeker_experience_repository.get_all(user_id)

    # TODO convert to resource
    resource: JobSeekerResource = JobSeekerResource(profile=job_seeker,
                                                    experience_list=job_seeker_experience_list,
                                                    answers=job_seeker_answers)

@pytest.mark.skip(msg="Test batch get items debug")
def test_get_batch_items_debug(endpoint_url):
    try:

        user_id = '751ef537-e95a-4217-9287-d89a8861d948'

        job_seeker_answers: JobSeekerAnswers = JobSeekerAnswers(
            **job_seeker_answers_repository.get_by_seeker_id(user_id))

        answers_arr = [job_seeker_answers.a1,
                       job_seeker_answers.a2,
                       job_seeker_answers.a3,
                       job_seeker_answers.a4,
                       job_seeker_answers.a5,
                       job_seeker_answers.a6,
                       job_seeker_answers.a7,
                       job_seeker_answers.a8,
                       job_seeker_answers.a9,
                       job_seeker_answers.a10]

        search_results: List[JobSearchResult] = jobs_repository.get_jobs(answers_arr, 100)

        employer_keys = []
        dynamo_resource = boto3.resource("dynamodb")
        employer_table_name = get_env_or_raise(EmployerConstants.EMPLOYERS_TABLE_NAME)

        for item in search_results:
            item.employer_job.created_time = int(item.employer_job.created_time)
            employer_keys.append({"employer_id": item.employer_job.employer_id})

        if len(employer_keys) > 0:
            try:
                response = dynamo_resource.batch_get_item(
                    RequestItems={
                        employer_table_name: {
                            'Keys': employer_keys,
                            'ConsistentRead': True
                        }
                    },
                    ReturnConsumedCapacity='TOTAL'
                )
            except ClientError as err:
                print(err.response['Error']['Message'])

            else:
                employers_list = response['Responses'][employer_table_name]
                employers_dict = {x['employer_id']: x for x in employers_list}
                for item in search_results:
                    item.employer = employers_dict.get(item.employer_job.employer_id)
                    item.employer['created_time'] = int(item.employer['created_time'])

        search_results = [item.dict() for item in search_results]

        print()
    except (ValidationError, TypeError) as err:
        print()
    except NotFoundError as err:
        print()
    except Exception as err:
        print()


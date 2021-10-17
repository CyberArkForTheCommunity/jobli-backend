# pylint: disable = print-used
import os
from typing import List

import pytest
from dotenv import load_dotenv

from service.dao.job_seeker_answers_repository import job_seeker_answers_repository
from service.dao.job_seeker_experience_repository import job_seeker_experience_repository
from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.jobs_repository import jobs_repository
from service.dao.model.experience import Experience
from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.models.employer.employer_job import JobSearchResult
from service.models.job_seeker_resource import JobSeekerResource
from tests.helpers.environment_handler import load_env_vars


@pytest.fixture(scope="module")
def endpoint_url():
    load_dotenv()
    load_env_vars()
    endpoint_url = os.environ['JOBLI_API_GW']
    return endpoint_url[:-1]


# endregion
# noinspection PyPep8Naming
@pytest.mark.skip(msg="Test retrieval of relevant job for debug")
def test_job_seekers_get_relevant_jobs_debug(endpoint_url):
    assert os.environ["JOB_SEEKERS_TABLE_NAME"] is not None
    print("\nseekers_table: ", os.environ["JOB_SEEKERS_TABLE_NAME"])

    user_id = '7dd6f937-88d6-4a13-8032-d3456b7dd8bb'

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

    user_id = '7dd6f937-88d6-4a13-8032-d3456b7dd8bb'
# convert to model
    job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get(user_id))

    job_seeker_answers: JobSeekerAnswers = \
        JobSeekerAnswers(**job_seeker_answers_repository.get_by_seeker_id(user_id))

    job_seeker_experience_list: List[Experience] = job_seeker_experience_repository.get_all(user_id)

    # TODO convert to resource
    resource: JobSeekerResource = JobSeekerResource(profile=job_seeker,
                                                    experience_list=job_seeker_experience_list,
                                                    answers=job_seeker_answers)
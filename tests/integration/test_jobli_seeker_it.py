# pylint: disable = print-used
import json
import os
import uuid
from http import HTTPStatus
from typing import List

import pytest
import requests
from dotenv import load_dotenv

from service.common.exceptions import NotFoundError
from service.dao.job_seeker_experience_repository import job_seeker_experience_repository
from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.model.experience import Experience
from service.dao.model.job_seeker import JobSeeker
from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto
from service.dtos.job_seeker_profile_dto import JobSeekerProfileDto
# from cdk.jobli_service_cdk.service_stack.jobli_construct import get_stack_name
# from jobli_service_cdk.service_stack.constants import BASE_NAME
from service.dtos.jobli_dto import UpdateUserTypeDto, UserType
from tests.helpers.cognito_auth_util import add_auth_header
from tests.helpers.environment_handler import load_env_vars
from tests.helpers.random_utils import random_string


# region test fixtures

@pytest.fixture(scope="module")
def endpoint_url():
    load_dotenv()
    # load_env_vars(get_stack_name(BASE_NAME))
    load_env_vars()
    endpoint_url = os.environ['JOBLI_API_GW']
    return endpoint_url[:-1]


@pytest.fixture(scope="module")
def auth_headers():
    return add_auth_header()

# endregion


def test_create_or_update_seeker_profile(endpoint_url, auth_headers):
    # when create entity

    profile_dto: JobSeekerProfileDto = JobSeekerProfileDto(full_name=random_string(), birth_year=1970, birth_month=1,
                                                           birth_day=1,
                                                           address=random_string(), email=random_string())
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)

    response = requests.api.put(url=f"{endpoint_url}/api/seeker/profile", headers=headers, json=profile_dto.dict())

    # then assert created
    assert response.status_code == HTTPStatus.OK
    # # assert created_date & updated_date was initialize
    # resource = json.loads(response.content)
    # assert resource['full_name'] == profile_dto.full_name
    # day_seconds = 24 * 60 * 60
    # now = datetime.now().timestamp()
    # assert now - day_seconds < resource['created_date'] < now + day_seconds
    # assert resource['created_date'] == resource['updated_date']
    #
    # # when get the created entity
    # response = requests.api.get(url=f"{endpoint_url}/jobli/{jobli_dto.name}", headers=auth_headers)
    #
    # # then assert all fields saved successfully
    # assert response.status_code == HTTPStatus.OK
    # resource = json.loads(response.content)
    # assert resource['name'] == jobli_dto.name
    # assert now - day_seconds < resource['created_date'] < now + day_seconds
    # assert resource['created_date'] == resource['updated_date']


@pytest.mark.skip(reason="This test will work only if user exists and doesn't already have answers in DB")
def test_add_seeker_answers(endpoint_url, auth_headers):
    # when create entity

    answers_dto: List[JobSeekerAnswerDto] = []

    for i in range(1, 10):
        answers_dto.append(JobSeekerAnswerDto(key="a" + str(i), question="q" + str(i), answer=True))

    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    json_body = json.dumps([ob.__dict__ for ob in answers_dto])
    response = requests.api.post(url=f"{endpoint_url}/api/seeker/answers", headers=headers, data=json_body)

    # then assert created
    assert response.status_code == HTTPStatus.OK


@pytest.mark.skip(reason="This test will work only if user doesn't exist in cognito")
def test_set_user_type(endpoint_url, auth_headers):
    # when create entity
    jobli_dto: UpdateUserTypeDto = UpdateUserTypeDto(user_type=UserType.employer)
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.post(url=f"{endpoint_url}/api/users/type", headers=headers, json=jobli_dto.dict())

    # then assert
    assert response.status_code == HTTPStatus.OK


# noinspection PyPep8Naming
def test_job_seekers_crud_against_dynamo_db(endpoint_url):
    assert os.environ["JOB_SEEKERS_TABLE_NAME"] is not None
    print("\nseekers_table: ", os.environ["JOB_SEEKERS_TABLE_NAME"])

    job_seeker_id = str(uuid.uuid4())
    full_name = str(uuid.uuid4())
    address = str(uuid.uuid4())
    job_seeker_dict = {
        "id": job_seeker_id,
        "full_name": full_name,
        "birth_date": 11003484,
        "address": address,
        "email": "dummy@company.com"}
    job_seeker = JobSeeker(**job_seeker_dict)
    job_seeker_repository.create(job_seeker=job_seeker, user="testUser")

    job_seeker_read = JobSeeker(**job_seeker_repository.get(job_seeker_id=job_seeker_id))

    assert job_seeker_read.creationTime is not None
    assert job_seeker_read.version == 0
    assert job_seeker_read.id == job_seeker_id
    assert job_seeker_read.address == address

    # job_seeker_dict = job_seeker_repository.get(job_seeker_id)

    job_seeker_read.address = "new address"
    job_seeker_repository.update(job_seeker_read, user="11111")

    job_seeker_read = JobSeeker(**job_seeker_repository.get(job_seeker_id=job_seeker_id))
    assert job_seeker_read.address == "new address"
    assert job_seeker_read.version == 1

    # delete and validate it does not exist
    job_seeker_repository.delete(job_seeker_id)
    try:
        JobSeeker(**job_seeker_repository.get(job_seeker_id=job_seeker_id))
        raise Exception("Expected NotFoundError")
    except NotFoundError:
        # all good
        pass


def test_create_delete_read_experience(endpoint_url):
    assert os.environ["JOB_SEEKERS_TABLE_NAME"] is not None
    print("\nseekers_table: ", os.environ["JOB_SEEKERS_TABLE_NAME"])

    new_experience_id = str(uuid.uuid4())
    job_seeker_id = "11111"
    experience_dict = {
        "end_year": 2000,
        "experience_id": new_experience_id,
        "job_seeker_id": job_seeker_id,
        "role": "cook",
        "role_description": "do some cooking",
        "start_year": 2018,
        "workplace_name": "CyberArk Dining Room"
    }
    experience = Experience(**experience_dict)
    job_seeker_experience_repository.create(experience)

    experience_list = job_seeker_experience_repository.get_all(job_seeker_id=job_seeker_id)
    assert len(list(filter(lambda x: x.experience_id == new_experience_id, experience_list))) == 1

    new_experience = job_seeker_experience_repository.get(job_seeker_id=job_seeker_id, experience_id=new_experience_id)
    assert new_experience.experience_id == new_experience_id

    job_seeker_experience_repository.delete(job_seeker_id=job_seeker_id, experience_id=new_experience_id)

    try:
        job_seeker_experience_repository.get(job_seeker_id=job_seeker_id, experience_id=new_experience_id)
        raise Exception("Expected not to find this experience")
    except NotFoundError:
        # all good. this is what we expected
        pass

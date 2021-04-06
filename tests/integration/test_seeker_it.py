# pylint: disable = print-used
import json
import os
from datetime import datetime
from http import HTTPStatus

import pytest
import requests
from dotenv import load_dotenv

from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto
from service.dtos.job_seeker_profile_dto import JobSeekerProfileDto
# from cdk.jobli_service_cdk.service_stack.jobli_construct import get_stack_name
# from jobli_service_cdk.service_stack.constants import BASE_NAME
from service.dtos.jobli_dto import JobliDto, UpdateUserTypeDto, UserType
from tests.helpers.cognito_auth_util import add_auth_header
from tests.helpers.environment_handler import load_env_vars, get_stack_name
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


def test_add_seeker_answers(endpoint_url, auth_headers):
    # when create entity

    answers_dto: [JobSeekerAnswerDto] = []

    for i in range(1, 10):
        answers_dto.append(JobSeekerAnswerDto(key="a" + str(i), question="q" + str(i), answer=True))

    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    json_body = json.dumps([ob.__dict__ for ob in answers_dto])
    response = requests.api.post(url=f"{endpoint_url}/api/seeker/answers", headers=headers, data=json_body)

    # then assert created
    assert response.status_code == HTTPStatus.OK


def test_set_user_type(endpoint_url, auth_headers):
    # when create entity
    jobli_dto: UpdateUserTypeDto = UpdateUserTypeDto(user_type=UserType.employer)
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.post(url=f"{endpoint_url}/api/users/type", headers=headers, json=jobli_dto.dict())

    # then assert
    assert response.status_code == HTTPStatus.OK


def test_read_job_seekers_table_name():
    os.environ["PROJECT_DIR"] = "/Users/Amir.Zahavi/Git/jobli-backend"
    # seekers_table = get_stack_output(get_stack_name(), 'JOB_SEEKERS_TABLE_NAME')

    print("=========")
    print("get_stack_name(): ", get_stack_name())
    print("seekers_table: ", os.environ["JOB_SEEKERS_TABLE_NAME"])
    # print("seekers_table: ", seekers_table)
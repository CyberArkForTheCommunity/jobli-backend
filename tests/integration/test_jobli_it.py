# pylint: disable = print-used
import json
import requests
import os
from datetime import datetime
from http import HTTPStatus
import pytest
from dotenv import load_dotenv
from tests.helpers.environment_handler import load_env_vars, get_stack_name
from tests.helpers.random_utils import random_string
from tests.helpers.cognito_auth_util import add_auth_header

# from cdk.jobli_service_cdk.service_stack.jobli_construct import get_stack_name
# from jobli_service_cdk.service_stack.constants import BASE_NAME
from service.dtos.jobli_dto import JobliDto


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


def test_create_jobli(endpoint_url, auth_headers):
    # when create entity
    jobli_dto: JobliDto = JobliDto(name=random_string())
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.post(url=f"{endpoint_url}/jobli", headers=headers, json=jobli_dto.dict())

    # then assert created
    assert response.status_code == HTTPStatus.CREATED
    # assert created_date & updated_date was initialize
    resource = json.loads(response.content)
    assert resource['name'] == jobli_dto.name
    day_seconds = 24 * 60 * 60
    now = datetime.now().timestamp()
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert resource['created_date'] == resource['updated_date']

    # when get the created entity
    response = requests.api.get(url=f"{endpoint_url}/jobli/{jobli_dto.name}", headers=auth_headers)

    # then assert all fields saved successfully
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    assert resource['name'] == jobli_dto.name
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert resource['created_date'] == resource['updated_date']


def test_get_jobli(endpoint_url, auth_headers):
    # read by name
    response = requests.api.get(url=f"{endpoint_url}/jobli/Alex", headers=auth_headers)
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    assert resource['name'] == "Alex"
    day_seconds = 24 * 60 * 60
    now = datetime.now().timestamp()
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert resource['created_date'] == resource['updated_date']


def test_update_jobli(endpoint_url, auth_headers):
    # when create entity
    jobli_dto: JobliDto = JobliDto(name=random_string())
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    requests.api.post(url=f"{endpoint_url}/jobli", headers=headers, json=jobli_dto.dict())

    # then update the entity
    response = requests.api.put(url=f"{endpoint_url}/jobli/{jobli_dto.name}", headers=headers,
                                json=jobli_dto.dict())

    # then assert
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    day_seconds = 24 * 60 * 60
    now = datetime.now().timestamp()
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert now - day_seconds < resource['updated_date'] < now + day_seconds
    assert resource['created_date'] < resource['updated_date']

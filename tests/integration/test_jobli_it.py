# pylint: disable = print-used
import json
import requests
import os
from datetime import datetime
from http import HTTPStatus
import pytest
from tests.helpers.environment_handler import load_env_vars
from tests.helpers.random_utils import random_string

# from cdk.jobli_service_cdk.service_stack.jobli_construct import get_stack_name
# from jobli_service_cdk.service_stack.constants import BASE_NAME
from service.dtos.jobli_dto import JobliDto


@pytest.fixture(scope="module")
def endpoint_url():
    stack_name = "Jobli"
    # load_env_vars(get_stack_name(BASE_NAME))
    load_env_vars(stack_name)
    endpoint_url = os.environ['JOBLI_API_GW']
    return endpoint_url[:-1]


def test_create_jobli(endpoint_url):
    # when create entity
    jobli_dto: JobliDto = JobliDto(name=random_string())
    response = requests.api.post(url=f"{endpoint_url}/jobli", headers={"Content-Type": "application/json"}, json=jobli_dto.json())

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
    response = requests.api.get(url=f"{endpoint_url}/jobli/{jobli_dto.name}", headers={})

    # then assert all fields saved successfully
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    assert resource['name'] == jobli_dto.name
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert resource['created_date'] == resource['updated_date']


def test_get_jobli(endpoint_url):
    # read by name
    response = requests.api.get(url=f"{endpoint_url}/jobli/Alex", headers={})
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    assert resource['name'] == "Alex"
    day_seconds = 24 * 60 * 60
    now = datetime.now().timestamp()
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert resource['created_date'] == resource['updated_date']


def test_update_jobli(endpoint_url):
    # when create entity
    jobli_dto: JobliDto = JobliDto(name=random_string())
    requests.api.post(url=f"{endpoint_url}/jobli", headers={"Content-Type": "application/json"}, json=jobli_dto.json())

    # then update the entity
    response = requests.api.put(url=f"{endpoint_url}/jobli/{jobli_dto.name}", headers={"Content-Type": "application/json"}, json=jobli_dto.json())

    # then assert
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    day_seconds = 24 * 60 * 60
    now = datetime.now().timestamp()
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert now - day_seconds < resource['updated_date'] < now + day_seconds
    assert resource['created_date'] < resource['updated_date']

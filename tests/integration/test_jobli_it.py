# pylint: disable = print-used
import json
import os
from datetime import datetime
from http import HTTPStatus
import pytest
from dotenv import load_dotenv
from infra_automation_utils.environment_handler import load_env_vars
from infra_automation_utils.random_utils import random_string
from infra_automation_utils.api_utils.api_util import ApiUtil

from stack_utils.stack_name import get_stack_name
from service.dtos.jobli_dto import JobliDto
from jobli_service_cdk.service_stack.constants import BASE_NAME


@pytest.fixture(scope="module")
def api():
    if os.environ.get('USER_NAME') is None:
        load_dotenv()
    load_env_vars(get_stack_name(BASE_NAME))
    return ApiUtil(endpoint_url=os.environ['JOBLI_API_GW'])


def test_create_jobli(api):
    # when create entity
    jobli_dto: JobliDto = JobliDto(name=random_string())
    response = api.post("/jobli", headers={"Content-Type": "application/json"}, body=jobli_dto.json())

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
    response = api.get(f'/jobli/{jobli_dto.name}', headers={})

    # then assert all fields saved successfully
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    assert resource['name'] == jobli_dto.name
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert resource['created_date'] == resource['updated_date']


def test_get_jobli(api):
    # read by name
    response = api.get('/jobli/Alex', headers={})
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    assert resource['name'] == "Alex"
    day_seconds = 24 * 60 * 60
    now = datetime.now().timestamp()
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert resource['created_date'] == resource['updated_date']


def test_update_jobli(api):
    # when create entity
    jobli_dto: JobliDto = JobliDto(name=random_string())
    api.post("/jobli", headers={"Content-Type": "application/json"}, body=jobli_dto.json())

    # then update the entity
    response = api.put(f'/jobli/{jobli_dto.name}', headers={"Content-Type": "application/json"}, body=jobli_dto.json())

    # then assert
    assert response.status_code == HTTPStatus.OK
    resource = json.loads(response.content)
    day_seconds = 24 * 60 * 60
    now = datetime.now().timestamp()
    assert now - day_seconds < resource['created_date'] < now + day_seconds
    assert now - day_seconds < resource['updated_date'] < now + day_seconds
    assert resource['created_date'] < resource['updated_date']

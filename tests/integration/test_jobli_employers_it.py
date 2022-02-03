import random
import string
import json

import requests
import os
from datetime import datetime, timedelta
from http import HTTPStatus
import pytest
from dotenv import load_dotenv
from pydantic.networks import HttpUrl
from service.models.employer.employer_job import EmployerJob, JobScope
from tests.helpers.environment_handler import load_env_vars
from tests.helpers.cognito_auth_util import add_auth_header
from service.models.employer.employer import Employer
from service.models.common.address import Address
from typing import List

SOME_EMPLOYER = Employer(
    employer_email="a@b.c",
    business_name="some_business",
    business_address=Address(full_address="some address in some city"),
    business_website="https://www.some-site.com",
    description="This is a description of some business",
    employer_terms=["Term1", "Term2"]
)


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


def get_random_email(name_length: int, domain: str) -> str:
    return ''.join(random.choice(string.ascii_letters) for x in range(name_length)) + domain


def get_employer_by_name(business_name: str, existing_employers: List[Employer]) -> Employer:
    for employer in existing_employers:
        if employer.business_name == business_name:
            return employer
    return None


# @pytest.mark.skip(reason="This test is to fill employer_and_jobs_from_file")
def test_create_jobli_employer_and_jobs_from_file(endpoint_url, auth_headers):
    try:
        project_dir: str = os.getenv('PROJECT_DIR')
        job_test_file = open(f"{project_dir}/tests/resources/Jobli_jobs.json", encoding="UTF-8")
        test_data = json.load(job_test_file)

        # get existing employers in db table, later if the employer already exist the employer  wont be created
        existing_employers: List[Employer] = get_exiting_employer_list(auth_headers, endpoint_url)
        print(existing_employers)

        # iterate the josn file, if employer already exist - skip insert, alway create a job
        for employer_data in test_data:

            employer: Employer = Employer.parse_obj(employer_data)
            # check if employer already stored, skip insert if exist
            persist_employer: Employer = get_employer_by_name(employer.business_name, existing_employers)
            if not persist_employer:
                # create employer
                employer.employer_email = get_random_email(5, "@gmail.com")
                employer.employer_terms = ["הודעה ראשונה", "הודעה שניה"]

                employer.business_website = HttpUrl(f'https://www.global.com', scheme='https', host="global")

                # address handling
                address: Address = Address()
                address.city = "פתח תקוה"
                address.apartment = random.randint(1, 1000)
                address.street = "ג׳בוטינסקי"
                address.full_address = f"{address.city} {address.street} {address.apartment}"
                employer.business_address = address

                persist_employer = save_new_employer(auth_headers, employer, endpoint_url)
                print(f"new object: {persist_employer}")

            # create and store a job
            job: EmployerJob = EmployerJob(**employer_data)
            job.employer_id = persist_employer.employer_id

            save_new_job(auth_headers, job, endpoint_url)
    except IOError as exc:
        print(f"error on data population:: validate the json file path")
        assert False
    finally:
        job_test_file.close()


def get_exiting_employer_list(auth_headers, endpoint_url) -> List[Employer]:
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.get(url=f"{endpoint_url}/api/employers", headers=headers)
    assert response.status_code == HTTPStatus.OK
    employer_list: List[Employer] = []
    employees_json = json.loads(response.text)["employers"]
    for emp in employees_json:
        employ = Employer(**json.loads(emp))
        employer_list.append(employ)

    return employer_list


def save_new_employer(auth_headers, employer, endpoint_url) -> Employer:
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.post(url=f"{endpoint_url}/api/employers", headers=headers, json=employer.dict())
    assert response.status_code == HTTPStatus.CREATED
    returned_employer: Employer = Employer.parse_obj(response.json())
    assert returned_employer.employer_id
    return returned_employer


def save_new_job(auth_headers: dict, job: EmployerJob, endpoint_url: str) -> EmployerJob:
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.post(url=f"{endpoint_url}/api/employers/{job.employer_id}/jobs", headers=headers,
                                 json=job.dict())
    assert response.status_code == HTTPStatus.CREATED
    returned_job: Employer = EmployerJob.parse_obj(response.json())
    assert returned_job.job_id
    return returned_job


def test_create_jobli_employer(endpoint_url, auth_headers):
    # Create the employer
    employer = SOME_EMPLOYER
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.post(url=f"{endpoint_url}/api/employers", headers=headers, json=employer.dict())

    # Assert and test
    assert response.status_code == HTTPStatus.CREATED
    returned_employer: Employer = Employer.parse_obj(response.json())
    assert returned_employer.business_name == employer.business_name
    assert returned_employer.employer_email == employer.employer_email
    assert returned_employer.business_website == employer.business_website
    assert returned_employer.description == employer.description
    assert returned_employer.employer_id
    assert returned_employer.created_time < (datetime.now() + timedelta(days=1)).timestamp()

    # Get the created entity
    response = requests.api.get(url=f"{endpoint_url}/api/employers/{returned_employer.employer_id}",
                                headers=headers)
    assert response.status_code == HTTPStatus.OK
    returned_employer = Employer.parse_obj(response.json())
    assert returned_employer.business_name == employer.business_name
    assert returned_employer.employer_email == employer.employer_email
    assert returned_employer.business_website == employer.business_website
    assert returned_employer.description == employer.description
    assert returned_employer.employer_id
    assert returned_employer.created_time < (datetime.now() + timedelta(days=1)).timestamp()


def test_update_jobli_employer(endpoint_url, auth_headers):
    value = "{\"employer_id\": \"261fe233-8da8-4dfd-af77-f5c7acba7409\", \"employer_email\": \"a@b.c\", \"business_name\": \"some business updated\", \"business_address\": {\"full_address\": \"some address in some city\", \"city\": null, \"street\": null, \"apartment\": null}, \"business_website\": \"https://www.new-website.com\", \"description\": \"The description changed!\", \"employer_terms\": [\"Term1\", \"Term2\", \"Term3\"], \"business_media\": null}"

    employer_value = Employer.parse_raw(value)

    # Create the employer
    employer = SOME_EMPLOYER
    employer.business_name = "some business updated"
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    response = requests.api.post(url=f"{endpoint_url}/api/employers", headers=headers, json=employer.dict())

    # Assert and test
    assert response.status_code == HTTPStatus.CREATED
    returned_employer: Employer = Employer.parse_obj(response.json())
    assert returned_employer.business_name == employer.business_name
    assert returned_employer.employer_email == employer.employer_email
    assert returned_employer.business_website == employer.business_website
    assert returned_employer.description == employer.description
    assert returned_employer.employer_id
    assert returned_employer.created_time < (datetime.now() + timedelta(days=1)).timestamp()

    # Update the employer
    returned_employer.employer_terms.append("Term3")
    returned_employer.description = "The description changed!"
    returned_employer.business_website = "https://www.new-website.com"
    returned_employer.business_address.full_address = "check address changed"
    returned_employer.business_address.city = "Tel Aviv"

    # update_employer = Employer()
    # update_employer.employer_id = returned_employer.employer_id
    # update_employer.employer_terms = returned_employer.employer_terms
    # update_employer.employer_terms.append("Term3")
    # update_employer.description = "The description changed!"
    # update_employer.business_website = "https://www.new-website.com"
    returned_employer.__delattr__("created_time")

    response = requests.api.put(url=f"{endpoint_url}/api/employers/{returned_employer.employer_id}",
                                headers=headers, json=returned_employer.dict())
    assert response.status_code == HTTPStatus.OK
    returned_employer = Employer.parse_obj(response.json())
    assert returned_employer.business_name == employer.business_name
    assert returned_employer.employer_email == employer.employer_email
    assert returned_employer.description == "The description changed!"
    assert returned_employer.employer_id
    assert returned_employer.created_time < (datetime.now() + timedelta(days=1)).timestamp()


def test_get_employers(endpoint_url, auth_headers):
    # Add all the employers
    employers: List[Employer] = [SOME_EMPLOYER.copy() for _ in range(5)]
    headers = {"Content-Type": "application/json"}
    headers.update(auth_headers)
    for idx, e in enumerate(employers):
        e.business_name += str(idx)
        e.business_address.city = "SpecialTelAviv"
        response = requests.api.post(url=f"{endpoint_url}/api/employers", headers=headers, json=e.dict())
        assert response.status_code == HTTPStatus.CREATED
        returned_employer: Employer = Employer.parse_obj(response.json())
        assert returned_employer.business_name == e.business_name
        assert returned_employer.employer_email == e.employer_email
        assert returned_employer.business_website == e.business_website
        assert returned_employer.description == e.description
        assert returned_employer.employer_id
        assert returned_employer.created_time < (datetime.now() + timedelta(days=1)).timestamp()

    # Get all employers
    response = requests.api.get(url=f"{endpoint_url}/api/employers?city=SpecialTelAviv", headers=headers)
    assert response.status_code == HTTPStatus.OK

    returned_employers: List[Employer] = [Employer.parse_raw(item) for item in response.json()["employers"]]
    assert len(returned_employers) >= 5

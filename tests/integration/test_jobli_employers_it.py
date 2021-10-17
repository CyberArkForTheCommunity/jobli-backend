# pylint: disable = print-used
import requests
import os
from datetime import datetime, timedelta
from http import HTTPStatus
import pytest
from dotenv import load_dotenv
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

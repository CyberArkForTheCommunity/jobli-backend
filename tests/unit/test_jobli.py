import json

from pytest_mock import MockerFixture

from service import handler
from service.dtos.jobli_dto import JobliDto
from tests.unit.test_utils import random_string


def test_get_jobli(mocker: MockerFixture):
    jobli_dto: JobliDto = JobliDto(name=random_string())

    response = handler.get_jobli({"pathParameters": {"name": jobli_dto.name}}, mocker.MagicMock())
    actual_jobli = json.loads(response["body"])

    assert actual_jobli['name'] == jobli_dto.name

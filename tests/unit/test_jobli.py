import json
from aws_lambda_context import LambdaContext
from service.dtos.jobli_dto import JobliDto
from service import handler

from tests.unit.test_utils import random_string


def test_get_jobli():
    jobli_dto: JobliDto = JobliDto(name=random_string())

    response = handler.get_jobli({"pathParameters": {"name": jobli_dto.name}}, LambdaContext())
    actual_jobli = json.loads(response["body"])

    assert actual_jobli['name'] == jobli_dto.name

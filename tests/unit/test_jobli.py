import json
from infra_automation_utils.random_utils import random_string
from aws_lambda_context import LambdaContext
from service.dtos.jobli_dto import JobliDto
from service import handler


def test_get_jobli():
    jobli_dto: JobliDto = JobliDto(name=random_string())

    response = handler.get_jobli({"pathParameters": {"name": jobli_dto.name}}, LambdaContext())
    actual_jobli = json.loads(response["body"])

    assert actual_jobli['name'] == jobli_dto.name


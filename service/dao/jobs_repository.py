from typing import Dict, List
from pydantic import parse_obj_as

from aws_lambda_powertools import Logger
import boto3

from service.common.exceptions import NotFoundError
from service.common.utils import get_env_or_raise
from service.lambdas.employer.constants import EmployerConstants
from service.models.employer.employer_job import EmployerJob, JobSearchResult

logger = Logger()

class _JobsRepository:
    def get_jobs(self, answers: List[bool], max_results: int) -> List[JobSearchResult]:
        dynamo_resource = boto3.resource("dynamodb")
        jobs_table = dynamo_resource.Table(get_env_or_raise(EmployerConstants.JOBS_TABLE_NAME))
        results = parse_obj_as(List[EmployerJob], jobs_table.scan().get("Items", []))
        jobs = []
        for item in results:
            score = 0
            for i in range(1, 10):
                score += (answers[i - 1] == item.get('a' + str(i)))
            jobs.append(JobSearchResult(score=score, employer_job=item))
        return sorted(jobs, key=lambda x: x.score, reverse=True)[:max_results]


jobs_repository: _JobsRepository = _JobsRepository()

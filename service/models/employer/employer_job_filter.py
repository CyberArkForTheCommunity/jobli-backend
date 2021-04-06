from pydantic import BaseModel, Field
from typing import Optional
from service.lambdas.employer.constants import EmployerConstants


class EmployerJobFilter(BaseModel):
    job_id: Optional[str]
    last_pagination_key: Optional[str]
    limit_per_page: Optional[int] = Field(default=EmployerConstants.LIMITS_PER_EMPLOYER_PAGE)

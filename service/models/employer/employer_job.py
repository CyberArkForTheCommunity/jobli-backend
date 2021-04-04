from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import timedelta
from service.models.common import Question


class JobScope(str, Enum):
    Full = "full",
    Partial = "partial",
    TimeBased = "time_based"


class EmployerJob(BaseModel):
    employer_id: str = Field(description="Related employer ID")
    job_fields: List[str] = Field(description="List of fields for the job")
    job_name: str = Field(description="Name of the job")
    job_description: str = Field(description="Description of the job")
    job_employees_count: int = Field(description="Amount of employees needed for the job")
    job_scope: JobScope = Field(description="Scope of the job in time")
    job_time_scope: Optional[List[timedelta]] = Field(description="Time deltas of the job if TimeBased")
    questions: List[Question] = Field(description="Questions of the employer job")
    job_requirements: Optional[List[str]] = Field(description="Job requirmenets needed")
    job_salary: Optional[int] = Field(description="Optional job salary")
    job_experience_needed: str = Field(description="Experience needed for the job")

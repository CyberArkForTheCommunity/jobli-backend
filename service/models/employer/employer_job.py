from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import timedelta
from service.models.common import Answer
from decimal import Decimal


class JobScope(str, Enum):
    Full = "full",
    Partial = "partial",
    TimeBased = "time_based"


class EmployerJob(BaseModel):
    job_id: Optional[str] = Field(description="Job ID")
    employer_id: Optional[str] = Field(description="Related employer ID")
    job_fields: Optional[List[str]] = Field(description="List of fields for the job")
    job_name: Optional[str] = Field(description="Name of the job")
    job_description: Optional[str] = Field(description="Description of the job")
    job_employees_count: Optional[int] = Field(description="Amount of employees needed for the job")
    job_scope: Optional[JobScope] = Field(description="Scope of the job in time")
    job_time_scope: Optional[List[timedelta]] = Field(description="Time deltas of the job if TimeBased")
    answers: Optional[List[Answer]] = Field(description="Questions of the employer job")
    job_requirements: Optional[List[str]] = Field(description="Job requirmenets needed")
    job_salary: Optional[int] = Field(description="Optional job salary")
    job_experience_needed: Optional[str] = Field(description="Experience needed for the job")
    created_time: Optional[Decimal] = Field(description="Creation time of the employer job")

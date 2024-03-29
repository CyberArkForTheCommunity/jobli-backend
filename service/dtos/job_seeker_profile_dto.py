# pylint: disable=no-name-in-module
from typing import Optional

from pydantic import BaseModel, validator


class JobSeekerProfileDto(BaseModel):
    full_name: str
    birth_year: int
    birth_month: int
    birth_day: int
    address: str
    email: str
    about_me: Optional[str]
    job_ambitions: Optional[str]
    hobbies: Optional[str]

    # pylint: disable=no-self-argument,no-self-use,invalid-name
    # noinspection PyMethodParameters
    @validator('full_name')
    def validate_changes(cls, v):
        if not v:
            raise ValueError('full name cannot be empty')
        return v

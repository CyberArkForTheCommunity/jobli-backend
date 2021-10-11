# pylint: disable=no-name-in-module
from pydantic import BaseModel, validator


class JobSeekerExperienceDto(BaseModel):
    workplace_name: str
    start_year: int
    end_year: int
    role: str
    role_description: str

    # pylint: disable=no-self-argument,no-self-use,invalid-name
    # noinspection PyMethodParameters
    @validator('workplace_name')
    def validate_changes(cls, v):
        if not v:
            raise ValueError('workspace name name cannot be empty')
        return v

# pylint: disable=no-name-in-module
from enum import Enum
from pydantic import BaseModel, validator


class JobliDto(BaseModel):
    name: str

    # pylint: disable=no-self-argument,no-self-use,invalid-name
    # noinspection PyMethodParameters
    @validator('name')
    def validate_changes(cls, v):
        if not v:
            raise ValueError('name cannot be empty')
        return v


class UserType(str, Enum):
    employer = 'employer'
    job_seeker = 'job_seeker'


class UpdateUserTypeDto(BaseModel):
    user_type: UserType

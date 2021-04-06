# pylint: disable=no-name-in-module
from pydantic import BaseModel, validator


class JobSeekerAnswerDto(BaseModel):
    key: str
    question: str
    answer: bool

    # pylint: disable=no-self-argument,no-self-use,invalid-name
    @validator('key')
    def validate_changes(cls, v):
        if not v:
            raise ValueError('key name cannot be empty')
        return v

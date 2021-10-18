# pylint: disable=no-name-in-module
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator, Field


class Jobli(BaseModel):
    name: str
    created_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_date: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # pylint: disable=no-self-argument,no-self-use,invalid-name
    # noinspection PyMethodParameters
    @validator('name')
    def validate_changes(cls, v):
        if not v:
            raise ValueError('name cannot be empty')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%FT%T%z")
        }
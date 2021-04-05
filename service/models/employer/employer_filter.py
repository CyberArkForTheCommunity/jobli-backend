from pydantic import BaseModel, Field
from typing import Optional


class EmployerFilter(BaseModel):
    employer_id: Optional[str]
    business_name: Optional[str]
    city: Optional[str]
    last_pagination_key: Optional[str]
    limit_per_page: Optional[int] = Field(default=100)

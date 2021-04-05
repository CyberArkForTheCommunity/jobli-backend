from pydantic import BaseModel, HttpUrl, AnyUrl, Field
from service.models.common import Address
from typing import List, Optional


class Employer(BaseModel):
    employer_id: Optional[str] = Field(description="ID of the employer")
    employer_email: str = Field(description="")
    business_name: str = Field(description="Name of the business")
    business_address: Address = Field(description="Address of the employer")
    business_website: HttpUrl = Field(description="Website of the business")
    description: str = Field(description="Description of the business")
    employer_terms: List[str] = Field(description="Terms to be applied to the employer")
    business_media: List[AnyUrl] = Field(description="List of media urls to s3 for the business")

from pydantic import BaseModel, HttpUrl, AnyUrl, Field
from service.models.common import Address
from typing import List, Optional
from datetime import datetime


class Employer(BaseModel):
    employer_id: Optional[str] = Field(description="ID of the employer")
    employer_email: Optional[str] = Field(description="Email of the employer")
    business_name: Optional[str] = Field(description="Name of the business")
    business_address: Optional[Address] = Field(description="Address of the employer")
    business_website: Optional[HttpUrl] = Field(description="Website of the business")
    description: Optional[str] = Field(description="Description of the business")
    employer_terms: Optional[List[str]] = Field(description="Terms to be applied to the employer")
    business_media: Optional[List[AnyUrl]] = Field(description="List of media urls to s3 for the business")
    created_time: Optional[datetime] = Field(description="Creation time of the employer")
from pydantic import BaseModel, Field
from typing import Optional


class Address(BaseModel):
    full_address: Optional[str] = Field(description="Full address of the object")
    city: Optional[str] = Field(description="City of the object")
    street: Optional[str] = Field(description="Street of the object")
    apartment: Optional[str] = Field(description="Apartment info of the object")

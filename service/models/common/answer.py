from pydantic import BaseModel, Field


class Answer(BaseModel):
    key: str = Field(description="Name of the question")
    question: str = Field(description="The actual question")
    answer: bool = Field(description="Boolean answer")

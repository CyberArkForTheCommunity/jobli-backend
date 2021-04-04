from pydantic import BaseModel, Field


class Question(BaseModel):
    question_text: str = Field()

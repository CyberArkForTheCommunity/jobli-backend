from pydantic import BaseModel


class Answer(BaseModel):
    key: str
    question: int
    answer: bool

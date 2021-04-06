from typing import Dict, Optional

from pydantic.main import BaseModel

from service.dao.single_table_service import SingleTableRecord


class Experience(BaseModel, SingleTableRecord):
    # def __init__(self, **kwargs):
    #     if 'version' not in kwargs:
    #         self.version = 0
    #     for attribute, value in kwargs.items():
    #         if hasattr(self, attribute):
    #             setattr(self, attribute, value)

    experience_id: str
    workplace: str
    year_start: int
    year_end: Optional[int]
    role: Optional[str]
    role_description: Optional[str]

    creationTime: Optional[str]
    lastUpdatedTime: Optional[str]
    version: int = 0

    def produce_pk(self) -> str:
        pass

    def produce_sk(self) -> str:
        pass

    def produce_gsi1_sk(self) -> Optional[str]:
        pass

    def produce_gsi1_pk(self) -> Optional[str]:
        pass

    def as_dict(self) -> Dict:
        pass

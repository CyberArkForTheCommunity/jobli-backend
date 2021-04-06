from typing import Dict

from service.dao.single_table_service import SingleTableRecord


class Experience(SingleTableRecord):
    def __init__(self, **kwargs):
        if 'version' not in kwargs:
            self.version = 0
        for attribute, value in kwargs.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)

    experience_id: str = None
    workplace: str = None
    year_start: int = None
    year_end: int = None
    role: str = None
    role_description: str = None

    creationTime: str = None
    lastUpdatedBy: str = None
    version: int = 0

    def produce_pk(self) -> str:
        pass

    def produce_sk(self) -> str:
        pass

    def produce_gsi1_sk(self) -> str:
        pass

    def produce_gsi1_pk(self) -> str:
        pass

    def as_dict(self) -> Dict:
        pass

from typing import Dict

from service.dao.single_table_service import SingleTableRecord


class Skill(SingleTableRecord):

    def __init__(self, **kwargs):
        if 'version' not in kwargs:
            self.version = 0
        for attribute, value in kwargs.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)

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

    id: str = None
    name: str = None

    creationTime: str = None
    lastUpdatedBy: str = None
    version: int = 0
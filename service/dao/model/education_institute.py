from typing import Optional, Dict

from service.dao.single_table_service import SingleTableRecord


class EducationInstitute(SingleTableRecord):
    def __init__(self, **kwargs):
        if 'version' not in kwargs:
            self.version = 0
        for attribute, value in kwargs.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)

    institute_id: str
    name: str
    year_start: int
    year_end: Optional[int]
    certificate: Optional[str]

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

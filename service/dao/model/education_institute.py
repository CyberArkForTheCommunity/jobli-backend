from typing import Optional, Dict

from service.dao.single_table_service import SingleTableRecord


class EducationInstitute(SingleTableRecord):
    institute_id: str
    name: str
    year_start: int
    year_end: Optional[int]
    certificate: Optional[str]

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

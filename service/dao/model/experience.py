from typing import Dict

from service.dao.single_table_service import SingleTableRecord


class Experience(SingleTableRecord):
    experience_id: str = None
    workplace: str = None
    year_start: int = None
    year_end: int = None
    role: str = None
    role_description: str = None

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

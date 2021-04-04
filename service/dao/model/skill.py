from typing import Dict

from service.dao.single_table_service import SingleTableRecord


class Skill(SingleTableRecord):
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
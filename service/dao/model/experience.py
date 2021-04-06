from typing import Dict, Optional

from pydantic.main import BaseModel

from service.dao.single_table_service import SingleTableRecord, DATA_DELIMITER

_EXPERIENCE_PK_PREFIX = "EXPERIENCE" + DATA_DELIMITER
EXPERIENCE_SK_PREFIX = "EXPERIENCE_ID" + DATA_DELIMITER

class Experience(BaseModel, SingleTableRecord):
    # def __init__(self, **kwargs):
    #     if 'version' not in kwargs:
    #         self.version = 0
    #     for attribute, value in kwargs.items():
    #         if hasattr(self, attribute):
    #             setattr(self, attribute, value)
    job_seeker_id: str
    experience_id: str
    workplace_name: str
    start_year: int
    end_year: Optional[int]
    role: Optional[str]
    role_description: Optional[str]

    creationTime: Optional[str]
    lastUpdatedTime: Optional[str]
    version: int = 0

    @staticmethod
    def build_pk(job_seeker_id: str):
        return _EXPERIENCE_PK_PREFIX + DATA_DELIMITER + job_seeker_id

    @staticmethod
    def build_sk(experience_id: str):
        return EXPERIENCE_SK_PREFIX + experience_id

    def produce_pk(self) -> str:
        return self.build_pk(self.job_seeker_id)

    def produce_sk(self) -> str:
        return self.build_sk(self.experience_id)

    def produce_gsi1_sk(self) -> Optional[str]:
        pass

    def produce_gsi1_pk(self) -> Optional[str]:
        pass

    def as_dict(self) -> Dict:
        return self.dict()

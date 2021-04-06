from typing import Dict

from service.dao.single_table_service import DATA_DELIMITER, SingleTableRecord

JOB_SEEKER_ANSWERS_PK = "JOB_SEEKER_ANSWER"
JOB_SEEKER_ANSWERS_SK_PREFIX = "JOB_SEEKER_ID"


class JobSeekerAnswers(SingleTableRecord):

    def __init__(self, **kwargs):
        if 'version' not in kwargs:
            self.version = 0
        for attribute, value in kwargs.items():
            if hasattr(self, attribute):
                setattr(self, attribute, value)

    job_seeker_id: str
    job_seeker_name: str
    a1: bool = None
    a2: bool = None
    a3: bool = None
    a4: bool = None
    a5: bool = None
    a6: bool = None
    a7: bool = None
    a8: bool = None
    a9: bool = None
    a10: bool = None

    creationTime: str = None
    lastUpdatedBy: str = None
    version: int = 0

    @staticmethod
    def build_pk():
        return JOB_SEEKER_ANSWERS_PK

    @staticmethod
    def build_sk(job_seeker_id: str):
        return JOB_SEEKER_ANSWERS_SK_PREFIX + DATA_DELIMITER + job_seeker_id

    def produce_pk(self) -> str:
        return self.build_pk()

    def produce_sk(self) -> str:
        return self.build_sk(self.job_seeker_id)

    def produce_gsi1_pk(self) -> str:
        return None

    def produce_gsi1_sk(self) -> str:
        return None

    def as_dict(self) -> Dict:
        return self.__dict__

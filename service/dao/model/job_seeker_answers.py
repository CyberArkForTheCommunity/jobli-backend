from typing import Dict

from service.dao.single_table_service import DATA_DELIMITER, SingleTableRecord

JOB_SEEKER_ANSWERS_PK_PREFIX = "JOB_SEEKER_ANSWERS" + DATA_DELIMITER


class JobSeekerAnswers(SingleTableRecord):
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

    @staticmethod
    def build_pk(job_seeker_id: str):
        return JOB_SEEKER_ANSWERS_PK_PREFIX + job_seeker_id

    @staticmethod
    def build_sk():
        return DATA_DELIMITER

    def produce_pk(self) -> str:
        return self.build_pk(self.job_seeker_id)

    def produce_sk(self) -> str:
        return DATA_DELIMITER

    def produce_gsi1_pk(self) -> str:
        return None

    def produce_gsi1_sk(self) -> str:
        return None

    def as_dict(self) -> Dict:
        return self.__dict__

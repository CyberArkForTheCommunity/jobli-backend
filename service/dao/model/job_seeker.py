from typing import Dict

# from file_management.jobli.service.single_table_service import SingleTableRecord
from service.dao.single_table_service import SingleTableRecord, DATA_DELIMITER

JOB_SEEKER_PK_PREFIX = "JOB_SEEKER" + DATA_DELIMITER
FILES_PK1_CUSTOMER_ID_PREFIX = "CUSTOMER" + DATA_DELIMITER
FILES_SK1_TYPE_PREFIX = "TYPE" + DATA_DELIMITER


class JobSeeker(SingleTableRecord):
    id: str = None
    full_name: str = None
    birth_date: str = None
    city: str = None
    street: str = None
    apartment: int = None
    email: str = None

    # skills: List[Skill] = None
    # languages: List[Language] = None
    # education_institutes: List[EducationInstitute] = None
    # experience: List[Experience] = None
    # summary: str
    # job_ambitions: str
    # hobbies: str

    @staticmethod
    def build_pk(job_seeker_id: str):
        return JOB_SEEKER_PK_PREFIX + job_seeker_id

    @staticmethod
    def build_sk():
        return DATA_DELIMITER

    def produce_pk(self) -> str:
        return self.build_pk(self.id)

    def produce_sk(self) -> str:
        return DATA_DELIMITER

    def produce_gsi1_pk(self) -> str:
        return None

    def produce_gsi1_sk(self) -> str:
        return None

    def as_dict(self) -> Dict:
        return self.__dict__

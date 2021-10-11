from typing import List

from aws_lambda_powertools import Logger

from service.common.exceptions import NotFoundError
from service.dao.model.experience import Experience, EXPERIENCE_SK_PREFIX
from service.dao.single_table_service import single_table_service

logger = Logger()


class _JobSeekerExperienceRepository:

    def __init__(self):
        self.__single_table_service = single_table_service

    def create(self, experience: Experience, user: str = None) -> Experience:
        # if not user:
        #     user = SessionContext.get_user_name()
        logger.debug(f"saving experience {experience.__str__()} to db")
        dict_ret = self.__single_table_service.create_item(experience, user)
        return Experience(**dict_ret)

    def get_all(self, job_seeker_id: str) -> List[Experience]:
        dict_list = self.__single_table_service.find_by_pk_and_sk_begins_with(Experience.build_pk(job_seeker_id),
                                                                              EXPERIENCE_SK_PREFIX)
        return [Experience(**item) for item in dict_list]

    def get(self, job_seeker_id: str, experience_id: str) -> Experience:
        dict_ret = self.__single_table_service.find_by_pk_and_sk(Experience.build_pk(job_seeker_id),
                                                                 Experience.build_sk(experience_id))
        if not dict_ret:
            raise NotFoundError(f"JobSeeker experience with id='{experience_id}' not found")
        return Experience(**dict_ret)

    def delete(self, job_seeker_id: str, experience_id: str) -> None:
        self.__single_table_service.remove_item(pk=Experience.build_pk(job_seeker_id),
                                                sk=Experience.build_sk(experience_id))

    def update(self, experience: Experience, user: str = None) -> None:
        self.__single_table_service.update_item(experience, user)


job_seeker_experience_repository: _JobSeekerExperienceRepository = _JobSeekerExperienceRepository()

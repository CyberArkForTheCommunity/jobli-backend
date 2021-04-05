import logging
from typing import List

from pydantic import BaseModel

from service.dao.model.job_seeker_answers import JobSeekerAnswers, JOB_SEEKER_ANSWERS_PK, JOB_SEEKER_ANSWERS_SK_PREFIX
from service.dao.single_table_service import single_table_service

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    score: int
    job_seeker_id: str
    job_seeker_name: str


class _JobSeekerAnswersRepository:

    def __init__(self):
        self.__single_table_service = single_table_service

    def create(self, job_seeker_answers: JobSeekerAnswers, user: str = None) -> None:
        # if not user:
        #     user = SessionContext.get_user_name()
        logger.debug(f"saving file {job_seeker_answers.__str__()} to db")
        self.__single_table_service.create_item(job_seeker_answers, user)

    def find_best_match_answers(self, answers: List[bool], max_results: int = 100) -> List[SearchResult]:
        results = self.__single_table_service.find_by_pk_and_sk_begins_with(JOB_SEEKER_ANSWERS_PK,
                                                                            JOB_SEEKER_ANSWERS_SK_PREFIX)

        scores = []
        for item in results:
            score = 0
            for i in range(1, 10):
                score += (answers[i - 1] == item.get('a' + str(i)))
            scores.append(SearchResult(score=score,
                                       job_seeker_id=item.get('job_seeker_id'),
                                       job_seeker_name=item.get('job_seeker_name')))

            # in the future it will be better to keep just higher scores up to max_results
        return sorted(scores, key=lambda x: x.score, reverse=True)[:max_results]

    # def read(self, file_id: str) -> Dict:
    #     """
    #
    #     :param file_id:
    #     :return:
    #     :raises FileItemNotFoundError if no such file
    #     """
    #     file_record_dict = self.__single_table_service.find_by_pk_and_sk(File.build_pk(file_id), File.build_sk())
    #     if not file_record_dict:
    #         raise FileItemNotFoundError()
    #
    #     return file_record_dict
    #
    # def read_by_customer_id(self, customer_id: str, file_type: FileType = None) -> List[Dict]:
    #     file_type_str = file_type.value if file_type else ""
    #     ret = self.__single_table_service.find_all_by_gsi1pk_and_gsi1sk_begins_with(
    #         File.build_gsi1_pk(customer_id), File.build_gsi1_sk(file_type_str))
    #     if ret is None:
    #         return []
    #     else:
    #         return ret
    #
    # def read_all_files(self) -> List[dict]:
    #     return self.__single_table_service.find_all_by_pk_starts_with(FILES_PK_FILE_PREFIX)
    #

    # def update(self, file: File, user: str = None) -> None:
    #     self.__single_table_service.update_item(file, user)
    #
    # def delete(self, file_id: str) -> None:
    #     logger.info(f"Deleting file id '{file_id}'")
    #     self.__single_table_service.remove_item(File.build_pk(file_id), File.build_sk())


job_seeker_answers_repository: _JobSeekerAnswersRepository = _JobSeekerAnswersRepository()

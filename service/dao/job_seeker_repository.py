import logging
from typing import Dict

from service.common.exceptions import NotFoundError
from service.dao.single_table_service import single_table_service
from service.dao.model.job_seeker import JobSeeker

logger = logging.getLogger(__name__)


class _JobSeekerRepository:

    def __init__(self):
        self.__single_table_service = single_table_service

    def create(self, job_seeker: JobSeeker, user: str = None) -> None:
        # if not user:
        #     user = SessionContext.get_user_name()
        logger.debug(f"saving file {job_seeker.__str__()} to db")
        self.__single_table_service.create_item(job_seeker, user)

    def get(self, job_seeker_id: str) -> Dict:
        job_seeker_record_dict = self.__single_table_service.find_by_pk_and_sk(JobSeeker.build_pk(job_seeker_id), JobSeeker.build_sk())
        if not job_seeker_record_dict:
            raise NotFoundError(f"JobSeeker with id={job_seeker_id} not found")

        return job_seeker_record_dict

    def update(self, job_seeker: JobSeeker, user: str = None) -> None:
        self.__single_table_service.update_item(job_seeker, user)

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
    # def read_all_files_by_type(self, file_type: FileType) -> List[dict]:
    #     filter_expression = Attr('type').eq(file_type.value)
    #     return self.__single_table_service.scan_by_filter(filter_expression)
    #

    #
    # def delete(self, file_id: str) -> None:
    #     logger.info(f"Deleting file id '{file_id}'")
    #     self.__single_table_service.remove_item(File.build_pk(file_id), File.build_sk())


job_seeker_repository: _JobSeekerRepository = _JobSeekerRepository()

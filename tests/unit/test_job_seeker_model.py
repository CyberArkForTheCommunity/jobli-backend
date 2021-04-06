import json
import os
import unittest
import uuid

from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto


# noinspection PyMethodMayBeStatic
class JobSeekerModelTest(unittest.TestCase):

    @staticmethod
    def setUpClass(cls) -> None:
        os.environ["JOB_SEEKERS_TABLE_NAME"] = "JobliDorgjobseekercrudapi-Servicejoblijobseeker0340200E-1X6XOQWAXPFD8"

    def setUp(self) -> None:
        self.job_seeker_id = str(uuid.uuid4())
        self.full_name = str(uuid.uuid4())

    def test_read_from_db(self):
        job_seeker_dict = job_seeker_repository.get("11111")
        job_seeker: JobSeeker = JobSeeker(**job_seeker_dict)

        # job_seeker.birth_date = int(job_seeker.birth_date)
        # job_seeker.version = int(job_seeker.version)

        print(json.dumps(job_seeker.as_dict()))

        job_seeker.full_name = 'Test User 4'

        job_seeker_repository.update(job_seeker)

    def test_JobSeekerAnswers_model(self):
        answers_model = JobSeekerAnswers(job_seeker_id=self.job_seeker_id,
                                         job_seeker_name=self.full_name)

        # answers_model = answers.model

        self.__assert_new_model_atts(answers_model)

    def test_JobSeekerAnswers_pydantic_model_with_decimal_creation_time(self):
        answers_model = JobSeekerAnswers(job_seeker_id=self.job_seeker_id,
                                         job_seeker_name=self.full_name,
                                         creationTime="dummy")

        self.assertEqual("dummy", answers_model.creationTime)

        answers_model.json()
        my_dict = answers_model.dict()
        print(my_dict)

        str_json = answers_model.json()
        # str_json = json.dumps(answers_model)

        print(str_json)

    def test_model(self):
        dto = JobSeekerAnswerDto(key="a", question="q", answer=True)
        print(dto)
        print(dto.__dict__)
        s_obj = json.dumps(dto.__dict__)
        dto_list = [dto]
        print("s_obj", s_obj)

        json_string = json.dumps([ob.__dict__ for ob in dto_list])
        print("json_string", json_string)

        # s_dtos = json.dumps(dto_list)

    def __assert_new_model_atts(self, answers_model):
        self.assertEqual(self.job_seeker_id, answers_model.job_seeker_id)
        self.assertEqual(self.full_name, answers_model.job_seeker_name)
        self.assertEqual(0, answers_model.version)
        self.assertIsNone(answers_model.creationTime)
        self.assertIsNone(answers_model.lastUpdatedTime)

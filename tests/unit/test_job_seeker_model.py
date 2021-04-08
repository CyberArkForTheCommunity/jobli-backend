import json
import uuid

from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto

job_seeker_id: str = str(uuid.uuid4())
full_name: str = str(uuid.uuid4())


# noinspection PyPep8Naming
def test_JobSeekerAnswers_model():
    answers_model = JobSeekerAnswers(job_seeker_id=job_seeker_id,
                                     job_seeker_name=full_name)

    __assert_new_model_atts(answers_model)


# noinspection PyPep8Naming
def test_JobSeekerAnswers_pydantic_model_with_decimal_creation_time():
    answers_model = JobSeekerAnswers(job_seeker_id=job_seeker_id,
                                     job_seeker_name=full_name,
                                     creationTime="dummy")

    assert "dummy" == answers_model.creationTime
    answers_model.json()
    my_dict = answers_model.dict()
    print(my_dict)
    str_json = answers_model.json()
    print(str_json)


# noinspection PyPep8Naming
def test_JobSeekerAnswerDto():
    dto = JobSeekerAnswerDto(key="a", question="q", answer=True)
    print(dto)
    print(dto.__dict__)
    s_obj = json.dumps(dto.__dict__)
    dto_list = [dto]
    print("s_obj", s_obj)

    json_string = json.dumps([ob.__dict__ for ob in dto_list])
    print("json_string", json_string)


def __assert_new_model_atts(answers_model):
    assert job_seeker_id == answers_model.job_seeker_id
    assert full_name == answers_model.job_seeker_name
    assert 0 == answers_model.version
    assert answers_model.creationTime is None
    assert answers_model.lastUpdateTime is None

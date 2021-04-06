import json
import uuid

from service.dao.job_seeker_answers_repository import job_seeker_answers_repository
from service.dao.job_seeker_repository import job_seeker_repository
from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers

if __name__ == "__main__":

    # job_seeker = JobSeeker()
    # job_seeker.id = "11111" #str(uuid.uuid4())
    # job_seeker.city = "Tel Aviv"
    # job_seeker.birth_date = "10-07-1974"
    # job_seeker.apartment = 7
    # job_seeker.email = "testuser3@gmail.com"
    # job_seeker.full_name = "Test User 3"
    # job_seeker.street = "EEE"
    #
    # job_seeker_repository.create(job_seeker)

    job_seeker: JobSeeker = JobSeeker(**job_seeker_repository.get("11111"))

    #job_seeker.birth_date = int(job_seeker.birth_date)
    #job_seeker.version = int(job_seeker.version)

    print(json.dumps(job_seeker.as_dict()))

    job_seeker.full_name = 'Test User 4'

    job_seeker_repository.update(job_seeker)
    # job_seeker = JobSeeker()
    # job_seeker.id = "11111" #str(uuid.uuid4())
    # job_seeker.city = "Tel Aviv"
    # job_seeker.birth_date = "10-07-1974"
    # job_seeker.apartment = 7
    # job_seeker.email = "testuser3@gmail.com"
    # job_seeker.full_name = "Test User 3"
    # job_seeker.street = "EEE"

    #job_seeker_repository.create(job_seeker)



    #
    # answers = JobSeekerAnswers()
    # answers.a1 = True
    # answers.a2 = True
    # answers.a3 = True
    # answers.a4 = False
    # answers.a5 = True
    # answers.a6 = True
    # answers.a7 = False
    # answers.a8 = False
    # answers.a9 = True
    # answers.a10 = False
    #
    # answers.job_seeker_id = job_seeker.id
    # answers.job_seeker_name = job_seeker.full_name
    #
    # job_seeker_repository.create(job_seeker)
    #
    # job_seeker_answers_repository.create(answers)

    # job_seekers = job_seeker_answers_repository.find_best_match_answers(
    #     [True, False, True, False, False, False, False, False, False, True], 10)
    #
    # for result in job_seekers:
    #     print(result.job_seeker_name, ' - score=', result.score)

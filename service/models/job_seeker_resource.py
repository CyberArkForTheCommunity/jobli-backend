# pylint: disable=no-name-in-module
from pydantic import BaseModel
from typing import List

from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.dtos.job_seeker_answer_dto import JobSeekerAnswerDto
from service.dtos.job_seeker_experience_dto import JobSeekerExperienceDto
from service.dtos.job_seeker_profile_dto import JobSeekerProfileDto


class JobSeekerResource(BaseModel):
    profile: JobSeeker
#    experience: List[JobSeekerExperienceDto]

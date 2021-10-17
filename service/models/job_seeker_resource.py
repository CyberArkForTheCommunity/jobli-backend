# pylint: disable=no-name-in-module
from typing import List, Optional

from pydantic import BaseModel

from service.dao.model.job_seeker import JobSeeker
from service.dao.model.job_seeker_answers import JobSeekerAnswers
from service.dtos.job_seeker_experience_dto import JobSeekerExperienceDto


class JobSeekerResource(BaseModel):
    profile: Optional[JobSeeker]
    answers: Optional[JobSeekerAnswers]
    experience_list: Optional[List[JobSeekerExperienceDto]]


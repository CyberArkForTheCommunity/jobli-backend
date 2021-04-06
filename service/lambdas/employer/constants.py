from typing import Final


class EmployerConstants:
    EMPLOYERS_TABLE_NAME: Final = "EMPLOYERS_TABLE_NAME"
    JOBS_TABLE_NAME: Final = "JOBS_TABLE_NAME"
    LIMITS_PER_EMPLOYER_PAGE: Final = 100
    HEADERS = {
        'Content-Type': 'application/json',
        "Access-Control-Allow-Origin": "*"
    }
from datetime import date

from schema import ApplicationStatus, Job

job_1 = Job(
    company="example company 1",
    role="data engineer",
    location="Madrid/Remote",
    tags="Python, SQL",
    status=ApplicationStatus.INTERESTED,
)

job_2 = Job(
    company="example company 2",
    role="data engineer",
    location="Madrid/Remote",
    tags="Python, Snowflake, PySpark",
    status=ApplicationStatus.ACTIVE,
    applied_on=date(2026, 9, 12),
    stage="Recruiter interview",
)

job_3 = Job(
    company="example company 3",
    role="Python developer",
    location="Remote",
    tags="Python",
    status=ApplicationStatus.CLOSED,
    applied_on=date(2026, 9, 5),
    outcome="Withdrawn",
)

ALL_JOBS = [job_1, job_2, job_3]

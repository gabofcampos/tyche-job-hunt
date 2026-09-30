import sqlite3
from contextlib import closing
from datetime import date
from functools import partial
from pathlib import Path

import pytest
from assertpy import assert_that

from src.schema import ApplicationStatus, Job
from src.storage import initialize_database, insert_job, load_jobs


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "jobs.sqlite3"
    initialize_database(path)
    return path


@pytest.fixture
def saved_jobs(db_path: Path) -> list[Job]:
    jobs = [
        Job("Z Example", "Developer", "", "", ApplicationStatus.INTERESTED),
        Job(
            "Example O'Brien",
            "Engineer",
            "Remote",
            "Python, SQL",
            ApplicationStatus.ACTIVE,
            date(2026, 9, 12),
            "Technical interview",
        ),
        Job(
            "A Example",
            "Analyst",
            "Madrid",
            "SQL",
            ApplicationStatus.CLOSED,
            date(2026, 9, 1),
            outcome="Withdrawn",
        ),
        Job("No date", "Engineer", "", "", ApplicationStatus.ACTIVE),
    ]
    for job in jobs:
        insert_job(job, db_path)
    return jobs


class TestStorage:
    def test_empty_table(self, db_path: Path) -> None:
        jobs = load_jobs(db_path)

        assert_that(jobs).is_empty()

    def test_round_trip_preserves_fields_and_insertion_order(
        self, db_path: Path, saved_jobs: list[Job]
    ) -> None:
        jobs = load_jobs(db_path)

        assert_that(jobs).is_equal_to(saved_jobs)

    def test_repeated_loads_preserve_order(
        self, db_path: Path, saved_jobs: list[Job]
    ) -> None:
        first_load = load_jobs(db_path)

        second_load = load_jobs(db_path)

        assert_that(second_load).is_equal_to(first_load)

    def test_invalid_date_is_not_an_empty_board(self, db_path: Path) -> None:
        job = Job("Example", "Developer", "", "", ApplicationStatus.ACTIVE)
        insert_job(job, db_path)
        with closing(sqlite3.connect(db_path)) as connection:
            with connection:
                connection.execute(
                    "UPDATE jobs SET applied_on = ? WHERE id = ?",
                    ("invalid-date", job.id),
                )

        load_invalid_jobs = partial(load_jobs, db_path)

        assert_that(load_invalid_jobs).raises(ValueError).when_called_with()

    def test_corrupt_database_is_not_an_empty_board(self, db_path: Path) -> None:
        db_path.write_bytes(b"This is not a SQLite database")

        load_corrupt_database = partial(load_jobs, db_path)

        assert_that(load_corrupt_database).raises(
            sqlite3.DatabaseError
        ).when_called_with()

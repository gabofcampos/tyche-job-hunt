import sqlite3
from collections.abc import Iterator
from contextlib import closing
from datetime import date
from pathlib import Path

import pytest
from assertpy import assert_that

from src.schema import ApplicationStatus, Job
from src.storage import Storage


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "jobs.sqlite3"
    return path


@pytest.fixture
def storage(db_path: Path) -> Iterator[Storage]:
    with Storage(db_path) as instance:
        instance.initialize_database()
        yield instance


@pytest.fixture
def saved_jobs(storage: Storage) -> list[Job]:
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
        storage.insert_job(job)
    return jobs


class TestStorage:
    def test_empty_table(self, storage: Storage) -> None:
        jobs = storage.load_jobs()

        assert_that(jobs).is_empty()

    def test_round_trip_preserves_fields_and_insertion_order(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        jobs = storage.load_jobs()

        assert_that(jobs).is_equal_to(saved_jobs)

    def test_repeated_loads_preserve_order(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        first_load = storage.load_jobs()

        second_load = storage.load_jobs()

        assert_that(second_load).is_equal_to(first_load)

    def test_invalid_date_is_not_an_empty_board(
        self, db_path: Path, storage: Storage
    ) -> None:
        job = Job("Example", "Developer", "", "", ApplicationStatus.ACTIVE)
        storage.insert_job(job)
        with closing(sqlite3.connect(db_path)) as connection:
            with connection:
                connection.execute(
                    "UPDATE jobs SET applied_on = ? WHERE id = ?",
                    ("invalid-date", job.id),
                )

        load_invalid_jobs = storage.load_jobs

        assert_that(load_invalid_jobs).raises(ValueError).when_called_with()

    def test_corrupt_database_is_not_an_empty_board(self, db_path: Path) -> None:
        db_path.write_bytes(b"This is not a SQLite database")

        with Storage(db_path) as storage:
            load_corrupt_database = storage.load_jobs

            assert_that(load_corrupt_database).raises(
                sqlite3.DatabaseError
            ).when_called_with()

    def test_saved_jobs_survive_connection_reopening(
        self, db_path: Path, saved_jobs: list[Job]
    ) -> None:
        with Storage(db_path) as reopened:
            jobs = reopened.load_jobs()

        assert_that(jobs).is_equal_to(saved_jobs)

    def test_connection_closes_after_context_exit(self, db_path: Path) -> None:
        with Storage(db_path) as storage:
            storage.initialize_database()

        load_after_close = storage.load_jobs

        assert_that(load_after_close).raises(
            sqlite3.ProgrammingError
        ).when_called_with()

    def test_failed_insert_allows_subsequent_save(self, storage: Storage) -> None:
        original = Job("Example", "Developer", "", "", ApplicationStatus.INTERESTED)
        subsequent = Job("Another", "Developer", "", "", ApplicationStatus.ACTIVE)
        storage.insert_job(original)

        try:
            storage.insert_job(original)
        except sqlite3.IntegrityError:
            pass
        storage.insert_job(subsequent)
        jobs = storage.load_jobs()

        assert_that(jobs).is_equal_to([original, subsequent])

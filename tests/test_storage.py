import sqlite3
from collections.abc import Iterator
from contextlib import closing
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from assertpy import assert_that

from src.schema import ApplicationStatus, Job
from src.storage import JobNotFoundError, Storage


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

    def test_legacy_database_migration_preserves_job(self, tmp_path: Path) -> None:
        path = tmp_path / "legacy.sqlite3"
        with closing(sqlite3.connect(path)) as connection:
            with connection:
                connection.execute(
                    "CREATE TABLE jobs (id TEXT PRIMARY KEY, company TEXT, role TEXT, location TEXT, tags TEXT, status TEXT, applied_on TEXT, stage TEXT, outcome TEXT)"
                )
                connection.execute(
                    "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        "old-id",
                        "Example",
                        "Developer",
                        "",
                        "",
                        "Interested",
                        None,
                        None,
                        None,
                    ),
                )
        expected = Job(
            "Example", "Developer", "", "", ApplicationStatus.INTERESTED, id="old-id"
        )

        with Storage(path) as database:
            database.initialize_database()
            database.initialize_database()
            jobs = database.load_jobs()

        assert_that(jobs).is_equal_to([expected])

    def test_notes_migration_preserves_platform_and_is_repeatable(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "pre-notes.sqlite3"
        with closing(sqlite3.connect(path)) as connection:
            with connection:
                connection.execute(
                    "CREATE TABLE jobs (id TEXT PRIMARY KEY, company TEXT, role TEXT, location TEXT, tags TEXT, status TEXT, applied_on TEXT, stage TEXT, outcome TEXT, platform TEXT NOT NULL DEFAULT '')"
                )
                connection.execute(
                    "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        "old-id",
                        "Example",
                        "Developer",
                        "Remote",
                        "Python",
                        "Active",
                        "2026-09-12",
                        "Interview",
                        None,
                        "https://example.com/job",
                    ),
                )
        expected = Job(
            "Example",
            "Developer",
            "Remote",
            "Python",
            ApplicationStatus.ACTIVE,
            date(2026, 9, 12),
            "Interview",
            id="old-id",
            platform="https://example.com/job",
        )

        with Storage(path) as database:
            database.initialize_database()
            database.initialize_database()
            jobs = database.load_jobs()

        assert_that(jobs).is_equal_to([expected])


class TestUpdateJob:
    def test_update_changes_only_that_job_and_keeps_order(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        updated = replace(
            saved_jobs[1],
            company="Renamed",
            status=ApplicationStatus.CLOSED,
            stage=None,
            outcome="Rejected",
            platform="https://example.com/job",
            notes="Line one\nLine two",
        )

        storage.update_job(updated)
        jobs = storage.load_jobs()

        assert_that(jobs).is_equal_to(
            [saved_jobs[0], updated, saved_jobs[2], saved_jobs[3]]
        )

    def test_update_can_clear_application_details(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        updated = replace(
            saved_jobs[1],
            status=ApplicationStatus.INTERESTED,
            applied_on=None,
            stage=None,
        )

        storage.update_job(updated)
        jobs = storage.load_jobs()

        assert_that(jobs[1]).is_equal_to(updated)

    def test_update_survives_connection_reopening(
        self, db_path: Path, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        updated = replace(saved_jobs[0], notes="Follow up Monday")
        storage.update_job(updated)

        with Storage(db_path) as reopened:
            jobs = reopened.load_jobs()

        assert_that(jobs[0]).is_equal_to(updated)

    def test_missing_id_raises_job_not_found(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        missing = Job("Ghost", "Developer", "", "", ApplicationStatus.INTERESTED)

        update_missing = storage.update_job

        assert_that(update_missing).raises(JobNotFoundError).when_called_with(missing)

    def test_missing_id_does_not_insert(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        missing = Job("Ghost", "Developer", "", "", ApplicationStatus.INTERESTED)

        try:
            storage.update_job(missing)
        except JobNotFoundError:
            pass
        jobs = storage.load_jobs()

        assert_that(jobs).is_equal_to(saved_jobs)

    def test_failed_update_leaves_data_unchanged(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        invalid = replace(saved_jobs[1], company=None, notes="Should not save")

        try:
            storage.update_job(invalid)
        except sqlite3.IntegrityError:
            pass
        jobs = storage.load_jobs()

        assert_that(jobs).is_equal_to(saved_jobs)

    def test_failed_update_allows_subsequent_update(
        self, storage: Storage, saved_jobs: list[Job]
    ) -> None:
        invalid = replace(saved_jobs[1], company=None)
        valid = replace(saved_jobs[1], notes="Saved after retry")

        try:
            storage.update_job(invalid)
        except sqlite3.IntegrityError:
            pass
        storage.update_job(valid)
        jobs = storage.load_jobs()

        assert_that(jobs[1]).is_equal_to(valid)

    def test_deletion_persists_after_reopening(
        self, db_path: Path, saved_jobs: list[Job], storage: Storage
    ) -> None:
        target = saved_jobs[1]

        storage.delete_job(target.id)
        with Storage(db_path) as reopened:
            jobs = reopened.load_jobs()

        assert_that(jobs).is_equal_to(
            [job for job in saved_jobs if job.id != target.id]
        )

    def test_delete_missing_id_raises(self, storage: Storage) -> None:
        from src.storage import JobNotFoundError

        delete = storage.delete_job

        assert_that(delete).raises(JobNotFoundError).when_called_with("missing-id")

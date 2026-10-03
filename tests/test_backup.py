import sqlite3
from datetime import date
from pathlib import Path

import pytest
from assertpy import assert_that

from src.backup import backup_database, copy_database
from src.schema import ApplicationStatus, Job
from src.storage import Storage


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "data" / "jobs.sqlite3"
    with Storage(path) as storage:
        storage.initialize_database()
        for status in ApplicationStatus:
            storage.insert_job(
                Job(
                    company=f"Fictional {status.value}",
                    notes="First line\nSecond line",
                    role="Engineer",
                    location="Remote",
                    tags="Python, SQL",
                    status=status,
                    applied_on=(
                        date(2026, 9, 12)
                        if status != ApplicationStatus.INTERESTED
                        else None
                    ),
                    stage=(
                        "Technical interview"
                        if status == ApplicationStatus.ACTIVE
                        else None
                    ),
                    outcome="Withdrawn" if status == ApplicationStatus.CLOSED else None,
                )
            )
    return path


class TestBackup:
    def test_snapshot_restores_all_jobs(self, source: Path, tmp_path: Path) -> None:
        with Storage(source) as storage:
            expected = storage.load_jobs()
        snapshot = backup_database(source, tmp_path / "backups")
        with Storage(source) as storage:
            storage.insert_job(
                Job("Later job", "Developer", "", "", ApplicationStatus.INTERESTED)
            )

        restored = copy_database(snapshot, tmp_path / "restored" / "jobs.sqlite3")
        with Storage(restored) as storage:
            jobs = storage.load_jobs()

        assert_that(jobs).is_equal_to(expected)

    def test_existing_destination_is_preserved(
        self, source: Path, tmp_path: Path
    ) -> None:
        destination = tmp_path / "existing.sqlite3"
        destination.write_bytes(b"Keep this file")

        try:
            copy_database(source, destination)
        except FileExistsError:
            pass

        assert_that(destination.read_bytes()).is_equal_to(b"Keep this file")

    def test_missing_source_does_not_create_database(self, tmp_path: Path) -> None:
        source = tmp_path / "missing.sqlite3"
        destination = tmp_path / "backup.sqlite3"

        try:
            copy_database(source, destination)
        except sqlite3.OperationalError:
            pass

        assert_that((source.exists(), destination.exists())).is_equal_to((False, False))

    def test_corrupt_source_leaves_no_snapshot(self, tmp_path: Path) -> None:
        source = tmp_path / "broken.sqlite3"
        source.write_bytes(b"Not a database")
        destination = tmp_path / "backup.sqlite3"

        try:
            copy_database(source, destination)
        except sqlite3.DatabaseError:
            pass

        assert_that(destination.exists()).is_false()

    def test_snapshots_have_distinct_names(self, source: Path, tmp_path: Path) -> None:
        first = backup_database(source, tmp_path / "backups")

        second = backup_database(source, tmp_path / "backups")

        assert_that(second).is_not_equal_to(first)

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from types import TracebackType

from src.schema import ApplicationStatus, Job

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.sqlite3"


class Storage:
    """
    Own one SQLite connection;
    each operation manages its transaction.
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(db_path, autocommit=False)
        self._connection.row_factory = sqlite3.Row

    def __enter__(self) -> Storage:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def initialize_database(self) -> None:
        with self._connection:
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY NOT NULL,
                    company TEXT NOT NULL,
                    role TEXT NOT NULL,
                    location TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (
                        status IN ('Interested', 'Active', 'Closed')
                    ),
                    applied_on TEXT,
                    stage TEXT,
                    outcome TEXT,
                    platform TEXT NOT NULL DEFAULT ''
                )
            """)
            columns = {
                row["name"]
                for row in self._connection.execute("PRAGMA table_info(jobs)")
            }
            if "platform" not in columns:
                self._connection.execute(
                    "ALTER TABLE jobs ADD COLUMN platform TEXT NOT NULL DEFAULT ''"
                )

    def insert_job(self, job: Job) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO jobs (
                    id, company, role, location, tags, status,
                    applied_on, stage, outcome, platform
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.company,
                    job.role,
                    job.location,
                    job.tags,
                    job.status.value,
                    job.applied_on.isoformat() if job.applied_on is not None else None,
                    job.stage,
                    job.outcome,
                    job.platform,
                ),
            )

    def load_jobs(self) -> list[Job]:
        with self._connection:
            rows = self._connection.execute("""
                SELECT id, company, role, location, tags, status,
                       applied_on, stage, outcome, platform
                FROM jobs
                ORDER BY rowid ASC
                """).fetchall()

        return [
            Job(
                id=row["id"],
                company=row["company"],
                role=row["role"],
                location=row["location"],
                tags=row["tags"],
                status=ApplicationStatus(row["status"]),
                applied_on=(
                    date.fromisoformat(row["applied_on"])
                    if row["applied_on"] is not None
                    else None
                ),
                stage=row["stage"],
                outcome=row["outcome"],
                platform=row["platform"],
            )
            for row in rows
        ]

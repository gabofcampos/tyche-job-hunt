from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from src.schema import ApplicationStatus, Job

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.sqlite3"


def initialize_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(db_path, autocommit=False)) as connection:
        with connection:
            connection.execute("""
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
                    outcome TEXT
                )
            """)


def insert_job(job: Job, db_path: Path = DEFAULT_DB_PATH) -> None:
    with closing(sqlite3.connect(db_path, autocommit=False)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    id, company, role, location, tags, status,
                    applied_on, stage, outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )


def load_jobs(db_path: Path = DEFAULT_DB_PATH) -> list[Job]:
    with closing(sqlite3.connect(db_path, autocommit=False)) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            rows = connection.execute("""
                SELECT id, company, role, location, tags, status,
                       applied_on, stage, outcome
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
        )
        for row in rows
    ]

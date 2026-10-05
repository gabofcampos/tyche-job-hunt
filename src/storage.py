from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from types import TracebackType

from src.schema import ApplicationStatus, Company, CompanyInterestRate, Job, WorkSetup

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.sqlite3"


class JobNotFoundError(LookupError):
    """Raised when an update or deletion targets an ID that is not stored."""


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
                    platform TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT ''
                )
            """)
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY NOT NULL,
                    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
                    industry TEXT NOT NULL,
                    location TEXT NOT NULL,
                    work_setup TEXT,
                    interest TEXT NOT NULL CHECK (interest IN ('Very high', 'High', 'Somewhat')),
                    tags TEXT NOT NULL,
                    website_url TEXT NOT NULL,
                    careers_url TEXT NOT NULL,
                    contacted INTEGER NOT NULL CHECK (contacted IN (0, 1)),
                    why_interested TEXT NOT NULL,
                    contacted_on TEXT,
                    notes TEXT NOT NULL
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
            if "notes" not in columns:
                self._connection.execute(
                    "ALTER TABLE jobs ADD COLUMN notes TEXT NOT NULL DEFAULT ''"
                )

    def insert_company(self, company: Company) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO companies (
                    id, name, industry, location, work_setup, interest, tags,
                    website_url, careers_url, contacted, why_interested, contacted_on, notes
                ) VALUES (
                    :id, :name, :industry, :location, :work_setup, :interest, :tags,
                    :website_url, :careers_url, :contacted, :why_interested, :contacted_on, :notes
                )
                """,
                company_to_params(company),
            )

    def load_companies(self) -> list[Company]:
        with self._connection:
            rows = self._connection.execute(
                "SELECT * FROM companies ORDER BY rowid ASC"
            ).fetchall()
        return [row_to_company(row) for row in rows]

    def insert_job(self, job: Job) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO jobs (
                    id, company, role, location, tags, status,
                    applied_on, stage, outcome, platform, notes
                ) VALUES (
                    :id, :company, :role, :location, :tags, :status,
                    :applied_on, :stage, :outcome, :platform, :notes
                )
                """,
                job_to_params(job),
            )

    def update_job(self, job: Job) -> None:
        with self._connection:
            cursor = self._connection.execute(
                """
                UPDATE jobs SET
                    company = :company, role = :role, location = :location,
                    tags = :tags, status = :status, applied_on = :applied_on,
                    stage = :stage, outcome = :outcome, platform = :platform,
                    notes = :notes
                WHERE id = :id
                """,
                job_to_params(job),
            )
            if cursor.rowcount == 0:
                raise JobNotFoundError(job.id)

    def delete_job(self, job_id: str) -> None:
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM jobs WHERE id = ?", (job_id,)
            )
            if cursor.rowcount == 0:
                raise JobNotFoundError(job_id)

    def load_jobs(self) -> list[Job]:
        with self._connection:
            rows = self._connection.execute("""
                SELECT id, company, role, location, tags, status,
                       applied_on, stage, outcome, platform, notes
                FROM jobs
                ORDER BY rowid ASC
                """).fetchall()

        return [row_to_job(row) for row in rows]


def job_to_params(job: Job) -> dict[str, str | None]:
    """Map a Job to named SQL parameters; the inverse of row_to_job."""
    return {
        "id": job.id,
        "company": job.company,
        "role": job.role,
        "location": job.location,
        "tags": job.tags,
        "status": job.status.value,
        "applied_on": (
            job.applied_on.isoformat() if job.applied_on is not None else None
        ),
        "stage": job.stage,
        "outcome": job.outcome,
        "platform": job.platform,
        "notes": job.notes,
    }


def row_to_job(row: sqlite3.Row) -> Job:
    return Job(
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
        notes=row["notes"],
    )


def company_to_params(company: Company) -> dict[str, str | int | None]:
    return {
        "id": company.id,
        "name": company.name,
        "industry": company.industry,
        "location": company.location,
        "work_setup": (
            company.work_setup.value if company.work_setup is not None else None
        ),
        "interest": company.interest.value,
        "tags": company.tags,
        "website_url": company.website_url,
        "careers_url": company.careers_url,
        "contacted": int(company.contacted),
        "why_interested": company.why_interested,
        "contacted_on": (
            company.contacted_on.isoformat() if company.contacted_on else None
        ),
        "notes": company.notes,
    }


def row_to_company(row: sqlite3.Row) -> Company:
    return Company(
        id=row["id"],
        name=row["name"],
        industry=row["industry"],
        location=row["location"],
        work_setup=(
            WorkSetup(row["work_setup"]) if row["work_setup"] is not None else None
        ),
        interest=CompanyInterestRate(row["interest"]),
        tags=row["tags"],
        website_url=row["website_url"],
        careers_url=row["careers_url"],
        contacted=bool(row["contacted"]),
        why_interested=row["why_interested"],
        contacted_on=(
            date.fromisoformat(row["contacted_on"]) if row["contacted_on"] else None
        ),
        notes=row["notes"],
    )

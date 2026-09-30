import sqlite3
from contextlib import closing
from pathlib import Path

DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "jobs.sqlite3"
)

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
"""Create manual SQLite snapshots without overwriting existing files."""

import argparse
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from src.storage import DEFAULT_DB_PATH

DEFAULT_BACKUP_DIR = DEFAULT_DB_PATH.parent.parent / "backups"


def copy_database(source: Path, destination: Path) -> Path:
    """Copy a readable database to a new file using SQLite's backup API."""
    source = source.resolve()
    destination = destination.resolve()
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as reader:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.touch(exist_ok=False)
        try:
            with closing(sqlite3.connect(destination)) as writer:
                reader.backup(writer)
        except sqlite3.Error, OSError:
            destination.unlink(missing_ok=True)
            raise
    return destination


def backup_database(
    source: Path = DEFAULT_DB_PATH, backup_dir: Path = DEFAULT_BACKUP_DIR
) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return copy_database(source, backup_dir / f"jobs-{timestamp}.sqlite3")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    args = parser.parse_args()
    try:
        destination = backup_database(args.source, args.backup_dir)
    except (sqlite3.Error, OSError) as error:
        parser.exit(1, f"Backup failed: {error}\n")
    print(f"Backup created: {destination}")


if __name__ == "__main__":
    main()

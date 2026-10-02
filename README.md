# tyche-job-hunt

the purpose of this repo is to create a simple job tracker.

rules:
- it will be born and developed out of necessity
- it will iterate in the smallest simplest way posible
- it will be practical

## just cloned the repo...
### how do I install the dependencies?
install the repo dependencies by running
```bash
uv sync
```

### how do I initialize the database?

The app automatically creates `data/jobs.sqlite3` and its `jobs` table on
startup if they do not exist. No separate initialization command is needed.
Existing records are preserved.

Jobs and their selected statuses are saved to SQLite and loaded on each full
app rerun. Closing and reopening Streamlit preserves saved jobs as long as the
database file remains in place. Search, popup state, and unsaved drafts are
temporary. Jobs from older in-memory sessions are not automatically imported.

The database is local runtime data and is not included in a fresh clone.

### how do I run it?

Run from the repository root so Python can resolve the `src` package:

```bash
uv run python -m streamlit run src/app.py
```

### how do I run the tests?
The suite uses pytest and assertpy, installed with the development dependencies.
Run it from the repository root:

```bash
uv run python -m pytest -q
```

Storage and dashboard tests use temporary databases, so
they do not require database initialization or modify `data/jobs.sqlite3`.

To run only the storage tests:
```bash
uv run python -m pytest tests/test_storage.py -q
```


### how do I back up my jobs?

From the repository root:

```bash
uv run python -m src.backup
```

This uses SQLite's `Connection.backup()` to create a snapshot named
`backups/jobs-<UTC timestamp>.sqlite3`. Both connections are closed after copying.
The source is `data/jobs.sqlite3`; it must already exist. Existing destination
files are never overwritten. If copying fails, the command reports an error
and removes its incomplete destination.

`backups/` is outside the runtime `data/` directory and excluded from Git.
A backup on the same disk does not protect against disk loss. Copy snapshots
to another device or use a backed-up folder:

```bash
uv run python -m src.backup --backup-dir /path/to/independent-backups
```

The backup API supports an active database, but each snapshot contains only
saved data, not unsaved form entries. See the
[Python SQLite backup documentation](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).

### how do I restore a backup?

1. Stop all Streamlit processes using this database (Ctrl+C in their terminals).
2. Choose a snapshot. Keep the current database by moving the entire `data/`
   directory to a new, uniquely named directory such as
   `backups/data-before-restore-20261002T120000`. Moving the whole directory
   preserves any SQLite sidecar files too. Do not overwrite an earlier copy.
3. Run the following from the repository root, replacing the example snapshot
   filename with the one you chose:

```bash
uv run python - <<'PYTHON'
from pathlib import Path
from src.backup import copy_database
from src.storage import DEFAULT_DB_PATH, Storage

snapshot = Path("backups/jobs-REPLACE-WITH-TIMESTAMP.sqlite3")
copy_database(snapshot, DEFAULT_DB_PATH)
with Storage() as storage:
    jobs = storage.load_jobs()
print(f"Restored {len(jobs)} jobs")
PYTHON
```

The copy refuses to overwrite an existing destination. If restoration fails,
keep Streamlit stopped, preserve any failed restore separately, and move the
original directory back into place. Do not initialize an empty replacement as
recovery. Keep the original until you have checked the restored board.

4. Restart with `uv run python -m streamlit run src/app.py` and check the cards,
   status counts, and application details.

Backup tests restore into temporary paths and compare all Job fields and IDs.
They never overwrite the normal database. Run them with:

```bash
uv run python -m pytest tests/test_backup.py -q
```


### what does persistence cover?

Saved jobs retain their IDs, company, role, location, tags, selected status, and
relevant application details. The board derives columns and counts from those
records. Search text, popup visibility, and unsaved form entries are temporary.

App sessions on this machine share `data/jobs.sqlite3`. A full rerun reads the
latest committed jobs, but there is no live synchronization between browser
sessions and no authentication. Existing job editing, status changes, and deletion
are not implemented.

The database and default backup paths are relative to the project location,
not the shell working directory. Keeping the database file is necessary for
persistence; deployment to an ephemeral filesystem needs separate durable
storage. Creating the table at startup does not migrate an existing schema.

### what has been verified?

The automated checks cover storage round trips, validation, failed-save retry,
search, fresh sessions, and snapshot recovery. They use disposable databases
and never reset normal application data.

Run focused checks with:

```bash
uv run python -m pytest tests/test_dashboard.py -q
uv run python -m pytest tests/test_restart.py -q
uv run python -m pytest tests/test_backup.py -q
```

The restart test saves through the form in a headless Streamlit test process,
waits for it to exit, and loads the same database in a new process. It compares
all job fields and IDs, ordering, cards, and counts. Backup tests restore a
snapshot into a separate database and verify the saved records.

The manual browser/Streamlit server stop-start check was confirmed complete
by the user on 2026-10-02. Milestone 2 verification is complete.

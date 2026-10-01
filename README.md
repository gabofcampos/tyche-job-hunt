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
test suit uses pytest (installed in dev dependencies). to run the test suite once deps installed:

```bash
uv run python -m pytest -q
```

Tests use pytest and assertpy. 
Storage tests create temporary databases, so
they do not require database initialization or modify `data/jobs.sqlite3`.

To run only the storage tests:
```bash
uv run python -m pytest tests/test_storage.py -q
```

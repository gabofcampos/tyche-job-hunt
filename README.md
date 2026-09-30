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

The app does not initialize SQLite automatically yet. To create the local
database, run this from the repository root:

```bash
uv run python - <<'PYTHON'
from src.storage import Storage

with Storage() as storage:
    storage.initialize_database()
PYTHON
```

The `with` block closes the shared connection when finished. Each storage
method commits or rolls back its own transaction.

This will create a `data/jobs.sqlite3` and its empty `jobs` table. It is safe to run
again: existing records are preserved. The database is local runtime data and
is not included in a fresh clone.

Database initialization is not required to run the current dashboard. The app
still keeps jobs in Streamlit session state; creating the database does not yet
make those jobs persist across sessions. 

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

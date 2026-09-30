# tyche-job-hunt

the purpose of this repo is to create a simple job tracker.

rules:
- it will be born and developed out of necessity
- it will iterate in the smallest simplest way posible
- it will be practical

## just cloned the repo...
### how do I install it?
install the repo dependencies by running
```
uv sync
```

### how do I initialize the database?

The app does not initialize SQLite automatically yet. To create the local
database, run this from the repository root:

```bash
uv run python -c "from src.storage import initialize_database; initialize_database()"
```

This will create a `data/jobs.sqlite3` and its empty `jobs` table. It is safe to run
again: existing records are preserved. The database is local runtime data and
is not included in a fresh clone.

Database initialization is not required to run the current dashboard. The app
still keeps jobs in Streamlit session state; creating the database does not yet
make those jobs persist across sessions. 

### how do I run it?
```
uv run streamlit run src/app.py
```

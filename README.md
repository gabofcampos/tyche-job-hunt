# tyche-job-hunt

A simple local tracker for job applications and companies you would like to work for.

Read the [design and implementation decisions](docs/decisions.md) for the reasoning
behind the project's technical choices.

rules:

- it will be born and developed out of necessity
- it will iterate in the smallest simplest way posible
- it will be practical

## just cloned the repo...
### how do I install the dependencies?

Use Python 3.14 or newer and `uv`. Install the dependencies from the repository root:
```bash
uv sync
```

### how do I initialize the database?

The app automatically creates `data/jobs.sqlite3` and its `jobs` and `companies` tables on
startup if they do not exist. No separate initialization command is needed.
Existing records are preserved.

Jobs, their selected statuses, and companies are saved to SQLite and loaded on
each full app rerun. Closing and reopening Streamlit preserves saved data as long as the
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
With `make` installed, run the Makefile target from the repository root:

```bash
make test
```

Storage and dashboard tests use temporary databases, so
they do not require database initialization or modify `data/jobs.sqlite3`.

The Makefile runs the complete suite. To run only the storage tests, invoke
pytest directly:
```bash
uv run python -m pytest tests/test_storage.py -q
```

### how do I format and check the code?

Sort imports with isort and format Python files with Black:

```bash
make format
```

To format the code and then run the complete test suite:

```bash
make check
```

Both `make format` and `make check` can modify files in `src/` and `tests/`.
Installation, app startup, backups, and focused tests use the direct commands
below or above because they do not currently have Makefile targets.


### how do I back up my jobs and companies?

From the repository root:

```bash
uv run python -m src.backup
```

This uses SQLite's `Connection.backup()` to create a snapshot named
`backups/jobs-<UTC timestamp>.sqlite3`. Both connections are closed after copying.
The snapshot includes both jobs and companies. The source is
`data/jobs.sqlite3`; it must already exist. Existing destination
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
    storage.initialize_database()
    jobs = storage.load_jobs()
    companies = storage.load_companies()
print(f"Restored {len(jobs)} jobs and {len(companies)} companies")
PYTHON
```

The copy refuses to overwrite an existing destination. If restoration fails,
keep Streamlit stopped, preserve any failed restore separately, and move the
original directory back into place. Do not initialize an empty replacement as
recovery. Keep the original until you have checked the restored board.

4. Restart with `uv run python -m streamlit run src/app.py` and check the cards,
   status counts, application details, and the Companies tab.

Older snapshots made before company tracking contain no companies; initialization
creates an empty companies table while preserving restored jobs.

Backup tests restore into temporary paths and compare all Job fields and IDs.
They never overwrite the normal database. Run them with:

```bash
uv run python -m pytest tests/test_backup.py -q
```


### how do I view and edit a job?

- **Open details:** click **View details** on a card. A details panel opens to
  the right of the board, which narrows to make room. On narrow screens the
  columns stack and the panel appears after the Closed column, so scroll down
  to it. Choosing another card replaces the panel; **Close details** restores
  the full-width board. Searching does not close the panel, even if the job's
  card is filtered out.
- **Posting link:** the posting URL appears as **Open original posting** only if
  it is an `http://` or `https://` URL with a host. Anything else is shown as
  plain text with a hint, never as a clickable link.
- **Notes:** optional, multiline, and shown as plain text in the panel (Markdown
  is not interpreted). Cards do not show notes.
- **Edit:** click **Edit job** at the bottom of the panel. The form opens with
  the saved values. **Submit** updates that job in place: it keeps its ID and
  its position within its column, and moves to another column if you changed
  its status. **Cancel**, the dialog's X, or Escape discards the draft; the
  next Edit or Add always starts from fresh values.
- **Status rules on save** (create and edit): Interested clears the application
  date, stage, and outcome; Active keeps the date and stage and clears the
  outcome; Closed keeps the date and outcome and clears the stage. The form
  states this above the date field.
- **Validation:** company and role are required (surrounding spaces are
  trimmed). The posting URL may be empty; otherwise it must pass the same
  `http(s)` rule as the link. If saving fails, your draft stays in the form
  with an error and nothing is changed.

The panel is a native Streamlit column beside the board, not the overlay
drawer in `designs/job_tracker_detail_drawer.excalidraw`: it resizes the board
instead of covering it. Cards still show company above role and include the
posting URL as text, unlike the drawing's role-first cards.

### how do I manage companies?

The **Companies** tab tracks places you would like to work, independently of job
applications.

- **Add:** click **Add company**. The name is required. You can also record
  industry, location, work setup (Remote, Hybrid, or On-site), interest, tags,
  website and careers URLs, why you saved it, contact details, and notes.
  URLs must use HTTP or HTTPS. The contact date is saved only when **Contacted**
  is checked.
- **Find:** search company names, tags, or notes; narrow results with the column
  filters; and sort names A–Z or Z–A. **Clear filters** resets the search and
  column filters. The right-aligned **Previous** and **Next** controls show
  **Page X of Y**, with six companies per page.
- **Details:** click a company name to open its panel. Until you select one,
  the table uses the full width. Closing the panel restores that layout.
  Filtering does not close an already selected company's details.
- **Edit:** click **Edit company** in the details panel. The form starts with
  saved values; **Submit** updates the same record. **Cancel**, X, or Escape
  discards the draft. A failed save leaves your entries available for retry.
- **Delete:** click **Delete company** in the details panel to remove the saved
  company immediately and close the panel. There is no confirmation or undo.

Companies are not yet linked to job applications: the Jobs column shows **—**,
linked jobs are unavailable, and editing or deleting a company does not change
any job records.

Jobs can also be deleted immediately using **Delete job** in their details panel.

### what does persistence cover?

Saved jobs retain their IDs, company, role, location, tags, selected status,
relevant application details, posting URL, and optional multiline notes,
including after edits. Existing databases automatically gain the notes column
without replacing saved jobs. The board derives columns and counts from those
records. Companies retain all their form fields and IDs, including after edits.
Search text, the open details panel, form visibility, and unsaved
drafts are temporary and are not restored after a restart.

App sessions on this machine share `data/jobs.sqlite3`. A full rerun reads the
latest committed jobs and companies, but there is no live synchronization between browser
sessions and no authentication. Jobs can be edited from the detail panel,
including status changes; edits keep the job's ID and board position, and the last
successful save wins. Job and company deletions also persist across restarts.

The database and default backup paths are relative to the project location,
not the shell working directory. Keeping the database file is necessary for
persistence; deployment to an ephemeral filesystem needs separate durable
storage. Startup applies the supported additive changes (the posting URL and
notes columns on older job tables, and the companies table) without replacing
existing records. It is not a general migration system.

### what has been verified?

The automated checks cover storage round trips, validation, failed-save retry,
search, fresh sessions, and snapshot recovery. They use disposable databases
and never reset normal application data.

Run focused checks with:

```bash
uv run python -m pytest tests/test_dashboard.py -q
uv run python -m pytest tests/test_company_form.py tests/test_companies_dashboard.py -q
uv run python -m pytest tests/test_restart.py -q
uv run python -m pytest tests/test_backup.py -q
```

The restart test saves through the form in a headless Streamlit test process,
waits for it to exit, and loads the same database in a new process. It compares
all job fields and IDs, ordering, cards, and counts. Backup tests restore a
snapshot into a separate database and verify the saved records.

The manual browser/Streamlit server stop-start check was confirmed complete
by the user on 2026-10-02. Milestone 2 verification is complete.

Milestone 3 adds automated checks for selecting, closing, and switching details;
posting links; notes; prefilled edit forms; updates that keep ID, count, and
order; status rules; status changes under an active search; validation;
failed-save retry; missing jobs; and edits surviving a separate process and a
backup restore.

On 2026-10-03 a headless Chrome run, driven by Playwright against a disposable copy
of the app with fictional jobs, checked: the panel on the right at 1440 px; a
long company name wrapping inside the panel; the posting link target; Edit
prefill; Escape and X discarding a draft; Tab reaching **Edit job** and Enter
opening it; saving, refreshing the panel, and showing a success message; the invalid-URL
error keeping the draft; and at 390 px, the panel stacking below the columns
with no horizontal overflow. A human visual pass in a regular browser window
is still pending.

The first Companies version has automated coverage for creation, validation,
search and filters, selection under filtering, editing, cancellation, deletion,
failed-save retry, missing records, and persistence after reopening the database.
Work setup round trips cover each enum value and an unspecified value. Pagination
navigation, page boundaries, and filtering were also checked with Streamlit AppTest.

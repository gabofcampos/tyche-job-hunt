"""Run the dashboard in an isolated process against a supplied test database."""

import json
import sys
from dataclasses import asdict
from datetime import date
from functools import partial
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src import job_form, storage
from src.schema import ApplicationStatus
from src.storage import Storage


def main() -> None:
    mode, database, output = sys.argv[1:]
    db_path = Path(database)
    factory = partial(Storage, db_path)
    storage.Storage = factory
    job_form.Storage = factory
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[2] / "src/app.py")
    ).run()
    errors = [e.message for e in app.exception]
    if mode == "write":
        for status in ApplicationStatus:
            app.button(key=f"add_{status.name.lower()}").click().run()
            values = {
                "Company": f"Fictional {status.value}",
                "Role": "Data engineer",
                "Location (optional)": "Remote",
                "Tags (optional)": "Python, SQL",
            }
            for widget in app.text_input:
                if widget.label in values:
                    widget.set_value(values[widget.label])
            app.text_area[0].set_value("Fictional notes\nSecond line")
            app.date_input[0].set_value(date(2026, 9, 12))
            app.selectbox[1].select("Technical interview")
            app.selectbox[2].select("Withdrawn")
            next(b for b in app.button if b.label == "Submit").click().run()
            errors.extend(e.message for e in app.exception)
    with Storage(db_path) as instance:
        jobs = instance.load_jobs()
    snapshot = {
        "errors": errors,
        "jobs": [asdict(job) for job in jobs],
        "companies": [h.value for h in app.subheader],
        "details": [c.value for c in app.caption],
        "counts": [m.value for m in app.markdown if "-badge[" in m.value],
    }
    Path(output).write_text(
        json.dumps(
            snapshot,
            default=lambda value: (
                value.value
                if isinstance(value, ApplicationStatus)
                else value.isoformat()
            ),
        )
    )


if __name__ == "__main__":
    main()

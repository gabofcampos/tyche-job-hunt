from functools import partial
from pathlib import Path

import pytest
from assertpy import assert_that
from streamlit.testing.v1 import AppTest

from src import job_form, storage
from src.schema import ApplicationStatus
from src.storage import Storage


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "jobs.sqlite3"
    factory = partial(Storage, path)
    monkeypatch.setattr(storage, "Storage", factory)
    monkeypatch.setattr(job_form, "Storage", factory)
    return path


@pytest.fixture
def app(db_path: Path) -> AppTest:
    return AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "src/app.py")
    ).run()


def submit(app: AppTest, company: str, role: str) -> None:
    next(w for w in app.text_input if w.label == "Company").set_value(company)
    next(w for w in app.text_input if w.label == "Role").set_value(role)
    next(b for b in app.button if b.label == "Submit").click().run()


class TestDashboard:
    def test_startup_initializes_empty_database(
        self, app: AppTest, db_path: Path
    ) -> None:
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (
                list(app.exception),
                jobs,
                [m.value for m in app.markdown if "-badge[" in m.value],
            )
        ).is_equal_to(([], [], [":yellow-badge[0]", ":blue-badge[0]", ":red-badge[0]"]))

    @pytest.mark.parametrize("status", list(ApplicationStatus))
    def test_column_submission_saves_once_and_refreshes_board(
        self, app: AppTest, db_path: Path, status: ApplicationStatus
    ) -> None:
        app.button(key=f"add_{status.name.lower()}").click().run()
        default_status = app.selectbox[0].value

        submit(app, "Example", "Developer")
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (
                list(app.exception),
                default_status,
                [(j.company, j.role, j.status) for j in jobs],
                [h.value for h in app.subheader],
                [m.value for m in app.markdown if "-badge[" in m.value],
            )
        ).is_equal_to(
            (
                [],
                status,
                [("Example", "Developer", status)],
                ["Example"],
                [
                    f":{color}-badge[{int(s == status)}]"
                    for color, s in zip(["yellow", "blue", "red"], ApplicationStatus)
                ],
            )
        )

    def test_new_session_loads_saved_jobs(self, app: AppTest, db_path: Path) -> None:
        app.button(key="add_job").click().run()
        submit(app, "Example", "Developer")

        fresh = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "src/app.py")
        ).run()

        assert_that(
            (list(fresh.exception), [h.value for h in fresh.subheader])
        ).is_equal_to(([], ["Example"]))

    def test_search_and_clear_preserve_saved_job(
        self, app: AppTest, db_path: Path
    ) -> None:
        app.button(key="add_job").click().run()
        submit(app, "Example", "Developer")

        app.text_input[0].set_value("no-match").run()
        hidden_cards = [h.value for h in app.subheader]
        app.text_input[0].set_value("").run()
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (
                hidden_cards,
                [h.value for h in app.subheader],
                len(jobs),
                list(app.exception),
            )
        ).is_equal_to(([], ["Example"], 1, []))

    def test_invalid_submission_then_cancel_saves_nothing(
        self, app: AppTest, db_path: Path
    ) -> None:
        app.button(key="add_job").click().run()

        submit(app, "  ", "Developer")
        error = app.error[0].value
        app.button(key="cancel_job_form").click().run()
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (error, jobs, app.session_state.job_form_open, list(app.exception))
        ).is_equal_to(("Enter both a company and a role.", [], False, []))

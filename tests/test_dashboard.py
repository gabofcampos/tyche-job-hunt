import sqlite3
from datetime import date
from functools import partial
from pathlib import Path
from unittest.mock import Mock

import pytest
from assertpy import assert_that
from streamlit.testing.v1 import AppTest

from src import job_form, storage
from src.schema import ApplicationStatus, Job
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


def fill_text_fields(app: AppTest, values: dict[str, str]) -> None:
    for label, value in values.items():
        next(widget for widget in app.text_input if widget.label == label).set_value(
            value
        )


def fill_application_details(app: AppTest, applied_on: date, stage: str) -> None:
    next(
        widget
        for widget in app.date_input
        if widget.label == "Application date (optional)"
    ).set_value(applied_on)
    next(
        widget for widget in app.selectbox if widget.label == "Stage (Active jobs)"
    ).select(stage)


def click_submit(app: AppTest) -> None:
    next(button for button in app.button if button.label == "Submit").click().run()


def submit(app: AppTest, company: str, role: str) -> None:
    fill_text_fields(app, {"Company": company, "Role": role})
    click_submit(app)


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

    @pytest.mark.parametrize("error", [sqlite3.OperationalError, OSError])
    def test_failed_save_preserves_draft(
        self, app: AppTest, monkeypatch: pytest.MonkeyPatch, error: type[Exception]
    ) -> None:
        app.button(key="add_active").click().run()
        fill_text_fields(
            app, {"Location (optional)": "Remote", "Tags (optional)": "Python, SQL"}
        )
        fill_application_details(app, date(2026, 9, 12), "Technical interview")
        monkeypatch.setattr(
            Storage, "insert_job", Mock(side_effect=error("Simulated failure"))
        )

        submit(app, "Example", "Developer")

        assert_that(
            (
                list(app.exception),
                app.session_state.job_form_open,
                [w.value for w in app.text_input if w.label != "Search jobs"],
                [w.value for w in app.selectbox],
                app.date_input[0].value,
            )
        ).is_equal_to(
            (
                [],
                True,
                ["Example", "Developer", "", "Remote", "Python, SQL"],
                [ApplicationStatus.ACTIVE, "Technical interview", None],
                date(2026, 9, 12),
            )
        )

    def test_failed_save_shows_error_without_success(
        self, app: AppTest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app.button(key="add_job").click().run()
        monkeypatch.setattr(
            Storage,
            "insert_job",
            Mock(side_effect=sqlite3.OperationalError("Simulated failure")),
        )

        submit(app, "Example", "Developer")

        assert_that(([e.value for e in app.error], list(app.success))).is_equal_to(
            (
                [
                    "Could not save this job. Your entries are still in the form. "
                    "Check that the data folder is writable and the database "
                    "is not locked, then click Submit again."
                ],
                [],
            )
        )

    def test_failed_save_adds_no_row(
        self, app: AppTest, db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app.button(key="add_job").click().run()
        monkeypatch.setattr(
            Storage,
            "insert_job",
            Mock(side_effect=sqlite3.OperationalError("Simulated failure")),
        )

        submit(app, "Example", "Developer")
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(jobs).is_empty()

    def test_retry_after_failed_save_saves_exactly_once(
        self, app: AppTest, db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        app.button(key="add_job").click().run()
        with monkeypatch.context() as patch:
            patch.setattr(
                Storage,
                "insert_job",
                Mock(side_effect=sqlite3.OperationalError("Simulated failure")),
            )
            submit(app, "Example", "Developer")

        click_submit(app)
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (
                list(app.exception),
                [(j.company, j.role) for j in jobs],
                app.session_state.job_form_open,
            )
        ).is_equal_to(([], [("Example", "Developer")], False))

    @pytest.mark.parametrize("method", ["initialize_database", "load_jobs"])
    @pytest.mark.parametrize("error", [sqlite3.OperationalError, OSError])
    def test_storage_failure_stops_board(
        self,
        app: AppTest,
        monkeypatch: pytest.MonkeyPatch,
        method: str,
        error: type[Exception],
    ) -> None:
        monkeypatch.setattr(
            Storage, method, Mock(side_effect=error("Simulated failure"))
        )

        app.run()

        assert_that(
            (
                list(app.exception),
                [e.value for e in app.error],
                list(app.header),
                [m.value for m in app.markdown if "-badge[" in m.value],
            )
        ).is_equal_to(
            (
                [],
                [
                    "Could not open or read the jobs database. "
                    "Check that the data folder is accessible and writable, "
                    "then reload the app."
                ],
                [],
                [],
            )
        )

    def test_invalid_stored_value_stops_board(
        self, app: AppTest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            Storage, "load_jobs", Mock(side_effect=ValueError("Invalid date"))
        )

        app.run()

        assert_that(
            (list(app.exception), [e.value for e in app.error], list(app.header))
        ).is_equal_to(
            (
                [],
                [
                    "The jobs database contains an invalid date or status. "
                    "Check the stored data or restore a known-good backup."
                ],
                [],
            )
        )

    @pytest.mark.parametrize("query", ["eXaMpLe", " DEVELOPER "])
    def test_search_is_case_insensitive(self, app: AppTest, query: str) -> None:
        app.button(key="add_job").click().run()
        submit(app, "Example", "Developer")

        app.text_input[0].set_value(query).run()

        assert_that([h.value for h in app.subheader]).is_equal_to(["Example"])

    @pytest.mark.parametrize(
        "company,role",
        [("", "Developer"), ("Example", ""), (" ", "Developer"), ("Example", " ")],
    )
    def test_required_fields_reject_empty_or_whitespace(
        self, app: AppTest, db_path: Path, company: str, role: str
    ) -> None:
        app.button(key="add_job").click().run()

        submit(app, company, role)
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that((jobs, [e.value for e in app.error])).is_equal_to(
            ([], ["Enter both a company and a role."])
        )

    def test_header_opens_fresh_form_after_save(self, app: AppTest) -> None:
        app.button(key="add_active").click().run()
        fill_application_details(app, date(2026, 9, 12), "Technical interview")
        submit(app, "Example", "Developer")

        app.button(key="add_job").click().run()

        assert_that(
            (
                [w.value for w in app.text_input if w.label != "Search jobs"],
                [w.value for w in app.selectbox],
                app.date_input[0].value,
            )
        ).is_equal_to(
            (["", "", "", "", ""], [ApplicationStatus.INTERESTED, None, None], None)
        )

    def test_platform_survives_new_session(self, app: AppTest, db_path: Path) -> None:
        app.button(key="add_job").click().run()
        fill_text_fields(
            app, {"Job search platform (URL)": " https://example.com/jobs "}
        )
        submit(app, "Example", "Developer")

        fresh = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "src/app.py")
        ).run()
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (jobs[0].platform, [t.value for t in fresh.text], list(fresh.exception))
        ).is_equal_to(
            (
                "https://example.com/jobs",
                ["Developer", "Job search platform: https://example.com/jobs"],
                [],
            )
        )

    def test_duplicate_cards_select_and_switch_by_id(
        self, app: AppTest, db_path: Path
    ) -> None:
        first = Job("Example", "Developer", "", "", ApplicationStatus.INTERESTED)
        second = Job("Example", "Developer", "", "", ApplicationStatus.INTERESTED)
        with Storage(db_path) as database:
            database.insert_job(first)
            database.insert_job(second)
        app.run()

        app.button(key=f"job_{first.id}").click().run()
        first_selection = app.session_state.selected_job_id
        app.button(key=f"job_{second.id}").click().run()

        assert_that(
            (first_selection, app.session_state.selected_job_id, list(app.exception))
        ).is_equal_to((first.id, second.id, []))

    def test_search_hides_card_but_keeps_details(
        self, app: AppTest, db_path: Path
    ) -> None:
        job = Job("Example", "Developer", "", "", ApplicationStatus.ACTIVE)
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()
        app.button(key=f"job_{job.id}").click().run()

        app.text_input[0].set_value("no-match").run()

        assert_that(
            (
                app.session_state.selected_job_id,
                [h.value for h in app.subheader],
                [t.value for t in app.text],
                list(app.exception),
            )
        ).is_equal_to(
            (
                job.id,
                ["Example"],
                [
                    "Developer",
                    "No application date provided.",
                    "No stage provided.",
                    "No location provided.",
                    "No tags provided.",
                ],
                [],
            )
        )

    def test_close_clears_selection(self, app: AppTest, db_path: Path) -> None:
        job = Job("Example", "Developer", "", "", ApplicationStatus.ACTIVE)
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()
        app.button(key=f"job_{job.id}").click().run()

        app.button(key="close_job_details").click().run()

        assert_that(
            (
                app.session_state.selected_job_id,
                [b.label for b in app.button if b.key == "close_job_details"],
                list(app.exception),
            )
        ).is_equal_to((None, [], []))

    def test_missing_selection_is_cleared_with_message(self, app: AppTest) -> None:
        app.session_state.selected_job_id = "missing-job"

        app.run()

        assert_that(
            (
                app.session_state.selected_job_id,
                [i.value for i in app.info],
                list(app.exception),
            )
        ).is_equal_to(
            (
                None,
                [
                    "This job is no longer available. Select another job to view its details."
                ],
                [],
            )
        )

    @pytest.mark.parametrize(
        "status,expected",
        [
            (ApplicationStatus.INTERESTED, ["Developer", "Remote"]),
            (
                ApplicationStatus.ACTIVE,
                ["Developer", "Applied 12 Sep 2026", "Technical interview", "Remote"],
            ),
            (
                ApplicationStatus.CLOSED,
                ["Developer", "Applied 12 Sep 2026", "Withdrawn", "Remote"],
            ),
        ],
    )
    def test_detail_panel_displays_relevant_fields(
        self,
        app: AppTest,
        db_path: Path,
        status: ApplicationStatus,
        expected: list[str],
    ) -> None:
        job = Job(
            "Example",
            "Developer",
            "Remote",
            "Python, SQL",
            status,
            date(2026, 9, 12),
            "Technical interview",
            "Withdrawn",
        )
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()

        app.button(key=f"job_{job.id}").click().run()
        panel = app.get_by_key("job_details")

        assert_that(
            (
                list(app.exception),
                [t.value for t in panel.text],
                [m.value for m in panel.markdown],
            )
        ).is_equal_to(
            (
                [],
                expected,
                [
                    f":{ {ApplicationStatus.INTERESTED: 'yellow', ApplicationStatus.ACTIVE: 'blue', ApplicationStatus.CLOSED: 'red'}[status]}-badge[{status.value}]",
                    ":gray-badge[Python]",
                    ":gray-badge[SQL]",
                ],
            )
        )

    @pytest.mark.parametrize(
        "status,expected",
        [
            (
                ApplicationStatus.INTERESTED,
                ["Developer", "No location provided.", "No tags provided."],
            ),
            (
                ApplicationStatus.ACTIVE,
                [
                    "Developer",
                    "No application date provided.",
                    "No stage provided.",
                    "No location provided.",
                    "No tags provided.",
                ],
            ),
            (
                ApplicationStatus.CLOSED,
                [
                    "Developer",
                    "No application date provided.",
                    "No outcome provided.",
                    "No location provided.",
                    "No tags provided.",
                ],
            ),
        ],
    )
    def test_detail_panel_handles_missing_fields(
        self,
        app: AppTest,
        db_path: Path,
        status: ApplicationStatus,
        expected: list[str],
    ) -> None:
        job = Job("Example", "Developer", "", " , ", status)
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()

        app.button(key=f"job_{job.id}").click().run()

        assert_that([t.value for t in app.get_by_key("job_details").text]).is_equal_to(
            expected
        )

    def test_close_restores_board_layout(self, app: AppTest, db_path: Path) -> None:
        job = Job("Example", "Developer", "", "", ApplicationStatus.INTERESTED)
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()
        original_columns = len(app.columns)
        app.button(key=f"job_{job.id}").click().run()
        expanded_columns = len(app.columns)

        app.button(key="close_job_details").click().run()

        assert_that(
            (
                expanded_columns - original_columns,
                len(app.columns),
                app.session_state.selected_job_id,
                list(app.exception),
            )
        ).is_equal_to((2, original_columns, None, []))

import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date
from functools import partial
from pathlib import Path
from unittest.mock import Mock

import pytest
from assertpy import assert_that
from streamlit.testing.v1 import AppTest

from src import job_form, messages, storage
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
        ).is_equal_to((messages.REQUIRED_FIELDS, [], False, []))

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
                [
                    w.value
                    for w in app.text_input
                    if w.key and w.key.startswith("job_draft_")
                ],
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
                [messages.SAVE_FAILED],
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
                [messages.DATABASE_UNREADABLE],
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
                [messages.DATABASE_INVALID],
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
            ([], [messages.REQUIRED_FIELDS])
        )

    def test_header_opens_fresh_form_after_save(self, app: AppTest) -> None:
        app.button(key="add_active").click().run()
        fill_application_details(app, date(2026, 9, 12), "Technical interview")
        submit(app, "Example", "Developer")

        app.button(key="add_job").click().run()

        assert_that(
            (
                [
                    w.value
                    for w in app.text_input
                    if w.key and w.key.startswith("job_draft_")
                ],
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
                [messages.SELECTED_JOB_UNAVAILABLE],
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
        ).is_equal_to((4, original_columns, None, []))

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/jobs/1",
            "http://example.com/job?q=python",
            "  https://example.com/jobs  ",
        ],
    )
    def test_posting_link_uses_trimmed_url(
        self, app: AppTest, db_path: Path, url: str
    ) -> None:
        job = Job(
            "Example", "Developer", "", "", ApplicationStatus.INTERESTED, platform=url
        )
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()

        app.button(key=f"job_{job.id}").click().run()
        links = app.get_by_key("job_details").get("link_button")
        with Storage(db_path) as database:
            stored_url = database.load_jobs()[0].platform

        assert_that(
            (
                [(link.proto.label, link.proto.url) for link in links],
                stored_url,
                list(app.exception),
            )
        ).is_equal_to(([("Open original posting", url.strip())], url, []))

    @pytest.mark.parametrize("url", ["", "   "])
    def test_missing_posting_url_has_no_link(
        self, app: AppTest, db_path: Path, url: str
    ) -> None:
        job = Job(
            "Example", "Developer", "", "", ApplicationStatus.INTERESTED, platform=url
        )
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()

        app.button(key=f"job_{job.id}").click().run()
        panel = app.get_by_key("job_details")

        assert_that(
            (
                list(panel.get("link_button")),
                next(
                    c.value
                    for c in panel.caption
                    if c.value.startswith(("No posting", "This posting"))
                ),
            )
        ).is_equal_to(([], "No posting link."))

    @pytest.mark.parametrize(
        "url",
        [
            "javascript:alert(1)",
            "ftp://example.com/job",
            "example.com",
            "https:///jobs",
            "https://[broken",
            "https://example.com:bad",
            "https://example .com",
            "https://example.com/\njob",
            "https://example.com\\job",
        ],
    )
    def test_invalid_posting_url_is_plain_text(
        self, app: AppTest, db_path: Path, url: str
    ) -> None:
        job = Job(
            "Example", "Developer", "", "", ApplicationStatus.INTERESTED, platform=url
        )
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()

        app.button(key=f"job_{job.id}").click().run()
        panel = app.get_by_key("job_details")
        with Storage(db_path) as database:
            stored_url = database.load_jobs()[0].platform

        assert_that(
            (
                list(panel.get("link_button")),
                panel.text[-1].value,
                next(
                    c.value
                    for c in panel.caption
                    if c.value.startswith(("No posting", "This posting"))
                ),
                stored_url,
                list(app.exception),
            )
        ).is_equal_to(
            (
                [],
                url,
                messages.INVALID_POSTING_LINK,
                url,
                [],
            )
        )

    @pytest.mark.parametrize(
        "notes", ["First line\nSecond line with **literal** text", ""]
    )
    def test_notes_survive_new_session_and_display(
        self, app: AppTest, db_path: Path, notes: str
    ) -> None:
        app.button(key="add_job").click().run()
        app.text_area[0].set_value(notes)
        submit(app, "Example", "Developer")
        with Storage(db_path) as database:
            saved = database.load_jobs()[0]

        fresh = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "src/app.py")
        ).run()
        fresh.button(key=f"job_{saved.id}").click().run()
        panel = fresh.get_by_key("job_details")
        displayed = panel.text[-1].value if notes else panel.caption[-1].value

        assert_that((saved.notes, displayed, list(fresh.exception))).is_equal_to(
            (notes, notes or "No notes provided.", [])
        )


def seed(db_path: Path, *jobs: Job) -> None:
    with Storage(db_path) as database:
        for job in jobs:
            database.insert_job(job)


def load(db_path: Path) -> list[Job]:
    with Storage(db_path) as database:
        return database.load_jobs()


def open_edit(app: AppTest, job: Job) -> None:
    app.run()
    app.button(key=f"job_{job.id}").click().run()
    app.button(key="edit_job").click().run()


def draft(app: AppTest) -> list[object]:
    return [
        app.text_input(key="job_draft_company").value,
        app.text_input(key="job_draft_role").value,
        app.text_input(key="job_draft_platform").value,
        app.text_input(key="job_draft_location").value,
        app.text_input(key="job_draft_tags").value,
        app.selectbox(key="job_draft_status").value,
        app.date_input(key="job_draft_applied_on").value,
        app.selectbox(key="job_draft_stage").value,
        app.selectbox(key="job_draft_outcome").value,
        app.text_area(key="job_draft_notes").value,
    ]


ACTIVE_JOB = Job(
    "Example",
    "Developer",
    "Remote",
    "Python, SQL",
    ApplicationStatus.ACTIVE,
    date(2026, 9, 12),
    "Technical interview",
    platform="https://example.com/jobs/1",
    notes="First line\nSecond line",
)
OTHER_JOB = Job(
    "Other",
    "Analyst",
    "Madrid",
    "SQL",
    ApplicationStatus.CLOSED,
    date(2026, 9, 1),
    outcome="Withdrawn",
)


class TestEditForm:
    def test_edit_prefills_selected_job(self, app: AppTest, db_path: Path) -> None:
        seed(db_path, ACTIVE_JOB, OTHER_JOB)

        open_edit(app, ACTIVE_JOB)

        assert_that((draft(app), list(app.exception))).is_equal_to(
            (
                [
                    "Example",
                    "Developer",
                    "https://example.com/jobs/1",
                    "Remote",
                    "Python, SQL",
                    ApplicationStatus.ACTIVE,
                    date(2026, 9, 12),
                    "Technical interview",
                    None,
                    "First line\nSecond line",
                ],
                [],
            )
        )

    def test_switching_jobs_prefills_new_job(self, app: AppTest, db_path: Path) -> None:
        seed(db_path, ACTIVE_JOB, OTHER_JOB)
        open_edit(app, ACTIVE_JOB)
        app.button(key="cancel_job_form").click().run()

        app.button(key=f"job_{OTHER_JOB.id}").click().run()
        app.button(key="edit_job").click().run()

        assert_that(draft(app)).is_equal_to(
            [
                "Other",
                "Analyst",
                "",
                "Madrid",
                "SQL",
                ApplicationStatus.CLOSED,
                date(2026, 9, 1),
                None,
                "Withdrawn",
                "",
            ]
        )

    def test_reopening_edit_discards_unsaved_draft(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        app.text_input(key="job_draft_company").set_value("Unsaved")
        app.button(key="cancel_job_form").click().run()

        app.button(key="edit_job").click().run()

        assert_that(app.text_input(key="job_draft_company").value).is_equal_to(
            "Example"
        )

    def test_add_after_edit_opens_blank_form(self, app: AppTest, db_path: Path) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        app.button(key="cancel_job_form").click().run()

        app.button(key="add_closed").click().run()

        assert_that(draft(app)).is_equal_to(
            ["", "", "", "", "", ApplicationStatus.CLOSED, None, None, None, ""]
        )

    def test_cancel_changes_nothing_and_keeps_details(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        app.text_input(key="job_draft_company").set_value("Unsaved")

        app.button(key="cancel_job_form").click().run()

        assert_that(
            (
                load(db_path),
                app.session_state.selected_job_id,
                app.session_state.job_form_open,
                [h.value for h in app.get_by_key("job_details").subheader],
                list(app.exception),
            )
        ).is_equal_to(([ACTIVE_JOB], ACTIVE_JOB.id, False, ["Example"], []))

    def test_edit_of_vanished_job_does_not_open_form(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        app.run()
        app.button(key=f"job_{ACTIVE_JOB.id}").click().run()
        with closing(sqlite3.connect(db_path)) as connection:
            with connection:
                connection.execute("DELETE FROM jobs")

        app.button(key="edit_job").click().run()

        assert_that(
            (
                app.session_state.job_form_open,
                messages.EDIT_JOB_UNAVAILABLE in [i.value for i in app.info],
                list(app.exception),
            )
        ).is_equal_to((False, True, []))

    def test_unlisted_saved_stage_is_kept(self, app: AppTest, db_path: Path) -> None:
        job = Job(
            "Example", "Developer", "", "", ApplicationStatus.ACTIVE, stage="Interview"
        )
        seed(db_path, job)
        open_edit(app, job)

        click_submit(app)

        assert_that(load(db_path)).is_equal_to([job])


class TestSaveEdits:
    def test_edit_updates_one_row_and_keeps_identity(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB, OTHER_JOB)
        open_edit(app, ACTIVE_JOB)
        fill_text_fields(app, {"Company": "  Renamed  ", "Location (optional)": ""})
        app.text_area(key="job_draft_notes").set_value("Updated note")

        click_submit(app)

        assert_that(load(db_path)).is_equal_to(
            [
                replace(
                    ACTIVE_JOB, company="Renamed", location="", notes="Updated note"
                ),
                OTHER_JOB,
            ]
        )

    def test_edit_refreshes_details_and_keeps_selection(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        fill_text_fields(app, {"Company": "Renamed"})

        click_submit(app)

        assert_that(
            (
                app.session_state.selected_job_id,
                app.session_state.job_form_open,
                [h.value for h in app.get_by_key("job_details").subheader],
                [s.value for s in app.success],
                list(app.exception),
            )
        ).is_equal_to(
            (
                ACTIVE_JOB.id,
                False,
                ["Renamed"],
                [messages.job_updated(ApplicationStatus.ACTIVE)],
                [],
            )
        )

    def test_status_change_moves_card_and_counts(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        app.selectbox(key="job_draft_status").set_value(ApplicationStatus.CLOSED)
        app.selectbox(key="job_draft_outcome").select("Rejected")

        click_submit(app)

        assert_that(
            [m.value for m in app.markdown if "-badge[" in m.value][:4]
        ).is_equal_to(
            [
                ":yellow-badge[0]",
                ":blue-badge[0]",
                ":red-badge[1]",
                ":red-badge[Closed]",
            ]
        )

    @pytest.mark.parametrize(
        "status,expected",
        [
            (ApplicationStatus.INTERESTED, (None, None, None)),
            (ApplicationStatus.ACTIVE, (date(2026, 9, 12), "Offer", None)),
            (ApplicationStatus.CLOSED, (date(2026, 9, 12), None, "Rejected")),
        ],
    )
    def test_status_rules_clear_irrelevant_details(
        self,
        app: AppTest,
        db_path: Path,
        status: ApplicationStatus,
        expected: tuple[object, ...],
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        app.selectbox(key="job_draft_status").set_value(status)
        app.selectbox(key="job_draft_stage").select("Offer")
        app.selectbox(key="job_draft_outcome").select("Rejected")

        click_submit(app)
        saved = load(db_path)[0]

        assert_that((saved.applied_on, saved.stage, saved.outcome)).is_equal_to(
            expected
        )

    def test_edited_job_outside_search_stays_in_details(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        app.run()
        app.text_input[0].set_value("example").run()
        app.button(key=f"job_{ACTIVE_JOB.id}").click().run()
        app.button(key="edit_job").click().run()
        fill_text_fields(app, {"Company": "Renamed", "Role": "Manager"})

        click_submit(app)

        assert_that(
            (
                [h.value for h in app.get_by_key("job_details").subheader],
                [b.key for b in app.button if b.key == f"job_{ACTIVE_JOB.id}"],
            )
        ).is_equal_to((["Renamed"], []))

    @pytest.mark.parametrize("company,role", [(" ", "Developer"), ("Example", "")])
    def test_edit_requires_company_and_role(
        self, app: AppTest, db_path: Path, company: str, role: str
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)

        submit(app, company, role)

        assert_that(
            (
                load(db_path),
                [e.value for e in app.error],
                app.session_state.job_form_open,
            )
        ).is_equal_to(([ACTIVE_JOB], [messages.REQUIRED_FIELDS], True))

    @pytest.mark.parametrize(
        "url",
        ["example.com", "javascript:alert(1)", "https:///jobs", "https://a b.com"],
    )
    def test_edit_rejects_invalid_url_and_keeps_draft(
        self, app: AppTest, db_path: Path, url: str
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        fill_text_fields(app, {"Job search platform (URL)": url})

        click_submit(app)

        assert_that(
            (
                load(db_path),
                [e.value for e in app.error],
                app.text_input(key="job_draft_platform").value,
                list(app.success),
            )
        ).is_equal_to(
            (
                [ACTIVE_JOB],
                [messages.INVALID_POSTING_URL],
                url,
                [],
            )
        )

    def test_create_rejects_invalid_url(self, app: AppTest, db_path: Path) -> None:
        app.button(key="add_job").click().run()
        fill_text_fields(app, {"Job search platform (URL)": "example.com"})

        submit(app, "Example", "Developer")

        assert_that(load(db_path)).is_empty()

    def test_edit_can_clear_malformed_url(self, app: AppTest, db_path: Path) -> None:
        job = replace(ACTIVE_JOB, platform="example.com")
        seed(db_path, job)
        open_edit(app, job)
        fill_text_fields(app, {"Job search platform (URL)": "  "})

        click_submit(app)

        assert_that(load(db_path)[0].platform).is_equal_to("")

    @pytest.mark.parametrize("error", [sqlite3.OperationalError, OSError])
    def test_failed_update_keeps_draft_and_data(
        self,
        app: AppTest,
        db_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        error: type[Exception],
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        fill_text_fields(app, {"Company": "Renamed"})
        monkeypatch.setattr(
            Storage, "update_job", Mock(side_effect=error("Simulated failure"))
        )

        click_submit(app)

        assert_that(
            (
                load(db_path),
                app.text_input(key="job_draft_company").value,
                app.session_state.job_form_open,
                len(app.error),
                list(app.success),
            )
        ).is_equal_to(([ACTIVE_JOB], "Renamed", True, 1, []))

    def test_missing_job_on_save_shows_error(self, app: AppTest, db_path: Path) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        with closing(sqlite3.connect(db_path)) as connection:
            with connection:
                connection.execute("DELETE FROM jobs")

        click_submit(app)

        assert_that(
            (load(db_path), [e.value for e in app.error], list(app.success))
        ).is_equal_to(
            (
                [],
                [messages.JOB_NOT_FOUND_ON_SAVE],
                [],
            )
        )

    def test_create_still_inserts_new_row(self, app: AppTest, db_path: Path) -> None:
        seed(db_path, ACTIVE_JOB)
        app.run()
        app.button(key="add_job").click().run()

        submit(app, "New", "Engineer")

        assert_that(
            [(j.company, j.id == ACTIVE_JOB.id) for j in load(db_path)]
        ).is_equal_to([("Example", True), ("New", False)])

    def test_status_change_under_search_moves_card(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB, OTHER_JOB)
        app.run()
        app.text_input[0].set_value("example").run()
        app.button(key=f"job_{ACTIVE_JOB.id}").click().run()
        app.button(key="edit_job").click().run()
        app.selectbox(key="job_draft_status").set_value(ApplicationStatus.INTERESTED)

        click_submit(app)

        assert_that(
            (
                app.text_input[0].value,
                [m.value for m in app.markdown if "-badge[" in m.value][:3],
                [h.value for h in app.subheader],
                list(app.exception),
            )
        ).is_equal_to(
            (
                "example",
                [":yellow-badge[1]", ":blue-badge[0]", ":red-badge[0]"],
                ["Example", "Example"],
                [],
            )
        )

    def test_retry_after_failed_update_saves_once(
        self, app: AppTest, db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seed(db_path, ACTIVE_JOB, OTHER_JOB)
        open_edit(app, ACTIVE_JOB)
        fill_text_fields(app, {"Company": "Renamed"})
        with monkeypatch.context() as patch:
            patch.setattr(
                Storage,
                "update_job",
                Mock(side_effect=sqlite3.OperationalError("Simulated failure")),
            )
            click_submit(app)

        click_submit(app)

        assert_that(
            (
                load(db_path),
                app.session_state.job_form_open,
                [s.value for s in app.success],
            )
        ).is_equal_to(
            (
                [replace(ACTIVE_JOB, company="Renamed"), OTHER_JOB],
                False,
                [messages.job_updated(ApplicationStatus.ACTIVE)],
            )
        )

    def test_dismissed_form_state_saves_nothing(
        self, app: AppTest, db_path: Path
    ) -> None:
        seed(db_path, ACTIVE_JOB)
        open_edit(app, ACTIVE_JOB)
        app.text_input(key="job_draft_company").set_value("Unsaved")

        app.session_state.job_form_open = False
        app.run()

        assert_that(
            (
                load(db_path),
                app.session_state.selected_job_id,
                [w.key for w in app.text_input if w.key == "job_draft_company"],
            )
        ).is_equal_to(([ACTIVE_JOB], ACTIVE_JOB.id, []))

    def test_delete_removes_selected_id_and_refreshes_board(
        self, app: AppTest, db_path: Path
    ) -> None:
        first = Job("Same company", "Same role", "", "", ApplicationStatus.ACTIVE)
        second = replace(first, id="another-id")
        with Storage(db_path) as database:
            database.insert_job(first)
            database.insert_job(second)
        app.run()
        app.button(key=f"job_{first.id}").click().run()

        app.button(key="delete_job").click().run()
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (
                jobs,
                app.session_state.selected_job_id,
                [s.value for s in app.success],
                [m.value for m in app.markdown if "-badge[" in m.value],
                list(app.exception),
            )
        ).is_equal_to(
            (
                [second],
                None,
                [messages.JOB_DELETED],
                [":yellow-badge[0]", ":blue-badge[1]", ":red-badge[0]"],
                [],
            )
        )

    def test_failed_delete_preserves_job_and_selection(
        self, app: AppTest, db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        job = Job("Example", "Developer", "", "", ApplicationStatus.ACTIVE)
        with Storage(db_path) as database:
            database.insert_job(job)
        app.run()
        app.button(key=f"job_{job.id}").click().run()
        monkeypatch.setattr(
            Storage, "delete_job", Mock(side_effect=sqlite3.OperationalError("Locked"))
        )

        app.button(key="delete_job").click().run()
        with Storage(db_path) as database:
            jobs = database.load_jobs()

        assert_that(
            (
                jobs,
                app.session_state.selected_job_id,
                [e.value for e in app.error],
                list(app.success),
                list(app.exception),
            )
        ).is_equal_to(([job], job.id, [messages.DELETE_FAILED], [], []))

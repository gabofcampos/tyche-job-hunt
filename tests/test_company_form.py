import sqlite3
from functools import partial
from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that
from streamlit.testing.v1 import AppTest

from src import company_form, job_form, storage
from src.schema import Company, CompanyInterestRate, WorkSetup
from src.storage import Storage


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "companies.sqlite3"
    factory = partial(Storage, path)
    for module in (storage, company_form, job_form):
        monkeypatch.setattr(module, "Storage", factory)
    return path


@pytest.fixture
def app(db_path):
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "src/app.py")
    ).run()
    app.button(key="add_company").click().run()
    return app


class TestCompanyForm:
    def test_save_survives_new_session(self, app, db_path):
        app.text_input(key="company_draft_name").set_value("  CARTO  ")

        app.button(key="submit_company_form").click().run()
        fresh = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "src/app.py")
        ).run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that(
            (
                list(app.exception),
                list(fresh.exception),
                [c.name for c in companies],
                [b.label for b in fresh.button if b.key.startswith("company_")],
                app.session_state.company_form_open,
            )
        ).is_equal_to(([], [], ["CARTO"], ["CARTO"], False))

    @pytest.mark.parametrize(
        "name,url", [("   ", ""), ("CARTO", "javascript:alert(1)")]
    )
    def test_invalid_input_is_not_saved(self, app, db_path, name, url):
        app.text_input(key="company_draft_name").set_value(name)
        app.text_input(key="company_draft_website").set_value(url)

        app.button(key="submit_company_form").click().run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that(
            (companies, len(app.error), app.session_state.company_form_open)
        ).is_equal_to(([], 1, True))

    def test_cancel_discards_draft(self, app, db_path):
        app.text_input(key="company_draft_name").set_value("Discard")

        app.button(key="cancel_company_form").click().run()
        app.button(key="add_company").click().run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that(
            (companies, app.text_input(key="company_draft_name").value)
        ).is_equal_to(([], ""))

    def test_failed_save_preserves_draft_and_retry_saves_once(self, app, db_path):
        app.text_input(key="company_draft_name").set_value("Retry")
        with patch.object(
            Storage, "insert_company", side_effect=sqlite3.OperationalError("locked")
        ):
            app.button(key="submit_company_form").click().run()
        retained = app.text_input(key="company_draft_name").value
        error_count = len(app.error)

        app.button(key="submit_company_form").click().run()
        app.run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that((retained, error_count, [c.name for c in companies])).is_equal_to(
            ("Retry", 1, ["Retry"])
        )


class TestCompanyStorage:
    @pytest.mark.parametrize("work_setup", [None, *WorkSetup])
    def test_all_fields_survive_reopening_and_initialization(self, db_path, work_setup):
        from datetime import date

        company = Company(
            "O'Brien",
            "Geo",
            "EU",
            work_setup,
            CompanyInterestRate.HIGH,
            "maps, Python",
            "https://example.com",
            "https://example.com/jobs",
            True,
            "Spatial products",
            date(2026, 10, 1),
            notes="Follow up",
        )
        with Storage(db_path) as database:
            database.initialize_database()
            database.insert_company(company)

        with Storage(db_path) as database:
            database.initialize_database()
            companies = database.load_companies()

        assert_that(companies).is_equal_to([company])


@pytest.fixture
def selected_company(app, db_path):
    app.text_input(key="company_draft_name").set_value("Original")
    app.selectbox(key="company_draft_work_setup").select(WorkSetup.HYBRID)
    app.text_area(key="company_draft_notes").set_value("Keep these notes")
    app.button(key="submit_company_form").click().run()
    with Storage(db_path) as database:
        company = database.load_companies()[0]
    app.button(key=f"company_{company.id}").click().run()
    return company


class TestEditDeleteCompany:
    def test_edit_preserves_id_and_other_fields(self, app, db_path, selected_company):
        from dataclasses import replace

        app.button(key="edit_company").click().run()
        app.text_input(key="company_draft_name").set_value("Renamed")

        app.button(key="submit_company_form").click().run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that((list(app.exception), companies)).is_equal_to(
            ([], [replace(selected_company, name="Renamed")])
        )

    def test_cancel_edit_preserves_saved_company(self, app, db_path, selected_company):
        app.button(key="edit_company").click().run()
        app.text_input(key="company_draft_name").set_value("Discard")

        app.button(key="cancel_company_form").click().run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that(companies).is_equal_to([selected_company])

    def test_delete_persists_and_closes_details(self, app, db_path, selected_company):
        app.button(key="delete_company").click().run()

        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that(
            (
                companies,
                app.session_state.selected_company_id,
                [h.value for h in app.subheader],
                list(app.exception),
            )
        ).is_equal_to(([], None, ["All companies"], []))

    def test_delete_failure_keeps_company_selected(
        self, app, db_path, selected_company
    ):
        with patch.object(
            Storage, "delete_company", side_effect=sqlite3.OperationalError("locked")
        ):
            app.button(key="delete_company").click().run()

        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that(
            (companies, app.session_state.selected_company_id, len(app.error))
        ).is_equal_to(([selected_company], selected_company.id, 1))

    def test_edit_failure_preserves_draft_for_retry(
        self, app, db_path, selected_company
    ):
        app.button(key="edit_company").click().run()
        app.text_input(key="company_draft_name").set_value("Retry")
        with patch.object(
            Storage, "update_company", side_effect=sqlite3.OperationalError("locked")
        ):
            app.button(key="submit_company_form").click().run()
        retained = app.text_input(key="company_draft_name").value

        app.button(key="submit_company_form").click().run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that((retained, [(c.id, c.name) for c in companies])).is_equal_to(
            ("Retry", [(selected_company.id, "Retry")])
        )

    def test_edit_missing_company_does_not_recreate_it(
        self, app, db_path, selected_company
    ):
        app.button(key="edit_company").click().run()
        with Storage(db_path) as database:
            database.delete_company(selected_company.id)

        app.button(key="submit_company_form").click().run()
        with Storage(db_path) as database:
            companies = database.load_companies()

        assert_that(
            (companies, len(app.error), app.session_state.company_form_open)
        ).is_equal_to(([], 1, True))

    def test_delete_missing_id_raises(self, db_path):
        from src.storage import CompanyNotFoundError

        with Storage(db_path) as database:
            database.initialize_database()

            delete = database.delete_company

            assert_that(delete).raises(CompanyNotFoundError).when_called_with("missing")

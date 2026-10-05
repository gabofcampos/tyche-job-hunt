import sqlite3
from functools import partial
from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that
from streamlit.testing.v1 import AppTest

from src import company_form, job_form, storage
from src.schema import Company, CompanyInterestRate
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
    def test_all_fields_survive_reopening_and_initialization(self, db_path):
        from datetime import date

        company = Company(
            "O'Brien",
            "Geo",
            "EU",
            None,
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

from assertpy import assert_that
from streamlit.testing.v1 import AppTest


def companies_app():
    from src.companies_dashboard import render_companies_dashboard
    from src.schema import Company, CompanyInterestRate

    render_companies_dashboard(
        [
            Company(
                name="CARTO",
                industry="Geospatial",
                location="Remote EU",
                work_setup="Remote",
                interest=CompanyInterestRate.HIGH,
                tags="maps, Python",
                website_url="https://carto.com",
                careers_url="",
                contacted=False,
                why_interested="Spatial data products",
                id="carto",
            ),
            Company(
                name="Strava",
                industry="Fitness",
                location="Europe",
                work_setup="Hybrid",
                interest=CompanyInterestRate.SOMEWHAT,
                tags="outdoors",
                website_url="",
                careers_url="",
                contacted=False,
                why_interested="Fitness products",
                id="strava",
            ),
        ]
    )


class TestCompaniesDashboard:
    def test_search_filters_company_rows(self):
        app = AppTest.from_function(companies_app).run()

        app.text_input(key="companies_search").set_value("python").run()

        assert_that(
            [b.label for b in app.button if b.key.startswith("company_")]
        ).is_equal_to(["CARTO"])

    def test_selected_details_survive_filtering(self):
        app = AppTest.from_function(companies_app).run()
        app.button(key="company_carto").click().run()

        app.text_input(key="companies_search").set_value("Strava").run()

        assert_that([t.value for t in app.text]).contains("Spatial data products")

    def test_clear_filters_restores_rows(self):
        app = AppTest.from_function(companies_app).run()
        app.selectbox(key="companies_industry").select("Fitness").run()

        app.button(key="clear_company_filters").click().run()

        assert_that(
            [b.label for b in app.button if b.key.startswith("company_")]
        ).is_equal_to(["CARTO", "Strava"])

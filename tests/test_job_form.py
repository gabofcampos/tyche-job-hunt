import pytest
from assertpy import assert_that

from src.job_form import validate_job
from src.schema import ApplicationStatus, Job


def job(company: str = "Example", role: str = "Developer", platform: str = "") -> Job:
    return Job(company, role, "", "", ApplicationStatus.INTERESTED, platform=platform)


class TestValidateJob:
    @pytest.mark.parametrize(
        "platform", ["", "https://example.com/jobs/1", "http://example.com"]
    )
    def test_valid_job_has_no_error(self, platform: str) -> None:
        candidate = job(platform=platform)

        error = validate_job(candidate)

        assert_that(error).is_none()

    @pytest.mark.parametrize("company,role", [("", "Developer"), ("Example", "")])
    def test_missing_company_or_role_is_rejected(self, company: str, role: str) -> None:
        candidate = job(company, role)

        error = validate_job(candidate)

        assert_that(error).is_equal_to("Enter both a company and a role.")

    @pytest.mark.parametrize("platform", ["example.com", "ftp://example.com/job"])
    def test_invalid_posting_url_is_rejected(self, platform: str) -> None:
        candidate = job(platform=platform)

        error = validate_job(candidate)

        assert_that(error).starts_with("Enter a posting URL")

    def test_required_fields_are_checked_before_url(self) -> None:
        candidate = job(company="", platform="example.com")

        error = validate_job(candidate)

        assert_that(error).is_equal_to("Enter both a company and a role.")

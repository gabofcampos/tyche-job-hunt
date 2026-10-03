from datetime import date

import pytest
from assertpy import assert_that

from src.presentation import application_details
from src.schema import ApplicationStatus, Job


def job(status: ApplicationStatus, applied_on: date | None = None) -> Job:
    return Job(
        "Example",
        "Developer",
        "",
        "",
        status,
        applied_on,
        stage="Technical interview",
        outcome="Withdrawn",
    )


class TestApplicationDetails:
    @pytest.mark.parametrize(
        "status,expected",
        [
            (ApplicationStatus.INTERESTED, []),
            (
                ApplicationStatus.ACTIVE,
                [
                    ("Application", "Applied 12 Sep 2026"),
                    ("Stage", "Technical interview"),
                ],
            ),
            (
                ApplicationStatus.CLOSED,
                [("Application", "Applied 12 Sep 2026"), ("Outcome", "Withdrawn")],
            ),
        ],
    )
    def test_rows_follow_status(
        self, status: ApplicationStatus, expected: list[tuple[str, str]]
    ) -> None:
        candidate = job(status, date(2026, 9, 12))

        rows = application_details(candidate)

        assert_that(rows).is_equal_to(expected)

    @pytest.mark.parametrize(
        "status,expected",
        [
            (
                ApplicationStatus.ACTIVE,
                [
                    ("Application", "No application date provided."),
                    ("Stage", "No stage provided."),
                ],
            ),
            (
                ApplicationStatus.CLOSED,
                [
                    ("Application", "No application date provided."),
                    ("Outcome", "No outcome provided."),
                ],
            ),
        ],
    )
    def test_missing_values_have_placeholders(
        self, status: ApplicationStatus, expected: list[tuple[str, str]]
    ) -> None:
        candidate = Job("Example", "Developer", "", "", status)

        rows = application_details(candidate)

        assert_that(rows).is_equal_to(expected)

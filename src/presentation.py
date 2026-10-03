"""Shared display choices for the job board and details."""

from src.schema import ApplicationStatus

STATUS_COLORS = {
    ApplicationStatus.INTERESTED: "yellow",
    ApplicationStatus.ACTIVE: "blue",
    ApplicationStatus.CLOSED: "red",
}

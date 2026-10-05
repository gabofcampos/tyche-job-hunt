"""User-facing feedback text, shared by the app and its tests."""

from src.schema import ApplicationStatus

DATABASE_UNREADABLE = (
    "Could not open or read the database. "
    "Check that the data folder is accessible and writable, "
    "then reload the app."
)
DATABASE_INVALID = (
    "The database contains an invalid date, status, or company interest. "
    "Check the stored data or restore a known-good backup."
)
SELECTED_JOB_UNAVAILABLE = (
    "This job is no longer available. Select another job to view its details."
)
EDIT_JOB_UNAVAILABLE = "This job is no longer available to edit."
REQUIRED_FIELDS = "Enter both a company and a role."
JOB_DELETED = "Job deleted."
DELETE_JOB_UNAVAILABLE = "This job is no longer available to delete."
DELETE_FAILED = "Could not delete this job. Check database access and try again."
INVALID_POSTING_URL = (
    "Enter a posting URL that starts with http:// or https:// "
    "and includes a valid host, or leave it empty."
)
INVALID_POSTING_LINK = "This posting link needs an HTTP or HTTPS URL with a valid host."
SAVE_FAILED = (
    "Could not save this job. Your entries are still in the form. "
    "Check that the data folder is writable and the database "
    "is not locked, then click Submit again."
)
JOB_NOT_FOUND_ON_SAVE = (
    "This job is no longer saved, so your changes were not applied. "
    "Copy anything you need, then cancel and reload the board."
)


def job_added(status: ApplicationStatus) -> str:
    return f"Job added to {status.value}."


def job_updated(status: ApplicationStatus) -> str:
    return f"Job updated in {status.value}."

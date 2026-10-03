"""Shared display choices for the job board and details."""

from src.schema import ApplicationStatus, Job

STATUS_COLORS = {
    ApplicationStatus.INTERESTED: "yellow",
    ApplicationStatus.ACTIVE: "blue",
    ApplicationStatus.CLOSED: "red",
}


def application_details(job: Job) -> list[tuple[str, str]]:
    """Status-specific (label, text) rows for the details panel."""
    rows = []
    if job.status != ApplicationStatus.INTERESTED:
        rows.append(
            (
                "Application",
                (
                    f"Applied {job.applied_on:%d %b %Y}"
                    if job.applied_on is not None
                    else "No application date provided."
                ),
            )
        )
    if job.status == ApplicationStatus.ACTIVE:
        rows.append(("Stage", job.stage or "No stage provided."))
    elif job.status == ApplicationStatus.CLOSED:
        rows.append(("Outcome", job.outcome or "No outcome provided."))
    return rows

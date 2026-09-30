import streamlit as st

from src.schema import ApplicationStatus, Job


def render_job_card(job: Job) -> None:
    with st.container(border=True, gap="xsmall"):
        st.subheader(job.company, anchor=False)
        st.text(job.role)
        if job.location:
            st.caption(f":material/location_on: {job.location}")

        tags = " · ".join(tag.strip() for tag in job.tags.split(",") if tag.strip())
        if tags:
            st.caption(tags)

        if job.status == ApplicationStatus.ACTIVE:
            if job.applied_on is not None:
                st.caption(f"Applied {job.applied_on:%d %b %Y}")
            if job.stage:
                st.caption(f"Stage: {job.stage}")

        elif job.status == ApplicationStatus.CLOSED:
            if job.applied_on is not None:
                st.caption(f"Applied {job.applied_on:%d %b %Y}")
            if job.outcome:
                st.caption(f"Outcome: {job.outcome}")


def render_no_jobs(
    application_status: ApplicationStatus, *, search_has_no_matches: bool = False
) -> None:
    with st.container(border=True, gap="xsmall"):
        if search_has_no_matches:
            st.caption(
                f"No matching jobs in {application_status.value}. "
                "Try another search or clear it to see all jobs."
            )
        else:
            st.caption(f"No jobs in {application_status.value} yet.")

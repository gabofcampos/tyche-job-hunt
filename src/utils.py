import streamlit as st
from schema import ApplicationStatus, Job


def render_job_card(job: Job) -> None:
    with st.container(border=True, gap="xsmall"):
        st.subheader(job.company, anchor=False)
        st.text(job.role)
        st.caption(f":material/location_on: {job.location}")

        if job.status == ApplicationStatus.INTERESTED:
            st.caption(" · ".join(tag.strip() for tag in job.tags.split(",") if tag.strip()))

        elif job.status == ApplicationStatus.ACTIVE:
            if job.applied_on is not None:
                st.caption(f"Applied {job.applied_on:%d %b %Y}")
            if job.stage:
                st.caption(f"Stage: {job.stage}")

        elif job.status == ApplicationStatus.CLOSED:
            if job.applied_on is not None:
                st.caption(f"Applied {job.applied_on:%d %b %Y}")
            if job.outcome:
                st.caption(f"Outcome: {job.outcome}")

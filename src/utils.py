import streamlit as st
from schema import ApplicationStatus, Job


def render_job_card(job: Job) -> None:
    with st.container(border=True):
        st.subheader(job.company)
        st.write(job.role)
        st.caption(job.location)

        if job.status == ApplicationStatus.INTERESTED:
            st.caption(job.tags)

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
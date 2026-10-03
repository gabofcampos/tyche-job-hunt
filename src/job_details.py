import streamlit as st

from src.schema import Job


def render_job_details(job: Job) -> None:
    with st.container(border=True, key="job_details"):
        st.subheader(job.company, anchor=False)
        st.text(job.role)
        if st.button("Close details", key="close_job_details"):
            st.session_state.selected_job_id = None
            st.rerun()

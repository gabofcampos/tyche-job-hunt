import streamlit as st
from schema import Job

def render_job_card(job: Job) -> None:
    with st.container(border=True):
        st.subheader(job.company)
        st.write(job.role)
        st.caption(job.location)
        st.caption(job.tags)
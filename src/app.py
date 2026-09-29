import streamlit as st
from schema import ApplicationStatus
from utils import render_job_card
from data import ALL_JOBS

st.set_page_config(
    page_title="tyche (fortuna)",
    page_icon="💼",
    layout="wide",
)

board_columns = [
    (ApplicationStatus.INTERESTED, "Jobs I want to consider (not yet applied).", "yellow"),
    (ApplicationStatus.ACTIVE, "Applied and waiting on an answer.", "blue"),
    (ApplicationStatus.CLOSED, "Rejection, withdrawn, or otherwise finished.", "red"),
]

for column, (status, description, color) in zip(st.columns(3, gap="medium"), board_columns):
    jobs = [job for job in ALL_JOBS if job.status == status]
    with column:
        with st.container(border=True, height="stretch"):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.header(status.value, anchor=False)
                st.badge(str(len(jobs)), color=color)
            st.caption(description)

            with st.container(height="stretch"):
                for job in jobs:
                    render_job_card(job)

            st.button("Add a job", icon=":material/add:", width="stretch",
                      disabled=True, key=f"add_{status.name.lower()}")

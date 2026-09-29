import streamlit as st
from schema import Job, ApplicationStatus
from utils import render_job_card

st.set_page_config(
    page_title="tyche (fortuna)",
    page_icon="💼",
    layout="wide",
)

st.title("💼 Tyche - Job Hunt Tracker")

st.write("Welcome to my job tracking tool.")

job_1 = Job(
    company="example company 1",
    role="data engineer",
    location="Madrid/Remote",
    tags="Python, SQL",
    status=ApplicationStatus.INTERESTED
)
job_2 = Job(
    company= "example company 2",
    role= "data engineer",
    location= "Madrid/Remote",
    tags= "Python, Snowflake, PySpark",
    status=ApplicationStatus.ACTIVE

)
jobs = [job_1, job_2]
interested_in_jobs = [job for job in jobs if job.status == ApplicationStatus.INTERESTED]
active_in_jobs = [job for job in jobs if job.status == ApplicationStatus.ACTIVE]
closed_in_jobs = [job for job in jobs if job.status == ApplicationStatus.CLOSED]

col_interested, col_active, col_closed = st.columns(3, border=True)

col_interested, col_active, col_closed = st.columns(3, border=True)

with col_interested:
    st.title("Interested")
    st.caption("jobs considered (not yet applied)")

    for job in interested_in_jobs:
        render_job_card(job)

    st.button("+ add a job")

with col_active:
    st.title("Active")
    st.caption("applied and waiting on an answer")

    for job in active_in_jobs:
        render_job_card(job)

with col_closed:
    st.title("Closed")
    st.caption("rejection, withdrawn, or otherwise finished")

    for job in closed_in_jobs:
        render_job_card(job)
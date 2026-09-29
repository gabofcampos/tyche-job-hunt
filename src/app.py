import streamlit as st
from schema import Job

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
    tags="Python, SQL"
)
job_2 = Job(
    company= "example company 2",
    role= "data engineer",
    location= "Madrid/Remote",
    tags= "Python, Snowflake, PySpark"
)
interested_in_jobs = [job_1, job_2]


col_interested, col_active, col_closed = st.columns(3, border=True)

col_interested.title("Interested")
col_interested.caption("jobs considered (not yet applied)")
for job_card in interested_in_jobs:
    job = col_interested.container(border=True)
    with job:
        st.subheader(job_card.company)
        st.write(job_card.role)
        st.caption(job_card.location)
        st.caption(job_card.tags)
col_interested.button("+ add a job")

col_active.title("Active")
col_active.caption("applied and waiting on an answer")

col_closed.title("Closed")
col_closed.caption("rejection, withdrawn, or otherwise finished")


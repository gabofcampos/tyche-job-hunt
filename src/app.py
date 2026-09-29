import streamlit as st

from schema import ApplicationStatus, Job
from utils import render_job_card, render_no_jobs

st.set_page_config(
    page_title="tyche (fortuna)",
    page_icon="💼",
    layout="wide",
)

if "jobs" not in st.session_state:
    st.session_state.jobs = []


with st.container(border=True):
    title, search, add = st.columns([3, 2, 1], vertical_alignment="center")
    with title:
        st.title("💼 Job Tracker", anchor=False)
    with search:
        query = (
            st.text_input(
                "Search jobs",
                type="search",
                placeholder="Search jobs…",
                label_visibility="collapsed",
            )
            .strip()
            .casefold()
        )
    with add:
        st.button(
            "Add job",
            icon=":material/add:",
            type="primary",
            disabled=True,
            width="stretch",
            key="add_job",
        )

with st.form("job_form"):
    st.subheader("Job details")

    company = st.text_input("Company")
    role = st.text_input("Role")

    submitted = st.form_submit_button("Submit")
if submitted:
    company = company.strip()
    role = role.strip()
    if not company or not role:
        st.error("Enter both a company and a role.")
    else:
        st.session_state.jobs.append(
            Job(
                company=company,
                role=role,
                location="",
                tags="",
                status=ApplicationStatus.INTERESTED,
            )
        )
        st.success("Job added to Interested.")

searched_for_jobs = [
    job
    for job in st.session_state.jobs
    if query in f"{job.company} {job.role} {job.location} {job.tags}".casefold()
]

board_columns = [
    (
        ApplicationStatus.INTERESTED,
        "Jobs I want to consider (not yet applied).",
        "yellow",
    ),
    (ApplicationStatus.ACTIVE, "Applied and waiting on an answer.", "blue"),
    (ApplicationStatus.CLOSED, "Rejection, withdrawn, or otherwise finished.", "red"),
]

for column, (status, description, color) in zip(
    st.columns(3, gap="medium"), board_columns
):
    jobs = [job for job in searched_for_jobs if job.status == status]
    with column:
        with st.container(border=True, height="stretch"):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.header(status.value, anchor=False)
                st.badge(str(len(jobs)), color=color)
            st.caption(description)

            with st.container(height="stretch"):
                for job in jobs:
                    render_job_card(job)
                if not jobs:
                    has_jobs_before_search = any(
                        job.status == status for job in st.session_state.jobs
                    )
                    render_no_jobs(
                        status,
                        search_has_no_matches=bool(query) and has_jobs_before_search,
                    )

            st.button(
                "Add a job",
                icon=":material/add:",
                width="stretch",
                disabled=True,
                key=f"add_{status.name.lower()}",
            )

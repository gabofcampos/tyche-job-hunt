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
if "job_form_open" not in st.session_state:
    st.session_state.job_form_open = False


def close_job_form():
    st.session_state.job_form_open = False


@st.dialog("Job details", on_dismiss=close_job_form)
def show_job_form():
    st.html("""
        <style>
        .st-key-cancel_job_form button {
            background-color: #c92a2a;
            border-color: #c92a2a;
            color: white;
        }
        .st-key-cancel_job_form button:hover {
            background-color: #a51111;
            border-color: #a51111;
            color: white;
        }
        .st-key-cancel_job_form button:focus-visible {
            outline: 2px solid #c92a2a;
            outline-offset: 3px;
        }
        </style>
    """)
    with st.form("job_form", border=False):
        company = st.text_input("Company")
        role = st.text_input("Role")
        location = st.text_input("Location (optional)")
        tags = st.text_input("Tags (optional)", placeholder="Python, SQL")
        selected_status = st.selectbox(
            "Status", list(ApplicationStatus), format_func=lambda status: status.value
        )
        st.caption(
            "For Active and Closed jobs, you can add an application date. "
            "Stage is used for Active jobs; outcome is used for Closed jobs. "
            "Interested jobs ignore these details."
        )
        applied_on = st.date_input("Application date (optional)", value=None)
        stage = st.selectbox(
            "Stage (Active jobs)",
            [
                "Application submitted",
                "Recruiter interview",
                "Technical interview",
                "Final interview",
                "Offer",
            ],
            index=None,
            placeholder="Select a stage (optional)",
        )
        outcome = st.selectbox(
            "Outcome (Closed jobs)",
            [
                "Rejected",
                "Withdrawn",
                "Offer accepted",
                "Offer declined",
                "Position closed",
            ],
            index=None,
            placeholder="Select an outcome (optional)",
        )

        with st.container(horizontal=True):
            submitted = st.form_submit_button("Submit")
            cancelled = st.form_submit_button("Cancel", key="cancel_job_form")
    if cancelled:
        close_job_form()
        st.rerun()

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
                    location=location.strip(),
                    tags=tags.strip(),
                    status=selected_status,
                    applied_on=(
                        applied_on
                        if selected_status != ApplicationStatus.INTERESTED
                        else None
                    ),
                    stage=(
                        stage if selected_status == ApplicationStatus.ACTIVE else None
                    ),
                    outcome=(
                        outcome if selected_status == ApplicationStatus.CLOSED else None
                    ),
                )
            )
            st.session_state.job_added_message = (
                f"Job added to {selected_status.value}."
            )
            close_job_form()
            st.rerun()


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
        if st.button(
            "Add job",
            icon=":material/add:",
            type="primary",
            width="stretch",
            key="add_job",
        ):
            st.session_state.job_form_open = True

if st.session_state.get("job_form_open", False):
    show_job_form()

if "job_added_message" in st.session_state:
    st.success(st.session_state.pop("job_added_message"))

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

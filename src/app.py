import sqlite3

import streamlit as st

from src import messages
from src.job_cards import render_job_card, render_no_jobs
from src.job_details import render_job_details
from src.job_form import open_job_form, show_job_form
from src.presentation import STATUS_COLORS
from src.schema import ApplicationStatus
from src.storage import Storage

st.set_page_config(
    page_title="tyche (fortuna)",
    page_icon="💼",
    layout="wide",
)

try:
    with Storage() as storage:
        storage.initialize_database()
        all_jobs = storage.load_jobs()
except sqlite3.Error, OSError:
    st.error(messages.DATABASE_UNREADABLE)
    st.stop()
except ValueError:
    st.error(messages.DATABASE_INVALID)
    st.stop()

if "job_form_open" not in st.session_state:
    st.session_state.job_form_open = False

def render_jobs_dashboard():
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
                width="stretch",
                key="add_job",
                on_click=open_job_form,
            )

    if st.session_state.get("job_form_open", False):
        show_job_form(all_jobs)

    if "job_saved_message" in st.session_state:
        st.success(st.session_state.pop("job_saved_message"))
    if "job_delete_error" in st.session_state:
        st.error(st.session_state.pop("job_delete_error"))

    searched_for_jobs = [
        job
        for job in all_jobs
        if query in f"{job.company} {job.role} {job.location} {job.tags}".casefold()
    ]

    board_columns = [
        (
            ApplicationStatus.INTERESTED,
            "Jobs I want to consider (not yet applied).",
        ),
        (ApplicationStatus.ACTIVE, "Applied and waiting on an answer."),
        (ApplicationStatus.CLOSED, "Rejection, withdrawn, or otherwise finished."),
    ]

    selected_job_id = st.session_state.get("selected_job_id")
    selected_job = next((job for job in all_jobs if job.id == selected_job_id), None)
    if selected_job_id is not None and selected_job is None:
        st.session_state.selected_job_id = None
        st.info(messages.SELECTED_JOB_UNAVAILABLE)

    if selected_job is not None:
        board_area, details_area = st.columns([2, 1], gap="medium")
    else:
        board_area = st.container()

    with board_area:
        for column, (status, description) in zip(
            st.columns(3, gap="medium"), board_columns
        ):
            jobs = [job for job in searched_for_jobs if job.status == status]
            with column:
                with st.container(border=True, height="stretch"):
                    with st.container(horizontal=True, vertical_alignment="center"):
                        st.header(status.value, anchor=False)
                        st.badge(str(len(jobs)), color=STATUS_COLORS[status])
                    st.caption(description)

                    with st.container(height="stretch"):
                        for job in jobs:
                            render_job_card(job)
                        if not jobs:
                            has_jobs_before_search = any(
                                job.status == status for job in all_jobs
                            )
                            render_no_jobs(
                                status,
                                search_has_no_matches=bool(query)
                                and has_jobs_before_search,
                            )

                    st.button(
                        "Add a job",
                        icon=":material/add:",
                        width="stretch",
                        key=f"add_{status.name.lower()}",
                        on_click=open_job_form,
                        args=(status,),
                    )

    if selected_job is not None:
        with details_area:
            render_job_details(selected_job)


def render_companies_dashboard():
    st.text_input(
        "Search companies",
        placeholder="Company name, tags or notes...",
        key="companies_search",
    )

jobs_tab, companies_tab = st.tabs(["Jobs", "Companies"])

with jobs_tab:
    render_jobs_dashboard()

with companies_tab:
    render_companies_dashboard()
import streamlit as st

from job_cards import render_job_card, render_no_jobs
from job_form import open_job_form, show_job_form
from schema import ApplicationStatus

st.set_page_config(
    page_title="tyche (fortuna)",
    page_icon="💼",
    layout="wide",
)

if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "job_form_open" not in st.session_state:
    st.session_state.job_form_open = False


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
                key=f"add_{status.name.lower()}",
                on_click=open_job_form,
                args=(status,),
            )

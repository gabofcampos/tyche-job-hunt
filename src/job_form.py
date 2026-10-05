import sqlite3
from dataclasses import replace
from pathlib import Path

import streamlit as st

from src import messages
from src.schema import ApplicationStatus, Job, is_valid_http_url
from src.storage import JobNotFoundError, Storage

STAGES = [
    "Application submitted",
    "Recruiter interview",
    "Technical interview",
    "Final interview",
    "Offer",
]
OUTCOMES = [
    "Rejected",
    "Withdrawn",
    "Offer accepted",
    "Offer declined",
    "Position closed",
]


def open_job_form(status: ApplicationStatus = ApplicationStatus.INTERESTED) -> None:
    st.session_state.job_form_status = status
    st.session_state.job_form_job_id = None
    st.session_state.job_form_needs_draft = True
    st.session_state.company_form_open = False
    st.session_state.job_form_open = True


def open_edit_form(job_id: str) -> None:
    st.session_state.job_form_job_id = job_id
    st.session_state.job_form_needs_draft = True
    st.session_state.company_form_open = False
    st.session_state.job_form_open = True


def delete_job(job_id: str) -> None:
    try:
        with Storage() as storage:
            storage.delete_job(job_id)
    except JobNotFoundError:
        st.session_state.job_delete_error = messages.DELETE_JOB_UNAVAILABLE
    except sqlite3.Error, OSError:
        st.session_state.job_delete_error = messages.DELETE_FAILED
    else:
        if st.session_state.get("selected_job_id") == job_id:
            st.session_state.selected_job_id = None
        if st.session_state.get("job_form_job_id") == job_id:
            close_job_form()
            st.session_state.job_form_job_id = None
        st.session_state.job_saved_message = messages.JOB_DELETED


def close_job_form() -> None:
    st.session_state.job_form_open = False


def load_draft(job: Job) -> None:
    """Seed widget state before the form renders, so every open starts fresh."""
    st.session_state.job_draft_company = job.company
    st.session_state.job_draft_role = job.role
    st.session_state.job_draft_platform = job.platform
    st.session_state.job_draft_location = job.location
    st.session_state.job_draft_tags = job.tags
    st.session_state.job_draft_status = job.status
    st.session_state.job_draft_applied_on = job.applied_on
    st.session_state.job_draft_stage = job.stage
    st.session_state.job_draft_outcome = job.outcome
    st.session_state.job_draft_notes = job.notes


def with_saved_value(options: list[str], key: str) -> list[str]:
    # A stored value outside the options would silently become None and be lost.
    value = st.session_state.get(key)
    return options if value is None or value in options else [*options, value]


def validate_job(job: Job) -> str | None:
    """Return the first problem with a trimmed job, or None if it can be saved."""
    if not job.company or not job.role:
        return messages.REQUIRED_FIELDS
    if job.platform and not is_valid_http_url(job.platform):
        return messages.INVALID_POSTING_URL
    return None


def show_job_form(saved_jobs: list[Job]) -> None:
    """Show the create form, or the edit form for the job being edited."""
    job_id = st.session_state.get("job_form_job_id")
    needs_draft = st.session_state.pop("job_form_needs_draft", False)
    if needs_draft or "job_draft_company" not in st.session_state:
        if job_id is None:
            status = st.session_state.get(
                "job_form_status", ApplicationStatus.INTERESTED
            )
            load_draft(Job("", "", "", "", status))
        else:
            job = next((job for job in saved_jobs if job.id == job_id), None)
            if job is None:
                close_job_form()
                st.info(messages.EDIT_JOB_UNAVAILABLE)
                return
            load_draft(job)
    # Once a draft exists it stays open; saving reports a job that has vanished.
    if job_id is None:
        add_job_dialog(None)
    else:
        edit_job_dialog(job_id)


def job_form_body(job_id: str | None) -> None:
    st.html(Path(__file__).parent / "styles" / "job_form.css")
    with st.form("job_form", border=False):
        company = st.text_input("Company", key="job_draft_company")
        role = st.text_input("Role", key="job_draft_role")
        platform = st.text_input("Job search platform (URL)", key="job_draft_platform")
        location = st.text_input("Location (optional)", key="job_draft_location")
        tags = st.text_input(
            "Tags (optional)", placeholder="Python, SQL", key="job_draft_tags"
        )
        selected_status = st.selectbox(
            "Status",
            list(ApplicationStatus),
            format_func=lambda status: status.value,
            key="job_draft_status",
        )
        st.caption(
            "Saving applies the status rules: Interested clears the application "
            "date, stage, and outcome. Active keeps the date and stage and clears "
            "the outcome. Closed keeps the date and outcome and clears the stage."
        )
        applied_on = st.date_input(
            "Application date (optional)", key="job_draft_applied_on"
        )
        stage = st.selectbox(
            "Stage (Active jobs)",
            with_saved_value(STAGES, "job_draft_stage"),
            placeholder="Select a stage (optional)",
            key="job_draft_stage",
        )
        outcome = st.selectbox(
            "Outcome (Closed jobs)",
            with_saved_value(OUTCOMES, "job_draft_outcome"),
            placeholder="Select an outcome (optional)",
            key="job_draft_outcome",
        )

        notes = st.text_area("Notes (optional)", key="job_draft_notes")

        with st.container(horizontal=True):
            submitted = st.form_submit_button("Submit")
            cancelled = st.form_submit_button("Cancel", key="cancel_job_form")
    if cancelled:
        close_job_form()
        st.rerun()

    if submitted:
        saved_job = Job(
            company=company.strip(),
            role=role.strip(),
            platform=platform.strip(),
            notes=notes.strip(),
            location=location.strip(),
            tags=tags.strip(),
            status=selected_status,
            applied_on=(
                applied_on if selected_status != ApplicationStatus.INTERESTED else None
            ),
            stage=(stage if selected_status == ApplicationStatus.ACTIVE else None),
            outcome=(outcome if selected_status == ApplicationStatus.CLOSED else None),
        )
        if job_id is not None:
            saved_job = replace(saved_job, id=job_id)

        error = validate_job(saved_job)
        if error is not None:
            st.error(error)
        else:
            try:
                with Storage() as storage:
                    if job_id is None:
                        storage.insert_job(saved_job)
                    else:
                        storage.update_job(saved_job)
            except JobNotFoundError:
                st.error(messages.JOB_NOT_FOUND_ON_SAVE)
            except sqlite3.Error, OSError:
                st.error(messages.SAVE_FAILED)
            else:
                st.session_state.job_saved_message = (
                    messages.job_added(selected_status)
                    if job_id is None
                    else messages.job_updated(selected_status)
                )
                close_job_form()
                st.rerun()


add_job_dialog = st.dialog("Job details", on_dismiss=close_job_form)(job_form_body)
edit_job_dialog = st.dialog("Edit job", on_dismiss=close_job_form)(job_form_body)

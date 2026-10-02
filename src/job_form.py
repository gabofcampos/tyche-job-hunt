from pathlib import Path

import streamlit as st

from schema import ApplicationStatus, Job


def open_job_form(status: ApplicationStatus = ApplicationStatus.INTERESTED) -> None:
    st.session_state.job_form_status = status
    st.session_state.job_form_open = True


def close_job_form() -> None:
    st.session_state.job_form_open = False


@st.dialog("Job details", on_dismiss=close_job_form)
def show_job_form() -> None:
    st.html(Path(__file__).parent / "styles" / "job_form.css")
    with st.form("job_form", border=False):
        company = st.text_input("Company")
        role = st.text_input("Role")
        platform = st.text_input("Job search platform (URL)")
        location = st.text_input("Location (optional)")
        tags = st.text_input("Tags (optional)", placeholder="Python, SQL")
        selected_status = st.selectbox(
            "Status",
            list(ApplicationStatus),
            index=list(ApplicationStatus).index(st.session_state.job_form_status),
            format_func=lambda status: status.value,
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
                    platform=platform.strip(),
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

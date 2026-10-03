import streamlit as st

from src.job_form import open_edit_form
from src.presentation import STATUS_COLORS
from src.schema import ApplicationStatus, Job, is_valid_posting_url


def close_job_details() -> None:
    st.session_state.selected_job_id = None


def render_job_details(job: Job) -> None:
    with st.container(border=True, key="job_details"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.header("Job details", anchor=False)
            st.button(
                "Close details", key="close_job_details", on_click=close_job_details
            )
        st.subheader(job.company, anchor=False)
        st.text(job.role)
        st.badge(job.status.value, color=STATUS_COLORS[job.status])

        if job.status != ApplicationStatus.INTERESTED:
            st.caption("Application")
            if job.applied_on is not None:
                st.text(f"Applied {job.applied_on:%d %b %Y}")
            else:
                st.text("No application date provided.")

        if job.status == ApplicationStatus.ACTIVE:
            st.caption("Stage")
            st.text(job.stage or "No stage provided.")
        elif job.status == ApplicationStatus.CLOSED:
            st.caption("Outcome")
            st.text(job.outcome or "No outcome provided.")

        st.caption("Location")
        st.text(job.location or "No location provided.")
        st.caption("Tags")
        tags = [tag.strip() for tag in job.tags.split(",") if tag.strip()]
        if tags:
            with st.container(horizontal=True, gap="xsmall"):
                for tag in tags:
                    st.badge(tag, color="gray")
        else:
            st.text("No tags provided.")

        st.caption("Job posting")
        posting_url = job.platform.strip()
        if not posting_url:
            st.caption("No posting link.")
        elif is_valid_posting_url(posting_url):
            st.link_button("Open original posting", posting_url)
        else:
            st.text(job.platform)
            st.caption(
                "This posting link needs an HTTP or HTTPS URL with a valid host."
            )

        st.caption("Notes")
        if job.notes:
            st.text(job.notes)
        else:
            st.caption("No notes provided.")

        st.button(
            "Edit job",
            icon=":material/edit:",
            key="edit_job",
            width="stretch",
            on_click=open_edit_form,
            args=(job.id,),
        )

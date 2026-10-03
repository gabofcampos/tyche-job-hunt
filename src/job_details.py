import streamlit as st

from src.schema import ApplicationStatus, Job


def close_job_details() -> None:
    st.session_state.selected_job_id = None


def render_job_details(job: Job) -> None:
    colors = {
        ApplicationStatus.INTERESTED: "yellow",
        ApplicationStatus.ACTIVE: "blue",
        ApplicationStatus.CLOSED: "red",
    }
    with st.container(border=True, key="job_details"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.header("Job details", anchor=False)
            st.button(
                "Close details", key="close_job_details", on_click=close_job_details
            )
        st.subheader(job.company, anchor=False)
        st.text(job.role)
        st.badge(job.status.value, color=colors[job.status])

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

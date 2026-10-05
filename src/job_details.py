from pathlib import Path

import streamlit as st

from src import messages
from src.job_form import delete_job, open_edit_form
from src.presentation import STATUS_COLORS, application_details
from src.schema import Job, is_valid_http_url


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

        for label, value in application_details(job):
            st.caption(label)
            st.text(value)

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
        elif is_valid_http_url(posting_url):
            st.link_button("Open original posting", posting_url)
        else:
            st.text(job.platform)
            st.caption(messages.INVALID_POSTING_LINK)

        st.caption("Notes")
        if job.notes:
            st.text(job.notes)
        else:
            st.caption("No notes provided.")

        edit_col, del_col = st.columns([0.6, 0.4])
        with edit_col:
            st.button(
                "Edit job",
                icon=":material/edit:",
                key="edit_job",
                width="stretch",
                on_click=open_edit_form,
                args=(job.id,),
            )

        with del_col:
            st.html(Path(__file__).parent / "styles" / "job_delete.css")
            st.button(
                "Delete job",
                icon=":material/delete:",
                key="delete_job",
                width="stretch",
                on_click=delete_job,
                args=(job.id,),
            )

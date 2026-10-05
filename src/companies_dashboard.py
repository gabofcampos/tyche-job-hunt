import streamlit as st

from src import messages
from src.job_cards import render_job_card, render_no_jobs
from src.job_details import render_job_details
from src.job_form import open_job_form, show_job_form
from src.presentation import STATUS_COLORS
from src.schema import ApplicationStatus, Job


def render_companies_dashboard() -> None:
    st.text_input(
        "Search companies",
        placeholder="Company name, tags or notes...",
        key="companies_search",
    )
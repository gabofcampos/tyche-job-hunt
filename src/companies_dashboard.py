import streamlit as st

from src.schema import Company


def render_companies_dashboard() -> None:
    st.text_input(
        "Search companies",
        placeholder="Company name, tags or notes...",
        key="companies_search",
    )

    with st.container(border=True):
        company, industry, location, work_setup, interest, tags, jobs = st.columns(7)

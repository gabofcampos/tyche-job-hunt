import streamlit as st

from src.schema import Company


def render_companies_dashboard() -> None:
    st.text_input(
        "Search companies",
        placeholder="Company name, tags or notes...",
        key="companies_search",
    )

    with st.container(border=True):
        company_col, industry_col, location_col, work_setup_col, interest_col, tags_col, jobs_col = st.columns(7)
        with company_col:
            st.markdown("#### company")
        with industry_col:
            st.markdown("#### industry")
        with location_col:
            st.markdown("#### location")
        with work_setup_col:
            st.markdown("#### work setup")
        with interest_col:
            st.markdown("#### interest")
        with tags_col:
            st.markdown("#### tags")
        with jobs_col:
            st.markdown("#### jobs")

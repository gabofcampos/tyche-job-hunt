import sqlite3

import streamlit as st

from src.schema import Company, CompanyInterestRate, is_valid_posting_url
from src.storage import Storage


def open_company_form() -> None:
    for key in list(st.session_state):
        if key.startswith("company_draft_"):
            del st.session_state[key]
    st.session_state.job_form_open = False
    st.session_state.company_form_open = True


def close_company_form() -> None:
    st.session_state.company_form_open = False


@st.dialog("Add company", on_dismiss=close_company_form)
def show_company_form() -> None:
    with st.form("company_form", border=False):
        name = st.text_input("Company name", key="company_draft_name")
        industry = st.text_input("Industry (optional)", key="company_draft_industry")
        location = st.text_input("Location (optional)", key="company_draft_location")
        work_setup = st.selectbox(
            "Work setup (optional)",
            ["Remote", "Hybrid", "On-site"],
            index=None,
            key="company_draft_work_setup",
        )
        interest = st.selectbox(
            "Interest",
            list(CompanyInterestRate),
            format_func=lambda value: value.value,
            key="company_draft_interest",
        )
        tags = st.text_input(
            "Tags (optional)", placeholder="Python, maps", key="company_draft_tags"
        )
        website = st.text_input("Website URL (optional)", key="company_draft_website")
        careers = st.text_input("Careers URL (optional)", key="company_draft_careers")
        why = st.text_area("Why I saved it (optional)", key="company_draft_why")
        contacted = st.checkbox("Contacted", key="company_draft_contacted")
        contacted_on = st.date_input(
            "Contact date (optional)", value=None, key="company_draft_contacted_on"
        )
        st.caption("The contact date is saved only when Contacted is checked.")
        notes = st.text_area("Notes (optional)", key="company_draft_notes")
        with st.container(horizontal=True):
            submitted = st.form_submit_button(
                "Submit", type="primary", key="submit_company_form"
            )
            cancelled = st.form_submit_button("Cancel", key="cancel_company_form")

    if cancelled:
        close_company_form()
        st.rerun()
    if not submitted:
        return
    if not name.strip():
        st.error("Enter a company name.")
        return
    if any(
        url.strip() and not is_valid_posting_url(url.strip())
        for url in (website, careers)
    ):
        st.error(
            "Enter valid HTTP or HTTPS URLs for Website and Careers, or leave them empty."
        )
        return
    company = Company(
        name=name.strip(),
        industry=industry.strip(),
        location=location.strip(),
        work_setup=work_setup,
        interest=interest,
        tags=tags.strip(),
        website_url=website.strip(),
        careers_url=careers.strip(),
        contacted=contacted,
        contacted_on=contacted_on if contacted else None,
        why_interested=why.strip(),
        notes=notes.strip(),
    )
    try:
        with Storage() as storage:
            storage.insert_company(company)
    except sqlite3.Error, OSError:
        st.error(
            "Could not save this company. Your entries are still in the form. Check database access, then click Submit again."
        )
    else:
        st.session_state.selected_company_id = company.id
        st.session_state.company_saved_message = f"Company added: {company.name}."
        close_company_form()
        st.rerun()

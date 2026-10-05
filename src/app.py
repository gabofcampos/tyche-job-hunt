import sqlite3

import streamlit as st

from src import messages
from src.companies_dashboard import render_companies_dashboard
from src.jobs_dashboard import render_jobs_dashboard
from src.storage import Storage

st.set_page_config(
    page_title="tyche (fortuna)",
    page_icon="💼",
    layout="wide",
)

try:
    with Storage() as storage:
        storage.initialize_database()
        all_jobs = storage.load_jobs()
        all_companies = storage.load_companies()
except sqlite3.Error, OSError:
    st.error(messages.DATABASE_UNREADABLE)
    st.stop()
except ValueError:
    st.error(messages.DATABASE_INVALID)
    st.stop()

if "job_form_open" not in st.session_state:
    st.session_state.job_form_open = False

jobs_tab, companies_tab = st.tabs(["Jobs", "Companies"])

with jobs_tab:
    render_jobs_dashboard(all_jobs)

with companies_tab:
    render_companies_dashboard(all_companies)

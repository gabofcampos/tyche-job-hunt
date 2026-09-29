import streamlit as st

st.set_page_config(
    page_title="tyche (fortuna)",
    page_icon="💼",
    layout="wide",
)

st.title("💼 Tyche - Job Hunt Tracker")

st.write("Welcome to my job tracking tool.")

col_interested, col_active, col_closed = st.columns(3, border=True)

col_interested.title("Interested")
col_interested.caption("jobs considered (not yet applied)")
job = col_interested.container(border=True)
with job:
    st.subheader("Example Company")
    st.write("Data Engineer")
    st.caption("Madrid / Remote")
    st.caption("Python · SQL")
col_interested.button("+ add a job")

col_active.title("Active")
col_active.caption("applied and waiting on an answer")

col_closed.title("Closed")
col_closed.caption("rejection, withdrawn, or otherwise finished")


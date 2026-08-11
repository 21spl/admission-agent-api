import streamlit as st
from utils.session import is_logged_in, is_officer, is_student


def require_login():
    """Call at the top of any page that requires authentication."""
    if not is_logged_in():
        st.warning("Please log in to access this page.")
        st.page_link("app.py", label="Go to Login", icon="🔑")
        st.stop()


def require_student():
    """Call at the top of any student-only page."""
    require_login()
    if not is_student():
        st.error("This page is only available to students.")
        st.stop()


def require_officer():
    """Call at the top of any officer/admin-only page."""
    require_login()
    if not is_officer():
        st.error("This page is only available to officers.")
        st.stop()

import streamlit as st
from utils.session import (
    init_session_state,
    is_logged_in,
    is_officer,
    is_student,
    logout,
)



st.set_page_config(page_title="Admission Portal", page_icon="🎓", layout="centered")
init_session_state()


def logout_page():
    logout()
    st.rerun()


if not is_logged_in():
    public_pages = [
        st.Page("app_pages/home.py", title="Home", icon="🏠"),
        st.Page("app_pages/login.py", title="Login / Register", icon="🔑"),
        st.Page("app_pages/support.py", title="Support (Public)", icon="💬"),
    ]
    pg = st.navigation(public_pages)
    pg.run()
    st.stop()


student_pages = [
    st.Page("app_pages/dashboard.py", title="Dashboard", icon="🏠"),
    st.Page("app_pages/application.py", title="Application", icon="📝"),
    st.Page("app_pages/documents.py", title="Documents", icon="📄"),
    st.Page("app_pages/offers.py", title="Offers", icon="🎓"),
    st.Page("app_pages/loan.py", title="Loan", icon="💰"),
    st.Page("app_pages/my_history.py", title="My History", icon="🕓"),
    st.Page("app_pages/support.py", title="Support", icon="💬"),
]

officer_pages = [
    st.Page("app_pages/admin_reviews.py", title="Reviews", icon="🛡️"),
    st.Page("app_pages/admin_shortlisting.py", title="Shortlisting", icon="📋"),
    st.Page("app_pages/admin_history.py", title="Application History", icon="🕓"),
    st.Page("app_pages/admin_notifications.py", title="Notifications", icon="🔔"),
    st.Page("app_pages/support.py", title="Support", icon="💬"),
]

account_pages = [
    st.Page(logout_page, title="Log out", icon="🚪"),
]

if is_student():
    pg = st.navigation({"Student Portal": student_pages, "Account": account_pages})
elif is_officer():
    pg = st.navigation({"Admin Portal": officer_pages, "Account": account_pages})
else:
    pg = st.navigation(public_pages)

pg.run()

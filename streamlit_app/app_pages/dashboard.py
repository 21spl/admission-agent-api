import streamlit as st
from api import application as application_api
from api.client import APIError
from components.auth_guard import require_student
from components.status_badge import status_badge

require_student()

st.title("🏠 Dashboard")

try:
    application = application_api.get_my_application()
except APIError as e:
    st.error(f"Could not load your dashboard: {e.detail}")
    st.stop()

if application is None:
    st.info("You haven't started your application yet.")
    st.page_link("pages/2_Application.py", label="Start Application", icon="📝")
else:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Application Status**")
        status_badge(application["status"])
    with col2:
        st.metric("Total Marks", application["total_marks"])

    st.divider()
    st.markdown("### Quick Links")
    st.page_link("pages/2_Application.py", label="View / Edit Application", icon="📝")
    st.page_link("pages/3_Documents.py", label="Upload Documents", icon="📄")
    st.page_link("pages/4_Offers.py", label="View Offers", icon="🎓")
    st.page_link("pages/5_Loan.py", label="Loan Application", icon="💰")
    st.page_link("pages/6_Support.py", label="Get Support", icon="💬")

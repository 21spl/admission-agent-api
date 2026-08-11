import streamlit as st
from api import loan as loan_api
from api.client import APIError
from components.auth_guard import require_student
from components.status_badge import status_badge

require_student()

st.title("💰 Loan Application")

try:
    loan = loan_api.get_loan_status()
except APIError as e:
    st.error(f"Could not load your loan status: {e.detail}")
    st.stop()

if loan:
    st.subheader("Your Loan Application")
    status_badge(loan["status"])

    if loan.get("extracted_annual_income") is not None:
        st.metric("Extracted Annual Income", f"₹{loan['extracted_annual_income']:,.2f}")

    if loan.get("decided_at"):
        st.caption(f"Decided on: {loan['decided_at']}")
    else:
        st.caption("Awaiting decision.")

else:
    st.subheader("Apply for a Loan")
    st.caption("Upload your income certificate (PDF or DOCX) to apply.")

    uploaded_file = st.file_uploader("Income Certificate", type=["pdf", "docx"])

    if st.button(
        "Submit Loan Application", type="primary", disabled=uploaded_file is None
    ):
        try:
            file_bytes = uploaded_file.read()
            loan_api.apply_for_loan(
                filename=uploaded_file.name,
                file_bytes=file_bytes,
                content_type=uploaded_file.type,
            )
            st.success("Loan application submitted!")
            st.rerun()
        except APIError as e:
            st.error(f"Submission failed: {e.detail}")

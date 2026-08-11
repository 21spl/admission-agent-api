import streamlit as st
from api import admin_review as admin_review_api
from api.client import APIError
from components.auth_guard import require_officer
from components.status_badge import status_badge

require_officer()

st.title("🛡️ Pending Document Reviews")

try:
    reviews = admin_review_api.list_pending_reviews()
except APIError as e:
    st.error(f"Could not load pending reviews: {e.detail}")
    st.stop()

if not reviews:
    st.info("No applications are currently pending manual review.")
    st.stop()

for review in reviews:
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Application ID:** `{review['application_id']}`")
            st.caption(
                f"Submitted: {review['submitted_at']}  ·  Updated: {review['updated_at']}"
            )
        with col2:
            status_badge(review["status"])

        if review.get("validation_issues"):
            st.warning(f"Validation issues: {review['validation_issues']}")
        if review.get("validation_flags"):
            st.caption(f"Validation flags: {review['validation_flags']}")

        doc_col1, doc_col2 = st.columns(2)
        with doc_col1:
            if review.get("class12_marksheet"):
                st.link_button("View Class 12 Marksheet", review["class12_marksheet"])
            else:
                st.caption("No marksheet on file")
        with doc_col2:
            if review.get("id_card"):
                st.link_button("View ID Card", review["id_card"])
            else:
                st.caption("No ID card on file")

        decision_col1, decision_col2 = st.columns(2)
        app_id = review["application_id"]
        with decision_col1:
            if st.button(
                "✅ Approve",
                key=f"approve_{app_id}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    admin_review_api.submit_review_decision(app_id, approve=True)
                    st.success("Application approved.")
                    st.rerun()
                except APIError as e:
                    st.error(f"Failed: {e.detail}")
        with decision_col2:
            if st.button("❌ Reject", key=f"reject_{app_id}", use_container_width=True):
                try:
                    admin_review_api.submit_review_decision(app_id, approve=False)
                    st.warning("Application rejected.")
                    st.rerun()
                except APIError as e:
                    st.error(f"Failed: {e.detail}")

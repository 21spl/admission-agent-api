import streamlit as st
from api import application as application_api
from api import document as document_api
from api.client import APIError
from components.auth_guard import require_student
from components.status_badge import status_badge
from utils.constants import DOCUMENT_TYPES

require_student()

st.title("📄 Documents")

try:
    application = application_api.get_my_application()
except APIError as e:
    st.error(f"Could not load your application: {e.detail}")
    st.stop()

if not application:
    st.warning("You need to submit your application before uploading documents.")
    st.page_link("app_pages/application.py", label="Go to Application", icon="📝")
    st.stop()

tab_upload, tab_status = st.tabs(["Upload", "Verification Status"])

with tab_upload:
    st.subheader("Upload a Document")
    doc_type = st.selectbox("Document Type", DOCUMENT_TYPES)
    uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])

    if st.button("Upload", type="primary", disabled=uploaded_file is None):
        try:
            file_bytes = uploaded_file.read()
            document_api.upload_document(
                doc_type=doc_type,
                filename=uploaded_file.name,
                file_bytes=file_bytes,
                content_type=uploaded_file.type,
            )
            st.success(f"{uploaded_file.name} uploaded successfully!")
        except APIError as e:
            st.error(f"Upload failed: {e.detail}")

    st.divider()
    st.subheader("Request Validation")
    st.caption("Once all required documents are uploaded, request AI validation.")
    if st.button("Request Document Validation"):
        try:
            result = document_api.request_validation(application["id"])
            st.success("Validation requested.")
            st.json(result)
        except APIError as e:
            st.error(f"Validation request failed: {e.detail}")

with tab_status:
    st.subheader("Document Verification Status")
    try:
        documents = document_api.list_my_documents()
    except APIError as e:
        st.error(f"Could not load documents: {e.detail}")
        documents = []

    if not documents:
        st.info("You haven't uploaded any documents yet.")
    else:
        for doc in documents:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{doc['doc_type'].replace('_', ' ').title()}**")
                    st.caption(f"Uploaded: {doc['uploaded_at']}")
                with col2:
                    status_badge(doc["validation_status"])
                if doc.get("validation_reason"):
                    st.caption(f"Reason: {doc['validation_reason']}")

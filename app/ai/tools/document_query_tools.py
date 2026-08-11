# app/ai/tools/document_query_tools.py
"""
All tools here are scoped to a single application, resolved server-side
from the JWT before this factory is called. application_id is NEVER an
LLM-fillable parameter.
"""

from fastapi import HTTPException
from llama_index.core.tools import FunctionTool

from app.core.factories import get_application_service, get_document_service
from app.models.enums import DocumentType


def build_document_query_tools(db, application_id) -> list[FunctionTool]:
    application_service = get_application_service(db)
    document_service = get_document_service(db, application_service)

    async def list_my_documents() -> list[dict]:
        """List all documents uploaded for the logged-in student's application, with validation status."""
        doc_list = await document_service.list_application_documents(application_id)
        return [
            {
                "document_id": doc.id,
                "document_type": doc.doc_type,
                "document_status": doc.validation_status,
                "file_type": doc.content_type,
            }
            for doc in doc_list
        ]

    async def document_upload_pending() -> list[str]:
        """List required document types the student has NOT uploaded yet."""
        try:
            await application_service.get_application_by_id(application_id)
        except HTTPException:
            return ["error", "No application found"]

        all_docs = await document_service.list_application_documents(application_id)
        required_types = {
            DocumentType.CLASS12_MARKSHEET.value,
            DocumentType.ID_CARD.value,
        }
        uploaded_types = {doc.doc_type for doc in all_docs}
        return list(required_types - uploaded_types)

    async def get_document_download_link(document_type: DocumentType) -> dict:
        """Get a downloadable link for a specific document type on this application.
        document_type must be one of: CLASS12_MARKSHEET, ID_CARD, INCOME_CERTIFICATE."""
        doc_ = await document_service.get_document_by_application_id_and_type(
            application_id, document_type
        )
        if doc_ is None:
            return {"error": "No document found."}
        download_link = await document_service.get_download_link(doc_.id)
        return {
            "document_id": doc_.id,
            "document_type": doc_.doc_type,
            "download_link": download_link,
        }

    async def inspect_validation_issue() -> dict:
        """Get validation issues/blockages currently flagged on this application's documents."""
        try:
            application = await application_service.get_application_by_id(
                application_id
            )
        except HTTPException:
            return {"error": "No application found."}

        return {"validation_issues": application.validation_issues}

    return [
        FunctionTool.from_defaults(
            async_fn=list_my_documents,
            name="list_student_uploaded_documents",
            description="Lists all documents uploaded for the logged-in student's application, with validation status.",
        ),
        FunctionTool.from_defaults(
            async_fn=document_upload_pending,
            name="get_pending_or_missing_documents",
            description="Returns required document types the student has NOT uploaded yet.",
        ),
        FunctionTool.from_defaults(
            async_fn=get_document_download_link,
            name="get_document_download_link",
            description="Generates a download link for a specific document type (CLASS12_MARKSHEET, ID_CARD, or INCOME_CERTIFICATE) on the student's own application.",
        ),
        FunctionTool.from_defaults(
            async_fn=inspect_validation_issue,
            name="inspect_application_validation_issues",
            description="Retrieves validation blockages or discrepancies flagged on the student's uploaded documents.",
        ),
    ]

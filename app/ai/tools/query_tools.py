# app/ai/student_support/tools/query_tools.py
"""
Read-only tools scoped to a single authenticated student.
NEVER accept student_id as a tool parameter — it is bound via closure
at build time from the validated JWT, so the LLM cannot access another
student's data even under adversarial prompting.
"""

from typing import Dict, List
import uuid

from llama_index.core.tools import FunctionTool
from sqlalchemy.ext.asyncio import AsyncSession



from app.models.enums import *
from app.models.domain import *
from app.services import application_history_service
from app.services.application_service import ApplicationService
from app.services.document_service import DocumentService
from app.services.offer_service import OfferService
from app.services.loan_service import LoanService

from app.core.factories import get_application_service, get_document_service, get_loan_service, get_offer_service, get_student_service
from app.core.factories import get_branch_service, get_application_history_service





def get_student_query_tools(db: AsyncSession) -> List[FunctionTool]:
    """
    Factory: call this once per request after JWT Authentication
    """
    student_service = get_student_service(db)
    application_service = get_application_service(db)
    document_service = get_document_service(db, application_service)
    offer_service = get_offer_service(db, application_service)
    loan_service = get_loan_service(db)
    branch_service = get_branch_service(db)
    application_history_service = get_application_history_service(db)

    

    #========================= tool to get application status==========================
    async def get_my_application_status(application_id: uuid.UUID) -> dict:
        app_ = await application_service.get_application_by_id(application_id)
        if app_ is None:
            return {"error": "No application found."}
        return {
            "application_id": app_.id,
            "status": app_.status
        }

    # ======================== tool to get document download link ============================
    async def get_document_download_link(application_id: uuid.UUID, document_type: DocumentType) -> dict:

        doc_ = document_service.get_document_by_application_id_and_type(application_id, document_type)

        if doc_ is None:
            return {"error": "No document found."}

        download_link = document_service.get_download_link(doc_.id)
        return {
            "document_id": doc_.id,
            "document_type": doc_.doc_type,
            "download_link": download_link
        }
        

    async def get_my_offers(application_id: uuid.UUID) -> list[dict]:

        offer_list = await offer_service.list_my_offers(application_id)
        return [
            {
                "offer_id": offer.id,
                "application_id": offer.application_id,
                "status": offer.status,
                "round_number": offer.round_number,
                "offered_branch": branch_service.get_branch(offer.branch_id)
            }
            for offer in offer_list
        ]

    async def get_my_branch_preferences(application_id: uuid.UUID) -> list[dict]:

        # first get the application
        application = await application_service.get_application_by_id(application_id)

        # then get the branch preferences
        preference_list = application.preferences

        return [
            {
                "branch_id": preference.branch_id,
                "branch_name": branch_service.get_branch(preference.branch_id).name,
                "preference_order": preference.preference_order,
                "was_offered": offer_service.check_branch_offered_to_student(application_id, preference.branch_id)   
            }
            for preference in preference_list
        ]

    async def get_my_application_status_history(application_id: uuid.UUID) -> list[dict]:

        status_history_list = application_history_service.get_history_for_officer(application_id)

        return [
            {
                "timestamp": history.changed_at,
                "old_status": history.old_status,
                "new_status": history.new_status,
                "changed_by": history.changed_by
            }
            for history in status_history_list
        ]

    async def get_my_loan_application(application_id: uuid.UUID) -> dict:
        loan = await loan_service.get_loan_application_by_application_id(application_id)
        if loan is None:
            return {"error": "No loan application found."}
        return {
            "loan_id": loan.id,
            "status": loan.status
        }


    async def inspect_validation_issue(application_id: uuid.UUID) -> dict:
        application = await application_service.get_application_by_id(application_id)
        if application is None:
            return {"error": "No application found."}
        return {
            "application_id": application.id,
            "validation_issues": application.validation_issues
        }

    async def list_my_documents(application_id: uuid.UUID) -> list[dict]:
        doc_list = await document_service.list_application_documents(application_id)
        return [
            {
                "document_id": doc.id,
                "document_type": doc.doc_type,
                "document_status": doc.validation_status,
                "file_type": doc.content_type
            }
            for doc in doc_list
        ]

    async def document_upload_pending(application_id: uuid.UUID) -> List[DocumentType]:
        application = await application_service.get_application_by_id(application_id)
        if application is None:
            return "No application found."

        all_docs = await document_service.list_application_documents(application_id)
        required_types = {DocumentType.CLASS12_MARKSHEET.value, DocumentType.ID_CARD.value}
        uploaded_types = {doc.doc_type for doc in all_docs}

        return list(required_types - uploaded_types)


    async def get_all_branch_details() -> list[dict]:
        branch_list = await branch_service.list_branches()
        return [
            {
                "branch_id": branch.id,
                "branch_name": branch.name,
                "branch_code": branch.code,
                "total_seats": branch.total_seats,
                "cutoff_marks": branch.cutoff_marks
            }
            for branch in branch_list
        ]
        
    


    # ============================= TOOL DEFINITION WITH STRUCTURAL DESCRIPTIONS =============================

    validation_issue_inspection_tool = FunctionTool.from_defaults(
        async_fn=inspect_validation_issue,
        name="inspect_application_validation_issues",
        description=(
            "Retrieves a list of blockages, data discrepancies, or verification errors preventing "
            "an application from advancing. Requires a valid application_id (UUID format). "
            "Ask the student for their application ID if it is not present in the current context."
        )
    )

    document_listing_tool = FunctionTool.from_defaults(
        async_fn=list_my_documents,
        name="list_student_uploaded_documents",
        description=(
            "Fetches metadata for all documents currently uploaded to a student's application profile. "
            "Shows validation status and file formats. Requires a valid application_id (UUID format). "
            "Prompt the student for their ID if unknown."
        )
    )

    pending_documents_inspection_tool = FunctionTool.from_defaults(
        async_fn=document_upload_pending,
        name="get_pending_or_missing_documents",
        description=(
            "Checks the application and returns a list of required documents that the student "
            "has NOT uploaded yet (e.g., missing ID card or marksheets). Requires a valid application_id "
            "(UUID format). Ask the user for their application ID before running this tool."
        )
    )

    branch_details_tool = FunctionTool.from_defaults(
        async_fn=get_all_branch_details,
        name="get_all_academic_branch_details",
        description=(
            "Provides general information about all available academic branches, including names, codes, "
            "seat availability, and admission cutoff marks. This is a public query tool and "
            "does NOT require any application_id or student arguments."
        )
    )

    application_status_tool = FunctionTool.from_defaults(
        async_fn=get_my_application_status,
        name="get_student_application_status",
        description=(
            "Retrieves the current status of the student's admission application. "
            "Requires a valid application_id in UUID format (e.g., '123e4567-e89b-12d3-a456-426614174000'). "
            "If the user has not provided their application ID or if it is missing from the conversation context, "
            "you MUST explicitly ask the user to provide it before calling this tool."
        )
    )

    document_download_tool = FunctionTool.from_defaults(
        async_fn=get_document_download_link,
        name="get_document_download_link",
        description=(
            "Generates a downloadable file link for a specific document type belonging to the application. "
            "Requires an application_id (UUID format) and a DocumentType enumeration value."
            "DocumentType can be CLASS12_MARKSHEET or ID_CARD or INCOME_CERTIFICATE."
            "If the application ID is missing from the context, stop and ask the user for it first."
        )
    )

    offer_tool = FunctionTool.from_defaults(
        async_fn=get_my_offers,
        name="get_student_admission_offers",
        description=(
            "Fetches all course or branch admission offers extended to the student's application. "
            "Requires a valid application_id (UUID format). Ask the user for their application ID "
            "if they haven't mentioned it yet."
        )
    )

    branch_preferences_tool = FunctionTool.from_defaults(
        async_fn=get_my_branch_preferences,
        name="get_student_branch_preferences",
        description=(
            "Lists the academic branch rankings chosen by the student and their offer status. "
            "Requires a valid application_id (UUID format). Prompts the user for the ID if unknown."
        )
    )

    application_history_tool = FunctionTool.from_defaults(
        async_fn=get_my_application_status_history,
        name="get_student_application_history",
        description=(
            "Retrieves a complete chronological audit trail of the application status transitions. "
            "Requires a valid application_id (UUID format). Never guess or hallucinate this ID."
        )
    )

    loan_tool = FunctionTool.from_defaults(
        async_fn=get_my_loan_application,
        name="get_student_loan_details",
        description=(
            "Fetches processing information and approval statuses regarding educational loans. "
            "Requires a valid application_id (UUID format). Ask the user for their ID if missing."
        )
    )

    return [
        validation_issue_inspection_tool,
        document_listing_tool,
        pending_documents_inspection_tool,
        branch_details_tool,
        application_status_tool,
        document_download_tool,
        offer_tool,
        branch_preferences_tool,
        application_history_tool,
        loan_tool
    ]


   
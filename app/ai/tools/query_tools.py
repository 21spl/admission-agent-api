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
from app.services.application_service import ApplicationService
from app.services.document_service import DocumentService
from app.services.offer_service import OfferService
from app.services.loan_service import LoanService

from app.core.factories import get_application_service, get_document_service, get_loan_service, get_offer_service, get_student_service






def build_student_query_tools(db: AsyncSession) -> List[FunctionTool]:
    """
    Factory: call this once per request after JWT Authentication
    """
    student_service = get_student_service(db)
    application_service = get_application_service(db)
    document_service = get_document_service(db, application_service)
    offer_service = get_offer_service(db, application_service)
    loan_service = get_loan_service(db)

    

    #========================= tool to get application status==========================
    async def get_my_application_status(application_id: uuid.UUID) -> Dict:
        app_ = await application_service.get_application_by_id(application_id)
        if app_ is None:
            return {"error": "No application found."}
        return {
            "application_id": app_.id,
            "status": app_.status
        }

    # ======================== tool to get document download link ============================
    async def get_document_download_link(application_id: uuid.UUID, document_type: DocumentType) -> Dict:

        doc_ = document_service.get_document_by_application_id_and_type(application_id, document_type)

        if doc_ is None:
            return {"error": "No document found."}

        download_link = document_service.get_download_link(doc_.id)
        return {
            "document_id": doc_.id,
            "document_type": doc_.doc_type,
            "download_link": download_link
        }
        


   

    
   
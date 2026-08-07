
import uuid

from fastapi import Depends

from app.core.dependencies import get_current_officer
from app.models.domain import Application, Document, Officer
from app.models.enums import ApplicationStatus, DocumentType, ValidationStatus
from app.schemas.document import DocumentValidationUpdateRequest

from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository

class AdminReviewService:
    def __init__(self, application_repository: ApplicationRepository, document_repository: DocumentRepository):
        self.application_repository = application_repository
        self.document_repository = document_repository

    #====================================== VALIDATE APPLICATION MANUALLY ======================================
    async def validate_application_manually(self, application_id: uuid.UUID) -> Application:
        # get the application by id
        application = await self.application_repository.get_with_details(application_id)

        # get all the documents for this application
        all_docs = await self.document_repository.get_by_application_id(application_id)

        # mark all the documents VALID
        for doc in all_docs:
            # skip the income certificate only
            if(doc.doc_type==DocumentType.INCOME_CERTIFICATE.value):
                continue
            doc.validation_status = ValidationStatus.VALID.value
            doc.validation_reason = "All documents validated manually by admin"
            await self.document_repository.update(doc)

        # update the application status now
        application.status = ApplicationStatus.VALIDATED
        # also set flags to 0
        application.validation_flags = 0
        application.validation_issues = None
        await self.application_repository.update(application)

        return await self.application_repository.get_with_details(application_id)

    #====================================== REJECT APPLICATION MANUALLY ======================================
    async def reject_application_manually(self, application_id: uuid.UUID) -> Application:
        # get the application by id
        application = await self.application_repository.get_with_details(application_id)

        # get all the documents for this application
        all_docs = await self.document_repository.get_by_application_id(application_id)

        # mark all the documents INVALID
        for doc in all_docs:
            # skip the income certificate only
            if(doc.doc_type==DocumentType.INCOME_CERTIFICATE.value):
                continue
            doc.validation_status = ValidationStatus.INVALID.value
            doc.validation_reason = "Data mismatch issues"
            await self.document_repository.update(doc)

        # update the application status now
        application.status = ApplicationStatus.REJECTED
        await self.application_repository.update(application)

        return await self.application_repository.get_with_details(application_id)

        

        
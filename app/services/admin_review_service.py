import uuid

from app.models.domain import Application
from app.models.enums import ApplicationStatus, DocumentType, ValidationStatus
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository
from app.services.application_service import ApplicationService


class AdminReviewService:
    def __init__(
        self,
        application_repository: ApplicationRepository,
        application_service: ApplicationService,
        document_repository: DocumentRepository,
    ):
        self.application_repository = application_repository
        self.document_repository = document_repository
        self.application_service = application_service

    # ====================================== VALIDATE APPLICATION MANUALLY ======================================
    async def validate_application_manually(
        self, application_id: uuid.UUID
    ) -> Application:
        # get the application by id
        application = await self.application_repository.get_with_details(application_id)

        # get all the documents for this application
        all_docs = await self.document_repository.get_by_application_id(application_id)

        # mark all the documents VALID
        for doc in all_docs:
            # skip the income certificate only
            if doc.doc_type == DocumentType.INCOME_CERTIFICATE.value:
                continue
            doc.validation_status = ValidationStatus.VALID.value
            doc.validation_reason = "All documents validated manually by admin"
            await self.document_repository.update(doc)

        # update the only the non-status fields
        # also set flags to 0
        application.validation_flags = 0
        application.validation_issues = None

        await self.application_repository.update(application)

        # also call the application service method to update the application status history
        await self.application_service.update_application_status(
            application.id, ApplicationStatus.VALIDATED, changed_by="admin"
        )

        return await self.application_repository.get_with_details(application_id)

    # ====================================== REJECT APPLICATION MANUALLY ======================================
    async def reject_application_manually(
        self, application_id: uuid.UUID
    ) -> Application:
        # get the application by id
        application = await self.application_repository.get_with_details(application_id)

        # get all the documents for this application
        all_docs = await self.document_repository.get_by_application_id(application_id)

        # mark all the documents INVALID
        for doc in all_docs:
            # skip the income certificate only
            if doc.doc_type == DocumentType.INCOME_CERTIFICATE.value:
                continue
            doc.validation_status = ValidationStatus.INVALID.value
            doc.validation_reason = "Data mismatch issues"
            await self.document_repository.update(doc)

        # also call the application service method to update the application status history

        await self.application_repository.update(application)

        await self.application_service.update_application_status(
            application.id, ApplicationStatus.REJECTED, changed_by="admin"
        )

        return await self.application_repository.get_with_details(application_id)

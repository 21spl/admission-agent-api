import io
import uuid
from typing import List
from fastapi import HTTPException, status

from app.services.application_history_service import ApplicationHistoryService
from app.services.notification_service import NotificationService
from app.storage import storage_manager, StorageUploadError

# import repositories
from app.repositories.document_repository import DocumentRepository
from app.repositories.application_repository import ApplicationRepository

# import schemas

from app.schemas.document import DocumentValidationUpdateRequest

# import models
from app.models.domain import Document, Student
from app.models.enums import DocumentType, ValidationStatus, ApplicationStatus, AllowedFileType
from app.models.enums import DocumentType, ValidationStatus, ApplicationStatus, AllowedFileType, AI_MANAGED_TYPES

# import services
from app.services.application_service import ApplicationService
# import storage manager
from app.storage import storage_manager, StorageUploadError, StorageFetchError

from app.models.enums import AllowedFileType

class DocumentService:
    def __init__(
        self, 
        repository: DocumentRepository, 
        application_repository: ApplicationRepository, 
        application_service: ApplicationService,
    ):
        self.repository = repository
        self.application_repository = application_repository
        self.application_service = application_service


    
#=============================================== UPLOAD DOCUMENT ======================================================
    async def upload_document_metadata(
        self, student: Student, doc_type: DocumentType, filename: str,
        file_bytes: bytes, content_type: AllowedFileType
    ) -> Document:
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active application found. Please submit your application marks and preferences first."
            )

        existing_doc = await self.repository.get_by_type(application.id, doc_type.value)
        storage_key = storage_manager.build_student_doc_key(application.id, doc_type.value, filename)

        try:
            await storage_manager.upload_document(io.BytesIO(file_bytes), storage_key, content_type.value)
        except StorageUploadError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to store the uploaded document. Please try again."
            )

        if existing_doc:
            existing_doc.storage_key = storage_key
            existing_doc.content_type = content_type.value
            existing_doc.file_size_bytes = len(file_bytes)
            existing_doc.validation_status = ValidationStatus.PENDING.value
            existing_doc.validation_reason = None
            updated_doc = await self.repository.update(existing_doc)
            await self.application_service.update_application_status(
                application.id, ApplicationStatus.DOCS_PENDING, f"STUDENT_OVERWRITE_{student.id}"
            )
            return updated_doc

        new_doc = Document(
            application_id=application.id,
            doc_type=doc_type.value,
            storage_key=storage_key,
            content_type=content_type.value,
            file_size_bytes=len(file_bytes),
            validation_status=ValidationStatus.PENDING.value
        )
        created_doc = await self.repository.create(new_doc)
        doc_id = created_doc.id
        await self.application_service.update_application_status(
            application.id, ApplicationStatus.DOCS_PENDING, f"STUDENT_UPLOAD_{student.id}"
        )
        return await self.repository.get_by_id(doc_id)



#=============================================== LIST ALL DOCUMENTS FOR AN APPLICATION =========================================
    async def list_application_documents(self, application_id: uuid.UUID) -> List[Document]:
        return await self.repository.get_by_application_id(application_id)


#=============================================== GET DOCUMENT BY ID =========================================
    async def get_document_bytes(self, document_id: uuid.UUID) -> tuple[bytes, str, str]:
        """Fetches the raw file bytes for a document, along with its content type and filename hint."""
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found.")

        try:
            file_bytes = await storage_manager.fetch_document(document.storage_key)
        except StorageFetchError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve the document from storage. Please try again."
            )

        return file_bytes, document.content_type, document.storage_key


#=============================================== GET ALL DOCUMENT BYTES FOR AN APPLICATION =========================================
    async def get_all_document_bytes_for_application(self, application_id: uuid.UUID) -> list[tuple[bytes, str, str]]:
        """Fetches raw bytes for every document belonging to an application, for batch indexing."""
        documents = await self.repository.get_by_application_id(application_id)
        results = []
        for doc in documents:
            file_bytes = await storage_manager.fetch_document(doc.storage_key)
            results.append((file_bytes, doc.content_type, doc.storage_key))
        return results

# =============================================== CHECK ALL DOCUMENTS UPLOADED OR NOT =========================================
    async def check_all_document_types_uploaded(self, application_id: uuid.UUID) -> bool:
        all_docs = await self.repository.get_by_application_id(application_id)
        required_types = {DocumentType.CLASS12_MARKSHEET.value, DocumentType.ID_CARD.value}
        uploaded_types = {doc.doc_type for doc in all_docs}
        if required_types.issubset(uploaded_types):
            await self.application_service.update_application_status(application_id, ApplicationStatus.ALL_DOCS_UPLOADED, "AI")
            return True
        return False



#=================================== MARK AUTO VALIDATED BY AI ===================================


    async def mark_auto_validated(self, application_id: uuid.UUID, doc_types: list[str]) -> None:
        application = await self.application_repository.get_by_id(application_id)
        # only change the non-status fields and update
        application.validation_flags = 0
        application.validation_issues = None
        await self.application_repository.update(application)

        # now mark all the documments VALID
        all_docs = await self.repository.get_by_application_id(application_id)
        for doc in all_docs:
            if doc.doc_type in doc_types:
                doc.validation_status = ValidationStatus.VALID.value
                doc.validation_reason = None
                await self.repository.update(doc)

        # now only update the application status
        await self.application_service.update_application_status(application_id, ApplicationStatus.VALIDATED, "AI")



#=================================== MARK AUTO REJECTED BY AI ===================================


    async def mark_auto_rejected(self, application_id: uuid.UUID, reason: str, doc_types: list[str]) -> None:
        application = await self.application_repository.get_by_id(application_id)
        # only change the non-status fields and update
        application.validation_issues = reason
        await self.application_repository.update(application)

        all_docs = await self.repository.get_by_application_id(application_id)
        for doc in all_docs:
            if doc.doc_type in doc_types:
                doc.validation_status = ValidationStatus.INVALID.value
                doc.validation_reason = reason
                await self.repository.update(doc)

        # now only update the application status
        await self.application_service.update_application_status(application_id, ApplicationStatus.REJECTED, "AI")



#=================================== MARK AUTO PENDING BY AI ===================================

    async def mark_auto_pending(
        self, application_id: uuid.UUID, flags: int, issues: str, doc_types: list[str]
    ) -> None:
        application = await self.application_repository.get_by_id(application_id)
        # only change the non-status fields and update
        application.validation_flags = flags
        application.validation_issues = issues
        await self.application_repository.update(application)

        all_docs = await self.repository.get_by_application_id(application_id)
        for doc in all_docs:
            if doc.doc_type in doc_types:
                doc.validation_status = ValidationStatus.PENDING.value
                doc.validation_reason = None
                await self.repository.update(doc)

        # now only update the application status
        await self.application_service.update_application_status(application_id, ApplicationStatus.PENDING_REVIEW, "AI")


        # Individual Document.validation_status intentionally left as PENDING here —
        # the grey-zone case needs a human decision before any doc gets flipped to
        # VALID/INVALID. The admin's eventual decision (submit_review_decision)
        # resolves this via mark_validated/mark_rejected.


# ================================== Get download link for a document ==================================
    async def get_download_link(self, document_id: uuid.UUID) -> str:
        # get the document record from the database
        doc = await self.repository.get_by_id(document_id)
        key = doc.storage_key
        link = await storage_manager.generate_presigned_url(key)
        return link


    
import io
import uuid
from typing import List
from fastapi import HTTPException, status

from app.storage import storage_manager, StorageUploadError

# import repositories
from app.repositories.document_repository import DocumentRepository
from app.repositories.application_repository import ApplicationRepository

# import schemas

from app.schemas.document import DocumentValidationUpdateRequest

# import models
from app.models.domain import Document, Student
from app.models.enums import DocumentType, ValidationStatus, ApplicationStatus, AllowedFileType

# import services
from app.services.application_service import ApplicationService

class DocumentService:
    def __init__(self, repository: DocumentRepository, application_repository: ApplicationRepository, application_service: ApplicationService):
        self.repository = repository
        self.application_repository = application_repository
        self.application_service = application_service

    from app.models.enums import AllowedFileType

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
        await self.application_service.update_application_status(
            application.id, ApplicationStatus.DOCS_PENDING, f"STUDENT_UPLOAD_{student.id}"
        )
        return created_doc

    async def list_application_documents(self, application_id: uuid.UUID) -> List[Document]:
        return await self.repository.get_by_application_id(application_id)

    async def process_document_validation(self, document_id: uuid.UUID, data: DocumentValidationUpdateRequest, officer_name: str) -> Document:
        """Updates document verification records and evaluates overall application states."""
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found.")

        # Update document metadata attributes
        document.validation_status = data.validation_status.value
        document.validation_reason = data.validation_reason if data.validation_status == ValidationStatus.INVALID else None
        updated_doc = await self.repository.update(document)

        # Fetch all matching files to run state transition evaluation rules
        all_docs = await self.repository.get_by_application_id(document.application_id)
        
        # Evaluate states: If any document is rejected, flip application to DOCS_INVALID
        if any(d.validation_status == ValidationStatus.INVALID.value for d in all_docs):
            await self.application_service.update_application_status(
                document.application_id, ApplicationStatus.DOCS_INVALID, officer_name
            )
        # Required documentation core checklist count validation (e.g. at least Marksheet and ID)
        elif len(all_docs) >= 2 and all(d.validation_status == ValidationStatus.VALID.value for d in all_docs):
            await self.application_service.update_application_status(
                document.application_id, ApplicationStatus.DOCS_VALIDATED, officer_name
            )

        return updated_doc



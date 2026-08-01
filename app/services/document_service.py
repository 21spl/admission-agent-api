import uuid
from typing import List
from fastapi import HTTPException, status
from app.repositories.document_repository import DocumentRepository
from app.repositories.application_repository import ApplicationRepository
from app.schemas.document import DocumentValidationUpdateRequest
from app.models.domain import Document, Student
from app.models.enums import DocumentType, ValidationStatus, ApplicationStatus
from app.services.application_service import ApplicationService

class DocumentService:
    def __init__(self, repository: DocumentRepository, application_repository: ApplicationRepository, application_service: ApplicationService):
        self.repository = repository
        self.application_repository = application_repository
        self.application_service = application_service

    async def upload_document_metadata(self, student: Student, doc_type: DocumentType, filename: str) -> Document:
        """Validates student application context and registers uploaded document paths."""
        # 1. Look up the student's active application header
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active application found. Please submit your application marks and preferences first."
            )

        # 2. Check if a document of this type already exists to simulate an overwrite/replacement
        existing_doc = await self.repository.get_by_type(application.id, doc_type.value)
        
        # In a real disk setup, you'd save the bytes here. For the free tier cloud plan, 
        # we generate a unique reference file path string and track it inside Neon.
        simulated_path = f"uploads/{application.id}/{uuid.uuid4()}_{filename}"

        if existing_doc:
            existing_doc.file_path = simulated_path
            existing_doc.validation_status = ValidationStatus.PENDING.value
            existing_doc.validation_reason = None
            updated_doc = await self.repository.update(existing_doc)
            
            # Reset application status back to pending documentation review loop
            await self.application_service.update_application_status(
                application.id, ApplicationStatus.DOCS_PENDING, f"STUDENT_OVERWRITE_{student.id}"
            )
            return updated_doc

        # 3. Create a fresh document record entry
        new_doc = Document(
            application_id=application.id,
            doc_type=doc_type.value,
            file_path=simulated_path,
            validation_status=ValidationStatus.PENDING.value
        )
        created_doc = await self.repository.create(new_doc)

        # Update application overview state
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



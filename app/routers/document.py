import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from app.core.factories import get_document_service
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse, DocumentValidationUpdateRequest
from app.core.dependencies import get_current_student, get_current_officer
from app.models.domain import Student, Officer
from app.models.enums import DocumentType

router = APIRouter(prefix="/documents", tags=["Document Infrastructure"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_stream(
    doc_type: DocumentType = Form(..., description="The classification type of the uploaded document file"),
    file: UploadFile = File(..., description="The physical file payload payload matching PDF or images"),
    service: DocumentService = Depends(get_document_service),
    current_student: Student = Depends(get_current_student)
):
    """
    Secured Student Endpoint: Allows an authenticated applicant to upload 
    verification document variants as a multi-part form asset stream.
    """
    return await service.upload_document_metadata(
        student=current_student, 
        doc_type=doc_type, 
        filename=file.filename
    )


@router.get("/application/{application_id}", response_model=List[DocumentResponse], status_code=status.HTTP_200_OK)
async def get_documents_by_application(
    application_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
    current_officer: Officer = Depends(get_current_officer)
):
    """
    Secured Officer Endpoint: Allows an authenticated admission officer to 
    inspect the complete listing of files uploaded against an application instance index.
    """
    return await service.list_application_documents(application_id)


@router.patch("/{document_id}/verify", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def verify_uploaded_document(
    document_id: uuid.UUID,
    payload: DocumentValidationUpdateRequest,
    service: DocumentService = Depends(get_document_service),
    current_officer: Officer = Depends(get_current_officer)
):
    """
    Secured Officer Endpoint: Allows a logged-in officer to transition validation 
    states and flag file exceptions. Automatically prompts application status history re-evaluations.
    """
    operator_identity = f"OFFICER_ID:{current_officer.id}"
    return await service.process_document_validation(
        document_id=document_id, 
        data=payload, 
        officer_name=operator_identity
    )

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from app.ai.config import initialize_ai_environment
from app.ai.workflows.document_validation_workflow import DocumentValidationWorkflow
from app.core.factories import get_document_service
from app.repositories import application_repository
from app.core.factories import get_application_repository
from app.services.document_service import DocumentService

from app.schemas.document import DocumentResponse, DocumentValidationUpdateRequest
from app.core.dependencies import get_current_student, get_current_officer
from app.models.domain import Student, Officer
from app.models.enums import DocumentType

from app.core.dependencies import get_current_student, get_current_officer, validate_uploaded_file_type
from app.models.enums import AllowedFileType

router = APIRouter(prefix="/documents", tags=["Document Infrastructure"])

llm = initialize_ai_environment()

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_stream(
    doc_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    validated_content_type: AllowedFileType = Depends(validate_uploaded_file_type),
    service: DocumentService = Depends(get_document_service),
    current_student: Student = Depends(get_current_student)
):
    file_bytes = await file.read()
    return await service.upload_document_metadata(
        student=current_student,
        doc_type=doc_type,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=validated_content_type
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
    if current_officer is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
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


@router.post("/applications/{application_id}/documents/validate")
async def request_all_document_validation(
    application_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
    student: Student = Depends(get_current_student),
    application_repository: application_repository = Depends(get_application_repository)
):
    if student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    if not await service.check_all_document_types_uploaded(application_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All document types not uploaded",
        )

    workflow = DocumentValidationWorkflow(
        document_service=service,
        application_repository=application_repository,  
        llm=llm,
        timeout=120,
        verbose=False,
    )

    result = await workflow.run(application_id=application_id)
    return result



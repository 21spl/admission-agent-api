import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.ai.config import initialize_ai_environment
from app.ai.workflows.document_validation_workflow import DocumentValidationWorkflow
from app.core.dependencies import (
    get_current_student,
    validate_uploaded_file_type,
)
from app.core.factories import (
    get_application_repository,
    get_document_service,
    get_student_repository,
)
from app.models.domain import Student
from app.models.enums import AllowedFileType, DocumentType
from app.repositories import application_repository, student_repository
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Document Infrastructure"])

llm = initialize_ai_environment()

# ================================= UPLOAD DOCUMENT ===============================


@router.post(
    "/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_file_stream(
    doc_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    validated_content_type: AllowedFileType = Depends(validate_uploaded_file_type),
    service: DocumentService = Depends(get_document_service),
    current_student: Student = Depends(get_current_student),
):
    file_bytes = await file.read()
    return await service.upload_document_metadata(
        student=current_student,
        doc_type=doc_type,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=validated_content_type,
    )


'''
=================================== FOLLOWING METHOD IS LIKELY TO BE DEPRECATED ================================
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

'''


# ================================ REQUEST FOR DOCUMENT VALIDATION ================================


@router.post("/applications/{application_id}/documents/validate")
async def request_all_document_validation(
    application_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
    student: Student = Depends(get_current_student),
    application_repository: application_repository = Depends(
        get_application_repository
    ),
    student_repository: student_repository = Depends(get_student_repository),
):
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    if not await service.check_all_document_types_uploaded(application_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All document types not uploaded",
        )

    workflow = DocumentValidationWorkflow(
        document_service=service,
        application_repository=application_repository,
        student_repository=student_repository,
        llm=llm,
        timeout=120,
        verbose=False,
    )

    result = await workflow.run(application_id=application_id)
    return result


@router.get(
    "/me", response_model=list[DocumentResponse], status_code=status.HTTP_200_OK
)
async def list_my_documents(
    service: DocumentService = Depends(get_document_service),
    current_student: Student = Depends(get_current_student),
):
    """
    Secured Student Endpoint: Lists all documents uploaded against the
    current student's application, including validation status.
    """
    if current_student.application is None:
        raise HTTPException(
            status_code=404, detail="No application found for this student."
        )

    return await service.list_application_documents(current_student.application.id)
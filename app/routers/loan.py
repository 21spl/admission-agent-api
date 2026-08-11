from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.dependencies import get_current_student
from app.core.factories import get_loan_service
from app.models.domain import Student
from app.models.enums import AllowedFileType
from app.schemas.loan import LoanApplicationResponse
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loan", tags=["loan"])


ALLOWED_CONTENT_TYPES = {t.value for t in AllowedFileType}


@router.post(
    "/apply",
    response_model=LoanApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_for_loan(
    file: UploadFile = File(...),
    student: Student = Depends(get_current_student),
    loan_service: LoanService = Depends(get_loan_service),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported file type: {file.content_type}",
        )

    file_bytes = await file.read()
    content_type = AllowedFileType(file.content_type)

    return await loan_service.request_loan(
        student=student,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=content_type,
    )


@router.get("/status", response_model=LoanApplicationResponse)
async def get_loan_application(
    student: Student = Depends(get_current_student),
    loan_service: LoanService = Depends(get_loan_service),
):
    loan_application = await loan_service.get_loan_application(student)
    # convert to response model
    response = LoanApplicationResponse(
        id=loan_application.id,
        application_id=loan_application.application_id,
        income_certificate_doc_id=loan_application.income_certificate_doc_id,
        status=loan_application.status,
        extracted_annual_income=loan_application.extracted_annual_income,
        decided_at=loan_application.decided_at,
    )

    return response

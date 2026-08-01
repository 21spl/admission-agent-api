import uuid
from fastapi import APIRouter, Depends, status
from app.core.factories import get_loan_service
from app.services.loan_service import LoanService
from app.schemas.loan import LoanApplicationCreateRequest, LoanStatusUpdateRequest, LoanApplicationResponse
from app.core.dependencies import get_current_student, get_current_officer
from app.models.domain import Student, Officer

router = APIRouter(prefix="/loans", tags=["Student Loan Infrastructure"])

@router.post("/apply", response_model=LoanApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_loan_application(
    payload: LoanApplicationCreateRequest,
    service: LoanService = Depends(get_loan_service),
    current_student: Student = Depends(get_current_student)
):
    """
    Secured Student Endpoint: Allows an authenticated applicant to initialize 
    a support loan application using an income certificate verification document index.
    """
    return await service.apply_for_student_loan(current_student, payload)


@router.get("/me", response_model=LoanApplicationResponse, status_code=status.HTTP_200_OK)
async def get_my_loan_status(
    service: LoanService = Depends(get_loan_service),
    current_student: Student = Depends(get_current_student)
):
    """
    Secured Student Endpoint: Allows applicants to check evaluation metrics 
    and progress logs mapped to their profile.
    """
    return await service.get_loan_by_student(current_student)


@router.patch("/{loan_id}/evaluate", response_model=LoanApplicationResponse, status_code=status.HTTP_200_OK)
async def officer_evaluate_loan(
    loan_id: uuid.UUID,
    payload: LoanStatusUpdateRequest,
    service: LoanService = Depends(get_loan_service),
    current_officer: Officer = Depends(get_current_officer)
):
    """
    Secured Officer Endpoint: Restricts processing pipelines to authenticated internal 
    officers to explicitly APPROVE or REJECT a student loan application folder.
    """
    return await service.evaluate_loan_application(loan_id, payload)

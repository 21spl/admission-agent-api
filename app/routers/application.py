from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_student
from app.core.factories import get_application_service
from app.models.domain import Student
from app.schemas.application import ApplicationCreateRequest, ApplicationResponse
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])

# ================================= SUBMIT APPLICATION ===============================


@router.post(
    "", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def submit_admission_application(
    payload: ApplicationCreateRequest,
    service: ApplicationService = Depends(get_application_service),
    current_student: Student = Depends(get_current_student),
):
    """
    Secured Student Endpoint: Allows an authenticated student to submit
    their centralized marks and branch preferences.
    """
    return await service.create_student_application(current_student, payload)


# =============================== GET MY APPLICATION ===============================
@router.get("/me", response_model=ApplicationResponse, status_code=status.HTTP_200_OK)
async def get_my_application_profile(
    service: ApplicationService = Depends(get_application_service),
    current_student: Student = Depends(get_current_student),
):
    """
    Secured Student Endpoint: Allows a logged-in student to check their
    active application workflow metrics and preference state.
    """
    return await service.get_student_application(current_student)

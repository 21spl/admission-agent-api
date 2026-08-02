import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from app.core.factories import get_application_history_service
from app.services.application_history_service import ApplicationHistoryService
from app.schemas.application_history import ApplicationStatusHistoryResponse
from app.core.dependencies import get_current_student, get_current_officer
from app.models.domain import Student, Officer

router = APIRouter(prefix="/applications/history", tags=["Application Audit History"])

@router.get("/me", response_model=List[ApplicationStatusHistoryResponse], status_code=status.HTTP_200_OK)
async def get_my_application_audit_trail(
    service: ApplicationHistoryService = Depends(get_application_history_service),
    current_student: Student = Depends(get_current_student)
):
    """
    Secured Student Endpoint: Allows an applicant to track every historical 
    status update applied to their admission folder.
    """
    return await service.get_history_for_student(current_student)


@router.get("/application/{application_id}", response_model=List[ApplicationStatusHistoryResponse], status_code=status.HTTP_200_OK)
async def officer_get_application_audit_trail(
    application_id: uuid.UUID,
    service: ApplicationHistoryService = Depends(get_application_history_service),
    current_officer: Officer = Depends(get_current_officer)
):
    """
    Secured Officer Endpoint: Provides administrative visibility into the full 
    chronological state transitions of any given application ID for interview verifications.
    """
    if current_officer is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return await service.get_history_for_officer(application_id)


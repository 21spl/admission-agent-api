import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from pydantic import EmailStr
from app.core.factories import get_notification_service
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationLogResponse
from app.core.dependencies import get_current_officer
from app.models.domain import Officer

router = APIRouter(prefix="/notifications", tags=["Notification Communications Ledger"])

@router.get("/application/{application_id}", response_model=List[NotificationLogResponse], status_code=status.HTTP_200_OK)
async def get_notifications_for_application(
    application_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
    current_officer: Officer = Depends(get_current_officer)
):
    """
    Secured Officer Endpoint: Allows an authenticated officer to verify the full history 
    of system communications sent to a specific student folder.
    """
    if current_officer is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await service.get_application_logs(application_id)


@router.get("/recipient", response_model=List[NotificationLogResponse], status_code=status.HTTP_200_OK)
async def get_notifications_by_email_address(
    email: EmailStr,
    service: NotificationService = Depends(get_notification_service),
    current_officer: Officer = Depends(get_current_officer)
):
    """
    Secured Officer Endpoint: Allows administrative staff to audit logs 
    by targeting a specific recipient email address.
    """
    if current_officer is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await service.get_logs_by_email(str(email))

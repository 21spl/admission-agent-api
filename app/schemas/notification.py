import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import NotificationType, NotificationStatus

class NotificationLogCreate(BaseModel):
    application_id: Optional[uuid.UUID] = None
    recipient_email: EmailStr
    type: NotificationType
    status: NotificationStatus = Field(default=NotificationStatus.SENT)

class NotificationLogResponse(BaseModel):
    id: uuid.UUID
    application_id: Optional[uuid.UUID]
    recipient_email: str
    type: str
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True

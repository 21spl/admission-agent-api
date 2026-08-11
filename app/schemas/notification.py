import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import NotificationStatus, NotificationType


class NotificationLogCreate(BaseModel):
    application_id: uuid.UUID | None = None
    recipient_email: EmailStr
    type: NotificationType
    status: NotificationStatus = Field(default=NotificationStatus.SENT)


class NotificationLogResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID | None
    recipient_email: str
    type: NotificationType
    status: NotificationStatus
    sent_at: datetime

    class Config:
        from_attributes = True

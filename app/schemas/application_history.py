import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import ApplicationStatus

class ApplicationStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    old_status: Optional[ApplicationStatus] = None
    new_status: ApplicationStatus
    changed_by: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True



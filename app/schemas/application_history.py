import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ApplicationStatus


class ApplicationStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    old_status: ApplicationStatus | None = None
    new_status: ApplicationStatus
    changed_by: str | None
    changed_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApplicationStatus


class ReviewsPendingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: uuid.UUID
    submitted_at: datetime
    status: ApplicationStatus
    validation_flags: int | None
    validation_issues: str | None
    updated_at: datetime
    class12_marksheet: str | None = None
    id_card: str | None = None

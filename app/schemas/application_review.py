import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.models.enums import ApplicationStatus


class ReviewsPendingResponse:
    application_id: uuid.UUID
    submitted_at: datetime
    status: ApplicationStatus
    validation_flags: int
    validation_issues: List[str]
    updated_at: datetime
    class12_Marksheet: str
    id_card: str

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.models.enums import ApplicationStatus


from pydantic import BaseModel, ConfigDict
from typing import Optional

class ReviewsPendingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: uuid.UUID
    submitted_at: datetime
    status: ApplicationStatus
    validation_flags: Optional[int]
    validation_issues: Optional[str]
    updated_at: datetime
    class12_marksheet: Optional[str] = None
    id_card: Optional[str] = None

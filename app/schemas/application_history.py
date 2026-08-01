import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ApplicationStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    old_status: str
    new_status: str
    changed_by: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True



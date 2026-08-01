import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import DocumentType, ValidationStatus

class DocumentResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    doc_type: DocumentType
    file_path: str
    validation_status: ValidationStatus
    validation_reason: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class DocumentValidationUpdateRequest(BaseModel):
    validation_status: ValidationStatus
    validation_reason: Optional[str] = None

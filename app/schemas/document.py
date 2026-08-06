import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import DocumentType, ValidationStatus, AllowedFileType

class DocumentResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    doc_type: DocumentType
    storage_key: str
    content_type: str
    file_size_bytes: int
    validation_status: ValidationStatus
    validation_reason: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class DocumentValidationUpdateRequest(BaseModel):
    validation_status: ValidationStatus
    validation_reason: Optional[str] = None
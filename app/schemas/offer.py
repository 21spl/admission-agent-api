import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.enums import OfferStatus
from pydantic import BaseModel, Field, field_validator

class OfferResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    branch_id: uuid.UUID
    status: OfferStatus
    sent_at: datetime
    responded_at: Optional[datetime]
    expires_at: datetime

    class Config:
        from_attributes = True

class OfferDecisionRequest(BaseModel):
    status: OfferStatus = Field(..., description="Must explicitly be either ACCEPTED or REJECTED")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: OfferStatus) -> OfferStatus:
        if v not in [OfferStatus.ACCEPTED, OfferStatus.REJECTED]:
            raise ValueError("Direct student decision inputs must be limited to ACCEPTED or REJECTED choices.")
        return v




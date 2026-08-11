import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import OfferStatus


class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    branch_id: uuid.UUID
    round_number: int
    status: OfferStatus
    sent_at: datetime
    responded_at: datetime | None
    expires_at: datetime


class OfferDecisionRequest(BaseModel):
    accept: bool

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.enums import LoanStatus
from pydantic import BaseModel, Field, field_validator

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import LoanStatus

class LoanApplicationCreateRequest(BaseModel):
    income_certificate_doc_id: uuid.UUID = Field(..., description="UUID reference link to the uploaded income certificate document")


class LoanStatusUpdateRequest(BaseModel):
    status: LoanStatus = Field(..., description="Must explicitly transition to either APPROVED or REJECTED")

    @field_validator("status")
    @classmethod
    def validate_decision_status(cls, v: LoanStatus) -> LoanStatus:
        if v not in [LoanStatus.APPROVED, LoanStatus.REJECTED]:
            raise ValueError("Administrative decision states must be explicitly bounded to APPROVED or REJECTED.")
        return v

class LoanApplicationResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    income_certificate_doc_id: uuid.UUID
    status: LoanStatus
    extracted_annual_income: Optional[float]
    decided_at: Optional[datetime]

    class Config:
        from_attributes = True
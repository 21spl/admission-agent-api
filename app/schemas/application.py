import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ApplicationStatus


class PreferenceEntry(BaseModel):
    branch_id: uuid.UUID
    preference_order: int = Field(
        ..., ge=1, le=5, description="Preference ranking from 1 to 5"
    )


class ApplicationCreateRequest(BaseModel):
    total_marks: float = Field(
        ..., ge=0.0, le=100.0, description="Student's normalized academic entry score"
    )
    preferences: list[PreferenceEntry] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Ordered list of branch preferences",
    )

    @field_validator("preferences")
    @classmethod
    def validate_preferences_unique(
        cls, v: list[PreferenceEntry]
    ) -> list[PreferenceEntry]:
        # Validate unique branch references
        branch_ids = [p.branch_id for p in v]
        if len(branch_ids) != len(set(branch_ids)):
            raise ValueError(
                "Duplicate branches are not allowed within preference rankings."
            )

        # Validate consecutive sequence numbers starting from 1
        orders = sorted([p.preference_order for p in v])
        expected_orders = list(range(1, len(v) + 1))
        if orders != expected_orders:
            raise ValueError(
                f"Preference orders must be a continuous sequence starting from 1 to {len(v)}."
            )

        return v


class PreferenceResponse(BaseModel):
    id: uuid.UUID
    branch_id: uuid.UUID
    preference_order: int

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    total_marks: float
    status: ApplicationStatus
    submitted_at: datetime
    updated_at: datetime
    preferences: list[PreferenceResponse]

    class Config:
        from_attributes = True

# app/ai/schemas/doc_validation_schemas.py

from datetime import date
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# -------------------- MARKSHEET -------------------- #

class SubjectMarks(BaseModel):
    physics: float
    chemistry: float
    mathematics: float
    english: float


class Marksheet(BaseModel):
    student_name: str
    passing_year: int = Field(
        ...,
        description="The calendar year of passing, e.g., 2026",
    )
    dob: date
    exam_name: str
    certifying_organization: str

    subject_wise_marks: SubjectMarks

    max_marks: float
    grade: Optional[str] = None

    # Computed fields
    subject_count: Optional[int] = None
    total_marks: Optional[float] = None
    percentage: Optional[float] = None

    @model_validator(mode="after")
    def calculate_metrics(self) -> "Marksheet":
        # Validate max marks
        if self.max_marks <= 0:
            raise ValueError("max_marks must be greater than 0")

        # Validate subject marks
        for subject, marks in [
            ("Physics", self.subject_wise_marks.physics),
            ("Chemistry", self.subject_wise_marks.chemistry),
            ("Mathematics", self.subject_wise_marks.mathematics),
            ("English", self.subject_wise_marks.english),
        ]:
            if marks < 0:
                raise ValueError(f"{subject} marks cannot be negative")

            if marks > self.max_marks:
                raise ValueError(
                    f"{subject} marks cannot exceed max_marks"
                )

        self.subject_count = 4

        self.total_marks = (
            self.subject_wise_marks.physics
            + self.subject_wise_marks.chemistry
            + self.subject_wise_marks.mathematics
            + self.subject_wise_marks.english
        )

        self.percentage = round(
            (self.total_marks / self.max_marks) * 100,
            2,
        )

        return self


# ---------------- GOVERNMENT ID ---------------- #

class GovernmentIDCard(BaseModel):
    id_type: str = Field(
        ...,
        description="Type of ID such as Aadhaar, PAN, Passport or Driving License",
    )

    id_number: str = Field(
        ...,
        description="Unique identification number",
    )

    full_name: str = Field(
        ...,
        description="Full name printed on the card",
    )

    father_name: Optional[str] = Field(
        None,
        description="Father's or Guardian's name",
    )

    dob: date = Field(
        ...,
        description="Date of birth",
    )

    gender: str = Field(
        ...,
        description="Gender mentioned on the ID",
    )

    address: str = Field(
        ...,
        description="Complete residential address",
    )

    @field_validator(
        "id_number",
        "full_name",
        "id_type",
        "address",
        mode="before",
    )
    @classmethod
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "GovernmentIDCard":
        if self.dob >= date.today():
            raise ValueError("Date of birth must be in the past")

        return self
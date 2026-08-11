# app/ai/schemas/doc_validation_schemas.py

from datetime import date, datetime, timezone

from pydantic import (
    BaseModel,
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
    computer_science: float


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
    grade: str | None = None

    # Computed fields
    subject_count: int | None = None
    total_marks: float | None = None
    percentage: float | None = None

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
            ("Computer Science", self.subject_wise_marks.computer_science),
        ]:
            if marks < 0:
                raise ValueError(f"{subject} marks cannot be negative")

            if marks > self.max_marks:
                raise ValueError(f"{subject} marks cannot exceed max_marks")

        self.subject_count = 5

        self.total_marks = (
            self.subject_wise_marks.physics
            + self.subject_wise_marks.chemistry
            + self.subject_wise_marks.mathematics
            + self.subject_wise_marks.english
            + self.subject_wise_marks.computer_science
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

    father_name: str | None = Field(
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
        if self.dob >= datetime.now(tz=timezone.utc).date():
            raise ValueError("Date of birth must be in the past")

        return self

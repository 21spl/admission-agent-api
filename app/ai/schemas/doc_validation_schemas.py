# app/ai/schemas/doc_validation_schemas.py

from datetime import date
from typing import Dict, Optional
from pydantic import BaseModel, Field, model_validator


class Marksheet(BaseModel):
    student_name: str
    passing_year: int = Field(..., description="The calendar year of passing, e.g., 2026")
    dob: date
    exam_name: str
    certifying_organization: str
    subject_wise_marks: Dict[str, float]
    max_marks: float
    grade: Optional[str] = None
    
    # Computed fields (initialized as None, calculated automatically)
    subject_count: Optional[int] = None
    total_marks: Optional[float] = None
    percentage: Optional[float] = None

    @model_validator(mode="after")
    def calculate_metrics(self) -> "Marksheet":
        # Automatically count the number of subjects
        self.subject_count = len(self.subject_wise_marks)
        
        # Automatically sum up the marks
        self.total_marks = sum(self.subject_wise_marks.values())
        
        # Automatically calculate percentage based on maximum possible marks
        if self.max_marks > 0:
            self.percentage = round((self.total_marks / self.max_marks) * 100, 2)
            
        return self
        
        
        
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class GovernmentIDCard(BaseModel):
    # Core Identification
    id_type: str = Field(..., description="Type of ID, e.g., Aadhaar, PAN, Passport, Driving License")
    id_number: str = Field(..., description="Unique identification number")
    
    # Personal Information
    full_name: str = Field(..., description="Full name printed on the card")
    father_name: Optional[str] = Field(None, description="Father's or Guardian's name")
    dob: date = Field(..., description="Date of birth")
    gender: str = Field(..., description="Gender as mentioned on the ID")
    address: str = Field(..., description="Full residential address")
    

    # Clean up whitespace from text inputs automatically
    @field_validator("id_number", "full_name", "id_type", mode="before")
    @classmethod
    def clean_whitespace(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    # Validate logical flow of dates and compute expiration status
    @model_validator(mode="after")
    def validate_dates(self) -> "GovernmentIDCard":

        # Ensure date of birth is in the past
        if self.dob >= date.today():
            raise ValueError("dob (Date of Birth) must be in the past")
    
        return self

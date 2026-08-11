import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

# --- REGISTRATION DATA SCHEMAS (INPUTS) ---


# ================================== STUDENT REGISTER REQUEST SCHEMA =================================================
class StudentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    phone: str | None = Field(None, max_length=20)
    dob: date = Field(
        ..., description="Student's date of birth", examples=["2005-12-31"]
    )


# ====================================== LOGIN REQUEST SCHEMA (INPUT) - For both Student and Officer ==============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ============================ AUTHENTICATION RESPONSE - TOKEN RESPONSE SCHEMA (OUTPUTS) ============================
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ================================== STUDENT PROFILE RESPONSE SCHEMA ===============================================


class StudentProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ================================= OFFICER PROFILE RESPONSE SCHEMA ===================================================


class OfficerProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

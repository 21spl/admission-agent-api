from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid
from datetime import datetime
from app.models.enums import OfficerRole

# --- REGISTRATION DATA SCHEMAS (INPUTS) ---
class StudentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)

class OfficerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)


# --- LOGIN REQUEST SCHEMA (INPUT) ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- AUTHENTICATION RESPONSE SCHEMAS (OUTPUTS) ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class StudentProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class OfficerProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

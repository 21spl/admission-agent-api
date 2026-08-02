import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.config import settings
from app.models.domain import Student, Officer
from app.models.enums import OfficerRole

from fastapi import UploadFile, File, HTTPException, status
from app.models.enums import AllowedFileType
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials



# Replaces OAuth2PasswordBearer — this is just an "expect a Bearer token" marker for Swagger/OpenAPI
bearer_scheme = HTTPBearer()


#============================= HELPER METHODs TO DECODE JWT PAYLOADS FROM TOKENS ==============================================

async def decode_token_payload(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Intercepts, parses, and cryptographically verifies an incoming JWT."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token validation expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid credentials token profile.")

async def get_current_student(payload: dict = Depends(decode_token_payload), db: AsyncSession = Depends(get_db)) -> Student:
    """Guards student-only endpoints, injecting the authenticated entity row."""
    if payload.get("user_type") != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Student account scope required.")
    
    student_id = payload.get("sub")
    result = await db.execute(select(Student).where(Student.id == uuid.UUID(student_id)))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return student

async def get_current_officer(payload: dict = Depends(decode_token_payload), db: AsyncSession = Depends(get_db)) -> Officer:
    """Guards officer-only administrative paths, returning active officer profiles."""
    if payload.get("user_type") != "officer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Officer administrative scope required.")
    
    officer_id = payload.get("sub")
    result = await db.execute(select(Officer).where(Officer.id == uuid.UUID(officer_id)))
    officer = result.scalar_one_or_none()
    
    if not officer:
        raise HTTPException(status_code=404, detail="Administrative record profile not found.")
    return officer





async def validate_uploaded_file_type(file: UploadFile = File(...)) -> AllowedFileType:
    """Validates the uploaded file's declared content type before it reaches the service layer."""
    try:
        return AllowedFileType(file.content_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Only PDF and DOCX are accepted."
        )





#=============================================== CURRENTLY ROLE GUARD IS NOT IN USE ================================================
class RoleGuard:
    """
    Role validation provider wrapper.
    Ensures that an officer has the appropriate privileges before executing a route.
    """
    def __init__(self, allowed_roles: list[OfficerRole]):
        self.allowed_roles = [r.value for r in allowed_roles]

    def __call__(self, current_officer: Officer = Depends(get_current_officer)) -> Officer:
        if current_officer.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Privilege level insufficient to access this secure admin function."
            )
        return current_officer

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.domain import Student, Officer
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import (
    StudentRegisterRequest, OfficerRegisterRequest, 
    LoginRequest, TokenResponse, OfficerCreateByAdminRequest, OfficerProfileResponse
)
from app.models.enums import OfficerRole
from app.core.dependencies import RoleGuard

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/student/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_student(payload: StudentRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new Student account and returns an Access Token."""
    # Check if a user with this email already exists
    existing = await db.execute(select(Student).where(Student.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A student account with this email already exists.")
    
    # Instantiate the mapped entity row securely
    new_student = Student(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        phone=payload.phone
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    
    # Issue a secure JWT context immediately upon registration
    token = create_access_token(user_id=new_student.id, user_type="student")
    return {"access_token": token, "token_type": "bearer"}


@router.post("/student/login", response_model=TokenResponse)
async def login_student(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates student login credentials and returns an Access Token."""
    result = await db.execute(select(Student).where(Student.email == payload.email))
    student = result.scalar_one_or_none()
    
    if not student or not verify_password(payload.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    token = create_access_token(user_id=student.id, user_type="student")
    return {"access_token": token, "token_type": "bearer"}


@router.post("/officer/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_officer(payload: OfficerRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new internal Admission Officer profile (base role only)."""
    existing = await db.execute(select(Officer).where(Officer.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="An officer account with this email already exists.")
    new_officer = Officer(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=OfficerRole.ADMISSION_OFFICER,  # always base role, never from client input
    )
    db.add(new_officer)
    await db.commit()
    await db.refresh(new_officer)
    token = create_access_token(user_id=new_officer.id, user_type="officer")
    return {"access_token": token, "token_type": "bearer"}





@router.post(
    "/officer/create",
    response_model=OfficerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_officer(
    payload: OfficerCreateByAdminRequest,
    db: AsyncSession = Depends(get_db),
    _admin: Officer = Depends(RoleGuard([OfficerRole.ADMIN])),
):
    """Admin-only: provisions a new officer account with any role, including ADMIN."""
    existing = await db.execute(select(Officer).where(Officer.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="An officer account with this email already exists.")
    new_officer = Officer(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_officer)
    await db.commit()
    await db.refresh(new_officer)
    return new_officer


@router.post("/officer/login", response_model=TokenResponse)
async def login_officer(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates administrative staff login credentials."""
    result = await db.execute(select(Officer).where(Officer.email == payload.email))
    officer = result.scalar_one_or_none()
    
    if not officer or not verify_password(payload.password, officer.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    token = create_access_token(user_id=officer.id, user_type="officer")
    return {"access_token": token, "token_type": "bearer"}

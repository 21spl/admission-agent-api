from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.domain import Officer, Student
from app.schemas.auth import (
    LoginRequest,
    StudentRegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==========================================END POINT FOR STUDENT REGISTRATION =====================================================


@router.post(
    "/student/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_student(
    payload: StudentRegisterRequest, db: AsyncSession = Depends(get_db)
):
    """Registers a new Student account and returns an Access Token."""
    # Check if a user with this email already exists
    existing = await db.execute(select(Student).where(Student.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="A student account with this email already exists."
        )

    # ensure date of birth is in the past
    if payload.dob >= datetime.now(tz=timezone.utc).date():
        raise HTTPException(
            status_code=400, detail="Date of birth must be in the past."
        )

    # Instantiate the mapped entity row securely
    new_student = Student(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        phone=payload.phone,
        date_of_birth=payload.dob,
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)

    # Issue a secure JWT context immediately upon registration
    token = create_access_token(user_id=new_student.id, user_type="student")
    return {"access_token": token, "token_type": "bearer"}


# ==========================================END POINT FOR STUDENT LOGIN =====================================================


@router.post("/student/login", response_model=TokenResponse)
async def login_student(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates student login credentials and returns an Access Token."""
    result = await db.execute(select(Student).where(Student.email == payload.email))
    student = result.scalar_one_or_none()

    if not student or not verify_password(payload.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user_id=student.id, user_type="student")
    return {"access_token": token, "token_type": "bearer"}


# ==========================================END POINT FOR OFFICER LOGIN====================================================


@router.post("/officer/login", response_model=TokenResponse)
async def login_officer(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates administrative staff login credentials."""
    result = await db.execute(select(Officer).where(Officer.email == payload.email))
    officer = result.scalar_one_or_none()

    if not officer or not verify_password(payload.password, officer.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user_id=officer.id, user_type="officer")
    return {"access_token": token, "token_type": "bearer"}

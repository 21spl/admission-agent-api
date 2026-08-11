import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.dependencies import (
    decode_token_payload,
    get_current_officer,
    get_current_student,
    validate_uploaded_file_type,
)
from app.models.enums import AllowedFileType, OfficerRole

# ============================================================
# decode_token_payload
# ============================================================


@pytest.mark.asyncio
async def test_decode_token_payload_returns_valid_payload():
    payload = {
        "sub": str(uuid.uuid4()),
        "user_type": "student",
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    credentials = MagicMock()
    credentials.credentials = token

    result = await decode_token_payload(credentials)

    assert result["sub"] == payload["sub"]
    assert result["user_type"] == "student"


@pytest.mark.asyncio
async def test_decode_token_payload_raises_401_for_invalid_token():
    credentials = MagicMock()
    credentials.credentials = "this-is-not-a-valid-jwt"

    with pytest.raises(HTTPException) as exc_info:
        await decode_token_payload(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid credentials token profile."


@pytest.mark.asyncio
async def test_decode_token_payload_raises_401_for_expired_token():
    payload = {
        "sub": str(uuid.uuid4()),
        "user_type": "student",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    credentials = MagicMock()
    credentials.credentials = token

    with pytest.raises(HTTPException) as exc_info:
        await decode_token_payload(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token validation expired."


# ============================================================
# get_current_student
# ============================================================


@pytest.mark.asyncio
async def test_get_current_student_returns_student(
    db_session,
    test_student,
):
    payload = {
        "sub": str(test_student.id),
        "user_type": "student",
    }

    result = await get_current_student(
        payload=payload,
        db=db_session,
    )

    assert result.id == test_student.id
    assert result.email == test_student.email


@pytest.mark.asyncio
async def test_get_current_student_rejects_officer_token(
    db_session,
):
    payload = {
        "sub": str(uuid.uuid4()),
        "user_type": "officer",
    }

    with pytest.raises(HTTPException) as exc_info:
        await get_current_student(
            payload=payload,
            db=db_session,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied. Student account scope required."


@pytest.mark.asyncio
async def test_get_current_student_raises_404_when_student_not_found(
    db_session,
):
    payload = {
        "sub": str(uuid.uuid4()),
        "user_type": "student",
    }

    with pytest.raises(HTTPException) as exc_info:
        await get_current_student(
            payload=payload,
            db=db_session,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Student profile not found."


# ============================================================
# get_current_officer
# ============================================================


@pytest.mark.asyncio
async def test_get_current_officer_returns_officer(
    db_session,
):
    from app.models.domain import Officer

    officer = Officer(
        name="Test Officer",
        email=f"dependency_officer_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="fake-hashed-password",
        role=OfficerRole.ADMIN,
    )

    db_session.add(officer)
    await db_session.flush()

    payload = {
        "sub": str(officer.id),
        "user_type": "officer",
    }

    result = await get_current_officer(
        payload=payload,
        db=db_session,
    )

    assert result.id == officer.id
    assert result.email == officer.email


@pytest.mark.asyncio
async def test_get_current_officer_rejects_student_token(
    db_session,
):
    payload = {
        "sub": str(uuid.uuid4()),
        "user_type": "student",
    }

    with pytest.raises(HTTPException) as exc_info:
        await get_current_officer(
            payload=payload,
            db=db_session,
        )

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail == "Access denied. Officer administrative scope required."
    )


@pytest.mark.asyncio
async def test_get_current_officer_raises_404_when_officer_not_found(
    db_session,
):
    payload = {
        "sub": str(uuid.uuid4()),
        "user_type": "officer",
    }

    with pytest.raises(HTTPException) as exc_info:
        await get_current_officer(
            payload=payload,
            db=db_session,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Administrative record profile not found."


# ============================================================
# validate_uploaded_file_type
# ============================================================


@pytest.mark.asyncio
async def test_validate_uploaded_file_type_accepts_pdf():
    file = MagicMock(spec=UploadFile)
    file.content_type = "application/pdf"

    result = await validate_uploaded_file_type(file)

    assert result == AllowedFileType.PDF


@pytest.mark.asyncio
async def test_validate_uploaded_file_type_accepts_docx():
    file = MagicMock(spec=UploadFile)
    file.content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    result = await validate_uploaded_file_type(file)

    assert result == AllowedFileType.DOCX


@pytest.mark.asyncio
async def test_validate_uploaded_file_type_rejects_unsupported_type():
    file = MagicMock(spec=UploadFile)
    file.content_type = "image/png"

    with pytest.raises(HTTPException) as exc_info:
        await validate_uploaded_file_type(file)

    assert exc_info.value.status_code == 415
    assert "Unsupported file type" in exc_info.value.detail

# tests/test_track_a/test_student_service.py
import uuid
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.core.factories import get_student_service

# ---------------- create_new_student ----------------


@pytest.mark.asyncio
async def test_create_new_student_succeeds_with_valid_data(db_session):
    service = get_student_service(db_session)
    student = await service.create_new_student(
        name="Alice Kumar",
        email=f"alice_{uuid.uuid4().hex[:8]}@example.com",
        password="SecurePass123!",
        phone="9876543210",
        date_of_birth=date(2004, 1, 1),
    )
    assert student.id is not None
    assert student.hashed_password != "SecurePass123!"  # must be hashed, not stored raw


@pytest.mark.asyncio
async def test_create_new_student_allows_optional_phone_none(db_session):
    service = get_student_service(db_session)
    student = await service.create_new_student(
        name="Bob Singh",
        email=f"bob_{uuid.uuid4().hex[:8]}@example.com",
        password="SecurePass123!",
        phone=None,
        date_of_birth=date(2003, 5, 20),
    )
    assert student.phone is None


@pytest.mark.asyncio
async def test_create_new_student_rejects_duplicate_email(db_session, test_student):
    service = get_student_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_new_student(
            name="Duplicate Attempt",
            email=test_student.email,
            password="AnotherPass123!",
            phone=None,
            date_of_birth=date(2004, 3, 3),
        )
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_new_student_rejects_future_date_of_birth(db_session):
    service = get_student_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_new_student(
            name="Time Traveler",
            email=f"future_{uuid.uuid4().hex[:8]}@example.com",
            password="SecurePass123!",
            phone=None,
            date_of_birth=date.today() + timedelta(days=1),
        )
    assert exc_info.value.status_code == 400
    assert "past" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_new_student_rejects_dob_equal_to_today(db_session):
    """Boundary case: `>=` means today itself must also be rejected, not just future dates."""
    service = get_student_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_new_student(
            name="Born Today",
            email=f"today_{uuid.uuid4().hex[:8]}@example.com",
            password="SecurePass123!",
            phone=None,
            date_of_birth=date.today(),
        )
    assert exc_info.value.status_code == 400


# ---------------- get_student_by_id ----------------


@pytest.mark.asyncio
async def test_get_student_by_id_returns_real_student(db_session, test_student):
    service = get_student_service(db_session)
    fetched = await service.get_student_by_id(test_student.id)
    assert fetched is not None
    assert fetched.id == test_student.id


@pytest.mark.asyncio
async def test_get_student_by_id_returns_none_for_unknown_id(db_session):
    """
    NOTE: asserting None here, NOT HTTPException — unlike ApplicationService,
    this repository call has no visible raise in get_student_by_id itself.
    Confirm StudentRepository.get_by_id actually returns None on a miss
    (rather than raising) before trusting this assertion; if it behaves
    like ApplicationRepository.get_with_details instead, this needs
    pytest.raises like the application tests do.
    """
    service = get_student_service(db_session)
    result = await service.get_student_by_id(uuid.uuid4())
    assert result is None


# ---------------- get_student_by_email ----------------


@pytest.mark.asyncio
async def test_get_student_by_email_returns_real_student(db_session, test_student):
    service = get_student_service(db_session)
    fetched = await service.get_student_by_email(test_student.email)
    assert fetched is not None
    assert fetched.email == test_student.email


@pytest.mark.asyncio
async def test_get_student_by_email_returns_none_for_unknown_email(db_session):
    """NOTE: same caveat as above — confirm get_by_email returns None, doesn't raise."""
    service = get_student_service(db_session)
    result = await service.get_student_by_email("definitely_not_registered@example.com")
    assert result is None


# ---------------- get_student_application ----------------


@pytest.mark.asyncio
async def test_get_student_application_returns_application_when_exists(
    db_session, test_student, test_application
):
    """
    test_application fixture creates an application tied to test_student,
    so this should return it via the student.application relationship.
    """
    service = get_student_service(db_session)
    application = await service.get_student_application(test_student.id)
    assert application is not None
    assert application.id == test_application.id


@pytest.mark.asyncio
async def test_get_student_application_raises_404_for_unknown_student_id(db_session):
    """Matches the fixed get_student_application: raises HTTPException(404)
    on an unknown student_id rather than crashing with AttributeError."""
    service = get_student_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.get_student_application(uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_student_application_when_student_has_no_application(
    db_session, test_student
):
    """
    A registered student who hasn't created an application yet — this is
    the exact case your chat router's 'no application yet' short-circuit
    depends on. Confirm this returns None (not an exception) so
    current_student.application_id being None downstream is a safe check,
    matching how the router was designed.
    """
    service = get_student_service(db_session)
    application = await service.get_student_application(test_student.id)
    assert application is None

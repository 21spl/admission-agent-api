import uuid

from datetime import date, timedelta

import pytest

from app.core.security import hash_password
from app.models.domain import Officer
from app.models.enums import OfficerRole


# ============================================================
# Student Registration
# ============================================================

@pytest.mark.asyncio
async def test_register_student_success(client):
    response = await client.post(
        "/auth/student/register",
        json={
            "name": "Test Student",
            "email": "register_test@example.com",
            "password": "TestPassword123!",
            "phone": "9876543210",
            "dob": "2005-06-15",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"]


@pytest.mark.asyncio
async def test_register_student_rejects_duplicate_email(
    client,
):
    payload = {
        "name": "Test Student",
        "email": "duplicate_test@example.com",
        "password": "TestPassword123!",
        "phone": "9876543210",
        "dob": "2005-06-15",
    }

    first_response = await client.post(
        "/auth/student/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/auth/student/register",
        json=payload,
    )

    assert second_response.status_code == 400
    assert (
        second_response.json()["detail"]
        == "A student account with this email already exists."
    )


@pytest.mark.asyncio
async def test_register_student_rejects_future_dob(client):
    future_date = date.today() + timedelta(days=1)

    response = await client.post(
        "/auth/student/register",
        json={
            "name": "Future DOB Student",
            "email": "future_dob@example.com",
            "password": "TestPassword123!",
            "phone": "9876543210",
            "dob": future_date.isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Date of birth must be in the past."


@pytest.mark.asyncio
async def test_register_student_rejects_today_as_dob(client):
    response = await client.post(
        "/auth/student/register",
        json={
            "name": "Today DOB Student",
            "email": "today_dob@example.com",
            "password": "TestPassword123!",
            "phone": "9876543210",
            "dob": date.today().isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Date of birth must be in the past."


@pytest.mark.asyncio
async def test_register_student_rejects_invalid_request(client):
    response = await client.post(
        "/auth/student/register",
        json={
            "name": "Invalid Student",
            "email": "not-an-email",
            "password": "short",
            "dob": "not-a-date",
        },
    )

    assert response.status_code == 422


# ============================================================
# Student Login
# ============================================================

@pytest.mark.asyncio
async def test_login_student_success(
    client,
    test_student,
):
    response = await client.post(
        "/auth/student/login",
        json={
            "email": test_student.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"]


@pytest.mark.asyncio
async def test_login_student_raises_401_for_wrong_password(
    client,
    test_student,
):
    response = await client.post(
        "/auth/student/login",
        json={
            "email": test_student.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_student_raises_401_for_unknown_email(client):
    response = await client.post(
        "/auth/student/login",
        json={
            "email": "does_not_exist@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_student_rejects_invalid_request(client):
    response = await client.post(
        "/auth/student/login",
        json={
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


# ============================================================
# Officer Login
# ============================================================

@pytest.mark.asyncio
async def test_login_officer_success(
    client,
    db_session,
):
    officer = Officer(
        name="Test Officer",
        email="officer_test@example.com",
        hashed_password=hash_password("OfficerPassword123!"),
        role=OfficerRole.ADMIN,
    )

    db_session.add(officer)
    await db_session.flush()

    response = await client.post(
        "/auth/officer/login",
        json={
            "email": officer.email,
            "password": "OfficerPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"]


@pytest.mark.asyncio
async def test_login_officer_raises_401_for_wrong_password(
    client,
    db_session,
):
    officer = Officer(
        name="Test Officer",
        email="officer_wrong_password@example.com",
        hashed_password=hash_password("OfficerPassword123!"),
        role=OfficerRole.ADMIN,
    )

    db_session.add(officer)
    await db_session.flush()

    response = await client.post(
        "/auth/officer/login",
        json={
            "email": officer.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_officer_raises_401_for_unknown_email(client):
    response = await client.post(
        "/auth/officer/login",
        json={
            "email": "unknown_officer@example.com",
            "password": "OfficerPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_officer_rejects_invalid_request(client):
    response = await client.post(
        "/auth/officer/login",
        json={
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422




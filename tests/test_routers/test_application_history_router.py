import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.factories import get_application_history_service
from app.main import app
from app.models.enums import ApplicationStatus

# ============================================================
# Helpers
# ============================================================


async def _get_student_token(client, test_student):
    response = await client.post(
        "/auth/student/login",
        json={
            "email": test_student.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


async def _get_officer_token(client, test_officer):
    response = await client.post(
        "/auth/officer/login",
        json={
            "email": test_officer.email,
            "password": "TestOfficerPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def _override_history_service(service):
    app.dependency_overrides[get_application_history_service] = lambda: service


def _clear_history_service_override():
    app.dependency_overrides.pop(
        get_application_history_service,
        None,
    )


# ============================================================
# GET /applications/history/me
# ============================================================


@pytest.mark.asyncio
async def test_get_my_application_audit_trail_requires_authentication(
    client,
):
    response = await client.get("/applications/history/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_my_application_audit_trail_rejects_invalid_token(
    client,
):
    response = await client.get(
        "/applications/history/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_application_audit_trail_returns_empty_list(
    client,
    test_student,
):
    token = await _get_student_token(
        client,
        test_student,
    )

    history_service = MagicMock()

    history_service.get_history_for_student = AsyncMock(return_value=[])

    _override_history_service(history_service)

    try:
        response = await client.get(
            "/applications/history/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_history_service_override()

    assert response.status_code == 200
    assert response.json() == []

    history_service.get_history_for_student.assert_awaited_once_with(test_student)


@pytest.mark.asyncio
async def test_get_my_application_audit_trail_returns_history(
    client,
    test_student,
):
    token = await _get_student_token(
        client,
        test_student,
    )

    history_id_1 = uuid.uuid4()
    history_id_2 = uuid.uuid4()
    application_id = uuid.uuid4()

    history_1 = MagicMock()
    history_1.id = history_id_1
    history_1.application_id = application_id
    history_1.old_status = ApplicationStatus.STARTED
    history_1.new_status = ApplicationStatus.PENDING_REVIEW
    history_1.changed_by = str(test_student.id)
    history_1.created_at = datetime.now(timezone.utc)

    history_2 = MagicMock()
    history_2.id = history_id_2
    history_2.application_id = application_id
    history_2.old_status = ApplicationStatus.PENDING_REVIEW
    history_2.new_status = ApplicationStatus.OFFER_ACCEPTED
    history_2.changed_by = str(test_student.id)
    history_2.created_at = datetime.now(timezone.utc)

    history_service = MagicMock()

    history_service.get_history_for_student = AsyncMock(
        return_value=[
            history_1,
            history_2,
        ]
    )

    _override_history_service(history_service)

    try:
        response = await client.get(
            "/applications/history/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_history_service_override()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["id"] == str(history_id_1)
    assert data[0]["application_id"] == str(application_id)

    assert data[1]["id"] == str(history_id_2)
    assert data[1]["application_id"] == str(application_id)

    history_service.get_history_for_student.assert_awaited_once_with(test_student)


# ============================================================
# Student endpoint must not accept officer credentials
# ============================================================


@pytest.mark.asyncio
async def test_get_my_application_audit_trail_rejects_officer(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    response = await client.get(
        "/applications/history/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


# ============================================================
# GET /applications/history/application/{application_id}
# ============================================================


@pytest.mark.asyncio
async def test_officer_get_application_audit_trail_requires_authentication(
    client,
):
    application_id = uuid.uuid4()

    response = await client.get(f"/applications/history/application/{application_id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_officer_get_application_audit_trail_rejects_invalid_token(
    client,
):
    application_id = uuid.uuid4()

    response = await client.get(
        f"/applications/history/application/{application_id}",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_officer_get_application_audit_trail_rejects_invalid_uuid(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    response = await client.get(
        "/applications/history/application/not-a-uuid",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_officer_get_application_audit_trail_returns_empty_list(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_id = uuid.uuid4()

    history_service = MagicMock()

    history_service.get_history_for_officer = AsyncMock(return_value=[])

    _override_history_service(history_service)

    try:
        response = await client.get(
            f"/applications/history/application/{application_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_history_service_override()

    assert response.status_code == 200
    assert response.json() == []

    history_service.get_history_for_officer.assert_awaited_once_with(application_id)


@pytest.mark.asyncio
async def test_officer_get_application_audit_trail_returns_history(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_id = uuid.uuid4()

    history_id = uuid.uuid4()

    history = MagicMock()

    history.id = history_id
    history.application_id = application_id
    history.old_status = ApplicationStatus.STARTED
    history.new_status = ApplicationStatus.PENDING_REVIEW
    history.changed_by = str(test_officer.id)
    history.created_at = datetime.now(timezone.utc)

    history_service = MagicMock()

    history_service.get_history_for_officer = AsyncMock(return_value=[history])

    _override_history_service(history_service)

    try:
        response = await client.get(
            f"/applications/history/application/{application_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_history_service_override()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(history_id)
    assert data[0]["application_id"] == str(application_id)

    history_service.get_history_for_officer.assert_awaited_once_with(application_id)


# ============================================================
# Officer endpoint must reject student credentials
# ============================================================


@pytest.mark.asyncio
async def test_officer_get_application_audit_trail_rejects_student(
    client,
    test_student,
):
    token = await _get_student_token(
        client,
        test_student,
    )

    application_id = uuid.uuid4()

    response = await client.get(
        f"/applications/history/application/{application_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403

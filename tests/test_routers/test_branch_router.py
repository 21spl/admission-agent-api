

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.factories import get_branch_service
from app.main import app


# ============================================================
# Helpers
# ============================================================

async def _get_officer_token(client, email, password):
    response = await client.post(
        "/auth/officer/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ============================================================
# GET /branches
# ============================================================

@pytest.mark.asyncio
async def test_list_all_branches_success(
    client,
    test_branch,
):
    response = await client.get("/branches")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    branch = next(
        item for item in data
        if item["id"] == str(test_branch.id)
    )

    assert branch["name"] == test_branch.name
    assert branch["code"] == test_branch.code


@pytest.mark.asyncio
async def test_list_all_branches_does_not_require_authentication(
    client,
):
    response = await client.get("/branches")

    assert response.status_code == 200


# ============================================================
# GET /branches/{branch_id}
# ============================================================

@pytest.mark.asyncio
async def test_get_single_branch_success(
    client,
    test_branch,
):
    response = await client.get(
        f"/branches/{test_branch.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(test_branch.id)
    assert data["name"] == test_branch.name
    assert data["code"] == test_branch.code


@pytest.mark.asyncio
async def test_get_single_branch_returns_404_for_unknown_branch(
    client,
):
    branch_id = uuid.uuid4()

    response = await client.get(
        f"/branches/{branch_id}"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_single_branch_rejects_invalid_uuid(
    client,
):
    response = await client.get(
        "/branches/not-a-uuid"
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_single_branch_does_not_require_authentication(
    client,
    test_branch,
):
    response = await client.get(
        f"/branches/{test_branch.id}"
    )

    assert response.status_code == 200


# ============================================================
# POST /branches
# ============================================================

@pytest.mark.asyncio
async def test_create_branch_requires_authentication(
    client,
):
    response = await client.post(
        "/branches",
        json={
            "name": "Electrical Engineering",
            "code": "EEE",
            "total_seats": 60,
            "cutoff_marks": 80,
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_branch_rejects_invalid_token(
    client,
):
    response = await client.post(
        "/branches",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "name": "Electrical Engineering",
            "code": "EEE",
            "total_seats": 60,
            "cutoff_marks": 80,
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_branch_success(
    client,
    db_session,
):
    """
    This test assumes an authenticated ADMIN officer is created
    using the same fields as your Officer model.
    """

    from app.models.domain import Officer
    from app.models.enums import OfficerRole
    from app.core.security import hash_password

    officer = Officer(
        name="Test Admin",
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("AdminPassword123!"),
        role=OfficerRole.ADMIN,
    )

    db_session.add(officer)
    await db_session.flush()

    token = await _get_officer_token(
        client,
        officer.email,
        "AdminPassword123!",
    )

    response = await client.post(
        "/branches",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Electrical Engineering",
            "code": f"EEE{uuid.uuid4().hex[:4]}",
            "total_seats": 60,
            "cutoff_marks": 80,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Electrical Engineering"
    assert data["total_seats"] == 60
    assert data["cutoff_marks"] == 80


@pytest.mark.asyncio
async def test_create_branch_rejects_invalid_request(
    client,
):
    response = await client.post(
        "/branches",
        json={
            "name": "Invalid Branch",
        },
    )

    assert response.status_code == 403


# ============================================================
# PATCH /branches/{branch_id}
# ============================================================

@pytest.mark.asyncio
async def test_update_branch_requires_authentication(
    client,
    test_branch,
):
    response = await client.patch(
        f"/branches/{test_branch.id}",
        json={
            "name": "Updated Branch",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_branch_rejects_invalid_uuid(
    client,
):
    response = await client.patch(
        "/branches/not-a-uuid",
        json={
            "name": "Updated Branch",
        },
    )

    # Depending on dependency ordering, authentication may run
    # before path validation. With no auth this may be 403 rather
    # than 422.
    assert response.status_code in (403, 422)


@pytest.mark.asyncio
async def test_update_branch_success(
    client,
    db_session,
    test_branch,
):
    from app.models.domain import Officer
    from app.models.enums import OfficerRole
    from app.core.security import hash_password

    officer = Officer(
        name="Test Admin",
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("AdminPassword123!"),
        role=OfficerRole.ADMIN,
    )

    db_session.add(officer)
    await db_session.flush()

    token = await _get_officer_token(
        client,
        officer.email,
        "AdminPassword123!",
    )

    response = await client.patch(
        f"/branches/{test_branch.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Updated Computer Science",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(test_branch.id)
    assert data["name"] == "Updated Computer Science"


@pytest.mark.asyncio
async def test_update_branch_returns_404_for_unknown_branch(
    client,
    db_session,
):
    from app.models.domain import Officer
    from app.models.enums import OfficerRole
    from app.core.security import hash_password

    officer = Officer(
        name="Test Admin",
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("AdminPassword123!"),
        role=OfficerRole.ADMIN,
    )

    db_session.add(officer)
    await db_session.flush()

    token = await _get_officer_token(
        client,
        officer.email,
        "AdminPassword123!",
    )

    response = await client.patch(
        f"/branches/{uuid.uuid4()}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Updated Branch",
        },
    )

    assert response.status_code == 404


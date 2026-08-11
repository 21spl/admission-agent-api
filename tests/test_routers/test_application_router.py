import pytest

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


# ============================================================
# POST /applications
# ============================================================


@pytest.mark.asyncio
async def test_submit_application_success(
    client,
    test_student,
    test_branch,
):
    token = await _get_student_token(client, test_student)

    response = await client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "total_marks": 87,
            "preferences": [
                {
                    "branch_id": str(test_branch.id),
                    "preference_order": 1,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["student_id"] == str(test_student.id)
    assert data["total_marks"] == 87


@pytest.mark.asyncio
async def test_submit_application_requires_authentication(
    client,
    test_branch,
):
    response = await client.post(
        "/applications",
        json={
            "total_marks": 87,
            "preferences": [
                {
                    "branch_id": str(test_branch.id),
                    "preference_order": 1,
                }
            ],
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_submit_application_rejects_invalid_token(
    client,
    test_branch,
):
    response = await client.post(
        "/applications",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "total_marks": 87,
            "preferences": [
                {
                    "branch_id": str(test_branch.id),
                    "preference_order": 1,
                }
            ],
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_submit_application_rejects_invalid_request(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    response = await client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "total_marks": 87,
            # preferences intentionally missing
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_application_rejects_student_token_for_invalid_body(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    response = await client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "total_marks": "not-a-number",
            "preferences": [],
        },
    )

    assert response.status_code == 422


# ============================================================
# GET /applications/me
# ============================================================


@pytest.mark.asyncio
async def test_get_my_application_returns_application(
    client,
    test_student,
    test_application,
):
    token = await _get_student_token(client, test_student)

    response = await client.get(
        "/applications/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(test_application.id)
    assert data["student_id"] == str(test_student.id)
    assert data["total_marks"] == test_application.total_marks


@pytest.mark.asyncio
async def test_get_my_application_requires_authentication(
    client,
):
    response = await client.get(
        "/applications/me",
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_my_application_rejects_invalid_token(
    client,
):
    response = await client.get(
        "/applications/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401

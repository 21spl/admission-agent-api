
import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException

from app.core.factories import get_shortlisting_service
from app.main import app


# ============================================================
# Helpers
# ============================================================

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


# ============================================================
# POST /admin/rounds/{round_number}/shortlist
# ============================================================

@pytest.mark.asyncio
async def test_trigger_shortlisting_round_requires_authentication(
    client,
):
    response = await client.post(
        "/admin/rounds/1/shortlist",
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_trigger_shortlisting_round_rejects_invalid_token(
    client,
):
    response = await client.post(
        "/admin/rounds/1/shortlist",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_trigger_shortlisting_round_rejects_invalid_round_number(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    response = await client.post(
        "/admin/rounds/not-a-number/shortlist",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_trigger_shortlisting_round_success(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    shortlisting_service = MagicMock()

    shortlisting_service.run_shortlisting_round = AsyncMock(
        return_value={
            "round_number": 1,
            "status": "completed",
            "offers_created": 25,
        }
    )

    app.dependency_overrides[
        get_shortlisting_service
    ] = lambda: shortlisting_service

    try:
        response = await client.post(
            "/admin/rounds/1/shortlist",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_shortlisting_service,
            None,
        )

    assert response.status_code == 200

    assert response.json() == {
        "round_number": 1,
        "status": "completed",
        "offers_created": 25,
    }

    shortlisting_service.run_shortlisting_round.assert_awaited_once_with(
        1
    )


@pytest.mark.asyncio
async def test_trigger_shortlisting_round_passes_round_number_to_service(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    shortlisting_service = MagicMock()

    shortlisting_service.run_shortlisting_round = AsyncMock(
        return_value={
            "round_number": 3,
            "status": "completed",
        }
    )

    app.dependency_overrides[
        get_shortlisting_service
    ] = lambda: shortlisting_service

    try:
        response = await client.post(
            "/admin/rounds/3/shortlist",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_shortlisting_service,
            None,
        )

    assert response.status_code == 200

    shortlisting_service.run_shortlisting_round.assert_awaited_once_with(
        3
    )


@pytest.mark.asyncio
async def test_trigger_shortlisting_round_converts_value_error_to_400(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    shortlisting_service = MagicMock()

    shortlisting_service.run_shortlisting_round = AsyncMock(
        side_effect=ValueError(
            "Shortlisting round 1 has already been completed."
        )
    )

    app.dependency_overrides[
        get_shortlisting_service
    ] = lambda: shortlisting_service

    try:
        response = await client.post(
            "/admin/rounds/1/shortlist",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_shortlisting_service,
            None,
        )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Shortlisting round 1 has already been completed."
    )

    shortlisting_service.run_shortlisting_round.assert_awaited_once_with(
        1
    )


@pytest.mark.asyncio
async def test_trigger_shortlisting_round_propagates_unhandled_exception(
    client,
    test_officer,
):
    """
    The router only catches ValueError.
    Other exceptions should not be silently converted to 400.
    """

    token = await _get_officer_token(
        client,
        test_officer,
    )

    shortlisting_service = MagicMock()

    shortlisting_service.run_shortlisting_round = AsyncMock(
        side_effect=RuntimeError("Database failure")
    )

    app.dependency_overrides[
        get_shortlisting_service
    ] = lambda: shortlisting_service

    try:
        with pytest.raises(RuntimeError, match="Database failure"):
            await client.post(
                "/admin/rounds/1/shortlist",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )
    finally:
        app.dependency_overrides.pop(
            get_shortlisting_service,
            None,
        )


# ============================================================
# Boundary / path parameter checks
# ============================================================

@pytest.mark.asyncio
async def test_trigger_shortlisting_round_accepts_zero_as_integer(
    client,
    test_officer,
):
    """
    This test documents the current router behavior:
    round_number is only typed as int, so zero is accepted by FastAPI.
    
    If your business rule says rounds must be 1, 2, or 3,
    enforce that in the route/service and change this test.
    """

    token = await _get_officer_token(
        client,
        test_officer,
    )

    shortlisting_service = MagicMock()

    shortlisting_service.run_shortlisting_round = AsyncMock(
        return_value={
            "round_number": 0,
            "status": "completed",
        }
    )

    app.dependency_overrides[
        get_shortlisting_service
    ] = lambda: shortlisting_service

    try:
        response = await client.post(
            "/admin/rounds/0/shortlist",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_shortlisting_service,
            None,
        )

    assert response.status_code == 200

    shortlisting_service.run_shortlisting_round.assert_awaited_once_with(
        0
    )


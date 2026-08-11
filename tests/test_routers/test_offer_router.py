import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.factories import get_offer_service
from app.main import app
from app.models.enums import OfferStatus

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


# ============================================================
# GET /offers/me
# ============================================================


@pytest.mark.asyncio
async def test_get_my_offers_returns_empty_list_when_student_has_no_offers(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    response = await client.get(
        "/offers/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_my_offers_requires_authentication(client):
    response = await client.get("/offers/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_my_offers_rejects_invalid_token(client):
    response = await client.get(
        "/offers/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


# ============================================================
# PATCH /offers/{offer_id}/respond
# ============================================================


@pytest.mark.asyncio
async def test_respond_to_offer_requires_authentication(
    client,
):
    offer_id = uuid.uuid4()

    response = await client.patch(
        f"/offers/{offer_id}/respond",
        json={
            "accept": True,
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_respond_to_offer_rejects_invalid_token(
    client,
):
    offer_id = uuid.uuid4()

    response = await client.patch(
        f"/offers/{offer_id}/respond",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "accept": True,
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_respond_to_offer_rejects_invalid_offer_id(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    response = await client.patch(
        "/offers/not-a-uuid/respond",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "accept": True,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_respond_to_offer_rejects_invalid_request_body(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    response = await client.patch(
        f"/offers/{uuid.uuid4()}/respond",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_respond_to_offer_propagates_service_404(
    client,
    test_student,
):
    """
    Router-level test:
    the service says the offer doesn't exist,
    so FastAPI should return 404.
    """

    token = await _get_student_token(client, test_student)

    service = AsyncMock()

    service.process_student_decision = AsyncMock(
        side_effect=HTTPException(
            status_code=404,
            detail="Offer not found.",
        )
    )

    app.dependency_overrides[get_offer_service] = lambda: service

    try:
        offer_id = uuid.uuid4()

        response = await client.patch(
            f"/offers/{offer_id}/respond",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "accept": True,
            },
        )

    finally:
        app.dependency_overrides.pop(
            get_offer_service,
            None,
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Offer not found."

    service.process_student_decision.assert_awaited_once()

    call_kwargs = service.process_student_decision.await_args.kwargs

    assert call_kwargs["student"].id == test_student.id
    assert call_kwargs["offer_id"] == offer_id


@pytest.mark.asyncio
async def test_respond_to_offer_propagates_service_409(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    service = AsyncMock()

    service.process_student_decision = AsyncMock(
        side_effect=HTTPException(
            status_code=409,
            detail="Offer already resolved.",
        )
    )

    app.dependency_overrides[get_offer_service] = lambda: service

    try:
        response = await client.patch(
            f"/offers/{uuid.uuid4()}/respond",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "accept": True,
            },
        )

    finally:
        app.dependency_overrides.pop(
            get_offer_service,
            None,
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Offer already resolved."


# ============================================================
# GET /offers/application/{application_id}
# ============================================================


@pytest.mark.asyncio
async def test_get_offers_by_application_returns_empty_list(
    client,
    test_officer,
    test_application,
):
    token = await _get_officer_token(client, test_officer)

    response = await client.get(
        f"/offers/application/{test_application.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_offers_by_application_requires_authentication(
    client,
    test_application,
):
    response = await client.get(
        f"/offers/application/{test_application.id}",
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_offers_by_application_rejects_invalid_token(
    client,
    test_application,
):
    response = await client.get(
        f"/offers/application/{test_application.id}",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_offers_by_application_rejects_invalid_application_id(
    client,
    test_officer,
):
    token = await _get_officer_token(client, test_officer)

    response = await client.get(
        "/offers/application/not-a-uuid",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


# ============================================================
# Successful GET /offers/me
# ============================================================


@pytest.mark.asyncio
async def test_get_my_offers_returns_offers(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    offer = {
        "id": uuid.uuid4(),
        "application_id": uuid.uuid4(),
        "branch_id": uuid.uuid4(),
        "round_number": 1,
        "status": OfferStatus.PENDING,
        "sent_at": datetime.now(timezone.utc),
        "responded_at": None,
        "expires_at": datetime.now(timezone.utc),
    }

    service = AsyncMock()

    service.list_my_offers = AsyncMock(return_value=[offer])

    app.dependency_overrides[get_offer_service] = lambda: service

    try:
        response = await client.get(
            "/offers/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    finally:
        app.dependency_overrides.pop(
            get_offer_service,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(offer["id"])
    assert data[0]["application_id"] == str(offer["application_id"])
    assert data[0]["branch_id"] == str(offer["branch_id"])
    assert data[0]["round_number"] == 1
    assert data[0]["status"] == OfferStatus.PENDING.value
    assert data[0]["responded_at"] is None

    service.list_my_offers.assert_awaited_once()

    student_arg = service.list_my_offers.await_args.args[0]

    assert student_arg.id == test_student.id


# ============================================================
# Successful PATCH /offers/{offer_id}/respond
# ============================================================


@pytest.mark.asyncio
async def test_accept_offer_success(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    offer_id = uuid.uuid4()
    application_id = uuid.uuid4()
    branch_id = uuid.uuid4()

    now = datetime.now(timezone.utc)

    offer = {
        "id": offer_id,
        "application_id": application_id,
        "branch_id": branch_id,
        "round_number": 1,
        "status": OfferStatus.ACCEPTED,
        "sent_at": now,
        "responded_at": now,
        "expires_at": now,
    }

    service = AsyncMock()

    service.process_student_decision = AsyncMock(return_value=offer)

    app.dependency_overrides[get_offer_service] = lambda: service

    try:
        response = await client.patch(
            f"/offers/{offer_id}/respond",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "accept": True,
            },
        )

    finally:
        app.dependency_overrides.pop(
            get_offer_service,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(offer_id)
    assert data["application_id"] == str(application_id)
    assert data["branch_id"] == str(branch_id)
    assert data["round_number"] == 1
    assert data["status"] == OfferStatus.ACCEPTED.value

    service.process_student_decision.assert_awaited_once()

    call_kwargs = service.process_student_decision.await_args.kwargs

    assert call_kwargs["student"].id == test_student.id
    assert call_kwargs["offer_id"] == offer_id

    assert call_kwargs["data"].accept is True


@pytest.mark.asyncio
async def test_reject_offer_success(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    offer_id = uuid.uuid4()
    application_id = uuid.uuid4()
    branch_id = uuid.uuid4()

    sent_at = datetime.now(timezone.utc)
    responded_at = datetime.now(timezone.utc)
    expires_at = datetime.now(timezone.utc)

    offer = {
        "id": offer_id,
        "application_id": application_id,
        "branch_id": branch_id,
        "round_number": 1,
        "status": OfferStatus.REJECTED,
        "sent_at": sent_at,
        "responded_at": responded_at,
        "expires_at": expires_at,
    }

    service = AsyncMock()

    service.process_student_decision = AsyncMock(return_value=offer)

    app.dependency_overrides[get_offer_service] = lambda: service

    try:
        response = await client.patch(
            f"/offers/{offer_id}/respond",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "accept": False,
            },
        )

    finally:
        app.dependency_overrides.pop(
            get_offer_service,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(offer_id)
    assert data["application_id"] == str(application_id)
    assert data["branch_id"] == str(branch_id)
    assert data["round_number"] == 1
    assert data["status"] == OfferStatus.REJECTED.value

    service.process_student_decision.assert_awaited_once()

    call_kwargs = service.process_student_decision.await_args.kwargs

    assert call_kwargs["student"].id == test_student.id
    assert call_kwargs["offer_id"] == offer_id
    assert call_kwargs["data"].accept is False


# ============================================================
# Successful GET /offers/application/{application_id}
# ============================================================


@pytest.mark.asyncio
async def test_get_offers_by_application_returns_offers(
    client,
    test_officer,
    test_application,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    offer = {
        "id": uuid.uuid4(),
        "application_id": test_application.id,
        "branch_id": uuid.uuid4(),
        "round_number": 1,
        "status": OfferStatus.PENDING,
        "sent_at": datetime.now(timezone.utc),
        "responded_at": None,
        "expires_at": datetime.now(timezone.utc),
    }

    service = AsyncMock()

    service.list_offers_for_application = AsyncMock(return_value=[offer])

    app.dependency_overrides[get_offer_service] = lambda: service

    try:
        response = await client.get(
            f"/offers/application/{test_application.id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    finally:
        app.dependency_overrides.pop(
            get_offer_service,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(offer["id"])
    assert data[0]["application_id"] == str(test_application.id)
    assert data[0]["branch_id"] == str(offer["branch_id"])
    assert data[0]["round_number"] == 1
    assert data[0]["status"] == OfferStatus.PENDING.value
    assert data[0]["responded_at"] is None

    service.list_offers_for_application.assert_awaited_once_with(test_application.id)

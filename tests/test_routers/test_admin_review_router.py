
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.factories import (
    get_admin_review_service,
    get_application_repository,
    get_document_service,
)
from app.main import app
from app.models.enums import ApplicationStatus, DocumentType


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


def _override_dependency(dependency, value):
    app.dependency_overrides[dependency] = lambda: value


def _clear_dependency_overrides(*dependencies):
    for dependency in dependencies:
        app.dependency_overrides.pop(dependency, None)


# ============================================================
# GET /admin/document-reviews/
# ============================================================

@pytest.mark.asyncio
async def test_list_pending_reviews_requires_authentication(
    client,
):
    response = await client.get(
        "/admin/document-reviews/"
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_pending_reviews_rejects_invalid_token(
    client,
):
    response = await client.get(
        "/admin/document-reviews/",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_pending_reviews_returns_empty_list(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_repository = MagicMock()
    application_repository.list_by_status = AsyncMock(
        return_value=[]
    )

    document_service = MagicMock()

    _override_dependency(
        get_application_repository,
        application_repository,
    )
    _override_dependency(
        get_document_service,
        document_service,
    )

    try:
        response = await client.get(
            "/admin/document-reviews/",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
            get_document_service,
        )

    assert response.status_code == 200
    assert response.json() == []

    application_repository.list_by_status.assert_awaited_once_with(
        ApplicationStatus.PENDING_REVIEW
    )


@pytest.mark.asyncio
async def test_list_pending_reviews_returns_application_with_document_links(
    client,
    test_officer,
    test_application,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    # --------------------------------------------------------
    # Create fake application/document objects.
    # We don't need to insert them into the database because
    # this is a router test.
    # --------------------------------------------------------

    marksheet_doc = MagicMock()
    marksheet_doc.id = uuid.uuid4()
    marksheet_doc.doc_type = DocumentType.CLASS12_MARKSHEET

    id_card_doc = MagicMock()
    id_card_doc.id = uuid.uuid4()
    id_card_doc.doc_type = DocumentType.ID_CARD

    application = MagicMock()

    application.id = test_application.id
    application.submitted_at = datetime.now(timezone.utc)
    application.status = ApplicationStatus.PENDING_REVIEW

    # These must match ReviewsPendingResponse:
    # validation_flags: Optional[int]
    # validation_issues: Optional[str]
    application.validation_flags = 0
    application.validation_issues = None

    application.updated_at = datetime.now(timezone.utc)

    application.documents = [
        marksheet_doc,
        id_card_doc,
    ]

    # --------------------------------------------------------
    # Mock dependencies
    # --------------------------------------------------------

    application_repository = MagicMock()

    application_repository.list_by_status = AsyncMock(
        return_value=[application]
    )

    document_service = MagicMock()

    document_service.get_download_link = AsyncMock(
        side_effect=[
            "https://storage.test/marksheet.pdf",
            "https://storage.test/id-card.pdf",
        ]
    )

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    _override_dependency(
        get_document_service,
        document_service,
    )

    try:
        response = await client.get(
            "/admin/document-reviews/",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
            get_document_service,
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    review = data[0]

    assert review["application_id"] == str(test_application.id)
    assert review["status"] == ApplicationStatus.PENDING_REVIEW.value

    assert review["validation_flags"] == 0
    assert review["validation_issues"] is None

    assert review["class12_marksheet"] == (
        "https://storage.test/marksheet.pdf"
    )

    assert review["id_card"] == (
        "https://storage.test/id-card.pdf"
    )

    application_repository.list_by_status.assert_awaited_once_with(
        ApplicationStatus.PENDING_REVIEW
    )

    assert document_service.get_download_link.await_count == 2

    document_service.get_download_link.assert_any_await(
        marksheet_doc.id
    )

    document_service.get_download_link.assert_any_await(
        id_card_doc.id
    )


@pytest.mark.asyncio
async def test_list_pending_reviews_handles_missing_documents(
    client,
    test_officer,
    test_application,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    # Application has no documents.
    application = MagicMock()

    application.id = test_application.id
    application.submitted_at = datetime.now(timezone.utc)
    application.status = ApplicationStatus.PENDING_REVIEW

    # Must match ReviewsPendingResponse types.
    application.validation_flags = 0
    application.validation_issues = None

    application.updated_at = datetime.now(timezone.utc)

    application.documents = []

    application_repository = MagicMock()

    application_repository.list_by_status = AsyncMock(
        return_value=[application]
    )

    document_service = MagicMock()

    document_service.get_download_link = AsyncMock()

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    _override_dependency(
        get_document_service,
        document_service,
    )

    try:
        response = await client.get(
            "/admin/document-reviews/",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
            get_document_service,
        )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    review = data[0]

    assert review["validation_flags"] == 0
    assert review["validation_issues"] is None

    assert review["class12_marksheet"] is None
    assert review["id_card"] is None

    document_service.get_download_link.assert_not_awaited()


# ============================================================
# POST /admin/document-reviews/{application_id}/decision
# ============================================================

@pytest.mark.asyncio
async def test_submit_review_decision_requires_authentication(
    client,
    test_application,
):
    response = await client.post(
        f"/admin/document-reviews/{test_application.id}/decision",
        json={
            "approve": True,
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_submit_review_decision_rejects_invalid_token(
    client,
    test_application,
):
    response = await client.post(
        f"/admin/document-reviews/{test_application.id}/decision",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        json={
            "approve": True,
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_submit_review_decision_rejects_invalid_application_id(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    response = await client.post(
        "/admin/document-reviews/not-a-uuid/decision",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "approve": True,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_review_decision_rejects_invalid_request_body(
    client,
    test_officer,
    test_application,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    response = await client.post(
        f"/admin/document-reviews/{test_application.id}/decision",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_review_decision_returns_404_when_application_not_found(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_repository = MagicMock()

    application_repository.get_by_id = AsyncMock(
        return_value=None
    )

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    try:
        application_id = uuid.uuid4()

        response = await client.post(
            f"/admin/document-reviews/{application_id}/decision",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "approve": True,
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
        )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "No pending review found for this application."
    )

    application_repository.get_by_id.assert_awaited_once_with(
        application_id
    )


@pytest.mark.asyncio
async def test_submit_review_decision_returns_404_when_application_not_pending(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application = MagicMock()

    application.id = uuid.uuid4()
    application.status = ApplicationStatus.STARTED

    application_repository = MagicMock()

    application_repository.get_by_id = AsyncMock(
        return_value=application
    )

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    try:
        response = await client.post(
            f"/admin/document-reviews/{application.id}/decision",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "approve": True,
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
        )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "No pending review found for this application."
    )


# ============================================================
# APPROVE
# ============================================================

@pytest.mark.asyncio
async def test_submit_review_decision_approve_success(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_id = uuid.uuid4()

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.PENDING_REVIEW

    application_repository = MagicMock()

    application_repository.get_by_id = AsyncMock(
        return_value=application
    )

    admin_review_service = MagicMock()

    admin_review_service.validate_application_manually = AsyncMock()

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    _override_dependency(
        get_admin_review_service,
        admin_review_service,
    )

    try:
        response = await client.post(
            f"/admin/document-reviews/{application_id}/decision",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "approve": True,
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
            get_admin_review_service,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "resolved"
    assert data["application_id"] == str(application_id)

    application_repository.get_by_id.assert_awaited_once_with(
        application_id
    )

    admin_review_service.validate_application_manually.assert_awaited_once_with(
        application_id
    )


# ============================================================
# REJECT
# ============================================================

@pytest.mark.asyncio
async def test_submit_review_decision_reject_success(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_id = uuid.uuid4()

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.PENDING_REVIEW

    application_repository = MagicMock()

    application_repository.get_by_id = AsyncMock(
        return_value=application
    )

    admin_review_service = MagicMock()

    admin_review_service.reject_application_manually = AsyncMock()

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    _override_dependency(
        get_admin_review_service,
        admin_review_service,
    )

    try:
        response = await client.post(
            f"/admin/document-reviews/{application_id}/decision",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "approve": False,
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
            get_admin_review_service,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "resolved"
    assert data["application_id"] == str(application_id)

    application_repository.get_by_id.assert_awaited_once_with(
        application_id
    )

    admin_review_service.reject_application_manually.assert_awaited_once_with(
        application_id
    )


# ============================================================
# APPROVE / REJECT MUST NOT CALL THE OTHER PATH
# ============================================================

@pytest.mark.asyncio
async def test_approve_decision_does_not_call_reject(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_id = uuid.uuid4()

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.PENDING_REVIEW

    application_repository = MagicMock()

    application_repository.get_by_id = AsyncMock(
        return_value=application
    )

    admin_review_service = MagicMock()

    admin_review_service.validate_application_manually = AsyncMock()
    admin_review_service.reject_application_manually = AsyncMock()

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    _override_dependency(
        get_admin_review_service,
        admin_review_service,
    )

    try:
        response = await client.post(
            f"/admin/document-reviews/{application_id}/decision",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "approve": True,
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
            get_admin_review_service,
        )

    assert response.status_code == 200

    admin_review_service.validate_application_manually.assert_awaited_once_with(
        application_id
    )

    admin_review_service.reject_application_manually.assert_not_awaited()


@pytest.mark.asyncio
async def test_reject_decision_does_not_call_approve(
    client,
    test_officer,
):
    token = await _get_officer_token(
        client,
        test_officer,
    )

    application_id = uuid.uuid4()

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.PENDING_REVIEW

    application_repository = MagicMock()

    application_repository.get_by_id = AsyncMock(
        return_value=application
    )

    admin_review_service = MagicMock()

    admin_review_service.validate_application_manually = AsyncMock()
    admin_review_service.reject_application_manually = AsyncMock()

    _override_dependency(
        get_application_repository,
        application_repository,
    )

    _override_dependency(
        get_admin_review_service,
        admin_review_service,
    )

    try:
        response = await client.post(
            f"/admin/document-reviews/{application_id}/decision",
            headers={
                "Authorization": f"Bearer {token}",
            },
            json={
                "approve": False,
            },
        )
    finally:
        _clear_dependency_overrides(
            get_application_repository,
            get_admin_review_service,
        )

    assert response.status_code == 200

    admin_review_service.reject_application_manually.assert_awaited_once_with(
        application_id
    )

    admin_review_service.validate_application_manually.assert_not_awaited()


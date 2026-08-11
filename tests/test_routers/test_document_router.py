

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.dependencies import (
    get_current_student,
    validate_uploaded_file_type,
)
from app.core.factories import (
    get_document_service,
    get_application_repository,
    get_student_repository,
)
from app.models.enums import DocumentType
from app.main import app


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


def _override_document_service(service_mock):
    app.dependency_overrides[get_document_service] = lambda: service_mock


def _clear_document_service_override():
    app.dependency_overrides.pop(get_document_service, None)


# ============================================================
# POST /documents/upload
# ============================================================

@pytest.mark.asyncio
async def test_upload_document_success(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    service = MagicMock()
    service.upload_document_metadata = AsyncMock(
        return_value=MagicMock(
            id=uuid.uuid4(),
            document_type=next(iter(DocumentType)),
            filename="marksheet.pdf",
        )
    )

    _override_document_service(service)

    try:
        doc_type = next(iter(DocumentType)).value

        response = await client.post(
            "/documents/upload",
            headers={
                "Authorization": f"Bearer {token}",
            },
            data={
                "doc_type": doc_type,
            },
            files={
                "file": (
                    "marksheet.pdf",
                    b"fake pdf content",
                    "application/pdf",
                ),
            },
        )

    finally:
        _clear_document_service_override()

    assert response.status_code == 201

    service.upload_document_metadata.assert_awaited_once()

    call_kwargs = service.upload_document_metadata.await_args.kwargs

    assert call_kwargs["student"].id == test_student.id
    assert call_kwargs["filename"] == "marksheet.pdf"
    assert call_kwargs["file_bytes"] == b"fake pdf content"


@pytest.mark.asyncio
async def test_upload_document_requires_authentication(
    client,
):
    doc_type = next(iter(DocumentType)).value

    response = await client.post(
        "/documents/upload",
        data={
            "doc_type": doc_type,
        },
        files={
            "file": (
                "marksheet.pdf",
                b"fake pdf content",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_document_rejects_invalid_token(
    client,
):
    doc_type = next(iter(DocumentType)).value

    response = await client.post(
        "/documents/upload",
        headers={
            "Authorization": "Bearer invalid-token",
        },
        data={
            "doc_type": doc_type,
        },
        files={
            "file": (
                "marksheet.pdf",
                b"fake pdf content",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_document_rejects_unsupported_file_type(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    doc_type = next(iter(DocumentType)).value

    response = await client.post(
        "/documents/upload",
        headers={
            "Authorization": f"Bearer {token}",
        },
        data={
            "doc_type": doc_type,
        },
        files={
            "file": (
                "photo.png",
                b"fake image content",
                "image/png",
            ),
        },
    )

    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_document_rejects_missing_file(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    doc_type = next(iter(DocumentType)).value

    response = await client.post(
        "/documents/upload",
        headers={
            "Authorization": f"Bearer {token}",
        },
        data={
            "doc_type": doc_type,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_document_rejects_missing_document_type(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    response = await client.post(
        "/documents/upload",
        headers={
            "Authorization": f"Bearer {token}",
        },
        files={
            "file": (
                "marksheet.pdf",
                b"fake pdf content",
                "application/pdf",
            ),
        },
    )

    assert response.status_code == 422


# ============================================================
# POST /documents/applications/{application_id}/documents/validate
# ============================================================

@pytest.mark.asyncio
async def test_request_document_validation_success(
    client,
    test_student,
    test_application,
):
    token = await _get_student_token(client, test_student)

    service = MagicMock()

    service.check_all_document_types_uploaded = AsyncMock(
        return_value=True
    )

    application_repository = MagicMock()
    student_repository = MagicMock()

    app.dependency_overrides[get_document_service] = lambda: service
    app.dependency_overrides[
        get_application_repository
    ] = lambda: application_repository
    app.dependency_overrides[
        get_student_repository
    ] = lambda: student_repository

    workflow_result = {
        "status": "completed",
        "application_id": str(test_application.id),
    }

    try:
        with patch(
            "app.ai.workflows.document_validation_workflow.DocumentValidationWorkflow"
        ) as workflow_class:

            workflow = MagicMock()
            workflow.run = AsyncMock(
                return_value=workflow_result
            )

            workflow_class.return_value = workflow

            response = await client.post(
                f"/documents/applications/{test_application.id}/documents/validate",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

    finally:
        app.dependency_overrides.pop(
            get_document_service,
            None,
        )
        app.dependency_overrides.pop(
            get_application_repository,
            None,
        )
        app.dependency_overrides.pop(
            get_student_repository,
            None,
        )

    assert response.status_code == 200
    assert response.json() == workflow_result

    service.check_all_document_types_uploaded.assert_awaited_once_with(
        test_application.id
    )

    workflow_class.assert_called_once_with(
        document_service=service,
        application_repository=application_repository,
        student_repository=student_repository,
        llm=workflow_class.call_args.kwargs["llm"],
        timeout=120,
        verbose=False,
    )

    workflow.run.assert_awaited_once_with(
        application_id=test_application.id
    )


@pytest.mark.asyncio
async def test_request_document_validation_returns_400_when_not_all_documents_uploaded(
    client,
    test_student,
    test_application,
):
    token = await _get_student_token(client, test_student)

    service = MagicMock()

    service.check_all_document_types_uploaded = AsyncMock(
        return_value=False
    )

    _override_document_service(service)

    try:
        response = await client.post(
            f"/documents/applications/{test_application.id}/documents/validate",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
    finally:
        _clear_document_service_override()

    assert response.status_code == 400
    assert response.json()["detail"] == "All document types not uploaded"

    service.check_all_document_types_uploaded.assert_awaited_once_with(
        test_application.id
    )


@pytest.mark.asyncio
async def test_request_document_validation_requires_authentication(
    client,
    test_application,
):
    response = await client.post(
        f"/documents/applications/{test_application.id}/documents/validate",
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_request_document_validation_rejects_invalid_token(
    client,
    test_application,
):
    response = await client.post(
        f"/documents/applications/{test_application.id}/documents/validate",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_request_document_validation_rejects_invalid_application_id(
    client,
    test_student,
):
    token = await _get_student_token(client, test_student)

    response = await client.post(
        "/documents/applications/not-a-uuid/documents/validate",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422






# tests/test_track_a/test_document_service.py
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.factories import get_application_service, get_document_service
from app.models.enums import (
    AllowedFileType,
    ApplicationStatus,
    DocumentType,
    ValidationStatus,
)


def _mock_storage():
    """Reusable patch context for the two storage calls every upload test needs."""
    return patch.multiple(
        "app.services.document_service.storage_manager",
        upload_document=AsyncMock(),
        build_student_doc_key=lambda *a, **kw: "student-docs/fake-key.pdf",
    )


# ---------------- upload_document_metadata ----------------


@pytest.mark.asyncio
async def test_upload_document_raises_404_when_no_application(db_session, test_student):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        with pytest.raises(HTTPException) as exc_info:
            await document_service.upload_document_metadata(
                test_student,
                DocumentType.ID_CARD,
                "id.pdf",
                b"fake bytes",
                AllowedFileType.PDF,
            )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_upload_document_creates_new_pending_document(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        doc = await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"fake bytes",
            AllowedFileType.PDF,
        )

    assert doc.validation_status == ValidationStatus.PENDING.value
    assert doc.doc_type == DocumentType.ID_CARD.value


@pytest.mark.asyncio
async def test_upload_document_advances_application_status_to_docs_pending(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    application = await application_service.get_application_by_id(test_application.id)
    assert application.status == ApplicationStatus.DOCS_PENDING


@pytest.mark.asyncio
async def test_upload_document_reupload_overwrites_same_row_and_resets_pending(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        first = await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id_v1.pdf",
            b"v1",
            AllowedFileType.PDF,
        )
        # simulate it having been validated before the re-upload
        first.validation_status = ValidationStatus.VALID.value
        await db_session.flush()

        second = await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id_v2.pdf",
            b"v2",
            AllowedFileType.PDF,
        )

    assert first.id == second.id  # same row, not a duplicate
    assert (
        second.validation_status == ValidationStatus.PENDING.value
    )  # reset, not still VALID


@pytest.mark.asyncio
async def test_upload_document_raises_502_on_storage_failure(
    db_session, test_student, test_application
):
    from app.storage import StorageUploadError

    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with patch.multiple(
        "app.services.document_service.storage_manager",
        upload_document=AsyncMock(side_effect=StorageUploadError),
        build_student_doc_key=lambda *a, **kw: "student-docs/fake-key.pdf",
    ):
        with pytest.raises(HTTPException) as exc_info:
            await document_service.upload_document_metadata(
                test_student,
                DocumentType.ID_CARD,
                "id.pdf",
                b"fake bytes",
                AllowedFileType.PDF,
            )
    assert exc_info.value.status_code == 502


# ---------------- get_document_by_application_id_and_type ----------------


@pytest.mark.asyncio
async def test_get_document_by_type_finds_uploaded_document(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    found = await document_service.get_document_by_application_id_and_type(
        test_application.id, DocumentType.ID_CARD
    )
    assert found is not None


@pytest.mark.asyncio
async def test_get_document_by_type_returns_none_when_absent(
    db_session, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    found = await document_service.get_document_by_application_id_and_type(
        test_application.id, DocumentType.INCOME_CERTIFICATE
    )
    assert found is None


# ---------------- list_application_documents ----------------


@pytest.mark.asyncio
async def test_list_application_documents_empty_initially(db_session, test_application):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)
    docs = await document_service.list_application_documents(test_application.id)
    assert docs == []


# ---------------- get_document_bytes ----------------


@pytest.mark.asyncio
async def test_get_document_bytes_raises_404_for_unknown_document(db_session):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with pytest.raises(HTTPException) as exc_info:
        await document_service.get_document_bytes(uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_document_bytes_raises_502_on_fetch_failure(
    db_session, test_student, test_application
):
    from app.storage import StorageFetchError

    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        doc = await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    with (
        patch(
            "app.services.document_service.storage_manager.fetch_document",
            new_callable=AsyncMock,
            side_effect=StorageFetchError,
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await document_service.get_document_bytes(doc.id)
    assert exc_info.value.status_code == 502


# ---------------- check_all_document_types_uploaded ----------------


@pytest.mark.asyncio
async def test_check_all_document_types_uploaded_false_initially(
    db_session, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)
    result = await document_service.check_all_document_types_uploaded(
        test_application.id
    )
    assert result is False


@pytest.mark.asyncio
async def test_check_all_document_types_uploaded_true_when_both_present(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )
        await document_service.upload_document_metadata(
            test_student,
            DocumentType.CLASS12_MARKSHEET,
            "marks.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    result = await document_service.check_all_document_types_uploaded(
        test_application.id
    )
    assert result is True

    application = await application_service.get_application_by_id(test_application.id)
    assert application.status == ApplicationStatus.ALL_DOCS_UPLOADED


# ---------------- mark_auto_validated / rejected / pending ----------------


@pytest.mark.asyncio
async def test_mark_auto_validated_sets_documents_valid_and_application_validated(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    await document_service.mark_auto_validated(
        test_application.id, [DocumentType.ID_CARD.value]
    )

    docs = await document_service.list_application_documents(test_application.id)
    assert docs[0].validation_status == ValidationStatus.VALID.value

    application = await application_service.get_application_by_id(test_application.id)
    assert application.status == ApplicationStatus.VALIDATED
    assert application.validation_issues is None
    assert application.validation_flags == 0


@pytest.mark.asyncio
async def test_mark_auto_validated_raises_404_for_unknown_application(db_session):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)
    with pytest.raises(HTTPException) as exc_info:
        await document_service.mark_auto_validated(uuid.uuid4(), [])
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_auto_rejected_sets_reason_and_invalid(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    await document_service.mark_auto_rejected(
        test_application.id, "Name mismatch on ID card", [DocumentType.ID_CARD.value]
    )

    docs = await document_service.list_application_documents(test_application.id)
    assert docs[0].validation_status == ValidationStatus.INVALID.value
    assert docs[0].validation_reason == "Name mismatch on ID card"

    application = await application_service.get_application_by_id(test_application.id)
    assert application.status == ApplicationStatus.REJECTED
    assert application.validation_issues == "Name mismatch on ID card"


@pytest.mark.asyncio
async def test_mark_auto_pending_leaves_documents_pending_but_flags_application(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    await document_service.mark_auto_pending(
        test_application.id,
        flags=2,
        issues="Low OCR confidence on DOB field",
        doc_types=[DocumentType.ID_CARD.value],
    )

    docs = await document_service.list_application_documents(test_application.id)
    assert (
        docs[0].validation_status == ValidationStatus.PENDING.value
    )  # unchanged by design

    application = await application_service.get_application_by_id(test_application.id)
    assert application.status == ApplicationStatus.PENDING_REVIEW
    assert application.validation_flags == 2
    assert application.validation_issues == "Low OCR confidence on DOB field"


# ---------------- get_download_link ----------------


@pytest.mark.asyncio
async def test_get_download_link_raises_404_for_unknown_document(db_session):
    """Confirms the None-check fix — should raise HTTPException(404), not AttributeError."""
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with pytest.raises(HTTPException) as exc_info:
        await document_service.get_download_link(uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_download_link_returns_presigned_url(
    db_session, test_student, test_application
):
    application_service = get_application_service(db_session)
    document_service = get_document_service(db_session, application_service)

    with _mock_storage():
        doc = await document_service.upload_document_metadata(
            test_student,
            DocumentType.ID_CARD,
            "id.pdf",
            b"x",
            AllowedFileType.PDF,
        )

    with patch(
        "app.services.document_service.storage_manager.generate_presigned_url",
        new_callable=AsyncMock,
        return_value="https://fake-presigned-url.example.com/id.pdf",
    ):
        link = await document_service.get_download_link(doc.id)

    assert link == "https://fake-presigned-url.example.com/id.pdf"

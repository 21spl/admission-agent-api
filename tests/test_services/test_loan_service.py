# tests/test_track_a/test_loan_service.py
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.core.factories import get_loan_service
from app.models.enums import ApplicationStatus, LoanStatus, AllowedFileType
from app.core.config import settings


def _mock_llm_with_income(income_value):
    """Fake initialize_ai_environment() return value whose acomplete()
    resolves to the expected JSON shape."""
    fake_llm = MagicMock()
    text = f'{{"annual_income_inr": {income_value}}}' if income_value is not None else '{"annual_income_inr": null}'
    fake_response = MagicMock()
    fake_response.text = text
    fake_llm.acomplete = AsyncMock(return_value=fake_response)
    return fake_llm


def _mock_storage_patches():
    return patch.multiple(
        "app.services.loan_service.storage_manager",
        upload_document=AsyncMock(),
        build_student_doc_key=lambda *a, **kw: "student-docs/fake-key.pdf",
    )


async def _set_status(db_session, application, status_: ApplicationStatus):
    application.status = status_
    await db_session.flush()


# ---------------- request_loan ----------------

@pytest.mark.asyncio
async def test_request_loan_raises_404_when_no_application(db_session, test_student):
    loan_service = get_loan_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_request_loan_raises_409_when_offer_not_accepted(db_session, test_student, test_application):
    loan_service = get_loan_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)
    assert exc_info.value.status_code == 409
    assert "offer has been accepted" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_request_loan_raises_409_when_decision_already_exists(db_session, test_student, test_application):
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)

    with patch(
        "app.services.loan_service.initialize_ai_environment",
        return_value=_mock_llm_with_income(300000),
    ), patch.object(
        loan_service, "_read_pdf_text", return_value="Annual income: Rs. 3,00,000"
    ), _mock_storage_patches():
        await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)

        with pytest.raises(HTTPException) as exc_info:
            await loan_service.request_loan(test_student, "income2.pdf", b"fake2", AllowedFileType.PDF)

    assert exc_info.value.status_code == 409
    assert "already been made" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_request_loan_raises_422_when_income_extraction_fails(db_session, test_student, test_application):
    """Extraction returns null income — should surface as 422, and critically,
    should NOT have uploaded anything to storage (extract-before-persist ordering)."""
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)

    with patch(
        "app.services.loan_service.initialize_ai_environment",
        return_value=_mock_llm_with_income(None),
    ), patch.object(
        loan_service, "_read_pdf_text", return_value="Some unrelated document text"
    ), patch(
        "app.services.loan_service.storage_manager.upload_document", new_callable=AsyncMock,
    ) as mock_upload:
        with pytest.raises(HTTPException) as exc_info:
            await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)

    assert exc_info.value.status_code == 422
    mock_upload.assert_not_awaited()  # confirms extract-before-persist ordering held


@pytest.mark.asyncio
async def test_request_loan_raises_422_when_pdf_has_no_readable_text(db_session, test_student, test_application):
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)

    with patch.object(loan_service, "_read_pdf_text", return_value="   "):
        with pytest.raises(HTTPException) as exc_info:
            await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_request_loan_approves_when_income_below_threshold(db_session, test_student, test_application):
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)
    below_threshold = settings.LOAN_INCOME_THRESHOLD_INR - 1

    with patch(
        "app.services.loan_service.initialize_ai_environment",
        return_value=_mock_llm_with_income(below_threshold),
    ), patch.object(
        loan_service, "_read_pdf_text", return_value=f"Annual income: Rs. {below_threshold}"
    ), _mock_storage_patches():
        loan = await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)

    assert loan.status == LoanStatus.APPROVED
    assert loan.extracted_annual_income == below_threshold


@pytest.mark.asyncio
async def test_request_loan_rejects_when_income_above_threshold(db_session, test_student, test_application):
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)
    above_threshold = settings.LOAN_INCOME_THRESHOLD_INR + 100000

    with patch(
        "app.services.loan_service.initialize_ai_environment",
        return_value=_mock_llm_with_income(above_threshold),
    ), patch.object(
        loan_service, "_read_pdf_text", return_value=f"Annual income: Rs. {above_threshold}"
    ), _mock_storage_patches():
        loan = await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)

    assert loan.status == LoanStatus.REJECTED


@pytest.mark.asyncio
async def test_request_loan_income_exactly_at_threshold_is_approved(db_session, test_student, test_application):
    """Boundary check: condition is `<=`, so exact threshold should be APPROVED."""
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)
    exact_threshold = settings.LOAN_INCOME_THRESHOLD_INR

    with patch(
        "app.services.loan_service.initialize_ai_environment",
        return_value=_mock_llm_with_income(exact_threshold),
    ), patch.object(
        loan_service, "_read_pdf_text", return_value=f"Annual income: Rs. {exact_threshold}"
    ), _mock_storage_patches():
        loan = await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)

    assert loan.status == LoanStatus.APPROVED


@pytest.mark.asyncio
async def test_request_loan_raises_422_on_malformed_llm_json(db_session, test_student, test_application):
    """LLM returns something that isn't valid JSON — should surface as a
    clean 422 via IncomeExtractionError, not an unhandled JSONDecodeError."""
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)

    bad_llm = MagicMock()
    bad_response = MagicMock()
    bad_response.text = "Sorry, I cannot process this request."
    bad_llm.acomplete = AsyncMock(return_value=bad_response)

    with patch(
        "app.services.loan_service.initialize_ai_environment", return_value=bad_llm,
    ), patch.object(
        loan_service, "_read_pdf_text", return_value="Some document text"
    ):
        with pytest.raises(HTTPException) as exc_info:
            await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_request_loan_raises_502_on_storage_failure(db_session, test_student, test_application):
    from app.storage import StorageUploadError
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)

    with patch(
        "app.services.loan_service.initialize_ai_environment",
        return_value=_mock_llm_with_income(200000),
    ), patch.object(
        loan_service, "_read_pdf_text", return_value="Annual income: Rs. 2,00,000"
    ), patch.multiple(
        "app.services.loan_service.storage_manager",
        upload_document=AsyncMock(side_effect=StorageUploadError),
        build_student_doc_key=lambda *a, **kw: "student-docs/fake-key.pdf",
    ):
        with pytest.raises(HTTPException) as exc_info:
            await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)
    assert exc_info.value.status_code == 502


# ---------------- get_loan_application ----------------

@pytest.mark.asyncio
async def test_get_loan_application_raises_404_when_no_application(db_session, test_student):
    loan_service = get_loan_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await loan_service.get_loan_application(test_student)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_loan_application_raises_404_when_no_loan_yet(db_session, test_student, test_application):
    loan_service = get_loan_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await loan_service.get_loan_application(test_student)
    assert exc_info.value.status_code == 404
    assert "no loan application" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_loan_application_returns_real_loan(db_session, test_student, test_application):
    await _set_status(db_session, test_application, ApplicationStatus.OFFER_ACCEPTED)
    loan_service = get_loan_service(db_session)

    with patch(
        "app.services.loan_service.initialize_ai_environment",
        return_value=_mock_llm_with_income(200000),
    ), patch.object(
        loan_service, "_read_pdf_text", return_value="Annual income: Rs. 2,00,000"
    ), _mock_storage_patches():
        created = await loan_service.request_loan(test_student, "income.pdf", b"fake", AllowedFileType.PDF)

    fetched = await loan_service.get_loan_application(test_student)
    assert fetched.id == created.id


# ---------------- get_loan_application_by_application_id ----------------

@pytest.mark.asyncio
async def test_get_loan_application_by_application_id_returns_none_when_absent(db_session, test_application):
    """
    NOTE: this method has no None-check of its own — it returns whatever
    loan_repository.get_by_application_id gives back directly. Confirm
    that repository method returns None on no match rather than raising.
    """
    loan_service = get_loan_service(db_session)
    result = await loan_service.get_loan_application_by_application_id(test_application.id)
    assert result is None
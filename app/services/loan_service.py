import asyncio
import io
import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pypdf import PdfReader

from app.ai.config import initialize_ai_environment
from app.core.config import settings
from app.models.domain import Document, LoanApplication, Student
from app.models.enums import AllowedFileType, ApplicationStatus, DocumentType, LoanStatus
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.loan_repository import LoanRepository
from app.storage import StorageUploadError, storage_manager

logger = logging.getLogger(__name__)

llm = initialize_ai_environment()


class IncomeExtractionError(Exception):
    """Raised when the annual income figure cannot be reliably extracted from the document."""


class LoanService:
    def __init__(
        self,
        loan_repository: LoanRepository,
        application_repository: ApplicationRepository,
        document_repository: DocumentRepository,
    ):

        self.loan_repository = loan_repository
        self.application_repository = application_repository
        self.document_repository = document_repository

    # =========================================== REQUEST LOAN (orchestrator) ======================================
    async def request_loan(
        self, student: Student, filename: str, file_bytes: bytes, content_type: AllowedFileType
    ) -> LoanApplication:
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No application profile active for this account.")

        if application.status != ApplicationStatus.OFFER_ACCEPTED:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Loan applications can only be submitted after an offer has been accepted.",
            )

        existing = await self.loan_repository.get_by_application_id(application.id)
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "A loan decision has already been made for this application.",
            )

        # Extract FIRST, from the raw bytes already in memory — nothing is
        # persisted (S3 or DB) until we know the document is actually usable.
        try:
            income = await self._extract_annual_income(file_bytes)
        except IncomeExtractionError as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from e

        # Only now do we upload + create records, since extraction succeeded.
        document = await self._upload_income_certificate(application.id, filename, file_bytes, content_type)

        loan_status = (
            LoanStatus.APPROVED
            if income <= settings.LOAN_INCOME_THRESHOLD_INR
            else LoanStatus.REJECTED
        )

        loan_application = LoanApplication(
            application_id=application.id,
            income_certificate_doc_id=document.id,
            status=loan_status,
            extracted_annual_income=income,
            decided_at=datetime.now(timezone.utc),
        )
        return await self.loan_repository.create(loan_application)

    # ============================================ UPLOAD INCOME CERTIFICATE ==================================
    async def _upload_income_certificate(
        self, application_id, filename: str, file_bytes: bytes, content_type: AllowedFileType
    ) -> Document:
        storage_key = storage_manager.build_student_doc_key(
            application_id, DocumentType.INCOME_CERTIFICATE.value, filename
        )

        try:
            await storage_manager.upload_document(io.BytesIO(file_bytes), storage_key, content_type.value)
        except StorageUploadError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to store the uploaded document. Please try again.",
            )

        new_doc = Document(
            application_id=application_id,
            doc_type=DocumentType.INCOME_CERTIFICATE.value,
            storage_key=storage_key,
            content_type=content_type.value,
            file_size_bytes=len(file_bytes),
        )
        return await self.document_repository.create(new_doc)

    # ========================================== EXTRACT ANNUAL INCOME ==========================================
    async def _extract_annual_income(self, file_bytes: bytes) -> float:
        """Single-purpose extraction: reads the stated annual parental income
        directly from in-memory PDF bytes, before anything is persisted."""
        pdf_text = await asyncio.to_thread(self._read_pdf_text, file_bytes)
        if not pdf_text.strip():
            raise IncomeExtractionError("Could not read any content from the uploaded document.")

        prompt = (
            "You are extracting a single figure from an Indian income certificate. "
            "Read the document text below and return ONLY valid JSON, no markdown, "
            "no preamble, in this exact shape:\n"
            '{"annual_income_inr": <number or null>}\n\n'
            "If you cannot confidently find a stated annual income figure in INR, "
            "return null for annual_income_inr.\n\n"
            f"Document text:\n{pdf_text}"
        )

        response = await llm.acomplete(prompt)

        try:
            parsed = json.loads(response.text.strip())
            income = parsed.get("annual_income_inr")
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error("Failed to parse income extraction response: %s", e)
            raise IncomeExtractionError("Could not parse extraction response.") from e

        if income is None:
            raise IncomeExtractionError("Could not find a stated annual income in the document.")

        try:
            return float(income)
        except (TypeError, ValueError) as e:
            raise IncomeExtractionError("Extracted income value was not numeric.") from e

    # ========================================== READ PDF TEXT =================================================
    @staticmethod
    def _read_pdf_text(file_bytes: bytes) -> str:
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    # =========================================== GET LOAN STATUS ================================================
    async def get_loan_status(self, student: Student) -> LoanApplication:
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No application profile active for this account.")

        loan_application = await self.loan_repository.get_by_application_id(application.id)
        if not loan_application:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No loan application on record.")
        return loan_application
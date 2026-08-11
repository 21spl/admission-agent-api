from enum import Enum


class OfficerRole(str, Enum):
    ADMISSION_OFFICER = "ADMISSION_OFFICER"
    ADMIN = "ADMIN"


class ApplicationStatus(str, Enum):
    STARTED = "STARTED"
    SUBMITTED = "SUBMITTED"
    DOCS_PENDING = "DOCS_PENDING"
    ALL_DOCS_UPLOADED = "ALL_DOCS_UPLOADED"

    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    WITHDRAWN = "WITHDRAWN"

    # Following two enums are not used---
    DOCS_VALIDATED = "DOCS_VALIDATED"
    DOCS_INVALID = "DOCS_INVALID"
    # ----------------------------------------------

    OFFER_MADE = "OFFER_MADE"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"
    OFFER_REJECTED = "OFFER_REJECTED"
    OFFER_EXPIRED = "OFFER_EXPIRED"
    WAITLISTED = "WAITLISTED"
    UNDER_VALIDATION = "UNDER_VALIDATION"
    DOCUMENTS_PENDING_UPLOAD = "DOCUMENTS_PENDING_UPLOAD"


class DocumentType(str, Enum):
    CLASS12_MARKSHEET = "CLASS12_MARKSHEET"
    ID_CARD = "ID_CARD"
    INCOME_CERTIFICATE = "INCOME_CERTIFICATE"
    OTHER = "OTHER"


# Document types validated automatically by DocumentValidationWorkflow.
# All other DocumentType members are validated manually via
# PATCH /documents/{document_id}/verify.
AI_MANAGED_TYPES = {
    DocumentType.CLASS12_MARKSHEET.value,
    DocumentType.ID_CARD.value,
}


class ValidationStatus(str, Enum):
    PENDING = "PENDING"
    VALID = "VALID"
    INVALID = "INVALID"


class OfferStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class NotificationType(str, Enum):
    SHORTLIST_OFFER = "SHORTLIST_OFFER"
    LOAN_APPROVAL = "LOAN_APPROVAL"
    WAITLIST_UPDATE = "WAITLIST_UPDATE"
    REJECTION = "REJECTION"


class NotificationStatus(str, Enum):
    SENT = "SENT"
    FAILED = "FAILED"


class LoanStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AllowedFileType(str, Enum):
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

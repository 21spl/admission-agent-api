# Mirrors app/models/enums.py — keep in sync with backend

APPLICATION_STATUSES = [
    "STARTED",
    "SUBMITTED",
    "DOCS_PENDING",
    "ALL_DOCS_UPLOADED",
    "VALIDATED",
    "REJECTED",
    "PENDING_REVIEW",
    "WITHDRAWN",
    "OFFER_MADE",
    "OFFER_ACCEPTED",
    "OFFER_REJECTED",
    "OFFER_EXPIRED",
    "WAITLISTED",
    "UNDER_VALIDATION",
    "DOCUMENTS_PENDING_UPLOAD",
]

DOCUMENT_TYPES = ["CLASS12_MARKSHEET", "ID_CARD", "INCOME_CERTIFICATE", "OTHER"]

VALIDATION_STATUSES = ["PENDING", "VALID", "INVALID"]

OFFER_STATUSES = ["PENDING", "ACCEPTED", "REJECTED", "EXPIRED"]

LOAN_STATUSES = ["NOT_REQUESTED", "PENDING", "APPROVED", "REJECTED"]

# Status -> (label color, background color) for badges
STATUS_COLORS = {
    # neutral / in-progress
    "STARTED": ("#664d03", "#fff3cd"),
    "SUBMITTED": ("#084298", "#cfe2ff"),
    "DOCS_PENDING": ("#664d03", "#fff3cd"),
    "DOCUMENTS_PENDING_UPLOAD": ("#664d03", "#fff3cd"),
    "ALL_DOCS_UPLOADED": ("#084298", "#cfe2ff"),
    "UNDER_VALIDATION": ("#084298", "#cfe2ff"),
    "PENDING_REVIEW": ("#664d03", "#fff3cd"),
    "PENDING": ("#664d03", "#fff3cd"),
    "WAITLISTED": ("#664d03", "#fff3cd"),
    # positive
    "VALIDATED": ("#0f5132", "#d1e7dd"),
    "VALID": ("#0f5132", "#d1e7dd"),
    "OFFER_MADE": ("#0f5132", "#d1e7dd"),
    "OFFER_ACCEPTED": ("#0f5132", "#d1e7dd"),
    "ACCEPTED": ("#0f5132", "#d1e7dd"),
    "APPROVED": ("#0f5132", "#d1e7dd"),
    # negative
    "REJECTED": ("#842029", "#f8d7da"),
    "OFFER_REJECTED": ("#842029", "#f8d7da"),
    "OFFER_EXPIRED": ("#842029", "#f8d7da"),
    "EXPIRED": ("#842029", "#f8d7da"),
    "INVALID": ("#842029", "#f8d7da"),
    "WITHDRAWN": ("#842029", "#f8d7da"),
    "NOT_REQUESTED": ("#41464b", "#e2e3e5"),
}

DEFAULT_STATUS_COLOR = ("#41464b", "#e2e3e5")

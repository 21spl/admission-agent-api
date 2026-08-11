# app/api/routes/admin_review.py

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import get_current_officer
from app.core.factories import (
    get_admin_review_service,
    get_application_repository,
    get_document_service,
)
from app.models.domain import Application, Officer
from app.models.enums import ApplicationStatus, DocumentType
from app.schemas.application_review import ReviewsPendingResponse

router = APIRouter(prefix="/admin/document-reviews", tags=["Admin Review"])


# ============================================= LIST PENDING REVIEWS =========================================================


@router.get("/", response_model=list[ReviewsPendingResponse])
async def list_pending_reviews(
    application_repository=Depends(get_application_repository),
    officer: Officer = Depends(get_current_officer),
    document_service=Depends(get_document_service),
):
    applications = await application_repository.list_by_status(
        ApplicationStatus.PENDING_REVIEW
    )

    # this is an inner function that builds a response for each application
    async def build_response(app: Application) -> ReviewsPendingResponse:
        marksheet_doc = next(
            (d for d in app.documents if d.doc_type == DocumentType.CLASS12_MARKSHEET),
            None,
        )
        id_card_doc = next(
            (d for d in app.documents if d.doc_type == DocumentType.ID_CARD), None
        )

        marksheet_link = (
            await document_service.get_download_link(marksheet_doc.id)
            if marksheet_doc
            else None
        )
        id_card_link = (
            await document_service.get_download_link(id_card_doc.id)
            if id_card_doc
            else None
        )

        return ReviewsPendingResponse(
            application_id=app.id,
            submitted_at=app.submitted_at,
            status=app.status,
            validation_flags=app.validation_flags,
            validation_issues=app.validation_issues,
            updated_at=app.updated_at,
            class12_marksheet=marksheet_link,
            id_card=id_card_link,
        )

    return await asyncio.gather(*(build_response(app) for app in applications))


# ============================================= SUBMIT REVIEW DECISION =========================================================


class ReviewDecision(BaseModel):
    approve: bool


@router.post("/{application_id}/decision")
async def submit_review_decision(
    application_id: uuid.UUID,
    decision: ReviewDecision,
    officer: Officer = Depends(get_current_officer),
    document_service=Depends(get_document_service),
    application_repository=Depends(get_application_repository),
    admin_review_service=Depends(get_admin_review_service),
):
    application = await application_repository.get_by_id(application_id)
    if application is None or application.status != ApplicationStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending review found for this application.",
        )

    if decision.approve:
        # call validate_application_manually function
        await admin_review_service.validate_application_manually(application_id)
    else:
        await admin_review_service.reject_application_manually(application_id)

    return {"status": "resolved", "application_id": application_id}

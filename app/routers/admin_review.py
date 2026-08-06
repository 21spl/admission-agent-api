
# app/api/routes/admin_review.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import get_current_officer
from app.core.factories import get_admin_review_service, get_application_repository, get_document_service

from app.models.domain import Officer
from app.models.enums import ApplicationStatus, DocumentType
from app.models.enums import ApplicationStatus, AI_MANAGED_TYPES

router = APIRouter(prefix="/admin/document-reviews", tags=["admin-review"])


#============================================= LIST PENDING REVIEWS =========================================================

@router.get("/")
async def list_pending_reviews(
    application_repository=Depends(get_application_repository),
    officer: Officer = Depends(get_current_officer),
):
    return await application_repository.list_by_status(ApplicationStatus.PENDING_REVIEW)


class ReviewDecision(BaseModel):
    approve: bool

#============================================= SUBMIT REVIEW DECISION =========================================================
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
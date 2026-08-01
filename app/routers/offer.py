import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from app.core.factories import get_offer_service
from app.services.offer_service import OfferService
from app.schemas.offer import OfferResponse, OfferDecisionRequest
from app.core.dependencies import get_current_student, get_current_officer
from app.models.domain import Student, Officer

router = APIRouter(prefix="/offers", tags=["Offers & Allocations"])

@router.get("/me", response_model=List[OfferResponse], status_code=status.HTTP_200_OK)
async def get_my_active_offers(
    service: OfferService = Depends(get_offer_service),
    current_student: Student = Depends(get_current_student)
):
    """
    Secured Student Endpoint: Allows an authenticated applicant to look up 
    their history of admission offers.
    """
    # Fetch active student context application reference mapping
    app_record = await service.application_repository.get_by_student_id(current_student.id)
    if not app_record:
        return []
    return await service.list_application_offers(app_record.id)


@router.patch("/{offer_id}/respond", response_model=OfferResponse, status_code=status.HTTP_200_OK)
async def respond_to_admission_offer(
    offer_id: uuid.UUID,
    payload: OfferDecisionRequest,
    service: OfferService = Depends(get_offer_service),
    current_student: Student = Depends(get_current_student)
):
    """
    Secured Student Endpoint: Allows a student to explicitly ACCEPT or REJECT 
    a pending admission offer. Updates seat counts atomically.
    """
    return await service.process_student_decision(
        student=current_student, 
        offer_id=offer_id, 
        data=payload
    )


@router.get("/application/{application_id}", response_model=List[OfferResponse], status_code=status.HTTP_200_OK)
async def get_offers_by_application_id(
    application_id: uuid.UUID,
    service: OfferService = Depends(get_offer_service),
    current_officer: Officer = Depends(get_current_officer)
):
    """
    Secured Officer Endpoint: Allows internal admission administrative staff to inspect 
    the full offer ledger associated with any student application index tracker.
    """
    return await service.list_application_offers(application_id)

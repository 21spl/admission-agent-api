import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, status
from app.repositories.offer_repository import OfferRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService
from app.schemas.offer import OfferDecisionRequest
from app.models.domain import Offer, Student
from app.models.enums import OfferStatus, ApplicationStatus

class OfferService:
    def __init__(
        self, 
        repository: OfferRepository, 
        branch_repository: BranchRepository,
        application_repository: ApplicationRepository,
        application_service: ApplicationService
    ):
        self.repository = repository
        self.branch_repository = branch_repository
        self.application_repository = application_repository
        self.application_service = application_service

    async def list_application_offers(self, application_id: uuid.UUID) -> List[Offer]:
        return await self.repository.get_by_application_id(application_id)

    async def process_student_decision(self, student: Student, offer_id: uuid.UUID, data: OfferDecisionRequest) -> Offer:
        """Processes student decisions (ACCEPT/REJECT) and dynamically updates seat allocations."""
        # 1. Verify the parent student application envelope
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No application found.")

        # 2. Extract and validate target offer lifecycle boundaries
        offer = await self.repository.get_by_id(offer_id)
        if not offer or offer.application_id != application.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target offer reference not found.")

        if offer.status != OfferStatus.PENDING.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This offer has already been processed.")

        if datetime.now(timezone.utc) > offer.expires_at.replace(tzinfo=timezone.utc):
            offer.status = OfferStatus.EXPIRED.value
            await self.repository.update(offer)
            await self.application_service.update_application_status(
                application.id, ApplicationStatus.OFFER_EXPIRED, f"SYSTEM_TIMEOUT_STUDENT_{student.id}"
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This admission offer has expired.")

        # 3. Handle state machine transitions based on input data
        operator_log = f"STUDENT_ACTION_{student.id}"
        offer.responded_at = datetime.now(timezone.utc)

        if data.status == OfferStatus.ACCEPTED:
            # Atomic capacity allocation execution guard block
            success = await self.branch_repository.decrement_available_seats(offer.branch_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Seat allocation capacity exhausted for this target branch branch selection."
                )
            
            offer.status = OfferStatus.ACCEPTED.value
            await self.application_service.update_application_status(
                application.id, ApplicationStatus.OFFER_ACCEPTED, operator_log
            )

        elif data.status == OfferStatus.REJECTED:
            offer.status = OfferStatus.REJECTED.value
            # Note: No seat return is required here because seats decrement ONLY on explicit choice acceptance.
            await self.application_service.update_application_status(
                application.id, ApplicationStatus.OFFER_REJECTED, operator_log
            )

        return await self.repository.update(offer)



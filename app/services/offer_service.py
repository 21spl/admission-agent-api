import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Offer, Student, Branch
from app.models.enums import OfferStatus, ApplicationStatus
from app.repositories.shortlisting_preference_repository import ShortlistingPreferenceRepository
from app.schemas.offer import OfferDecisionRequest, OfferResponse

from app.repositories.offer_repository import OfferRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService


class OfferService:
    def __init__(
        self,
        db: AsyncSession,
        offer_repository: OfferRepository,
        application_repository: ApplicationRepository,
        preference_repository: ShortlistingPreferenceRepository,
        application_service: ApplicationService,
    ):
        self.db = db
        self.offer_repository = offer_repository
        self.application_repository = application_repository
        self.preference_repository = preference_repository
        self.application_service = application_service

    async def list_my_offers(self, student: Student) -> List[Offer]:
        application = await self.application_repository.get_by_student_id(student.id)
        if application is None:
            return []
        return await self.offer_repository.get_by_application_id(application.id)

    async def list_offers_for_application(self, application_id: uuid.UUID) -> List[Offer]:
        return await self.offer_repository.get_by_application_id(application_id)

    async def process_student_decision(
        self, student: Student, offer_id: uuid.UUID, data: OfferDecisionRequest
    ) -> OfferResponse:
        offer = await self.offer_repository.get_by_id(offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found.")

        application = await self.application_repository.get_with_details(offer.application_id)
        if application is None or application.student_id != student.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found.")

        if offer.status != OfferStatus.PENDING:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Offer already resolved (status={offer.status}).")

        now = datetime.now(timezone.utc)
        if offer.expires_at < now:
            raise HTTPException(status.HTTP_410_GONE, "This offer has expired.")

        if data.accept:
            # --- accept path ---
            stmt = (
                update(Branch)
                .where(Branch.id == offer.branch_id)
                .where(Branch.available_seats > 0)
                .values(available_seats=Branch.available_seats - 1)
            )
            result = await self.db.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(status.HTTP_409_CONFLICT, "No seats remaining for this branch.")

            offer.status = OfferStatus.ACCEPTED
            offer.responded_at = now
            offer = await self.offer_repository.update(offer)

            await self.application_service.update_application_status(
                application.id, ApplicationStatus.OFFER_ACCEPTED, changed_by=str(student.id)
            )
            return OfferResponse.model_validate(offer)

        # --- reject path ---
        first_pref = await self.preference_repository.get_first_preference(application.id)
        first_pref_branch_id = first_pref.branch_id if first_pref else None

        offer.status = OfferStatus.REJECTED
        offer.responded_at = now
        offer = await self.offer_repository.update(offer)

        if first_pref_branch_id == offer.branch_id:
            await self.application_service.update_application_status(
                application.id, ApplicationStatus.WITHDRAWN, changed_by=str(student.id)
            )
            return OfferResponse.model_validate(offer)

        await self.application_service.update_application_status(
            application.id, ApplicationStatus.OFFER_REJECTED, changed_by=str(student.id)
        )
        return OfferResponse.model_validate(offer)
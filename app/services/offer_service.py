import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Offer, Application, ShortlistingPreference, Student
from app.models.enums import OfferStatus, ApplicationStatus
from app.schemas.offer import OfferDecisionRequest, OfferResponse


class OfferService:
    def __init__(self, db: AsyncSession):
        self.db = db


    #==================================================== LIST OFFERS ======================================================
    async def list_my_offers(self, student: Student) -> List[Offer]:
        result = await self.db.execute(
            select(Offer)
            .join(Application, Application.id == Offer.application_id)
            .where(Application.student_id == student.id)
            .order_by(Offer.sent_at.desc())
        )
        return result.scalars().all()

    
    #========================================= LIST OFFERS FOR APPLICATION ==============================================
    async def list_offers_for_application(self, application_id: uuid.UUID) -> List[Offer]:
        result = await self.db.execute(
            select(Offer)
            .where(Offer.application_id == application_id)
            .order_by(Offer.round_number.asc())
        )
        return result.scalars().all()

    
    #========================================= PROCESS STUDENT DECISION ==============================================
    async def process_student_decision(
        self, student: Student, offer_id: uuid.UUID, data: OfferDecisionRequest
    ) -> OfferResponse:
        offer = await self.db.get(Offer, offer_id)
        if offer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found.")

        application = await self.db.get(Application, offer.application_id)
        if application is None or application.student_id != student.id:
            # don't leak whether the offer exists for someone else's application
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found.")

        if offer.status != OfferStatus.PENDING:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Offer already resolved (status={offer.status})."
            )
        if offer.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_410_GONE, "This offer has expired.")

        now = datetime.now(timezone.utc)

        if data.accept:
            offer.status = OfferStatus.ACCEPTED
            offer.responded_at = now
            application.status = ApplicationStatus.OFFER_ACCEPTED
            await self.db.commit()
            await self.db.refresh(offer)
            return OfferResponse.model_validate(offer)

        #=================================================== MANAGE REJECTIONS ==========================================
        first_pref_branch_id = await self.db.scalar(
            select(ShortlistingPreference.branch_id)
            .where(ShortlistingPreference.application_id == application.id)
            .order_by(ShortlistingPreference.preference_order.asc())
            .limit(1)
        )

        offer.status = OfferStatus.REJECTED
        offer.responded_at = now

        if first_pref_branch_id == offer.branch_id:
            # capture response data BEFORE delete/commit — the Offer row
            # cascades away with the Application, so the ORM object is
            # unusable (expired + gone) once the delete is committed
            response_data = OfferResponse.model_validate(offer)
            await self.db.delete(application)
            await self.db.commit()
            return response_data

        application.status = ApplicationStatus.OFFER_REJECTED
        await self.db.commit()
        await self.db.refresh(offer)
        return OfferResponse.model_validate(offer)


    
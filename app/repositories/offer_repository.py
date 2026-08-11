import uuid

from sqlalchemy import select

from app.models.domain import Offer
from app.models.enums import OfferStatus
from app.repositories.base_repository import BaseRepository


class OfferRepository(BaseRepository[Offer]):
    def __init__(self, db):
        super().__init__(Offer, db)

    async def get_by_application_id(self, application_id: uuid.UUID) -> list[Offer]:
        """Retrieves a historical ledger list of all offers issued to an application."""
        stmt = select(Offer).where(Offer.application_id == application_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_pending_offer(self, application_id: uuid.UUID) -> Offer | None:
        """Locates a currently active, non-expired pending offer row for decision processing."""
        stmt = (
            select(Offer)
            .where(Offer.application_id == application_id)
            .where(Offer.status == OfferStatus.PENDING.value)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

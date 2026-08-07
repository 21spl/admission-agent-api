# app/repositories/shortlisting_preference_repository.py
import uuid
from typing import List, Optional
from sqlalchemy import select

from app.models.domain import ShortlistingPreference
from app.repositories.base_repository import BaseRepository


class ShortlistingPreferenceRepository(BaseRepository[ShortlistingPreference]):
    def __init__(self, db):
        super().__init__(ShortlistingPreference, db)

    async def get_ordered_by_application(self, application_id: uuid.UUID) -> List[ShortlistingPreference]:
        result = await self.db.execute(
            select(ShortlistingPreference)
            .where(ShortlistingPreference.application_id == application_id)
            .order_by(ShortlistingPreference.preference_order.asc())
        )
        return list(result.scalars().all())

    async def get_first_preference(self, application_id: uuid.UUID) -> Optional[ShortlistingPreference]:
        result = await self.db.execute(
            select(ShortlistingPreference)
            .where(ShortlistingPreference.application_id == application_id)
            .order_by(ShortlistingPreference.preference_order.asc())
            .limit(1)
        )
        return result.scalars().first()
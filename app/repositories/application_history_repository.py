import uuid
from typing import List
from sqlalchemy import select
from app.repositories.base_repository import BaseRepository
from app.models.domain import ApplicationStatusHistory

class ApplicationStatusHistoryRepository(BaseRepository[ApplicationStatusHistory]):
    def __init__(self, db):
        super().__init__(ApplicationStatusHistory, db)

    #============= Get Application Status History by Application ID =================
    async def get_by_application_id(self, application_id: uuid.UUID) -> List[ApplicationStatusHistory]:
        """Fetches the complete audit trail for an application, sorted chronologically."""
        stmt = (
            select(ApplicationStatusHistory)
            .where(ApplicationStatusHistory.application_id == application_id)
            .order_by(ApplicationStatusHistory.changed_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


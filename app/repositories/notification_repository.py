import uuid
from typing import List
from sqlalchemy import select
from app.repositories.base_repository import BaseRepository
from app.models.domain import NotificationLog

class NotificationRepository(BaseRepository[NotificationLog]):
    def __init__(self, db):
        super().__init__(NotificationLog, db)

    async def get_by_application_id(self, application_id: uuid.UUID) -> List[NotificationLog]:
        """Retrieves a historical ledger list of all messages sent to an application."""
        stmt = (
            select(NotificationLog)
            .where(NotificationLog.application_id == application_id)
            .order_by(NotificationLog.sent_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_recipient_email(self, email: str) -> List[NotificationLog]:
        """Looks up messaging logs across tracking IDs matching a specific destination email."""
        stmt = (
            select(NotificationLog)
            .where(NotificationLog.recipient_email == email)
            .order_by(NotificationLog.sent_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())



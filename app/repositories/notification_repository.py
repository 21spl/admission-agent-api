import uuid

from sqlalchemy import select

from app.models.domain import NotificationLog
from app.models.enums import NotificationStatus, NotificationType
from app.repositories.base_repository import BaseRepository


class NotificationLogRepository(BaseRepository[NotificationLog]):
    def __init__(self, db):
        super().__init__(NotificationLog, db)

    # ============================= CREATE NEW NOTIFICATION ENTRY ========================================
    async def create(
        self,
        recipient_email: str,
        notification_type: NotificationType,
        status: NotificationStatus,
        application_id: uuid.UUID | None = None,
    ) -> NotificationLog:
        # override BaseRepository.create()
        entry = NotificationLog(
            application_id=application_id,
            recipient_email=recipient_email,
            type=notification_type,
            status=status,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    # ==================== GET NOTIFICATION LOGS BY APPLICATION ID ================================
    async def get_by_application_id(
        self, application_id: uuid.UUID
    ) -> list[NotificationLog]:
        """Retrieves a historical ledger list of all messages sent to an application."""
        stmt = (
            select(NotificationLog)
            .where(NotificationLog.application_id == application_id)
            .order_by(NotificationLog.sent_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ==================== GET NOTIFICATION LOGS BY RECIPIENT EMAIL ================================
    async def get_by_recipient_email(self, email: str) -> list[NotificationLog]:
        """Looks up messaging logs across tracking IDs matching a specific destination email."""
        stmt = (
            select(NotificationLog)
            .where(NotificationLog.recipient_email == email)
            .order_by(NotificationLog.sent_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

import uuid

from app.models.domain import NotificationLog

# import repository
from app.repositories.notification_repository import NotificationLogRepository

# import schemas
from app.schemas.notification import NotificationLogCreate


class NotificationService:
    def __init__(self, repository: NotificationLogRepository):
        self.repository = repository

    async def log_notification(self, data: NotificationLogCreate) -> NotificationLog:
        """Registers a fresh message delivery event inside the database audit ledger."""
        return await self.repository.create(
            recipient_email=str(data.recipient_email),
            notification_type=data.type,
            status=data.status,
            application_id=data.application_id,
        )

    async def get_application_logs(
        self, application_id: uuid.UUID
    ) -> list[NotificationLog]:
        return await self.repository.get_by_application_id(application_id)

    async def get_logs_by_email(self, email: str) -> list[NotificationLog]:
        return await self.repository.get_by_recipient_email(email)

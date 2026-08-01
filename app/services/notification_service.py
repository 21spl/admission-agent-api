import uuid
from typing import List
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationLogCreate
from app.models.domain import NotificationLog, Student

class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def log_notification(self, data: NotificationLogCreate) -> NotificationLog:
        """Registers a fresh message delivery event inside the database audit ledger."""
        new_log = NotificationLog(
            application_id=data.application_id,
            recipient_email=str(data.recipient_email),
            type=data.type.value,
            status=data.status.value
        )
        return await self.repository.create(new_log)

    async def get_application_logs(self, application_id: uuid.UUID) -> List[NotificationLog]:
        return await self.repository.get_by_application_id(application_id)

    async def get_logs_by_email(self, email: str) -> List[NotificationLog]:
        return await self.repository.get_by_recipient_email(email)



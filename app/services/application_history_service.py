import uuid
from typing import List
from fastapi import HTTPException, status
# import repositories
from app.repositories.application_history_repository import ApplicationStatusHistoryRepository
from app.repositories.application_repository import ApplicationRepository
from app.models.domain import ApplicationStatusHistory, Student

class ApplicationHistoryService:
    def __init__(
        self, 
        repository: ApplicationStatusHistoryRepository,
        application_repository: ApplicationRepository
    ):
        self.repository = repository
        self.application_repository = application_repository

    async def get_history_for_student(self, student: Student) -> List[ApplicationStatusHistory]:
        """Allows a student to retrieve logs for their own application profile."""
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No application profile active for this account."
            )
        return await self.repository.get_by_application_id(application.id)

    async def get_history_for_officer(self, application_id: uuid.UUID) -> List[ApplicationStatusHistory]:
        """Allows an admission officer to inspect audit trails for any specific tracking ID."""
        return await self.repository.get_by_application_id(application_id)



import uuid

from fastapi import HTTPException, status

from app.models.domain import (
    Application,
    ApplicationStatusHistory,
    ShortlistingPreference,
    Student,
)
from app.models.enums import ApplicationStatus
from app.repositories.application_repository import ApplicationRepository
from app.schemas.application import ApplicationCreateRequest


class ApplicationService:
    def __init__(self, repository: ApplicationRepository):
        self.repository = repository

    # ================================== CREATE STUDENT APPLICATION ==================================
    async def create_student_application(
        self, student: Student, data: ApplicationCreateRequest
    ) -> Application:
        existing = await self.repository.get_by_student_id(student.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An application record is already active for this student account.",
            )

        new_application = Application(
            student_id=student.id,
            total_marks=data.total_marks,
            status=ApplicationStatus.STARTED,
        )

        for pref in data.preferences:
            new_application.preferences.append(
                ShortlistingPreference(
                    branch_id=pref.branch_id, preference_order=pref.preference_order
                )
            )

        new_application.history.append(
            ApplicationStatusHistory(
                old_status=None,
                new_status=ApplicationStatus.STARTED,
                changed_by=f"STUDENT_ID:{student.id}",
            )
        )

        await self.repository.create(new_application)
        return await self.repository.get_by_student_id(student.id)

    # ================================== GET STUDENT APPLICATION ==================================
    async def get_student_application(self, student: Student) -> Application:
        application = await self.repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "No application profile active for this student account.",
            )
        return application

    # ================================== GET APPLICATION BY ID ==================================
    async def get_application_by_id(self, application_id: uuid.UUID) -> Application:
        application = await self.repository.get_with_details(application_id)
        if not application:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Application entry not found."
            )
        return application

    # ================================== UPDATE APPLICATION STATUS ==================================
    async def update_application_status(
        self, application_id: uuid.UUID, new_status: ApplicationStatus, changed_by: str
    ) -> Application:
        application = await self.repository.get_with_details(application_id)
        if not application:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Application entry not found."
            )

        old_status = application.status
        if old_status == new_status:
            return application

        application.status = new_status
        application.history.append(
            ApplicationStatusHistory(
                old_status=old_status, new_status=new_status, changed_by=changed_by
            )
        )
        await self.repository.update(application)
        return await self.repository.get_with_details(application_id)

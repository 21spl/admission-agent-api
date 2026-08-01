import uuid
from typing import List
from fastapi import HTTPException, status
from app.repositories.application_repository import ApplicationRepository
from app.schemas.application import ApplicationCreateRequest
from app.models.domain import Application, ApplicationPreference, ApplicationStatusHistory, Student
from app.models.enums import ApplicationStatus

class ApplicationService:
    def __init__(self, repository: ApplicationRepository):
        self.repository = repository

    async def create_student_application(self, student: Student, data: ApplicationCreateRequest) -> Application:
        # Business Rule Invariant: Ensure the student has not already created an application
        existing = await self.repository.get_by_student_id(student.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An application record is already active for this student account."
            )

        # Build application header model
        new_application = Application(
            student_id=student.id,
            total_marks=data.total_marks,
            status=ApplicationStatus.STARTED.value
        )

        # Build nested application preferences collection mapping
        for pref in data.preferences:
            pref_entity = ApplicationPreference(
                branch_id=pref.branch_id,
                preference_order=pref.preference_order
            )
            new_application.preferences.append(pref_entity)

        # Seed initial status state history log record block
        initial_history = ApplicationStatusHistory(
            old_status="NONE",
            new_status=ApplicationStatus.STARTED.value,
            changed_by=f"STUDENT_ID:{student.id}"
        )
        new_application.history.append(initial_history)

        return await self.repository.create(new_application)

    async def get_student_application(self, student: Student) -> Application:
        application = await self.repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No application profile active for this student account context."
            )
        return application

    async def update_application_status(self, application_id: uuid.UUID, new_status: ApplicationStatus, operator_name: str) -> Application:
        """
        State machine transition manager.
        Pushes a historical state log track entry for database audits.
        """
        application = await self.repository.get_with_details(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application entry not found.")

        old_status = application.status
        if old_status == new_status.value:
            return application

        # Update entity attribute parameters
        application.status = new_status.value

        # Append historical change log block record
        audit_log = ApplicationStatusHistory(
            old_status=old_status,
            new_status=new_status.value,
            changed_by=operator_name
        )
        application.history.append(audit_log)

        return await self.repository.update(application)

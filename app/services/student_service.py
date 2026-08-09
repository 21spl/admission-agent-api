

import uuid

from app.models.domain import Application, Student
from app.repositories.application_repository import ApplicationRepository
from app.repositories.student_repository import StudentRepository


class StudentService:

    def __init__(
        self,
        student_repository: StudentRepository,
        application_repository: ApplicationRepository
        ):
        
        self.student_repository = student_repository
        self.application_repository = application_repository

    async def get_student_application(self, student_id: uuid.UUID) -> Application:
        current_student = await self.student_repository.get_by_id(student_id)
        return current_student.application

    async def get_student_by_id(self, student_id: uuid.UUID) -> Student:
        return await self.student_repository.get_by_id(student_id)
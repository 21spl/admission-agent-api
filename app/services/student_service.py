import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status

from app.core.security import hash_password
from app.models.domain import Application, Student
from app.repositories.application_repository import ApplicationRepository
from app.repositories.student_repository import StudentRepository


class StudentService:
    def __init__(
        self,
        student_repository: StudentRepository,
        application_repository: ApplicationRepository,
    ):

        self.student_repository = student_repository
        self.application_repository = application_repository

    async def create_new_student(
        self,
        name: str,
        email: str,
        password: str,
        phone: str | None,
        date_of_birth: date,
    ) -> Student:
        existing = await self.student_repository.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A student account with email '{email}' already exists.",
            )

        if date_of_birth >= datetime.now(tz=timezone.utc).date():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date of birth must be in the past.",
            )

        student = Student(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            phone=phone,
            date_of_birth=date_of_birth,
        )
        return await self.student_repository.create(student)

    async def get_student_application(self, student_id: uuid.UUID) -> Application:
        current_student = await self.student_repository.get_by_id_with_application(
            student_id
        )

        if not current_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found.",
            )
        return current_student.application

    async def get_student_by_id(self, student_id: uuid.UUID) -> Student:
        return await self.student_repository.get_by_id(student_id)

    async def get_student_by_email(self, email: str) -> Student:
        return await self.student_repository.get_by_email(email)

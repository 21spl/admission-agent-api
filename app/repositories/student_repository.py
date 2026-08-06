# app/repositories/student_repository.py

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Student


class StudentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, student_id: uuid.UUID) -> Optional[Student]:
        result = await self.session.execute(
            select(Student).where(Student.id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Student]:
        # ASSUMPTION: your login/registration flow already normalizes email
        # case somewhere (you mentioned fixing email case sensitivity in
        # login queries earlier) — mirroring that here with .ilike() so this
        # repository is consistent regardless of where it's called from.
        result = await self.session.execute(
            select(Student).where(Student.email.ilike(email))
        )
        return result.scalar_one_or_none()

    async def create(self, student: Student) -> Student:
        self.session.add(student)
        await self.session.flush()
        return student

    async def save(self, student: Student) -> Student:
        await self.session.flush()
        return student

    async def delete(self, student: Student) -> None:
        await self.session.delete(student)
        await self.session.flush()
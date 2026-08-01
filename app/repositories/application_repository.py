import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.repositories.base_repository import BaseRepository
from app.models.domain import Application

class ApplicationRepository(BaseRepository[Application]):
    def __init__(self, db):
        super().__init__(Application, db)

    async def get_by_student_id(self, student_id: uuid.UUID) -> Optional[Application]:
        """Fetches an existing application record complete with eagerly pre-fetched preferences."""
        stmt = (
            select(Application)
            .where(Application.student_id == student_id)
            .options(selectinload(Application.preferences))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_details(self, application_id: uuid.UUID) -> Optional[Application]:
        """Eagerly resolves all nested collections for downstream multi-agent pipeline tasks."""
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(
                selectinload(Application.preferences),
                selectinload(Application.documents),
                selectinload(Application.history)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()




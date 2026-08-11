import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, entity: T) -> T:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def get_by_id(self, id: uuid.UUID) -> T | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))  # type: ignore
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update(self, entity: T) -> T:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

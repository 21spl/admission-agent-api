import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Branch
from app.repositories.base_repository import BaseRepository


class BranchRepository(BaseRepository[Branch]):
    def __init__(self, db: AsyncSession):
        super().__init__(Branch, db)

    async def get_by_code(self, code: str) -> Branch | None:
        """Fetches a branch by code string for uniqueness validation loops."""
        result = await self.db.execute(select(Branch).where(Branch.code == code))
        return result.scalar_one_or_none()

    async def decrement_available_seats(self, branch_id: uuid.UUID) -> bool:
        """
        Concurrency-safe seat allocation update primitive.
        Decrements target value strictly if available_seats > 0.
        """
        stmt = (
            update(Branch)
            .where(Branch.id == branch_id)
            .where(Branch.available_seats > 0)
            .values(available_seats=Branch.available_seats - 1)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def increment_available_seats(self, branch_id: uuid.UUID) -> None:
        """Atomically returns an open seat slot capacity back to the track."""
        stmt = (
            update(Branch)
            .where(Branch.id == branch_id)
            .values(available_seats=Branch.available_seats + 1)
        )
        await self.db.execute(stmt)
        await self.db.commit()

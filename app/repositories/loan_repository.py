import uuid
from typing import Optional
from sqlalchemy import select
from app.repositories.base_repository import BaseRepository
from app.models.domain import LoanApplication

import uuid
from typing import Optional

from sqlalchemy import select

from app.models.domain import LoanApplication
from app.repositories.base_repository import BaseRepository


class LoanRepository(BaseRepository[LoanApplication]):
    def __init__(self, db):
        super().__init__(LoanApplication, db)

    async def get_by_application_id(self, application_id: uuid.UUID) -> Optional[LoanApplication]:
        """Fetches the loan decision for a given application, if one has been made."""
        stmt = select(LoanApplication).where(LoanApplication.application_id == application_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

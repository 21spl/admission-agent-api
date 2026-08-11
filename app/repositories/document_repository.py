import uuid

from sqlalchemy import select

from app.models.domain import Document
from app.models.enums import DocumentType
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db):
        super().__init__(Document, db)

    async def get_by_application_id(self, application_id: uuid.UUID) -> list[Document]:
        """Fetches all documents linked to a specific application."""
        stmt = select(Document).where(Document.application_id == application_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(
        self, application_id: uuid.UUID, doc_type: DocumentType
    ) -> Document | None:
        """Looks up a specific document type within an application to check for overwrites."""
        stmt = (
            select(Document)
            .where(Document.application_id == application_id)
            .where(Document.doc_type == doc_type)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

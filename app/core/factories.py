from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.branch_repository import BranchRepository
from app.services.branch_service import BranchService

def get_branch_service(db: AsyncSession = Depends(get_db)) -> BranchService:
    """Dependency Injection provider function returning mapped service nodes."""
    return BranchService(BranchRepository(db))

def get_branch_repository(db: AsyncSession = Depends(get_db)) -> BranchRepository:
    """Dependency Injection provider function returning mapped repository nodes."""
    return BranchRepository(db)

from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService

def get_application_service(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(ApplicationRepository(db))

def get_application_repository(db: AsyncSession = Depends(get_db)) -> ApplicationRepository:
    return ApplicationRepository(db)

from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.core.factories import get_application_service
from app.repositories.application_repository import ApplicationRepository

def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(
        repository=DocumentRepository(db),
        application_repository=ApplicationRepository(db),
        application_service=get_application_service(db)
    )


from app.repositories.offer_repository import OfferRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.application_repository import ApplicationRepository
from app.core.factories import get_application_service
from app.services.offer_service import OfferService

def get_offer_service(db: AsyncSession = Depends(get_db)) -> OfferService:
    return OfferService(
        repository=OfferRepository(db),
        branch_repository=BranchRepository(db),
        application_repository=ApplicationRepository(db),
        application_service=get_application_service(db)
    )

from app.repositories.application_history_repository import ApplicationStatusHistoryRepository
from app.repositories.application_repository import ApplicationRepository
from app.services.application_history_service import ApplicationHistoryService

def get_application_history_service(db: AsyncSession = Depends(get_db)) -> ApplicationHistoryService:
    return ApplicationHistoryService(
        repository=ApplicationStatusHistoryRepository(db),
        application_repository=ApplicationRepository(db)
    )


from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService

def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))



from app.repositories.loan_repository import LoanRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository
from app.services.loan_service import LoanService

def get_loan_service(db: AsyncSession = Depends(get_db)) -> LoanService:
    return LoanService(
        repository=LoanRepository(db),
        application_repository=ApplicationRepository(db),
        document_repository=DocumentRepository(db)
    )


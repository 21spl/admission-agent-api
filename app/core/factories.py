from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.repositories.branch_repository import BranchRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.offer_repository import OfferRepository
from app.repositories.application_history_repository import ApplicationStatusHistoryRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.loan_repository import LoanRepository

from app.services.branch_service import BranchService
from app.services.application_service import ApplicationService
from app.services.document_service import DocumentService
from app.services.offer_service import OfferService
from app.services.application_history_service import ApplicationHistoryService
from app.services.notification_service import NotificationService
from app.services.loan_service import LoanService
from app.services.admin_review_service import AdminReviewService
from app.services.shortlisting.shortlisting_service import ShortlistingService


# =================================== REPOSITORIES =====================================

def get_branch_repository(db: AsyncSession = Depends(get_db)) -> BranchRepository:
    return BranchRepository(db)


def get_student_repository(db: AsyncSession = Depends(get_db)) -> StudentRepository:
    return StudentRepository(db)


def get_application_repository(db: AsyncSession = Depends(get_db)) -> ApplicationRepository:
    return ApplicationRepository(db)


# =================================== SERVICES =====================================

def get_branch_service(db: AsyncSession = Depends(get_db)) -> BranchService:
    return BranchService(BranchRepository(db))


def get_application_service(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(ApplicationRepository(db))


def get_application_history_service(db: AsyncSession = Depends(get_db)) -> ApplicationHistoryService:
    return ApplicationHistoryService(
        repository=ApplicationStatusHistoryRepository(db),
        application_repository=ApplicationRepository(db),
    )


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


def get_document_service(
    db: AsyncSession = Depends(get_db),
    application_service: ApplicationService = Depends(get_application_service),
    application_history_service: ApplicationHistoryService = Depends(get_application_history_service),
) -> DocumentService:
    return DocumentService(
        repository=DocumentRepository(db),
        application_repository=ApplicationRepository(db),
        application_service=application_service,
        application_history_service=application_history_service,
    )


def get_offer_service(
    db: AsyncSession = Depends(get_db),
    application_service: ApplicationService = Depends(get_application_service),
    application_history_service: ApplicationHistoryService = Depends(get_application_history_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> OfferService:
    return OfferService(
        repository=OfferRepository(db),
        branch_repository=BranchRepository(db),
        application_repository=ApplicationRepository(db),
        application_service=application_service,
        application_history_service=application_history_service,
        notification_service=notification_service,
    )


def get_loan_service(db: AsyncSession = Depends(get_db)) -> LoanService:
    return LoanService(
        repository=LoanRepository(db),
        application_repository=ApplicationRepository(db),
        document_repository=DocumentRepository(db),
    )


def get_admin_review_service(db: AsyncSession = Depends(get_db)) -> AdminReviewService:
    return AdminReviewService(ApplicationRepository(db), DocumentRepository(db))


def get_shortlisting_service(
    db: AsyncSession = Depends(get_db),
    application_history_service: ApplicationHistoryService = Depends(get_application_history_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> ShortlistingService:
    return ShortlistingService(db, application_history_service, notification_service)
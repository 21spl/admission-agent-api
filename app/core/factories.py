from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.application_history_repository import (
    ApplicationStatusHistoryRepository,
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.notification_repository import NotificationLogRepository
from app.repositories.offer_repository import OfferRepository
from app.repositories.shortlisting_preference_repository import (
    ShortlistingPreferenceRepository,
)
from app.repositories.student_repository import StudentRepository
from app.services.admin_review_service import AdminReviewService
from app.services.application_history_service import ApplicationHistoryService
from app.services.application_service import ApplicationService
from app.services.branch_service import BranchService
from app.services.document_service import DocumentService
from app.services.loan_service import LoanService
from app.services.mail_service import MailService
from app.services.notification_service import NotificationService
from app.services.offer_service import OfferService
from app.services.shortlisting.shortlisting_service import ShortlistingService
from app.services.student_service import StudentService


# ================================== REPOSITORIES ====================================
def get_application_history_repository(db: AsyncSession = Depends(get_db)) -> ApplicationStatusHistoryRepository:  # noqa: B008
    return ApplicationStatusHistoryRepository(db)

def get_application_repository(db: AsyncSession = Depends(get_db)) -> ApplicationRepository:  # noqa: B008
    return ApplicationRepository(db)


def get_branch_repository(db: AsyncSession = Depends(get_db)) -> BranchRepository:  # noqa: B008
    return BranchRepository(db)

def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:  # noqa: B008
    return DocumentRepository(db)

def get_offer_repository(db: AsyncSession = Depends(get_db)) -> OfferRepository:  # noqa: B008
    return OfferRepository(db)

def get_notification_repository(db: AsyncSession = Depends(get_db)) -> NotificationLogRepository:  # noqa: B008
    return NotificationLogRepository(db)

def get_loan_repository(db: AsyncSession = Depends(get_db)) -> LoanRepository:  # noqa: B008
    return LoanRepository(db)

def get_shortlisting_preference_repository(db: AsyncSession = Depends(get_db)) -> ShortlistingPreferenceRepository:  # noqa: B008
    return ShortlistingPreferenceRepository(db)

def get_student_repository(db: AsyncSession = Depends(get_db)) -> StudentRepository:  # noqa: B008
    return StudentRepository(db)

    



# =================================== SERVICES =====================================

def get_branch_service(db: AsyncSession = Depends(get_db)) -> BranchService:
    return BranchService(BranchRepository(db))

#================================== GET APPLICATION SERVICE ================================
def get_application_service(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(ApplicationRepository(db))

#================================== GET APPLICATION HISTORY SERVICE ================================
def get_application_history_service(db: AsyncSession = Depends(get_db)) -> ApplicationHistoryService:
    return ApplicationHistoryService(
        repository=ApplicationStatusHistoryRepository(db),
        application_repository=ApplicationRepository(db),
    )

#================================== GET NOTIFICATION SERVICE ================================
def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationLogRepository(db))


#================================== GET DOCUMENT SERVICE ================================
def get_document_service(
    db: AsyncSession = Depends(get_db),
    application_service: ApplicationService = Depends(get_application_service),
) -> DocumentService:
    return DocumentService(
        repository=DocumentRepository(db),
        application_repository=ApplicationRepository(db),
        application_service=application_service,
    )


#================================== GET OFFER SERVICE ================================

def get_offer_service(
    db: AsyncSession = Depends(get_db),
    application_service: ApplicationService = Depends(get_application_service),
) -> OfferService:
    return OfferService(
        db,
        offer_repository=OfferRepository(db),
        application_repository=ApplicationRepository(db),
        application_service=application_service,
        preference_repository=ShortlistingPreferenceRepository(db),
    )


# ============================ GET LOAN SERVICE ===========================================
def get_loan_service(db: AsyncSession = Depends(get_db)) -> LoanService:
    return LoanService(
        loan_repository=LoanRepository(db),
        application_repository=ApplicationRepository(db),
        document_repository=DocumentRepository(db),
    )

# ================================== GET ADMIN REVIEW SERVICE ================================
def get_admin_review_service(
    db: AsyncSession = Depends(get_db),
    application_service: ApplicationService = Depends(get_application_service)
) -> AdminReviewService:
    return AdminReviewService(ApplicationRepository(db), application_service, DocumentRepository(db))


# ================================== GET MAIL SERVICE ================================
def get_mail_service(db: AsyncSession = Depends(get_db), notification_service: NotificationService = Depends(get_notification_service)) -> MailService:
    return MailService(db, notification_service)

# ================================== GET SHORTLISTING SERVICE ================================
def get_shortlisting_service(db: AsyncSession = Depends(get_db), mail_service: MailService = Depends(get_mail_service)) -> ShortlistingService:
    return ShortlistingService(db, mail_service)



def get_student_service(db: AsyncSession = Depends(get_db)) -> StudentService:
    return StudentService(StudentRepository(db), ApplicationRepository(db))




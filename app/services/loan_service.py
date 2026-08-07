import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status

# import repository
from app.repositories.loan_repository import LoanRepository
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository

# import schemas
from app.schemas.loan import LoanApplicationCreateRequest, LoanStatusUpdateRequest
# import models
from app.models.domain import LoanApplication, Student
from app.models.enums import LoanStatus, DocumentType

class LoanService:
    def __init__(
        self, 
        repository: LoanRepository,
        application_repository: ApplicationRepository,
        document_repository: DocumentRepository
    ):
        self.repository = repository
        self.application_repository = application_repository
        self.document_repository = document_repository

    #================================ APPLY FOR STUDENT LOAN ==================================

    async def apply_for_student_loan(self, student: Student, data: LoanApplicationCreateRequest) -> LoanApplication:
        """Validates parent states and instantiates a unique structural loan application tracking sub-entity."""
        # 1. Look up student application envelope mapping bounds
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application header records not found.")

        # 2. Check if a loan process sub-entity has already been established
        existing_loan = await self.repository.get_by_application_id(application.id)
        if existing_loan and existing_loan.status != LoanStatus.NOT_REQUESTED.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A student loan request process is already active.")

        # 3. Verify target income verification file linkage properties match constraints
        doc = await self.document_repository.get_by_id(data.income_certificate_doc_id)
        if not doc or doc.application_id != application.id or doc.doc_type != DocumentType.INCOME_CERTIFICATE.value:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Target document link is invalid or not an income certificate.")

        if existing_loan:
            existing_loan.income_certificate_doc_id = data.income_certificate_doc_id
            existing_loan.status = LoanStatus.PENDING.value
            existing_loan.decided_at = None
            return await self.repository.update(existing_loan)

        new_loan = LoanApplication(
            application_id=application.id,
            income_certificate_doc_id=data.income_certificate_doc_id,
            status=LoanStatus.PENDING.value
        )
        return await self.repository.create(new_loan)

    # ================================ GET LOAN BY STUDENT ==================================

    async def get_loan_by_student(self, student: Student) -> LoanApplication:
        application = await self.application_repository.get_by_student_id(student.id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application records missing.")
        
        loan = await self.repository.get_by_application_id(application.id)
        if not loan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No student loan records created for this account.")
        return loan

    #================================= EVALUATE LOAN APPLICATION ==================================

    async def evaluate_loan_application(self, loan_id: uuid.UUID, data: LoanStatusUpdateRequest) -> LoanApplication:
        loan = await self.repository.get_by_id(loan_id)
        if not loan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target loan tracking record index missing.")

        if data.status not in [LoanStatus.APPROVED, LoanStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported loan decision status."
            )

        loan.status = data.status.value
        loan.decided_at = datetime.now(timezone.utc)
        return await self.repository.update(loan)



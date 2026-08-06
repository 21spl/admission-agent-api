# app/models/domain.py

import uuid
from datetime import datetime, timezone, date
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Date, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

# now we import all the enums
from app.models.enums import (
    OfficerRole, ApplicationStatus, DocumentType, 
    ValidationStatus, OfferStatus, NotificationType, 
    NotificationStatus, LoanStatus, AllowedFileType
)

# Shared timestamp helper mapping to ensure clean system audit generation
def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    # Spring-style cascade mapping relationships
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="student", cascade="all, delete-orphan")


class Officer(Base):
    __tablename__ = "officers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
    Enum(OfficerRole, name="officer_role", values_callable=lambda x: [e.value for e in x]),
    default=OfficerRole.ADMISSION_OFFICER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    cutoff_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), unique=True, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
    Enum(ApplicationStatus, name="application_status", values_callable=lambda x: [e.value for e in x]),
    default=ApplicationStatus.STARTED, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    validation_flags: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    validation_issues: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="application")
    preferences: Mapped[List["ApplicationPreference"]] = relationship("ApplicationPreference", back_populates="application", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    offers: Mapped[List["Offer"]] = relationship("Offer", back_populates="application", cascade="all, delete-orphan")
    history: Mapped[List["ApplicationStatusHistory"]] = relationship("ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan")
    loan_application: Mapped[Optional["LoanApplication"]] = relationship("LoanApplication", back_populates="application", cascade="all, delete-orphan")


class ApplicationPreference(Base):
    __tablename__ = "application_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    preference_order: Mapped[int] = mapped_column(Integer, nullable=False)

    application: Mapped["Application"] = relationship("Application", back_populates="preferences")
    
    # Enforces normalization layout—prevents a student from setting identical ranks or branch duplication
    __table_args__ = (
        UniqueConstraint('application_id', 'preference_order', name='uq_application_pref_order'),
        UniqueConstraint('application_id', 'branch_id', name='uq_application_branch'),
    )


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    doc_type: Mapped[str] = mapped_column(
        Enum(DocumentType, name="document_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(
        Enum(AllowedFileType, name="allowed_file_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_status: Mapped[str] = mapped_column(
        Enum(ValidationStatus, name="validation_status", values_callable=lambda x: [e.value for e in x]),
        default=ValidationStatus.PENDING
    )
    validation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    application: Mapped["Application"] = relationship("Application", back_populates="documents")



class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    status: Mapped[str] = mapped_column(
    Enum(OfferStatus, name="offer_status", values_callable=lambda x: [e.value for e in x]),
    default=OfferStatus.PENDING, index=True)
    
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    application: Mapped["Application"] = relationship("Application", back_populates="offers")


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    old_status: Mapped[str] = mapped_column(
    Enum(ApplicationStatus, name="application_status", values_callable=lambda x: [e.value for e in x]),
    nullable=False)
    new_status: Mapped[str] = mapped_column(
    Enum(ApplicationStatus, name="application_status", values_callable=lambda x: [e.value for e in x]),
    nullable=False)
    changed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # e.g., 'SYSTEM' or Officer UUID string
    
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    application: Mapped["Application"] = relationship("Application", back_populates="history")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[str] = mapped_column(
    Enum(NotificationType, name="notification_type", values_callable=lambda x: [e.value for e in x]),
    nullable=False)
    status: Mapped[str] = mapped_column(
    Enum(NotificationStatus, name="notification_status", values_callable=lambda x: [e.value for e in x]),
    default=NotificationStatus.SENT)
    
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), unique=True, nullable=False)
    income_certificate_doc_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    status: Mapped[str] = mapped_column(
    Enum(LoanStatus, name="loan_status", values_callable=lambda x: [e.value for e in x]),
    default=LoanStatus.NOT_REQUESTED)
    
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="loan_application")

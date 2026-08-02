"""convert doc_type, status history, and notification columns to enums

Revision ID: 9c1315902377
Revises: 8b5da9329247
Create Date: 2026-08-02 09:50:36.589834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '9c1315902377'
down_revision: Union[str, Sequence[str], None] = '8b5da9329247'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


application_status_enum = postgresql.ENUM(
    'STARTED', 'SUBMITTED', 'DOCS_PENDING', 'DOCS_VALIDATED', 'DOCS_INVALID',
    'OFFER_MADE', 'OFFER_ACCEPTED', 'OFFER_REJECTED', 'OFFER_EXPIRED',
    'WAITLISTED', 'REJECTED',
    name='application_status',
    create_type=False,  # already exists — never create/drop it here
)
document_type_enum = postgresql.ENUM(
    'CLASS12_MARKSHEET', 'ID_CARD', 'INCOME_CERTIFICATE', 'OTHER',
    name='document_type',
)
notification_type_enum = postgresql.ENUM(
    'SHORTLIST_OFFER', 'LOAN_APPROVAL', 'WAITLIST_UPDATE', 'REJECTION',
    name='notification_type',
)
notification_status_enum = postgresql.ENUM(
    'SENT', 'FAILED',
    name='notification_status',
)


def upgrade() -> None:
    # Create the three genuinely new enum types
    document_type_enum.create(op.get_bind(), checkfirst=True)
    notification_type_enum.create(op.get_bind(), checkfirst=True)
    notification_status_enum.create(op.get_bind(), checkfirst=True)

    # Clean up legacy sentinel value before casting old_status to enum
    op.execute("UPDATE application_status_history SET old_status = NULL WHERE old_status = 'NONE'")

    op.alter_column(
        'application_status_history', 'old_status',
        existing_type=sa.VARCHAR(length=50),
        type_=application_status_enum,
        postgresql_using='old_status::application_status',
        nullable=True,
    )
    op.alter_column(
        'application_status_history', 'new_status',
        existing_type=sa.VARCHAR(length=50),
        type_=application_status_enum,
        postgresql_using='new_status::application_status',
        existing_nullable=False,
    )
    op.alter_column(
        'documents', 'doc_type',
        existing_type=sa.VARCHAR(length=50),
        type_=document_type_enum,
        postgresql_using='doc_type::document_type',
        existing_nullable=False,
    )
    op.alter_column(
        'notification_logs', 'type',
        existing_type=sa.VARCHAR(length=50),
        type_=notification_type_enum,
        postgresql_using='"type"::notification_type',
        existing_nullable=False,
    )
    op.alter_column(
        'notification_logs', 'status',
        existing_type=sa.VARCHAR(length=50),
        type_=notification_status_enum,
        postgresql_using='status::notification_status',
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'notification_logs', 'status',
        existing_type=notification_status_enum,
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        'notification_logs', 'type',
        existing_type=notification_type_enum,
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        'documents', 'doc_type',
        existing_type=document_type_enum,
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        'application_status_history', 'new_status',
        existing_type=application_status_enum,
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        'application_status_history', 'old_status',
        existing_type=application_status_enum,
        type_=sa.VARCHAR(length=50),
        nullable=False,
    )
    op.execute("UPDATE application_status_history SET old_status = 'NONE' WHERE old_status IS NULL")

    # Only drop the three new types — application_status predates this migration
    notification_status_enum.drop(op.get_bind(), checkfirst=True)
    notification_type_enum.drop(op.get_bind(), checkfirst=True)
    document_type_enum.drop(op.get_bind(), checkfirst=True)
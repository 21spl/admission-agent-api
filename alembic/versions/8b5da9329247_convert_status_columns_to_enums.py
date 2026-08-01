"""convert_status_columns_to_enums

Revision ID: 8b5da9329247
Revises: b83ce111335b
Create Date: 2026-08-01 09:43:09.395023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b5da9329247'
down_revision: Union[str, Sequence[str], None] = 'b83ce111335b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### create enum types explicitly first ###
    application_status_enum = sa.Enum(
        'STARTED', 'SUBMITTED', 'DOCS_PENDING', 'DOCS_VALIDATED', 'DOCS_INVALID',
        'OFFER_MADE', 'OFFER_ACCEPTED', 'OFFER_REJECTED', 'OFFER_EXPIRED',
        'WAITLISTED', 'REJECTED', name='application_status'
    )
    validation_status_enum = sa.Enum('PENDING', 'VALID', 'INVALID', name='validation_status')
    loan_status_enum = sa.Enum('NOT_REQUESTED', 'PENDING', 'APPROVED', 'REJECTED', name='loan_status')
    offer_status_enum = sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', name='offer_status')
    officer_role_enum = sa.Enum('ADMISSION_OFFICER', 'ADMIN', name='officer_role')

    bind = op.get_bind()
    application_status_enum.create(bind)
    validation_status_enum.create(bind)
    loan_status_enum.create(bind)
    offer_status_enum.create(bind)
    officer_role_enum.create(bind)

    # ### alter columns with explicit USING casts ###
    op.alter_column('applications', 'status',
        existing_type=sa.VARCHAR(length=50),
        type_=application_status_enum,
        existing_nullable=False,
        postgresql_using='status::application_status')

    op.alter_column('documents', 'validation_status',
        existing_type=sa.VARCHAR(length=50),
        type_=validation_status_enum,
        existing_nullable=False,
        postgresql_using='validation_status::validation_status')

    op.alter_column('loan_applications', 'status',
        existing_type=sa.VARCHAR(length=50),
        type_=loan_status_enum,
        existing_nullable=False,
        postgresql_using='status::loan_status')

    op.alter_column('offers', 'status',
        existing_type=sa.VARCHAR(length=50),
        type_=offer_status_enum,
        existing_nullable=False,
        postgresql_using='status::offer_status')

    op.alter_column('officers', 'role',
        existing_type=sa.VARCHAR(length=50),
        type_=officer_role_enum,
        existing_nullable=False,
        postgresql_using='role::officer_role')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('officers', 'role',
        existing_type=sa.Enum('ADMISSION_OFFICER', 'ADMIN', name='officer_role'),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False)

    op.alter_column('offers', 'status',
        existing_type=sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', name='offer_status'),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False)

    op.alter_column('loan_applications', 'status',
        existing_type=sa.Enum('NOT_REQUESTED', 'PENDING', 'APPROVED', 'REJECTED', name='loan_status'),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False)

    op.alter_column('documents', 'validation_status',
        existing_type=sa.Enum('PENDING', 'VALID', 'INVALID', name='validation_status'),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False)

    op.alter_column('applications', 'status',
        existing_type=sa.Enum('STARTED', 'SUBMITTED', 'DOCS_PENDING', 'DOCS_VALIDATED', 'DOCS_INVALID',
                               'OFFER_MADE', 'OFFER_ACCEPTED', 'OFFER_REJECTED', 'OFFER_EXPIRED',
                               'WAITLISTED', 'REJECTED', name='application_status'),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False)

    bind = op.get_bind()
    sa.Enum(name='application_status').drop(bind)
    sa.Enum(name='validation_status').drop(bind)
    sa.Enum(name='loan_status').drop(bind)
    sa.Enum(name='offer_status').drop(bind)
    sa.Enum(name='officer_role').drop(bind)


    
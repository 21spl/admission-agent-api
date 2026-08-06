"""add validated and pending_review to application_status enum

Revision ID: 4fe002e24b0a
Revises: 69ca23eb0a26
Create Date: 2026-08-06 18:02:18.299799

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fe002e24b0a'
down_revision: Union[str, Sequence[str], None] = '69ca23eb0a26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'VALIDATED'")
    op.execute("ALTER TYPE application_status ADD VALUE IF NOT EXISTS 'PENDING_REVIEW'")


def downgrade() -> None:
    # Postgres doesn't support dropping enum values directly.
    # A real downgrade would require recreating the type without these values
    # and migrating any rows using them — skip unless actually needed.
    pass
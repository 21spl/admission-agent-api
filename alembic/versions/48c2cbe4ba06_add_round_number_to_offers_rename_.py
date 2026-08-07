"""add round_number to offers, rename application_preferences table

Revision ID: 48c2cbe4ba06
Revises: 4fe002e24b0a
Create Date: 2026-08-07 09:56:36.179295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48c2cbe4ba06'
down_revision: Union[str, Sequence[str], None] = '4fe002e24b0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # rename instead of drop/create -> preserves data + underlying FK/PK objects
    op.rename_table('application_preferences', 'shortlisting_preferences')

    # add nullable first, backfill, THEN enforce not-null -> avoids failing
    # on any existing rows in offers
    op.add_column('offers', sa.Column('round_number', sa.Integer(), nullable=True))
    op.execute("UPDATE offers SET round_number = 1 WHERE round_number IS NULL")
    op.alter_column('offers', 'round_number', nullable=False)

    op.create_index(op.f('ix_offers_round_number'), 'offers', ['round_number'], unique=False)
    op.create_unique_constraint('uq_offer_application_round', 'offers', ['application_id', 'round_number'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_offer_application_round', 'offers', type_='unique')
    op.drop_index(op.f('ix_offers_round_number'), table_name='offers')
    op.drop_column('offers', 'round_number')

    op.rename_table('shortlisting_preferences', 'application_preferences')
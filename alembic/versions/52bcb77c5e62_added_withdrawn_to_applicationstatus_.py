"""added WITHDRAWN to ApplicationStatus enum

Revision ID: 52bcb77c5e62
Revises: cf022ca7a972
Create Date: 2026-08-07 17:15:02.821792

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "52bcb77c5e62"
down_revision: str | Sequence[str] | None = "cf022ca7a972"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE application_status ADD VALUE 'WITHDRAWN'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres doesn't support removing a value from an enum type directly.
    # A real downgrade would require creating a new enum type without
    # WITHDRAWN, migrating the column over, dropping the old type, and
    # renaming the new one in its place — destructive if any row is
    # currently WITHDRAWN. Left as a no-op; only build the full teardown if
    # you actually need to roll back past this revision.

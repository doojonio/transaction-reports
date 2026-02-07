"""Transaction date indexes

Revision ID: 430dad917dda
Revises: 16fb8c3675b4
Create Date: 2026-02-07 18:57:59.966892

"""

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "430dad917dda"
down_revision: Union[str, Sequence[str], None] = "16fb8c3675b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("idx_transactions_date", "transactions", [text("DATE(created_at)")])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_transactions_date", "transactions")

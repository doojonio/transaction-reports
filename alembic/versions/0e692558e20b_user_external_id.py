"""User external id

Revision ID: 0e692558e20b
Revises: 430dad917dda
Create Date: 2026-02-08 14:07:42.334677

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0e692558e20b"
down_revision: Union[str, Sequence[str], None] = "430dad917dda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("external_id", sa.Integer(), nullable=True))
    op.execute("""
        CREATE SEQUENCE users_external_id_seq OWNED BY users.external_id;
    """)
    # set default to nextval
    op.execute("""
        UPDATE users SET external_id = nextval('users_external_id_seq');
    """)
    op.execute("""
        SELECT setval('users_external_id_seq', (SELECT MAX(external_id) FROM users));
    """)
    op.alter_column(
        "users",
        "external_id",
        server_default=sa.text("nextval('users_external_id_seq')"),
        nullable=False,
    )
    op.create_index("ix_users_external_id", "users", ["external_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "external_id")

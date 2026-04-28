"""add conv last read at

Revision ID: a1f8c4b9e203
Revises: 39120275dc23
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1f8c4b9e203"
# Re-chain after seed colleges migration to keep the Alembic graph linear.
down_revision: Union[str, Sequence[str], None] = "39120275dc23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("last_read_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("conversations", "last_read_at")

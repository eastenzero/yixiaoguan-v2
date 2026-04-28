"""add conv last read at

Revision ID: a1f8c4b9e203
Revises: c4a81b9d1e21
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1f8c4b9e203"
down_revision: Union[str, Sequence[str], None] = "c4a81b9d1e21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("last_read_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("conversations", "last_read_at")

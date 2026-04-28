"""backfill conv last read at

Revision ID: b2e7a91c4d80
Revises: a1f8c4b9e203
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2e7a91c4d80"
down_revision: Union[str, Sequence[str], None] = "a1f8c4b9e203"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE conversations "
            "SET last_read_at = updated_at "
            "WHERE last_read_at IS NULL"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE conversations SET last_read_at = NULL"))

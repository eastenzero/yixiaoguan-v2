"""add chat_analytics cost columns

Revision ID: 11f120f3ef96
Revises: 3fd32d018c9c
Create Date: 2026-05-08 18:14:25.053473

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "11f120f3ef96"
down_revision: Union[str, Sequence[str], None] = "3fd32d018c9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_analytics", sa.Column("prompt_tokens", sa.Integer(), nullable=True))
    op.add_column("chat_analytics", sa.Column("completion_tokens", sa.Integer(), nullable=True))
    op.add_column("chat_analytics", sa.Column("total_tokens", sa.Integer(), nullable=True))
    op.add_column("chat_analytics", sa.Column("prompt_price", sa.Numeric(10, 7), nullable=True))
    op.add_column("chat_analytics", sa.Column("completion_price", sa.Numeric(10, 7), nullable=True))
    op.add_column("chat_analytics", sa.Column("total_price", sa.Numeric(10, 7), nullable=True))
    op.add_column("chat_analytics", sa.Column("currency", sa.String(10), nullable=True))
    op.add_column("chat_analytics", sa.Column("latency", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_analytics", "latency")
    op.drop_column("chat_analytics", "currency")
    op.drop_column("chat_analytics", "total_price")
    op.drop_column("chat_analytics", "completion_price")
    op.drop_column("chat_analytics", "prompt_price")
    op.drop_column("chat_analytics", "total_tokens")
    op.drop_column("chat_analytics", "completion_tokens")
    op.drop_column("chat_analytics", "prompt_tokens")

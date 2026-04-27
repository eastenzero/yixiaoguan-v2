"""colleges add campus

Revision ID: b4592e64bdd6
Revises: c4a81b9d1e21
Create Date: 2026-04-27 20:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b4592e64bdd6"
down_revision: Union[str, Sequence[str], None] = "c4a81b9d1e21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("colleges", sa.Column("campus", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("colleges", "campus")

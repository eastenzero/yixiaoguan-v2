"""r08 scope publish

Revision ID: c4a81b9d1e21
Revises: 7c7a6f2c4d11
Create Date: 2026-04-21 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4a81b9d1e21"
down_revision: Union[str, Sequence[str], None] = "7c7a6f2c4d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    knowledgescope = sa.Enum("class", "college", "global", name="knowledgescope")
    knowledgescope.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "kb_suggestions",
        sa.Column("scope", knowledgescope, nullable=False, server_default="college"),
    )
    op.add_column("kb_suggestions", sa.Column("scope_value", sa.Integer(), nullable=True))
    op.add_column("kb_suggestions", sa.Column("representative_query", sa.Text(), nullable=False, server_default=""))
    op.add_column("kb_suggestions", sa.Column("question_hash", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("kb_suggestions", sa.Column("reject_reason", sa.Text(), nullable=True))
    op.add_column("kb_suggestions", sa.Column("published_at", sa.DateTime(), nullable=True))

    op.alter_column("kb_suggestions", "scope", server_default=None)
    op.alter_column("kb_suggestions", "representative_query", server_default=None)
    op.alter_column("kb_suggestions", "question_hash", server_default=None)


def downgrade() -> None:
    op.drop_column("kb_suggestions", "published_at")
    op.drop_column("kb_suggestions", "reject_reason")
    op.drop_column("kb_suggestions", "question_hash")
    op.drop_column("kb_suggestions", "representative_query")
    op.drop_column("kb_suggestions", "scope_value")
    op.drop_column("kb_suggestions", "scope")

    knowledgescope = sa.Enum("class", "college", "global", name="knowledgescope")
    knowledgescope.drop(op.get_bind(), checkfirst=True)

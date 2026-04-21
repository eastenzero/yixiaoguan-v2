"""add chat_analytics

Revision ID: 7c7a6f2c4d11
Revises: ff1f0ab0c5f8
Create Date: 2026-04-21 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7c7a6f2c4d11"
down_revision: Union[str, Sequence[str], None] = "ff1f0ab0c5f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_analytics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_college_id", sa.Integer(), nullable=True),
        sa.Column("user_class_id", sa.Integer(), nullable=True),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column("query_norm", sa.String(length=255), nullable=True),
        sa.Column("rag_score", sa.Float(), nullable=True),
        sa.Column("kb_doc_matched", sa.String(length=512), nullable=True),
        sa.Column("is_answered", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["user_class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["user_college_id"], ["colleges.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_chat_analytics_unanswered",
        "chat_analytics",
        ["is_answered", sa.text("created_at DESC")],
        unique=False,
        postgresql_where=sa.text("is_answered = FALSE"),
    )
    op.create_index(
        "idx_chat_analytics_college",
        "chat_analytics",
        ["user_college_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_chat_analytics_class",
        "chat_analytics",
        ["user_class_id", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_chat_analytics_class", table_name="chat_analytics")
    op.drop_index("idx_chat_analytics_college", table_name="chat_analytics")
    op.drop_index("idx_chat_analytics_unanswered", table_name="chat_analytics")
    op.drop_table("chat_analytics")

"""add r11 pilot tables

Revision ID: 3fd32d018c9c
Revises: b2e7a91c4d80
Create Date: 2026-05-08 18:02:33.307378

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3fd32d018c9c"
down_revision: Union[str, Sequence[str], None] = "b2e7a91c4d80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("contact", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=32), server_default=sa.text("'general'"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_feedbacks_created",
        "feedbacks",
        [sa.text("created_at DESC")],
        unique=False,
    )

    op.create_table(
        "unanswered_user_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_provided_college_id", sa.Integer(), nullable=True),
        sa.Column("user_provided_grade", sa.String(length=16), nullable=True),
        sa.Column("user_provided_category", sa.String(length=32), nullable=True),
        sa.Column("user_provided_note", sa.Text(), nullable=True),
        sa.Column("unanswered_question_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["unanswered_question_id"], ["unanswered_questions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_provided_college_id"], ["colleges.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_uuf_question",
        "unanswered_user_feedback",
        ["unanswered_question_id"],
        unique=False,
    )
    op.create_index(
        "idx_uuf_created",
        "unanswered_user_feedback",
        [sa.text("created_at DESC")],
        unique=False,
    )

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("props", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("client_ts", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_events_user_day",
        "events",
        ["user_id", sa.text("date(created_at)")],
        unique=False,
    )
    op.create_index(
        "idx_events_name_day",
        "events",
        ["event_name", sa.text("date(created_at)")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_events_name_day", table_name="events")
    op.drop_index("idx_events_user_day", table_name="events")
    op.drop_table("events")

    op.drop_index("idx_uuf_created", table_name="unanswered_user_feedback")
    op.drop_index("idx_uuf_question", table_name="unanswered_user_feedback")
    op.drop_table("unanswered_user_feedback")

    op.drop_index("idx_feedbacks_created", table_name="feedbacks")
    op.drop_table("feedbacks")

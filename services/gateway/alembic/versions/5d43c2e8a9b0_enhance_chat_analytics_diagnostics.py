"""enhance chat_analytics diagnostics

Revision ID: 5d43c2e8a9b0
Revises: 11f120f3ef96
Create Date: 2026-07-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "5d43c2e8a9b0"
down_revision: Union[str, Sequence[str], None] = "11f120f3ef96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_analytics", sa.Column("student_message_id", sa.Integer(), nullable=True))
    op.add_column("chat_analytics", sa.Column("ai_message_id", sa.Integer(), nullable=True))
    op.add_column("chat_analytics", sa.Column("provider", sa.String(length=32), nullable=True))
    op.add_column("chat_analytics", sa.Column("provider_mode", sa.String(length=32), nullable=True))
    op.add_column("chat_analytics", sa.Column("workflow_id", sa.String(length=128), nullable=True))
    op.add_column("chat_analytics", sa.Column("workflow_run_id", sa.String(length=128), nullable=True))
    op.add_column("chat_analytics", sa.Column("dify_conversation_id", sa.String(length=128), nullable=True))
    op.add_column("chat_analytics", sa.Column("dify_message_id", sa.String(length=128), nullable=True))
    op.add_column("chat_analytics", sa.Column("dataset_id", sa.String(length=128), nullable=True))
    op.add_column(
        "chat_analytics",
        sa.Column("dataset_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("chat_analytics", sa.Column("intent", sa.String(length=64), nullable=True))
    op.add_column("chat_analytics", sa.Column("outcome", sa.String(length=64), nullable=True))
    op.add_column("chat_analytics", sa.Column("answer_head", sa.String(length=512), nullable=True))
    op.add_column("chat_analytics", sa.Column("answer_length", sa.Integer(), nullable=True))
    op.add_column("chat_analytics", sa.Column("topn_count", sa.Integer(), nullable=True))
    op.add_column("chat_analytics", sa.Column("best_doc_id", sa.String(length=128), nullable=True))
    op.add_column("chat_analytics", sa.Column("best_segment_id", sa.String(length=128), nullable=True))
    op.add_column("chat_analytics", sa.Column("score_threshold", sa.Float(), nullable=True))
    op.add_column("chat_analytics", sa.Column("threshold_bucket", sa.String(length=32), nullable=True))
    op.add_column(
        "chat_analytics",
        sa.Column("retrieval_debug", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("chat_analytics", sa.Column("analytics_schema_version", sa.Integer(), nullable=True))
    op.add_column(
        "chat_analytics",
        sa.Column(
            "data_quality_flag",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE chat_analytics
        SET
            analytics_schema_version = COALESCE(analytics_schema_version, 1),
            data_quality_flag = COALESCE(data_quality_flag, 'legacy_missing_diag'),
            provider = COALESCE(provider, 'dify'),
            provider_mode = COALESCE(provider_mode, 'primary'),
            intent = COALESCE(intent, 'unknown'),
            outcome = COALESCE(
                outcome,
                CASE
                    WHEN is_answered IS TRUE THEN 'rag_answered'
                    WHEN is_answered IS FALSE AND rag_score IS NULL THEN 'unknown'
                    WHEN is_answered IS FALSE AND rag_score < 0.3 THEN 'rag_low_confidence'
                    ELSE 'unknown'
                END
            ),
            score_threshold = COALESCE(score_threshold, 0.3),
            threshold_bucket = COALESCE(
                threshold_bucket,
                CASE
                    WHEN rag_score IS NULL THEN 'no_score'
                    WHEN rag_score < 0.15 THEN 'lt_0_15'
                    WHEN rag_score < 0.30 THEN '0_15_0_30'
                    WHEN rag_score < 0.50 THEN '0_30_0_50'
                    WHEN rag_score < 0.70 THEN '0_50_0_70'
                    ELSE 'gte_0_70'
                END
            ),
            topn_count = COALESCE(topn_count, 0)
        WHERE
            analytics_schema_version IS NULL
            OR data_quality_flag IS NULL
            OR provider IS NULL
            OR provider_mode IS NULL
            OR intent IS NULL
            OR outcome IS NULL
            OR score_threshold IS NULL
            OR threshold_bucket IS NULL
            OR topn_count IS NULL
        """
    )

    for column_name, column_type, default in (
        ("provider", sa.String(length=32), sa.text("'dify'")),
        ("provider_mode", sa.String(length=32), sa.text("'primary'")),
        ("intent", sa.String(length=64), sa.text("'unknown'")),
        ("outcome", sa.String(length=64), sa.text("'unknown'")),
        ("topn_count", sa.Integer(), sa.text("0")),
        ("analytics_schema_version", sa.Integer(), sa.text("2")),
        ("data_quality_flag", sa.String(length=64), sa.text("'clean'")),
    ):
        op.alter_column(
            "chat_analytics",
            column_name,
            existing_type=column_type,
            nullable=False,
            server_default=default,
            existing_server_default=None,
        )

    op.create_foreign_key(
        "fk_chat_analytics_student_message_id_messages",
        "chat_analytics",
        "messages",
        ["student_message_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_chat_analytics_ai_message_id_messages",
        "chat_analytics",
        "messages",
        ["ai_message_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_chat_analytics_provider",
        "chat_analytics",
        "provider in ('dify','pgvector_shadow','local_fallback','manual_test','unknown')",
    )
    op.create_check_constraint(
        "ck_chat_analytics_provider_mode",
        "chat_analytics",
        "provider_mode in ('primary','shadow','fallback','eval_replay')",
    )
    op.create_check_constraint(
        "ck_chat_analytics_threshold_bucket",
        "chat_analytics",
        "threshold_bucket is null or threshold_bucket in "
        "('no_score','lt_0_15','0_15_0_30','0_30_0_50','0_50_0_70','gte_0_70')",
    )
    op.create_check_constraint(
        "ck_chat_analytics_data_quality_flag",
        "chat_analytics",
        "data_quality_flag in "
        "('clean','legacy_missing_diag','test_noise','provider_error','partial_metadata')",
    )

    op.create_index(
        "idx_chat_analytics_created_v2",
        "chat_analytics",
        [sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index("idx_chat_analytics_ai_message", "chat_analytics", ["ai_message_id"], unique=False)
    op.create_index(
        "idx_chat_analytics_provider_workflow",
        "chat_analytics",
        ["provider", "workflow_id"],
        unique=False,
    )
    op.create_index("idx_chat_analytics_dataset", "chat_analytics", ["dataset_id"], unique=False)
    op.create_index(
        "idx_chat_analytics_intent_outcome",
        "chat_analytics",
        ["intent", "outcome", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_chat_analytics_threshold",
        "chat_analytics",
        ["threshold_bucket", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_chat_analytics_threshold", table_name="chat_analytics")
    op.drop_index("idx_chat_analytics_intent_outcome", table_name="chat_analytics")
    op.drop_index("idx_chat_analytics_dataset", table_name="chat_analytics")
    op.drop_index("idx_chat_analytics_provider_workflow", table_name="chat_analytics")
    op.drop_index("idx_chat_analytics_ai_message", table_name="chat_analytics")
    op.drop_index("idx_chat_analytics_created_v2", table_name="chat_analytics")

    op.drop_constraint("ck_chat_analytics_data_quality_flag", "chat_analytics", type_="check")
    op.drop_constraint("ck_chat_analytics_threshold_bucket", "chat_analytics", type_="check")
    op.drop_constraint("ck_chat_analytics_provider_mode", "chat_analytics", type_="check")
    op.drop_constraint("ck_chat_analytics_provider", "chat_analytics", type_="check")
    op.drop_constraint("fk_chat_analytics_ai_message_id_messages", "chat_analytics", type_="foreignkey")
    op.drop_constraint("fk_chat_analytics_student_message_id_messages", "chat_analytics", type_="foreignkey")

    op.drop_column("chat_analytics", "data_quality_flag")
    op.drop_column("chat_analytics", "analytics_schema_version")
    op.drop_column("chat_analytics", "retrieval_debug")
    op.drop_column("chat_analytics", "threshold_bucket")
    op.drop_column("chat_analytics", "score_threshold")
    op.drop_column("chat_analytics", "best_segment_id")
    op.drop_column("chat_analytics", "best_doc_id")
    op.drop_column("chat_analytics", "topn_count")
    op.drop_column("chat_analytics", "answer_length")
    op.drop_column("chat_analytics", "answer_head")
    op.drop_column("chat_analytics", "outcome")
    op.drop_column("chat_analytics", "intent")
    op.drop_column("chat_analytics", "dataset_ids")
    op.drop_column("chat_analytics", "dataset_id")
    op.drop_column("chat_analytics", "dify_message_id")
    op.drop_column("chat_analytics", "dify_conversation_id")
    op.drop_column("chat_analytics", "workflow_run_id")
    op.drop_column("chat_analytics", "workflow_id")
    op.drop_column("chat_analytics", "provider_mode")
    op.drop_column("chat_analytics", "provider")
    op.drop_column("chat_analytics", "ai_message_id")
    op.drop_column("chat_analytics", "student_message_id")

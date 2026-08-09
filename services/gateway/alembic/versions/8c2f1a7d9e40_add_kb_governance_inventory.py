"""add kb governance inventory

Revision ID: 8c2f1a7d9e40
Revises: 5d43c2e8a9b0
Create Date: 2026-07-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "8c2f1a7d9e40"
down_revision: Union[str, Sequence[str], None] = "5d43c2e8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kb_entries", sa.Column("entry_uid", sa.String(255), nullable=True))
    op.add_column("kb_entries", sa.Column("doc_id", sa.String(128), nullable=True))
    op.add_column("kb_entries", sa.Column("content", sa.Text(), nullable=True))
    op.add_column("kb_entries", sa.Column("raw_content", sa.Text(), nullable=True))
    op.add_column("kb_entries", sa.Column("content_hash", sa.String(64), nullable=True))
    op.add_column("kb_entries", sa.Column("corpus_version", sa.String(64), nullable=True))
    op.add_column("kb_entries", sa.Column("governance_source_type", sa.String(64), nullable=True))
    op.add_column("kb_entries", sa.Column("legacy_origin", sa.String(64), nullable=True))
    op.add_column("kb_entries", sa.Column("lifecycle_status", sa.String(32), nullable=True))
    op.add_column("kb_entries", sa.Column("layer", sa.String(64), nullable=True))
    op.add_column("kb_entries", sa.Column("rag_policy", sa.String(32), nullable=True))
    op.add_column("kb_entries", sa.Column("confidence", sa.String(32), nullable=True))
    op.add_column("kb_entries", sa.Column("audience", postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column("kb_entries", sa.Column("freshness", sa.String(32), nullable=True))
    op.add_column("kb_entries", sa.Column("governance_scope", sa.String(32), nullable=True))
    op.add_column("kb_entries", sa.Column("governance_scope_value", sa.String(128), nullable=True))
    op.add_column("kb_entries", sa.Column("college_id", sa.Integer(), nullable=True))
    op.add_column("kb_entries", sa.Column("source_paths", postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column(
        "kb_entries",
        sa.Column("student_rag_visible", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("kb_entries", sa.Column("governance_metadata", postgresql.JSONB(), nullable=True))
    op.add_column("kb_entries", sa.Column("import_batch_uid", sa.String(128), nullable=True))
    op.add_column("kb_entries", sa.Column("published_at", sa.DateTime(), nullable=True))
    op.add_column("kb_entries", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("kb_entries", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_foreign_key("fk_kb_entries_college_id", "kb_entries", "colleges", ["college_id"], ["id"])

    op.execute(
        """
        UPDATE kb_entries
        SET entry_uid = 'legacy:kbe:' || id,
            corpus_version = 'legacy-v1',
            governance_source_type = CASE
                WHEN original_source LIKE 'teacher-kb-%' THEN 'teacher_publish'
                ELSE 'legacy_import'
            END,
            legacy_origin = 'v1_433',
            lifecycle_status = 'legacy',
            student_rag_visible = false,
            published_at = created_at,
            updated_at = created_at
        WHERE entry_uid IS NULL
        """
    )
    op.alter_column("kb_entries", "entry_uid", nullable=False)
    op.create_index("ix_kb_entries_entry_uid", "kb_entries", ["entry_uid"], unique=True)
    op.create_index("ix_kb_entries_doc_id", "kb_entries", ["doc_id"], unique=False)
    op.create_index("ix_kb_entries_import_batch_uid", "kb_entries", ["import_batch_uid"], unique=False)
    op.drop_constraint("kb_entries_dify_document_id_key", "kb_entries", type_="unique")

    op.create_table(
        "kb_publication_targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("kb_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("target_role", sa.String(32), nullable=False),
        sa.Column("dataset_id", sa.String(128), nullable=False),
        sa.Column("document_id", sa.String(128), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=True),
        sa.Column("indexing_status", sa.String(32), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("target_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("import_batch_uid", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("entry_id", "provider", "target_role", name="uq_kb_publication_target_entry_role"),
    )
    op.create_index(
        "uq_kb_publication_target_active_provider",
        "kb_publication_targets",
        ["provider", "dataset_id", "document_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )
    op.execute(
        """
        INSERT INTO kb_publication_targets (
            entry_id, provider, target_role, dataset_id, document_id,
            document_name, indexing_status, enabled, archived, is_active,
            sync_error, target_metadata
        )
        SELECT id, 'dify', 'legacy_reference', dify_dataset_id, dify_document_id,
               title, NULL, false, false, false,
               'Legacy v1 mapping preserved for audit; not the active v2 student source.',
               jsonb_build_object('legacy_origin', 'v1_433')
        FROM kb_entries
        """
    )

    op.create_table(
        "kb_governance_import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_uid", sa.String(128), nullable=False, unique=True),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=True),
        sa.Column("backup_path", sa.String(1024), nullable=False),
        sa.Column("backup_sha256", sa.String(64), nullable=False),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("inserted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unchanged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("before_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("after_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "kb_governance_import_rows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("kb_governance_import_batches.id"), nullable=False),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("kb_entries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entry_uid", sa.String(255), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("previous_state", postgresql.JSONB(), nullable=True),
        sa.Column("publication_target_id", sa.Integer(), sa.ForeignKey("kb_publication_targets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("publication_action", sa.String(16), nullable=True),
        sa.Column("previous_publication_state", postgresql.JSONB(), nullable=True),
        sa.Column("applied_state_hash", sa.String(64), nullable=False),
        sa.Column("applied_publication_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("batch_id", "entry_uid", name="uq_kb_governance_import_row"),
    )
    op.create_table(
        "kb_governance_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entry_id", sa.Integer(), sa.ForeignKey("kb_entries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("kb_governance_import_batches.id"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM kb_governance_import_batches)
               OR EXISTS (SELECT 1 FROM kb_entries WHERE corpus_version <> 'legacy-v1') THEN
                RAISE EXCEPTION
                    'Refusing downgrade while governance import evidence or non-legacy entries exist; restore the rehearsed pre-migration dump instead';
            END IF;
        END $$
        """
    )
    op.drop_table("kb_governance_audit_events")
    op.drop_table("kb_governance_import_rows")
    op.drop_table("kb_governance_import_batches")
    op.drop_table("kb_publication_targets")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM kb_entries GROUP BY dify_document_id HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade while duplicate Dify document mappings remain; rollback governance import batches first';
            END IF;
        END $$
        """
    )
    op.create_unique_constraint("kb_entries_dify_document_id_key", "kb_entries", ["dify_document_id"])
    op.drop_index("ix_kb_entries_import_batch_uid", table_name="kb_entries")
    op.drop_index("ix_kb_entries_doc_id", table_name="kb_entries")
    op.drop_index("ix_kb_entries_entry_uid", table_name="kb_entries")
    op.drop_constraint("fk_kb_entries_college_id", "kb_entries", type_="foreignkey")
    for column in (
        "updated_at", "reviewed_at", "published_at", "import_batch_uid", "governance_metadata",
        "student_rag_visible", "source_paths", "college_id", "governance_scope_value",
        "governance_scope", "freshness", "audience", "confidence", "rag_policy", "layer",
        "lifecycle_status", "legacy_origin", "governance_source_type", "corpus_version",
        "content_hash", "raw_content", "content", "doc_id", "entry_uid",
    ):
        op.drop_column("kb_entries", column)

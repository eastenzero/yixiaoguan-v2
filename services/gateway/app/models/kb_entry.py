from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class KbEntry(Base):
    """KB 条目: Dify 文档 ↔ 原始来源映射"""
    __tablename__ = "kb_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Dify 侧
    dify_document_id: Mapped[str] = mapped_column(String(128), nullable=False)
    dify_dataset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    # KB 内容
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    # 原始来源（S4 "查看原始文件" 用）
    original_source: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    #   例: "学生手册-生活服务.md 行 4927-5041"
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    material_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    campus: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # v1 原始文件名
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    #   例: "KB-0150-电费缴纳指南.md"
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # 治理字段（8c2f1a7d9e40）。这些字段描述内容生命周期，不能用
    # created_at 冒充来源发布日期或核验日期。
    entry_uid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    doc_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    corpus_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    governance_source_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    legacy_origin: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    lifecycle_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    layer: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rag_policy: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    audience: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    freshness: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    governance_scope: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    governance_scope_value: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    college_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("colleges.id"), nullable=True)
    source_paths: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    student_rag_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    governance_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    import_batch_uid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

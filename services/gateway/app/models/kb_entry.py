from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class KbEntry(Base):
    """KB 条目: Dify 文档 ↔ 原始来源映射"""
    __tablename__ = "kb_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Dify 侧
    dify_document_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
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

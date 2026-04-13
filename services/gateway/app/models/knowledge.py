import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Enum, String, Text, ForeignKey, Integer, ARRAY, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base


class SuggestionStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SuggestionSource(enum.Enum):
    teacher_input = "teacher_input"
    auto_scrape_web = "auto_scrape_web"
    auto_scrape_wechat = "auto_scrape_wechat"


class KbSuggestion(Base):
    __tablename__ = "kb_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[SuggestionSource] = mapped_column(Enum(SuggestionSource, name="suggestionsource"), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    college_id: Mapped[Optional[int]] = mapped_column(ForeignKey("colleges.id"), nullable=True)
    status: Mapped[SuggestionStatus] = mapped_column(Enum(SuggestionStatus, name="suggestionstatus"), nullable=False)
    submitted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    dify_document_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class UnansweredQuestion(Base):
    __tablename__ = "unanswered_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sample_conv_ids: Mapped[Optional[list[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    college_id: Mapped[Optional[int]] = mapped_column(ForeignKey("colleges.id"), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    kb_suggestion_id: Mapped[Optional[int]] = mapped_column(ForeignKey("kb_suggestions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class CollegeDataset(Base):
    __tablename__ = "college_datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), unique=True, nullable=False)
    dify_dataset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

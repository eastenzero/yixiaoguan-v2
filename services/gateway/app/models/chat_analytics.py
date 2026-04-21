from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChatAnalytics(Base):
    __tablename__ = "chat_analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_college_id: Mapped[int | None] = mapped_column(ForeignKey("colleges.id"), nullable=True)
    user_class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"), nullable=True)
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    query_norm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rag_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    kb_doc_matched: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_answered: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

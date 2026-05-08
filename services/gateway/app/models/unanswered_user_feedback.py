from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UnansweredUserFeedback(Base):
    __tablename__ = "unanswered_user_feedback"
    __table_args__ = (
        Index("idx_uuf_question", "unanswered_question_id"),
        Index("idx_uuf_created", text("created_at DESC")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_provided_college_id: Mapped[int | None] = mapped_column(ForeignKey("colleges.id"), nullable=True)
    user_provided_grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    user_provided_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    user_provided_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    unanswered_question_id: Mapped[int | None] = mapped_column(ForeignKey("unanswered_questions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

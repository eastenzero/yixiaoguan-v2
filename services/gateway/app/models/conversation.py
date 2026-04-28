import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Enum, String, Text, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base


class ConversationStatus(enum.Enum):
    ai_serving = "ai_serving"
    pending_teacher = "pending_teacher"
    teacher_serving = "teacher_serving"
    resolved = "resolved"
    closed = "closed"


class SenderType(enum.Enum):
    student = "student"
    ai = "ai"
    teacher = "teacher"
    system = "system"


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_conversations_student", "student_id"),
        Index("idx_conversations_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    teacher_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus, name="conversationstatus"), nullable=False)
    dify_conversation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_created", "conversation_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType, name="sendertype"), nullable=False)
    sender_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[Optional[dict]] = Column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

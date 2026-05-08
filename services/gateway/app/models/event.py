from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("idx_events_user_day", "user_id", text("date(created_at)")),
        Index("idx_events_name_day", "event_name", text("date(created_at)")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_name: Mapped[str] = mapped_column(String(64), nullable=False)
    props: Mapped[dict[str, object]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    client_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

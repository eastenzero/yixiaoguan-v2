"""Frontend event tracking endpoint (R11)."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.utils.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_EVENTS_PER_REQUEST = 50
MAX_EVENT_NAME_LEN = 64


class TrackEvent(BaseModel):
    event: str = Field(min_length=1, max_length=MAX_EVENT_NAME_LEN)
    props: dict[str, Any] = Field(default_factory=dict)
    client_ts: datetime | None = None


class TrackRequest(BaseModel):
    events: list[TrackEvent] = Field(default_factory=list, max_length=MAX_EVENTS_PER_REQUEST)


@router.post("")
async def track(
    body: TrackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int | bool | str]:
    """Batch ingest frontend events with fire-and-forget semantics."""
    if not body.events:
        return {"ok": True, "received": 0}

    received = 0
    try:
        for ev in body.events:
            db.add(
                Event(
                    user_id=current_user.id,
                    event_name=ev.event[:MAX_EVENT_NAME_LEN],
                    props=ev.props or {},
                    client_ts=ev.client_ts,
                )
            )
            received += 1
        await db.commit()
    except Exception as exc:
        logger.warning(
            "track ingest failed (user=%s, events=%d): %s",
            current_user.id,
            len(body.events),
            exc,
        )
        await db.rollback()
        return {"ok": True, "received": 0, "error": "ingest_failed"}

    return {"ok": True, "received": received}

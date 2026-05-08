import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.services.conversation_service import get_conversation

logger = logging.getLogger(__name__)
router = APIRouter()


class CentrifugoSubscribeRequest(BaseModel):
    client: str | None = None
    user: str | None = None
    channel: str
    transport: str | None = None
    protocol: str | None = None
    encoding: str | None = None


def _check_secret(x_auth: str | None, secret: str | None) -> None:
    expected = settings.centrifugo_proxy_secret
    if not expected:
        raise HTTPException(status_code=503, detail="centrifugo proxy secret not configured")
    if x_auth == expected or secret == expected:
        return
    raise HTTPException(status_code=401, detail="bad proxy auth")


def _deny(code: int, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _allow() -> dict:
    return {"result": {}}


async def _load_user(db: AsyncSession, user_id_str: str) -> User | None:
    try:
        user_id = int(user_id_str)
    except (TypeError, ValueError):
        return None
    return await db.scalar(select(User).where(User.id == user_id))


@router.post("/centrifugo/subscribe")
async def centrifugo_subscribe(
    body: CentrifugoSubscribeRequest,
    x_auth: str | None = Header(default=None, alias="X-Auth"),
    secret: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Internal-only Centrifugo subscribe proxy."""
    _check_secret(x_auth, secret)

    channel = body.channel or ""
    user_id_str = body.user or ""

    if channel.startswith("user#"):
        if channel == f"user#{user_id_str}":
            return _allow()
        return _deny(403, "cannot subscribe to other user's channel")

    if channel == "$teachers":
        user = await _load_user(db, user_id_str)
        if not user:
            return _deny(401, "auth required")
        if user.role not in (UserRole.teacher, UserRole.admin):
            return _deny(403, "not a teacher")
        return _allow()

    if channel.startswith("conv:"):
        try:
            conv_id = int(channel.split(":", 1)[1])
        except (IndexError, ValueError):
            return _deny(403, "invalid channel")

        try:
            user = await _load_user(db, user_id_str)
            if not user:
                return _deny(403, "invalid user")
            conv = await get_conversation(db, conv_id, user)
            if conv is None:
                return _deny(403, "conv not accessible")
            return _allow()
        except Exception as exc:
            logger.warning("centrifugo subscribe check failed for %s: %s", channel, exc)
            return _deny(403, "subscribe check failed")

    return _deny(403, "unknown channel")

import logging
from typing import Any

from fastapi import Request
from jose import JWTError, jwt as jose_jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger(__name__)


def _get_user_id_or_ip(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        try:
            payload: dict[str, Any] = jose_jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except JWTError as exc:
            logger.debug("rate_limit JWT decode failed: %s", exc)
        except Exception as exc:  # belt-and-suspenders for malformed tokens
            logger.debug("rate_limit unexpected JWT error: %s", exc)
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_get_user_id_or_ip,
    storage_uri=settings.redis_url,
    strategy="moving-window",
)

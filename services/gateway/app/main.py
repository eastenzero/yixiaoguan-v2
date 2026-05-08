import httpx
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.config import settings
from app.database import get_db
from app.utils.deps import get_redis
from app.routers import internal as internal_router
from app.routers.auth import router as auth_router
from app.routers.conversations import router as conversation_router
from app.routers.actions import router as actions_router
from app.routers.ws import router as ws_router
from app.routers.chat import router as chat_router
from app.routers.knowledge import router as knowledge_router
from app.routers.announcements import router as announcements_router
from app.routers.admin import router as admin_router
from app.routers.analytics import router as analytics_router
from app.routers import college as college_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.utils.rate_limit import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(
        settings.redis_url, decode_responses=True
    )
    yield
    await app.state.redis.close()

app = FastAPI(
    title="医小管 v2 Gateway",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.get("/health")
async def health(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    checks = {}

    # PG check
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    # Redis check
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # Dify check
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.dify_api_url}/parameters",
                headers={"Authorization": f"Bearer {settings.dify_api_key}"},
                timeout=5.0
            )
            checks["dify"] = "ok" if resp.status_code < 500 else f"error: {resp.status_code}"
    except Exception as e:
        checks["dify"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "version": "2.0.0",
        "checks": checks
    }

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(conversation_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(actions_router, prefix="/api/conversations", tags=["conversation-actions"])
app.include_router(ws_router, tags=["websocket"])

# 路由挂载点（后续 spec 逐步添加）：
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(announcements_router, prefix="/api/v1/announcements", tags=["announcements"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(internal_router.router, prefix="/api/internal", tags=["internal"])
app.include_router(analytics_router)  # self-prefixed /api/analytics
app.include_router(college_router.router, prefix="/api", tags=["college"])

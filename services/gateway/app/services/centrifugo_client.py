import time
import logging
import httpx
from jose import jwt
from app.config import settings
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class CentrifugoClient:
    """Centrifugo Server API 客户端"""

    def __init__(self):
        self.api_url = settings.centrifugo_api_url.rstrip("/")
        self.api_key = settings.centrifugo_api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def publish(self, channel: str, data: dict) -> bool:
        """向指定频道发布消息。

        Centrifugo v6 已经弃用 ``/api/publish`` / ``/api/broadcast`` 旧风格端点，
        统一使用 ``POST /api`` + JSON-RPC body ``{"method":"publish","params":{...}}``。
        之前的代码打 ``/api/publish`` 返回 400 Bad Request，导致所有 publish 静默失败 ——
        这是 "教师发消息学生端收不到" 的真正根因。
        """
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/api",
                    json={"method": "publish", "params": {"channel": channel, "data": data}},
                    headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                    timeout=5.0,
                )
                if resp.status_code != 200:
                    logger.error("Centrifugo publish failed: %s %s", resp.status_code, resp.text)
                    return False
                # Centrifugo 即便 HTTP 200 也可能 body 里带 error
                body = resp.json() if resp.content else {}
                if "error" in body:
                    logger.error("Centrifugo publish error body: %s", body["error"])
                    return False
                return True
        except Exception as e:
            logger.error("Centrifugo publish error: %s", e)
            return False

    async def broadcast(self, channels: list[str], data: dict) -> bool:
        """向多个频道广播同一消息（Centrifugo v6 JSON-RPC 风格）"""
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/api",
                    json={"method": "broadcast", "params": {"channels": channels, "data": data}},
                    headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                    timeout=5.0,
                )
                if resp.status_code != 200:
                    logger.error("Centrifugo broadcast failed: %s %s", resp.status_code, resp.text)
                    return False
                body = resp.json() if resp.content else {}
                if "error" in body:
                    logger.error("Centrifugo broadcast error body: %s", body["error"])
                    return False
                return True
        except Exception as e:
            logger.error("Centrifugo broadcast error: %s", e)
            return False


def build_centrifugo_token(user: User) -> str:
    """生成 Centrifugo 连接 JWT"""
    now = int(time.time())
    channels = [f"user#{user.id}"]
    if user.role in (UserRole.teacher, UserRole.admin):
        channels.append("$teachers")
    payload = {
        "sub": str(user.id),
        "exp": now + 3600,
        "info": {"name": user.name, "role": user.role.value},
        "channels": channels,
    }
    return jwt.encode(payload, settings.centrifugo_secret, algorithm="HS256")


# 全局单例
centrifugo = CentrifugoClient()

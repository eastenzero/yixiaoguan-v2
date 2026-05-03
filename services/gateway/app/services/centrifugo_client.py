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
        """向指定频道发布消息"""
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/api/publish",
                    json={"channel": channel, "data": data},
                    headers={"Authorization": f"apikey {self.api_key}"},
                    timeout=5.0,
                )
                if resp.status_code != 200:
                    logger.error("Centrifugo publish failed: %s %s", resp.status_code, resp.text)
                    return False
                return True
        except Exception as e:
            logger.error("Centrifugo publish error: %s", e)
            return False

    async def broadcast(self, channels: list[str], data: dict) -> bool:
        """向多个频道广播同一消息"""
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/api/broadcast",
                    json={"channels": channels, "data": data},
                    headers={"Authorization": f"apikey {self.api_key}"},
                    timeout=5.0,
                )
                return resp.status_code == 200
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

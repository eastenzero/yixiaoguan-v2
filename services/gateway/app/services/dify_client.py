import json
import logging
from typing import AsyncGenerator, Optional
import httpx
from httpx_sse import aconnect_sse
from app.config import settings

logger = logging.getLogger(__name__)


class DifyClient:
    """封装 Dify API 调用"""

    def __init__(self):
        self.base_url = settings.dify_api_url
        self.api_key = settings.dify_api_key
        self.dataset_api_key = settings.dify_dataset_api_key

    # ============================================================
    # Chat API — 流式调用 Chatflow
    # ============================================================
    async def chat_stream(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[dict] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        调用 Dify POST /v1/chat-messages (streaming)。
        yield 的 dict 格式:
          {"event": "message", "answer": "你好", "conversation_id": "xxx"}
          {"event": "message_end", "metadata": {...}, "conversation_id": "xxx"}
          {"event": "error", "message": "..."}

        调用方需要:
        1. 收到第一个事件时，如果 conversation_id 是新的，保存到 DB
        2. 逐 token 转发给前端 SSE
        3. message_end 时保存完整 AI 消息到 DB
        """
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user_id,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with aconnect_sse(
                client, "POST", f"{self.base_url}/chat-messages",
                headers=headers,
                json=payload,
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    if not sse.data:
                        continue
                    try:
                        data = json.loads(sse.data)
                        yield data
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON SSE data: {sse.data}")

    # ============================================================
    # Dataset API — 创建文档（KB 迁移用）
    # ============================================================
    async def create_document(
        self,
        dataset_id: str,
        title: str,
        content: str,
    ) -> dict:
        """
        POST /v1/datasets/{dataset_id}/document/create-by-text
        返回 {"document": {"id": "...", ...}, "batch": "..."}
        """
        headers = {
            "Authorization": f"Bearer {self.dataset_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "name": title,
            "text": content,
            "indexing_technique": "high_quality",
            "process_rule": {"mode": "automatic"},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/datasets/{dataset_id}/document/create-by-text",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()


# 单例
dify_client = DifyClient()

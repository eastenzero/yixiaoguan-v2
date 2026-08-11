import json
import logging
from typing import AsyncGenerator, Optional
import httpx
from httpx_sse import aconnect_sse
from app.config import settings

logger = logging.getLogger(__name__)

PROFILE_REQUEST_TERMS = ("请提供", "请告诉", "告诉我你的", "请补充", "补充你的", "请填写", "请选择")
PROFILE_FIELD_TERMS = ("学院", "年级", "专业", "班级", "身份", "职位", "学生类型")


def filter_actionable_suggestions(questions: list[object]) -> list[str]:
    """Keep only prompts that the assistant can answer when clicked immediately."""
    result = []
    for raw in questions:
        question = str(raw).strip()
        if not question or question in result:
            continue
        requests_profile = any(term in question for term in PROFILE_REQUEST_TERMS) and any(
            field in question for field in PROFILE_FIELD_TERMS
        )
        if requests_profile:
            continue
        result.append(question)
        if len(result) == 3:
            break
    return result


class DifyClient:
    """封装 Dify API 调用"""

    def __init__(self):
        self.base_url = settings.dify_api_url
        self.api_key = settings.dify_api_key
        self.dataset_api_key = settings.dify_dataset_api_key
        self.polish_api_key = getattr(settings, "dify_polish_api_key", "")

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

    # ============================================================
    # Suggested Questions — 回答后生成关联问题
    # ============================================================
    async def generate_suggestions(
        self,
        query: str,
        answer_summary: str,
        *,
        timeout: float = 5.0,
    ) -> list[str]:
        """
        调用 Dify blocking chat 生成 3 条关联问题。
        返回字符串列表，失败返回空列表。
        """
        prompt = (
            f"用户问：\"{query}\"\n"
            f"AI 答（摘要）：\"{answer_summary[:300]}\"\n\n"
            "请基于以上对话，生成3个可直接推进办事的简短追问。"
            "优先覆盖申请条件、所需材料、办理流程/时间节点、负责部门中的三个不同方面；"
            "不要生成空泛问题，也不要虚构答案中未出现的学院、金额或日期。"
            "每一条都必须是点击后 AI 能立即继续回答的问题；"
            "禁止生成‘请提供/告诉我/请补充学院、年级、专业、班级、职位或身份’这类要求用户填资料的句子。\n"
            "仅输出 JSON 数组，如 [\"问题1\",\"问题2\",\"问题3\"]，不要其他内容。"
        )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "user": "suggestion-generator",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat-messages",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("answer", "").strip()
                # 从回答中提取 JSON 数组
                import re as _re
                match = _re.search(r'\[.*\]', answer, _re.DOTALL)
                if match:
                    questions = json.loads(match.group())
                    if isinstance(questions, list):
                        return filter_actionable_suggestions(questions)
        except Exception as e:
            logger.warning(f"generate_suggestions failed: {e}")
        return []

    async def polish_text(
        self,
        *,
        question: str,
        raw_answer: str,
        scope_label: str,
    ) -> str:
        api_key = self.polish_api_key or self.api_key
        if not api_key:
            raise RuntimeError("dify polish api key is not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {
                "question": question,
                "raw_answer": raw_answer,
                "scope": scope_label,
            },
            "query": f"请将以下教师答复整理为知识库文风。问题：{question}\n答复：{raw_answer}",
            "response_mode": "blocking",
            "user": "knowledge-polisher",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat-messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = str(data.get("answer", "")).strip()
            if not answer:
                raise RuntimeError("empty polish result")
            return answer


# 单例
dify_client = DifyClient()

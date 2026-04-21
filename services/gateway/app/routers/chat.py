import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session, get_db
from app.utils.deps import get_current_user
from app.models.user import User, UserRole
from app.models.conversation import ConversationStatus, SenderType
from app.schemas.chat import ChatSendRequest, ChatSendResponse
from app.services.analytics import record_chat_analytics
from app.services.conversation_service import (
    get_conversation, add_message, build_message_broadcast_event,
)
from app.services.state_machine import transition
from app.services.dify_client import dify_client
from app.services.ws_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


def _schedule_chat_analytics(
    *,
    conv_id: int,
    user: User,
    raw_query: str,
    response_text: str,
    dify_metadata: dict | None,
):
    async def runner() -> None:
        try:
            async with async_session() as session:
                await record_chat_analytics(
                    session,
                    conv_id=conv_id,
                    user=user,
                    raw_query=raw_query,
                    response_text=response_text,
                    dify_metadata=dify_metadata,
                )
        except Exception as exc:
            logger.warning("Failed to schedule chat analytics for conv=%s: %s", conv_id, exc)

    asyncio.create_task(runner())


@router.post("/send")
async def chat_send(
    body: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    学生发送消息。
    - ai_serving: 保存消息 → 调 Dify → 返回 SSE StreamingResponse
    - pending_teacher / teacher_serving: 保存消息 → WS 广播 → 返回 JSON
    - 其他状态: 403
    """
    # 仅学生可使用此端点
    if current_user.role != UserRole.student:
        raise HTTPException(403, "仅学生可使用 /api/chat/send")

    # 获取并校验会话
    conv = await get_conversation(db, body.conv_id, current_user)
    if not conv:
        raise HTTPException(404, "会话不存在")

    if conv.status == ConversationStatus.resolved:
        await transition(db, conv, "reactivate", actor=current_user)
        await manager.broadcast_to_room(
            f"conv:{conv.id}",
            {
                "type": "status_changed",
                "data": {"conv_id": conv.id, "status": "ai_serving", "previous_status": "resolved"},
            },
        )

    # 状态检查
    if conv.status not in (
        ConversationStatus.ai_serving,
        ConversationStatus.pending_teacher,
        ConversationStatus.teacher_serving,
    ):
        raise HTTPException(403, f"当前状态 {conv.status.value} 不可发送消息")

    # 1. 保存学生消息到 DB
    student_msg = await add_message(
        db, conv.id, SenderType.student,
        body.content, sender_id=current_user.id,
    )

    # 2. WS 广播学生消息
    await manager.broadcast_to_room(
        f"conv:{conv.id}",
        build_message_broadcast_event(student_msg, conv_id=conv.id),
    )

    # 3. 根据状态路由
    if conv.status == ConversationStatus.ai_serving:
        # ---- AI 路径：返回 SSE 流 ----
        return StreamingResponse(
            _stream_ai_response(db, conv, current_user, body.content),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # ---- 教师路径：返回 JSON ----
        return ChatSendResponse(
            message_id=student_msg.id,
            conv_id=conv.id,
            sender_type="student",
            content=body.content,
            created_at=student_msg.created_at.isoformat(),
        )


def build_dify_inputs(user: User) -> dict[str, str]:
    """构造传给 Dify 的 inputs 字典（纯函数，便于单测）。"""
    return {
        "college_name": user.college.name if user.college else "",
        "campus": "",  # TODO: campus 字段暂缺，待后续在 colleges 表加字段后回填
        "class_id": user.class_.name if user.class_ else "",
    }


async def _stream_ai_response(db, conv, user, query: str):
    """
    内部生成器：调 Dify → 逐 token 发 SSE → 最后保存 AI 消息。
    """
    full_answer = ""
    sources = []
    new_dify_conv_id = conv.dify_conversation_id
    message_end_metadata: dict | None = None

    try:
        async for event in dify_client.chat_stream(
            query=query,
            user_id=str(user.id),
            conversation_id=conv.dify_conversation_id,
            inputs=build_dify_inputs(user),
        ):
            event_type = event.get("event", "")

            if event_type == "message":
                token = event.get("answer", "")
                full_answer += token
                # 捕获 Dify 新生成的 conversation_id
                if not new_dify_conv_id:
                    new_dify_conv_id = event.get("conversation_id")
                yield f"event: message\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

            elif event_type == "message_end":
                # 提取来源引用
                metadata = event.get("metadata", {})
                message_end_metadata = metadata if isinstance(metadata, dict) else None
                retriever_resources = metadata.get("retriever_resources", [])
                sources = [
                    {"title": r.get("document_name", ""),
                     "score": r.get("score", 0),
                     "content": r.get("content", "")[:200]}
                    for r in retriever_resources
                ]
                # 不在这里 yield message_end，等保存完再发

            elif event_type == "error":
                err_msg = event.get("message", "AI 服务暂时不可用")
                yield f"event: error\ndata: {json.dumps({'message': err_msg}, ensure_ascii=False)}\n\n"
                return

    except Exception as e:
        logger.error(f"Dify stream error: {e}")
        yield f"event: error\ndata: {json.dumps({'message': 'AI 服务异常，请稍后再试'}, ensure_ascii=False)}\n\n"
        return

    # 保存 AI 消息到 DB
    ai_msg = await add_message(
        db, conv.id, SenderType.ai, full_answer,
        metadata={"sources": sources, "dify_conversation_id": new_dify_conv_id},
    )

    # 更新 Dify conversation_id（首次对话时）
    if new_dify_conv_id and new_dify_conv_id != conv.dify_conversation_id:
        from sqlalchemy import update as sa_update
        from app.models.conversation import Conversation
        await db.execute(
            sa_update(Conversation)
            .where(Conversation.id == conv.id)
            .values(dify_conversation_id=new_dify_conv_id)
        )
        await db.commit()

    # WS 广播 AI 消息
    await manager.broadcast_to_room(
        f"conv:{conv.id}",
        build_message_broadcast_event(
            ai_msg,
            conv_id=conv.id,
            metadata={"sources": sources},
        ),
    )

    # 发送 message_end 和 done
    yield f"event: message_end\ndata: {json.dumps({'full_content': full_answer, 'sources': sources, 'message_id': ai_msg.id}, ensure_ascii=False)}\n\n"
    yield "event: done\ndata: {}\n\n"
    _schedule_chat_analytics(
        conv_id=conv.id,
        user=user,
        raw_query=query,
        response_text=full_answer,
        dify_metadata=message_end_metadata,
    )

import asyncio
import json
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session, get_db
from app.utils.deps import get_current_user
from app.utils.rate_limit import limiter
from app.models.user import User, UserRole
from app.models.conversation import ConversationStatus, SenderType
from app.schemas.chat import ChatSendRequest, ChatSendResponse
from app.services.analytics import (
    record_chat_analytics,
    extract_rag_metrics,
    judge_is_answered,
)
from app.services.conversation_service import (
    get_conversation, add_message, build_message_broadcast_event,
)
from app.services.state_machine import transition
from app.services.dify_client import dify_client
from app.services.ws_manager import manager
from app.services.centrifugo_client import centrifugo
from app.services.announcement_service import (
    get_active_announcements_for_user,
    mark_announcement_read,
)
from app.services.source_evidence import ANSWER_DISCLAIMER, build_source_evidence

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
@limiter.limit("10/minute")
async def chat_send(
    request: Request,
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
        _status_data = {
            "type": "status_changed",
            "data": {"conv_id": conv.id, "status": "ai_serving", "previous_status": "resolved"},
        }
        await centrifugo.publish(f"conv:{conv.id}", _status_data)
        await manager.broadcast_to_room(f"conv:{conv.id}", _status_data)

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
    _student_event = build_message_broadcast_event(student_msg, conv_id=conv.id)
    await centrifugo.publish(f"conv:{conv.id}", _student_event)
    await manager.broadcast_to_room(f"conv:{conv.id}", _student_event)

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
        "campus": user.college.campus or "" if user.college else "",
        "class_name": user.class_.name if user.class_ else "",
    }


def _entry_cohort(text: str) -> int | None:
    match = re.search(r"(?<!\d)(20)?(\d{2})\s*级", text)
    if not match:
        return None
    return 2000 + int(match.group(2))


def build_dify_query(query: str, class_name: str = "") -> str:
    """Inject the confirmed cohort split only for make-up/retake questions."""
    if not any(term in query for term in ("补考", "重修", "挂科", "不及格")):
        return query

    cohort = _entry_cohort(query) or _entry_cohort(class_name)
    if cohort is None:
        route = (
            "用户入学年级尚不明确。先追问入学年级；如需在本轮给出帮助，"
            "可并列说明2023级及以前与2024级及以后的两种规则，禁止统一回答。"
        )
    elif cohort <= 2023:
        route = (
            f"已识别为{cohort}级：正常课程考核不及格后原则上仍有一次补考机会；"
            "补考仍不合格再按规定重修。"
        )
    else:
        route = (
            f"已识别为{cohort}级：常规课程考核不及格后不再安排补考，直接按规定重修。"
        )

    return (
        f"{query}\n\n"
        "【系统补充的校内规则上下文】\n"
        "普通本科生按入学年级分流：2023级及以前原则上保留一次补考机会；"
        "2024级及以后常规挂科后不安排补考，直接重修。\n"
        f"{route}\n"
        "旷考、作弊、取消考试资格、缓考、实践课程、研究生、继续教育和其他特殊培养类型另行核验。"
        "公开网页暂未找到明确写出2024级切换点的正式文件，回答须标注这是当前校内执行口径，"
        "并提示以教务部、学院最新通知及负责部门答复为准。"
    )


async def _stream_ai_response(db, conv, user, query: str):
    """
    内部生成器：调 Dify → 逐 token 发 SSE → 最后保存 AI 消息。
    """
    full_answer = ""
    sources = []
    new_dify_conv_id = conv.dify_conversation_id
    message_end_metadata: dict | None = None

    try:
        # R05-4: deliver active unread announcements first
        try:
            announcements = await get_active_announcements_for_user(db, user)
            for ann in announcements:
                ann_event = {
                    "id": ann.id,
                    "title": ann.title,
                    "content": ann.content,
                    "created_by": ann.created_by,
                    "created_at": ann.created_at.isoformat(),
                    "expire_at": ann.expire_at.isoformat(),
                }
                yield f"event: announcement\ndata: {json.dumps(ann_event, ensure_ascii=False)}\n\n"
                await mark_announcement_read(db, user_id=user.id, announcement_id=ann.id)
        except Exception as exc:
            logger.warning("announcement delivery failed for user=%s: %s", user.id, exc)
            # do NOT block chat — announcement delivery is best-effort

        async for event in dify_client.chat_stream(
            query=build_dify_query(
                query,
                user.class_.name if user.class_ else "",
            ),
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
                try:
                    sources = await build_source_evidence(
                        db,
                        retriever_resources,
                        user_college=user.college.name if user.college else None,
                        query=query,
                    )
                except Exception as exc:
                    logger.warning("source evidence enrichment failed: %s", exc)
                    sources = [
                        {
                            "title": r.get("document_name", ""),
                            "score": r.get("score", 0),
                            "content": r.get("content", "")[:600],
                            "document_id": r.get("document_id"),
                            "dataset_id": r.get("dataset_id"),
                            "source_label": "校园知识库",
                            "source_type": "knowledge_base",
                            "verified": False,
                        }
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
        metadata={
            "sources": sources,
            "dify_conversation_id": new_dify_conv_id,
            "answer_notice": ANSWER_DISCLAIMER,
        },
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
    _ai_event = build_message_broadcast_event(
        ai_msg,
        conv_id=conv.id,
        metadata={
            "sources": sources,
            "answer_notice": ANSWER_DISCLAIMER,
        },
    )
    await centrifugo.publish(f"conv:{conv.id}", _ai_event)
    await manager.broadcast_to_room(f"conv:{conv.id}", _ai_event)

    # 发送 message_end
    yield f"event: message_end\ndata: {json.dumps({'full_content': full_answer, 'sources': sources, 'message_id': ai_msg.id, 'answer_notice': ANSWER_DISCLAIMER}, ensure_ascii=False)}\n\n"

    is_answered = True
    try:
        rag_score, _ = extract_rag_metrics(message_end_metadata or {})
        is_answered = judge_is_answered(rag_score, full_answer)
    except Exception as e:
        logger.warning(f"Answer quality evaluation failed for conv={conv.id}: {e}")

    # R10: 异步生成关联问题推荐
    try:
        suggestions = await dify_client.generate_suggestions(query, full_answer)
        if suggestions:
            yield f"event: suggestions\ndata: {json.dumps({'questions': suggestions}, ensure_ascii=False)}\n\n"
    except Exception as e:
        logger.warning(f"Suggestions generation failed for conv={conv.id}: {e}")

    if not is_answered:
        try:
            yield (
                "event: unanswered_invite\n"
                f"data: {json.dumps({'message_id': ai_msg.id, 'conv_id': conv.id}, ensure_ascii=False)}\n\n"
            )
        except Exception as e:
            logger.warning(f"unanswered_invite emit failed for conv={conv.id}: {e}")

    yield "event: done\ndata: {}\n\n"
    _schedule_chat_analytics(
        conv_id=conv.id,
        user=user,
        raw_query=query,
        response_text=full_answer,
        dify_metadata=message_end_metadata,
    )

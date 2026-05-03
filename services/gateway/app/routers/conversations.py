from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User, UserRole
from app.models.conversation import ConversationStatus, SenderType
from app.schemas.conversation import (
    CreateConversationRequest,
    ConversationListResponse,
    ConversationResponse,
    MessageListResponse,
    MessageResponse,
    SendMessageRequest,
    UnreadSummaryResponse,
)
from app.services.conversation_service import (
    add_message,
    build_message_broadcast_event,
    create_conversation,
    get_conversation,
    get_unread_summary,
    list_conversations,
    list_messages,
    mark_conversation_read,
)
from app.services.state_machine import transition
from app.services.ws_manager import manager
from app.services.centrifugo_client import centrifugo

router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=201)
async def create(
    body: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生创建新会话"""
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="仅学生可创建会话")
    conv = await create_conversation(db, current_user, body.title)
    return conv


@router.get("", response_model=ConversationListResponse)
async def list_convs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.conversation import ConversationStatus
    status_enum = None
    if status:
        try:
            status_enum = ConversationStatus(status)
        except ValueError:
            pass
    items, total = await list_conversations(db, current_user, page, size, status_enum)
    return ConversationListResponse(items=cast(list[ConversationResponse], items), total=total)


@router.get("/unread-summary", response_model=UnreadSummaryResponse)
async def unread_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return per-conversation unread counts for current student."""
    if current_user.role != UserRole.student:
        return UnreadSummaryResponse(items=[], total_unread=0)
    return await get_unread_summary(db, current_user)


@router.post("/{conv_id}/mark-read", status_code=204)
async def mark_read(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a conversation as read up to now."""
    await mark_conversation_read(db, conv_id, current_user)
    return None


@router.get("/{conv_id}", response_model=ConversationResponse)
async def get_conv(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await get_conversation(db, conv_id, current_user)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv


@router.get("/{conv_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conv_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 先校验会话权限
    conv = await get_conversation(db, conv_id, current_user)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    items, total = await list_messages(db, conv_id, page, size)
    return MessageListResponse(items=cast(list[MessageResponse], items), total=total)


@router.post("/{conv_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conv_id: int,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发送消息。
    - 学生发送: sender_type=student
    - 教师发送: sender_type=teacher
    教师接单后可通过该接口实时插入对话。
    """
    conv = await get_conversation(db, conv_id, current_user)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    if current_user.role == UserRole.student:
        if conv.status == ConversationStatus.closed:
            raise HTTPException(status_code=403, detail="会话已关闭，无法发送消息")
        if conv.status == ConversationStatus.resolved:
            await transition(db, conv, "reactivate", actor=current_user)
            _reactivate_data = {
                "type": "status_changed",
                "data": {"conv_id": conv_id, "status": "ai_serving", "previous_status": "resolved"},
            }
            await centrifugo.publish(f"conv:{conv_id}", _reactivate_data)
            await manager.broadcast_to_room(f"conv:{conv_id}", _reactivate_data)
        if conv.status not in (
            ConversationStatus.ai_serving,
            ConversationStatus.pending_teacher,
            ConversationStatus.teacher_serving,
        ):
            raise HTTPException(status_code=403, detail=f"当前状态 {conv.status.value} 不可发送消息")

    if current_user.role in {UserRole.teacher, UserRole.admin}:
        if conv.status != ConversationStatus.teacher_serving:
            raise HTTPException(status_code=403, detail="当前会话状态不允许教师回复")
        if current_user.role == UserRole.teacher and conv.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="仅接单后可回复该会话")

    # 根据角色确定 sender_type
    if current_user.role == UserRole.student:
        sender_type = SenderType.student
    elif current_user.role in {UserRole.teacher, UserRole.admin}:
        sender_type = SenderType.teacher
    else:
        sender_type = SenderType.system

    msg = await add_message(
        db, conv_id, sender_type, body.content, sender_id=current_user.id
    )
    # WS 广播新消息
    _msg_event = build_message_broadcast_event(msg, conv_id=conv_id)
    await centrifugo.publish(f"conv:{conv_id}", _msg_event)
    await manager.broadcast_to_room(f"conv:{conv_id}", _msg_event)
    return msg

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Conversation
from app.models.user import User, UserRole
from app.schemas.conversation import ConversationResponse
from app.services.conversation_service import can_access_conversation
from app.services.state_machine import InvalidTransition, transition
from app.services.ws_manager import manager
from app.services.centrifugo_client import centrifugo
from app.utils.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_conv(db: AsyncSession, conv_id: int) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv


async def _get_accessible_conv(
    db: AsyncSession,
    conv_id: int,
    current_user: User,
) -> Conversation:
    conv = await _get_conv(db, conv_id)
    if not await can_access_conversation(db, conv, current_user):
        raise HTTPException(status_code=403, detail="无权操作此会话")
    return conv


async def _notify_college_teachers(
    db: AsyncSession,
    conv: Conversation,
    current_user: User,
):
    if current_user.college_id is None:
        return
    result = await db.execute(
        select(User.id).where(
            User.role == UserRole.teacher,
            User.college_id == current_user.college_id,
            User.is_active,
        )
    )
    teacher_ids = list(result.scalars().all())
    if not teacher_ids:
        return
    _notify_data = {
        "type": "escalation_notify",
        "data": {
            "conv_id": conv.id,
            "student_id": conv.student_id,
            "title": conv.title,
            "status": conv.status.value,
            "created_at": conv.created_at.isoformat(),
        },
    }
    await centrifugo.broadcast([f"user#{tid}" for tid in teacher_ids], _notify_data)
    await manager.broadcast_to_college_teachers(
        current_user.college_id, teacher_ids, _notify_data,
    )


@router.post("/{conv_id}/escalate", response_model=ConversationResponse)
async def escalate(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生呼叫教师"""
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="仅学生可呼叫教师")
    conv = await _get_accessible_conv(db, conv_id, current_user)
    if conv.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此会话")
    try:
        await transition(db, conv, "escalate", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    try:
        await _notify_college_teachers(db, conv, current_user)
    except Exception as exc:
        logger.warning("Failed to notify college teachers for conv=%s: %s", conv_id, exc)
    _esc_data = {"type": "status_changed", "data": {"conv_id": conv_id, "status": "pending_teacher"}}
    await centrifugo.publish(f"conv:{conv_id}", _esc_data)
    await manager.broadcast_to_room(f"conv:{conv_id}", _esc_data)
    return conv


@router.post("/{conv_id}/accept", response_model=ConversationResponse)
async def accept(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教师接单"""
    if current_user.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="仅教师可接单")
    conv = await _get_accessible_conv(db, conv_id, current_user)
    try:
        await transition(db, conv, "accept", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    _accept_data = {"type": "status_changed", "data": {"conv_id": conv_id, "status": "teacher_serving",
                                                        "teacher_id": current_user.id, "teacher_name": current_user.name}}
    await centrifugo.publish(f"conv:{conv_id}", _accept_data)
    await manager.broadcast_to_room(f"conv:{conv_id}", _accept_data)
    return conv


@router.post("/{conv_id}/resolve", response_model=ConversationResponse)
async def resolve(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教师标记解决"""
    if current_user.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="仅教师可标记解决")
    conv = await _get_accessible_conv(db, conv_id, current_user)
    if current_user.role != UserRole.admin and conv.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="仅接单教师可操作")
    try:
        await transition(db, conv, "resolve", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    _resolve_data = {"type": "status_changed", "data": {"conv_id": conv_id, "status": "resolved"}}
    await centrifugo.publish(f"conv:{conv_id}", _resolve_data)
    await manager.broadcast_to_room(f"conv:{conv_id}", _resolve_data)
    return conv


@router.post("/{conv_id}/close", response_model=ConversationResponse)
async def close(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """关闭会话（学生/教师/管理员均可）"""
    conv = await _get_accessible_conv(db, conv_id, current_user)
    try:
        await transition(db, conv, "close", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    _close_data = {"type": "status_changed", "data": {"conv_id": conv_id, "status": "closed"}}
    await centrifugo.publish(f"conv:{conv_id}", _close_data)
    await manager.broadcast_to_room(f"conv:{conv_id}", _close_data)
    return conv

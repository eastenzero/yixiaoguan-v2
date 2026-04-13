from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User, UserRole
from app.models.conversation import Conversation, ConversationStatus
from app.services.state_machine import transition, InvalidTransition
from app.schemas.conversation import ConversationResponse
from app.services.ws_manager import manager
from sqlalchemy import select

router = APIRouter()


async def _get_conv(db: AsyncSession, conv_id: int) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv


@router.post("/{conv_id}/escalate", response_model=ConversationResponse)
async def escalate(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """学生呼叫教师"""
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="仅学生可呼叫教师")
    conv = await _get_conv(db, conv_id)
    if conv.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此会话")
    try:
        await transition(db, conv, "escalate", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    await manager.broadcast_to_room(
        f"conv:{conv_id}",
        {"type": "status_changed", "data": {"conv_id": conv_id, "status": "pending_teacher"}}
    )
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
    conv = await _get_conv(db, conv_id)
    try:
        await transition(db, conv, "accept", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    await manager.broadcast_to_room(
        f"conv:{conv_id}",
        {"type": "status_changed", "data": {"conv_id": conv_id, "status": "teacher_serving",
                                             "teacher_id": current_user.id, "teacher_name": current_user.name}}
    )
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
    conv = await _get_conv(db, conv_id)
    if conv.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="仅接单教师可操作")
    try:
        await transition(db, conv, "resolve", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    await manager.broadcast_to_room(
        f"conv:{conv_id}",
        {"type": "status_changed", "data": {"conv_id": conv_id, "status": "resolved"}}
    )
    return conv


@router.post("/{conv_id}/close", response_model=ConversationResponse)
async def close(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """关闭会话（学生/教师/管理员均可）"""
    conv = await _get_conv(db, conv_id)
    # 学生只能关自己的
    if current_user.role == UserRole.student and conv.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    try:
        await transition(db, conv, "close", actor=current_user)
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    await manager.broadcast_to_room(
        f"conv:{conv_id}",
        {"type": "status_changed", "data": {"conv_id": conv_id, "status": "closed"}}
    )
    return conv

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User, UserRole
from app.models.conversation import SenderType
from app.schemas.conversation import (
    CreateConversationRequest, ConversationResponse,
    ConversationListResponse, MessageListResponse,
    MessageResponse, SendMessageRequest,
)
from app.services.conversation_service import (
    create_conversation, list_conversations,
    get_conversation, list_messages, add_message,
)
from app.services.ws_manager import manager

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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await list_conversations(db, current_user, page, size)
    return ConversationListResponse(items=items, total=total)


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
    return MessageListResponse(items=items, total=total)


@router.post("/{conv_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conv_id: int,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发送消息（S2 阶段只写库，不调 Dify）。
    - 学生发送: sender_type=student
    - 教师发送: sender_type=teacher
    S3 阶段会在此基础上添加 Dify 调用。
    """
    conv = await get_conversation(db, conv_id, current_user)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 根据角色确定 sender_type
    if current_user.role == UserRole.student:
        sender_type = SenderType.student
    elif current_user.role == UserRole.teacher:
        sender_type = SenderType.teacher
    else:
        sender_type = SenderType.system

    msg = await add_message(
        db, conv_id, sender_type, body.content, sender_id=current_user.id
    )
    # WS 广播新消息
    await manager.broadcast_to_room(
        f"conv:{conv_id}",
        {
            "type": "new_message",
            "data": {
                "id": msg.id,
                "conv_id": conv_id,
                "sender_type": sender_type.value,
                "sender_id": current_user.id,
                "content": body.content,
                "created_at": msg.created_at.isoformat(),
            }
        }
    )
    return msg

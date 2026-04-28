from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from app.models.conversation import Conversation, Message, ConversationStatus, SenderType
from app.models.user import User, UserRole
from app.schemas.conversation import UnreadSummaryItem, UnreadSummaryResponse


def build_message_broadcast_event(
    msg: Message,
    *,
    conv_id: int | None = None,
    metadata: dict | None = None,
) -> dict:
    sender_type = msg.sender_type.value if isinstance(msg.sender_type, SenderType) else str(msg.sender_type)
    data = {
        "id": msg.id,
        "conv_id": conv_id or msg.conversation_id,
        "sender_type": sender_type,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }
    if msg.sender_id is not None:
        data["sender_id"] = msg.sender_id
    if metadata is not None:
        data["metadata"] = metadata
    return {"type": "new_message", "data": data}


async def can_access_conversation(
    db: AsyncSession,
    conv: Conversation,
    user: User,
) -> bool:
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.student:
        return conv.student_id == user.id
    if user.role != UserRole.teacher:
        return False
    if conv.teacher_id == user.id:
        return True
    if conv.status != ConversationStatus.pending_teacher or user.college_id is None:
        return False
    from app.models.user import User as UserModel
    stmt = select(UserModel.college_id).where(UserModel.id == conv.student_id)
    result = await db.execute(stmt)
    student_college_id = result.scalar_one_or_none()
    return student_college_id == user.college_id


async def create_conversation(
    db: AsyncSession,
    student: User,
    title: str | None = None,
) -> Conversation:
    """学生创建新会话"""
    conv = Conversation(
        student_id=student.id,
        status=ConversationStatus.ai_serving,
        title=title or "新对话",
    )
    db.add(conv)
    await db.flush()
    # 插入系统消息
    system_msg = Message(
        conversation_id=conv.id,
        sender_type=SenderType.system,
        content="会话已创建，AI 助手为您服务",
    )
    db.add(system_msg)
    await db.commit()
    await db.refresh(conv)
    return conv


async def list_conversations(
    db: AsyncSession,
    user: User,
    page: int = 1,
    size: int = 20,
    status: ConversationStatus | None = None,
) -> tuple[list[Conversation], int]:
    """
    学生: 查看自己的会话（所有状态）
    教师: 查看本学院的 pending_teacher + 自己正在服务的
    管理员: 查看所有
    """
    base = select(Conversation)

    if user.role == UserRole.student:
        base = base.where(Conversation.student_id == user.id)
    elif user.role == UserRole.teacher:
        from app.models.user import User as UserModel
        base = base.join(UserModel, Conversation.student_id == UserModel.id)
        if status is not None:
            # 教师 + 指定状态: 只看该状态下自己有权看到的
            if status == ConversationStatus.pending_teacher:
                base = base.where(
                    (UserModel.college_id == user.college_id) &
                    (Conversation.status == status)
                )
            else:
                base = base.where(
                    (Conversation.teacher_id == user.id) &
                    (Conversation.status == status)
                )
        else:
            # 教师无状态过滤: 本学院待接单 + 自己已接的
            base = base.where(
                or_(
                    (UserModel.college_id == user.college_id) &
                    (Conversation.status == ConversationStatus.pending_teacher),
                    Conversation.teacher_id == user.id,
                )
            )
        status = None  # already applied
    # admin 不加过滤

    # optional status filter (student / admin)
    if status is not None:
        base = base.where(Conversation.status == status)

    # count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # paginate
    stmt = base.order_by(Conversation.updated_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def get_conversation(
    db: AsyncSession,
    conv_id: int,
    user: User,
) -> Conversation | None:
    """获取会话详情，校验权限"""
    stmt = select(Conversation).where(Conversation.id == conv_id)
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        return None
    if not await can_access_conversation(db, conv, user):
        return None
    return conv


async def get_unread_summary(db: AsyncSession, current_user: User) -> UnreadSummaryResponse:
    """Return all student conversations with unread counts.

    Conversations without messages are included with unread_count=0 so the
    response remains a complete conversation summary for the current student.
    """
    conv_result = await db.execute(
        select(Conversation).where(Conversation.student_id == current_user.id)
    )
    conversations = list(conv_result.scalars().all())
    if not conversations:
        return UnreadSummaryResponse(items=[], total_unread=0)

    conv_ids = [conv.id for conv in conversations]
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id.in_(conv_ids))
        .order_by(Message.conversation_id, Message.created_at.desc())
    )
    messages = list(msg_result.scalars().all())

    messages_by_conv: dict[int, list[Message]] = {conv_id: [] for conv_id in conv_ids}
    for msg in messages:
        messages_by_conv.setdefault(msg.conversation_id, []).append(msg)

    items: list[UnreadSummaryItem] = []
    total_unread = 0
    unread_sender_types = {SenderType.teacher, SenderType.system}
    for conv in conversations:
        conv_messages = messages_by_conv.get(conv.id, [])
        last_message = conv_messages[0] if conv_messages else None
        unread_count = 0
        for msg in conv_messages:
            if msg.sender_type not in unread_sender_types:
                continue
            if conv.last_read_at is None or msg.created_at > conv.last_read_at:
                unread_count += 1

        total_unread += unread_count
        status = conv.status.value if isinstance(conv.status, ConversationStatus) else str(conv.status)
        last_sender_type = None
        if last_message is not None:
            last_sender_type = (
                last_message.sender_type.value
                if isinstance(last_message.sender_type, SenderType)
                else str(last_message.sender_type)
            )
        items.append(
            UnreadSummaryItem(
                conv_id=conv.id,
                title=conv.title,
                status=status,
                unread_count=unread_count,
                last_message_at=last_message.created_at if last_message else None,
                last_message_sender_type=last_sender_type,
                last_read_at=conv.last_read_at,
            )
        )

    items.sort(key=lambda item: item.last_message_at or datetime.min, reverse=True)
    return UnreadSummaryResponse(items=items, total_unread=total_unread)


async def mark_conversation_read(db: AsyncSession, conv_id: int, current_user: User) -> None:
    """Mark a student-owned conversation as read up to the current database time."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.student_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conv_id)
        .values(last_read_at=func.now())
    )
    await db.commit()


async def list_messages(
    db: AsyncSession,
    conv_id: int,
    page: int = 1,
    size: int = 50,
) -> tuple[list[Message], int]:
    """获取消息列表（分页，按时间正序）"""
    base = select(Message).where(Message.conversation_id == conv_id)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.order_by(Message.created_at.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def add_message(
    db: AsyncSession,
    conv_id: int,
    sender_type: SenderType,
    content: str,
    sender_id: int | None = None,
    metadata: dict | None = None,
) -> Message:
    """向会话添加一条消息"""
    msg = Message(
        conversation_id=conv_id,
        sender_type=sender_type,
        sender_id=sender_id,
        content=content,
    )
    if metadata:
        msg.metadata_ = metadata
    db.add(msg)
    # 更新会话 updated_at
    conv = await db.get(Conversation, conv_id)
    if conv:
        from sqlalchemy import update
        from datetime import datetime
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conv_id)
            .values(updated_at=datetime.now())
        )
    await db.commit()
    await db.refresh(msg)
    return msg

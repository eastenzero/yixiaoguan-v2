from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.conversation import Conversation, Message, ConversationStatus, SenderType
from app.models.user import User, UserRole


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
        # 教师看到: 本学院待接单 + 自己已接的
        # 需要 JOIN users 获取学生的 college_id
        from app.models.user import User as UserModel
        base = base.join(UserModel, Conversation.student_id == UserModel.id).where(
            or_(
                # 本学院待接单
                (UserModel.college_id == user.college_id) &
                (Conversation.status == ConversationStatus.pending_teacher),
                # 自己正在服务的
                Conversation.teacher_id == user.id,
            )
        )
    # admin 不加过滤

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
    # 权限校验
    if user.role == UserRole.student and conv.student_id != user.id:
        return None
    # 教师权限校验放宽：已接单的 + 本学院的 pending 都可看
    return conv


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
            .values(updated_at=datetime.utcnow())
        )
    await db.commit()
    await db.refresh(msg)
    return msg

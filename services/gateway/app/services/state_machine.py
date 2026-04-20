from datetime import datetime
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message, ConversationStatus, SenderType
from app.models.user import User


class InvalidTransition(Exception):
    """非法状态转换"""
    def __init__(self, current: str, action: str):
        self.current = current
        self.action = action
        super().__init__(f"Cannot {action} from {current}")


# ============================
# 合法转换表
# ============================
# (当前状态, 动作) → 目标状态
TRANSITIONS = {
    (ConversationStatus.ai_serving,       "escalate"):  ConversationStatus.pending_teacher,
    (ConversationStatus.pending_teacher,   "accept"):    ConversationStatus.teacher_serving,
    (ConversationStatus.pending_teacher,   "timeout"):   ConversationStatus.ai_serving,
    (ConversationStatus.teacher_serving,   "resolve"):   ConversationStatus.resolved,
    (ConversationStatus.resolved,          "reactivate"):ConversationStatus.ai_serving,
    (ConversationStatus.resolved,          "close"):     ConversationStatus.closed,
    # 补充: 任何非 closed 状态都可以直接关闭
    (ConversationStatus.ai_serving,        "close"):     ConversationStatus.closed,
    (ConversationStatus.pending_teacher,    "close"):     ConversationStatus.closed,
    (ConversationStatus.teacher_serving,    "close"):     ConversationStatus.closed,
}


async def transition(
    db: AsyncSession,
    conv: Conversation,
    action: str,
    actor: User | None = None,
    extra: dict | None = None,
) -> ConversationStatus:
    """
    执行状态转换。
    返回新状态。
    失败抛 InvalidTransition。
    """
    key = (conv.status, action)
    if key not in TRANSITIONS:
        raise InvalidTransition(conv.status.value, action)

    new_status = TRANSITIONS[key]
    now = datetime.now()

    # 更新会话状态
    update_values = {"status": new_status, "updated_at": now}

    if action == "accept" and actor:
        update_values["teacher_id"] = actor.id
    if action == "resolve":
        update_values["resolved_at"] = now
    if action == "close":
        update_values["closed_at"] = now
    if action == "reactivate":
        update_values["teacher_id"] = None
        update_values["resolved_at"] = None

    await db.execute(
        update(Conversation)
        .where(Conversation.id == conv.id)
        .values(**update_values)
    )

    # 写入系统消息
    system_messages = {
        "escalate":    "学生请求转接人工服务",
        "accept":      f"教师 {actor.name if actor else ''} 已接入对话",
        "timeout":     "暂无教师在线，继续 AI 服务",
        "resolve":     "教师已将问题标记为已解决",
        "reactivate":  "学生继续提问，AI 服务已重新激活",
        "close":       "会话已关闭",
    }

    msg = Message(
        conversation_id=conv.id,
        sender_type=SenderType.system,
        content=system_messages.get(action, f"状态变更: {new_status.value}"),
    )
    if extra:
        msg.metadata_ = extra
    db.add(msg)

    await db.commit()

    # 刷新 conv 对象
    await db.refresh(conv)
    return new_status

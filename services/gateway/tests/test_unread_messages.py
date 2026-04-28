from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.sql.dml import Update

from app.models.conversation import ConversationStatus, SenderType
from app.models.user import User, UserRole
from app.routers.conversations import unread_summary
from app.services.conversation_service import get_unread_summary, mark_conversation_read


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _FakeExecuteResult:
    def __init__(self, values=None, scalar_value=None):
        self._values = values or []
        self._scalar_value = scalar_value

    def scalars(self):
        return _FakeScalarResult(self._values)

    def scalar_one_or_none(self):
        return self._scalar_value


class _FakeDB:
    def __init__(self, conversations, messages):
        self.conversations = conversations
        self.messages = messages
        self.statements = []
        self.commit = AsyncMock()

    async def execute(self, statement):
        self.statements.append(statement)
        if isinstance(statement, Update):
            conv_id = statement.compile().params["id_1"]
            for conv in self.conversations:
                if conv.id == conv_id:
                    conv.last_read_at = datetime.now()
            return _FakeExecuteResult()
        statement_text = str(statement)
        if "FROM conversations" in statement_text:
            return _FakeExecuteResult(values=self.conversations, scalar_value=self.conversations[0] if self.conversations else None)
        return _FakeExecuteResult(values=self.messages)


def _user(user_id: int, role: UserRole) -> User:
    return User(
        id=user_id,
        staff_id=f"user-{user_id}",
        name=f"User {user_id}",
        role=role,
        college_id=1,
        class_id=None,
        password_hash="hashed",
    )


def _conv(conv_id: int, student_id: int, last_read_at=None):
    return SimpleNamespace(
        id=conv_id,
        student_id=student_id,
        title=f"Conv {conv_id}",
        status=ConversationStatus.teacher_serving,
        created_at=datetime(2026, 4, 28, 8, 0, 0),
        last_read_at=last_read_at,
    )


def _msg(msg_id: int, conv_id: int, sender_type: SenderType, created_at: datetime):
    return SimpleNamespace(
        id=msg_id,
        conversation_id=conv_id,
        sender_type=sender_type,
        sender_id=None,
        content=f"message {msg_id}",
        created_at=created_at,
    )


@pytest.mark.asyncio
async def test_student_with_no_messages_has_zero_unread():
    student = _user(101, UserRole.student)
    db = _FakeDB([_conv(1, student.id)], [])

    result = await get_unread_summary(db, student)

    assert result.total_unread == 0
    assert result.items[0].conv_id == 1
    assert result.items[0].unread_count == 0


@pytest.mark.asyncio
async def test_ai_and_system_only_messages_do_not_count_when_last_read_is_null():
    student = _user(102, UserRole.student)
    conv = _conv(2, student.id)
    base = datetime(2026, 4, 28, 9, 0, 0)
    messages = [
        _msg(1, conv.id, SenderType.student, base),
        _msg(2, conv.id, SenderType.ai, base + timedelta(minutes=1)),
        _msg(3, conv.id, SenderType.system, base + timedelta(minutes=2)),
    ]
    db = _FakeDB([conv], sorted(messages, key=lambda msg: msg.created_at, reverse=True))

    result = await get_unread_summary(db, student)

    assert result.total_unread == 0
    assert result.items[0].unread_count == 0
    assert result.items[0].last_message_sender_type == "system"


@pytest.mark.asyncio
async def test_teacher_messages_count_when_last_read_is_null():
    student = _user(106, UserRole.student)
    conv = _conv(6, student.id)
    base = datetime(2026, 4, 28, 9, 0, 0)
    messages = [
        _msg(1, conv.id, SenderType.student, base),
        _msg(2, conv.id, SenderType.ai, base + timedelta(minutes=1)),
        _msg(3, conv.id, SenderType.teacher, base + timedelta(minutes=2)),
        _msg(4, conv.id, SenderType.teacher, base + timedelta(minutes=3)),
        _msg(5, conv.id, SenderType.teacher, base + timedelta(minutes=4)),
        _msg(6, conv.id, SenderType.system, base + timedelta(minutes=5)),
    ]
    db = _FakeDB([conv], sorted(messages, key=lambda msg: msg.created_at, reverse=True))

    result = await get_unread_summary(db, student)

    assert result.total_unread == 3
    assert result.items[0].unread_count == 3
    assert result.items[0].last_message_sender_type == "system"


@pytest.mark.asyncio
async def test_mark_read_drops_existing_unread_to_zero():
    student = _user(103, UserRole.student)
    conv = _conv(3, student.id)
    base = datetime(2026, 4, 28, 8, 0, 0)
    messages = [
        _msg(1, conv.id, SenderType.teacher, base),
        _msg(2, conv.id, SenderType.teacher, base + timedelta(minutes=1)),
    ]
    db = _FakeDB([conv], sorted(messages, key=lambda msg: msg.created_at, reverse=True))

    await mark_conversation_read(db, conv.id, student)
    result = await get_unread_summary(db, student)

    assert result.total_unread == 0
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_new_teacher_message_after_mark_read_counts_as_unread():
    student = _user(104, UserRole.student)
    last_read_at = datetime(2026, 4, 28, 11, 0, 0)
    conv = _conv(4, student.id, last_read_at=last_read_at)
    messages = [
        _msg(1, conv.id, SenderType.teacher, last_read_at - timedelta(minutes=1)),
        _msg(2, conv.id, SenderType.teacher, last_read_at + timedelta(minutes=1)),
    ]
    db = _FakeDB([conv], sorted(messages, key=lambda msg: msg.created_at, reverse=True))

    result = await get_unread_summary(db, student)

    assert result.total_unread == 1
    assert result.items[0].unread_count == 1


@pytest.mark.asyncio
async def test_unread_query_is_scoped_to_current_student():
    student = _user(105, UserRole.student)
    db = _FakeDB([], [])

    result = await get_unread_summary(db, student)

    assert result.total_unread == 0
    statement = db.statements[0]
    assert "conversations.student_id" in str(statement.whereclause)
    assert statement.compile().params["student_id_1"] == student.id


@pytest.mark.asyncio
async def test_non_student_unread_summary_returns_empty_response():
    teacher = _user(201, UserRole.teacher)

    result = await unread_summary(db=object(), current_user=teacher)

    assert result.items == []
    assert result.total_unread == 0

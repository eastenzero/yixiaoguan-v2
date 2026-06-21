from datetime import datetime
from types import SimpleNamespace

import pytest

from app.models.conversation import ConversationStatus
from app.models.user import User, UserRole
from app.services.conversation_service import can_access_conversation, list_conversations


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _FakeExecuteResult:
    def __init__(self, values=None, scalar_value=None):
        self._values = values or []
        self._scalar_value = scalar_value

    def scalar(self):
        return self._scalar_value

    def scalar_one_or_none(self):
        return self._scalar_value

    def scalars(self):
        return _FakeScalarResult(self._values)


class _FakeDB:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        text = str(statement)
        if "count" in text.lower():
            return _FakeExecuteResult(scalar_value=0)
        return _FakeExecuteResult(values=[])


def _build_user(*, user_id: int, role: UserRole, college_id: int | None, staff_id: str) -> User:
    return User(
        id=user_id,
        staff_id=staff_id,
        name=f"{staff_id}-name",
        role=role,
        college_id=college_id,
        class_id=None,
        password_hash="hashed",
    )


def _build_conv(*, conv_id: int, student_id: int, status: ConversationStatus):
    return SimpleNamespace(
        id=conv_id,
        student_id=student_id,
        teacher_id=None,
        status=status,
        title="呼叫老师",
        created_at=datetime(2026, 4, 21, 5, 7, 0),
        updated_at=datetime(2026, 4, 21, 5, 7, 0),
    )


@pytest.mark.asyncio
async def test_no_college_teacher_cannot_access_pending_no_college_student_without_query():
    db = _FakeDB()
    teacher = _build_user(user_id=7001, role=UserRole.teacher, college_id=None, staff_id="teacher-no-college")
    conv = _build_conv(conv_id=90, student_id=8001, status=ConversationStatus.pending_teacher)

    assert await can_access_conversation(db, conv, teacher) is False
    assert db.statements == []


@pytest.mark.asyncio
async def test_no_college_teacher_pending_list_does_not_match_no_college_students():
    db = _FakeDB()
    teacher = _build_user(user_id=7002, role=UserRole.teacher, college_id=None, staff_id="teacher-no-college-2")

    items, total = await list_conversations(db, teacher, status=ConversationStatus.pending_teacher)

    assert items == []
    assert total == 0
    rendered = str(db.statements[-1])
    assert "users.college_id IS NULL" not in rendered
    assert "false" in rendered.lower() or "0 = 1" in rendered

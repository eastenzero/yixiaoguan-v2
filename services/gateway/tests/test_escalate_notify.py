from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.sql.elements import BooleanClauseList

from app.models.conversation import ConversationStatus
from app.models.user import User, UserRole
from app.routers.actions import _notify_college_teachers, escalate
from app.services.ws_manager import ConnectionManager


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _FakeExecuteResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return _FakeScalarResult(self._values)


class _FakeDB:
    def __init__(self, values):
        self.execute = AsyncMock(return_value=_FakeExecuteResult(values))


def _build_student(*, user_id: int, college_id: int, staff_id: str) -> User:
    return User(
        id=user_id,
        staff_id=staff_id,
        name=f"{staff_id}-name",
        role=UserRole.student,
        college_id=college_id,
        class_id=None,
        password_hash="hashed",
    )


def _assert_notify_filters(statement, *, college_id: int):
    conditions = statement.whereclause.clauses if isinstance(statement.whereclause, BooleanClauseList) else (statement.whereclause,)
    assert len(conditions) == 3
    rendered_conditions = {str(condition) for condition in conditions}
    assert 'users.role = :role_1' in rendered_conditions
    assert 'users.college_id = :college_id_1' in rendered_conditions
    assert 'users.is_active' in rendered_conditions
    compiled_params = statement.compile().params
    assert compiled_params['role_1'] == UserRole.teacher
    assert compiled_params['college_id_1'] == college_id


@pytest.mark.asyncio
async def test_notify_college_teachers_broadcasts_ticket_payload(monkeypatch):
    db = _FakeDB([4101, 4102])
    student = _build_student(user_id=4001, college_id=7, staff_id="student101")
    conv = SimpleNamespace(
        id=71,
        student_id=student.id,
        title="奖学金申请咨询",
        status=ConversationStatus.pending_teacher,
        created_at=datetime(2026, 4, 21, 5, 3, 0),
    )
    broadcast_mock = AsyncMock()

    monkeypatch.setattr(
        "app.routers.actions.manager.broadcast_to_college_teachers",
        broadcast_mock,
    )

    await _notify_college_teachers(db, conv, student)

    db.execute.assert_awaited_once()
    statement = db.execute.await_args.args[0]
    _assert_notify_filters(statement, college_id=student.college_id)
    broadcast_mock.assert_awaited_once_with(
        student.college_id,
        [4101, 4102],
        {
            "type": "escalation_notify",
            "data": {
                "conv_id": conv.id,
                "student_id": conv.student_id,
                "title": conv.title,
                "status": conv.status.value,
                "created_at": conv.created_at.isoformat(),
            },
        },
    )


@pytest.mark.asyncio
async def test_notify_college_teachers_returns_when_no_teachers_found(monkeypatch):
    db = _FakeDB([])
    student = _build_student(user_id=4005, college_id=9, staff_id="student105")
    conv = SimpleNamespace(
        id=75,
        student_id=student.id,
        title="宿舍报修咨询",
        status=ConversationStatus.pending_teacher,
        created_at=datetime(2026, 4, 21, 5, 6, 0),
    )
    broadcast_mock = AsyncMock()

    monkeypatch.setattr(
        "app.routers.actions.manager.broadcast_to_college_teachers",
        broadcast_mock,
    )

    await _notify_college_teachers(db, conv, student)

    db.execute.assert_awaited_once()
    statement = db.execute.await_args.args[0]
    _assert_notify_filters(statement, college_id=student.college_id)
    broadcast_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_connection_manager_broadcast_to_college_teachers_targets_only_given_ids():
    manager = ConnectionManager()
    manager.send_to_user = AsyncMock()
    message = {"type": "escalation_notify", "data": {"conv_id": 72}}

    await manager.broadcast_to_college_teachers(7, [4201, 4202], message)

    assert manager.send_to_user.await_count == 2
    called_user_ids = [call.args[0] for call in manager.send_to_user.await_args_list]
    assert called_user_ids == [4201, 4202]


@pytest.mark.asyncio
async def test_escalate_transitions_and_broadcasts_status(monkeypatch):
    db = object()
    student = _build_student(user_id=4002, college_id=7, staff_id="student102")
    conv = SimpleNamespace(
        id=73,
        student_id=student.id,
        status=ConversationStatus.ai_serving,
    )
    notify_mock = AsyncMock()
    broadcast_mock = AsyncMock()

    async def fake_transition(db_arg, conv_arg, action, actor=None):
        assert db_arg is db
        assert conv_arg is conv
        assert action == "escalate"
        assert actor is student
        conv.status = ConversationStatus.pending_teacher
        return ConversationStatus.pending_teacher

    monkeypatch.setattr("app.routers.actions._get_accessible_conv", AsyncMock(return_value=conv))
    monkeypatch.setattr("app.routers.actions.transition", fake_transition)
    monkeypatch.setattr("app.routers.actions._notify_college_teachers", notify_mock)
    monkeypatch.setattr("app.routers.actions.manager.broadcast_to_room", broadcast_mock)

    result = await escalate(conv.id, db=db, current_user=student)

    assert result is conv
    notify_mock.assert_awaited_once_with(db, conv, student)
    broadcast_mock.assert_awaited_once_with(
        f"conv:{conv.id}",
        {"type": "status_changed", "data": {"conv_id": conv.id, "status": "pending_teacher"}},
    )


@pytest.mark.asyncio
async def test_escalate_notify_failure_does_not_block_status_broadcast(monkeypatch):
    db = object()
    student = _build_student(user_id=4003, college_id=7, staff_id="student103")
    conv = SimpleNamespace(
        id=74,
        student_id=student.id,
        status=ConversationStatus.ai_serving,
    )
    broadcast_mock = AsyncMock()

    async def fake_transition(db_arg, conv_arg, action, actor=None):
        assert db_arg is db
        assert conv_arg is conv
        assert action == "escalate"
        assert actor is student
        conv.status = ConversationStatus.pending_teacher
        return ConversationStatus.pending_teacher

    async def fail_notify(db_arg, conv_arg, current_user_arg):
        assert db_arg is db
        assert conv_arg is conv
        assert current_user_arg is student
        raise RuntimeError("ws down")

    monkeypatch.setattr("app.routers.actions._get_accessible_conv", AsyncMock(return_value=conv))
    monkeypatch.setattr("app.routers.actions.transition", fake_transition)
    monkeypatch.setattr("app.routers.actions._notify_college_teachers", fail_notify)
    monkeypatch.setattr("app.routers.actions.manager.broadcast_to_room", broadcast_mock)

    result = await escalate(conv.id, db=db, current_user=student)

    assert result is conv
    assert conv.status == ConversationStatus.pending_teacher
    broadcast_mock.assert_awaited_once_with(
        f"conv:{conv.id}",
        {"type": "status_changed", "data": {"conv_id": conv.id, "status": "pending_teacher"}},
    )

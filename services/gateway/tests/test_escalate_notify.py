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
        if values and isinstance(values[0], list):
            self._values_by_call = list(values)
        else:
            self._values_by_call = [values]
        self.statements = []
        self.execute = AsyncMock(side_effect=self._execute)

    async def _execute(self, statement):
        self.statements.append(statement)
        values = self._values_by_call.pop(0) if self._values_by_call else []
        return _FakeExecuteResult(values)


def _build_student(*, user_id: int, college_id: int | None, staff_id: str) -> User:
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


def _assert_admin_fallback_filters(statement):
    conditions = statement.whereclause.clauses if isinstance(statement.whereclause, BooleanClauseList) else (statement.whereclause,)
    assert len(conditions) == 2
    rendered_conditions = {str(condition) for condition in conditions}
    assert 'users.role = :role_1' in rendered_conditions
    assert 'users.is_active' in rendered_conditions
    compiled_params = statement.compile().params
    assert compiled_params['role_1'] == UserRole.admin


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
                "student_college_id": student.college_id,
                "title": conv.title,
                "status": conv.status.value,
                "created_at": conv.created_at.isoformat(),
                "notification_scope": "college_teachers",
            },
        },
    )


@pytest.mark.asyncio
async def test_notify_college_teachers_falls_back_to_admins_when_no_teachers_found(monkeypatch):
    db = _FakeDB([[], [5101, 5102]])
    student = _build_student(user_id=4005, college_id=9, staff_id="student105")
    conv = SimpleNamespace(
        id=75,
        student_id=student.id,
        title="宿舍报修咨询",
        status=ConversationStatus.pending_teacher,
        created_at=datetime(2026, 4, 21, 5, 6, 0),
    )
    broadcast_mock = AsyncMock()
    send_to_user_mock = AsyncMock()
    centrifugo_mock = AsyncMock()

    monkeypatch.setattr(
        "app.routers.actions.manager.broadcast_to_college_teachers",
        broadcast_mock,
    )
    monkeypatch.setattr("app.routers.actions.manager.send_to_user", send_to_user_mock)
    monkeypatch.setattr("app.routers.actions.centrifugo.broadcast", centrifugo_mock)

    await _notify_college_teachers(db, conv, student)

    assert db.execute.await_count == 2
    _assert_notify_filters(db.statements[0], college_id=student.college_id)
    _assert_admin_fallback_filters(db.statements[1])
    broadcast_mock.assert_not_awaited()
    centrifugo_mock.assert_awaited_once()
    assert centrifugo_mock.await_args.args[0] == ["user#5101", "user#5102"]
    payload = centrifugo_mock.await_args.args[1]
    assert payload["data"]["notification_scope"] == "admin_fallback"
    assert payload["data"]["fallback_reason"] == "no_active_college_teachers"
    assert send_to_user_mock.await_count == 2


@pytest.mark.asyncio
async def test_notify_college_teachers_falls_back_to_admins_for_no_college_student(monkeypatch):
    db = _FakeDB([6101, 6102])
    student = _build_student(user_id=4006, college_id=None, staff_id="pilot:student106")
    conv = SimpleNamespace(
        id=76,
        student_id=student.id,
        title="呼叫老师",
        status=ConversationStatus.pending_teacher,
        created_at=datetime(2026, 4, 21, 5, 7, 0),
    )
    broadcast_mock = AsyncMock()
    send_to_user_mock = AsyncMock()
    centrifugo_mock = AsyncMock()

    monkeypatch.setattr(
        "app.routers.actions.manager.broadcast_to_college_teachers",
        broadcast_mock,
    )
    monkeypatch.setattr("app.routers.actions.manager.send_to_user", send_to_user_mock)
    monkeypatch.setattr("app.routers.actions.centrifugo.broadcast", centrifugo_mock)

    await _notify_college_teachers(db, conv, student)

    db.execute.assert_awaited_once()
    _assert_admin_fallback_filters(db.statements[0])
    broadcast_mock.assert_not_awaited()
    centrifugo_mock.assert_awaited_once()
    assert centrifugo_mock.await_args.args[0] == ["user#6101", "user#6102"]
    payload = centrifugo_mock.await_args.args[1]
    assert payload == {
        "type": "escalation_notify",
        "data": {
            "conv_id": conv.id,
            "student_id": conv.student_id,
            "student_college_id": None,
            "title": conv.title,
            "status": conv.status.value,
            "created_at": conv.created_at.isoformat(),
            "notification_scope": "admin_fallback",
            "fallback_reason": "student_without_college",
        },
    }
    assert send_to_user_mock.await_count == 2


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

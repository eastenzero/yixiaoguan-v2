from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.conversation import ConversationStatus, SenderType
from app.models.user import User, UserRole
from app.routers.conversations import send_message
from app.schemas.conversation import SendMessageRequest


def _build_user(*, user_id: int, role: UserRole, staff_id: str) -> User:
    return User(
        id=user_id,
        staff_id=staff_id,
        name=f"{staff_id}-name",
        role=role,
        college_id=1,
        class_id=None,
        password_hash="hashed",
    )


@pytest.mark.asyncio
async def test_teacher_send_message_persists_and_broadcasts(monkeypatch):
    db = object()
    teacher = _build_user(user_id=2001, role=UserRole.teacher, staff_id="teacher001")
    conv = SimpleNamespace(
        id=88,
        status=ConversationStatus.teacher_serving,
        teacher_id=teacher.id,
    )
    msg = SimpleNamespace(
        id=501,
        conversation_id=conv.id,
        sender_type=SenderType.teacher,
        sender_id=teacher.id,
        content="这条问题我来跟进。",
        created_at=datetime(2026, 4, 21, 5, 0, 0),
    )
    get_conversation_mock = AsyncMock(return_value=conv)
    add_message_mock = AsyncMock(return_value=msg)
    broadcast_mock = AsyncMock()

    monkeypatch.setattr("app.routers.conversations.get_conversation", get_conversation_mock)
    monkeypatch.setattr("app.routers.conversations.add_message", add_message_mock)
    monkeypatch.setattr("app.routers.conversations.manager.broadcast_to_room", broadcast_mock)

    result = await send_message(
        conv.id,
        SendMessageRequest(content=f"  {msg.content}  "),
        db=db,
        current_user=teacher,
    )

    assert result is msg
    get_conversation_mock.assert_awaited_once_with(db, conv.id, teacher)
    add_message_mock.assert_awaited_once_with(
        db,
        conv.id,
        SenderType.teacher,
        msg.content,
        sender_id=teacher.id,
    )
    broadcast_mock.assert_awaited_once()
    room_id, payload = broadcast_mock.await_args.args
    assert room_id == f"conv:{conv.id}"
    assert payload["type"] == "new_message"
    assert payload["data"]["conv_id"] == conv.id
    assert payload["data"]["sender_type"] == "teacher"
    assert payload["data"]["sender_id"] == teacher.id
    assert payload["data"]["content"] == msg.content
    assert payload["data"]["created_at"] == msg.created_at.isoformat()


@pytest.mark.asyncio
async def test_admin_send_message_in_teacher_serving_uses_teacher_sender_type(monkeypatch):
    db = object()
    admin = _build_user(user_id=1, role=UserRole.admin, staff_id="admin001")
    conv = SimpleNamespace(
        id=90,
        status=ConversationStatus.teacher_serving,
        teacher_id=2001,
    )
    msg = SimpleNamespace(
        id=502,
        conversation_id=conv.id,
        sender_type=SenderType.teacher,
        sender_id=admin.id,
        content="管理员代老师回复",
        created_at=datetime(2026, 4, 21, 5, 4, 0),
    )
    monkeypatch.setattr(
        "app.routers.conversations.get_conversation",
        AsyncMock(return_value=conv),
    )
    add_message_mock = AsyncMock(return_value=msg)
    broadcast_mock = AsyncMock()
    monkeypatch.setattr("app.routers.conversations.add_message", add_message_mock)
    monkeypatch.setattr("app.routers.conversations.manager.broadcast_to_room", broadcast_mock)

    result = await send_message(
        conv.id,
        SendMessageRequest(content=msg.content),
        db=db,
        current_user=admin,
    )

    assert result is msg
    add_message_mock.assert_awaited_once_with(
        db,
        conv.id,
        SenderType.teacher,
        msg.content,
        sender_id=admin.id,
    )
    broadcast_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_teacher_send_message_requires_assigned_teacher(monkeypatch):
    db = object()
    teacher = _build_user(user_id=2002, role=UserRole.teacher, staff_id="teacher002")
    conv = SimpleNamespace(
        id=89,
        status=ConversationStatus.teacher_serving,
        teacher_id=9999,
    )

    monkeypatch.setattr(
        "app.routers.conversations.get_conversation",
        AsyncMock(return_value=conv),
    )

    with pytest.raises(HTTPException) as exc_info:
        await send_message(
            conv.id,
            SendMessageRequest(content="我来回复"),
            db=db,
            current_user=teacher,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "仅接单后可回复该会话"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_value",
    [
        ConversationStatus.ai_serving,
        ConversationStatus.pending_teacher,
        ConversationStatus.resolved,
        ConversationStatus.closed,
    ],
)
async def test_teacher_send_message_requires_teacher_serving_status(monkeypatch, status_value):
    db = object()
    teacher = _build_user(user_id=2003, role=UserRole.teacher, staff_id="teacher003")
    conv = SimpleNamespace(
        id=91,
        status=status_value,
        teacher_id=teacher.id,
    )

    monkeypatch.setattr(
        "app.routers.conversations.get_conversation",
        AsyncMock(return_value=conv),
    )

    with pytest.raises(HTTPException) as exc_info:
        await send_message(
            conv.id,
            SendMessageRequest(content="状态不对时不能发送"),
            db=db,
            current_user=teacher,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "当前会话状态不允许教师回复"


@pytest.mark.asyncio
async def test_teacher_send_message_returns_404_when_conversation_missing(monkeypatch):
    db = object()
    teacher = _build_user(user_id=2004, role=UserRole.teacher, staff_id="teacher004")

    monkeypatch.setattr(
        "app.routers.conversations.get_conversation",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        await send_message(
            999,
            SendMessageRequest(content="找不到会话"),
            db=db,
            current_user=teacher,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "会话不存在"


def test_send_message_request_rejects_blank_content():
    with pytest.raises(ValidationError) as exc_info:
        SendMessageRequest(content="   ")

    assert "content must not be empty" in str(exc_info.value)

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.models.conversation import ConversationStatus, SenderType
from app.models.user import User, UserRole
from app.routers.chat import chat_send
from app.routers.conversations import send_message as conversation_send_message
from app.schemas.chat import ChatSendRequest, ChatSendResponse
from app.schemas.conversation import SendMessageRequest


@pytest.fixture(autouse=True)
def _disable_limiter(monkeypatch):
    monkeypatch.setattr("app.routers.chat.limiter.enabled", False)


def _build_student(*, user_id: int, staff_id: str) -> User:
    return User(
        id=user_id,
        staff_id=staff_id,
        name=f"{staff_id}-name",
        role=UserRole.student,
        college_id=1,
        class_id=None,
        password_hash="hashed",
    )


def _build_student_message(*, message_id: int, conv_id: int, student_id: int, content: str, created_at: datetime):
    return SimpleNamespace(
        id=message_id,
        conversation_id=conv_id,
        sender_type=SenderType.student,
        sender_id=student_id,
        content=content,
        created_at=created_at,
    )


def _build_ai_message(*, message_id: int, conv_id: int, content: str, created_at: datetime):
    return SimpleNamespace(
        id=message_id,
        conversation_id=conv_id,
        sender_type=SenderType.ai,
        sender_id=None,
        content=content,
        created_at=created_at,
        metadata_={"sources": []},
    )


async def _fake_chat_stream_factory(dify_calls: list[dict], ai_msg):
    async def fake_chat_stream(**kwargs):
        dify_calls.append(kwargs)
        yield {
            "event": "message",
            "answer": ai_msg.content,
            "conversation_id": ai_msg.conversation_id,
        }
        yield {
            "event": "message_end",
            "metadata": {"retriever_resources": []},
        }

    return fake_chat_stream


@pytest.mark.asyncio
async def test_chat_send_ai_serving_streams_dify(monkeypatch):
    db = object()
    student = _build_student(user_id=3000, staff_id="student000")
    conv = SimpleNamespace(
        id=65,
        status=ConversationStatus.ai_serving,
        teacher_id=None,
        dify_conversation_id="dify-65",
    )
    student_msg = _build_student_message(
        message_id=600,
        conv_id=conv.id,
        student_id=student.id,
        content="AI 你好",
        created_at=datetime(2026, 4, 21, 5, 0, 0),
    )
    ai_msg = _build_ai_message(
        message_id=604,
        conv_id=conv.id,
        content="这是 AI 的直接回复",
        created_at=datetime(2026, 4, 21, 5, 0, 1),
    )
    dify_calls = []
    broadcast_events = []

    async def fake_broadcast(room_id, payload):
        broadcast_events.append((room_id, payload))

    monkeypatch.setattr("app.routers.chat.get_conversation", AsyncMock(return_value=conv))
    monkeypatch.setattr("app.routers.chat.add_message", AsyncMock(side_effect=[student_msg, ai_msg]))
    monkeypatch.setattr("app.routers.chat.manager.broadcast_to_room", fake_broadcast)
    monkeypatch.setattr(
        "app.routers.chat.dify_client.chat_stream",
        await _fake_chat_stream_factory(dify_calls, ai_msg),
    )

    response = await chat_send(
        None,
        ChatSendRequest(conv_id=conv.id, content=student_msg.content),
        db=db,
        current_user=student,
    )

    assert isinstance(response, StreamingResponse)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)

    assert dify_calls == [{
        "query": student_msg.content,
        "user_id": str(student.id),
        "conversation_id": conv.dify_conversation_id,
        "inputs": {"college_name": "", "campus": "", "class_name": ""},
    }]
    assert broadcast_events[0][1]["data"]["sender_type"] == "student"
    assert broadcast_events[1][1]["data"]["sender_type"] == "ai"
    assert any("message_end" in chunk for chunk in chunks)


@pytest.mark.asyncio
@pytest.mark.parametrize("status_value", [ConversationStatus.pending_teacher, ConversationStatus.teacher_serving])
async def test_chat_send_non_ai_states_return_json_and_skip_dify(monkeypatch, status_value):
    db = object()
    student = _build_student(user_id=3001, staff_id="student001")
    conv = SimpleNamespace(
        id=66,
        status=status_value,
        teacher_id=5001,
        dify_conversation_id="dify-66",
    )
    student_msg = _build_student_message(
        message_id=601,
        conv_id=conv.id,
        student_id=student.id,
        content="老师在吗？",
        created_at=datetime(2026, 4, 21, 5, 1, 0),
    )
    get_conversation_mock = AsyncMock(return_value=conv)
    add_message_mock = AsyncMock(return_value=student_msg)
    broadcast_mock = AsyncMock()

    def fail_chat_stream(*args, **kwargs):
        raise AssertionError(f"{status_value.value} 下不应调用 Dify")

    monkeypatch.setattr("app.routers.chat.get_conversation", get_conversation_mock)
    monkeypatch.setattr("app.routers.chat.add_message", add_message_mock)
    monkeypatch.setattr("app.routers.chat.manager.broadcast_to_room", broadcast_mock)
    monkeypatch.setattr("app.routers.chat.dify_client.chat_stream", fail_chat_stream)

    result = await chat_send(
        None,
        ChatSendRequest(conv_id=conv.id, content=student_msg.content),
        db=db,
        current_user=student,
    )

    assert isinstance(result, ChatSendResponse)
    assert result.conv_id == conv.id
    assert result.message_id == student_msg.id
    assert result.sender_type == "student"
    assert result.content == student_msg.content
    get_conversation_mock.assert_awaited_once_with(db, conv.id, student)
    add_message_mock.assert_awaited_once_with(
        db,
        conv.id,
        SenderType.student,
        student_msg.content,
        sender_id=student.id,
    )
    broadcast_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_send_resolved_reactivates_before_streaming_ai(monkeypatch):
    db = object()
    student = _build_student(user_id=3002, staff_id="student002")
    conv = SimpleNamespace(
        id=67,
        status=ConversationStatus.resolved,
        teacher_id=5002,
        dify_conversation_id="dify-67",
    )
    student_msg = _build_student_message(
        message_id=602,
        conv_id=conv.id,
        student_id=student.id,
        content="我还有一个补充问题",
        created_at=datetime(2026, 4, 21, 5, 2, 0),
    )
    ai_msg = _build_ai_message(
        message_id=603,
        conv_id=conv.id,
        content="这是 AI 的恢复回复",
        created_at=datetime(2026, 4, 21, 5, 2, 1),
    )
    get_conversation_mock = AsyncMock(return_value=conv)
    add_message_mock = AsyncMock(side_effect=[student_msg, ai_msg])
    broadcast_events = []
    dify_calls = []

    async def fake_transition(db_arg, conv_arg, action, actor=None):
        assert db_arg is db
        assert conv_arg is conv
        assert action == "reactivate"
        assert actor is student
        conv.status = ConversationStatus.ai_serving
        return ConversationStatus.ai_serving

    async def fake_broadcast(room_id, payload):
        broadcast_events.append((room_id, payload))

    monkeypatch.setattr("app.routers.chat.get_conversation", get_conversation_mock)
    monkeypatch.setattr("app.routers.chat.add_message", add_message_mock)
    monkeypatch.setattr("app.routers.chat.transition", fake_transition)
    monkeypatch.setattr("app.routers.chat.manager.broadcast_to_room", fake_broadcast)
    monkeypatch.setattr(
        "app.routers.chat.dify_client.chat_stream",
        await _fake_chat_stream_factory(dify_calls, ai_msg),
    )

    response = await chat_send(
        None,
        ChatSendRequest(conv_id=conv.id, content=student_msg.content),
        db=db,
        current_user=student,
    )

    assert isinstance(response, StreamingResponse)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)

    assert dify_calls == [{
        "query": student_msg.content,
        "user_id": str(student.id),
        "conversation_id": conv.dify_conversation_id,
        "inputs": {"college_name": "", "campus": "", "class_name": ""},
    }]
    assert broadcast_events[0][0] == f"conv:{conv.id}"
    assert broadcast_events[0][1]["type"] == "status_changed"
    assert broadcast_events[0][1]["data"]["status"] == "ai_serving"
    assert broadcast_events[1][1]["data"]["sender_type"] == "student"
    assert broadcast_events[2][1]["data"]["sender_type"] == "ai"
    assert add_message_mock.await_count == 2
    assert any("message_end" in chunk for chunk in chunks)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_value",
    [
        ConversationStatus.ai_serving,
        ConversationStatus.pending_teacher,
        ConversationStatus.teacher_serving,
    ],
)
async def test_conversations_send_allows_student_in_active_states(monkeypatch, status_value):
    db = object()
    student = _build_student(user_id=3003, staff_id="student003")
    conv = SimpleNamespace(
        id=68,
        status=status_value,
        teacher_id=5003,
    )
    student_msg = _build_student_message(
        message_id=605,
        conv_id=conv.id,
        student_id=student.id,
        content="我补充一下情况",
        created_at=datetime(2026, 4, 21, 5, 3, 0),
    )
    broadcast_mock = AsyncMock()
    add_message_mock = AsyncMock(return_value=student_msg)

    monkeypatch.setattr("app.routers.conversations.get_conversation", AsyncMock(return_value=conv))
    monkeypatch.setattr("app.routers.conversations.add_message", add_message_mock)
    monkeypatch.setattr("app.routers.conversations.manager.broadcast_to_room", broadcast_mock)

    result = await conversation_send_message(
        conv.id,
        SendMessageRequest(content=student_msg.content),
        db=db,
        current_user=student,
    )

    assert result is student_msg
    add_message_mock.assert_awaited_once_with(
        db,
        conv.id,
        SenderType.student,
        student_msg.content,
        sender_id=student.id,
    )
    broadcast_mock.assert_awaited_once()
    assert broadcast_mock.await_args.args[1]["type"] == "new_message"


@pytest.mark.asyncio
async def test_conversations_send_resolved_reactivates_and_broadcasts(monkeypatch):
    db = object()
    student = _build_student(user_id=3004, staff_id="student004")
    conv = SimpleNamespace(
        id=69,
        status=ConversationStatus.resolved,
        teacher_id=5004,
    )
    student_msg = _build_student_message(
        message_id=606,
        conv_id=conv.id,
        student_id=student.id,
        content="我还有后续问题",
        created_at=datetime(2026, 4, 21, 5, 4, 0),
    )
    broadcast_events = []

    async def fake_transition(db_arg, conv_arg, action, actor=None):
        assert db_arg is db
        assert conv_arg is conv
        assert action == "reactivate"
        assert actor is student
        conv.status = ConversationStatus.ai_serving
        return ConversationStatus.ai_serving

    async def fake_broadcast(room_id, payload):
        broadcast_events.append((room_id, payload))

    monkeypatch.setattr("app.routers.conversations.get_conversation", AsyncMock(return_value=conv))
    monkeypatch.setattr("app.routers.conversations.transition", fake_transition)
    monkeypatch.setattr("app.routers.conversations.add_message", AsyncMock(return_value=student_msg))
    monkeypatch.setattr("app.routers.conversations.manager.broadcast_to_room", fake_broadcast)

    result = await conversation_send_message(
        conv.id,
        SendMessageRequest(content=student_msg.content),
        db=db,
        current_user=student,
    )

    assert result is student_msg
    assert broadcast_events[0][0] == f"conv:{conv.id}"
    assert broadcast_events[0][1] == {
        "type": "status_changed",
        "data": {"conv_id": conv.id, "status": "ai_serving", "previous_status": "resolved"},
    }
    assert broadcast_events[1][1]["type"] == "new_message"
    assert broadcast_events[1][1]["data"]["sender_type"] == "student"


@pytest.mark.asyncio
async def test_conversations_send_rejects_closed(monkeypatch):
    db = object()
    student = _build_student(user_id=3005, staff_id="student005")
    conv = SimpleNamespace(
        id=70,
        status=ConversationStatus.closed,
        teacher_id=5005,
    )
    add_message_mock = AsyncMock()

    monkeypatch.setattr("app.routers.conversations.get_conversation", AsyncMock(return_value=conv))
    monkeypatch.setattr("app.routers.conversations.add_message", add_message_mock)

    with pytest.raises(HTTPException) as exc_info:
        await conversation_send_message(
            conv.id,
            SendMessageRequest(content="关闭后不能发"),
            db=db,
            current_user=student,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "会话已关闭，无法发送消息"
    add_message_mock.assert_not_awaited()

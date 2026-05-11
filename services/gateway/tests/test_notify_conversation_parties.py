"""验证 notify_conversation_parties 的频道路由策略：

- 永远推 conv:{conv.id}
- 推 user#{student_id} 当 student 不是 actor
- 推 user#{teacher_id} 当 teacher 已接单且不是 actor
- legacy ws 永远只推 conv room

这是支撑学生端"老师回复学生不在 chat 详情页时也能立即收到"修复的核心契约。
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.conversation_service import notify_conversation_parties


def _conv(*, id_=42, student_id=18, teacher_id=None):
    return SimpleNamespace(id=id_, student_id=student_id, teacher_id=teacher_id)


@pytest.mark.asyncio
async def test_no_teacher_yet_student_actor_only_pushes_conv_channel(monkeypatch):
    """学生发送消息时只推 conv:{id}，不重复推自己的 user#{student_id}"""
    publish_mock = AsyncMock()
    broadcast_mock_centrifugo = AsyncMock()
    legacy_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.publish", publish_mock
    )
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.broadcast", broadcast_mock_centrifugo
    )
    monkeypatch.setattr(
        "app.services.conversation_service._ws_manager.broadcast_to_room", legacy_mock
    )

    conv = _conv(id_=42, student_id=18, teacher_id=None)
    data = {"type": "new_message", "data": {"id": 1}}

    await notify_conversation_parties(conv, data, actor_id=18)

    publish_mock.assert_awaited_once_with("conv:42", data)
    broadcast_mock_centrifugo.assert_not_awaited()
    legacy_mock.assert_awaited_once_with("conv:42", data)


@pytest.mark.asyncio
async def test_teacher_replies_pushes_to_conv_and_student_user_channel(monkeypatch):
    """教师回复学生：推 conv:{id} + user#{student_id}，但不推自己的 user#{teacher_id}"""
    publish_mock = AsyncMock()
    broadcast_mock = AsyncMock()
    legacy_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.publish", publish_mock
    )
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.broadcast", broadcast_mock
    )
    monkeypatch.setattr(
        "app.services.conversation_service._ws_manager.broadcast_to_room", legacy_mock
    )

    conv = _conv(id_=42, student_id=18, teacher_id=6)
    data = {"type": "new_message", "data": {"id": 99, "sender_type": "teacher"}}

    await notify_conversation_parties(conv, data, actor_id=6)

    # 应该走 broadcast 一次发两个 channel
    publish_mock.assert_not_awaited()
    broadcast_mock.assert_awaited_once()
    args, _kw = broadcast_mock.await_args
    assert set(args[0]) == {"conv:42", "user#18"}
    assert args[1] == data
    legacy_mock.assert_awaited_once_with("conv:42", data)


@pytest.mark.asyncio
async def test_admin_actor_pushes_to_both_user_channels(monkeypatch):
    """admin (非 student 非 teacher) 操作时，conv 双方的 user# 都收到"""
    broadcast_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.publish", AsyncMock()
    )
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.broadcast", broadcast_mock
    )
    monkeypatch.setattr(
        "app.services.conversation_service._ws_manager.broadcast_to_room", AsyncMock()
    )

    conv = _conv(id_=42, student_id=18, teacher_id=6)
    data = {"type": "status_changed", "data": {"conv_id": 42, "status": "closed"}}

    await notify_conversation_parties(conv, data, actor_id=999)  # admin id 不在 conv

    broadcast_mock.assert_awaited_once()
    args, _kw = broadcast_mock.await_args
    assert set(args[0]) == {"conv:42", "user#18", "user#6"}


@pytest.mark.asyncio
async def test_centrifugo_failure_does_not_block_legacy_ws(monkeypatch):
    """Centrifugo 抛错不应影响 legacy ws 广播"""
    failing_publish = AsyncMock(side_effect=RuntimeError("centrifugo down"))
    failing_broadcast = AsyncMock(side_effect=RuntimeError("centrifugo down"))
    legacy_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.publish", failing_publish
    )
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.broadcast", failing_broadcast
    )
    monkeypatch.setattr(
        "app.services.conversation_service._ws_manager.broadcast_to_room", legacy_mock
    )

    conv = _conv(id_=42, student_id=18, teacher_id=6)
    data = {"type": "new_message", "data": {"id": 1}}

    # 不应抛异常
    await notify_conversation_parties(conv, data, actor_id=6)

    legacy_mock.assert_awaited_once_with("conv:42", data)


@pytest.mark.asyncio
async def test_skips_teacher_user_channel_when_no_teacher_assigned(monkeypatch):
    """conv 还没接单 (teacher_id=None) 时，不应该尝试推 user#None"""
    broadcast_mock = AsyncMock()
    publish_mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.publish", publish_mock
    )
    monkeypatch.setattr(
        "app.services.conversation_service.centrifugo.broadcast", broadcast_mock
    )
    monkeypatch.setattr(
        "app.services.conversation_service._ws_manager.broadcast_to_room", AsyncMock()
    )

    conv = _conv(id_=42, student_id=18, teacher_id=None)
    data = {"type": "status_changed", "data": {"status": "pending_teacher"}}

    await notify_conversation_parties(conv, data, actor_id=18)

    # actor=student，且 teacher 未接单 → 只剩 conv 一个 channel
    publish_mock.assert_awaited_once_with("conv:42", data)
    broadcast_mock.assert_not_awaited()

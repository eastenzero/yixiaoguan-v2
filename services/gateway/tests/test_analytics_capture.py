from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError

from app.models.conversation import ConversationStatus, SenderType
from app.models.user import User, UserRole
from app.routers.chat import chat_send
from app.schemas.chat import ChatSendRequest
from app.services.analytics import (
    extract_rag_metrics,
    normalize_query,
    record_chat_analytics,
)


def _build_student(*, user_id: int, staff_id: str) -> User:
    return User(
        id=user_id,
        staff_id=staff_id,
        name=f"{staff_id}-name",
        role=UserRole.student,
        college_id=1,
        class_id=11,
        password_hash="hashed",
    )


def _build_message(*, message_id: int, conv_id: int, sender_type: str, content: str, created_at: datetime):
    return SimpleNamespace(
        id=message_id,
        conversation_id=conv_id,
        sender_type=sender_type,
        sender_id=None,
        content=content,
        created_at=created_at,
        metadata_={"sources": []},
    )


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDB:
    def __init__(self, existing_unanswered=None):
        self.add = MagicMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.execute = AsyncMock(return_value=_FakeExecuteResult(existing_unanswered))


@pytest.mark.parametrize(
    ("raw_query", "expected"),
    [
        ("怎么交电费", "交|电费"),
        ("电费怎么缴", "交|电费"),
        ("  电费缴纳？  ", "交|电费"),
    ],
)
def test_normalize_query_produces_stable_fingerprint(monkeypatch, raw_query, expected):
    token_map = {
        "怎么交电费": ["怎么", "交", "电费"],
        "电费怎么交": ["电费", "怎么", "交"],
        "电费交": ["电费", "交"],
    }
    monkeypatch.setattr("app.services.analytics.jieba.cut", lambda text: token_map[text])
    assert normalize_query(raw_query) == expected


def test_extract_rag_metrics_supports_retriever_resources():
    score, doc_name = extract_rag_metrics(
        {
            "retriever_resources": [
                {"document_name": "电费缴纳.md", "score": 0.85},
                {"document_name": "宿舍管理.md", "score": 0.21},
            ]
        }
    )
    assert score == 0.85
    assert doc_name == "电费缴纳.md"


def test_extract_rag_metrics_supports_retrieval_result_records():
    score, doc_name = extract_rag_metrics(
        {
            "retrieval_result": {
                "records": [
                    {"document_title": "校园卡补办", "score": 0.42},
                    {"document_title": "宿舍管理", "score": 0.35},
                ]
            }
        }
    )
    assert score == 0.42
    assert doc_name == "校园卡补办"


@pytest.mark.asyncio
async def test_record_chat_analytics_hit_path(monkeypatch):
    student = _build_student(user_id=6001, staff_id="student6001")
    db = _FakeDB()
    monkeypatch.setattr("app.services.analytics.jieba.cut", lambda text: ["电费", "交"])

    await record_chat_analytics(
        db,
        conv_id=88,
        user=student,
        raw_query="怎么交电费",
        response_text="可以通过校园生活服务平台缴纳宿舍电费。",
        dify_metadata={
            "retriever_resources": [{"document_name": "电费缴纳.md", "score": 0.85}],
        },
    )

    analytics = db.add.call_args_list[0].args[0]
    assert analytics.conversation_id == 88
    assert analytics.user_id == student.id
    assert analytics.query_norm == "交|电费"
    assert analytics.rag_score == 0.85
    assert analytics.kb_doc_matched == "电费缴纳.md"
    assert analytics.is_answered is True
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_chat_analytics_miss_path_creates_unanswered(monkeypatch):
    student = _build_student(user_id=6002, staff_id="student6002")
    db = _FakeDB()
    monkeypatch.setattr("app.services.analytics.jieba.cut", lambda text: ["交", "电费"])

    await record_chat_analytics(
        db,
        conv_id=89,
        user=student,
        raw_query="电费怎么缴",
        response_text="暂时没有查到明确答案。",
        dify_metadata={"retriever_resources": []},
    )

    analytics = db.add.call_args_list[0].args[0]
    unresolved = db.add.call_args_list[1].args[0]
    assert analytics.rag_score is None
    assert analytics.kb_doc_matched is None
    assert analytics.is_answered is False
    assert unresolved.question_text == "电费怎么缴"
    assert unresolved.hit_count == 1
    assert unresolved.sample_conv_ids == [89]
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_chat_analytics_metadata_missing_does_not_crash(monkeypatch):
    student = _build_student(user_id=6003, staff_id="student6003")
    db = _FakeDB()
    monkeypatch.setattr("app.services.analytics.jieba.cut", lambda text: ["图书馆", "预约"])

    await record_chat_analytics(
        db,
        conv_id=90,
        user=student,
        raw_query="图书馆怎么预约",
        response_text="抱歉，暂时没有相关资料。",
        dify_metadata=None,
    )

    analytics = db.add.call_args_list[0].args[0]
    assert analytics.rag_score is None
    assert analytics.kb_doc_matched is None
    assert analytics.is_answered is False
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_send_ai_path_still_returns_streaming_response_when_analytics_insert_fails(monkeypatch):
    db = object()
    student = _build_student(user_id=6004, staff_id="student6004")
    conv = SimpleNamespace(
        id=92,
        status=ConversationStatus.ai_serving,
        teacher_id=None,
        dify_conversation_id="dify-92",
    )
    student_msg = SimpleNamespace(
        id=702,
        conversation_id=conv.id,
        sender_type=SenderType.student,
        sender_id=student.id,
        content="analytics 不应阻塞",
        created_at=datetime(2026, 4, 21, 12, 0, 0),
    )
    ai_msg = _build_message(
        message_id=703,
        conv_id=conv.id,
        sender_type="ai",
        content="这是 AI 回复",
        created_at=datetime(2026, 4, 21, 12, 0, 1),
    )

    async def fake_chat_stream(**kwargs):
        yield {"event": "message", "answer": ai_msg.content, "conversation_id": conv.dify_conversation_id}
        yield {"event": "message_end", "metadata": {"retriever_resources": []}}

    monkeypatch.setattr("app.routers.chat.get_conversation", AsyncMock(return_value=conv))
    monkeypatch.setattr("app.routers.chat.add_message", AsyncMock(side_effect=[student_msg, ai_msg]))
    monkeypatch.setattr("app.routers.chat.dify_client.chat_stream", fake_chat_stream)
    monkeypatch.setattr("app.routers.chat.manager.broadcast_to_room", AsyncMock())
    monkeypatch.setattr("app.routers.chat._schedule_chat_analytics", lambda **kwargs: None)

    response = await chat_send(
        ChatSendRequest(conv_id=conv.id, content=student_msg.content),
        db=db,
        current_user=student,
    )

    assert isinstance(response, StreamingResponse)
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    assert any("message_end" in chunk for chunk in chunks)


@pytest.mark.asyncio
async def test_record_chat_analytics_eats_integrity_error(caplog, monkeypatch):
    student = _build_student(user_id=6006, staff_id="student6006")
    db = _FakeDB()
    db.add.side_effect = IntegrityError("insert into chat_analytics", {}, Exception("boom"))
    monkeypatch.setattr("app.services.analytics.jieba.cut", lambda text: ["测试"])

    await record_chat_analytics(
        db,
        conv_id=93,
        user=student,
        raw_query="测试问题",
        response_text="没有答案",
        dify_metadata={"retriever_resources": []},
    )

    assert "Failed to record chat analytics" in caplog.text
    db.rollback.assert_awaited_once()

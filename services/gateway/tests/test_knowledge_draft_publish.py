from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.knowledge import KnowledgeScope, SuggestionStatus
from app.models.user import User, UserRole
from app.services.knowledge_service import create_knowledge_draft, create_knowledge_draft_preview


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDB:
    def __init__(self, execute_results: list[object]):
        self._execute_results = list(execute_results)
        self.add = MagicMock(side_effect=self._capture_add)
        self.flush = AsyncMock(side_effect=self._flush)
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.refresh = AsyncMock()
        self.execute = AsyncMock(side_effect=self._execute)
        self.added: list[object] = []

    def _capture_add(self, value):
        self.added.append(value)

    async def _flush(self):
        for index, item in enumerate(self.added, start=1):
            if getattr(item, "id", None) is None:
                setattr(item, "id", 900 + index)
            if getattr(item, "created_at", None) is None:
                setattr(item, "created_at", datetime(2026, 4, 21, 13, 0, 0))

    async def _execute(self, statement):
        if not self._execute_results:
            raise AssertionError(f"unexpected execute: {statement}")
        return _FakeExecuteResult(self._execute_results.pop(0))


def _build_user(*, user_id: int, role: UserRole, college_id: int | None, class_id: int | None, staff_id: str) -> User:
    return User(
        id=user_id,
        staff_id=staff_id,
        name=f"{staff_id}-name",
        role=role,
        college_id=college_id,
        class_id=class_id,
        password_hash="hashed",
    )


def _build_unanswered(*, item_id: int, question_text: str, question_hash: str, college_id: int | None):
    return SimpleNamespace(
        id=item_id,
        question_text=question_text,
        question_hash=question_hash,
        college_id=college_id,
        hit_count=6,
        is_resolved=False,
        kb_suggestion_id=None,
    )


def _build_mapping(*, college_id: int, dataset_id: str):
    return SimpleNamespace(id=1, college_id=college_id, dify_dataset_id=dataset_id)


@pytest.mark.asyncio
async def test_create_knowledge_draft_preview_polishes_without_publishing(monkeypatch):
    teacher = _build_user(user_id=8000, role=UserRole.teacher, college_id=1, class_id=11, staff_id="teacher8000")
    unanswered = _build_unanswered(
        item_id=9,
        question_text="宿舍电费怎么交",
        question_hash="hash-preview",
        college_id=1,
    )
    db = _FakeDB([unanswered])

    polish_mock = AsyncMock(return_value="润色后的预览内容")
    monkeypatch.setattr("app.services.knowledge_service.polish_knowledge_content", polish_mock)
    create_document_mock = AsyncMock()
    monkeypatch.setattr("app.services.knowledge_service.dify_client.create_document", create_document_mock)

    preview = await create_knowledge_draft_preview(
        db,
        current_user=teacher,
        unanswered_question_id=unanswered.id,
        raw_answer="可以在校园生活服务平台缴费。",
        scope="class",
        scope_value=11,
    )

    assert preview["title"] == "宿舍电费怎么交"
    assert preview["raw_content"] == "可以在校园生活服务平台缴费。"
    assert preview["content"] == "润色后的预览内容"
    assert preview["scope"] == "class"
    assert preview["scope_value"] == 11
    assert preview["publish_mode"] == "requires_confirmation"
    assert unanswered.is_resolved is False
    assert unanswered.kb_suggestion_id is None
    assert db.added == []
    db.commit.assert_not_awaited()
    create_document_mock.assert_not_awaited()
    polish_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_knowledge_draft_class_scope_confirmed_publish(monkeypatch):
    teacher = _build_user(user_id=8001, role=UserRole.teacher, college_id=1, class_id=11, staff_id="teacher8001")
    unanswered = _build_unanswered(
        item_id=10,
        question_text="宿舍电费怎么交",
        question_hash="hash-electricity",
        college_id=1,
    )
    db = _FakeDB([unanswered, _build_mapping(college_id=1, dataset_id="dataset-college-1")])

    polish_mock = AsyncMock(return_value="不应在确认发布时润色")
    monkeypatch.setattr("app.services.knowledge_service.polish_knowledge_content", polish_mock)
    create_document_mock = AsyncMock(return_value={"document": {"id": "doc-class-1"}})
    monkeypatch.setattr("app.services.knowledge_service.dify_client.create_document", create_document_mock)

    entry, publish_mode = await create_knowledge_draft(
        db,
        current_user=teacher,
        unanswered_question_id=unanswered.id,
        raw_answer="可以在校园生活服务平台缴费。",
        confirmed_content="教师确认后的班级知识内容",
        scope="class",
        scope_value=11,
    )

    assert publish_mode == "published"
    assert entry.content == "教师确认后的班级知识内容"
    assert entry.scope == KnowledgeScope.class_
    assert entry.scope_value == 11
    assert entry.status == SuggestionStatus.approved
    assert entry.dify_document_id == "doc-class-1"
    assert entry.published_at is not None
    assert unanswered.is_resolved is True
    assert unanswered.kb_suggestion_id == entry.id
    polish_mock.assert_not_awaited()
    create_document_mock.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_knowledge_draft_college_scope_confirmed_publish(monkeypatch):
    teacher = _build_user(user_id=8002, role=UserRole.teacher, college_id=2, class_id=None, staff_id="teacher8002")
    unanswered = _build_unanswered(
        item_id=11,
        question_text="图书馆预约怎么操作",
        question_hash="hash-library",
        college_id=2,
    )
    db = _FakeDB([unanswered, _build_mapping(college_id=2, dataset_id="dataset-college-2")])

    polish_mock = AsyncMock(return_value="不应在确认发布时润色")
    monkeypatch.setattr("app.services.knowledge_service.polish_knowledge_content", polish_mock)
    monkeypatch.setattr(
        "app.services.knowledge_service.dify_client.create_document",
        AsyncMock(return_value={"document": {"id": "doc-college-2"}}),
    )

    entry, publish_mode = await create_knowledge_draft(
        db,
        current_user=teacher,
        unanswered_question_id=unanswered.id,
        raw_answer="可在图书馆系统中预约。",
        confirmed_content="教师确认后的学院知识内容",
        scope="college",
        scope_value=2,
    )

    assert publish_mode == "published"
    assert entry.content == "教师确认后的学院知识内容"
    assert entry.scope == KnowledgeScope.college
    assert entry.scope_value == 2
    assert entry.status == SuggestionStatus.approved
    assert unanswered.is_resolved is True
    polish_mock.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_knowledge_draft_global_scope_stays_pending(monkeypatch):
    teacher = _build_user(user_id=8003, role=UserRole.teacher, college_id=1, class_id=None, staff_id="teacher8003")
    unanswered = _build_unanswered(
        item_id=12,
        question_text="毕业证补办流程",
        question_hash="hash-global",
        college_id=1,
    )
    db = _FakeDB([unanswered])

    polish_mock = AsyncMock(return_value="不应在确认发布时润色")
    monkeypatch.setattr("app.services.knowledge_service.polish_knowledge_content", polish_mock)
    create_document_mock = AsyncMock()
    monkeypatch.setattr("app.services.knowledge_service.dify_client.create_document", create_document_mock)

    entry, publish_mode = await create_knowledge_draft(
        db,
        current_user=teacher,
        unanswered_question_id=unanswered.id,
        raw_answer="需要联系教务处补办。",
        confirmed_content="教师确认后的全校知识内容",
        scope="global",
        scope_value=None,
    )

    assert publish_mode == "pending_review"
    assert entry.content == "教师确认后的全校知识内容"
    assert entry.scope == KnowledgeScope.global_
    assert entry.status == SuggestionStatus.pending
    assert entry.dify_document_id is None
    assert unanswered.is_resolved is False
    assert unanswered.kb_suggestion_id == entry.id
    polish_mock.assert_not_awaited()
    create_document_mock.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_knowledge_draft_rejects_cross_scope(monkeypatch):
    teacher = _build_user(user_id=8004, role=UserRole.teacher, college_id=1, class_id=11, staff_id="teacher8004")
    unanswered = _build_unanswered(
        item_id=13,
        question_text="晚归申请流程",
        question_hash="hash-late-return",
        college_id=1,
    )
    db = _FakeDB([unanswered])
    monkeypatch.setattr(
        "app.services.knowledge_service.polish_knowledge_content",
        AsyncMock(return_value="不会用到"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_knowledge_draft(
            db,
            current_user=teacher,
            unanswered_question_id=unanswered.id,
            raw_answer="去辅导员处登记。",
            scope="class",
            scope_value=99,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "教师不能发布到其他班级"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_knowledge_draft_rejects_unconfirmed_publish(monkeypatch):
    teacher = _build_user(user_id=8008, role=UserRole.teacher, college_id=1, class_id=None, staff_id="teacher8008")
    unanswered = _build_unanswered(
        item_id=17,
        question_text="宿舍维修怎么报修",
        question_hash="hash-unconfirmed",
        college_id=1,
    )
    db = _FakeDB([unanswered])
    polish_mock = AsyncMock(return_value="不应在未确认发布时润色")
    monkeypatch.setattr("app.services.knowledge_service.polish_knowledge_content", polish_mock)

    with pytest.raises(HTTPException) as exc_info:
        await create_knowledge_draft(
            db,
            current_user=teacher,
            unanswered_question_id=unanswered.id,
            raw_answer="到宿管平台报修。",
            scope="college",
            scope_value=1,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "请先生成润色预览并确认发布内容"
    assert db.added == []
    db.commit.assert_not_awaited()
    polish_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_knowledge_draft_rolls_back_on_dify_failure(monkeypatch):
    teacher = _build_user(user_id=8005, role=UserRole.teacher, college_id=1, class_id=None, staff_id="teacher8005")
    unanswered = _build_unanswered(
        item_id=14,
        question_text="宿舍维修怎么报修",
        question_hash="hash-repair",
        college_id=1,
    )
    db = _FakeDB([unanswered, _build_mapping(college_id=1, dataset_id="dataset-college-1")])

    monkeypatch.setattr(
        "app.services.knowledge_service.polish_knowledge_content",
        AsyncMock(return_value="润色后的内容"),
    )
    monkeypatch.setattr(
        "app.services.knowledge_service.dify_client.create_document",
        AsyncMock(side_effect=RuntimeError("dify unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_knowledge_draft(
            db,
            current_user=teacher,
            unanswered_question_id=unanswered.id,
            raw_answer="到宿管平台报修。",
            confirmed_content="教师确认后的报修知识",
            scope="college",
            scope_value=1,
        )

    assert exc_info.value.status_code == 502
    assert "Dify 发布失败" in exc_info.value.detail
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_knowledge_draft_uses_confirmed_content_without_repolishing(monkeypatch):
    teacher = _build_user(user_id=8007, role=UserRole.teacher, college_id=1, class_id=None, staff_id="teacher8007")
    unanswered = _build_unanswered(
        item_id=16,
        question_text="校园卡丢了怎么办",
        question_hash="hash-confirmed",
        college_id=1,
    )
    db = _FakeDB([unanswered, _build_mapping(college_id=1, dataset_id="dataset-college-1")])

    polish_mock = AsyncMock(return_value="不应该再次润色")
    monkeypatch.setattr("app.services.knowledge_service.polish_knowledge_content", polish_mock)
    create_document_mock = AsyncMock(return_value={"document": {"id": "doc-confirmed-1"}})
    monkeypatch.setattr("app.services.knowledge_service.dify_client.create_document", create_document_mock)

    entry, publish_mode = await create_knowledge_draft(
        db,
        current_user=teacher,
        unanswered_question_id=unanswered.id,
        raw_answer="先挂失，再到服务中心补办。",
        confirmed_content="教师确认后的最终知识内容",
        scope="college",
        scope_value=1,
    )

    assert publish_mode == "published"
    assert entry.content == "教师确认后的最终知识内容"
    polish_mock.assert_not_awaited()
    create_document_mock.assert_awaited_once()
    assert create_document_mock.await_args.kwargs["content"] == "教师确认后的最终知识内容"


@pytest.mark.asyncio
async def test_create_knowledge_draft_preview_uses_fallback_when_polish_fails(monkeypatch):
    teacher = _build_user(user_id=8006, role=UserRole.teacher, college_id=1, class_id=None, staff_id="teacher8006")
    unanswered = _build_unanswered(
        item_id=15,
        question_text="校园卡丢了怎么办",
        question_hash="hash-card-loss",
        college_id=1,
    )
    db = _FakeDB([unanswered])

    monkeypatch.setattr(
        "app.services.knowledge_service.dify_client.polish_text",
        AsyncMock(side_effect=RuntimeError("polish down")),
    )
    create_document_mock = AsyncMock()
    monkeypatch.setattr("app.services.knowledge_service.dify_client.create_document", create_document_mock)

    preview = await create_knowledge_draft_preview(
        db,
        current_user=teacher,
        unanswered_question_id=unanswered.id,
        raw_answer="先挂失，再到服务中心补办。",
        scope="college",
        scope_value=1,
    )

    assert preview["publish_mode"] == "requires_confirmation"
    assert "适用范围：学院 1" in preview["content"]
    assert "问题：校园卡丢了怎么办" in preview["content"]
    assert "答复：先挂失，再到服务中心补办。" in preview["content"]
    assert db.added == []
    db.commit.assert_not_awaited()
    create_document_mock.assert_not_awaited()

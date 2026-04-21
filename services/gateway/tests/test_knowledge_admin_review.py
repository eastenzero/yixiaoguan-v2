from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.knowledge import KnowledgeScope, SuggestionStatus
from app.models.user import User, UserRole
from app.routers.knowledge import approve_review, get_pending_reviews, reject_review
from app.schemas.knowledge import RejectKnowledgeReviewRequest
from app.services.knowledge_service import approve_pending_review, list_pending_reviews, reject_pending_review


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return SimpleNamespace(all=lambda: self._value)


class _FakeDB:
    def __init__(self, execute_results: list[object]):
        self._execute_results = list(execute_results)
        self.add = MagicMock(side_effect=self._capture_add)
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.refresh = AsyncMock()
        self.execute = AsyncMock(side_effect=self._execute)
        self.added: list[object] = []

    def _capture_add(self, value):
        self.added.append(value)

    async def _execute(self, statement):
        if not self._execute_results:
            raise AssertionError(f"unexpected execute: {statement}")
        return _FakeExecuteResult(self._execute_results.pop(0))


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


def _build_pending_entry(*, entry_id: int):
    return SimpleNamespace(
        id=entry_id,
        title="毕业证补办流程",
        content="全校统一补办流程",
        raw_content="联系教务处补办",
        scope=KnowledgeScope.global_,
        scope_value=None,
        representative_query="毕业证补办流程",
        status=SuggestionStatus.pending,
        college_id=1,
        submitted_by=8101,
        reviewed_by=None,
        reject_reason=None,
        dify_document_id=None,
        created_at=datetime(2026, 4, 21, 13, 0, 0),
        published_at=None,
        reviewed_at=None,
    )


@pytest.mark.asyncio
async def test_list_pending_reviews_only_admin_can_access():
    teacher = _build_user(user_id=9101, role=UserRole.teacher, staff_id="teacher9101")

    with pytest.raises(HTTPException) as exc_info:
        await list_pending_reviews(SimpleNamespace(execute=AsyncMock()), teacher, limit=20)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "仅管理员可执行审核操作"


@pytest.mark.asyncio
async def test_get_pending_reviews_returns_global_pending_items(monkeypatch):
    admin = _build_user(user_id=9102, role=UserRole.admin, staff_id="admin9102")
    item = _build_pending_entry(entry_id=31)
    monkeypatch.setattr("app.routers.knowledge.list_pending_reviews", AsyncMock(return_value=([item], 1)))

    result = await get_pending_reviews(limit=20, db=object(), current_user=admin)

    assert result.total == 1
    assert result.items[0].id == 31
    assert result.items[0].scope == "global"
    assert result.items[0].status == "pending"


@pytest.mark.asyncio
async def test_approve_pending_review_publishes_and_marks_approved(monkeypatch):
    admin = _build_user(user_id=9103, role=UserRole.admin, staff_id="admin9103")
    entry = _build_pending_entry(entry_id=32)
    db = _FakeDB([entry, SimpleNamespace(id=1, college_id=1, dify_dataset_id="dataset-global")])

    monkeypatch.setattr(
        "app.services.knowledge_service.dify_client.create_document",
        AsyncMock(return_value={"document": {"id": "doc-global-32"}}),
    )

    approved = await approve_pending_review(
        db,
        current_user=admin,
        suggestion_id=entry.id,
    )

    assert approved.status == SuggestionStatus.approved
    assert approved.reviewed_by == admin.id
    assert approved.dify_document_id == "doc-global-32"
    assert approved.published_at is not None
    assert approved.reviewed_at is not None
    db.commit.assert_awaited_once()
    assert len(db.added) == 1


@pytest.mark.asyncio
async def test_reject_pending_review_marks_rejected_and_keeps_reason():
    admin = _build_user(user_id=9104, role=UserRole.admin, staff_id="admin9104")
    entry = _build_pending_entry(entry_id=33)
    db = _FakeDB([entry])

    rejected = await reject_pending_review(
        db,
        current_user=admin,
        suggestion_id=entry.id,
        reject_reason="需补充全校适用依据",
    )

    assert rejected.status == SuggestionStatus.rejected
    assert rejected.reviewed_by == admin.id
    assert rejected.reject_reason == "需补充全校适用依据"
    assert rejected.reviewed_at is not None
    db.commit.assert_awaited_once()
    assert db.added == []


@pytest.mark.asyncio
async def test_approve_pending_review_rejects_repeat_review():
    admin = _build_user(user_id=9105, role=UserRole.admin, staff_id="admin9105")
    entry = _build_pending_entry(entry_id=34)
    entry.status = SuggestionStatus.approved
    db = _FakeDB([entry])

    with pytest.raises(HTTPException) as exc_info:
        await approve_pending_review(
            db,
            current_user=admin,
            suggestion_id=entry.id,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "该知识条目不可重复审核"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_reject_pending_review_rejects_repeat_review():
    admin = _build_user(user_id=9106, role=UserRole.admin, staff_id="admin9106")
    entry = _build_pending_entry(entry_id=35)
    entry.status = SuggestionStatus.rejected
    db = _FakeDB([entry])

    with pytest.raises(HTTPException) as exc_info:
        await reject_pending_review(
            db,
            current_user=admin,
            suggestion_id=entry.id,
            reject_reason=None,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "该知识条目不可重复审核"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_router_reject_review_uses_default_reason(monkeypatch):
    admin = _build_user(user_id=9107, role=UserRole.admin, staff_id="admin9107")
    entry = _build_pending_entry(entry_id=36)
    entry.status = SuggestionStatus.rejected
    entry.reject_reason = "管理员驳回"
    entry.reviewed_by = admin.id
    entry.reviewed_at = datetime(2026, 4, 21, 14, 0, 0)
    monkeypatch.setattr("app.routers.knowledge.reject_pending_review", AsyncMock(return_value=entry))

    result = await reject_review(
        suggestion_id=entry.id,
        body=RejectKnowledgeReviewRequest(reject_reason=None),
        db=object(),
        current_user=admin,
    )

    assert result.entry.reject_reason == "管理员驳回"
    assert result.entry.status == "rejected"
    assert result.publish_mode == "pending_review"


@pytest.mark.asyncio
async def test_router_approve_review_returns_published_mode(monkeypatch):
    admin = _build_user(user_id=9108, role=UserRole.admin, staff_id="admin9108")
    entry = _build_pending_entry(entry_id=37)
    entry.status = SuggestionStatus.approved
    entry.reviewed_by = admin.id
    entry.reviewed_at = datetime(2026, 4, 21, 14, 5, 0)
    entry.published_at = datetime(2026, 4, 21, 14, 5, 0)
    entry.dify_document_id = "doc-approved-37"
    monkeypatch.setattr("app.routers.knowledge.approve_pending_review", AsyncMock(return_value=entry))

    result = await approve_review(
        suggestion_id=entry.id,
        db=object(),
        current_user=admin,
    )

    assert result.publish_mode == "published"
    assert result.entry.status == "approved"
    assert result.entry.dify_document_id == "doc-approved-37"

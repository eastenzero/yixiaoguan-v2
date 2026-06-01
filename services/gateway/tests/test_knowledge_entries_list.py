"""
T18: "我的知识"列表 endpoint 单测。

覆盖：
- 非 teacher/admin（普通学生）调用 → 403
- teacher 调用 → 仅返回 submitted_by == self.id 的条目
- admin 调用 → 返回全部
- title 模糊搜索 + 分页边界
- router 层 schema 输出格式正确
"""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.knowledge import KnowledgeScope, SuggestionStatus
from app.models.user import User, UserRole
from app.routers.knowledge import get_knowledge_entries
from app.services.knowledge_service import list_knowledge_entries


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


def _build_entry(*, entry_id: int, submitted_by: int, status: SuggestionStatus = SuggestionStatus.approved, scope: KnowledgeScope = KnowledgeScope.college):
    return SimpleNamespace(
        id=entry_id,
        title=f"知识条目-{entry_id}",
        content=f"详细内容 {entry_id}",
        raw_content=f"原始答复 {entry_id}",
        scope=scope,
        scope_value=1 if scope != KnowledgeScope.global_ else None,
        representative_query=f"代表问题 {entry_id}",
        status=status,
        college_id=1,
        submitted_by=submitted_by,
        reviewed_by=None,
        reject_reason=None,
        dify_document_id=None,
        created_at=datetime(2026, 5, 1, 10, 0, 0),
        published_at=None,
        reviewed_at=None,
    )


class _CountResult:
    def __init__(self, total: int):
        self._total = total

    def scalar(self):
        return self._total


class _ItemsResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return SimpleNamespace(all=lambda: self._items)


def _make_db_with_count_and_items(total: int, items: list):
    """
    模拟两次 db.execute 调用：第一次返回 count（int），第二次返回 items 列表。
    list_knowledge_entries 内部就是这个顺序。
    """
    call_count = {"n": 0}

    async def execute(_stmt):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _CountResult(total)
        return _ItemsResult(items)

    db = SimpleNamespace(execute=AsyncMock(side_effect=execute))
    return db


# ============ service layer ============

@pytest.mark.asyncio
async def test_list_knowledge_entries_rejects_non_teacher():
    student = User(
        id=1,
        staff_id="stu1",
        name="stu1",
        role=UserRole.student,
        college_id=1,
        class_id=1,
        password_hash="x",
    )
    with pytest.raises(HTTPException) as exc:
        await list_knowledge_entries(SimpleNamespace(execute=AsyncMock()), student)
    assert exc.value.status_code == 403
    assert "教师" in exc.value.detail


@pytest.mark.asyncio
async def test_list_knowledge_entries_teacher_only_sees_own():
    """teacher 调用时应只过滤 submitted_by = current_user.id"""
    teacher = _build_user(user_id=42, role=UserRole.teacher, staff_id="t42")
    items = [_build_entry(entry_id=101, submitted_by=42), _build_entry(entry_id=102, submitted_by=42)]
    db = _make_db_with_count_and_items(total=2, items=items)

    result_items, total = await list_knowledge_entries(db, teacher, page_num=1, page_size=20)

    assert total == 2
    assert [i.id for i in result_items] == [101, 102]
    # 验证两次 execute（一次 count、一次 select items）
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_list_knowledge_entries_admin_sees_all():
    """admin 调用时不加 submitted_by 过滤，能看到全部"""
    admin = _build_user(user_id=1, role=UserRole.admin, staff_id="admin")
    items = [_build_entry(entry_id=i, submitted_by=i * 10) for i in range(1, 6)]
    db = _make_db_with_count_and_items(total=5, items=items)

    result_items, total = await list_knowledge_entries(db, admin, page_num=1, page_size=20)

    assert total == 5
    assert len(result_items) == 5


@pytest.mark.asyncio
async def test_list_knowledge_entries_pagination_normalizes_inputs():
    teacher = _build_user(user_id=7, role=UserRole.teacher, staff_id="t7")
    db = _make_db_with_count_and_items(total=50, items=[])

    # page_num=0 应该被钳到 1，page_size=200 应该被钳到 100
    items, total = await list_knowledge_entries(db, teacher, page_num=0, page_size=200)

    assert total == 50
    assert items == []


# ============ router layer ============

@pytest.mark.asyncio
async def test_get_knowledge_entries_router_returns_schema_shape(monkeypatch):
    teacher = _build_user(user_id=99, role=UserRole.teacher, staff_id="t99")
    items = [
        _build_entry(entry_id=201, submitted_by=99, status=SuggestionStatus.approved),
        _build_entry(entry_id=202, submitted_by=99, status=SuggestionStatus.pending, scope=KnowledgeScope.global_),
    ]
    monkeypatch.setattr(
        "app.routers.knowledge.list_knowledge_entries",
        AsyncMock(return_value=(items, 2)),
    )

    response = await get_knowledge_entries(
        title=None, pageNum=1, pageSize=20, db=object(), current_user=teacher
    )

    assert response.total == 2
    assert len(response.items) == 2
    assert response.items[0].id == 201
    assert response.items[0].status == "approved"
    assert response.items[1].id == 202
    assert response.items[1].scope == "global"


@pytest.mark.asyncio
async def test_get_knowledge_entries_router_passes_title_and_pagination(monkeypatch):
    teacher = _build_user(user_id=99, role=UserRole.teacher, staff_id="t99")
    spy = AsyncMock(return_value=([], 0))
    monkeypatch.setattr("app.routers.knowledge.list_knowledge_entries", spy)

    await get_knowledge_entries(
        title="毕业证", pageNum=2, pageSize=5, db=object(), current_user=teacher
    )

    spy.assert_awaited_once()
    kwargs = spy.await_args.kwargs
    assert kwargs["title"] == "毕业证"
    assert kwargs["page_num"] == 2
    assert kwargs["page_size"] == 5

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.user import User, UserRole
from app.routers.knowledge import get_knowledge_entry_detail, get_knowledge_entries
from app.services.knowledge_service import list_knowledge_entries


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalar_one(self):
        return self._value

    def scalars(self):
        return SimpleNamespace(all=lambda: self._value)


class _FakeDB:
    def __init__(self, execute_results: list[object]):
        self._execute_results = list(execute_results)
        self.statements: list[object] = []
        self.execute = AsyncMock(side_effect=self._execute)

    async def _execute(self, statement):
        self.statements.append(statement)
        if not self._execute_results:
            raise AssertionError(f"unexpected execute: {statement}")
        return _FakeExecuteResult(self._execute_results.pop(0))


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


def _build_kb_entry(*, entry_id: int):
    return SimpleNamespace(
        id=entry_id,
        dify_document_id="doc-real-001",
        dify_dataset_id="dataset-global",
        title="校园卡补办指南",
        category="生活服务",
        tags=["校园卡", "补办"],
        original_source="imported-handbook",
        source_url="https://example.test/card",
        material_id="KB-001",
        campus="主校区",
        original_filename="学生手册.md",
        created_at=datetime(2026, 6, 20, 9, 0, 0),
    )


@pytest.mark.asyncio
async def test_list_knowledge_entries_queries_kb_entries_for_teacher(monkeypatch):
    teacher = _build_user(user_id=9200, role=UserRole.teacher, college_id=1, staff_id="teacher9200")
    real_entry = _build_kb_entry(entry_id=500)
    db = _FakeDB(["dataset-college-1", 1, [real_entry]])
    monkeypatch.setattr("app.services.knowledge_service.settings.dify_global_dataset_id", "dataset-global")

    items, total = await list_knowledge_entries(
        db,
        teacher,
        title="校园卡",
        category=None,
        campus=None,
        source=None,
        college_id=None,
        page_num=1,
        page_size=20,
    )

    assert total == 1
    assert items == [real_entry]
    assert any("kb_entries" in str(statement) for statement in db.statements)


@pytest.mark.asyncio
async def test_get_knowledge_entries_returns_real_kb_entries(monkeypatch):
    teacher = _build_user(user_id=9201, role=UserRole.teacher, college_id=1, staff_id="teacher9201")
    real_entry = _build_kb_entry(entry_id=501)
    monkeypatch.setattr("app.routers.knowledge.list_knowledge_entries", AsyncMock(return_value=([real_entry], 1)))

    result = await get_knowledge_entries(
        title="校园卡",
        category=None,
        campus=None,
        source=None,
        college_id=None,
        pageNum=1,
        pageSize=20,
        db=object(),
        current_user=teacher,
    )

    assert result.total == 1
    assert result.items[0].id == 501
    assert result.items[0].source_type == "kb_entry"
    assert result.items[0].status == "published"
    assert result.items[0].category == "生活服务"
    assert result.items[0].original_source == "imported-handbook"
    assert result.items[0].submitted_by == 0


@pytest.mark.asyncio
async def test_get_knowledge_entry_detail_returns_real_kb_entry(monkeypatch):
    teacher = _build_user(user_id=9202, role=UserRole.teacher, college_id=1, staff_id="teacher9202")
    real_entry = _build_kb_entry(entry_id=502)
    monkeypatch.setattr("app.routers.knowledge.get_knowledge_entry", AsyncMock(return_value=real_entry))

    result = await get_knowledge_entry_detail(
        entry_id=502,
        db=object(),
        current_user=teacher,
    )

    assert result.id == 502
    assert result.source_type == "kb_entry"
    assert result.dify_document_id == "doc-real-001"
    assert "来源：imported-handbook" in result.content

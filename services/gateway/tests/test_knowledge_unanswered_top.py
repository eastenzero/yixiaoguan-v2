from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.routers.knowledge import get_unanswered_top
from app.services.knowledge_service import list_unanswered_top


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


def _build_unanswered(*, item_id: int, question_text: str, hit_count: int, college_id: int | None, updated_at: datetime, is_resolved: bool = False):
    return SimpleNamespace(
        id=item_id,
        question_text=question_text,
        hit_count=hit_count,
        college_id=college_id,
        updated_at=updated_at,
        is_resolved=is_resolved,
        sample_conv_ids=[80 + item_id],
    )


@pytest.mark.asyncio
async def test_list_unanswered_top_teacher_filters_to_same_college_and_null(monkeypatch):
    teacher = _build_user(user_id=7001, role=UserRole.teacher, college_id=1, staff_id="teacher7001")
    db_execute = AsyncMock(return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [])))
    db = SimpleNamespace(execute=db_execute)
    same_college = _build_unanswered(
        item_id=1,
        question_text="宿舍电费怎么交",
        hit_count=8,
        college_id=1,
        updated_at=datetime(2026, 4, 21, 11, 0, 0),
    )
    no_college = _build_unanswered(
        item_id=2,
        question_text="校园卡补办去哪",
        hit_count=5,
        college_id=None,
        updated_at=datetime(2026, 4, 21, 10, 0, 0),
    )

    db_execute.return_value = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [same_college, no_college]))

    items, total = await list_unanswered_top(db, teacher, limit=20)

    assert total == 2
    assert [item.id for item in items] == [1, 2]
    statement = db_execute.await_args.args[0]
    rendered = str(statement)
    assert "unanswered_questions.is_resolved IS false" in rendered
    assert "unanswered_questions.college_id = :college_id_1 OR unanswered_questions.college_id IS NULL" in rendered


@pytest.mark.asyncio
async def test_get_unanswered_top_admin_can_see_cross_college(monkeypatch):
    admin = _build_user(user_id=7002, role=UserRole.admin, college_id=None, staff_id="admin7002")
    db = object()
    items = [
        _build_unanswered(
            item_id=3,
            question_text="图书馆预约怎么操作",
            hit_count=9,
            college_id=1,
            updated_at=datetime(2026, 4, 21, 11, 30, 0),
        ),
        _build_unanswered(
            item_id=4,
            question_text="护理实习请假流程",
            hit_count=7,
            college_id=2,
            updated_at=datetime(2026, 4, 21, 11, 20, 0),
        ),
    ]
    monkeypatch.setattr("app.routers.knowledge.list_unanswered_top", AsyncMock(return_value=(items, 2)))

    result = await get_unanswered_top(limit=20, db=db, current_user=admin)

    assert result.total == 2
    assert result.items[0].college_id == 1
    assert result.items[1].college_id == 2


@pytest.mark.asyncio
async def test_get_unanswered_top_limit_is_applied(monkeypatch):
    teacher = _build_user(user_id=7003, role=UserRole.teacher, college_id=1, staff_id="teacher7003")
    db = object()
    item = _build_unanswered(
        item_id=5,
        question_text="奖学金申请时间",
        hit_count=6,
        college_id=1,
        updated_at=datetime(2026, 4, 21, 9, 0, 0),
    )
    list_mock = AsyncMock(return_value=([item], 1))
    monkeypatch.setattr("app.routers.knowledge.list_unanswered_top", list_mock)

    result = await get_unanswered_top(limit=1, db=db, current_user=teacher)

    assert result.total == 1
    list_mock.assert_awaited_once_with(db, teacher, limit=1)


@pytest.mark.asyncio
async def test_get_unanswered_top_filters_resolved_in_service(monkeypatch):
    teacher = _build_user(user_id=7004, role=UserRole.teacher, college_id=1, staff_id="teacher7004")
    db_execute = AsyncMock(return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [])))
    db = SimpleNamespace(execute=db_execute)
    active_item = _build_unanswered(
        item_id=6,
        question_text="晚归申请流程",
        hit_count=4,
        college_id=1,
        updated_at=datetime(2026, 4, 21, 8, 0, 0),
    )
    db_execute.return_value = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [active_item]))

    items, total = await list_unanswered_top(db, teacher, limit=20)

    assert total == 1
    assert items[0].is_resolved is False
    assert "unanswered_questions.is_resolved IS false" in str(db_execute.await_args.args[0])


@pytest.mark.asyncio
async def test_get_unanswered_top_student_forbidden():
    student = _build_user(user_id=7005, role=UserRole.student, college_id=1, staff_id="student7005")

    with pytest.raises(HTTPException) as exc_info:
        await get_unanswered_top(limit=20, db=object(), current_user=student)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "仅教师或管理员可查看待补问题"

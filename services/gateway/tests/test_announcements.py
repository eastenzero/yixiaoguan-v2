from datetime import datetime, timedelta, UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.announcement import Announcement, AnnouncementRead
from app.models.user import User, UserRole
from app.services.announcement_service import (
    create_announcement,
    list_my_announcements,
    update_announcement,
    delete_announcement,
    get_active_announcements_for_user,
    mark_announcement_read,
)


class _FakeScalarResult:
    def __init__(self, values):
        self._values = list(values)

    def all(self):
        return self._values


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return _FakeScalarResult(self._value if isinstance(self._value, list) else [self._value] if self._value is not None else [])


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
        return self._execute_results.pop(0)


def _build_user(*, user_id: int, role: UserRole, college_id: int | None = None, class_id: int | None = None, staff_id: str = "u") -> User:
    return User(
        id=user_id,
        staff_id=staff_id,
        name=f"{staff_id}-name",
        role=role,
        college_id=college_id,
        class_id=class_id,
        password_hash="hashed",
    )


def _build_announcement(**kwargs) -> Announcement:
    defaults = dict(
        id=1,
        title="标题",
        content="内容",
        target_type="class",
        target_value=10,
        created_by=100,
        expire_at=datetime(2099, 1, 1),
        is_active=True,
        created_at=datetime(2026, 4, 21, 10, 0, 0),
        updated_at=datetime(2026, 4, 21, 10, 0, 0),
    )
    defaults.update(kwargs)
    return Announcement(**defaults)


def _build_create_payload(**kwargs):
    defaults = dict(
        title="标题",
        content="内容",
        target_type="class",
        target_value=10,
        expire_at=datetime(2099, 1, 1),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------- create ----------

@pytest.mark.asyncio
async def test_teacher_create_class_announcement_own_class():
    teacher = _build_user(user_id=100, role=UserRole.teacher, college_id=1, class_id=10, staff_id="t100")
    db = _FakeDB([])
    payload = _build_create_payload(target_type="class", target_value=10)
    ann = await create_announcement(db, teacher, payload)
    assert ann.title == "标题"
    assert ann.target_type == "class"
    assert ann.target_value == 10
    assert ann.created_by == 100
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_teacher_create_class_announcement_other_class_403():
    teacher = _build_user(user_id=100, role=UserRole.teacher, college_id=1, class_id=10, staff_id="t100")
    db = _FakeDB([])
    payload = _build_create_payload(target_type="class", target_value=99)
    with pytest.raises(HTTPException) as exc_info:
        await create_announcement(db, teacher, payload)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_teacher_create_college_announcement_own_college():
    teacher = _build_user(user_id=100, role=UserRole.teacher, college_id=1, class_id=10, staff_id="t100")
    db = _FakeDB([])
    payload = _build_create_payload(target_type="college", target_value=1)
    ann = await create_announcement(db, teacher, payload)
    assert ann.target_type == "college"
    assert ann.target_value == 1


@pytest.mark.asyncio
async def test_teacher_create_all_announcement_403():
    teacher = _build_user(user_id=100, role=UserRole.teacher, college_id=1, class_id=10, staff_id="t100")
    db = _FakeDB([])
    payload = _build_create_payload(target_type="all", target_value=None)
    with pytest.raises(HTTPException) as exc_info:
        await create_announcement(db, teacher, payload)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_create_all_announcement_success():
    admin = _build_user(user_id=1, role=UserRole.admin, staff_id="admin")
    db = _FakeDB([])
    payload = _build_create_payload(target_type="all", target_value=None)
    ann = await create_announcement(db, admin, payload)
    assert ann.target_type == "all"
    assert ann.target_value is None


# ---------- list mine ----------

@pytest.mark.asyncio
async def test_list_mine_returns_only_own():
    teacher = _build_user(user_id=100, role=UserRole.teacher, staff_id="t100")
    ann1 = _build_announcement(id=1, created_by=100)
    ann2 = _build_announcement(id=2, created_by=100)
    db = _FakeDB([_FakeExecuteResult([ann1, ann2])])
    items = await list_my_announcements(db, teacher, limit=50)
    assert len(items) == 2
    db.execute.assert_awaited_once()


# ---------- update ----------

@pytest.mark.asyncio
async def test_update_by_creator_success():
    teacher = _build_user(user_id=100, role=UserRole.teacher, staff_id="t100")
    ann = _build_announcement(id=1, created_by=100)
    db = _FakeDB([_FakeExecuteResult(ann)])
    payload = SimpleNamespace(title="新标题", content=None, expire_at=None, is_active=None)
    result = await update_announcement(db, teacher, 1, payload)
    assert result.title == "新标题"
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_update_by_stranger_teacher_403():
    teacher = _build_user(user_id=101, role=UserRole.teacher, staff_id="t101")
    ann = _build_announcement(id=1, created_by=100)
    db = _FakeDB([_FakeExecuteResult(ann)])
    payload = SimpleNamespace(title="新标题", content=None, expire_at=None, is_active=None)
    with pytest.raises(HTTPException) as exc_info:
        await update_announcement(db, teacher, 1, payload)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_by_admin_success():
    admin = _build_user(user_id=1, role=UserRole.admin, staff_id="admin")
    ann = _build_announcement(id=1, created_by=100)
    db = _FakeDB([_FakeExecuteResult(ann)])
    payload = SimpleNamespace(title="管理员改", content=None, expire_at=None, is_active=None)
    result = await update_announcement(db, admin, 1, payload)
    assert result.title == "管理员改"


# ---------- delete ----------

@pytest.mark.asyncio
async def test_delete_soft_delete():
    teacher = _build_user(user_id=100, role=UserRole.teacher, staff_id="t100")
    ann = _build_announcement(id=1, created_by=100, is_active=True)
    db = _FakeDB([_FakeExecuteResult(ann)])
    await delete_announcement(db, teacher, 1)
    assert ann.is_active is False
    db.commit.assert_awaited()


# ---------- get_active for user ----------

@pytest.mark.asyncio
async def test_expired_announcement_not_returned():
    student = _build_user(user_id=200, role=UserRole.student, college_id=1, class_id=10, staff_id="s200")
    db = _FakeDB([_FakeExecuteResult([])])
    items = await get_active_announcements_for_user(db, student, limit=3)
    assert items == []


@pytest.mark.asyncio
async def test_unread_returned_then_mark_read():
    student = _build_user(user_id=200, role=UserRole.student, college_id=1, class_id=10, staff_id="s200")
    ann = _build_announcement(id=1, target_type="class", target_value=10)
    db = _FakeDB([_FakeExecuteResult([ann])])
    items = await get_active_announcements_for_user(db, student, limit=3)
    assert len(items) == 1
    assert items[0].id == 1


@pytest.mark.asyncio
async def test_other_college_not_returned():
    student = _build_user(user_id=200, role=UserRole.student, college_id=1, class_id=10, staff_id="s200")
    db = _FakeDB([_FakeExecuteResult([])])
    items = await get_active_announcements_for_user(db, student, limit=3)
    assert items == []


# ---------- mark read ----------

@pytest.mark.asyncio
async def test_mark_read_idempotent():
    db = _FakeDB([_FakeExecuteResult(None), _FakeExecuteResult(None)])
    # Calling twice should not raise
    await mark_announcement_read(db, user_id=200, announcement_id=1)
    await mark_announcement_read(db, user_id=200, announcement_id=1)
    assert db.execute.await_count == 2
    assert db.commit.await_count == 2

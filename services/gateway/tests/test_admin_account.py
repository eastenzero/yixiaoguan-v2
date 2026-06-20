from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from passlib.hash import bcrypt

from app.models.user import User, UserRole
from app.services.auth_service import authenticate_user
from app.services.admin_account import ensure_admin_user

TEST_ADMIN_PASSWORD = "LocalTestAdminPassword!2026"


class _FakeExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDB:
    def __init__(self, user=None):
        self.user = user
        self.added: list[User] = []
        self.add = MagicMock(side_effect=self._add)
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.refresh = AsyncMock()
        self.execute = AsyncMock(side_effect=self._execute)

    def _add(self, user):
        self.added.append(user)
        self.user = user

    async def _execute(self, statement):
        return _FakeExecuteResult(self.user)


@pytest.mark.asyncio
async def test_ensure_admin_user_creates_announced_admin_account():
    db = _FakeDB()

    result = await ensure_admin_user(
        db,
        staff_id="admin",
        password=TEST_ADMIN_PASSWORD,
        name="内测管理员",
    )

    assert result.created is True
    assert result.staff_id == "admin"
    assert result.role_updated is True
    assert result.password_updated is True
    assert result.activated is True
    assert len(db.added) == 1

    user = db.added[0]
    assert user.staff_id == "admin"
    assert user.name == "内测管理员"
    assert user.role == UserRole.admin
    assert user.is_active is True
    assert bcrypt.verify(TEST_ADMIN_PASSWORD, user.password_hash)
    assert not user.password_hash.endswith(TEST_ADMIN_PASSWORD)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ensure_admin_user_repairs_role_active_state_and_password():
    old_hash = bcrypt.using(rounds=12).hash("old-password")
    user = User(
        id=100,
        staff_id="admin",
        name="旧账号",
        role=UserRole.teacher,
        college_id=1,
        class_id=None,
        password_hash=old_hash,
        is_active=False,
    )
    db = _FakeDB(user)

    result = await ensure_admin_user(
        db,
        staff_id="admin",
        password=TEST_ADMIN_PASSWORD,
        name="内测管理员",
    )

    assert result.created is False
    assert result.role_updated is True
    assert result.activated is True
    assert result.password_updated is True
    assert result.name_updated is True
    assert user.role == UserRole.admin
    assert user.is_active is True
    assert user.name == "内测管理员"
    assert bcrypt.verify(TEST_ADMIN_PASSWORD, user.password_hash)
    assert user.password_hash != old_hash
    db.add.assert_not_called()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ensure_admin_user_rejects_reserved_pilot_staff_id():
    db = SimpleNamespace()

    with pytest.raises(ValueError, match="pilot"):
        await ensure_admin_user(
            db,
            staff_id="pilot:admin",
            password=TEST_ADMIN_PASSWORD,
        )


@pytest.mark.asyncio
async def test_ensured_admin_can_login_through_teacher_client_role_gate():
    user = User(
        id=101,
        staff_id="admin",
        name="内测管理员",
        role=UserRole.admin,
        college_id=None,
        class_id=None,
        password_hash=bcrypt.using(rounds=12).hash(TEST_ADMIN_PASSWORD),
        is_active=True,
    )
    db = _FakeDB(user)

    authenticated = await authenticate_user(
        db,
        staff_id="admin",
        password=TEST_ADMIN_PASSWORD,
        expected_role="teacher",
    )

    assert authenticated is user

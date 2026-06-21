from dataclasses import dataclass

from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


@dataclass(frozen=True)
class EnsureAdminResult:
    staff_id: str
    created: bool
    role_updated: bool
    activated: bool
    password_updated: bool
    name_updated: bool


async def ensure_admin_user(
    db: AsyncSession,
    *,
    staff_id: str,
    password: str,
    name: str = "管理员",
) -> EnsureAdminResult:
    normalized_staff_id = staff_id.strip()
    if not normalized_staff_id:
        raise ValueError("staff_id is required")
    if normalized_staff_id.lower().startswith("pilot:"):
        raise ValueError("staff_id cannot use reserved pilot prefix")
    if not password:
        raise ValueError("password is required")

    result = await db.execute(select(User).where(User.staff_id == normalized_staff_id))
    user = result.scalar_one_or_none()
    password_hash = bcrypt.using(rounds=12).hash(password)

    if user is None:
        user = User(
            staff_id=normalized_staff_id,
            name=name.strip() or normalized_staff_id,
            role=UserRole.admin,
            college_id=None,
            class_id=None,
            password_hash=password_hash,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        refresh = getattr(db, "refresh", None)
        if refresh is not None:
            await refresh(user)
        return EnsureAdminResult(
            staff_id=normalized_staff_id,
            created=True,
            role_updated=True,
            activated=True,
            password_updated=True,
            name_updated=True,
        )

    role_updated = user.role != UserRole.admin
    activated = not user.is_active
    new_name = name.strip()
    name_updated = bool(new_name) and user.name != new_name

    user.role = UserRole.admin
    user.is_active = True
    user.password_hash = password_hash
    if new_name:
        user.name = new_name

    await db.commit()
    return EnsureAdminResult(
        staff_id=normalized_staff_id,
        created=False,
        role_updated=role_updated,
        activated=activated,
        password_updated=True,
        name_updated=name_updated,
    )

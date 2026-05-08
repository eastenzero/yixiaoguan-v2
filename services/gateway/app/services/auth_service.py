from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.jwt import create_access_token


class RoleMismatchError(Exception):
    pass


async def authenticate_user(
    db: AsyncSession,
    staff_id: str,
    password: str,
    expected_role: str | None = None,
) -> User | None:
    if staff_id.lower().startswith("pilot:"):
        return None

    stmt = select(User).where(User.staff_id == staff_id, User.is_active)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not bcrypt.verify(password, user.password_hash):
        return None

    if expected_role is not None:
        allowed_roles = [expected_role]
        if expected_role == "teacher":
            allowed_roles.append("admin")
        if user.role.value not in allowed_roles:
            raise RoleMismatchError()

    return user


def build_jwt_payload(user: User) -> dict:
    return {
        "sub": str(user.id),
        "staff_id": user.staff_id,
        "role": user.role.value,
        "college_id": user.college_id,
        "class_id": user.class_id,
        "name": user.name,
    }


def issue_token(user: User) -> str:
    return create_access_token(build_jwt_payload(user))

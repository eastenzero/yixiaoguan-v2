from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.jwt import create_access_token


async def authenticate_user(db: AsyncSession, staff_id: str, password: str) -> User | None:
    """验证学号+密码，返回 User 或 None"""
    stmt = select(User).where(User.staff_id == staff_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not bcrypt.verify(password, user.password_hash):
        return None
    return user


def build_jwt_payload(user: User) -> dict:
    """构建 JWT payload（参考 dev-spec-v2.md 8.2 节）"""
    return {
        "sub": str(user.id),
        "staff_id": user.staff_id,
        "role": user.role.value,
        "college_id": user.college_id,
        "class_id": user.class_id,
        "name": user.name,
    }


def issue_token(user: User) -> str:
    """签发 JWT"""
    return create_access_token(build_jwt_payload(user))

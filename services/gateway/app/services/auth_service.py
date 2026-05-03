from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.jwt import create_access_token


class RoleMismatchError(Exception):
    """角色不匹配异常，由调用方捕获并返回 403"""
    pass


async def authenticate_user(db: AsyncSession, staff_id: str, password: str, expected_role: str | None = None) -> User | None:
    """验证学号+密码+角色，返回 User 或 None；角色不匹配时抛出 RoleMismatchError"""
    stmt = select(User).where(User.staff_id == staff_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not bcrypt.verify(password, user.password_hash):
        return None
    # 角色隔离校验
    if expected_role is not None:
        allowed_roles = [expected_role]
        # 教师端允许管理员也登录
        if expected_role == 'teacher':
            allowed_roles.append('admin')
        if user.role.value not in allowed_roles:
            raise RoleMismatchError()
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

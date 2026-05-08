import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from passlib.hash import bcrypt
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Class, College, User, UserRole
from app.schemas.admin import (
    AdminUserItem,
    AdminUserListResponse,
    BatchImportRequest,
    BatchImportResponse,
    ResetPasswordResponse,
    ToggleActiveResponse,
)
from app.utils.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_admin(current_user: User) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return current_user


# ================================================================
# 1. GET /users — 用户列表（分页 + 筛选）
# ================================================================
@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    college_id: Optional[int] = None,
    class_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)

    stmt = select(User)
    count_stmt = select(func.count(User.id))

    # Filters
    if role:
        stmt = stmt.where(User.role == UserRole(role))
        count_stmt = count_stmt.where(User.role == UserRole(role))
    if college_id:
        stmt = stmt.where(User.college_id == college_id)
        count_stmt = count_stmt.where(User.college_id == college_id)
    if class_id:
        stmt = stmt.where(User.class_id == class_id)
        count_stmt = count_stmt.where(User.class_id == class_id)
    if keyword:
        kw = f"%{keyword}%"
        kw_filter = or_(User.staff_id.ilike(kw), User.name.ilike(kw))
        stmt = stmt.where(kw_filter)
        count_stmt = count_stmt.where(kw_filter)

    # Total count
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated results
    stmt = stmt.order_by(User.id).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    users = result.scalars().all()

    # Build response with college/class names
    items = []
    for u in users:
        items.append(AdminUserItem(
            id=u.id,
            staff_id=u.staff_id,
            name=u.name,
            role=u.role.value,
            college_id=u.college_id,
            college_name=u.college.name if u.college else None,
            class_id=u.class_id,
            class_name=u.class_.name if u.class_ else None,
            is_active=u.is_active,
            created_at=u.created_at,
        ))

    return AdminUserListResponse(items=items, total=total, page=page, size=size)


# ================================================================
# 2. POST /users/batch-import — 批量导入
# ================================================================
@router.post("/users/batch-import", response_model=BatchImportResponse)
async def batch_import(
    body: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)

    for user_in in body.users:
        if (user_in.staff_id or "").lower().startswith("pilot:"):
            raise HTTPException(400, "staff_id 不能以 'pilot:' 开头（保留前缀）")

    # Validate role
    try:
        role_enum = UserRole(body.role)
    except ValueError:
        raise HTTPException(400, f"无效角色: {body.role}")

    # Validate college exists
    college = (await db.execute(
        select(College).where(College.id == body.college_id)
    )).scalar_one_or_none()
    if not college:
        raise HTTPException(404, "学院不存在")

    # Validate class if provided
    if body.class_id:
        cls = (await db.execute(
            select(Class).where(Class.id == body.class_id)
        )).scalar_one_or_none()
        if not cls:
            raise HTTPException(404, "班级不存在")

    created = 0
    skipped = 0

    for u in body.users:
        # Check if already exists
        existing = (await db.execute(
            select(User.id).where(User.staff_id == u.staff_id)
        )).scalar_one_or_none()

        if existing:
            skipped += 1
            continue

        password_hash = bcrypt.using(rounds=12).hash(u.staff_id)
        db.add(User(
            staff_id=u.staff_id,
            name=u.name,
            role=role_enum,
            college_id=body.college_id,
            class_id=body.class_id,
            password_hash=password_hash,
            is_active=True,
        ))
        created += 1

    await db.commit()
    logger.info(
        "Batch import by admin=%s: created=%d skipped=%d",
        current_user.staff_id, created, skipped,
    )
    return BatchImportResponse(created=created, skipped=skipped)


# ================================================================
# 3. POST /users/{user_id}/reset-password — 重置密码
# ================================================================
@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)

    user = (await db.execute(
        select(User).where(User.id == user_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")

    user.password_hash = bcrypt.using(rounds=12).hash(user.staff_id)
    await db.commit()
    logger.info("Password reset by admin=%s for user=%s", current_user.staff_id, user.staff_id)
    return ResetPasswordResponse()


# ================================================================
# 4. PATCH /users/{user_id}/toggle-active — 启用/禁用
# ================================================================
@router.post("/users/{user_id}/toggle-active", response_model=ToggleActiveResponse)
async def toggle_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)

    user = (await db.execute(
        select(User).where(User.id == user_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")

    if user.id == current_user.id:
        raise HTTPException(400, "不能禁用自己")

    user.is_active = not user.is_active
    await db.commit()
    logger.info(
        "Toggle active by admin=%s: user=%s is_active=%s",
        current_user.staff_id, user.staff_id, user.is_active,
    )
    return ToggleActiveResponse(id=user.id, is_active=user.is_active)

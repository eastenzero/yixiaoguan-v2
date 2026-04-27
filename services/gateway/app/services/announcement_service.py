from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement, AnnouncementRead
from app.models.user import User, UserRole


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


async def create_announcement(
    db: AsyncSession,
    user: User,
    payload,
) -> Announcement:
    if user.role not in {UserRole.teacher, UserRole.admin}:
        raise HTTPException(status_code=403, detail="仅教师或管理员可发布通知")

    target_type = payload.target_type
    target_value = payload.target_value
    expire_at = _to_naive_utc(payload.expire_at)

    if expire_at <= _utcnow_naive():
        raise HTTPException(status_code=400, detail="过期时间必须在未来")

    if target_type == "all":
        if target_value is not None:
            raise HTTPException(status_code=400, detail="全局通知不需要目标值")
        if user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="仅管理员可发布全局通知")
    elif target_type == "college":
        if target_value is None:
            raise HTTPException(status_code=400, detail="学院通知需要学院ID")
        if user.role == UserRole.teacher and target_value != user.college_id:
            raise HTTPException(status_code=403, detail="不能发布到其他学院")
    elif target_type == "class":
        if target_value is None:
            raise HTTPException(status_code=400, detail="班级通知需要班级ID")
        if user.role == UserRole.teacher and target_value != user.class_id:
            raise HTTPException(status_code=403, detail="不能发布到其他班级")
    else:
        raise HTTPException(status_code=400, detail="无效的目标类型")

    ann = Announcement(
        title=payload.title,
        content=payload.content,
        target_type=target_type,
        target_value=target_value,
        created_by=user.id,
        expire_at=expire_at,
        is_active=True,
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann


async def list_my_announcements(
    db: AsyncSession,
    user: User,
    *,
    limit: int = 50,
) -> list[Announcement]:
    stmt = (
        select(Announcement)
        .where(Announcement.created_by == user.id)
        .order_by(Announcement.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_announcement(
    db: AsyncSession,
    user: User,
    ann_id: int,
    payload,
) -> Announcement:
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="通知不存在")

    if user.role != UserRole.admin and ann.created_by != user.id:
        raise HTTPException(status_code=403, detail="无权修改该通知")

    if payload.title is not None:
        ann.title = payload.title
    if payload.content is not None:
        ann.content = payload.content
    if payload.expire_at is not None:
        ann.expire_at = _to_naive_utc(payload.expire_at)
    if payload.is_active is not None:
        ann.is_active = payload.is_active

    await db.commit()
    await db.refresh(ann)
    return ann


async def delete_announcement(
    db: AsyncSession,
    user: User,
    ann_id: int,
) -> None:
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="通知不存在")

    if user.role != UserRole.admin and ann.created_by != user.id:
        raise HTTPException(status_code=403, detail="无权删除该通知")

    ann.is_active = False
    await db.commit()


async def get_active_announcements_for_user(
    db: AsyncSession,
    user: User,
    *,
    limit: int = 3,
) -> list[Announcement]:
    if user.role != UserRole.student:
        return []

    now = _utcnow_naive()
    target_filter = or_(
        Announcement.target_type == "all",
        and_(Announcement.target_type == "college", Announcement.target_value == user.college_id),
        and_(Announcement.target_type == "class", Announcement.target_value == user.class_id),
    )
    stmt = (
        select(Announcement)
        .outerjoin(
            AnnouncementRead,
            and_(
                AnnouncementRead.announcement_id == Announcement.id,
                AnnouncementRead.user_id == user.id,
            ),
        )
        .where(
            Announcement.is_active.is_(True),
            Announcement.expire_at > now,
            target_filter,
            AnnouncementRead.user_id.is_(None),
        )
        .order_by(Announcement.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_announcement_read(
    db: AsyncSession,
    *,
    user_id: int,
    announcement_id: int,
) -> None:
    stmt = (
        insert(AnnouncementRead)
        .values(user_id=user_id, announcement_id=announcement_id)
        .on_conflict_do_nothing()
    )
    await db.execute(stmt)
    await db.commit()


def serialize_announcement(ann: Announcement) -> dict:
    return {
        "id": ann.id,
        "title": ann.title,
        "content": ann.content,
        "target_type": ann.target_type,
        "target_value": ann.target_value,
        "created_by": ann.created_by,
        "expire_at": ann.expire_at,
        "is_active": ann.is_active,
        "created_at": ann.created_at,
        "updated_at": ann.updated_at,
    }

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse,
)
from app.services.announcement_service import (
    create_announcement,
    list_my_announcements,
    update_announcement,
    delete_announcement,
)
from app.utils.deps import get_current_user

router = APIRouter()


@router.post("", response_model=AnnouncementResponse, status_code=201)
async def create(
    payload: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {UserRole.teacher, UserRole.admin}:
        raise HTTPException(403, "仅教师或管理员可发布通知")
    ann = await create_announcement(db, current_user, payload)
    return AnnouncementResponse.model_validate(ann)


@router.get("/mine", response_model=AnnouncementListResponse)
async def list_mine(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await list_my_announcements(db, current_user, limit=limit)
    return AnnouncementListResponse(
        items=[AnnouncementResponse.model_validate(a) for a in items],
        total=len(items),
    )


@router.patch("/{id}", response_model=AnnouncementResponse)
async def update(
    id: int,
    payload: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ann = await update_announcement(db, current_user, id, payload)
    return AnnouncementResponse.model_validate(ann)


@router.delete("/{id}", status_code=204)
async def delete(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_announcement(db, current_user, id)
    return None

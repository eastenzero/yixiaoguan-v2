from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    target_type: Literal["all", "college", "class"]
    target_value: Optional[int] = None
    expire_at: datetime


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = None
    expire_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    target_type: str
    target_value: Optional[int]
    created_by: int
    expire_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    items: list[AnnouncementResponse]
    total: int

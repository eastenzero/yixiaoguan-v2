from datetime import datetime

from pydantic import BaseModel


# ---------- Users list ----------

class AdminUserItem(BaseModel):
    id: int
    staff_id: str
    name: str
    role: str
    college_id: int | None
    college_name: str | None = None
    class_id: int | None
    class_name: str | None = None
    is_active: bool
    created_at: datetime


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    total: int
    page: int
    size: int


# ---------- Batch import ----------

class BatchImportUser(BaseModel):
    staff_id: str
    name: str


class BatchImportRequest(BaseModel):
    college_id: int
    class_id: int | None = None
    role: str = "student"
    users: list[BatchImportUser]


class BatchImportResponse(BaseModel):
    created: int
    skipped: int


# ---------- Reset password ----------

class ResetPasswordResponse(BaseModel):
    ok: bool = True


# ---------- Toggle active ----------

class ToggleActiveResponse(BaseModel):
    id: int
    is_active: bool

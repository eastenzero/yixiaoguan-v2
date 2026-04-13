from pydantic import BaseModel


class LoginRequest(BaseModel):
    staff_id: str          # 学号或工号
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """GET /api/auth/me 返回体"""
    id: int
    staff_id: str
    name: str
    role: str              # "student" | "teacher" | "admin"
    college_id: int | None
    class_id: int | None
    avatar_url: str | None

from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    staff_id: str
    password: str
    expected_role: Optional[str] = None


class PilotAnonymousRequest(BaseModel):
    device_id: str


class TokenResponse(BaseModel):
    access_token: str
    centrifugo_token: str = ""
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    staff_id: str
    name: str
    role: str
    college_id: int | None
    class_id: int | None
    avatar_url: str | None

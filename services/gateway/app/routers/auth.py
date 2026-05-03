from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo
from app.services.auth_service import authenticate_user, issue_token, RoleMismatchError
from app.services.centrifugo_client import build_centrifugo_token
from app.utils.deps import get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await authenticate_user(db, body.staff_id, body.password, body.expected_role)
    except RoleMismatchError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该账号不属于此客户端，请使用正确的客户端登录",
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="学号或密码错误",
        )
    token = issue_token(user)
    ct = build_centrifugo_token(user) if settings.centrifugo_secret else ""
    return TokenResponse(access_token=token, centrifugo_token=ct)


@router.get("/centrifugo-token")
async def get_centrifugo_token(current_user: User = Depends(get_current_user)):
    """返回新的 Centrifugo 连接 JWT（用于前端 init 重连和 SDK getToken 回调）"""
    if not settings.centrifugo_secret:
        raise HTTPException(status_code=503, detail="Centrifugo not configured")
    return {"token": build_centrifugo_token(current_user)}


@router.get("/me", response_model=UserInfo)
async def me(current_user: User = Depends(get_current_user)):
    return UserInfo(
        id=current_user.id,
        staff_id=current_user.staff_id,
        name=current_user.name,
        role=current_user.role.value,
        college_id=current_user.college_id,
        class_id=current_user.class_id,
        avatar_url=current_user.avatar_url,
    )

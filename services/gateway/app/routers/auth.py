from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo
from app.services.auth_service import authenticate_user, issue_token
from app.utils.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.staff_id, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="学号或密码错误",
        )
    token = issue_token(user)
    return TokenResponse(access_token=token)


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

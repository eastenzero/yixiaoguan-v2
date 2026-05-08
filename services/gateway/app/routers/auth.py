import re

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, PilotAnonymousRequest, TokenResponse, UserInfo
from app.services.auth_service import RoleMismatchError, authenticate_user, issue_token
from app.services.centrifugo_client import build_centrifugo_token
from app.utils.deps import get_current_user

router = APIRouter()

PILOT_DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")
PILOT_PLACEHOLDER_HASH = bcrypt.hashpw(
    b"!!pilot-no-password-allowed!!",
    bcrypt.gensalt(),
).decode("utf-8")


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


@router.post("/pilot-anonymous", response_model=TokenResponse)
async def pilot_anonymous(
    body: PilotAnonymousRequest,
    db: AsyncSession = Depends(get_db),
):
    if not settings.pilot_mode_enabled:
        raise HTTPException(status_code=403, detail="pilot mode is disabled")

    if not PILOT_DEVICE_ID_PATTERN.fullmatch(body.device_id):
        raise HTTPException(status_code=400, detail="invalid device_id")

    staff_id = f"pilot:{body.device_id[:16]}"
    result = await db.execute(select(User).where(User.staff_id == staff_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            staff_id=staff_id,
            name=f"pilot-{body.device_id[:8]}",
            role=UserRole.student,
            college_id=None,
            class_id=None,
            password_hash=PILOT_PLACEHOLDER_HASH,
            is_active=True,
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(User).where(User.staff_id == staff_id))
            user = result.scalar_one_or_none()
            if user is None:
                raise
        else:
            await db.refresh(user)

    token = issue_token(user)
    ct = build_centrifugo_token(user) if settings.centrifugo_secret else ""
    return TokenResponse(access_token=token, centrifugo_token=ct)


@router.get("/centrifugo-token")
async def get_centrifugo_token(current_user: User = Depends(get_current_user)):
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

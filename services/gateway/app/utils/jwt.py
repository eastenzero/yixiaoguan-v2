from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings


def create_access_token(data: dict) -> str:
    """签发 JWT"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """解码 JWT，失败抛 JWTError"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

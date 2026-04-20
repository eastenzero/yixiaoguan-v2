import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Enum, String, Boolean, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base


class UserRole(enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class PlatformType(enum.Enum):
    wechat_mp = "wechat_mp"
    wechat_work = "wechat_work"
    h5 = "h5"
    app = "app"


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    classes: Mapped[List["Class"]] = relationship(back_populates="college")


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False)
    grade_year: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    college: Mapped["College"] = relationship(back_populates="classes")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="userrole"), nullable=False)
    college_id: Mapped[Optional[int]] = mapped_column(ForeignKey("colleges.id"), nullable=True)
    class_id: Mapped[Optional[int]] = mapped_column(ForeignKey("classes.id"), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    bindings: Mapped[List["UserBinding"]] = relationship(back_populates="user")
    college: Mapped[Optional["College"]] = relationship(lazy="selectin")
    class_: Mapped[Optional["Class"]] = relationship(
        foreign_keys=[class_id], lazy="selectin"
    )


class UserBinding(Base):
    __tablename__ = "user_bindings"
    __table_args__ = (
        UniqueConstraint("platform", "platform_uid", name="uq_user_binding_platform_uid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    platform: Mapped[PlatformType] = mapped_column(Enum(PlatformType, name="platformtype"), nullable=False)
    platform_uid: Mapped[str] = mapped_column(String(128), nullable=False)
    bound_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="bindings")

import enum
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# BigInteger for MySQL, Integer for SQLite to support autoincrement/rowid
PKType = BigInteger().with_variant(Integer, "sqlite")


class RoleEnum(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class AuthTypeEnum(str, enum.Enum):
    google = "google"
    local = "local"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    school_person_id: Mapped[str | None] = mapped_column(CHAR(6), unique=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name_kana: Mapped[str | None] = mapped_column(String(100))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    grade: Mapped[int | None] = mapped_column(Integer)
    class_name: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum), default=GenderEnum.unknown, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_reason: Mapped[str | None] = mapped_column(String(255))
    # 2FA関連
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    google_account: Mapped["UserGoogleAccount"] = relationship(
        back_populates="user", uselist=False
    )
    local_account: Mapped["UserLocalAccount"] = relationship(
        back_populates="user", uselist=False
    )
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
    login_logs: Mapped[list["LoginLog"]] = relationship(back_populates="user")


class UserGoogleAccount(Base):
    __tablename__ = "user_google_accounts"

    user_id: Mapped[int] = mapped_column(
        PKType, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    google_email: Mapped[str | None] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[User] = relationship(back_populates="google_account")


class UserLocalAccount(Base):
    __tablename__ = "user_local_accounts"

    user_id: Mapped[int] = mapped_column(
        PKType, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    login_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[User] = relationship(back_populates="local_account")


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint("session_token", name="uq_sessions_session_token"),
        UniqueConstraint("refresh_token_hash", name="uq_sessions_refresh_hash"),
    )

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        PKType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_token: Mapped[str] = mapped_column(String(64), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    auth_type: Mapped[AuthTypeEnum] = mapped_column(Enum(AuthTypeEnum), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    device_info: Mapped[str | None] = mapped_column(String(255))
    client_name: Mapped[str | None] = mapped_column(String(100))
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped[User] = relationship(back_populates="sessions")


class LoginLog(Base):
    __tablename__ = "login_logs"

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        PKType, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    login_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    auth_type: Mapped[AuthTypeEnum] = mapped_column(Enum(AuthTypeEnum), nullable=False)
    success: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    device_info: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    user: Mapped[User | None] = relationship(back_populates="login_logs")


class TempToken(Base):
    """2FA検証前の一時トークン管理用テーブル"""
    __tablename__ = "temp_tokens"
    __table_args__ = (
        UniqueConstraint("token", name="uq_temp_tokens_token"),
    )

    id: Mapped[int] = mapped_column(PKType, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

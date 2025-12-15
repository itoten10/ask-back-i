import logging
from datetime import timedelta

import httpx
import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_token,
    hash_refresh_token,
    now_utc,
    verify_password,
)
from app.models.user import AuthTypeEnum, RoleEnum, User
from app.repositories import login_log_repository, session_repository, user_repository
from app.schemas.auth import AuthSuccessResponse, TokenResponse


logger = logging.getLogger(__name__)


class AuthResult(AuthSuccessResponse):
    refresh_token: str


async def _issue_tokens(
    *,
    user: User,
    auth_type: AuthTypeEnum,
    db: AsyncSession,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResult:
    issued_at = now_utc()
    refresh_token = generate_token(32)
    refresh_hash = hash_refresh_token(refresh_token)
    session_token = generate_token(16)
    refresh_expires_at = issued_at + timedelta(days=settings.refresh_token_ttl_days)

    access_payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "session_token": session_token,
        "auth_type": auth_type.value,
    }
    access_token = create_access_token(
        access_payload,
        secret=settings.jwt_secret,
        expires_minutes=settings.access_token_ttl_min,
    )

    session = await session_repository.create_session(
        db,
        user_id=user.id,
        session_token=session_token,
        refresh_hash=refresh_hash,
        auth_type=auth_type,
        issued_at=issued_at,
        expires_at=refresh_expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return AuthResult(
        token=TokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_ttl_min * 60,
        ),
        user_id=user.id,
        role=user.role.value,
        full_name=user.full_name,
        email=user.email,
        session_token=session.session_token,
        issued_at=issued_at,
        refresh_token=refresh_token,
    )


async def login_with_local(
    *,
    db: AsyncSession,
    login_id: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResult:
    login_at = now_utc()
    login_id = login_id.strip()
    password = password.strip()
    if not login_id or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="login_id and password are required",
        )

    user, local_account = await user_repository.get_user_with_local_account(
        db, login_id
    )
    if not user or not local_account:
        await login_log_repository.create_login_log(
            db,
            user_id=None,
            auth_type=AuthTypeEnum.local,
            success=False,
            failure_reason="USER_NOT_FOUND",
            ip_address=ip_address,
            user_agent=user_agent,
            login_at=login_at,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.is_deleted or not user.is_active:
        await login_log_repository.create_login_log(
            db,
            user_id=user.id,
            auth_type=AuthTypeEnum.local,
            success=False,
            failure_reason="INACTIVE_OR_DELETED",
            ip_address=ip_address,
            user_agent=user_agent,
            login_at=login_at,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(password, local_account.password_hash):
        await login_log_repository.create_login_log(
            db,
            user_id=user.id,
            auth_type=AuthTypeEnum.local,
            success=False,
            failure_reason="INVALID_PASSWORD",
            ip_address=ip_address,
            user_agent=user_agent,
            login_at=login_at,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    result = await _issue_tokens(
        user=user,
        auth_type=AuthTypeEnum.local,
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await user_repository.touch_local_login(db, local_account)
    await login_log_repository.create_login_log(
        db,
        user_id=user.id,
        auth_type=AuthTypeEnum.local,
        success=True,
        failure_reason=None,
        ip_address=ip_address,
        user_agent=user_agent,
        login_at=login_at,
    )
    await db.commit()
    return result


async def exchange_google_code(code: str) -> tuple[str, str]:
    token_url = "https://oauth2.googleapis.com/token"
    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.warning("Google token endpoint failed: %s", token_resp.text)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed",
            )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        id_token = token_data.get("id_token")
        if not access_token or not id_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed",
            )
        return access_token, id_token


async def fetch_google_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            logger.warning("Google userinfo failed: %s", resp.text)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed",
            )
        return resp.json()


async def login_with_google(
    *,
    db: AsyncSession,
    code: str,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResult:
    login_at = now_utc()
    access_token, _ = await exchange_google_code(code)
    user_info = await fetch_google_userinfo(access_token)
    google_sub = user_info.get("sub")
    google_email = user_info.get("email")

    if not google_sub or not google_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",
        )

    if not google_email.lower().endswith("@gmail.com"):
        await login_log_repository.create_login_log(
            db,
            user_id=None,
            auth_type=AuthTypeEnum.google,
            success=False,
            failure_reason="NON_GMAIL_DOMAIN",
            ip_address=ip_address,
            user_agent=user_agent,
            login_at=login_at,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid email domain")

    user, google_account = await user_repository.get_user_by_google_sub(db, google_sub)
    if not user:
        user = await user_repository.get_user_by_email(db, google_email)
        if user:
            await user_repository.upsert_google_account(db, user, google_sub, google_email)
        else:
            await login_log_repository.create_login_log(
                db,
                user_id=None,
                auth_type=AuthTypeEnum.google,
                success=False,
                failure_reason="USER_NOT_FOUND",
                ip_address=ip_address,
                user_agent=user_agent,
                login_at=login_at,
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not registered"
            )

    if user.is_deleted or not user.is_active:
        await login_log_repository.create_login_log(
            db,
            user_id=user.id,
            auth_type=AuthTypeEnum.google,
            success=False,
            failure_reason="INACTIVE_OR_DELETED",
            ip_address=ip_address,
            user_agent=user_agent,
            login_at=login_at,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    result = await _issue_tokens(
        user=user,
        auth_type=AuthTypeEnum.google,
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await login_log_repository.create_login_log(
        db,
        user_id=user.id,
        auth_type=AuthTypeEnum.google,
        success=True,
        failure_reason=None,
        ip_address=ip_address,
        user_agent=user_agent,
        login_at=login_at,
    )
    await db.commit()
    return result


async def refresh_tokens(
    *,
    db: AsyncSession,
    refresh_token: str,
    ip_address: str | None,
    user_agent: str | None,
) -> AuthResult:
    refresh_hash = hash_refresh_token(refresh_token)
    session = await session_repository.get_session_by_refresh_hash(db, refresh_hash)
    if not session or session.revoked_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if session.expires_at < now_utc():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    stmt_user = await db.get(User, session.user_id)
    if not stmt_user or stmt_user.is_deleted or not stmt_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    result = await _issue_tokens(
        user=stmt_user,
        auth_type=session.auth_type,
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await session_repository.revoke_session(db, session, revoked_at=now_utc())
    await db.commit()
    return result


async def logout(
    *,
    db: AsyncSession,
    refresh_token: str | None,
) -> None:
    if not refresh_token:
        return
    refresh_hash = hash_refresh_token(refresh_token)
    session = await session_repository.get_session_by_refresh_hash(db, refresh_hash)
    if not session:
        return
    await session_repository.revoke_session(db, session, revoked_at=now_utc())
    await db.commit()


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
        ) from exc

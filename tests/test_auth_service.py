import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import pytest
from datetime import timedelta

from fastapi import HTTPException

from app.core.security import hash_password, hash_refresh_token, now_utc
from app.models.user import AuthTypeEnum, RoleEnum, User, UserLocalAccount
from app.repositories import session_repository
from app.services import auth_service


@pytest.mark.asyncio
async def test_login_and_refresh_tokens(session: AsyncSession):
    user = User(
        id=1,
        role=RoleEnum.admin,
        full_name="Admin User",
        full_name_kana="アドミンユーザー",
        email="admin@example.com",
    )
    session.add(user)
    await session.flush()

    local = UserLocalAccount(
        user_id=user.id,
        login_id="admin01",
        password_hash=hash_password("pass123"),
    )
    session.add(local)
    await session.commit()

    login_result = await auth_service.login_with_local(
        db=session,
        login_id="admin01",
        password="pass123",
        ip_address=None,
        user_agent=None,
    )

    assert login_result.user_id == user.id
    assert login_result.token.access_token
    assert login_result.refresh_token

    refreshed = await auth_service.refresh_tokens(
        db=session,
        refresh_token=login_result.refresh_token,
        ip_address=None,
        user_agent=None,
    )

    assert refreshed.token.access_token
    # session token should rotate
    assert refreshed.token.access_token != login_result.token.access_token


@pytest.mark.asyncio
async def test_student_local_login_forbidden(session: AsyncSession):
    user = User(
        id=2,
        role=RoleEnum.student,
        full_name="Student User",
        full_name_kana="スチューデント",
        email="student@example.com",
    )
    session.add(user)
    await session.flush()
    session.add(
        UserLocalAccount(
            user_id=user.id,
            login_id="student01",
            password_hash=hash_password("pass123"),
        )
    )
    await session.commit()

    with pytest.raises(HTTPException) as exc:
        await auth_service.login_with_local(
            db=session,
            login_id="student01",
            password="pass123",
            ip_address=None,
            user_agent=None,
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token_expired(session: AsyncSession):
    user = User(
        id=3,
        role=RoleEnum.admin,
        full_name="Admin User",
        full_name_kana="アドミン",
        email="expired@example.com",
    )
    session.add(user)
    await session.flush()

    # create an expired session manually
    refresh_token = "expired-refresh"
    refresh_hash = hash_refresh_token(refresh_token)
    await session_repository.create_session(
        session,
        user_id=user.id,
        session_token="session-expired",
        refresh_hash=refresh_hash,
        auth_type=AuthTypeEnum.local,
        issued_at=now_utc() - timedelta(days=15),
        expires_at=now_utc() - timedelta(days=1),
        ip_address=None,
        user_agent=None,
    )
    await session.commit()

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh_tokens(
            db=session,
            refresh_token=refresh_token,
            ip_address=None,
            user_agent=None,
        )
    assert exc.value.status_code == 401

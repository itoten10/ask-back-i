import pytest
from datetime import timedelta

from app.core.security import now_utc
from app.models.user import AuthTypeEnum, RoleEnum, User
from app.repositories import login_log_repository, session_repository
from app.core.security import hash_refresh_token


@pytest.mark.asyncio
async def test_session_repository_crud(session):
    user = User(
        id=30,
        role=RoleEnum.admin,
        full_name="Repo Admin",
        full_name_kana="レポアドミン",
        email="repo-admin@example.com",
    )
    session.add(user)
    await session.flush()

    refresh_token = "repo-refresh"
    refresh_hash = hash_refresh_token(refresh_token)
    issued = now_utc()
    expires = issued + timedelta(days=1)

    created = await session_repository.create_session(
        session,
        user_id=user.id,
        session_token="sess-token",
        refresh_hash=refresh_hash,
        auth_type=AuthTypeEnum.local,
        issued_at=issued,
        expires_at=expires,
        ip_address="127.0.0.1",
        user_agent="test-agent",
    )
    await session.commit()

    by_token = await session_repository.get_session_by_token(session, "sess-token")
    assert by_token is not None
    assert by_token.id == created.id

    by_refresh = await session_repository.get_session_by_refresh_hash(session, refresh_hash)
    assert by_refresh is not None

    await session_repository.revoke_session(session, created, now_utc())
    await session.commit()
    revoked = await session_repository.get_session_by_token(session, "sess-token")
    assert revoked.revoked_at is not None


@pytest.mark.asyncio
async def test_login_log_repository(session):
    user = User(
        id=31,
        role=RoleEnum.teacher,
        full_name="Log User",
        full_name_kana="ログユーザー",
        email="log@example.com",
    )
    session.add(user)
    await session.flush()

    log = await login_log_repository.create_login_log(
        session,
        user_id=user.id,
        auth_type=AuthTypeEnum.google,
        success=True,
        failure_reason=None,
        ip_address="127.0.0.1",
        user_agent="agent",
        login_at=now_utc(),
    )
    await session.commit()
    assert log.id is not None

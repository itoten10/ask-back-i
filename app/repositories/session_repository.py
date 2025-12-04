from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuthTypeEnum, UserSession


async def create_session(
    db: AsyncSession,
    *,
    user_id: int,
    session_token: str,
    refresh_hash: str,
    auth_type: AuthTypeEnum,
    issued_at: datetime,
    expires_at: datetime,
    ip_address: str | None,
    user_agent: str | None,
) -> UserSession:
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        refresh_token_hash=refresh_hash,
        auth_type=auth_type,
        ip_address=ip_address,
        user_agent=user_agent,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_by_refresh_hash(
    db: AsyncSession, refresh_hash: str
) -> UserSession | None:
    stmt = select(UserSession).where(UserSession.refresh_token_hash == refresh_hash)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_session_by_token(
    db: AsyncSession, session_token: str
) -> UserSession | None:
    stmt = select(UserSession).where(UserSession.session_token == session_token)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_session(db: AsyncSession, session: UserSession, revoked_at: datetime):
    stmt = (
        update(UserSession)
        .where(UserSession.id == session.id)
        .values(revoked_at=revoked_at)
    )
    await db.execute(stmt)

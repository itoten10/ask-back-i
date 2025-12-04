import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import now_utc
from app.models.user import TempToken


async def create_temp_token(
    db: AsyncSession, email: str, expiration_minutes: int | None = None
) -> TempToken:
    """一時トークン作成"""
    if expiration_minutes is None:
        expiration_minutes = settings.temp_token_expiration_minutes
    
    token = str(uuid.uuid4())
    expires_at = now_utc() + timedelta(minutes=expiration_minutes)
    
    temp_token = TempToken(
        token=token,
        email=email,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(temp_token)
    await db.flush()
    return temp_token


async def get_temp_token(
    db: AsyncSession, token: str
) -> TempToken | None:
    """一時トークン取得・検証"""
    stmt = (
        select(TempToken)
        .where(TempToken.token == token)
        .where(TempToken.is_used == False)
        .where(TempToken.expires_at > now_utc())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def invalidate_temp_token(
    db: AsyncSession, temp_token: TempToken
) -> None:
    """一時トークン無効化"""
    stmt = (
        update(TempToken)
        .where(TempToken.id == temp_token.id)
        .values(is_used=True)
    )
    await db.execute(stmt)



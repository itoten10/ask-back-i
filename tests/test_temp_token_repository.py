import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import now_utc
from app.models.user import TempToken
from app.repositories import temp_token_repository


@pytest.mark.asyncio
async def test_create_temp_token(session: AsyncSession):
    """一時トークン作成のテスト"""
    email = "test@example.com"
    
    temp_token = await temp_token_repository.create_temp_token(session, email)
    await session.commit()
    
    assert temp_token is not None
    assert temp_token.email == email
    assert temp_token.token is not None
    assert len(temp_token.token) > 0
    assert temp_token.is_used is False
    assert temp_token.expires_at > now_utc()


@pytest.mark.asyncio
async def test_get_temp_token(session: AsyncSession):
    """一時トークン取得のテスト"""
    email = "test@example.com"
    
    # トークン作成
    created_token = await temp_token_repository.create_temp_token(session, email)
    await session.commit()
    
    # トークン取得
    retrieved_token = await temp_token_repository.get_temp_token(session, created_token.token)
    
    assert retrieved_token is not None
    assert retrieved_token.token == created_token.token
    assert retrieved_token.email == email
    assert retrieved_token.is_used is False


@pytest.mark.asyncio
async def test_get_temp_token_expired(session: AsyncSession):
    """有効期限切れトークンの取得テスト"""
    email = "test@example.com"
    
    # トークン作成
    created_token = await temp_token_repository.create_temp_token(session, email)
    await session.commit()
    
    # 有効期限を過去に設定
    from sqlalchemy import update
    stmt = (
        update(TempToken)
        .where(TempToken.id == created_token.id)
        .values(expires_at=now_utc() - timedelta(minutes=1))
    )
    await session.execute(stmt)
    await session.commit()
    
    # 有効期限切れのトークンは取得できないこと
    retrieved_token = await temp_token_repository.get_temp_token(session, created_token.token)
    assert retrieved_token is None


@pytest.mark.asyncio
async def test_get_temp_token_used(session: AsyncSession):
    """使用済みトークンの取得テスト"""
    email = "test@example.com"
    
    # トークン作成
    created_token = await temp_token_repository.create_temp_token(session, email)
    await session.commit()
    
    # トークンを無効化
    await temp_token_repository.invalidate_temp_token(session, created_token)
    await session.commit()
    
    # 使用済みのトークンは取得できないこと
    retrieved_token = await temp_token_repository.get_temp_token(session, created_token.token)
    assert retrieved_token is None


@pytest.mark.asyncio
async def test_invalidate_temp_token(session: AsyncSession):
    """一時トークン無効化のテスト"""
    email = "test@example.com"
    
    # トークン作成
    temp_token = await temp_token_repository.create_temp_token(session, email)
    await session.commit()
    
    assert temp_token.is_used is False
    
    # トークン無効化
    await temp_token_repository.invalidate_temp_token(session, temp_token)
    await session.commit()
    
    # データベースから再取得して確認
    await session.refresh(temp_token)
    assert temp_token.is_used is True


@pytest.mark.asyncio
async def test_temp_token_expiration_minutes(session: AsyncSession):
    """一時トークンの有効期限設定のテスト"""
    email = "test@example.com"
    custom_expiration = 5  # 5分
    
    temp_token = await temp_token_repository.create_temp_token(
        session, email, expiration_minutes=custom_expiration
    )
    await session.commit()
    
    # 有効期限が設定された時間になっていること（許容誤差1分）
    expected_expires_at = now_utc() + timedelta(minutes=custom_expiration)
    time_diff = abs((temp_token.expires_at - expected_expires_at).total_seconds())
    assert time_diff < 60  # 1分以内の誤差



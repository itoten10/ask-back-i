import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import RoleEnum, User, UserGoogleAccount, UserLocalAccount
from app.repositories import user_repository


@pytest.mark.asyncio
async def test_get_user_with_local_account(session: AsyncSession):
    user = User(
        id=10,
        role=RoleEnum.admin,
        full_name="Admin User",
        full_name_kana="アドミンユーザー",
        email="admin@example.com",
    )
    local = UserLocalAccount(login_id="admin01", password_hash=hash_password("pass"), user=user)
    session.add_all([user, local])
    await session.commit()

    found_user, found_local = await user_repository.get_user_with_local_account(session, "admin01")
    assert found_user is not None
    assert found_local is not None
    assert found_user.id == user.id
    assert found_local.login_id == "admin01"


@pytest.mark.asyncio
async def test_upsert_google_account(session: AsyncSession):
    user = User(
        id=11,
        role=RoleEnum.teacher,
        full_name="Teacher User",
        full_name_kana="ティーチャー",
        email="teacher@example.com",
    )
    session.add(user)
    await session.flush()

    account = await user_repository.upsert_google_account(
        session, user=user, google_sub="sub123", google_email="teacher@gmail.com"
    )
    await session.commit()

    assert isinstance(account, UserGoogleAccount)
    assert account.user_id == user.id
    assert account.google_sub == "sub123"

    # second call should return existing account without duplicating
    again = await user_repository.upsert_google_account(
        session, user=user, google_sub="sub123", google_email="teacher@gmail.com"
    )
    assert again.user_id == user.id
    assert again.google_sub == "sub123"

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_password
from app.models.user import RoleEnum, User, UserLocalAccount, LoginLog
from app.services import auth_service


@pytest.mark.asyncio
async def test_local_login_and_me_flow(app_client):
    client, SessionLocal = app_client

    # seed a teacher user with local credentials
    async with SessionLocal() as db:  # type: AsyncSession
        user = User(
            id=20,
            role=RoleEnum.teacher,
            full_name="Teacher User",
            full_name_kana="ティーチャー",
            email="teacher@example.com",
        )
        db.add(user)
        await db.flush()
        db.add(
            UserLocalAccount(
                user_id=user.id,
                login_id="teacher01",
                password_hash=hash_password("pass123"),
            )
        )
        await db.commit()

    login_resp = client.post(
        "/auth/login/local",
        json={"login_id": "teacher01", "password": "pass123"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    token = data["token"]["access_token"]

    me_resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me = me_resp.json()
    assert me["email"] == "teacher@example.com"
    assert me["role"] == "teacher"

    # missing token should be unauthorized
    resp_unauth = client.get("/users/me")
    assert resp_unauth.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_flow(app_client):
    client, SessionLocal = app_client
    from app.core.config import settings

    # allow test client to keep the cookie over HTTP
    settings.refresh_cookie_secure = False

    async with SessionLocal() as db:
        user = User(
            id=21,
            role=RoleEnum.admin,
            full_name="Admin User",
            full_name_kana="アドミン",
            email="admin@example.com",
        )
        db.add(user)
        await db.flush()
        db.add(
            UserLocalAccount(
                user_id=user.id,
                login_id="admin01",
                password_hash=hash_password("pass123"),
            )
        )
        await db.commit()

    login_resp = client.post(
        "/auth/login/local",
        json={"login_id": "admin01", "password": "pass123"},
    )
    assert login_resp.status_code == 200

    # Get a fresh refresh_token directly from service to avoid client cookie limitations
    async with SessionLocal() as db:
        service_result = await auth_service.login_with_local(
            db=db,
            login_id="admin01",
            password="pass123",
            ip_address=None,
            user_agent=None,
        )
        refresh_token = service_result.refresh_token

    refresh_resp = client.post("/auth/refresh", cookies={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    new_token = refresh_resp.json()["access_token"]
    assert new_token


def test_google_login_endpoint(app_client):
    client, _ = app_client
    resp = client.get("/auth/google/login")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_url" in data


def test_logout_endpoint(app_client):
    client, _ = app_client
    resp = client.post("/auth/logout")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_login_stores_forwarded_ip(app_client):
    client, SessionLocal = app_client

    async with SessionLocal() as db:  # type: AsyncSession
        user = User(
            id=30,
            role=RoleEnum.teacher,
            full_name="Forwarded Teacher",
            full_name_kana="フォワード先生",
            email="forward@example.com",
        )
        db.add(user)
        await db.flush()
        db.add(
            UserLocalAccount(
                user_id=user.id,
                login_id="forward01",
                password_hash=hash_password("pass123"),
            )
        )
        await db.commit()

    client.post(
        "/auth/login/local",
        json={"login_id": "forward01", "password": "pass123"},
        headers={"x-forwarded-for": "203.0.113.10, 10.0.0.1", "x-real-ip": "198.51.100.5"},
    )

    async with SessionLocal() as db:
        # fetch most recent login log
        res = await db.execute(select(LoginLog).order_by(LoginLog.id.desc()).limit(1))
        row = res.first()
        assert row is not None
        log: LoginLog = row[0]
        assert log.ip_address == "203.0.113.10"

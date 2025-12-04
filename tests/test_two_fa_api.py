import pytest
import pyotp
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.user import RoleEnum, User, UserLocalAccount, TempToken
from app.repositories import temp_token_repository, user_repository


@pytest.mark.asyncio
async def test_google_login_endpoint_new_user(app_client):
    """Googleログインエンドポイント - 新規ユーザーのテスト"""
    client, SessionLocal = app_client
    
    # モックGoogle ID Token（デモ環境では簡易検証）
    # 実際のJWT形式のトークンを作成
    import jwt
    from app.core.config import settings
    
    id_token = jwt.encode(
        {
            "email": "newuser@gmail.com",
            "sub": "google-sub-123",
            "iss": "https://accounts.google.com",
        },
        "dummy-secret",
        algorithm="HS256"
    )
    
    response = client.post(
        "/api/auth/google-login",
        json={
            "id_token": id_token,
            "email": "newuser@gmail.com",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "temp_token" in data
    assert "is_2fa_enabled" in data
    assert "user_id" in data
    assert data["is_2fa_enabled"] is False  # 新規ユーザーは2FA未設定


@pytest.mark.asyncio
async def test_google_login_endpoint_existing_user(app_client):
    """Googleログインエンドポイント - 既存ユーザーのテスト"""
    client, SessionLocal = app_client
    
    # 既存ユーザーを作成
    async with SessionLocal() as db:
        user = User(
            role=RoleEnum.student,
            full_name="Existing User",
            email="existing@gmail.com",
            is_2fa_enabled=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        user_id = user.id
    
    import jwt
    
    id_token = jwt.encode(
        {
            "email": "existing@gmail.com",
            "sub": "google-sub-456",
            "iss": "https://accounts.google.com",
        },
        "dummy-secret",
        algorithm="HS256"
    )
    
    response = client.post(
        "/api/auth/google-login",
        json={
            "id_token": id_token,
            "email": "existing@gmail.com",
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert "temp_token" in data


@pytest.mark.asyncio
async def test_2fa_setup_endpoint(app_client):
    """2FA設定エンドポイントのテスト"""
    client, SessionLocal = app_client
    
    # ユーザーと一時トークンを作成
    async with SessionLocal() as db:
        user = User(
            role=RoleEnum.student,
            full_name="Test User",
            email="test@gmail.com",
            is_2fa_enabled=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        temp_token = await temp_token_repository.create_temp_token(db, user.email)
        await db.commit()
        token_value = temp_token.token
    
    response = client.post(
        "/api/2fa/setup",
        headers={"Authorization": f"Bearer {token_value}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "secret" in data
    assert "otpauth_url" in data
    assert data["secret"] is not None
    assert "otpauth://" in data["otpauth_url"]


@pytest.mark.asyncio
async def test_2fa_setup_endpoint_already_enabled(app_client):
    """2FA設定済みユーザーが再度設定しようとした場合のテスト"""
    client, SessionLocal = app_client
    
    # 2FA設定済みユーザーを作成
    async with SessionLocal() as db:
        user = User(
            role=RoleEnum.student,
            full_name="Test User",
            email="test2fa@gmail.com",
            is_2fa_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",
        )
        db.add(user)
        await db.commit()
        
        temp_token = await temp_token_repository.create_temp_token(db, user.email)
        await db.commit()
        token_value = temp_token.token
    
    response = client.post(
        "/api/2fa/setup",
        headers={"Authorization": f"Bearer {token_value}"}
    )
    
    assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_2fa_verify_endpoint(app_client):
    """2FA検証エンドポイント（未設定ユーザー）のテスト"""
    client, SessionLocal = app_client
    
    # ユーザーと一時トークン、シークレットを作成
    secret = "JBSWY3DPEHPK3PXP"  # テスト用固定シークレット
    async with SessionLocal() as db:
        user = User(
            role=RoleEnum.student,
            full_name="Test User",
            email="verify@gmail.com",
            is_2fa_enabled=False,
            totp_secret=secret,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        temp_token = await temp_token_repository.create_temp_token(db, user.email)
        await db.commit()
        token_value = temp_token.token
    
    # 正しいTOTPコードを生成
    totp = pyotp.TOTP(secret)
    correct_code = totp.now()
    
    response = client.post(
        "/api/2fa/verify",
        headers={"Authorization": f"Bearer {token_value}"},
        json={"code": correct_code}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_2fa_verify_endpoint_invalid_code(app_client):
    """2FA検証エンドポイント - 無効なコードのテスト"""
    client, SessionLocal = app_client
    
    secret = "JBSWY3DPEHPK3PXP"
    async with SessionLocal() as db:
        user = User(
            role=RoleEnum.student,
            full_name="Test User",
            email="invalid@gmail.com",
            is_2fa_enabled=False,
            totp_secret=secret,
        )
        db.add(user)
        await db.commit()
        
        temp_token = await temp_token_repository.create_temp_token(db, user.email)
        await db.commit()
        token_value = temp_token.token
    
    response = client.post(
        "/api/2fa/verify",
        headers={"Authorization": f"Bearer {token_value}"},
        json={"code": "000000"}  # 無効なコード
    )
    
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_2fa_verify_existing_endpoint(app_client):
    """2FA検証エンドポイント（設定済みユーザー）のテスト"""
    client, SessionLocal = app_client
    
    secret = "JBSWY3DPEHPK3PXP"
    async with SessionLocal() as db:
        user = User(
            role=RoleEnum.student,
            full_name="Test User",
            email="existing2fa@gmail.com",
            is_2fa_enabled=True,
            totp_secret=secret,
        )
        db.add(user)
        await db.commit()
        
        temp_token = await temp_token_repository.create_temp_token(db, user.email)
        await db.commit()
        token_value = temp_token.token
    
    # 正しいTOTPコードを生成
    totp = pyotp.TOTP(secret)
    correct_code = totp.now()
    
    response = client.post(
        "/api/2fa/verify-existing",
        headers={"Authorization": f"Bearer {token_value}"},
        json={"code": correct_code}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_2fa_verify_existing_endpoint_not_enabled(app_client):
    """2FA未設定ユーザーがverify-existingを呼び出した場合のテスト"""
    client, SessionLocal = app_client
    
    async with SessionLocal() as db:
        user = User(
            role=RoleEnum.student,
            full_name="Test User",
            email="notenabled@gmail.com",
            is_2fa_enabled=False,
        )
        db.add(user)
        await db.commit()
        
        temp_token = await temp_token_repository.create_temp_token(db, user.email)
        await db.commit()
        token_value = temp_token.token
    
    response = client.post(
        "/api/2fa/verify-existing",
        headers={"Authorization": f"Bearer {token_value}"},
        json={"code": "123456"}
    )
    
    assert response.status_code == 400  # Bad Request


@pytest.mark.asyncio
async def test_temp_token_authentication_required(app_client):
    """一時トークン認証が必要なエンドポイントのテスト"""
    client, SessionLocal = app_client
    
    # 認証ヘッダーなしでリクエスト
    response = client.post("/api/2fa/setup")
    assert response.status_code == 401  # Unauthorized
    
    # 無効なトークンでリクエスト
    response = client.post(
        "/api/2fa/setup",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401



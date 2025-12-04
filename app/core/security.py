import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def generate_token(length: int = 48) -> str:
    return secrets.token_urlsafe(length)


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def now_utc() -> datetime:
    return datetime.utcnow()


def create_access_token(
    data: Dict[str, Any],
    secret: str,
    expires_minutes: int,
) -> str:
    to_encode = data.copy()
    expire = now_utc() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm="HS256")


def verify_google_id_token(id_token: str, email: str) -> bool:
    """
    Google ID Token検証
    デモ環境: 簡易検証（JWT形式チェック、メールアドレス一致）
    本番環境: 完全検証（google-authライブラリ使用）
    """
    import os
    
    app_env = os.getenv("APP_ENV", "local")
    
    if app_env == "production":
        # 本番環境: 完全検証
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token
            
            from app.core.config import settings
            
            request_obj = requests.Request()
            id_info = id_token.verify_oauth2_token(
                id_token, request_obj, settings.google_client_id
            )
            
            # 発行者検証
            if id_info.get("iss") != "https://accounts.google.com":
                return False
            
            # メールアドレス検証
            if id_info.get("email") != email:
                return False
            
            return True
        except Exception:
            return False
    else:
        # デモ環境: 簡易検証
        try:
            # JWT形式チェック（署名検証なし）
            decoded = jwt.decode(
                id_token, options={"verify_signature": False}, algorithms=["HS256"]
            )
            
            # メールアドレス一致チェック
            if decoded.get("email") != email:
                return False
            
            # 基本的な形式チェック
            if not decoded.get("iss") or not decoded.get("sub"):
                return False
            
            return True
        except Exception:
            return False
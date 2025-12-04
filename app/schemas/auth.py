from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class LocalLoginRequest(BaseModel):
    login_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class GoogleLoginUrlResponse(BaseModel):
    authorization_url: str


class RefreshRequest(BaseModel):
    # Cookie ベース運用のためボディは不要だが、空のモデルで 422 を避ける
    pass


class LogoutResponse(BaseModel):
    detail: str


class AuthSuccessResponse(BaseModel):
    token: TokenResponse
    user_id: int
    role: str
    full_name: str
    email: EmailStr
    session_token: str
    issued_at: datetime


# 2FA関連スキーマ
class GoogleLoginRequest(BaseModel):
    """Google ID Tokenベースのログインリクエスト"""
    id_token: str = Field(..., min_length=1)
    email: EmailStr


class GoogleLoginResponse(BaseModel):
    """Googleログイン後のレスポンス（2FA設定状態と一時トークン）"""
    is_2fa_enabled: bool
    temp_token: str
    user_id: int


class TwoFASetupResponse(BaseModel):
    """2FA設定用QRコード情報"""
    secret: str
    otpauth_url: str


class TwoFAVerifyRequest(BaseModel):
    """TOTPコード検証リクエスト"""
    code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")


class ErrorResponse(BaseModel):
    """統一エラーレスポンス"""
    error: dict
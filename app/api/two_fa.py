from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import rate_limiter
from app.core.security import verify_google_id_token
from app.models.user import TempToken, User
from app.repositories import temp_token_repository, user_repository
from app.repositories.temp_token_repository import get_temp_token
from app.schemas.auth import (
    ErrorResponse,
    GoogleLoginRequest,
    GoogleLoginResponse,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
    TokenResponse,
)
from app.services import auth_service
from app.services.two_fa_service import (
    generate_otpauth_url,
    generate_totp_secret,
    verify_totp,
)


router = APIRouter(prefix="/api", tags=["2FA"])
temp_token_scheme = HTTPBearer(auto_error=False)


async def verify_temp_token_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(temp_token_scheme),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, TempToken]:
    """一時トークン検証の依存性注入"""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    
    token = credentials.credentials
    temp_token = await get_temp_token(db, token)
    if not temp_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired temp token",
        )
    
    user = await user_repository.get_user_by_email(db, temp_token.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user, temp_token


@router.post("/auth/google-login")
async def google_login(
    response: Response,
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Google ID Tokenベースのログイン
    2FA無効の場合は直接トークン発行、有効な場合は一時トークン発行
    """
    # Google ID Token検証
    if not verify_google_id_token(payload.id_token, payload.email):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID Token",
        )

    # ユーザー取得または作成
    user = await user_repository.create_or_get_user(
        db, email=payload.email, name=None  # 名前はGoogleから取得可能だが簡略化
    )
    await db.commit()

    # 2FAが無効の場合は直接JWTトークンを発行して認証完了
    if not user.is_2fa_enabled:
        from app.models.user import AuthTypeEnum

        result = await auth_service._issue_tokens(
            user=user,
            auth_type=AuthTypeEnum.google,
            db=db,
            ip_address=None,
            user_agent=None,
        )
        await db.commit()

        # refresh_tokenをCookieにセット
        response.set_cookie(
            key=settings.refresh_cookie_name,
            value=result.refresh_token,
            httponly=True,
            secure=settings.refresh_cookie_secure,
            samesite=settings.refresh_cookie_samesite,
            path=settings.refresh_cookie_path,
            domain=settings.refresh_cookie_domain,
            max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        )

        # 2FA無効の場合、temp_tokenの代わりにaccess_tokenを返す
        return GoogleLoginResponse(
            is_2fa_enabled=False,
            temp_token=None,  # temp_tokenはNoneにする
            user_id=user.id,
            access_token=result.token.access_token,  # access_tokenを返す
            token_type="bearer",
            expires_in=result.token.expires_in,
        )

    # 2FA有効の場合は一時トークン発行
    temp_token = await temp_token_repository.create_temp_token(db, payload.email)
    await db.commit()

    return GoogleLoginResponse(
        is_2fa_enabled=user.is_2fa_enabled,
        temp_token=temp_token.token,
        user_id=user.id,
    )


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(
    user_and_token: tuple[User, TempToken] = Depends(verify_temp_token_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    2FA未設定ユーザー向けのセットアップ情報生成
    一時トークン必須
    """
    # 一時トークン検証
    user, temp_token = user_and_token
    
    if user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="2FA already enabled",
        )
    
    # シークレット生成
    secret = generate_totp_secret()
    
    # ユーザーのtotp_secretに保存（まだ有効化しない）
    from sqlalchemy import update
    from app.models.user import User as UserModel
    
    stmt = (
        update(UserModel)
        .where(UserModel.id == user.id)
        .values(totp_secret=secret)
    )
    await db.execute(stmt)
    await db.commit()
    
    # otpauth:// URL生成
    otpauth_url = generate_otpauth_url(user.email, secret)
    
    return TwoFASetupResponse(secret=secret, otpauth_url=otpauth_url)


@router.post("/2fa/verify", response_model=TokenResponse)
async def verify_2fa(
    payload: TwoFAVerifyRequest,
    user_and_token: tuple[User, TempToken] = Depends(verify_temp_token_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    2FA未設定ユーザーのTOTPコード検証と本番トークン発行
    一時トークン必須
    """
    # 一時トークン検証
    user, temp_token = user_and_token
    
    # レート制限チェック
    if not rate_limiter.check_rate_limit(user.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    
    # ユーザーオブジェクトをデータベースから再取得（最新のtotp_secretを取得するため）
    from sqlalchemy import select
    stmt = select(User).where(User.id == user.id)
    result = await db.execute(stmt)
    user = result.scalar_one()
    
    # セッションをリフレッシュして最新の状態を取得
    await db.refresh(user)
    
    # TOTPシークレット取得
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TOTP secret not set",
        )
    
    # デバッグログ（本番環境では削除）
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Verifying TOTP code for user {user.email}, secret length: {len(user.totp_secret)}, code: {payload.code}")
    
    # TOTPコード検証
    if not verify_totp(user.totp_secret, payload.code):
        logger.warning(f"TOTP verification failed for user {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
        )
    
    # 2FA有効化
    await user_repository.enable_2fa(db, user, user.totp_secret)
    
    # 一時トークン無効化
    await temp_token_repository.invalidate_temp_token(db, temp_token)
    
    # JWTアクセストークン発行
    from app.models.user import AuthTypeEnum
    
    result = await auth_service._issue_tokens(
        user=user,
        auth_type=AuthTypeEnum.google,
        db=db,
        ip_address=None,  # リクエストから取得可能だが簡略化
        user_agent=None,
    )
    await db.commit()
    
    return TokenResponse(
        access_token=result.token.access_token,
        token_type="bearer",
        expires_in=result.token.expires_in,
    )


@router.post("/2fa/verify-existing", response_model=TokenResponse)
async def verify_existing_2fa(
    payload: TwoFAVerifyRequest,
    user_and_token: tuple[User, TempToken] = Depends(verify_temp_token_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    2FA設定済みユーザーのログイン時のコード検証
    一時トークン必須
    """
    # デバッグログ
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"verify_existing_2fa - payload: {payload}, code: {payload.code}")
    
    # 一時トークン検証
    user, temp_token = user_and_token
    
    # 2FA設定済みチェック
    if not user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled",
        )
    
    # レート制限チェック
    if not rate_limiter.check_rate_limit(user.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    
    # TOTPシークレット取得
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TOTP secret not found",
        )
    
    # TOTPコード検証
    if not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
        )
    
    # 一時トークン無効化
    await temp_token_repository.invalidate_temp_token(db, temp_token)

    # JWTアクセストークン発行
    from app.models.user import AuthTypeEnum

    result = await auth_service._issue_tokens(
        user=user,
        auth_type=AuthTypeEnum.google,
        db=db,
        ip_address=None,
        user_agent=None,
    )
    await db.commit()

    return TokenResponse(
        access_token=result.token.access_token,
        token_type="bearer",
        expires_in=result.token.expires_in,
    )


@router.post("/auth/exchange-token")
async def exchange_token(
    response: Response,
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
):
    """
    フロントエンドからaccess_tokenを受け取り、refresh_tokenクッキーを設定する
    NextAuthのサーバーサイドコールバック内で取得したクッキーがクライアントに転送されないため、
    クライアント側から再度リクエストしてrefresh_tokenクッキーを設定する
    """
    import jwt
    from app.models.user import AuthTypeEnum

    # access_tokenを検証
    try:
        payload = jwt.decode(
            authorization.credentials,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )

    # ユーザー取得
    user = await user_repository.find_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 新しいトークンペアを発行
    result = await auth_service._issue_tokens(
        user=user,
        auth_type=AuthTypeEnum.google,
        db=db,
        ip_address=None,
        user_agent=None,
    )
    await db.commit()

    # refresh_tokenをCookieにセット
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=result.refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
        domain=settings.refresh_cookie_domain,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
    )

    return TokenResponse(
        access_token=result.token.access_token,
        token_type="bearer",
        expires_in=result.token.expires_in,
    )


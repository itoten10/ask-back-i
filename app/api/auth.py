from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import (
    AuthSuccessResponse,
    GoogleLoginUrlResponse,
    LocalLoginRequest,
    LogoutResponse,
    TokenResponse,
)
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str | None:
    """
    Try to get the actual client IP.
    Priority:
      1. X-Forwarded-For (first entry)
      2. X-Real-IP
      3. request.client.host
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    x_real = request.headers.get("x-real-ip")
    if x_real:
        return x_real.strip()
    return request.client.host if request.client else None


def _set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
        domain=settings.refresh_cookie_domain,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        domain=settings.refresh_cookie_domain,
    )


@router.post("/login/local", response_model=AuthSuccessResponse)
async def login_local(
    payload: LocalLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _get_client_ip(request)
    result = await auth_service.login_with_local(
        db=db,
        login_id=payload.login_id,
        password=payload.password,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, result.refresh_token)
    return AuthSuccessResponse.model_validate(result)


@router.get("/google/login", response_model=GoogleLoginUrlResponse)
async def google_login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return {"authorization_url": auth_url}


@router.get("/google/callback")
async def google_callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _get_client_ip(request)
    result = await auth_service.login_with_google(
        db=db,
        code=code,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )
    frontend_base = settings.cors_origins[0] if settings.cors_origins else "http://localhost:3000"
    redirect_url = f"{frontend_base}/me"
    response = RedirectResponse(url=redirect_url)
    _set_refresh_cookie(response, result.refresh_token)
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _get_client_ip(request)
    refresh_token_cookie = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    result = await auth_service.refresh_tokens(
        db=db,
        refresh_token=refresh_token_cookie,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, result.refresh_token)
    return result.token


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token_cookie = request.cookies.get(settings.refresh_cookie_name)
    await auth_service.logout(db=db, refresh_token=refresh_token_cookie)
    response = JSONResponse(content={"detail": "logged out"})
    _clear_refresh_cookie(response)
    return response

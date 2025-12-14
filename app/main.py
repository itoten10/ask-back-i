import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import admin_users, auth, users, two_fa, posts, admin_database, thanks_letters, dashboard
from app.core.config import settings
from app.core.database import engine


async def run_migration_on_startup():
    """アプリケーション起動時にマイグレーションを実行"""
    try:
        async with engine.begin() as conn:
            # MySQLではIF NOT EXISTSが使えないため、エラーハンドリングが必要
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
                print("✓ Added is_2fa_enabled column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e).lower():
                    pass  # 既に存在する場合は無視
                else:
                    print(f"⚠ Warning: Could not add is_2fa_enabled column: {e}")

            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR(255) NULL"))
                print("✓ Added totp_secret column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e).lower():
                    pass  # 既に存在する場合は無視
                else:
                    print(f"⚠ Warning: Could not add totp_secret column: {e}")

            try:
                await conn.execute(text("""
                    CREATE TABLE temp_tokens (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        token VARCHAR(255) NOT NULL UNIQUE,
                        email VARCHAR(255) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_used BOOLEAN NOT NULL DEFAULT FALSE,
                        INDEX idx_token (token),
                        INDEX idx_email (email),
                        INDEX idx_expires_at (expires_at)
                    )
                """))
                print("✓ Created temp_tokens table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    pass  # 既に存在する場合は無視
                else:
                    print(f"⚠ Warning: Could not create temp_tokens table: {e}")

        print("✅ Database migration check completed")
    except Exception as e:
        print(f"⚠ Warning: Migration check failed (this is OK if tables already exist): {e}")


def create_app() -> FastAPI:
    app = FastAPI(title="School Auth")

    @app.on_event("startup")
    async def startup_event():
        """アプリケーション起動時のイベント"""
        await run_migration_on_startup()

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 422エラーの詳細をログ出力するための例外ハンドラー
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        print(f"🔴 422 Validation Error - Path: {request.url.path}, Method: {request.method}")
        print(f"🔴 422 Validation Error - Headers: {dict(request.headers)}")
        print(f"🔴 422 Validation Error - Details: {exc.errors()}")
        # exc.bodyはbytes型なので、文字列に変換してから表示
        body_str = exc.body.decode('utf-8') if hasattr(exc, 'body') and exc.body else 'N/A'
        print(f"🔴 422 Validation Error - Body: {body_str}")
        # exc.errors()の中のbytes型を文字列に変換
        errors = exc.errors()
        serializable_errors = []
        for error in errors:
            serializable_error = {}
            for key, value in error.items():
                if isinstance(value, bytes):
                    # bytes型の場合は文字列に変換
                    try:
                        serializable_error[key] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        serializable_error[key] = str(value)
                elif isinstance(value, tuple):
                    # tuple型の場合はリストに変換
                    serializable_error[key] = list(value)
                else:
                    serializable_error[key] = value
            serializable_errors.append(serializable_error)
        return JSONResponse(
            status_code=422,
            content={"detail": serializable_errors},
        )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(admin_users.router)
    app.include_router(two_fa.router)
    app.include_router(posts.router)
    app.include_router(admin_database.router, prefix="/admin/database", tags=["admin-database"])
    app.include_router(thanks_letters.router, prefix="/thanks-letters", tags=["thanks-letters"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    return app


app = create_app()

__all__ = ["app"]

"""データベースマイグレーション実行スクリプト（簡易版）"""
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine


async def run_migration():
    """マイグレーションを実行"""
    try:
        async with engine.begin() as conn:
            # MySQLではIF NOT EXISTSが使えないため、エラーハンドリングが必要
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
                print("✓ Added is_2fa_enabled column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e).lower():
                    print("ℹ Column is_2fa_enabled already exists")
                else:
                    raise

            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR(255) NULL"))
                print("✓ Added totp_secret column")
            except Exception as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e).lower():
                    print("ℹ Column totp_secret already exists")
                else:
                    raise

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
                    print("ℹ Table temp_tokens already exists")
                else:
                    raise

        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Running 2FA database migration (using existing database connection)...")
    asyncio.run(run_migration())



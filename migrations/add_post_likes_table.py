"""post_likesテーブル追加マイグレーション"""
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


async def run_migration():
    """マイグレーションを実行"""
    engine = create_async_engine(
        settings.database_url(),
        pool_pre_ping=True,
        echo=True,
        connect_args={"ssl": {"ssl_ca": settings.ssl_ca_path}} if settings.ssl_ca_path else {},
    )

    try:
        async with engine.begin() as conn:
            try:
                await conn.execute(text("""
                    CREATE TABLE post_likes (
                        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                        post_id BIGINT UNSIGNED NOT NULL,
                        user_id BIGINT UNSIGNED NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY uq_post_like_post_user (post_id, user_id),
                        INDEX idx_post_likes_post_id (post_id),
                        INDEX idx_post_likes_user_id (user_id),
                        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                print("✓ Created post_likes table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("ℹ Table post_likes already exists")
                else:
                    raise

        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Running post_likes table migration...")
    print(f"Database: {settings.db_host}/{settings.db_name}")
    asyncio.run(run_migration())

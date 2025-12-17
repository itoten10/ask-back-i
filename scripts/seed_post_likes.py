"""投稿にサンプルのいいねデータを追加するスクリプト"""
import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


async def seed_likes():
    """各投稿に10-20のいいねを追加"""
    engine = create_async_engine(
        settings.database_url(),
        pool_pre_ping=True,
        echo=False,
        connect_args={"ssl": {"ssl_ca": settings.ssl_ca_path}} if settings.ssl_ca_path else {},
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # 全ての投稿IDを取得
            posts_result = await session.execute(
                text("SELECT id FROM posts WHERE deleted_at IS NULL")
            )
            post_ids = [row[0] for row in posts_result.fetchall()]
            print(f"投稿数: {len(post_ids)}")

            # 全てのユーザーIDを取得
            users_result = await session.execute(
                text("SELECT id FROM users WHERE is_deleted = 0 AND is_active = 1")
            )
            user_ids = [row[0] for row in users_result.fetchall()]
            print(f"ユーザー数: {len(user_ids)}")

            if len(user_ids) < 10:
                print("警告: ユーザー数が少ないため、いいね数が少なくなります")

            # 既存のいいねを削除
            await session.execute(text("DELETE FROM post_likes"))
            await session.commit()
            print("既存のいいねを削除しました")

            # 各投稿にランダムないいねを追加（バッチINSERTで高速化）
            total_likes = 0
            all_likes = []

            for post_id in post_ids:
                # 10-20のランダムな数のいいねを追加
                like_count = random.randint(10, 20)

                # ユーザー数がlike_countより少ない場合は調整
                actual_count = min(like_count, len(user_ids))

                # ランダムにユーザーを選択
                selected_users = random.sample(user_ids, actual_count)

                for user_id in selected_users:
                    # ランダムな日時を生成（過去30日以内）
                    random_days = random.randint(0, 30)
                    random_hours = random.randint(0, 23)
                    created_at = datetime.utcnow() - timedelta(days=random_days, hours=random_hours)

                    all_likes.append({
                        "post_id": post_id,
                        "user_id": user_id,
                        "created_at": created_at
                    })

                total_likes += actual_count

            # バッチサイズ500でINSERT
            batch_size = 500
            for i in range(0, len(all_likes), batch_size):
                batch = all_likes[i:i + batch_size]
                if batch:
                    # バッチINSERTを実行
                    values_str = ", ".join([
                        f"({like['post_id']}, {like['user_id']}, '{like['created_at'].strftime('%Y-%m-%d %H:%M:%S')}')"
                        for like in batch
                    ])
                    await session.execute(
                        text(f"INSERT INTO post_likes (post_id, user_id, created_at) VALUES {values_str}")
                    )
                    print(f"  {min(i + batch_size, len(all_likes))}/{len(all_likes)} 件挿入...")

            await session.commit()
            print(f"✅ {len(post_ids)}件の投稿に合計{total_likes}件のいいねを追加しました")
            print(f"   平均いいね数: {total_likes / len(post_ids):.1f}")

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("投稿にいいねデータを追加中...")
    asyncio.run(seed_likes())

"""非認知能力の7項目をデータベースに登録するスクリプト"""
import asyncio
from datetime import datetime
import asyncmy
from app.core.config import settings


async def insert_abilities():
    """7つの非認知能力を登録"""
    ssl_config = {"ssl_ca": settings.ssl_ca_path} if settings.ssl_ca_path else None
    conn = await asyncmy.connect(
        host=settings.db_host,
        port=int(settings.db_port),
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        ssl=ssl_config,
    )

    try:
        cursor = conn.cursor()

        # 7つの非認知能力データ
        abilities = [
            {
                "code": "problem_setting",
                "name": "課題設定力",
                "description": "適切な課題を設定し、明確な問いを立てる力"
            },
            {
                "code": "information_gathering",
                "name": "情報収集力",
                "description": "必要な情報を効率的に収集し、整理する力"
            },
            {
                "code": "involvement",
                "name": "巻き込む力",
                "description": "他者を巻き込み、協力を得る力"
            },
            {
                "code": "communication",
                "name": "対話する力",
                "description": "他者と建設的な対話を行い、理解を深める力"
            },
            {
                "code": "humility",
                "name": "謙虚である力",
                "description": "他者の意見を受け入れ、学び続ける姿勢"
            },
            {
                "code": "execution",
                "name": "実行する力",
                "description": "計画を実行に移し、行動する力"
            },
            {
                "code": "completion",
                "name": "完遂する力",
                "description": "最後までやり遂げる力、継続する力"
            },
        ]

        now = datetime.utcnow()

        for ability in abilities:
            # 既に存在するかチェック
            await cursor.execute(
                "SELECT id FROM non_cog_abilities WHERE code = %s",
                (ability["code"],)
            )
            existing = await cursor.fetchone()

            if existing:
                print(f"✓ {ability['name']} は既に登録されています (ID: {existing[0]})")
            else:
                await cursor.execute(
                    """
                    INSERT INTO non_cog_abilities (code, name, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (ability["code"], ability["name"], ability["description"], now, now)
                )
                print(f"✅ {ability['name']} を登録しました")

        await conn.commit()
        print("\n✅ 非認知能力の登録が完了しました！")

    except Exception as e:
        print(f"❌ エラー: {e}")
        await conn.rollback()
        raise
    finally:
        await cursor.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(insert_abilities())

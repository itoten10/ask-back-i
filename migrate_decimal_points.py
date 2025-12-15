"""能力ポイントのカラムをDECIMAL型に変更"""
import asyncio
import ssl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DB_USER = "students"
DB_PASSWORD = "10th-tech0"
DB_HOST = "gen10-mysql-dev-01.mysql.database.azure.com"
DB_PORT = 3306
DB_NAME = "ask"
SSL_CA_PATH = "./DigiCertGlobalRootG2.crt.pem"

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ssl_context = ssl.create_default_context(cafile=SSL_CA_PATH)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False, connect_args={"ssl": ssl_context})
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def main():
    async with AsyncSessionLocal() as db:
        print("=== 能力ポイントカラムをDECIMAL型に変更 ===\n")

        # 1. thanks_letter_ability_points の points カラムを DECIMAL に変更
        print("1. thanks_letter_ability_points.points を DECIMAL(5,1) に変更...")
        try:
            await db.execute(text("""
                ALTER TABLE thanks_letter_ability_points
                MODIFY COLUMN points DECIMAL(5,1) NOT NULL DEFAULT 1.5
            """))
            await db.commit()
            print("   完了")
        except Exception as e:
            print(f"   エラー（既に変更済みかも）: {e}")

        # 2. post_ability_points の point カラムを DECIMAL に変更
        print("2. post_ability_points.point を DECIMAL(5,1) に変更...")
        try:
            await db.execute(text("""
                ALTER TABLE post_ability_points
                MODIFY COLUMN point DECIMAL(5,1) NOT NULL DEFAULT 1.0
            """))
            await db.commit()
            print("   完了")
        except Exception as e:
            print(f"   エラー（既に変更済みかも）: {e}")

        print("\n=== 完了 ===")


asyncio.run(main())

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings


engine = create_async_engine(
    settings.database_url(),
    pool_pre_ping=True,
    echo=False,
    connect_args={"ssl": {"ssl_ca": settings.ssl_ca_path}} if settings.ssl_ca_path else {},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

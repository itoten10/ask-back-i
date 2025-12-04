import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import create_app

from app.models.base import Base


@pytest.fixture
async def db_engine() -> AsyncEngine:
    """
    Provides an in-memory SQLite engine for each test.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(db_engine: AsyncEngine) -> AsyncSession:
    """
    Yields a single AsyncSession backed by the in-memory SQLite engine.
    """
    SessionLocal = async_sessionmaker(db_engine, expire_on_commit=False)
    async with SessionLocal() as db:
        yield db


@pytest.fixture
async def app_client(db_engine: AsyncEngine):
    """
    Provides a TestClient with get_db overridden to use the in-memory SQLite engine.
    Also returns the sessionmaker for seeding data.
    """
    SessionLocal = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with SessionLocal() as db:
            yield db

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client, SessionLocal
    finally:
        app.dependency_overrides.clear()
        client.close()

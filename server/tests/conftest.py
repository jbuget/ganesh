"""Fixtures shared by the integration tests.

Tests marked `db` hit a real PostgreSQL database: the schema is created by the
Alembic migrations, never by `create_all`, so that what runs in production is
exactly what gets tested.
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from alembic.config import Config

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://timesheet:timesheet@localhost:5432/timesheet_test",
)


@pytest.fixture(scope="session")
def migrated_database() -> str:
    """Applies the migrations to the test database, once per session."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return TEST_DATABASE_URL


@pytest_asyncio.fixture
async def db_session(migrated_database: str) -> AsyncGenerator[AsyncSession, None]:
    """One isolated session per test: everything is rolled back at the end."""
    engine = create_async_engine(migrated_database)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = factory(bind=connection)
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
    await engine.dispose()

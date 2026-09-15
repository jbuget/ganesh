"""Fixtures partagees par les tests d'integration.

Les tests marques `db` touchent une vraie base PostgreSQL : le schema est cree
par les migrations Alembic, jamais par `create_all`, afin de tester exactement
ce qui tournera en production.
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


def _sync_url(url: str) -> str:
    return url.replace("+asyncpg", "")


@pytest.fixture(scope="session")
def migrated_database() -> str:
    """Applique les migrations sur la base de test, une fois par session."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return TEST_DATABASE_URL


@pytest_asyncio.fixture
async def db_session(migrated_database: str) -> AsyncGenerator[AsyncSession, None]:
    """Une session isolee par test : tout est annule a la fin."""
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

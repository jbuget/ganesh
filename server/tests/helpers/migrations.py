"""Exercising a migration that rewrites data, rather than reading it.

The database is stood up at the revision just before the one under test,
filled with the shapes production holds, then carried one step forward —
which is exactly what the deploy does.

A database of its own each time, dropped at the end: the migrations here are
run out of step with the ones the rest of the suite shares, and a session-wide
schema taken back a revision would pull the ground from under every other test.

Synchronous on purpose. Alembic's `env.py` opens its own event loop to
migrate, which it cannot do from inside one already running.
"""

import asyncio
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config

#: The database the suite already talks to, which says where the server is.
SUITE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://timesheet:timesheet@localhost:5432/timesheet_test",
)
SERVER = SUITE_URL.rsplit("/", 1)[0]


async def _run(url: str, statements: str, autocommit: bool = False) -> None:
    engine = create_async_engine(
        url, isolation_level="AUTOCOMMIT" if autocommit else "READ COMMITTED"
    )
    try:
        async with engine.begin() as connection:
            for statement in filter(None, (s.strip() for s in statements.split(";"))):
                await connection.execute(text(statement))
    finally:
        await engine.dispose()


async def _read(url: str, query: str) -> list[tuple[Any, ...]]:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as connection:
            return [tuple(row) for row in (await connection.execute(text(query))).all()]
    finally:
        await engine.dispose()


def fill(url: str, statements: str) -> None:
    asyncio.run(_run(url, statements))


def rows(url: str, query: str) -> list[tuple[Any, ...]]:
    return asyncio.run(_read(url, query))


def _config(url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    return config


def upgrade(url: str, revision: str) -> None:
    """Forward to `revision` — what the deploy does, and nothing else."""
    command.upgrade(_config(url), revision)


def downgrade(url: str, revision: str) -> None:
    """Back to `revision` — what a rollback does."""
    command.downgrade(_config(url), revision)


@contextmanager
def database_at(revision: str, name: str) -> Iterator[str]:
    """A database of its own, `name`, stood up at `revision`."""
    postgres = f"{SERVER}/postgres"
    asyncio.run(
        _run(
            postgres,
            f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE); CREATE DATABASE "{name}"',
            autocommit=True,
        )
    )
    url = f"{SERVER}/{name}"
    upgrade(url, revision)

    try:
        yield url
    finally:
        asyncio.run(
            _run(
                postgres,
                f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)',
                autocommit=True,
            )
        )

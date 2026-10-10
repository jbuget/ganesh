"""Persistence of the links that open a digest."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.gazette.domain.entities.share_link import ShareLink
from src.modules.gazette.infrastructure.database.repositories.digest_repository_impl import (
    SqlDigestRepository,
)
from src.modules.gazette.infrastructure.database.repositories.share_link_repository_impl import (
    SqlShareLinkRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from tests.helpers.instants import paris
from tests.modules.gazette.infrastructure.test_digest_repository import a_digest


async def a_stored_digest_and_author(session: AsyncSession) -> tuple[int, int]:
    author = await SqlUserRepository(session).add(
        User(
            id=None,
            entra_oid="oid-link",
            email="link@waat.fr",
            display_name="Léa Chen",
            role=Role.TEAMMATE,
        )
    )
    digest = await SqlDigestRepository(session).add(a_digest())
    assert digest.id is not None and author.id is not None
    return digest.id, author.id


async def test_a_link_is_found_by_its_token(db_session: AsyncSession) -> None:
    digest_id, author_id = await a_stored_digest_and_author(db_session)
    repository = SqlShareLinkRepository(db_session)
    link = await repository.add(
        ShareLink.open(digest_id, author_id, paris(2026, 10, 11, 9))
    )

    found = await repository.get_by_token(link.token)

    assert found is not None
    assert found.id == link.id
    assert found.is_open


async def test_an_unknown_token_finds_nothing(db_session: AsyncSession) -> None:
    assert await SqlShareLinkRepository(db_session).get_by_token("x" * 43) is None


async def test_only_the_open_links_of_a_digest_are_listed(
    db_session: AsyncSession,
) -> None:
    digest_id, author_id = await a_stored_digest_and_author(db_session)
    repository = SqlShareLinkRepository(db_session)
    kept = await repository.add(
        ShareLink.open(digest_id, author_id, paris(2026, 10, 11, 9))
    )
    closed = await repository.add(
        ShareLink.open(digest_id, author_id, paris(2026, 10, 11, 10))
    )
    closed.revoke(paris(2026, 10, 12, 9))
    await repository.update(closed)

    listed = await repository.list_open_for_digest(digest_id)

    assert [link.id for link in listed] == [kept.id]


async def test_closing_a_link_survives_the_trip(db_session: AsyncSession) -> None:
    digest_id, author_id = await a_stored_digest_and_author(db_session)
    repository = SqlShareLinkRepository(db_session)
    link = await repository.add(
        ShareLink.open(digest_id, author_id, paris(2026, 10, 11, 9))
    )
    link.revoke(paris(2026, 10, 12, 9))
    await repository.update(link)

    found = await repository.get(link.id or 0)

    assert found is not None
    assert not found.is_open


async def test_two_links_cannot_share_a_token(db_session: AsyncSession) -> None:
    digest_id, author_id = await a_stored_digest_and_author(db_session)
    repository = SqlShareLinkRepository(db_session)
    link = ShareLink.open(digest_id, author_id, paris(2026, 10, 11, 9))
    await repository.add(link)

    with pytest.raises(IntegrityError):
        await repository.add(link)

"""The request repository, against a real PostgreSQL database."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.requests.domain.entities.request import Request, RequestState
from src.modules.requests.infrastructure.database.repositories.request_repository_impl import (
    SqlRequestRepository,
)
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.infrastructure.database.repositories.user_repository_impl import (
    SqlUserRepository,
)
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel

pytestmark = pytest.mark.db


async def seed(session: AsyncSession) -> tuple[int, int]:
    """An author and a sponsor, and their identifiers."""
    users = SqlUserRepository(session)
    author = await users.add(
        User(
            id=None,
            entra_oid="oid-request-1",
            email="a.metier@waat.fr",
            display_name="A. Métier",
            role=Role.GUEST,
        )
    )
    sponsor = await users.add(
        User(
            id=None,
            entra_oid="oid-request-2",
            email="c.direction@waat.fr",
            display_name="C. Direction",
            role=Role.GUEST,
            org_level=OrgLevel.COMEX,
        )
    )
    assert author.id is not None and sponsor.id is not None
    return author.id, sponsor.id


def make_request(author: int, sponsor: int, **overrides) -> Request:
    fields: dict = {
        "id": None,
        "title": "Relances de paiement à la main",
        "requester_id": author,
        "departments": [Department.FINANCE_ADMIN, Department.OPERATIONS],
        "sponsor_ids": [sponsor],
    }
    fields.update(overrides)
    return Request(**fields)


async def test_a_request_is_persisted_with_the_lists_it_carries(
    db_session: AsyncSession,
) -> None:
    author, sponsor = await seed(db_session)
    repository = SqlRequestRepository(db_session)

    stored = await repository.add(make_request(author, sponsor))
    assert stored.id is not None
    read = await repository.get_by_id(stored.id)

    assert read is not None
    assert read.title == "Relances de paiement à la main"
    assert read.departments == [Department.FINANCE_ADMIN, Department.OPERATIONS]
    assert read.sponsor_ids == [sponsor]
    assert read.state is RequestState.DRAFT


async def test_rewriting_the_sheet_rewrites_both_lists(
    db_session: AsyncSession,
) -> None:
    author, sponsor = await seed(db_session)
    repository = SqlRequestRepository(db_session)
    stored = await repository.add(make_request(author, sponsor))
    assert stored.id is not None

    stored.departments = [Department.CUSTOMER_SERVICE]
    await repository.update(stored)
    read = await repository.get_by_id(stored.id)

    assert read is not None
    assert read.departments == [Department.CUSTOMER_SERVICE]
    assert read.sponsor_ids == [sponsor]


async def test_the_team_reads_everything_but_other_peoples_drafts(
    db_session: AsyncSession,
) -> None:
    author, sponsor = await seed(db_session)
    repository = SqlRequestRepository(db_session)
    draft = await repository.add(make_request(author, sponsor))
    handed = await repository.add(
        make_request(author, sponsor, title="Un autre besoin")
    )
    assert draft.id is not None and handed.id is not None
    handed.state = RequestState.SUBMITTED
    await repository.update(handed)

    # The sponsor is on the team here: what they see is what has been handed
    # over, and nothing that is still being written.
    assert [r.id for r in await repository.list_readable_by(sponsor)] == [handed.id]
    # Its author sees their own draft in the same list.
    assert len(await repository.list_readable_by(author)) == 2
    assert len(await repository.list_for_requester(author)) == 2


async def test_a_request_is_erased(db_session: AsyncSession) -> None:
    author, sponsor = await seed(db_session)
    repository = SqlRequestRepository(db_session)
    stored = await repository.add(make_request(author, sponsor))
    assert stored.id is not None

    await repository.delete(stored.id)

    assert await repository.get_by_id(stored.id) is None

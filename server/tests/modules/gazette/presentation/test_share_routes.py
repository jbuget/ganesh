"""The routes that open a digest to whoever holds a link."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.config import get_settings
from src.main import app
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.gazette.application.use_cases.list_share_links import (
    ListShareLinksUseCase,
)
from src.modules.gazette.application.use_cases.read_shared_digest import (
    ReadSharedDigestUseCase,
)
from src.modules.gazette.application.use_cases.revoke_share_link import (
    RevokeShareLinkUseCase,
)
from src.modules.gazette.application.use_cases.share_digest import ShareDigestUseCase
from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.digest import Digest
from src.modules.gazette.domain.entities.focus import ProjectFocus
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.spotlight import Spotlight
from src.modules.gazette.presentation.dependencies import (
    get_list_share_links_use_case,
    get_read_shared_digest_use_case,
    get_revoke_share_link_use_case,
    get_share_digest_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryDigestRepository,
    InMemoryShareLinkRepository,
    InMemoryUserRepository,
)
from tests.helpers.instants import paris

LEA = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
MONTH = date(2026, 9, 1)
GAZETTE = f"{get_settings().api_prefix}/gazette"


@dataclass
class Desk:
    client: AsyncClient
    digests: InMemoryDigestRepository

    async def open_link(self) -> dict:
        response = await self.client.post(
            f"{GAZETTE}/share-links", json={"month": "2026-09-01", "version": 1}
        )
        assert response.status_code == 201
        return response.json()


def an_internal_digest() -> Digest:
    return Digest(
        month=MONTH,
        version=1,
        brief=Brief(
            month=MONTH,
            tally=Tally(projects_created=2),
            movements=[
                Movement(
                    kind=MovementKind.TEAMMATE_JOINED,
                    at=paris(2026, 9, 4, 10),
                    subject="Sam Okafor",
                )
            ],
            highlights=[
                Highlight(kind=HighlightKind.WENT_LIVE, project_id=7, label="Ganesh"),
                Highlight(
                    kind=HighlightKind.GO_LIVE_OVERDUE, project_id=8, label="NOMAD"
                ),
            ],
            focus=[ProjectFocus(project_id=7, label="Ganesh", updates_posted=9)],
        ),
        generated_at=paris(2026, 10, 9, 11),
        requested_by="Léa Chen",
        prose=Prose(text="Un mois de cadrage.", model="stub"),
        spotlights=(
            Spotlight(7, "Ganesh", "Ganesh tient le registre des temps.", "stub"),
        ),
    )


async def sign_in() -> Desk:
    digests = InMemoryDigestRepository()
    await digests.add(an_internal_digest())
    users = InMemoryUserRepository([LEA])
    links = InMemoryShareLinkRepository()
    audit_logs = InMemoryAuditLogRepository()

    app.dependency_overrides[get_current_user] = lambda: LEA
    app.dependency_overrides[get_share_digest_use_case] = lambda: ShareDigestUseCase(
        users, digests, links, audit_logs
    )
    app.dependency_overrides[get_list_share_links_use_case] = (
        lambda: ListShareLinksUseCase(users, digests, links)
    )
    app.dependency_overrides[get_revoke_share_link_use_case] = (
        lambda: RevokeShareLinkUseCase(digests, links, audit_logs)
    )
    app.dependency_overrides[get_read_shared_digest_use_case] = (
        lambda: ReadSharedDigestUseCase(digests, links)
    )
    return Desk(
        client=AsyncClient(transport=ASGITransport(app=app), base_url="http://test"),
        digests=digests,
    )


@pytest.fixture(autouse=True)
def _forget_the_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def reader() -> AsyncClient:
    """Somebody who has not signed in: no override of the door is made for them."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_a_teammate_opens_a_link_on_a_version() -> None:
    desk = await sign_in()

    link = await desk.open_link()

    assert len(link["token"]) >= 40
    assert link["created_by"] == "L. Chen"


@pytest.mark.asyncio
async def test_a_version_nobody_generated_cannot_be_shared() -> None:
    desk = await sign_in()

    response = await desk.client.post(
        f"{GAZETTE}/share-links", json={"month": "2026-09-01", "version": 4}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_the_team_lists_the_open_links_of_a_version() -> None:
    desk = await sign_in()
    opened = await desk.open_link()

    response = await desk.client.get(
        f"{GAZETTE}/share-links", params={"month": "2026-09-01", "version": 1}
    )

    assert [link["id"] for link in response.json()] == [opened["id"]]


@pytest.mark.asyncio
async def test_closing_a_link_closes_what_it_opened() -> None:
    desk = await sign_in()
    opened = await desk.open_link()
    address = f"{GAZETTE}/shared/{opened['token']}"
    assert (await reader().get(address)).status_code == 200

    closed = await desk.client.delete(f"{GAZETTE}/share-links/{opened['id']}")

    assert closed.status_code == 204
    assert (await reader().get(address)).status_code == 404


@pytest.mark.asyncio
async def test_closing_a_link_that_does_not_exist_is_not_found() -> None:
    desk = await sign_in()

    assert (await desk.client.delete(f"{GAZETTE}/share-links/99")).status_code == 404


@pytest.mark.asyncio
async def test_anybody_holding_the_token_reads_the_narrative() -> None:
    desk = await sign_in()
    opened = await desk.open_link()

    response = await reader().get(f"{GAZETTE}/shared/{opened['token']}")

    body = response.json()
    assert response.status_code == 200
    assert body["prose"] == "Un mois de cadrage."
    assert body["version"] == 1
    assert [s["label"] for s in body["spotlights"]] == ["Ganesh"]
    assert body["went_live"] == ["Ganesh"]
    assert body["names"] == ["Ganesh"]


@pytest.mark.asyncio
async def test_what_a_link_opens_carries_nothing_of_the_register() -> None:
    desk = await sign_in()
    opened = await desk.open_link()

    body = (await reader().get(f"{GAZETTE}/shared/{opened['token']}")).json()

    assert set(body).isdisjoint(
        {"chapters", "highlights", "versions", "requested_by", "is_generated"}
    )
    assert "Sam Okafor" not in str(body)
    assert "NOMAD" not in str(body)
    assert "Léa Chen" not in str(body)


@pytest.mark.asyncio
async def test_the_answer_keeps_the_token_out_of_engines_and_referrers() -> None:
    desk = await sign_in()
    opened = await desk.open_link()

    response = await reader().get(f"{GAZETTE}/shared/{opened['token']}")

    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "no-store" in response.headers["cache-control"]


@pytest.mark.asyncio
async def test_an_unknown_token_opens_nothing() -> None:
    await sign_in()

    assert (await reader().get(f"{GAZETTE}/shared/{'x' * 43}")).status_code == 404

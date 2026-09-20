"""The door that admits the team **and** a machine.

`require_scope` opens a route to a key and to nobody else, which is right for
the catalogue: no screen calls it. Every other route a key reaches is one the
team already uses, so the door is added rather than swapped — whoever signed
in keeps coming in exactly as before.

The property this file exists for, beside that one: **a scope the form offers
opens a route**. A key minted on a promise the API does not keep makes the
table of keys say what a key opens, and say it wrong.
"""

from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient

import src.main  # noqa: F401  — imported for the doors it wires at import time
from src.core.database import get_db
from src.main import app
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
)
from src.modules.api_keys.application.use_cases.check_rate_limit import (
    CheckRateLimitUseCase,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.api_keys.domain.services import key_material
from src.modules.api_keys.domain.services.rate_limit import RateLimit
from src.modules.api_keys.infrastructure.rate_limit.in_memory_rate_limit_store import (
    InMemoryRateLimitStore,
)
from src.modules.api_keys.presentation.dependencies import (
    OPENED_SCOPES,
    get_authenticate_api_key_use_case,
    get_check_rate_limit_use_case,
    teammate_or_machine,
)
from src.modules.users.application.use_cases.list_users import ListUsersUseCase
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import get_list_users_use_case
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import (
    InMemoryApiKeyRepository,
    InMemoryUserRepository,
)

OWNER = User(id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba")
MANAGER = User(
    id=2,
    entra_oid="oid-2",
    email="b@waat.fr",
    display_name="B. Cy",
    role=Role.MANAGER,
)
TEAM = [OWNER, MANAGER]

#: The directory, which the team reads on screen and a machine may read too.
URL = "/api/v1/users"


class NoCommitSession:
    """Stands in for the session the door commits `last_used_at` through."""

    async def commit(self) -> None: ...


@pytest.fixture
async def http() -> AsyncIterator[AsyncClient]:
    """A client with nobody at the door: each test says who turns up."""
    keys = InMemoryApiKeyRepository()
    users = InMemoryUserRepository(TEAM)
    app.dependency_overrides[get_db] = lambda: NoCommitSession()
    app.dependency_overrides[get_authenticate_api_key_use_case] = (
        lambda: AuthenticateApiKeyUseCase(keys=keys, users=users)
    )
    app.dependency_overrides[get_check_rate_limit_use_case] = (
        lambda: CheckRateLimitUseCase(
            store=InMemoryRateLimitStore(),
            limit=RateLimit(allowance=50, window=timedelta(minutes=1)),
        )
    )
    app.dependency_overrides[get_list_users_use_case] = lambda: ListUsersUseCase(
        users=users
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        client.keys = keys  # type: ignore[attr-defined]
        yield client
    app.dependency_overrides.clear()


async def a_key(client: AsyncClient, *scopes: ApiKeyScope) -> str:
    public_id, secret, token = key_material.generate()
    await client.keys.add(  # type: ignore[attr-defined]
        ApiKey(
            id=None,
            name="CI waat-tools",
            public_id=public_id,
            secret_hash=key_material.hash_secret(secret),
            owner_id=1,
            created_by=2,
            scopes=list(scopes),
        )
    )
    return token


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestTheTeamKeepsComingThrough:
    """Adding a door takes none away. This is the regression that matters."""

    @pytest.mark.asyncio
    async def test_a_teammate_reads_the_directory(self, http: AsyncClient) -> None:
        app.dependency_overrides[teammate_or_machine] = lambda: OWNER

        assert (await http.get(URL)).status_code == 200


class TestAMachineComesThroughToo:
    @pytest.mark.asyncio
    async def test_a_key_carrying_the_scope_is_let_in(self, http: AsyncClient) -> None:
        token = await a_key(http, ApiKeyScope.USERS_READ)

        response = await http.get(URL, headers=bearer(token))

        assert response.status_code == 200
        assert [row["display_name"] for row in response.json()] == ["A. Ba", "B. Cy"]

    @pytest.mark.asyncio
    async def test_a_broad_read_scope_covers_it(self, http: AsyncClient) -> None:
        token = await a_key(http, ApiKeyScope.ALL_READ)

        assert (await http.get(URL, headers=bearer(token))).status_code == 200

    @pytest.mark.asyncio
    async def test_writing_everything_grants_no_read(self, http: AsyncClient) -> None:
        # The two broad scopes are independent, one per verb. A key granted
        # every write must not quietly gain every read behind the reader's back.
        token = await a_key(http, ApiKeyScope.ALL_WRITE)

        assert (await http.get(URL, headers=bearer(token))).status_code == 403

    @pytest.mark.asyncio
    async def test_a_key_short_of_the_scope_is_told_so(self, http: AsyncClient) -> None:
        # 403, not 401: whoever holds a real key needs to know what to ask for.
        token = await a_key(http, ApiKeyScope.CATALOG_READ)

        assert (await http.get(URL, headers=bearer(token))).status_code == 403

    @pytest.mark.asyncio
    async def test_a_key_short_of_the_scope_does_not_fall_back_to_the_team(
        self, http: AsyncClient
    ) -> None:
        # The door a token knocks on is decided by the token, once. A key that
        # is refused must not be tried again as though a person had called.
        app.dependency_overrides[teammate_or_machine] = lambda: OWNER
        token = await a_key(http, ApiKeyScope.CATALOG_READ)
        del app.dependency_overrides[teammate_or_machine]

        assert (await http.get(URL, headers=bearer(token))).status_code == 403

    @pytest.mark.asyncio
    async def test_an_unknown_key_says_401_whatever_the_reason(
        self, http: AsyncClient
    ) -> None:
        for token in ("jns_broken", "jns_a_b", key_material.generate()[2]):
            assert (await http.get(URL, headers=bearer(token))).status_code == 401

    @pytest.mark.asyncio
    async def test_a_revoked_key_is_turned_away(self, http: AsyncClient) -> None:
        # Revoked, expired, unknown, owner deactivated: one answer for all of
        # them, so none can be told from the others by trying.
        token = await a_key(http, ApiKeyScope.USERS_READ)
        parsed = key_material.parse(token)
        assert parsed is not None
        public_id, _ = parsed
        stored = await http.keys.get_by_public_id(  # type: ignore[attr-defined]
            public_id
        )
        stored.revoke(by=2, at=clock.now())

        assert (await http.get(URL, headers=bearer(token))).status_code == 401

    @pytest.mark.asyncio
    async def test_every_answer_says_what_is_left_of_the_allowance(
        self, http: AsyncClient
    ) -> None:
        token = await a_key(http, ApiKeyScope.USERS_READ)

        response = await http.get(URL, headers=bearer(token))

        assert response.headers["X-RateLimit-Limit"] == "50"
        assert response.headers["X-RateLimit-Remaining"] == "49"

    @pytest.mark.asyncio
    async def test_a_teammate_is_counted_against_nothing(
        self, http: AsyncClient
    ) -> None:
        # The allowance guards the machine door. A person coming through the
        # other one has no bucket, and no header saying otherwise.
        app.dependency_overrides[teammate_or_machine] = lambda: OWNER

        response = await http.get(URL)

        assert "X-RateLimit-Limit" not in response.headers


def test_every_scope_the_form_offers_opens_a_route() -> None:
    """No scope may promise what no route keeps.

    The two broad ones are the exception by construction: they open nothing of
    their own and are honoured by `ApiKey.grants`, which is what lets them
    cover a scope invented after the key was minted.
    """
    broad = {ApiKeyScope.ALL_READ, ApiKeyScope.ALL_WRITE}

    assert set(ApiKeyScope) - broad == OPENED_SCOPES

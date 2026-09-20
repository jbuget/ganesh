"""The routes of the service accounts, and the doors a key may not open.

The security property this file exists for: **a key opens nothing by default**.
Every route in the product leans on `get_current_user`, which turns keys away;
a machine gets in only where a route asked for a scope.
"""

from collections.abc import AsyncIterator
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db
from src.main import app
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
)
from src.modules.api_keys.application.use_cases.check_rate_limit import (
    CheckRateLimitUseCase,
)
from src.modules.api_keys.application.use_cases.manage_api_keys import (
    CreateApiKeyUseCase,
    ListApiKeysUseCase,
    RevokeApiKeyUseCase,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.api_keys.domain.services import key_material
from src.modules.api_keys.domain.services.rate_limit import RateLimit
from src.modules.api_keys.infrastructure.rate_limit.in_memory_rate_limit_store import (
    InMemoryRateLimitStore,
)
from src.modules.api_keys.presentation.dependencies import (
    get_authenticate_api_key_use_case,
    get_check_rate_limit_use_case,
    get_create_api_key_use_case,
    get_list_api_keys_use_case,
    get_revoke_api_key_use_case,
)
from src.modules.auth.presentation.dependencies import (
    get_current_manager,
    get_current_user,
)
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.projects.application.use_cases.export_catalog import (
    ExportCatalogUseCase,
)
from src.modules.projects.presentation.dependencies import get_export_catalog_use_case
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryApiKeyRepository,
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectDetailRepository,
    InMemoryProjectRepository,
    InMemoryUserRepository,
)

TEAMMATE = User(id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba")
MANAGER = User(
    id=2,
    entra_oid="oid-2",
    email="b@waat.fr",
    display_name="B. Cy",
    role=Role.MANAGER,
)
TEAM = [TEAMMATE, MANAGER]


class NoCommitSession:
    """Stands in for the database session `require_scope` commits through.

    The key repository is in memory here: there is nothing to commit, and the
    dependency must not reach for a real connection to prove its wiring.
    """

    async def commit(self) -> None: ...


#: Small on purpose: three calls are enough to walk into the wall.
TEST_LIMIT = RateLimit(allowance=3, window=timedelta(minutes=1))


def wire(keys: InMemoryApiKeyRepository, limit: RateLimit = TEST_LIMIT) -> None:
    users = InMemoryUserRepository(TEAM)
    audit = InMemoryAuditLogRepository()
    app.dependency_overrides[get_db] = lambda: NoCommitSession()
    # One store per wiring, built here rather than in the lambda: rebuilt per
    # request it would hand every call a full bucket and limit nothing — which
    # is exactly what `lru_cache` guards against in production.
    rate_limit = CheckRateLimitUseCase(store=InMemoryRateLimitStore(), limit=limit)
    app.dependency_overrides[get_check_rate_limit_use_case] = lambda: rate_limit
    app.dependency_overrides[get_authenticate_api_key_use_case] = (
        lambda: AuthenticateApiKeyUseCase(keys=keys, users=users)
    )
    # The one route that opens to a machine: stood in for so the test proves
    # the door, not the catalogue behind it.
    app.dependency_overrides[get_export_catalog_use_case] = (
        lambda: ExportCatalogUseCase(
            projects=InMemoryProjectRepository([]),
            details=InMemoryProjectDetailRepository(),
            assignees=InMemoryProjectAssigneeRepository(),
            users=users,
        )
    )
    app.dependency_overrides[get_list_api_keys_use_case] = lambda: ListApiKeysUseCase(
        keys=keys, users=users
    )
    app.dependency_overrides[get_create_api_key_use_case] = lambda: CreateApiKeyUseCase(
        keys=keys,
        users=users,
        audit_logs=audit,
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )
    app.dependency_overrides[get_revoke_api_key_use_case] = lambda: RevokeApiKeyUseCase(
        keys=keys,
        audit_logs=audit,
        notifications=NotificationDelivery(InMemoryNotificationRepository()),
    )


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    keys = InMemoryApiKeyRepository()
    wire(keys)
    app.dependency_overrides[get_current_user] = lambda: TEAMMATE
    app.dependency_overrides[get_current_manager] = lambda: MANAGER
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        yield http
    app.dependency_overrides.clear()


PAYLOAD = {
    "name": "CI waat-tools",
    "owner_id": 1,
    "scopes": ["catalog:read"],
}


class TestMinting:
    @pytest.mark.asyncio
    async def test_a_manager_mints_a_key(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/api-keys", json=PAYLOAD)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_the_response_carries_the_whole_token(
        self, client: AsyncClient
    ) -> None:
        body = (await client.post("/api/v1/api-keys", json=PAYLOAD)).json()
        assert body["token"].startswith("jns_")
        assert len(body["token"].split("_")) == 3

    @pytest.mark.asyncio
    async def test_the_listing_never_carries_it_again(
        self, client: AsyncClient
    ) -> None:
        # There is no « reveal » route because there is nothing left to reveal.
        token = (await client.post("/api/v1/api-keys", json=PAYLOAD)).json()["token"]

        listing = await client.get("/api/v1/api-keys")

        assert token not in listing.text
        assert listing.json()[0]["masked"].startswith("jns_")
        assert listing.json()[0]["masked"] not in token.split("_")[2]

    @pytest.mark.asyncio
    async def test_a_key_without_a_scope_is_refused(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/api-keys", json={**PAYLOAD, "scopes": []})
        assert response.status_code == 422


class TestListing:
    @pytest.mark.asyncio
    async def test_the_whole_team_reads_it(self, client: AsyncClient) -> None:
        # `get_current_user` alone: a teammate, not a manager.
        assert (await client.get("/api/v1/api-keys")).status_code == 200

    @pytest.mark.asyncio
    async def test_a_key_names_the_people_behind_it(self, client: AsyncClient) -> None:
        await client.post("/api/v1/api-keys", json=PAYLOAD)
        row = (await client.get("/api/v1/api-keys")).json()[0]

        assert row["owner"]["display_name"] == "A. Ba"
        assert row["created_by"]["display_name"] == "B. Cy"
        assert row["state"] == "active"


class TestRevoking:
    @pytest.mark.asyncio
    async def test_a_key_is_cut_and_stays_in_the_table(
        self, client: AsyncClient
    ) -> None:
        key_id = (await client.post("/api/v1/api-keys", json=PAYLOAD)).json()["key"][
            "id"
        ]

        assert (await client.delete(f"/api/v1/api-keys/{key_id}")).status_code == 204

        row = (await client.get("/api/v1/api-keys")).json()[0]
        assert row["state"] == "revoked"
        assert row["revoked_by"]["display_name"] == "B. Cy"

    @pytest.mark.asyncio
    async def test_an_unknown_key_is_not_found(self, client: AsyncClient) -> None:
        assert (await client.delete("/api/v1/api-keys/999")).status_code == 404


class TestAKeyOpensNothingByDefault:
    """The rule the whole design leans on."""

    @pytest.fixture
    async def unauthenticated(self) -> AsyncIterator[AsyncClient]:
        self.keys = InMemoryApiKeyRepository()
        wire(self.keys)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as http:
            yield http
        app.dependency_overrides.clear()

    async def a_key_for(self, scope: ApiKeyScope) -> str:
        public_id, secret, token = key_material.generate()
        await self.keys.add(
            ApiKey(
                id=None,
                name="CI waat-tools",
                public_id=public_id,
                secret_hash=key_material.hash_secret(secret),
                owner_id=1,
                created_by=2,
                scopes=[scope],
            )
        )
        return token

    @pytest.mark.asyncio
    async def test_the_catalogue_lets_a_key_carrying_the_scope_through(
        self, unauthenticated: AsyncClient
    ) -> None:
        token = await self.a_key_for(ApiKeyScope.CATALOG_READ)

        response = await unauthenticated.get(
            "/api/v1/projects/catalog",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_a_key_short_of_the_scope_is_told_so(
        self, unauthenticated: AsyncClient
    ) -> None:
        # 403 rather than 401: whoever holds a real key needs to know what to
        # ask for.
        token = await self.a_key_for(ApiKeyScope.ENTRIES_READ)

        response = await unauthenticated.get(
            "/api/v1/projects/catalog",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_a_key_is_turned_away_from_a_human_route(
        self, unauthenticated: AsyncClient
    ) -> None:
        _, _, token = key_material.generate()

        response = await unauthenticated.get(
            "/api/v1/api-keys", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_a_key_cannot_manage_keys(self, unauthenticated: AsyncClient) -> None:
        _, _, token = key_material.generate()

        response = await unauthenticated.post(
            "/api/v1/api-keys",
            json=PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_the_catalogue_refuses_a_call_with_no_key(
        self, unauthenticated: AsyncClient
    ) -> None:
        response = await unauthenticated.get("/api/v1/projects/catalog")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_the_catalogue_refuses_an_unknown_key(
        self, unauthenticated: AsyncClient
    ) -> None:
        _, _, token = key_material.generate()

        response = await unauthenticated.get(
            "/api/v1/projects/catalog",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_the_catalogue_says_401_whatever_the_reason(
        self, unauthenticated: AsyncClient
    ) -> None:
        # Malformed, unknown: one answer. Telling them apart would hand an
        # attacker a way to enumerate.
        for token in ("jns_broken", "jns_a_b", "not-ours"):
            response = await unauthenticated.get(
                "/api/v1/projects/catalog",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 401


def test_every_scope_names_a_colon_separated_resource() -> None:
    """The vocabulary grows by adding a member, never by a wildcard."""
    for scope in ApiKeyScope:
        resource, _, verb = scope.value.partition(":")
        assert resource and verb
        assert "*" not in scope.value


def test_a_key_entity_never_carries_its_secret() -> None:
    public_id, secret, _ = key_material.generate()
    key = ApiKey(
        id=1,
        name="CI",
        public_id=public_id,
        secret_hash=key_material.hash_secret(secret),
        owner_id=1,
        created_by=2,
        scopes=[ApiKeyScope.CATALOG_READ],
    )
    assert secret not in repr(key)


class TestHowOftenAKeyMayCall:
    """A limit turns a leaked key into a nuisance rather than an outage."""

    @pytest.fixture
    async def unauthenticated(self) -> AsyncIterator[AsyncClient]:
        self.keys = InMemoryApiKeyRepository()
        wire(self.keys)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as http:
            yield http
        app.dependency_overrides.clear()

    async def a_key(self) -> str:
        public_id, secret, token = key_material.generate()
        await self.keys.add(
            ApiKey(
                id=None,
                name="CI waat-tools",
                public_id=public_id,
                secret_hash=key_material.hash_secret(secret),
                owner_id=1,
                created_by=2,
                scopes=[ApiKeyScope.CATALOG_READ],
            )
        )
        return token

    async def call(self, http: AsyncClient, token: str):
        return await http.get(
            "/api/v1/projects/catalog",
            headers={"Authorization": f"Bearer {token}"},
        )

    @pytest.mark.asyncio
    async def test_the_allowance_goes_through(
        self, unauthenticated: AsyncClient
    ) -> None:
        token = await self.a_key()
        for _ in range(TEST_LIMIT.allowance):
            assert (await self.call(unauthenticated, token)).status_code == 200

    @pytest.mark.asyncio
    async def test_the_call_after_is_turned_away(
        self, unauthenticated: AsyncClient
    ) -> None:
        token = await self.a_key()
        for _ in range(TEST_LIMIT.allowance):
            await self.call(unauthenticated, token)

        assert (await self.call(unauthenticated, token)).status_code == 429

    @pytest.mark.asyncio
    async def test_every_answer_says_what_is_left(
        self, unauthenticated: AsyncClient
    ) -> None:
        # A caller should be able to slow down before being told to.
        token = await self.a_key()
        response = await self.call(unauthenticated, token)

        assert response.headers["x-ratelimit-limit"] == str(TEST_LIMIT.allowance)
        assert response.headers["x-ratelimit-remaining"] == str(
            TEST_LIMIT.allowance - 1
        )

    @pytest.mark.asyncio
    async def test_the_refusal_says_how_long_to_wait(
        self, unauthenticated: AsyncClient
    ) -> None:
        token = await self.a_key()
        for _ in range(TEST_LIMIT.allowance):
            await self.call(unauthenticated, token)

        refused = await self.call(unauthenticated, token)

        assert refused.headers["x-ratelimit-remaining"] == "0"
        assert int(refused.headers["retry-after"]) >= 1

    @pytest.mark.asyncio
    async def test_one_key_does_not_shut_the_door_on_another(
        self, unauthenticated: AsyncClient
    ) -> None:
        spent = await self.a_key()
        fresh = await self.a_key()
        for _ in range(TEST_LIMIT.allowance + 1):
            await self.call(unauthenticated, spent)

        assert (await self.call(unauthenticated, fresh)).status_code == 200

    @pytest.mark.asyncio
    async def test_a_key_turned_away_at_the_door_spends_nothing(
        self, unauthenticated: AsyncClient
    ) -> None:
        # The limit guards against a caller holding a real key. Turning away a
        # forged one costs a hash, and must not eat anyone's allowance.
        token = await self.a_key()
        _, _, forged = key_material.generate()
        for _ in range(20):
            await self.call(unauthenticated, forged)

        for _ in range(TEST_LIMIT.allowance):
            assert (await self.call(unauthenticated, token)).status_code == 200

"""Letting a machine in — and, far more often, not.

Unknown, malformed, expired, revoked, owner deactivated: all five come back as
nothing at all, and the caller answers 401 to every one. Telling them apart
would hand an attacker a way to enumerate. Only a valid key short of a scope
raises, because there the caller needs to know what to ask for.
"""

from datetime import datetime, timedelta

import pytest

from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    AuthenticateApiKeyUseCase,
)
from src.modules.api_keys.domain.entities.api_key import (
    USE_FRESHNESS,
    ApiKey,
    ApiKeyScope,
)
from src.modules.api_keys.domain.services import key_material
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import ForbiddenActionError
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import (
    InMemoryApiKeyRepository,
    InMemoryUserRepository,
)

OWNER = User(
    id=10,
    entra_oid="a",
    email="t.da@waat.fr",
    display_name="Toni DA RODDA",
    role=Role.TEAMMATE,
)


def build(
    scopes: list[ApiKeyScope] | None = None,
    owner: User = OWNER,
    team: list[User] | None = None,
    **overrides: object,
):
    public_id, secret, token = key_material.generate()
    fields: dict[str, object] = {
        "id": 1,
        "name": "CI waat-tools",
        "public_id": public_id,
        "secret_hash": key_material.hash_secret(secret),
        "owner_id": 10,
        "created_by": 20,
        "scopes": scopes or [ApiKeyScope.CATALOG_READ],
    }
    fields.update(overrides)
    key = ApiKey(**fields)  # type: ignore[arg-type]
    keys = InMemoryApiKeyRepository([key])
    # `team` stands apart from `owner`: an empty directory is how a key whose
    # owner was erased is reproduced.
    use_case = AuthenticateApiKeyUseCase(
        keys=keys,
        users=InMemoryUserRepository([owner] if team is None else team),
    )
    return use_case, token, key


CATALOG = ApiKeyScope.CATALOG_READ


@pytest.mark.asyncio
async def test_a_good_key_with_the_scope_gets_in() -> None:
    use_case, token, key = build()
    caller = await use_case.execute(token, CATALOG)

    assert caller is not None
    assert caller.key.id == key.id
    assert caller.owner.id == 10


@pytest.mark.asyncio
async def test_the_caller_answers_under_its_owner() -> None:
    # This is what the audit records: nothing in the use cases has to learn
    # about machines, and the trace still says who is accountable.
    use_case, token, _ = build()
    caller = await use_case.execute(token, CATALOG)
    assert caller is not None and caller.actor_id == 10


class TestTurnedAwayWithoutASayingWhy:
    @pytest.mark.asyncio
    async def test_a_token_that_is_not_ours(self) -> None:
        use_case, _, _ = build()
        assert await use_case.execute("ghp_something", CATALOG) is None

    @pytest.mark.asyncio
    async def test_a_malformed_token(self) -> None:
        use_case, _, _ = build()
        assert await use_case.execute("jns_only-two-parts", CATALOG) is None

    @pytest.mark.asyncio
    async def test_an_unknown_public_id(self) -> None:
        use_case, _, _ = build()
        _, _, other = key_material.generate()
        assert await use_case.execute(other, CATALOG) is None

    @pytest.mark.asyncio
    async def test_a_known_public_id_with_the_wrong_secret(self) -> None:
        use_case, token, _ = build()
        public_id, _ = key_material.parse(token)  # type: ignore[misc]
        forged = f"jns_{public_id}_{'z' * 43}"
        assert await use_case.execute(forged, CATALOG) is None

    @pytest.mark.asyncio
    async def test_an_expired_key(self) -> None:
        use_case, token, _ = build(
            created_at=clock.now() - timedelta(days=400),
            expires_at=clock.now() - timedelta(days=1),
        )
        assert await use_case.execute(token, CATALOG) is None

    @pytest.mark.asyncio
    async def test_a_revoked_key(self) -> None:
        use_case, token, key = build()
        key.revoke(by=20, at=clock.now())
        assert await use_case.execute(token, CATALOG) is None

    @pytest.mark.asyncio
    async def test_a_key_whose_owner_was_deactivated(self) -> None:
        # Deactivating someone cuts their machines with them: that is the
        # offboarding story.
        gone = User(
            id=10,
            entra_oid="a",
            email="t.da@waat.fr",
            display_name="Toni DA RODDA",
            is_active=False,
            role=Role.TEAMMATE,
        )
        use_case, token, _ = build(owner=gone)
        assert await use_case.execute(token, CATALOG) is None

    @pytest.mark.asyncio
    async def test_a_key_whose_owner_no_longer_exists(self) -> None:
        use_case, token, _ = build()
        use_case._users = InMemoryUserRepository([])
        assert await use_case.execute(token, CATALOG) is None


@pytest.mark.asyncio
async def test_a_valid_key_short_of_the_scope_says_so() -> None:
    use_case, token, _ = build(scopes=[ApiKeyScope.ENTRIES_READ])
    with pytest.raises(ForbiddenActionError):
        await use_case.execute(token, CATALOG)


class TestRecordingUse:
    @pytest.mark.asyncio
    async def test_a_first_call_stamps_the_key(self) -> None:
        use_case, token, key = build()
        await use_case.execute(token, CATALOG)
        assert key.last_used_at is not None

    @pytest.mark.asyncio
    async def test_a_second_call_inside_the_window_does_not_restamp(self) -> None:
        use_case, token, key = build()
        await use_case.execute(token, CATALOG)
        first = key.last_used_at
        await use_case.execute(token, CATALOG)
        assert key.last_used_at == first

    @pytest.mark.asyncio
    async def test_a_call_past_the_window_stamps_again(self) -> None:
        use_case, token, key = build(
            last_used_at=clock.now() - USE_FRESHNESS - timedelta(minutes=1)
        )
        stale = key.last_used_at
        await use_case.execute(token, CATALOG)
        assert key.last_used_at != stale

    @pytest.mark.asyncio
    async def test_a_refused_key_is_never_stamped(self) -> None:
        use_case, token, key = build(scopes=[ApiKeyScope.ENTRIES_READ])
        with pytest.raises(ForbiddenActionError):
            await use_case.execute(token, CATALOG)
        assert key.last_used_at is None


@pytest.mark.asyncio
async def test_stamping_a_call_does_not_rewrite_the_aggregate() -> None:
    """Authenticating is a read path that happens to leave a mark.

    It goes through `record_use`, not `update`: rewriting the scope rows on
    every call would be write amplification for one column.
    """
    written: list[str] = []

    class WatchfulRepository(InMemoryApiKeyRepository):
        async def update(self, key: ApiKey) -> None:
            written.append("update")
            await super().update(key)

        async def record_use(self, key_id: int, used_at: datetime) -> None:
            written.append("record_use")
            await super().record_use(key_id, used_at)

    public_id, secret, token = key_material.generate()
    key = ApiKey(
        id=1,
        name="CI",
        public_id=public_id,
        secret_hash=key_material.hash_secret(secret),
        owner_id=10,
        created_by=20,
        scopes=[CATALOG],
    )
    use_case = AuthenticateApiKeyUseCase(
        keys=WatchfulRepository([key]), users=InMemoryUserRepository([OWNER])
    )

    await use_case.execute(token, CATALOG)

    assert written == ["record_use"]


class TestIdentifyingWithoutAskingWhatFor:
    """The door of the MCP server reads the envelope, not the letter.

    Which scope is needed there depends on the tool being asked for, so the
    door identifies the key and the tool checks its own scope. What must not
    change is which keys are turned away: the same five, for the same reasons.
    """

    @pytest.mark.asyncio
    async def test_a_good_key_is_identified_whatever_it_carries(self) -> None:
        use_case, token, key = build(scopes=[ApiKeyScope.ENTRIES_READ])
        caller = await use_case.identify(token)

        assert caller is not None
        assert caller.key.id == key.id
        assert caller.owner.id == 10

    @pytest.mark.asyncio
    async def test_a_revoked_key_is_turned_away_all_the_same(self) -> None:
        use_case, token, _ = build(revoked_at=datetime.now(), revoked_by=20)
        assert await use_case.identify(token) is None

    @pytest.mark.asyncio
    async def test_a_key_whose_owner_left_is_turned_away(self) -> None:
        use_case, token, _ = build(team=[])
        assert await use_case.identify(token) is None

    @pytest.mark.asyncio
    async def test_identifying_stamps_the_call(self) -> None:
        use_case, token, key = build()
        await use_case.identify(token)
        assert key.last_used_at is not None

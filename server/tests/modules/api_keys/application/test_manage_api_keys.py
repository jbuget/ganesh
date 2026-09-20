"""Minting, listing and cutting service accounts."""

from datetime import timedelta

import pytest

from src.modules.api_keys.application.dtos.api_key_dto import (
    CreateApiKeyCommand,
    RevokeApiKeyCommand,
    UpdateApiKeyCommand,
)
from src.modules.api_keys.application.use_cases.manage_api_keys import (
    CreateApiKeyUseCase,
    ListApiKeysUseCase,
    RevokeApiKeyUseCase,
    UpdateApiKeyUseCase,
)
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.domain.services import key_material
from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
    ValidationError,
)
from src.shared.utils import clock
from tests.helpers.in_memory_repositories import (
    InMemoryApiKeyRepository,
    InMemoryAuditLogRepository,
    InMemoryNotificationRepository,
    InMemoryUserRepository,
)

OWNER = User(id=10, entra_oid="a", email="t.da@waat.fr", display_name="Toni DA RODDA")
MANAGER = User(
    id=20,
    entra_oid="b",
    email="j.buget@waat.fr",
    display_name="Jérémy BUGET",
    role=Role.MANAGER,
)
GONE = User(
    id=30,
    entra_oid="c",
    email="x@waat.fr",
    display_name="Ancien",
    is_active=False,
)


def build():
    keys = InMemoryApiKeyRepository()
    audit = InMemoryAuditLogRepository()
    users = InMemoryUserRepository([OWNER, MANAGER, GONE])
    inbox = InMemoryNotificationRepository()
    delivery = NotificationDelivery(inbox)
    return (
        CreateApiKeyUseCase(
            keys=keys, users=users, audit_logs=audit, notifications=delivery
        ),
        ListApiKeysUseCase(keys=keys, users=users),
        RevokeApiKeyUseCase(keys=keys, audit_logs=audit, notifications=delivery),
        keys,
        audit,
        inbox,
    )


def command(**overrides: object) -> CreateApiKeyCommand:
    fields: dict[str, object] = {
        "actor_id": 20,
        "name": "CI waat-tools",
        "owner_id": 10,
        "scopes": [ApiKeyScope.CATALOG_READ],
    }
    fields.update(overrides)
    return CreateApiKeyCommand(**fields)  # type: ignore[arg-type]


class TestMinting:
    @pytest.mark.asyncio
    async def test_a_key_is_created_and_the_token_handed_over(self) -> None:
        create, *_ = build()
        minted = await create.execute(command())

        assert minted.key.id is not None
        assert minted.token.startswith("jns_")

    @pytest.mark.asyncio
    async def test_the_secret_is_never_stored(self) -> None:
        create, _, _, keys, _, _ = build()
        minted = await create.execute(command())

        stored = await keys.get_by_id(minted.key.id or 0)
        assert stored is not None
        assert minted.token not in stored.secret_hash
        assert key_material.parse(minted.token) is not None
        _, secret = key_material.parse(minted.token)  # type: ignore[misc]
        assert secret not in stored.secret_hash
        assert key_material.matches(secret, stored.secret_hash)

    @pytest.mark.asyncio
    async def test_the_owner_answers_for_it_and_a_manager_minted_it(self) -> None:
        create, *_ = build()
        minted = await create.execute(command())

        assert minted.key.owner_id == 10
        assert minted.key.created_by == 20

    @pytest.mark.asyncio
    async def test_an_unknown_owner_is_refused(self) -> None:
        create, *_ = build()
        with pytest.raises(EntityNotFoundError):
            await create.execute(command(owner_id=999))

    @pytest.mark.asyncio
    async def test_a_deactivated_owner_is_refused(self) -> None:
        # A key is only as alive as the person answering for it: this one
        # would be dead on arrival.
        create, *_ = build()
        with pytest.raises(ValidationError):
            await create.execute(command(owner_id=30))

    @pytest.mark.asyncio
    async def test_minting_is_traced_without_the_secret(self) -> None:
        create, _, _, _, audit, _ = build()
        minted = await create.execute(command())

        trace = audit.logs[0]
        assert trace.action.value == "api_key.create"
        assert trace.actor_id == 20
        assert trace.target_user_id == 10
        assert trace.new_value == key_material.masked(minted.key.public_id)
        assert minted.token not in str(trace.payload)


class TestListing:
    @pytest.mark.asyncio
    async def test_it_names_the_people_behind_the_keys(self) -> None:
        create, listing, *_ = build()
        await create.execute(command())

        read = await listing.execute()
        assert [key.name for key in read.keys] == ["CI waat-tools"]
        assert read.people[10].display_name == "Toni DA RODDA"

    @pytest.mark.asyncio
    async def test_a_deactivated_owner_is_still_named(self) -> None:
        # Hiding the line would hide the key, and a key nobody sees is a key
        # nobody revokes.
        _, listing, *_ = build()
        assert 30 in (await listing.execute()).people


class TestRevoking:
    @pytest.mark.asyncio
    async def test_a_key_is_cut(self) -> None:
        create, _, revoke, *_ = build()
        minted = await create.execute(command())

        cut = await revoke.execute(
            RevokeApiKeyCommand(actor_id=20, key_id=minted.key.id or 0)
        )
        assert cut.is_revoked is True
        assert cut.revoked_by == 20

    @pytest.mark.asyncio
    async def test_the_row_stays_so_the_audit_keeps_reading(self) -> None:
        create, listing, revoke, *_ = build()
        minted = await create.execute(command())
        await revoke.execute(
            RevokeApiKeyCommand(actor_id=20, key_id=minted.key.id or 0)
        )

        assert len((await listing.execute()).keys) == 1

    @pytest.mark.asyncio
    async def test_cutting_twice_is_refused(self) -> None:
        create, _, revoke, *_ = build()
        minted = await create.execute(command())
        cut = RevokeApiKeyCommand(actor_id=20, key_id=minted.key.id or 0)
        await revoke.execute(cut)

        with pytest.raises(ForbiddenActionError):
            await revoke.execute(cut)

    @pytest.mark.asyncio
    async def test_an_unknown_key_is_refused(self) -> None:
        _, _, revoke, _, _, _ = build()
        with pytest.raises(EntityNotFoundError):
            await revoke.execute(RevokeApiKeyCommand(actor_id=20, key_id=999))

    @pytest.mark.asyncio
    async def test_cutting_is_traced(self) -> None:
        create, _, revoke, _, audit, _ = build()
        minted = await create.execute(command())
        await revoke.execute(
            RevokeApiKeyCommand(actor_id=20, key_id=minted.key.id or 0)
        )

        assert [log.action.value for log in audit.logs] == [
            "api_key.create",
            "api_key.revoke",
        ]


@pytest.mark.asyncio
async def test_an_expiry_travels_to_the_key() -> None:
    create, *_ = build()
    expiry = clock.now() + timedelta(days=365)
    minted = await create.execute(command(expires_at=expiry))
    assert minted.key.expires_at == expiry


class TestEditing:
    """Only what a mistake at creation leaves wrong: the name and the scopes."""

    def use_cases(self):
        keys = InMemoryApiKeyRepository()
        audit = InMemoryAuditLogRepository()
        users = InMemoryUserRepository([OWNER, MANAGER, GONE])
        return (
            CreateApiKeyUseCase(
                keys=keys,
                users=users,
                audit_logs=audit,
                notifications=NotificationDelivery(InMemoryNotificationRepository()),
            ),
            UpdateApiKeyUseCase(keys=keys, users=users, audit_logs=audit),
            RevokeApiKeyUseCase(
                keys=keys,
                audit_logs=audit,
                notifications=NotificationDelivery(InMemoryNotificationRepository()),
            ),
            audit,
        )

    @pytest.mark.asyncio
    async def test_a_key_is_renamed(self) -> None:
        create, update, _, _ = self.use_cases()
        minted = await create.execute(command())

        changed = await update.execute(
            UpdateApiKeyCommand(
                actor_id=20, key_id=minted.key.id or 0, name="CI waat.tools"
            )
        )
        assert changed.key.name == "CI waat.tools"

    @pytest.mark.asyncio
    async def test_the_scopes_are_replaced(self) -> None:
        create, update, _, _ = self.use_cases()
        minted = await create.execute(command())

        changed = await update.execute(
            UpdateApiKeyCommand(
                actor_id=20,
                key_id=minted.key.id or 0,
                scopes=[ApiKeyScope.ALL_READ],
            )
        )
        assert changed.key.scopes == [ApiKeyScope.ALL_READ]

    @pytest.mark.asyncio
    async def test_a_field_left_out_is_a_field_left_alone(self) -> None:
        create, update, _, _ = self.use_cases()
        minted = await create.execute(command())

        changed = await update.execute(
            UpdateApiKeyCommand(actor_id=20, key_id=minted.key.id or 0, name="Autre")
        )
        assert changed.key.scopes == [ApiKeyScope.CATALOG_READ]

    @pytest.mark.asyncio
    async def test_the_secret_is_never_reissued(self) -> None:
        create, update, _, _ = self.use_cases()
        minted = await create.execute(command())
        before = minted.key.secret_hash

        changed = await update.execute(
            UpdateApiKeyCommand(actor_id=20, key_id=minted.key.id or 0, name="Autre")
        )
        assert changed.key.secret_hash == before
        assert changed.key.public_id == minted.key.public_id

    @pytest.mark.asyncio
    async def test_each_field_that_changed_leaves_one_trace(self) -> None:
        create, update, _, audit = self.use_cases()
        minted = await create.execute(command())
        audit.logs.clear()

        await update.execute(
            UpdateApiKeyCommand(
                actor_id=20,
                key_id=minted.key.id or 0,
                name="Autre",
                scopes=[ApiKeyScope.ALL_READ],
            )
        )
        assert sorted(log.payload["field"] for log in audit.logs) == ["name", "scopes"]

    @pytest.mark.asyncio
    async def test_changing_nothing_leaves_no_trace(self) -> None:
        create, update, _, audit = self.use_cases()
        minted = await create.execute(command())
        audit.logs.clear()

        await update.execute(
            UpdateApiKeyCommand(
                actor_id=20,
                key_id=minted.key.id or 0,
                name="CI waat-tools",
                scopes=[ApiKeyScope.CATALOG_READ],
            )
        )
        assert audit.logs == []

    @pytest.mark.asyncio
    async def test_a_revoked_key_is_frozen(self) -> None:
        create, update, revoke, _ = self.use_cases()
        minted = await create.execute(command())
        await revoke.execute(
            RevokeApiKeyCommand(actor_id=20, key_id=minted.key.id or 0)
        )

        with pytest.raises(ForbiddenActionError):
            await update.execute(
                UpdateApiKeyCommand(
                    actor_id=20, key_id=minted.key.id or 0, name="Autre"
                )
            )

    @pytest.mark.asyncio
    async def test_an_unknown_key_is_refused(self) -> None:
        _, update, _, _ = self.use_cases()
        with pytest.raises(EntityNotFoundError):
            await update.execute(
                UpdateApiKeyCommand(actor_id=20, key_id=999, name="Autre")
            )


async def test_the_owner_hears_a_key_minted_in_their_name() -> None:
    """A key answers to its owner, whoever minted it."""
    create, _, _, _, _, inbox = build()

    await create.execute(command())

    [told] = inbox.notifications
    assert told.recipient_id == 10
    assert told.kind is NotificationKind.API_KEY_CREATED
    assert told.payload == {"key_label": "CI waat-tools"}


async def test_the_owner_hears_their_key_revoked() -> None:
    create, _, revoke, _, _, inbox = build()
    minted = await create.execute(command())

    await revoke.execute(RevokeApiKeyCommand(actor_id=20, key_id=minted.key.id or 0))

    assert [told.kind for told in inbox.notifications] == [
        NotificationKind.API_KEY_CREATED,
        NotificationKind.API_KEY_REVOKED,
    ]


async def test_minting_a_key_for_oneself_rings_nowhere() -> None:
    create, _, _, _, _, inbox = build()

    await create.execute(command(actor_id=10))

    assert inbox.notifications == []

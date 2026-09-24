"""« J'ai passé la journée sur Ganesh. »

The one tool that writes, and the one with the most to break. Three properties
this file exists for:

- **it writes for the owner of the key and nobody else.** There is no
  `user_id` to get wrong, which is the guarantee rather than an omission;
- **every refusal comes back as a sentence.** A validated month, a weekend, a
  value that is not a half or a whole day: rules a person argues with on
  screen, and a machine would only ever be told « 422 »;
- **what is written is read back.** The answer says what the day now holds,
  so that nobody has to trust that it landed.
"""

import pytest
from fastapi import FastAPI

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.declaring import declare_time
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.entries.application.dtos.set_entry_dto import SetEntryCommand
from src.modules.entries.domain.entities.entry import Entry
from src.modules.entries.presentation.dependencies import get_set_entry_use_case
from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
)

OWNER = User(
    id=7, entra_oid="oid-7", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)


class Writer:
    """Stands in for `SetEntryUseCase`, and remembers what it was asked."""

    def __init__(self, answer: object | None = None) -> None:
        self.asked: SetEntryCommand | None = None
        self._answer = answer

    async def execute(self, command: SetEntryCommand) -> object:
        self.asked = command
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer or Entry(
            id=1,
            user_id=command.target_user_id,
            project_id=command.project_id,
            day=command.day,
            value=command.value,
            status_at_entry=ProjectStatus.DEVELOPMENT,
        )


class Wired:
    def __init__(self, writer: Writer, scope: ApiKeyScope | None = None) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_set_entry_use_case] = lambda: writer
        self.committed = 0
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=7,
            created_by=1,
            scopes=[scope or ApiKeyScope.ENTRIES_WRITE],
        )
        self._standing = standing(
            Machine(
                caller=MachineCaller(key=key, owner=OWNER),
                wiring=Wiring(
                    session=_Session(self),  # type: ignore[arg-type]
                    overrides=self.app.dependency_overrides,
                ),
            )
        )

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)
        self.app.dependency_overrides.clear()


class _Session:
    """Counts commits: a write nobody commits is a write nobody keeps."""

    def __init__(self, wired: Wired) -> None:
        self._wired = wired

    async def commit(self) -> None:
        self._wired.committed += 1


class TestItWritesForWhoeverHoldsTheKey:
    @pytest.mark.asyncio
    async def test_the_target_is_the_owner_of_the_key(self) -> None:
        writer = Writer()
        with Wired(writer):
            await declare_time(project_id=3, day="2026-09-21", value=1)

        assert writer.asked is not None
        assert writer.asked.target_user_id == OWNER.id
        assert writer.asked.actor_id == OWNER.id

    @pytest.mark.asyncio
    async def test_what_was_written_is_read_back(self) -> None:
        with Wired(Writer()) as wired:
            said = await declare_time(project_id=3, day="2026-09-21", value=0.5)

        assert "0,5 jour" in said
        assert "21/09/2026" in said
        assert wired.committed == 1

    @pytest.mark.asyncio
    async def test_a_key_short_of_the_scope_writes_nothing(self) -> None:
        """Reading everything does not grant writing anything."""
        writer = Writer()
        with (
            Wired(writer, ApiKeyScope.ALL_READ),
            pytest.raises(ToolError, match="entries:write"),
        ):
            await declare_time(project_id=3, day="2026-09-21", value=1)

        assert writer.asked is None


class TestEveryRefusalIsASentence:
    @pytest.mark.asyncio
    async def test_a_validated_month_says_what_it_takes_to_reopen_it(self) -> None:
        refusal = ForbiddenActionError("The month is validated.")
        with (
            Wired(Writer(refusal)) as wired,
            pytest.raises(ToolError) as raised,
        ):
            await declare_time(project_id=3, day="2026-09-21", value=1)

        assert "validé" in str(raised.value)
        assert wired.committed == 0

    @pytest.mark.asyncio
    async def test_a_weekend_is_named_and_nothing_is_written(self) -> None:
        """20/09/2026 is a Sunday. Said in French, before the domain is asked."""
        writer = Writer()
        with Wired(writer), pytest.raises(ToolError) as raised:
            await declare_time(project_id=3, day="2026-09-20", value=1)

        assert "week-end" in str(raised.value)
        assert "20/09/2026" in str(raised.value)
        assert writer.asked is None

    @pytest.mark.asyncio
    async def test_a_public_holiday_is_named_too(self) -> None:
        """14/07/2026 is the fourteenth of July."""
        with Wired(Writer()), pytest.raises(ToolError) as raised:
            await declare_time(project_id=3, day="2026-07-14", value=1)

        assert "férié" in str(raised.value)

    @pytest.mark.asyncio
    async def test_a_day_that_does_not_read_is_refused_before_anything_is_written(
        self,
    ) -> None:
        writer = Writer()
        with Wired(writer), pytest.raises(ToolError) as raised:
            await declare_time(project_id=3, day="hier", value=1)

        assert "AAAA-MM-JJ" in str(raised.value)
        assert writer.asked is None

    @pytest.mark.asyncio
    async def test_a_value_the_grid_does_not_hold_is_refused_in_words(self) -> None:
        """Half a day or a whole one. The refusal says so rather than « 422 »."""
        writer = Writer()
        with Wired(writer), pytest.raises(ToolError) as raised:
            await declare_time(project_id=3, day="2026-09-21", value=0.75)

        assert "0,5" in str(raised.value)
        # Quoted as it was written: a refusal that rounds tells the caller
        # they wrote something they did not.
        assert "0,75" in str(raised.value)
        assert writer.asked is None

    @pytest.mark.asyncio
    async def test_a_refusal_is_raised_rather_than_answered(self) -> None:
        """A write that did not happen must not read like one that did.

        Raising is what carries `isError` to the client; a sentence returned
        in the shape of an answer is taken for one.
        """
        with Wired(Writer()), pytest.raises(ToolError):
            await declare_time(project_id=3, day="2026-09-20", value=1)

    @pytest.mark.asyncio
    async def test_a_project_nobody_can_find_is_said_in_french(self) -> None:
        missing = EntityNotFoundError("The mission cannot be found.")
        with Wired(Writer(missing)), pytest.raises(ToolError) as raised:
            await declare_time(project_id=404, day="2026-09-21", value=1)

        assert "404" in str(raised.value)
        assert "find_project" in str(raised.value)

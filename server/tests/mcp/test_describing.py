"""Rewriting the sheet of a project from a terminal.

The description is **replaced**, not appended to: a model that wants to add a
paragraph reads the sheet first and writes the whole of it back. Three
properties this file exists for:

- **a refusal is raised, never returned** — a write that did not happen must
  not read like one that did;
- **a blank text is refused**, since clearing a sheet by accident is what a
  model recopying nothing would do;
- **the write is committed**, and said back with what it now holds.
"""

import pytest
from fastapi import FastAPI

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.describing import update_project_description
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.projects.application.use_cases.update_project_detail import (
    UpdateDescriptionCommand,
)
from src.modules.projects.presentation.dependencies import (
    get_update_description_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

OWNER = User(
    id=7, entra_oid="oid-7", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)


class Writer:
    """Stands in for `UpdateDescriptionUseCase`, and remembers what it was asked."""

    def __init__(self, refusal: Exception | None = None) -> None:
        self.asked: UpdateDescriptionCommand | None = None
        self._refusal = refusal

    async def execute(self, command: UpdateDescriptionCommand) -> None:
        self.asked = command
        if self._refusal is not None:
            raise self._refusal


class _Session:
    def __init__(self, wired: "Wired") -> None:
        self._wired = wired

    async def commit(self) -> None:
        self._wired.committed += 1


class Wired:
    def __init__(self, writer: Writer, scope: ApiKeyScope | None = None) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_update_description_use_case] = lambda: writer
        self.committed = 0
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=7,
            created_by=1,
            scopes=[scope or ApiKeyScope.PROJECTS_WRITE],
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


class TestTheSheetIsReplaced:
    @pytest.mark.asyncio
    async def test_the_text_goes_to_the_project_in_the_name_of_the_key_owner(
        self,
    ) -> None:
        writer = Writer()
        with Wired(writer):
            await update_project_description(project_id=3, description="# Nomad")

        assert writer.asked == UpdateDescriptionCommand(
            actor_id=OWNER.id, project_id=3, description="# Nomad"  # type: ignore[arg-type]
        )

    @pytest.mark.asyncio
    async def test_the_write_is_committed(self) -> None:
        with Wired(Writer()) as wired:
            await update_project_description(project_id=3, description="# Nomad")

        assert wired.committed == 1

    @pytest.mark.asyncio
    async def test_it_says_what_the_sheet_now_holds(self) -> None:
        with Wired(Writer()):
            said = await update_project_description(
                project_id=3, description="Une application."
            )

        assert "#3" in said
        assert "remplacée" in said
        assert "16 caractères" in said


class TestWhatItRefuses:
    @pytest.mark.asyncio
    async def test_a_blank_text_is_refused_rather_than_clearing_the_sheet(
        self,
    ) -> None:
        writer = Writer()
        with Wired(writer), pytest.raises(ToolError):
            await update_project_description(project_id=3, description="  \n ")

        assert writer.asked is None

    @pytest.mark.asyncio
    async def test_a_project_nobody_can_find_says_where_to_look(self) -> None:
        with (
            Wired(Writer(EntityNotFoundError("The mission cannot be found."))),
            pytest.raises(ToolError) as refused,
        ):
            await update_project_description(project_id=404, description="x")

        assert "404" in str(refused.value)
        assert "find_project" in str(refused.value)

    @pytest.mark.asyncio
    async def test_a_key_that_only_reads_is_turned_away(self) -> None:
        writer = Writer()
        with Wired(writer, scope=ApiKeyScope.PROJECTS_READ), pytest.raises(ToolError):
            await update_project_description(project_id=3, description="x")

        assert writer.asked is None

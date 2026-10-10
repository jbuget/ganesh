"""The tools, read on behalf of somebody asking the assistant.

The assistant's model consults the tools a terminal client reaches, in the
API's own process, for the person signed in. Which tools it gets, and what a
refusal becomes, is decided here.
"""

import inspect
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.assistant.shelf import SHELF, PersonCaller, Shelf
from src.mcp.server import TOOLS
from src.mcp.tools.declaring import declare_time
from src.mcp.tools.mood import team_mood
from src.mcp.tools.plan import person_plan
from src.mcp.tools.reviewing import record_review
from src.mcp.wiring import Provider
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.presentation.dependencies import (
    get_list_projects_use_case,
    get_project_detail_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import ConflictError, EntityNotFoundError

SYLVAIN = User(
    id=4, entra_oid="oid-4", email="s@waat.fr", display_name="S. P", role=Role.MANAGER
)

WAATCHER = Project(id=7, label="WAATcher", kind=ProjectKind.PROJECT)


class Stub:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> object:
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer


class Sessions:
    """Hands out sessions and remembers which are still open."""

    def __init__(self) -> None:
        self.opened: list[object] = []
        self.open_now = 0

    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[object]:
        session = object()
        self.opened.append(session)
        self.open_now += 1
        try:
            yield session
        finally:
            self.open_now -= 1


def a_shelf(
    overrides: dict[Provider, Provider] | None = None,
    sessions: Sessions | None = None,
) -> Shelf:
    return Shelf(SYLVAIN, overrides or {}, sessions=sessions or Sessions())  # type: ignore[arg-type]


def a_listing(project: Project) -> ListedProject:
    return ListedProject(project=project, entries=0, sub_projects=0)


class TestWhatIsOnTheShelf:
    def test_the_model_reads_projects_and_what_moved_on_them(self) -> None:
        assert [tool.__name__ for tool in SHELF] == [
            "find_project",
            "project_brief",
            "project_news",
            "what_changed",
            "portfolio_status",
            "person_plan",
        ]

    def test_every_argument_is_one_the_shelf_knows_how_to_check(self) -> None:
        """A tool taking a float would see every call refused, and nobody told."""
        checked = {int, str, int | None, str | None}
        for tool in SHELF:
            for parameter in inspect.signature(tool).parameters.values():
                assert parameter.annotation in checked, (tool.__name__, parameter)

    def test_nothing_that_writes_is_on_it(self) -> None:
        """A model that misread a question must not be able to act on it."""
        assert declare_time not in SHELF
        assert record_review not in SHELF

    def test_a_person_s_plan_is_read_by_the_assistant_and_by_no_key(self) -> None:
        """The projection is an arbitration: `roadmap:read` leaves it shut."""
        assert person_plan in SHELF
        assert person_plan not in TOOLS

    def test_the_moods_are_not_on_it(self) -> None:
        """Given in confidence to a screen, never to a chat."""
        assert team_mood not in SHELF


class TestPersonCaller:
    def test_a_person_is_granted_what_reads(self) -> None:
        assert PersonCaller(SYLVAIN).grants(ApiKeyScope.PROJECTS_READ)

    def test_a_person_is_granted_nothing_that_writes(self) -> None:
        assert not PersonCaller(SYLVAIN).grants(ApiKeyScope.ENTRIES_WRITE)

    def test_a_person_is_never_granted_the_moods(self) -> None:
        assert not PersonCaller(SYLVAIN).grants(ApiKeyScope.MOODS_READ)

    def test_a_person_who_may_write_may_read(self) -> None:
        assert PersonCaller(SYLVAIN).may(ApiKeyScope.PROJECTS_READ)

    def test_the_tools_answer_for_the_person_asking(self) -> None:
        assert PersonCaller(SYLVAIN).actor_id == 4


class TestConsulting:
    async def test_a_tool_is_read_for_the_person_asking(self) -> None:
        shelf = a_shelf(
            {get_list_projects_use_case: lambda: Stub([a_listing(WAATCHER)])}
        )

        reading = await shelf.consult("find_project", {"query": "waat"})

        assert reading.tool == "find_project"
        assert reading.arguments == {"query": "waat"}
        assert "WAATcher (#7)" in reading.result

    async def test_a_tool_that_is_not_on_the_shelf_is_said_not_to_exist(
        self,
    ) -> None:
        reading = await a_shelf().consult("declare_time", {"day": "2026-10-10"})

        assert "declare_time" in reading.result
        assert "n'existe pas" in reading.result

    async def test_arguments_a_tool_does_not_take_are_said_rather_than_raised(
        self,
    ) -> None:
        reading = await a_shelf().consult("project_brief", {"name": "WAATcher"})

        assert reading.result == (
            "« project_brief » ne prend pas ces paramètres : name=« WAATcher »."
        )

    async def test_an_argument_of_the_wrong_type_is_said_rather_than_raised(
        self,
    ) -> None:
        """« 7 » as text reaches no repository: the model is told, and corrects."""
        reading = await a_shelf().consult("project_brief", {"project_id": "7"})

        assert reading.result == (
            "« project_brief » ne prend pas ces paramètres : project_id=« 7 »."
        )

    async def test_each_reading_has_a_session_of_its_own_closed_after_it(
        self,
    ) -> None:
        """No transaction is held open while the model thinks between two reads."""
        sessions = Sessions()
        shelf = a_shelf(
            {get_list_projects_use_case: lambda: Stub([a_listing(WAATCHER)])},
            sessions,
        )

        await shelf.consult("find_project", {"query": "waat"})
        await shelf.consult("find_project", {"query": "waat"})

        assert len(sessions.opened) == 2
        assert sessions.opened[0] is not sessions.opened[1]
        assert sessions.open_now == 0

    async def test_a_refusal_is_read_back_to_the_model(self) -> None:
        shelf = a_shelf(
            {get_list_projects_use_case: lambda: Stub(ConflictError("Refusé."))}
        )

        reading = await shelf.consult("find_project", {"query": "waat"})

        assert reading.result == "Refusé."

    async def test_an_identifier_written_as_a_whole_float_is_read_as_an_integer(
        self,
    ) -> None:
        """JSON knows numbers, not integers: « 7.0 » is still project 7."""
        shelf = a_shelf(
            {get_project_detail_use_case: lambda: Stub(EntityNotFoundError("…"))}
        )

        reading = await shelf.consult("project_brief", {"project_id": 7.0})

        assert reading.arguments == {"project_id": 7}
        assert reading.result.startswith("Aucun projet ne porte l'identifiant 7.")

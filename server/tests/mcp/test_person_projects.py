"""« Sur quoi est Léa, et à quel titre ? »

`find_project` can already narrow the list to a person; it cannot say what
they are there. This reads the same list from the other side, title by title:
whoever answers for the choices, whom to call when it breaks, who has their
hands in it now.

- **a title is said, never ranked** — a role is what somebody is asked for;
- **what is absent is said** — somebody on no project is absent from this
  reading, which is not the same as unknown to the company;
- **no pronoun** — Ganesh does not know who says « il ».
"""

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.staffing import person_projects
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.presentation.dependencies import get_list_projects_use_case
from src.modules.users.domain.entities.user import Role, User


def a_user(user_id: int, name: str) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"{user_id}@waat.fr",
        display_name=name,
        role=Role.TEAMMATE,
    )


OWNER = a_user(9, "A. Ba")
LEA = a_user(1, "Léa Chen")
LEA_B = a_user(3, "Léa Brun")


def listed(
    project_id: int,
    label: str,
    leads: list[User] | None = None,
    tech_leads: list[User] | None = None,
    contributors: list[User] | None = None,
    is_active: bool = True,
) -> ListedProject:
    return ListedProject(
        project=Project(
            id=project_id, label=label, kind=ProjectKind.PROJECT, is_active=is_active
        ),
        entries=0,
        sub_projects=0,
        leads=leads or [],
        tech_leads=tech_leads or [],
        contributors=contributors or [],
    )


class Stub:
    def __init__(self, answer: list[ListedProject]) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> list[ListedProject]:
        return self._answer


class Wired:
    def __init__(self, projects: list[ListedProject]) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_list_projects_use_case] = lambda: Stub(
            projects
        )
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=9,
            created_by=1,
            scopes=[ApiKeyScope.PROJECTS_READ],
        )
        self._standing = standing(
            Machine(
                caller=MachineCaller(key=key, owner=OWNER),
                wiring=Wiring(session=None, overrides=self.app.dependency_overrides),  # type: ignore[arg-type]
            )
        )

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)
        self.app.dependency_overrides.clear()


class TestItSaysAtWhichTitle:
    @pytest.mark.asyncio
    async def test_each_title_is_read_on_its_own_line(self) -> None:
        projects = [
            listed(1, "WAATcher", leads=[LEA]),
            listed(2, "Nomad", tech_leads=[LEA], contributors=[LEA]),
        ]
        with Wired(projects):
            said = await person_projects("Léa Chen")

        assert said == (
            "Léa Chen :\n"
            "- Référent projet : WAATcher (#1)\n"
            "- Référent technique : Nomad (#2)\n"
            "- Intervenant actuel : Nomad (#2)"
        )

    @pytest.mark.asyncio
    async def test_a_title_nobody_gave_them_is_left_out(self) -> None:
        with Wired([listed(1, "WAATcher", contributors=[LEA])]):
            said = await person_projects("chen")

        assert "Référent" not in said

    @pytest.mark.asyncio
    async def test_an_archived_project_says_so(self) -> None:
        with Wired([listed(3, "Vieux portail", tech_leads=[LEA], is_active=False)]):
            said = await person_projects("chen")

        assert "Vieux portail (#3, archivé)" in said


class TestWhoItReads:
    @pytest.mark.asyncio
    async def test_several_people_matching_are_each_read(self) -> None:
        projects = [
            listed(1, "WAATcher", leads=[LEA]),
            listed(4, "Intranet", leads=[LEA_B]),
        ]
        with Wired(projects):
            said = await person_projects("léa")

        assert "Léa Brun :" in said
        assert "Léa Chen :" in said
        assert "plusieurs" in said.lower()

    @pytest.mark.asyncio
    async def test_nobody_matching_is_said_without_calling_them_unknown(self) -> None:
        with Wired([listed(1, "WAATcher", leads=[LEA])]):
            said = await person_projects("Zoé")

        assert "Personne" in said
        assert "Zoé" in said
        assert "inconnu" not in said

    @pytest.mark.asyncio
    async def test_a_blank_name_asks_who(self) -> None:
        with Wired([]):
            said = await person_projects("  ")

        assert "Aucun nom" in said

"""« Où en est ce projet, au juste ? »

`find_project` hands over a name and an identifier; `what_changed` hands over
a window. Neither answers the question somebody actually opens a project for,
and this file holds the three properties that answer it:

- **the sheet is read as a sentence.** « 128 jours déclarés pour 150 estimés »,
  never a field called `consumed_days`;
- **what is unknown is said.** No estimate, no announced date, nobody assigned:
  each is a fact about the mission, and silence is where a model invents one;
- **who carried it is named, never ranked.** The screen orders contributions by
  days; a model handed that order writes a sentence about who did the least.
"""

from datetime import date, datetime

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.brief import project_brief
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.projects.application.use_cases.get_project_detail import (
    Contribution,
    ProjectDetail,
)
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.presentation.dependencies import get_project_detail_use_case
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

ANNE = User(
    id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)
MARIE = User(
    id=2, entra_oid="oid-2", email="m@waat.fr", display_name="M. Ce", role=Role.TEAMMATE
)

WAATCHER = Project(
    id=7,
    label="WAATcher",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.DEVELOPMENT,
    estimated_days=150,
)
SUPERVISION = Project(
    id=8,
    label="WAATcher — Supervision",
    kind=ProjectKind.WORK_PACKAGE,
    status=ProjectStatus.OPERATIONS,
    parent_id=7,
)
IMPORT = Project(
    id=9,
    label="WAATcher — Import",
    kind=ProjectKind.WORK_PACKAGE,
    status=ProjectStatus.SCOPING,
    parent_id=7,
)


def a_detail(project: Project, **fields: object) -> ProjectDetail:
    """The sheet as the screen reads one, with only what a test says filled in."""
    return ProjectDetail(
        project=project,
        departments=[],
        links=[],
        phases_reached=fields.get("phases_reached", {}),  # type: ignore[arg-type]
        leads=fields.get("leads", []),  # type: ignore[arg-type]
        contributors=fields.get("contributors", []),  # type: ignore[arg-type]
        consumed_days=fields.get("consumed_days", 0.0),  # type: ignore[arg-type]
        contributions=fields.get("contributions", []),  # type: ignore[arg-type]
        sub_projects=fields.get("sub_projects", []),  # type: ignore[arg-type]
        stack=[],
        tags=[],
        dependencies=[],
        is_deletable=False,
        parent=fields.get("parent"),  # type: ignore[arg-type]
    )


def declared_by(*people: User) -> list[Contribution]:
    """Contributions in the order the screen hands them over: largest first."""
    return [
        Contribution(user=person, days=float(10 - rank), by_month=[])
        for rank, person in enumerate(people)
    ]


class Stub:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> object:
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer


class Wired:
    """An API whose project sheet is a stub, with a machine at the door."""

    def __init__(self, detail: object) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_project_detail_use_case] = lambda: Stub(
            detail
        )
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=1,
            created_by=1,
            scopes=[ApiKeyScope.PROJECTS_READ],
        )
        self._standing = standing(
            Machine(
                caller=MachineCaller(key=key, owner=ANNE),
                wiring=Wiring(session=None, overrides=self.app.dependency_overrides),  # type: ignore[arg-type]
            )
        )

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)
        self.app.dependency_overrides.clear()


class TestItNamesTheMission:
    @pytest.mark.asyncio
    async def test_it_says_the_kind_the_phase_and_since_when(self) -> None:
        detail = a_detail(
            WAATCHER,
            phases_reached={ProjectStatus.DEVELOPMENT: date(2026, 3, 8)},
        )
        with Wired(detail):
            said = await project_brief(7)

        assert said.startswith(
            "WAATcher (#7) — projet, construction depuis le 08/03/2026."
        )

    @pytest.mark.asyncio
    async def test_a_phase_nobody_dated_is_said_without_a_date(self) -> None:
        with Wired(a_detail(WAATCHER)):
            said = await project_brief(7)

        assert "WAATcher (#7) — projet, construction." in said

    @pytest.mark.asyncio
    async def test_a_work_package_says_whose_it_is(self) -> None:
        with Wired(a_detail(SUPERVISION, parent=WAATCHER)):
            said = await project_brief(8)

        assert "lot de WAATcher (#7)" in said

    @pytest.mark.asyncio
    async def test_an_archived_project_says_when_it_left(self) -> None:
        retired = Project(
            id=9,
            label="WAATcher V1",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.OPERATIONS,
            is_active=False,
            archived_at=datetime(2026, 3, 12, 9, 0),
        )
        with Wired(a_detail(retired)):
            said = await project_brief(9)

        assert "archivé le 12/03/2026" in said

    @pytest.mark.asyncio
    async def test_an_unknown_project_is_said_rather_than_invented(self) -> None:
        with Wired(EntityNotFoundError("The mission cannot be found.")):
            said = await project_brief(404)

        assert "404" in said
        assert "find_project" in said


class TestItWeighsWhatWasSpentAgainstWhatWasPlanned:
    @pytest.mark.asyncio
    async def test_it_says_what_is_left_of_the_estimate(self) -> None:
        with Wired(a_detail(WAATCHER, consumed_days=128.0)):
            said = await project_brief(7)

        assert "128 jours déclarés pour 150 estimés : il en reste 22." in said

    @pytest.mark.asyncio
    async def test_an_estimate_gone_past_says_by_how_much(self) -> None:
        with Wired(a_detail(WAATCHER, consumed_days=160.0)):
            said = await project_brief(7)

        assert "160 jours déclarés pour 150 estimés : 10 de plus que prévu." in said

    @pytest.mark.asyncio
    async def test_an_estimate_exactly_met_says_so(self) -> None:
        with Wired(a_detail(WAATCHER, consumed_days=150.0)):
            said = await project_brief(7)

        assert "l'estimation est atteinte" in said

    @pytest.mark.asyncio
    async def test_a_mission_nobody_estimated_says_that_rather_than_nothing(
        self,
    ) -> None:
        unestimated = Project(
            id=11,
            label="NOMAD",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.SCOPING,
        )
        with Wired(a_detail(unestimated, consumed_days=4.0)):
            said = await project_brief(11)

        assert "4 jours déclarés. Aucune estimation n'est enregistrée." in said

    @pytest.mark.asyncio
    async def test_a_mission_nothing_was_declared_on_agrees_in_the_singular(
        self,
    ) -> None:
        """« Aucun jour déclarés » is what a green suite says. Only a reader sees it."""
        with Wired(a_detail(WAATCHER, consumed_days=0.0)):
            said = await project_brief(7)

        assert "Aucun jour déclaré pour 150 estimés" in said
        assert "déclarés" not in said


class TestItSaysWhatItDoesNotKnow:
    @pytest.mark.asyncio
    async def test_an_announced_date_is_read_back(self) -> None:
        dated = Project(
            id=7,
            label="WAATcher",
            kind=ProjectKind.PROJECT,
            status=ProjectStatus.DEVELOPMENT,
            go_live_date=date(2026, 11, 30),
        )
        with Wired(a_detail(dated)):
            said = await project_brief(7)

        assert "Mise en service annoncée le 30/11/2026." in said

    @pytest.mark.asyncio
    async def test_no_announced_date_is_said_rather_than_left_out(self) -> None:
        with Wired(a_detail(WAATCHER)):
            said = await project_brief(7)

        assert "Aucune date de mise en service n'est annoncée." in said

    @pytest.mark.asyncio
    async def test_nobody_leading_it_is_said_rather_than_left_out(self) -> None:
        with Wired(a_detail(WAATCHER)):
            said = await project_brief(7)

        assert "Personne n'y est désigné responsable." in said


class TestItNamesWhoCarriedItWithoutRankingThem:
    @pytest.mark.asyncio
    async def test_the_leads_are_named(self) -> None:
        with Wired(a_detail(WAATCHER, leads=[ANNE, MARIE])):
            said = await project_brief(7)

        assert "Porté par A. Ba et M. Ce." in said

    @pytest.mark.asyncio
    async def test_the_people_who_declared_time_are_counted_never_listed(self) -> None:
        """The sheet orders them by days. A count carries no league table."""
        with Wired(a_detail(WAATCHER, contributions=declared_by(ANNE, MARIE))):
            said = await project_brief(7)

        assert "2 personnes y ont déclaré du temps." in said
        assert "A. Ba" not in said

    @pytest.mark.asyncio
    async def test_a_single_contributor_agrees_in_the_singular(self) -> None:
        with Wired(a_detail(WAATCHER, contributions=declared_by(ANNE))):
            said = await project_brief(7)

        assert "une personne y a déclaré du temps." in said


class TestItNamesTheWorkPackages:
    @pytest.mark.asyncio
    async def test_the_packages_are_named_with_their_identifiers(self) -> None:
        with Wired(a_detail(WAATCHER, sub_projects=[IMPORT, SUPERVISION])):
            said = await project_brief(7)

        assert (
            "2 lots rattachés : WAATcher — Import (#9) et WAATcher — Supervision (#8)."
            in said
        )

    @pytest.mark.asyncio
    async def test_a_single_package_agrees_in_the_singular(self) -> None:
        with Wired(a_detail(WAATCHER, sub_projects=[SUPERVISION])):
            said = await project_brief(7)

        assert "1 lot rattaché : WAATcher — Supervision (#8)." in said

    @pytest.mark.asyncio
    async def test_a_mission_with_no_package_says_nothing_of_them(self) -> None:
        with Wired(a_detail(WAATCHER)):
            said = await project_brief(7)

        assert "lot" not in said

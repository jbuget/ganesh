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
from src.shared.utils import clock

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
        tech_leads=fields.get("tech_leads", []),  # type: ignore[arg-type]
        contributors=fields.get("contributors", []),  # type: ignore[arg-type]
        consumed_days=fields.get("consumed_days", 0.0),  # type: ignore[arg-type]
        contributions=fields.get("contributions", []),  # type: ignore[arg-type]
        sub_projects=fields.get("sub_projects", []),  # type: ignore[arg-type]
        stack=[],
        catalog_tags=[],
        tags=[],
        dependencies=[],
        is_deletable=False,
        parent=fields.get("parent"),  # type: ignore[arg-type]
        # What `estimate_of` reads for a mission nobody has cut into trades.
        estimated_days=fields.get("estimated_days", project.estimated_days),  # type: ignore[arg-type]
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


class ByProject:
    """The sheet asked for: a package's when one is named, the mission's otherwise."""

    def __init__(self, detail: object, packages: dict[int | None, ProjectDetail]):
        self._detail = detail
        self._packages = packages

    async def execute(self, project_id: int) -> object:
        if project_id in self._packages:
            return self._packages[project_id]
        if isinstance(self._detail, Exception):
            raise self._detail
        return self._detail


class Wired:
    """An API whose project sheets are stubs, with a machine at the door."""

    def __init__(self, detail: object, *packages: ProjectDetail) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        sheets = {package.project.id: package for package in packages}
        self.app.dependency_overrides[get_project_detail_use_case] = lambda: ByProject(
            detail, sheets
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
    async def test_the_estimate_is_the_one_its_trades_add_up_to(self) -> None:
        """Not the column on the mission, left behind when the trades took it over."""
        cut_up = Project(id=7, label="WAATcher", kind=ProjectKind.PROJECT)
        with Wired(a_detail(cut_up, consumed_days=26.75, estimated_days=270.0)):
            said = await project_brief(7)

        assert "pour 270 estimés : il en reste 243,25." in said

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
    async def test_each_package_says_its_phase_and_what_was_declared_on_it(
        self,
    ) -> None:
        with Wired(
            a_detail(WAATCHER, sub_projects=[IMPORT, SUPERVISION]),
            a_detail(IMPORT, consumed_days=3.0),
            a_detail(SUPERVISION),
        ):
            said = await project_brief(7)

        assert (
            "2 lots rattachés :\n"
            "- WAATcher — Import (#9) : cadrage, 3 jours déclarés\n"
            "- WAATcher — Supervision (#8) : en service, aucun jour déclaré"
        ) in said

    @pytest.mark.asyncio
    async def test_a_single_package_agrees_in_the_singular(self) -> None:
        with Wired(
            a_detail(WAATCHER, sub_projects=[SUPERVISION]), a_detail(SUPERVISION)
        ):
            said = await project_brief(7)

        assert "1 lot rattaché :" in said

    @pytest.mark.asyncio
    async def test_what_was_declared_is_added_up_with_the_packages(self) -> None:
        """A project cut into lots is booked on its lots: its own days say little."""
        with Wired(
            a_detail(WAATCHER, consumed_days=1.0, sub_projects=[IMPORT, SUPERVISION]),
            a_detail(IMPORT, consumed_days=3.0),
            a_detail(SUPERVISION, consumed_days=2.5),
        ):
            said = await project_brief(7)

        assert "Avec ses lots, 6,5 jours déclarés en tout." in said

    @pytest.mark.asyncio
    async def test_the_estimate_of_a_project_cut_into_lots_says_it_is_its_own(
        self,
    ) -> None:
        """Read beside the total of its lots, a bare « il en reste » gets added up."""
        with Wired(
            a_detail(WAATCHER, consumed_days=128.0, sub_projects=[IMPORT]),
            a_detail(IMPORT, consumed_days=3.0),
        ):
            said = await project_brief(7)

        assert (
            "Sur le projet seul : 128 jours déclarés pour 150 estimés : il en reste 22."
            in said
        )

    @pytest.mark.asyncio
    async def test_a_mission_with_no_package_says_nothing_of_them(self) -> None:
        with Wired(a_detail(WAATCHER)):
            said = await project_brief(7)

        assert "lot" not in said


class TestItSaysWhoIsOnItNow:
    @pytest.mark.asyncio
    async def test_the_people_on_it_now_are_named(self) -> None:
        """An assignment, not a tally: naming it ranks nobody."""
        with Wired(a_detail(WAATCHER, contributors=[ANNE, MARIE])):
            said = await project_brief(7)

        assert "Intervenants actuels : A. Ba et M. Ce." in said

    @pytest.mark.asyncio
    async def test_the_technical_leads_are_named(self) -> None:
        with Wired(a_detail(WAATCHER, tech_leads=[MARIE])):
            said = await project_brief(7)

        assert "Référents techniques : M. Ce." in said

    @pytest.mark.asyncio
    async def test_the_last_two_months_are_counted_lots_included(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(clock, "today", lambda: date(2026, 10, 10))
        with Wired(
            a_detail(
                WAATCHER,
                sub_projects=[IMPORT],
                contributions=[
                    Contribution(
                        user=ANNE,
                        days=7.0,
                        by_month=[(date(2026, 10, 1), 2.0), (date(2026, 7, 1), 5.0)],
                    )
                ],
            ),
            a_detail(
                IMPORT,
                contributions=[
                    Contribution(
                        user=MARIE, days=1.5, by_month=[(date(2026, 9, 1), 1.5)]
                    )
                ],
            ),
        ):
            said = await project_brief(7)

        assert (
            "Depuis le 01/09/2026, 3,5 jours saisis par 2 personnes, lots compris "
            "— réalisés ou pré-saisis." in said
        )

    @pytest.mark.asyncio
    async def test_nothing_declared_lately_is_said(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(clock, "today", lambda: date(2026, 10, 10))
        with Wired(a_detail(WAATCHER, contributions=declared_by(ANNE))):
            said = await project_brief(7)

        assert "Personne n'y a saisi de temps depuis le 01/09/2026." in said


class TestTheSheetIsReadOnRequest:
    """A model rewrites the description only after having read it.

    Left out of the brief by default: a sheet runs to pages, and « où en est
    X ? » is not asked for them.
    """

    @pytest.mark.asyncio
    async def test_the_description_is_left_out_unless_asked_for(self) -> None:
        described = Project(
            id=7, label="WAATcher", kind=ProjectKind.PROJECT, description="# Fiche"
        )
        with Wired(a_detail(described)):
            said = await project_brief(7)

        assert "# Fiche" not in said

    @pytest.mark.asyncio
    async def test_it_is_handed_over_whole_when_asked_for(self) -> None:
        described = Project(
            id=7,
            label="WAATcher",
            kind=ProjectKind.PROJECT,
            description="# Fiche\n\nUn outil.",
        )
        with Wired(a_detail(described)):
            said = await project_brief(7, include_description=True)

        assert said.endswith("Description :\n# Fiche\n\nUn outil.")

    @pytest.mark.asyncio
    async def test_a_sheet_nobody_wrote_is_said(self) -> None:
        with Wired(a_detail(WAATCHER)):
            said = await project_brief(7, include_description=True)

        assert said.endswith("Aucune description n'est renseignée.")

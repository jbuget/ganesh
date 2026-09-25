"""« Qu'est-ce qui est en retard, et qu'est-ce qui arrive ? »

The question a manager puts to a portfolio, answered off the roadmap — the
screen that is *shown* rather than arbitrated. Two properties this file holds
to, both carried over from the screen itself:

- **a placeholder is never counted as a fact**: what went live is read off
  `went_live_on` and never off a bar that had to open somewhere to be drawn;
- **a mission with nothing to draw still shows**, because that is the line
  steering has to see.
"""

from datetime import date

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.portfolio import portfolio_status
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.planning.domain.entities.roadmap import (
    Roadmap,
    RoadmapMission,
    RoadmapSummary,
)
from src.modules.planning.domain.entities.workload_plan import PlanBlocker
from src.modules.planning.presentation.dependencies import get_roadmap_use_case
from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus
from src.modules.users.domain.entities.user import Role, User

OWNER = User(
    id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)


class Stub:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> object:
        return self._answer


class Wired:
    """An API whose roadmap is a stub, with a machine at the door."""

    def __init__(self, roadmap: Roadmap) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_roadmap_use_case] = lambda: Stub(roadmap)
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=1,
            created_by=1,
            scopes=[ApiKeyScope.ALL_READ],
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


def a_mission(label: str, **fields: object) -> RoadmapMission:
    return RoadmapMission(
        project_id=fields.pop("project_id", 1),  # type: ignore[arg-type]
        label=label,
        kind=ProjectKind.PROJECT,
        status=fields.pop("status", ProjectStatus.DEVELOPMENT),  # type: ignore[arg-type]
        priority=None,
        category=None,
        parent_id=None,
        **fields,  # type: ignore[arg-type]
    )


def a_roadmap(lines: list[RoadmapMission], **counts: int) -> Roadmap:
    return Roadmap(
        from_day=date(2026, 8, 1),
        to_day=date(2027, 2, 28),
        today=date(2026, 9, 21),
        missions=lines,
        summary=RoadmapSummary(
            missions=counts.get("missions", len(lines)),
            late=counts.get("late", 0),
            undated=counts.get("undated", 0),
            unestimated=counts.get("unestimated", 0),
            delivered=counts.get("delivered", 0),
        ),
    )


class TestWhatItSaysAboveTheBars:
    @pytest.mark.asyncio
    async def test_it_opens_on_the_tally_the_screen_opens_on(self) -> None:
        roadmap = a_roadmap([a_mission("WAATcher")], missions=14, late=3, delivered=2)
        with Wired(roadmap):
            said = await portfolio_status()

        assert "14 projets" in said
        assert "3 en retard" in said
        assert "2 mises en service" in said

    @pytest.mark.asyncio
    async def test_it_says_how_much_of_the_tally_to_believe(self) -> None:
        """« 5 sans date » is what says how much of the report to believe."""
        roadmap = a_roadmap(
            [a_mission("WAATcher")], missions=14, undated=5, unestimated=2
        )
        with Wired(roadmap):
            said = await portfolio_status()

        assert "5 n'ont pas de date annoncée" in said
        assert "2 n'ont pas d'estimation" in said

    @pytest.mark.asyncio
    async def test_a_portfolio_that_delivered_nothing_says_so(self) -> None:
        with Wired(a_roadmap([a_mission("WAATcher")], missions=1)):
            said = await portfolio_status()
        assert "aucune mise en service" in said


class TestWhatIsLate:
    @pytest.mark.asyncio
    async def test_a_late_mission_says_by_how_much_and_against_what(self) -> None:
        late = a_mission(
            "SiteTracker",
            target_date=date(2026, 9, 1),
            landing_date=date(2026, 9, 13),
            slippage_days=12,
            is_late=True,
        )
        with Wired(a_roadmap([late], missions=1, late=1)):
            said = await portfolio_status()

        assert "SiteTracker" in said
        assert "12 jours" in said
        assert "01/09/2026" in said

    @pytest.mark.asyncio
    async def test_what_is_on_time_is_not_listed_one_by_one(self) -> None:
        """A roadmap read out line by line is the screen, not an answer."""
        missions = [a_mission(f"Projet {n}", project_id=n) for n in range(1, 9)]
        with Wired(a_roadmap(missions, missions=8)):
            said = await portfolio_status()

        assert "Projet 4" not in said

    @pytest.mark.asyncio
    async def test_a_mission_the_projection_could_not_place_is_named(self) -> None:
        """A mission with no bar is a question, not an absence."""
        stuck = a_mission("EDIT", blocker=PlanBlocker.NO_ESTIMATE)
        with Wired(a_roadmap([stuck], missions=1)):
            said = await portfolio_status()

        assert "EDIT" in said
        assert "estim" in said

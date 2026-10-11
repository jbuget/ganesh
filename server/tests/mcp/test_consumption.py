"""« Où en est le budget de ce projet, métier par métier ? »

`project_brief` reads the estimate of the whole mission, as what is left. The
whole hides what steers: a build budget with days to spare says nothing of a
design that is already over. This reads each trade against its own.

- **what is left is said as what is left**, trade by trade — « il en reste
  15 », never two figures a model subtracts and gets wrong;
- **what is not budgeted is said**, not compared: a ratio against nothing is
  a number a model invents;
- **delivered and forecast are never added** — a supposition must not pass for
  time spent.
"""

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.consumption import project_consumption
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.projects.application.use_cases.get_project_consumption import (
    ProjectConsumption,
)
from src.modules.projects.domain.entities.activity import Activity
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.services.consumption import TradeConsumption
from src.modules.projects.presentation.dependencies import (
    get_project_consumption_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

OWNER = User(
    id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)
NOMAD = Project(id=1, label="Nomad", kind=ProjectKind.PROJECT)
IMPORT = Project(
    id=2, label="Nomad — Import", kind=ProjectKind.WORK_PACKAGE, parent_id=1
)


def trade(
    label: str | None,
    delivered: float,
    forecast: float = 0.0,
    budget: float | None = None,
    is_active: bool = True,
) -> TradeConsumption:
    activity = (
        None
        if label is None
        else Activity(
            id=1,
            project_id=1,
            label=label,
            estimated_days=budget,
            is_active=is_active,
        )
    )
    return TradeConsumption(activity=activity, delivered=delivered, forecast=forecast)


class Stub:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> object:
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer


class Wired:
    def __init__(self, answer: object) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_project_consumption_use_case] = lambda: Stub(
            answer
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


class TestEachTradeAgainstItsOwnBudget:
    @pytest.mark.asyncio
    async def test_a_trade_with_days_to_spare_says_what_is_left(self) -> None:
        sheet = ProjectConsumption(
            project=NOMAD, trades=[trade("Développement", 5, budget=20)]
        )
        with Wired(sheet):
            said = await project_consumption(1)

        assert said == (
            "Nomad (#1) :\n- Développement — 5 jours déclarés pour 20 estimés : "
            "il en reste 15."
        )

    @pytest.mark.asyncio
    async def test_a_trade_over_its_budget_says_by_how_much(self) -> None:
        sheet = ProjectConsumption(project=NOMAD, trades=[trade("Design", 6, budget=5)])
        with Wired(sheet):
            said = await project_consumption(1)

        assert "1 de plus que prévu" in said

    @pytest.mark.asyncio
    async def test_a_trade_that_reached_its_budget_says_so(self) -> None:
        sheet = ProjectConsumption(project=NOMAD, trades=[trade("Design", 5, budget=5)])
        with Wired(sheet):
            said = await project_consumption(1)

        assert "l'estimation est atteinte" in said

    @pytest.mark.asyncio
    async def test_a_trade_nobody_budgeted_is_not_compared_to_anything(self) -> None:
        sheet = ProjectConsumption(project=NOMAD, trades=[trade("Pilotage", 3)])
        with Wired(sheet):
            said = await project_consumption(1)

        assert "Pilotage — 3 jours déclarés, aucune estimation." in said

    @pytest.mark.asyncio
    async def test_a_trade_without_a_day_says_none_rather_than_zero(self) -> None:
        sheet = ProjectConsumption(project=NOMAD, trades=[trade("Design", 0, budget=5)])
        with Wired(sheet):
            said = await project_consumption(1)

        assert "aucun jour déclaré pour 5 estimés : il en reste 5" in said


class TestDeliveredAndForecastAreNotAdded:
    @pytest.mark.asyncio
    async def test_forecast_is_said_apart(self) -> None:
        sheet = ProjectConsumption(
            project=NOMAD, trades=[trade("Développement", 5, forecast=2, budget=20)]
        )
        with Wired(sheet):
            said = await project_consumption(1)

        assert "2 jours pré-saisis à venir" in said


class TestWhatIsListed:
    @pytest.mark.asyncio
    async def test_days_under_no_trade_say_nobody_said_which(self) -> None:
        sheet = ProjectConsumption(project=NOMAD, trades=[trade(None, 8)])
        with Wired(sheet):
            said = await project_consumption(1)

        assert "Sans métier — 8 jours déclarés" in said
        assert "reprise" in said

    @pytest.mark.asyncio
    async def test_an_archived_trade_says_so(self) -> None:
        sheet = ProjectConsumption(
            project=NOMAD, trades=[trade("Cadrage", 2, budget=3, is_active=False)]
        )
        with Wired(sheet):
            said = await project_consumption(1)

        assert "Cadrage (archivé)" in said

    @pytest.mark.asyncio
    async def test_a_project_without_a_trade_says_it_cannot_be_declared_on(
        self,
    ) -> None:
        with Wired(ProjectConsumption(project=NOMAD, trades=[])):
            said = await project_consumption(1)

        assert "aucun métier" in said.lower()

    @pytest.mark.asyncio
    async def test_the_work_packages_are_read_under_the_project(self) -> None:
        sheet = ProjectConsumption(
            project=NOMAD,
            trades=[trade("Développement", 5, budget=20)],
            work_packages=[
                ProjectConsumption(
                    project=IMPORT, trades=[trade("Développement", 1, budget=4)]
                )
            ],
        )
        with Wired(sheet):
            said = await project_consumption(1)

        assert "Lot Nomad — Import (#2) :" in said
        assert "1 jour déclaré pour 4 estimés : il en reste 3" in said


class TestWhatItRefuses:
    @pytest.mark.asyncio
    async def test_a_project_nobody_can_find_says_where_to_look(self) -> None:
        with Wired(EntityNotFoundError("The mission cannot be found.")):
            said = await project_consumption(404)

        assert "404" in said
        assert "find_project" in said

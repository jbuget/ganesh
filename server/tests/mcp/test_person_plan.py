"""« Comment est le planning de David ? À partir de quand est-il libre ? »

Two readings, never drawn alike: what the person **pre-entered** in their grid
— a fact they declared — and what the **plan de charge** projects on top of it
from the backlog — a supposition. Reading the second as the first is the
mistake the planning screen exists to prevent.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.plan import MOST_WEEKS, person_plan
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.entries.presentation.dependencies import get_month_grid_use_case
from src.modules.planning.domain.entities.workload_plan import (
    PersonPlan,
    PlanBlocker,
    ProjectedMission,
    WeeklyLoad,
)
from src.modules.planning.presentation.dependencies import get_workload_plan_use_case
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.users.domain.entities.user import Role, User
from src.modules.users.presentation.dependencies import get_list_users_use_case
from src.shared.utils import clock

TODAY = date(2026, 10, 12)

DAVID = User(
    id=3,
    entra_oid="oid-3",
    email="d@waat.fr",
    display_name="David DEHE",
    role=Role.TEAMMATE,
    first_name="David",
    last_name="Dehé",
)
DAVID_B = User(
    id=4,
    entra_oid="oid-4",
    email="db@waat.fr",
    display_name="David BRUN",
    role=Role.TEAMMATE,
)
LEA = User(
    id=1,
    entra_oid="oid-1",
    email="l@waat.fr",
    display_name="Léa Chen",
    role=Role.TEAMMATE,
)
VISITOR = User(
    id=9,
    entra_oid="oid-9",
    email="v@waat.fr",
    display_name="David Invité",
    role=Role.GUEST,
)

EDIT_V2 = Project(id=8, label="EDIT V2", kind=ProjectKind.WORK_PACKAGE, parent_id=7)
GMAO = Project(id=12, label="Sitetracker - GMAO", kind=ProjectKind.PROJECT)


@dataclass
class Row:
    """What `person_plan` reads of a grid row."""

    project_id: int
    project_label: str
    label: str
    kind: ProjectKind
    activity_id: int | None
    values: dict[date, float] = field(default_factory=dict)


@dataclass
class Grid:
    rows: list[Row]


@dataclass
class Load:
    user: User
    load: PersonPlan


@dataclass
class MissionRow:
    mission: Project
    projected: ProjectedMission
    assignees: list[User]


@dataclass
class Reading:
    people: list[Load]
    missions: list[MissionRow]


class Users:
    def __init__(self, people: list[User]) -> None:
        self._people = people

    async def execute(self, *args: object, **kwargs: object) -> list[User]:
        return self._people


class Grids:
    """A grid per month, as the use case answers one month at a time."""

    def __init__(self, months: dict[date, Grid]) -> None:
        self._months = months
        self.asked: list[tuple[int, date]] = []

    async def execute(self, query: object) -> Grid:
        user_id, month = query.user_id, query.month  # type: ignore[attr-defined]
        self.asked.append((user_id, month))
        return self._months.get(month, Grid(rows=[]))


class Plan:
    def __init__(self, reading: Reading) -> None:
        self._reading = reading

    async def execute(self, *args: object, **kwargs: object) -> Reading:
        return self._reading


def week(monday: date, booked: float, projected: float = 0.0) -> WeeklyLoad:
    return WeeklyLoad(
        week=monday, capacity=5.0, booked=booked, projected=projected, reserved=0.5
    )


def edit_row(*days: tuple[date, float]) -> Row:
    return Row(8, "EDIT V2", "Développement", ProjectKind.WORK_PACKAGE, 21, dict(days))


def away_row(*days: tuple[date, float]) -> Row:
    return Row(
        1,
        "Absences (congés, RTT, maladie)",
        "Absences (congés, RTT, maladie)",
        ProjectKind.OFF_PROJECT,
        None,
        dict(days),
    )


DAVID_WEEKS = [
    week(date(2026, 10, 12), booked=4.5),
    week(date(2026, 10, 19), booked=3.0, projected=1.5),
    week(date(2026, 10, 26), booked=0.0, projected=2.0),
]

DAVID_MISSIONS = [
    MissionRow(
        EDIT_V2,
        ProjectedMission(
            project_id=8,
            remaining_days=3.5,
            scheduled_days=3.5,
            ends_on=date(2026, 10, 28),
        ),
        [DAVID, LEA],
    ),
    MissionRow(
        GMAO,
        ProjectedMission(
            project_id=12,
            remaining_days=0,
            scheduled_days=0,
            blocker=PlanBlocker.NO_ESTIMATE,
        ),
        [DAVID],
    ),
]


class Wired:
    def __init__(
        self,
        people: list[User] | None = None,
        months: dict[date, Grid] | None = None,
        weeks: list[WeeklyLoad] | None = None,
        missions: list[MissionRow] | None = None,
    ) -> None:
        app = FastAPI()
        ToolServer().attach(app)
        self.grids = Grids(months or {})
        reading = Reading(
            people=[Load(DAVID, PersonPlan(user_id=3, weeks=weeks or []))],
            missions=missions or [],
        )
        app.dependency_overrides[get_list_users_use_case] = lambda: Users(
            people or [DAVID, DAVID_B, LEA, VISITOR]
        )
        app.dependency_overrides[get_month_grid_use_case] = lambda: self.grids
        app.dependency_overrides[get_workload_plan_use_case] = lambda: Plan(reading)
        key = ApiKey(
            id=1,
            name="clé",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=1,
            created_by=1,
            scopes=[ApiKeyScope.ROADMAP_READ],
        )
        self._standing = standing(
            Machine(
                caller=MachineCaller(key=key, owner=LEA),
                wiring=Wiring(session=None, overrides=app.dependency_overrides),  # type: ignore[arg-type]
            )
        )

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)


@pytest.fixture(autouse=True)
def _today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clock, "today", lambda: TODAY)


@pytest.mark.asyncio
class TestFindingThePerson:
    async def test_a_name_shared_by_two_people_asks_which_one(self) -> None:
        with Wired():
            said = await person_plan("david")

        assert said == (
            "Plusieurs personnes correspondent à « david » : David BRUN et "
            "David Dehé. Laquelle est visée ?"
        )

    async def test_no_name_at_all_finds_nobody_rather_than_everybody(self) -> None:
        with Wired():
            said = await person_plan("  ")

        assert said == "Aucun nom n'a été donné : de qui faut-il lire le planning ?"

    async def test_a_guest_is_not_somebody_whose_plan_is_read(self) -> None:
        with Wired(people=[VISITOR]):
            said = await person_plan("david")

        assert said == "Personne dans l'équipe ne correspond à « david »."

    async def test_a_name_is_matched_without_its_accents(self) -> None:
        with Wired(people=[DAVID, LEA]):
            said = await person_plan("dehe")

        assert said.startswith("David Dehé.")


@pytest.mark.asyncio
class TestWhatThePersonPreEntered:
    async def test_the_days_entered_ahead_are_read_project_by_project(self) -> None:
        october = Grid(
            rows=[
                edit_row(
                    (date(2026, 10, 9), 1.0),
                    (date(2026, 10, 13), 1.0),
                    (date(2026, 10, 14), 0.5),
                    (date(2026, 10, 23), 1.0),
                )
            ]
        )
        with Wired(people=[DAVID], months={date(2026, 10, 1): october}):
            said = await person_plan("David")

        assert (
            "Pré-saisi par David Dehé à partir d'aujourd'hui :\n"
            "- EDIT V2 (Développement) : 2,5 jours, du 13/10 au 23/10"
        ) in said
        assert "Rien n'est pré-saisi après le 23/10/2026." in said

    async def test_the_coming_months_are_read_too(self) -> None:
        wired = Wired(people=[DAVID])
        with wired:
            await person_plan("David")

        assert wired.grids.asked == [
            (3, date(2026, 10, 1)),
            (3, date(2026, 11, 1)),
            (3, date(2026, 12, 1)),
        ]

    async def test_time_off_project_is_never_named(self) -> None:
        """An absence may be a sick day: what kind is nobody's business here."""
        october = Grid(rows=[away_row((date(2026, 10, 16), 1.0))])
        with Wired(people=[DAVID], months={date(2026, 10, 1): october}):
            said = await person_plan("David")

        assert "- Hors projet : 1 jour, le 16/10" in said
        assert "maladie" not in said
        assert "Absences" not in said

    async def test_nothing_entered_ahead_is_said(self) -> None:
        with Wired(people=[DAVID]):
            said = await person_plan("David")

        assert "Rien n'est pré-saisi par David Dehé à partir d'aujourd'hui." in said


@pytest.mark.asyncio
class TestWhatThePlanProjects:
    async def test_nobody_on_any_project_is_said_by_name(self) -> None:
        with Wired(people=[DAVID], weeks=DAVID_WEEKS):
            said = await person_plan("David")

        assert "David Dehé n'intervient sur aucun projet du plan de charge." in said

    async def test_each_week_tells_the_entered_from_the_projected(self) -> None:
        with Wired(people=[DAVID], weeks=DAVID_WEEKS):
            said = await person_plan("David")

        assert "Plan de charge, une projection et non une saisie" in said
        assert "- semaine du 19/10 : 3 jours pré-saisis, 1,5 projeté, 0 libre" in said

    async def test_the_first_week_with_room_is_said(self) -> None:
        with Wired(people=[DAVID], weeks=DAVID_WEEKS):
            said = await person_plan("David")

        assert (
            "Première semaine avec de la place : celle du 26/10/2026 "
            "(2,5 jours libres)."
        ) in said

    async def test_no_room_over_the_horizon_is_said(self) -> None:
        with Wired(people=[DAVID], weeks=[week(date(2026, 10, 12), booked=4.5)]):
            said = await person_plan("David")

        assert "Aucune semaine n'a de place sur l'horizon du plan de charge." in said

    async def test_only_the_coming_weeks_are_read_out(self) -> None:
        weeks = [week(TODAY + timedelta(weeks=n), booked=4.5) for n in range(12)]
        with Wired(people=[DAVID], weeks=weeks):
            said = await person_plan("David")

        assert said.count("- semaine du") == MOST_WEEKS

    async def test_the_projects_it_places_on_the_person_say_when_they_land(
        self,
    ) -> None:
        with Wired(people=[DAVID], weeks=DAVID_WEEKS, missions=DAVID_MISSIONS):
            said = await person_plan("David")

        assert (
            "Projets sur lesquels David Dehé intervient, dans le plan de charge :\n"
            "- EDIT V2 : fin projetée le 28/10/2026, avec Léa Chen\n"
            "- Sitetracker - GMAO : pas de date, personne ne l'a estimé ; "
            "rien n'y est projeté"
        ) in said

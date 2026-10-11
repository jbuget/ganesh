"""« Qui est libre la semaine du 19 ? »

`person_plan` reads one person; this reads the week across the team. Same
projection, same suppositions: what is free is what the plan leaves after what
people pre-entered **and** what it projects on top, with the half day held back
each week already deducted. Said so, because a figure read as a commitment is
the mistake the planning screen exists to prevent.

Whoever is free is listed **alphabetically**, never by how much room they
have: a list sorted by free days is a list of who is idle.
"""

from dataclasses import dataclass, field
from datetime import date

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.plan import team_availability
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.planning.domain.entities.workload_plan import PersonPlan, WeeklyLoad
from src.modules.planning.presentation.dependencies import get_workload_plan_use_case
from src.modules.users.domain.entities.user import Role, User

TODAY = date(2026, 10, 12)
THIS_WEEK = date(2026, 10, 12)
NEXT_WEEK = date(2026, 10, 19)


def a_user(user_id: int, name: str, role: Role = Role.TEAMMATE) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"{user_id}@waat.fr",
        display_name=name,
        role=role,
    )


LEA = a_user(1, "Léa Chen")
MARC = a_user(2, "Marc Dupont")
ZOE = a_user(3, "Zoé Brun")
VISITOR = a_user(9, "Invité", Role.GUEST)


@dataclass
class Load:
    user: User
    load: PersonPlan


@dataclass
class Reading:
    from_day: date
    to_day: date
    people: list[Load] = field(default_factory=list)
    missions: list[object] = field(default_factory=list)


def week(monday: date, booked: float = 0.0, projected: float = 0.0) -> WeeklyLoad:
    return WeeklyLoad(
        week=monday, capacity=5.0, booked=booked, projected=projected, reserved=0.5
    )


def diary(user: User, *weeks: WeeklyLoad) -> Load:
    assert user.id is not None
    return Load(user, PersonPlan(user_id=user.id, weeks=list(weeks)))


class Plan:
    def __init__(self, reading: Reading) -> None:
        self._reading = reading

    async def execute(self, *args: object, **kwargs: object) -> Reading:
        return self._reading


class Wired:
    def __init__(self, *people: Load) -> None:
        app = FastAPI()
        ToolServer().attach(app)
        reading = Reading(
            from_day=THIS_WEEK, to_day=date(2027, 1, 3), people=list(people)
        )
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
    monkeypatch.setattr("src.mcp.tools.plan.clock.today", lambda: TODAY)


class TestWhoIsFree:
    @pytest.mark.asyncio
    async def test_the_people_with_room_are_listed_with_how_much(self) -> None:
        with Wired(
            diary(LEA, week(NEXT_WEEK, booked=2.5)),
            diary(MARC, week(NEXT_WEEK, booked=4.5)),
        ):
            said = await team_availability("2026-10-19")

        assert "Semaine du 19/10/2026" in said
        assert "- Léa Chen — 2 jours libres" in said
        assert "Marc Dupont" not in said

    @pytest.mark.asyncio
    async def test_they_are_listed_alphabetically_not_by_room(self) -> None:
        with Wired(
            diary(ZOE, week(NEXT_WEEK, booked=0)),
            diary(LEA, week(NEXT_WEEK, booked=4)),
        ):
            said = await team_availability("2026-10-19")

        assert said.index("Léa Chen") < said.index("Zoé Brun")

    @pytest.mark.asyncio
    async def test_the_projection_counts_against_the_room(self) -> None:
        with Wired(diary(LEA, week(NEXT_WEEK, booked=1, projected=3.5))):
            said = await team_availability("2026-10-19")

        assert "Personne n'a de place" in said

    @pytest.mark.asyncio
    async def test_those_with_none_are_counted_not_named(self) -> None:
        with Wired(
            diary(LEA, week(NEXT_WEEK, booked=0)),
            diary(MARC, week(NEXT_WEEK, booked=5)),
            diary(ZOE, week(NEXT_WEEK, booked=5)),
        ):
            said = await team_availability("2026-10-19")

        assert "2 autres n'ont pas de place" in said
        assert "Marc" not in said

    @pytest.mark.asyncio
    async def test_a_guest_is_not_part_of_the_team(self) -> None:
        with Wired(diary(VISITOR, week(NEXT_WEEK))):
            said = await team_availability("2026-10-19")

        assert "Invité" not in said


class TestWhichWeek:
    @pytest.mark.asyncio
    async def test_any_day_of_a_week_names_its_monday(self) -> None:
        with Wired(diary(LEA, week(NEXT_WEEK))):
            said = await team_availability("2026-10-22")

        assert "Semaine du 19/10/2026" in said

    @pytest.mark.asyncio
    async def test_no_date_is_the_week_running(self) -> None:
        with Wired(diary(LEA, week(THIS_WEEK))):
            said = await team_availability()

        assert "Semaine du 12/10/2026" in said

    @pytest.mark.asyncio
    async def test_a_date_that_does_not_read_is_said(self) -> None:
        with Wired():
            said = await team_availability("la semaine du 19")

        assert "AAAA-MM-JJ" in said

    @pytest.mark.asyncio
    async def test_a_week_past_the_horizon_says_how_far_the_plan_goes(self) -> None:
        with Wired(diary(LEA, week(THIS_WEEK))):
            said = await team_availability("2027-06-07")

        assert "ne couvre pas" in said
        assert "03/01/2027" in said


class TestItIsASupposition:
    @pytest.mark.asyncio
    async def test_it_says_that_what_is_free_is_projected_and_with_a_reserve(
        self,
    ) -> None:
        with Wired(diary(LEA, week(NEXT_WEEK))):
            said = await team_availability("2026-10-19")

        assert "projection" in said
        assert "demi-journée" in said

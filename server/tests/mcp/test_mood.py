"""« Comment va l'équipe, ces deux dernières semaines ? »

The one tool that reads something given in confidence, and the only one whose
tests are mostly about what it must **not** say.

The team screen names everyone, on purpose — but it never aggregates one
person over time, and that is exactly what a model handed the names would do
(« X est sous la moyenne depuis huit jours »). So this tool answers the
question the screen answers, in figures nobody can be read out of.
"""

from datetime import date

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.mood import FLOOR, team_mood
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.moods.application.dtos.mood_dtos import TeamMoods
from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from src.modules.moods.domain.services.mood_report import build_report
from src.modules.moods.presentation.dependencies import get_team_moods_use_case
from src.modules.users.domain.entities.user import Role, User

OWNER = User(
    id=1, entra_oid="oid-1", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)
TEAM = [
    User(
        id=n,
        entra_oid=f"oid-{n}",
        email=f"{n}@waat.fr",
        display_name=f"P{n} Nom",
        role=Role.TEAMMATE,
    )
    for n in range(1, 13)
]


class Stub:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    async def execute(self, *args: object, **kwargs: object) -> object:
        return self._answer


class Wired:
    def __init__(self, moods: TeamMoods, scope: ApiKeyScope | None = None) -> None:
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_team_moods_use_case] = lambda: Stub(moods)
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=1,
            created_by=1,
            scopes=[scope or ApiKeyScope.MOODS_READ],
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


def moods_on(day: date, levels: list[MoodLevel]) -> list[Mood]:
    return [
        Mood(id=None, user_id=n, day=day, level=level)
        for n, level in enumerate(levels, start=1)
    ]


def a_fortnight(by_day: dict[date, list[MoodLevel]], headcount: int = 12) -> TeamMoods:
    days = sorted(by_day, reverse=True)
    posted = [mood for day in days for mood in moods_on(day, by_day[day])]
    return TeamMoods(
        report=build_report(days, posted, headcount=headcount), people=TEAM
    )


GOOD = MoodLevel.GOOD
FLAT = MoodLevel.NEUTRAL
BAD = MoodLevel.BAD


class TestNobodyCanBeReadOutOfIt:
    @pytest.mark.asyncio
    async def test_no_name_ever_comes_out(self) -> None:
        with Wired(a_fortnight({date(2026, 9, 18): [GOOD, FLAT, BAD, GOOD]})):
            said = await team_mood()

        for person in TEAM:
            assert person.display_name not in said

    @pytest.mark.asyncio
    async def test_no_identifier_either(self) -> None:
        """Without an identifier, nothing can be recomposed person by person."""
        with Wired(a_fortnight({date(2026, 9, 18): [GOOD, FLAT, BAD, GOOD]})):
            said = await team_mood()

        assert "user_id" not in said
        assert "#1" not in said

    @pytest.mark.asyncio
    async def test_a_day_too_few_answered_is_not_averaged(self) -> None:
        """Two answers out of twelve say what two people felt, and no more."""
        thin = {date(2026, 9, 18): [BAD] * (FLOOR - 1)}
        with Wired(a_fortnight(thin)):
            said = await team_mood()

        assert "Trop peu" in said
        assert "sur 5" not in said

    @pytest.mark.asyncio
    async def test_the_key_must_carry_the_scope_itself(self) -> None:
        """`all:read` does not reach here. See `NEVER_BROAD`."""
        from mcp.server.mcpserver.exceptions import ToolError

        with (
            Wired(a_fortnight({date(2026, 9, 18): [GOOD]}), ApiKeyScope.ALL_READ),
            pytest.raises(ToolError, match="moods:read"),
        ):
            await team_mood()


class TestWhatItSays:
    @pytest.mark.asyncio
    async def test_it_reads_the_fortnight_as_one_figure(self) -> None:
        with Wired(
            a_fortnight(
                {
                    date(2026, 9, 18): [GOOD, GOOD, GOOD, FLAT],
                    date(2026, 9, 17): [GOOD, GOOD, FLAT, FLAT],
                }
            )
        ):
            said = await team_mood()

        assert "sur 5" in said
        assert "8 réponses" in said

    @pytest.mark.asyncio
    async def test_a_fortnight_nobody_answered_says_so(self) -> None:
        with Wired(a_fortnight({date(2026, 9, 18): []})):
            said = await team_mood()

        assert "Personne n'a répondu" in said

    @pytest.mark.asyncio
    async def test_the_days_that_dip_are_named_without_naming_anyone(self) -> None:
        with Wired(
            a_fortnight(
                {
                    date(2026, 9, 18): [BAD, BAD, BAD, BAD],
                    date(2026, 9, 17): [GOOD, GOOD, GOOD, GOOD],
                }
            )
        ):
            said = await team_mood()

        assert "18/09" in said

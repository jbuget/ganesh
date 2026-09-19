"""The team's morale over the last fortnight."""

from datetime import date

from src.modules.moods.application.use_cases.get_team_moods import GetTeamMoodsUseCase
from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryMoodRepository,
    InMemoryUserRepository,
)

ALICE = User(
    id=1,
    entra_oid="oid-1",
    email="l.chen@waat.fr",
    display_name="L. Chen",
    role=Role.TEAMMATE,
)
BOB = User(
    id=2,
    entra_oid="oid-2",
    email="g.belhadj@waat.fr",
    display_name="G. Belhadj",
    role=Role.TEAMMATE,
)
GONE = User(
    id=3,
    entra_oid="oid-3",
    email="m.roux@waat.fr",
    display_name="M. Roux",
    role=Role.TEAMMATE,
    is_active=False,
)
TUESDAY = date(2026, 9, 15)
MONDAY = date(2026, 9, 14)


def build(moods: list[Mood]) -> GetTeamMoodsUseCase:
    return GetTeamMoodsUseCase(
        users=InMemoryUserRepository([ALICE, BOB, GONE]),
        moods=InMemoryMoodRepository(moods),
    )


async def test_the_window_holds_the_working_days_most_recent_first() -> None:
    view = await build([]).execute(today=TUESDAY)

    assert [day.day for day in view.report.days][:2] == [TUESDAY, MONDAY]
    assert len(view.report.days) == 10


async def test_the_headcount_counts_who_could_answer_today() -> None:
    """A deactivated teammate is not a silence: they are no longer expected."""
    view = await build([]).execute(today=TUESDAY)

    assert view.report.headcount == 2


async def test_someone_who_has_left_counts_on_a_window_they_answered_in() -> None:
    """Otherwise a day reads « 3 / 2 », and a share above its whole says the
    denominator is the wrong one."""
    view = await build(
        [Mood(id=1, user_id=3, day=MONDAY, level=MoodLevel.GOOD)]
    ).execute(today=TUESDAY)

    assert view.report.headcount == 3
    assert view.report.days[1].participation == 1


async def test_a_deactivated_teammate_still_carries_the_moods_they_posted() -> None:
    view = await build(
        [Mood(id=1, user_id=3, day=MONDAY, level=MoodLevel.GOOD)]
    ).execute(today=TUESDAY)

    assert view.report.days[1].moods[0].user_id == 3
    assert [person.id for person in view.people] == [1, 2, 3]


async def test_a_mood_older_than_the_window_is_left_out() -> None:
    view = await build(
        [Mood(id=1, user_id=1, day=date(2026, 8, 20), level=MoodLevel.BAD)]
    ).execute(today=TUESDAY)

    assert all(day.moods == () for day in view.report.days)

"""What one may still answer for."""

from datetime import date

from src.modules.moods.application.use_cases.get_my_moods import GetMyMoodsUseCase
from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from tests.helpers.in_memory_repositories import InMemoryMoodRepository

TUESDAY = date(2026, 9, 15)
MONDAY = date(2026, 9, 14)


async def test_the_open_days_come_back_empty_when_nothing_was_posted() -> None:
    use_case = GetMyMoodsUseCase(moods=InMemoryMoodRepository())

    days = await use_case.execute(user_id=1, today=TUESDAY)

    assert [(day.day, day.level) for day in days] == [(TUESDAY, None), (MONDAY, None)]


async def test_a_day_already_answered_comes_back_filled_in() -> None:
    use_case = GetMyMoodsUseCase(
        moods=InMemoryMoodRepository(
            [Mood(id=1, user_id=1, day=MONDAY, level=MoodLevel.HARD)]
        )
    )

    days = await use_case.execute(user_id=1, today=TUESDAY)

    assert days[0].level is None
    assert days[1].level is MoodLevel.HARD


async def test_a_colleagues_mood_is_not_mine() -> None:
    use_case = GetMyMoodsUseCase(
        moods=InMemoryMoodRepository(
            [Mood(id=1, user_id=2, day=TUESDAY, level=MoodLevel.EXCELLENT)]
        )
    )

    days = await use_case.execute(user_id=1, today=TUESDAY)

    assert all(day.level is None for day in days)

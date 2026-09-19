"""Posting how a day felt, and taking it back."""

from datetime import date

import pytest

from src.modules.moods.application.dtos.mood_dtos import (
    ClearMoodCommand,
    SetMoodCommand,
)
from src.modules.moods.application.use_cases.clear_mood import ClearMoodUseCase
from src.modules.moods.application.use_cases.set_mood import SetMoodUseCase
from src.modules.moods.domain.entities.mood import Mood, MoodLevel
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import (
    EntityNotFoundError,
    ForbiddenActionError,
    ValidationError,
)
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
GONE = User(
    id=2,
    entra_oid="oid-2",
    email="m.roux@waat.fr",
    display_name="M. Roux",
    role=Role.TEAMMATE,
    is_active=False,
)
TUESDAY = date(2026, 9, 15)
MONDAY = date(2026, 9, 14)


def build(moods: list[Mood] | None = None):
    repository = InMemoryMoodRepository(moods)
    use_case = SetMoodUseCase(
        users=InMemoryUserRepository([ALICE, GONE]), moods=repository
    )
    return use_case, repository


async def test_a_teammate_posts_the_mood_of_the_day() -> None:
    use_case, moods = build()

    await use_case.execute(
        SetMoodCommand(user_id=1, day=TUESDAY, level=MoodLevel.GOOD), today=TUESDAY
    )

    saved = await moods.get(1, TUESDAY)
    assert saved is not None
    assert saved.level is MoodLevel.GOOD


async def test_a_teammate_answers_for_the_working_day_before() -> None:
    use_case, moods = build()

    await use_case.execute(
        SetMoodCommand(user_id=1, day=MONDAY, level=MoodLevel.HARD), today=TUESDAY
    )

    saved = await moods.get(1, MONDAY)
    assert saved is not None
    assert saved.level is MoodLevel.HARD


async def test_posting_again_changes_the_mood_rather_than_adding_one() -> None:
    use_case, moods = build()

    await use_case.execute(
        SetMoodCommand(user_id=1, day=TUESDAY, level=MoodLevel.BAD), today=TUESDAY
    )
    await use_case.execute(
        SetMoodCommand(user_id=1, day=TUESDAY, level=MoodLevel.EXCELLENT), today=TUESDAY
    )

    assert len(await moods.list_between(TUESDAY, TUESDAY)) == 1
    saved = await moods.get(1, TUESDAY)
    assert saved is not None
    assert saved.level is MoodLevel.EXCELLENT


async def test_a_day_further_back_is_refused() -> None:
    use_case, moods = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            SetMoodCommand(user_id=1, day=date(2026, 9, 11), level=MoodLevel.GOOD),
            today=TUESDAY,
        )

    assert await moods.get(1, date(2026, 9, 11)) is None


async def test_a_day_to_come_is_refused() -> None:
    use_case, _ = build()

    with pytest.raises(ValidationError):
        await use_case.execute(
            SetMoodCommand(user_id=1, day=date(2026, 9, 16), level=MoodLevel.GOOD),
            today=TUESDAY,
        )


async def test_a_deactivated_teammate_no_longer_posts() -> None:
    use_case, _ = build()

    with pytest.raises(ForbiddenActionError):
        await use_case.execute(
            SetMoodCommand(user_id=2, day=TUESDAY, level=MoodLevel.GOOD), today=TUESDAY
        )


async def test_an_unknown_user_is_not_found() -> None:
    use_case, _ = build()

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(
            SetMoodCommand(user_id=99, day=TUESDAY, level=MoodLevel.GOOD), today=TUESDAY
        )


async def test_a_teammate_takes_back_the_mood_of_the_day() -> None:
    use_case, moods = build([Mood(id=1, user_id=1, day=TUESDAY, level=MoodLevel.BAD)])
    clear = ClearMoodUseCase(users=InMemoryUserRepository([ALICE, GONE]), moods=moods)

    await clear.execute(ClearMoodCommand(user_id=1, day=TUESDAY), today=TUESDAY)

    assert await moods.get(1, TUESDAY) is None


async def test_taking_back_a_day_one_never_answered_is_harmless() -> None:
    _, moods = build()
    clear = ClearMoodUseCase(users=InMemoryUserRepository([ALICE, GONE]), moods=moods)

    await clear.execute(ClearMoodCommand(user_id=1, day=TUESDAY), today=TUESDAY)

    assert await moods.get(1, TUESDAY) is None


async def test_a_closed_day_can_no_longer_be_taken_back() -> None:
    """The window governs both ways: what one can no longer write, one can no
    longer unwrite. Otherwise a fortnight could be emptied after the fact."""
    _, moods = build(
        [Mood(id=1, user_id=1, day=date(2026, 9, 11), level=MoodLevel.BAD)]
    )
    clear = ClearMoodUseCase(users=InMemoryUserRepository([ALICE, GONE]), moods=moods)

    with pytest.raises(ValidationError):
        await clear.execute(
            ClearMoodCommand(user_id=1, day=date(2026, 9, 11)), today=TUESDAY
        )

    assert await moods.get(1, date(2026, 9, 11)) is not None


async def test_a_deactivated_teammate_takes_nothing_back() -> None:
    _, moods = build([Mood(id=1, user_id=2, day=TUESDAY, level=MoodLevel.BAD)])
    clear = ClearMoodUseCase(users=InMemoryUserRepository([ALICE, GONE]), moods=moods)

    with pytest.raises(ForbiddenActionError):
        await clear.execute(ClearMoodCommand(user_id=2, day=TUESDAY), today=TUESDAY)

"""Assembling the Synthèse d'activité for one window."""

from datetime import date

import pytest

from src.modules.activity_summary.application.dtos.activity_summary_dto import (
    ActivitySummaryQuery,
)
from src.modules.activity_summary.application.use_cases.get_activity_summary import (
    GetActivitySummaryUseCase,
)
from src.modules.activity_summary.domain.repositories.activity_summary_repository import (
    DeclaredDays,
    MissionRecord,
)
from src.modules.calendar.domain.entities.period import Period, PeriodRange
from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus
from src.modules.users.domain.entities.user import Role, User
from tests.helpers.in_memory_repositories import (
    InMemoryActivitySummaryRepository,
    InMemoryUserRepository,
)

TODAY = date(2026, 9, 17)
# Monday 7 to Sunday 13 September 2026, and the week before it.
LAST_WEEK = Period.of(PeriodRange.LAST_WEEK, TODAY)
THE_WEEK_BEFORE = LAST_WEEK.previous()


def a_user(user_id: int, display_name: str) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"{display_name.lower()}@waat.fr",
        display_name=display_name,
        role=Role.TEAMMATE,
    )


def a_mission(project_id: int, label: str) -> MissionRecord:
    return MissionRecord(
        project_id=project_id,
        label=label,
        kind=ProjectKind.PROJECT,
        status=ProjectStatus.DEVELOPMENT,
        category=None,
        parent_id=None,
    )


def a_use_case(
    users: list[User],
    missions: list[MissionRecord],
    declared: dict[str, list[DeclaredDays]],
) -> GetActivitySummaryUseCase:
    return GetActivitySummaryUseCase(
        users=InMemoryUserRepository(users),
        activity=InMemoryActivitySummaryRepository(
            declared=declared, missions=missions
        ),
    )


@pytest.mark.asyncio
async def test_the_summary_covers_the_window_that_was_asked_for() -> None:
    use_case = a_use_case([a_user(1, "Alice")], [], {})

    summary = await use_case.execute(
        ActivitySummaryQuery(range_=PeriodRange.LAST_WEEK, today=TODAY)
    )

    assert summary.period.start == date(2026, 9, 7)
    assert summary.period.end == date(2026, 9, 13)


@pytest.mark.asyncio
async def test_the_whole_team_becomes_columns() -> None:
    use_case = a_use_case([a_user(1, "Alice"), a_user(2, "Bob")], [], {})

    summary = await use_case.execute(
        ActivitySummaryQuery(range_=PeriodRange.LAST_WEEK, today=TODAY)
    )

    assert [someone.display_name for someone in summary.contributors] == [
        "Alice",
        "Bob",
    ]


@pytest.mark.asyncio
async def test_declared_days_land_on_their_mission() -> None:
    use_case = a_use_case(
        [a_user(1, "Alice")],
        [a_mission(1, "WAATcher")],
        {
            InMemoryActivitySummaryRepository.key(LAST_WEEK): [
                DeclaredDays(project_id=1, user_id=1, days=3.0)
            ]
        },
    )

    summary = await use_case.execute(
        ActivitySummaryQuery(range_=PeriodRange.LAST_WEEK, today=TODAY)
    )

    assert summary.projects[0].label == "WAATcher"
    assert summary.projects[0].days == 3.0


@pytest.mark.asyncio
async def test_the_window_before_is_read_to_say_what_moved() -> None:
    use_case = a_use_case(
        [a_user(1, "Alice")],
        [a_mission(1, "WAATcher")],
        {
            InMemoryActivitySummaryRepository.key(LAST_WEEK): [
                DeclaredDays(project_id=1, user_id=1, days=5.0)
            ],
            InMemoryActivitySummaryRepository.key(THE_WEEK_BEFORE): [
                DeclaredDays(project_id=1, user_id=1, days=2.0)
            ],
        },
    )

    summary = await use_case.execute(
        ActivitySummaryQuery(range_=PeriodRange.LAST_WEEK, today=TODAY)
    )

    assert summary.projects[0].movement == 3.0


@pytest.mark.asyncio
async def test_a_week_of_five_working_days_expects_five_of_each_person() -> None:
    use_case = a_use_case([a_user(1, "Alice"), a_user(2, "Bob")], [], {})

    summary = await use_case.execute(
        ActivitySummaryQuery(range_=PeriodRange.LAST_WEEK, today=TODAY)
    )

    assert summary.expected_days == 10.0
    assert summary.coverage == 0.0

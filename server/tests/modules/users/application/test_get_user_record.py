"""What the panel reads on a teammate: their missions, their time, their months."""

from datetime import date

import pytest

from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.months.domain.entities.month import Month, MonthState
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.users.application.dtos.user_record_dto import GetUserRecordQuery
from src.modules.users.application.use_cases.get_user_record import GetUserRecordUseCase
from src.modules.users.domain.entities.rhythm import Rhythm
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryEntryRepository,
    InMemoryMonthRepository,
    InMemoryProjectAssigneeRepository,
    InMemoryProjectRepository,
    InMemoryRhythmRepository,
    InMemoryUserRepository,
)

TODAY = date(2026, 9, 17)
TEAMMATE_ID = 7

WAATCHER = Project(
    id=1, label="WAATcher", kind=ProjectKind.PROJECT, status=ProjectStatus.DEVELOPMENT
)
GANESH = Project(
    id=2, label="Ganesh", kind=ProjectKind.PROJECT, status=ProjectStatus.SCOPING
)
LEAVE = Project(id=3, label="Congés", kind=ProjectKind.OFF_PROJECT, status=None)
RETIRED = Project(
    id=4,
    label="SALSA",
    kind=ProjectKind.PROJECT,
    status=ProjectStatus.OPERATIONS,
    is_active=False,
)


def teammate() -> User:
    return User(
        id=TEAMMATE_ID,
        entra_oid="oid-7",
        email="l.chen@waat.fr",
        display_name="L. Chen",
        role=Role.TEAMMATE,
    )


def entry(day: date, project_id: int, value: float = 1.0) -> Entry:
    return Entry(
        id=None,
        user_id=TEAMMATE_ID,
        project_id=project_id,
        day=day,
        value=DayValue(value),
    )


def build(
    entries: list[Entry] | None = None,
    months: list[Month] | None = None,
    assignments: dict[tuple[int, ProjectRole], list[int]] | None = None,
    users: list[User] | None = None,
    rhythms: list[Rhythm] | None = None,
) -> GetUserRecordUseCase:
    return GetUserRecordUseCase(
        users=InMemoryUserRepository(users if users is not None else [teammate()]),
        projects=InMemoryProjectRepository([WAATCHER, GANESH, LEAVE, RETIRED]),
        assignees=InMemoryProjectAssigneeRepository(assignments or {}),
        entries=InMemoryEntryRepository(entries or []),
        months=InMemoryMonthRepository(months or []),
        rhythms=InMemoryRhythmRepository(rhythms or []),
    )


async def read(use_case: GetUserRecordUseCase):
    return await use_case.execute(GetUserRecordQuery(user_id=TEAMMATE_ID, today=TODAY))


async def test_an_unknown_teammate_has_no_record() -> None:
    use_case = build(users=[])

    with pytest.raises(EntityNotFoundError):
        await read(use_case)


async def test_the_missions_one_is_attached_to_come_back_named() -> None:
    use_case = build(
        assignments={
            (WAATCHER.id, ProjectRole.CONTRIBUTOR): [TEAMMATE_ID],
            (GANESH.id, ProjectRole.LEAD): [TEAMMATE_ID],
        }
    )

    record = await read(use_case)

    assert [(m.label, m.is_lead) for m in record.missions] == [
        ("Ganesh", True),
        ("WAATcher", False),
    ]


async def test_holding_both_roles_on_a_mission_lists_it_once() -> None:
    use_case = build(
        assignments={
            (WAATCHER.id, ProjectRole.CONTRIBUTOR): [TEAMMATE_ID],
            (WAATCHER.id, ProjectRole.LEAD): [TEAMMATE_ID],
        }
    )

    record = await read(use_case)

    assert [(m.label, m.is_lead) for m in record.missions] == [("WAATcher", True)]


async def test_an_archived_mission_is_no_longer_something_one_works_on() -> None:
    use_case = build(assignments={(RETIRED.id, ProjectRole.CONTRIBUTOR): [TEAMMATE_ID]})

    record = await read(use_case)

    assert record.missions == []


async def test_somebody_elses_assignments_are_not_read() -> None:
    use_case = build(assignments={(WAATCHER.id, ProjectRole.CONTRIBUTOR): [99]})

    record = await read(use_case)

    assert record.missions == []


async def test_the_declared_window_names_the_missions_and_adds_them_up() -> None:
    use_case = build(
        entries=[
            entry(date(2026, 9, 14), WAATCHER.id),
            entry(date(2026, 9, 15), WAATCHER.id, value=0.5),
            entry(date(2026, 9, 15), LEAVE.id, value=0.5),
        ]
    )

    record = await read(use_case)

    assert record.declared.since == date(2026, 8, 19)
    assert record.declared.until == TODAY
    assert record.declared.days == 2.0
    assert [(line.label, line.days) for line in record.declared.missions] == [
        ("WAATcher", 1.5),
        ("Congés", 0.5),
    ]


async def test_off_project_time_says_it_is_off_project() -> None:
    use_case = build(entries=[entry(date(2026, 9, 15), LEAVE.id)])

    record = await read(use_case)

    assert [line.is_off_project for line in record.declared.missions] == [True]


async def test_an_archived_mission_still_says_where_the_time_went() -> None:
    use_case = build(entries=[entry(date(2026, 9, 15), RETIRED.id)])

    record = await read(use_case)

    assert [line.label for line in record.declared.missions] == ["SALSA"]


async def test_time_older_than_the_window_is_not_declared_time_any_more() -> None:
    use_case = build(entries=[entry(date(2026, 6, 15), WAATCHER.id)])

    record = await read(use_case)

    assert record.declared.missions == []
    assert record.declared.days == 0


async def test_the_months_come_back_newest_first_over_six_months() -> None:
    use_case = build()

    record = await read(use_case)

    assert [filling.month for filling in record.months] == [
        date(2026, 9, 1),
        date(2026, 8, 1),
        date(2026, 7, 1),
        date(2026, 6, 1),
        date(2026, 5, 1),
        date(2026, 4, 1),
    ]


async def test_a_month_carries_what_was_declared_on_it_and_its_state() -> None:
    use_case = build(
        entries=[
            entry(date(2026, 8, 3), WAATCHER.id),
            entry(date(2026, 8, 4), WAATCHER.id, value=0.5),
        ],
        months=[
            Month(
                user_id=TEAMMATE_ID,
                month=date(2026, 8, 1),
                state=MonthState.VALIDATED,
                validated_at=None,
                validated_by=1,
            )
        ],
    )

    record = await read(use_case)
    august = record.months[1]

    assert august.delivered == 1.5
    assert august.state is MonthState.VALIDATED


async def test_a_month_a_colleague_validated_is_not_read_as_ones_own() -> None:
    use_case = build(
        months=[
            Month(
                user_id=99,
                month=date(2026, 8, 1),
                state=MonthState.VALIDATED,
                validated_by=1,
            )
        ]
    )

    record = await read(use_case)

    assert all(filling.state is MonthState.OPEN for filling in record.months)


async def test_the_record_carries_the_rhythm_in_force() -> None:
    record = await read(
        build(
            rhythms=[
                Rhythm(
                    id=None,
                    user_id=TEAMMATE_ID,
                    pattern=WeekPattern(wednesday=0.0),
                    effective_from=date(2026, 3, 1),
                )
            ]
        )
    )

    assert record.rhythm is not None
    assert record.rhythm.pattern.days_per_week == 4.0
    assert record.rhythm.effective_from == date(2026, 3, 1)


async def test_a_record_carries_no_rhythm_until_one_is_declared() -> None:
    # Which reads as full time everywhere a figure is computed.
    record = await read(build())

    assert record.rhythm is None


async def test_a_rhythm_opening_later_is_not_the_one_in_force() -> None:
    record = await read(
        build(
            rhythms=[
                Rhythm(
                    id=None,
                    user_id=TEAMMATE_ID,
                    pattern=WeekPattern(wednesday=0.0),
                    effective_from=date(2026, 11, 1),
                )
            ]
        )
    )

    assert record.rhythm is None

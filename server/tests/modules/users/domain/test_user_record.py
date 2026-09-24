"""What the register reads back on one teammate: their time, their months."""

from datetime import date, datetime

from src.modules.entries.domain.entities.entry import DayValue, Entry
from src.modules.months.domain.entities.month import Month, MonthState
from src.modules.users.domain.services.user_record import (
    days_by_project,
    declaration_window,
    month_fillings,
    months_looked_back,
)

TODAY = date(2026, 9, 17)


def entry(day: date, project_id: int = 1, value: float = 1.0) -> Entry:
    return Entry(
        id=None,
        user_id=7,
        project_id=project_id,
        activity_id=None,
        day=day,
        value=DayValue(value),
    )


def test_the_declaration_window_ends_today_and_covers_thirty_days() -> None:
    since, until = declaration_window(TODAY)

    assert until == TODAY
    # Thirty days counting today, not thirty days before it.
    assert since == date(2026, 8, 19)


def test_days_by_project_adds_up_what_each_mission_received() -> None:
    since, until = declaration_window(TODAY)

    declared = days_by_project(
        [
            entry(date(2026, 9, 14), project_id=1),
            entry(date(2026, 9, 15), project_id=1, value=0.5),
            entry(date(2026, 9, 15), project_id=2, value=0.5),
        ],
        since,
        until,
    )

    assert [(line.project_id, line.days) for line in declared] == [(1, 1.5), (2, 0.5)]


def test_days_by_project_puts_the_heaviest_mission_first() -> None:
    since, until = declaration_window(TODAY)

    declared = days_by_project(
        [
            entry(date(2026, 9, 14), project_id=1, value=0.5),
            entry(date(2026, 9, 15), project_id=2),
            entry(date(2026, 9, 16), project_id=2),
        ],
        since,
        until,
    )

    assert [line.project_id for line in declared] == [2, 1]


def test_days_by_project_ignores_what_falls_outside_the_window() -> None:
    since, until = declaration_window(TODAY)

    declared = days_by_project(
        [
            entry(date(2026, 7, 1), project_id=1),
            entry(date(2026, 9, 30), project_id=2),
            entry(date(2026, 9, 15), project_id=3),
        ],
        since,
        until,
    )

    assert [line.project_id for line in declared] == [3]


def test_months_looked_back_runs_from_the_month_running_backwards() -> None:
    assert months_looked_back(TODAY, count=3) == [
        date(2026, 9, 1),
        date(2026, 8, 1),
        date(2026, 7, 1),
    ]


def test_months_looked_back_crosses_the_year_boundary() -> None:
    assert months_looked_back(date(2026, 2, 3), count=3) == [
        date(2026, 2, 1),
        date(2026, 1, 1),
        date(2025, 12, 1),
    ]


def test_a_month_tells_delivered_from_forecast() -> None:
    [september] = month_fillings(
        entries=[
            entry(date(2026, 9, 15)),
            entry(date(2026, 9, 17), value=0.5),
            # Posted ahead: a day of the plan, not a day worked.
            entry(date(2026, 9, 25)),
        ],
        states=[],
        today=TODAY,
        count=1,
    )

    assert september.delivered == 1.5
    assert september.forecast == 1.0


def test_a_month_running_is_measured_against_the_days_already_gone() -> None:
    [september] = month_fillings(entries=[], states=[], today=TODAY, count=1)

    assert september.working_days == 22
    # 1 to 17 September, weekends aside.
    assert september.elapsed_working_days == 13


def test_a_month_already_over_counts_every_one_of_its_working_days() -> None:
    _, august = month_fillings(entries=[], states=[], today=TODAY, count=2)

    assert august.month == date(2026, 8, 1)
    assert august.elapsed_working_days == august.working_days == 21


def test_a_month_nobody_validated_reads_as_open() -> None:
    [september] = month_fillings(entries=[], states=[], today=TODAY, count=1)

    assert september.state is MonthState.OPEN
    assert september.validated_at is None


def test_a_validated_month_says_so_and_when() -> None:
    validated_at = datetime(2026, 9, 1, 9, 30)
    _, august = month_fillings(
        entries=[],
        states=[
            Month(
                user_id=7,
                month=date(2026, 8, 1),
                state=MonthState.VALIDATED,
                validated_at=validated_at,
                validated_by=1,
            )
        ],
        today=TODAY,
        count=2,
    )

    assert august.state is MonthState.VALIDATED
    assert august.validated_at == validated_at


def test_a_month_outside_the_span_is_left_out() -> None:
    fillings = month_fillings(
        entries=[entry(date(2026, 3, 2))],
        states=[],
        today=TODAY,
        count=2,
    )

    assert [filling.month for filling in fillings] == [
        date(2026, 9, 1),
        date(2026, 8, 1),
    ]
    assert all(filling.delivered == 0 for filling in fillings)

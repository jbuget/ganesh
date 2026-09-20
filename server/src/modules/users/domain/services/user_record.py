"""What the register holds on one teammate: their time, and their months.

The mission sheet says who works on a mission; this says what one person
works on, what they declared lately, and where their months stand. The same
facts, read from the other side — and read here rather than in the use case,
so that the rules a reader leans on are tested on their own.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from src.modules.calendar.domain.services.working_days import DayKind, days_of_month
from src.modules.entries.domain.entities.entry import Entry
from src.modules.months.domain.entities.month import Month, MonthState
from src.modules.months.domain.services.month_period import first_day_of

#: How far back the panel looks. Six months is what a departure or a late
#: month is checked over; a year of rows would bury the two that matter.
MONTHS_LOOKED_BACK = 6

#: The window declared time is read over. Rolling rather than the month
#: running: read on the 2nd, a month running says almost nothing.
DECLARATION_WINDOW_DAYS = 30


@dataclass(frozen=True)
class DeclaredOnProject:
    """Days one person booked on one mission over the window."""

    project_id: int
    days: float


@dataclass(frozen=True)
class MonthFilling:
    """How full a month is, and whether it is closed.

    `working_days` is what the month calls for in all, `elapsed_working_days`
    what it has called for so far: a month running compares against the days
    already gone, or every reading before the 30th would look like a delay.
    """

    month: date
    delivered: float
    forecast: float
    working_days: int
    elapsed_working_days: int
    state: MonthState
    validated_at: datetime | None


def declaration_window(
    today: date, days: int = DECLARATION_WINDOW_DAYS
) -> tuple[date, date]:
    """The window declared time is read over, today included.

    Thirty days counting today: a window that ended yesterday would drop the
    half day somebody entered this morning, which is the one they would look
    for first.
    """
    return today - timedelta(days=days - 1), today


def days_by_project(
    entries: Iterable[Entry], since: date, until: date
) -> list[DeclaredOnProject]:
    """What each mission received over the window, heaviest first.

    Everything inside the window counts. It ends today, so nothing in it is
    posted ahead: there is no forecast to tell apart here.
    """
    totals: dict[int, float] = {}
    for entry in entries:
        if since <= entry.day <= until:
            totals[entry.project_id] = round(
                totals.get(entry.project_id, 0.0) + float(entry.value), 2
            )

    return [
        DeclaredOnProject(project_id=project_id, days=days)
        for project_id, days in sorted(
            totals.items(), key=lambda line: (-line[1], line[0])
        )
    ]


def months_looked_back(today: date, count: int = MONTHS_LOOKED_BACK) -> list[date]:
    """The months the panel shows, from the one running backwards."""
    months = []
    cursor = first_day_of(today)
    for _ in range(count):
        months.append(cursor)
        cursor = first_day_of(cursor - timedelta(days=1))
    return months


def _working_days(month: date) -> list[date]:
    return [
        day.day
        for day in days_of_month(month.year, month.month)
        if day.kind is DayKind.WORKING
    ]


def month_fillings(
    entries: Iterable[Entry],
    states: Iterable[Month],
    today: date,
    count: int = MONTHS_LOOKED_BACK,
) -> list[MonthFilling]:
    """The last months of one person: how full each is, and whether it is closed.

    A month nobody touched still shows a line. That a month is empty is what
    one opens this for, and a list that skipped it would answer « nothing to
    report » to the only question worth asking.
    """
    by_month = {first_day_of(state.month): state for state in states}

    delivered: dict[date, float] = {}
    forecast: dict[date, float] = {}
    for entry in entries:
        side = forecast if entry.is_forecast(today) else delivered
        month = first_day_of(entry.day)
        side[month] = round(side.get(month, 0.0) + float(entry.value), 2)

    fillings = []
    for month in months_looked_back(today, count):
        working = _working_days(month)
        state = by_month.get(month)
        fillings.append(
            MonthFilling(
                month=month,
                delivered=delivered.get(month, 0.0),
                forecast=forecast.get(month, 0.0),
                working_days=len(working),
                elapsed_working_days=sum(1 for day in working if day <= today),
                state=state.state if state else MonthState.OPEN,
                validated_at=state.validated_at if state else None,
            )
        )
    return fillings

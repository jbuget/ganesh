"""Builds a month's entry grid: missions as rows, days as columns."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.calendar.domain.services.working_days import (
    CalendarDay,
    days_of_month,
    working_days_count,
)
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.domain.repositories.user_mission_repository import (
    UserMissionRepository,
)
from src.modules.entries.domain.services.day_total import day_total, exceeds_one_day
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.months.domain.services.month_period import first_day_of
from src.modules.projects.domain.entities.project import ProjectKind
from src.modules.projects.domain.repositories.activity_repository import (
    ActivityRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


@dataclass(frozen=True)
class GetMonthGridQuery:
    """Asks for a user's grid for one month."""

    user_id: int
    month: date
    today: date | None = None


#: What names a row: the mission, and the activity under it. Null activity is
#: off-project work, which is declared on directly and stands on its own line.
RowKey = tuple[int, int | None]


@dataclass
class GridRow:
    """One grid row: an activity of a mission, and its entries for the month."""

    project_id: int
    activity_id: int | None
    #: What names the row — the activity, or the mission when there is none.
    label: str
    #: The mission the row hangs under, so the grid can group its rows.
    project_label: str
    kind: ProjectKind
    estimated_days: float | None
    values: dict[date, float] = field(default_factory=dict)
    actual_total: float = 0.0
    forecast_total: float = 0.0
    #: Consumed on this activity across every month and every teammate. The
    #: only figure comparable to `estimated_days`, which now covers the
    #: activity rather than the mission: an estimate counted in build days
    #: stops meaning anything once the days of every trade are taken off it.
    total_consumed_days: float = 0.0

    @property
    def total(self) -> float:
        """Month total, delivered and forecast together."""
        return round(self.actual_total + self.forecast_total, 2)


@dataclass
class DayTotal:
    """Total entered on one day, across every project."""

    day: date
    total: float
    exceeds_capacity: bool


@dataclass
class MonthGrid:
    """The complete grid for a month."""

    user_id: int
    month: date
    days: list[CalendarDay]
    rows: list[GridRow]
    day_totals: list[DayTotal]
    working_days: int
    is_writable: bool

    @property
    def actual_total(self) -> float:
        return round(sum(row.actual_total for row in self.rows), 2)

    @property
    def forecast_total(self) -> float:
        return round(sum(row.forecast_total for row in self.rows), 2)


class GetMonthGridUseCase:
    """Assembles the grid the entry screen displays."""

    def __init__(
        self,
        users: UserRepository,
        projects: ProjectRepository,
        activities: ActivityRepository,
        entries: EntryRepository,
        months: MonthRepository,
        user_missions: UserMissionRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._activities = activities
        self._entries = entries
        self._months = months
        self._user_missions = user_missions

    async def _row_consumption(self, key: RowKey, today: date) -> float:
        """Time already consumed on this row, forecast excluded.

        Read on the activity, because that is what the estimate covers now.
        Off-project work has no activity and answers for the mission, which
        is the same thing: it carries no other row.
        """
        project_id, activity_id = key
        entries = await self._entries.list_for_project(project_id)
        return round(
            sum(
                float(e.value)
                for e in entries
                if e.activity_id == activity_id and not e.is_forecast(today)
            ),
            2,
        )

    async def _empty_row(self, key: RowKey) -> GridRow | None:
        """The row opens with, before any time lands on it.

        A row naming an activity that no longer answers is dropped rather
        than drawn under the mission's name: it would read as a row one could
        declare on, and the write would be refused.
        """
        project_id, activity_id = key
        project = await self._projects.get_by_id(project_id)
        if project is None:
            return None

        label = project.label
        estimated_days = project.estimated_days
        if activity_id is not None:
            activity = await self._activities.get_by_id(activity_id)
            if activity is None or activity.project_id != project_id:
                return None
            label = activity.label
            estimated_days = activity.estimated_days

        return GridRow(
            project_id=project_id,
            activity_id=activity_id,
            label=label,
            project_label=project.label,
            kind=project.kind,
            estimated_days=estimated_days,
        )

    async def _rows_of_entered_time(
        self, user_id: int, month: date, today: date
    ) -> dict[RowKey, GridRow]:
        """One row per activity with time on it, delivered told from forecast."""
        rows: dict[RowKey, GridRow] = {}
        for entry in await self._entries.list_for_month(user_id, month):
            key: RowKey = (entry.project_id, entry.activity_id)
            row = rows.get(key)
            if row is None:
                row = await self._empty_row(key)
                if row is None:
                    continue
                rows[key] = row

            row.values[entry.day] = float(entry.value)
            if entry.is_forecast(today):
                row.forecast_total = round(row.forecast_total + float(entry.value), 2)
            else:
                row.actual_total = round(row.actual_total + float(entry.value), 2)
        return rows

    async def _add_rows_lined_up(
        self, rows: dict[RowKey, GridRow], user_id: int, month: date
    ) -> None:
        """Rows put on the month with nothing entered on them yet.

        They hold an empty row, which says « not entered yet » and never
        « nothing done ». A row that already carries time is already there.
        """
        for key in await self._user_missions.list_for_month(user_id, month):
            if key in rows:
                continue
            row = await self._empty_row(key)
            if row is not None:
                rows[key] = row

    def _day_totals(
        self, calendar_days: list[CalendarDay], rows: dict[RowKey, GridRow]
    ) -> list[DayTotal]:
        """What each day of the month adds up to, across every mission."""
        totals = []
        for calendar_day in calendar_days:
            total = day_total(
                row.values[calendar_day.day]
                for row in rows.values()
                if calendar_day.day in row.values
            )
            totals.append(
                DayTotal(
                    day=calendar_day.day,
                    total=total,
                    exceeds_capacity=exceeds_one_day([total]),
                )
            )
        return totals

    async def execute(self, query: GetMonthGridQuery) -> MonthGrid:
        if await self._users.get_by_id(query.user_id) is None:
            raise EntityNotFoundError("The user cannot be found.")

        month = first_day_of(query.month)
        today = query.today or clock.today()
        calendar_days = days_of_month(month.year, month.month)

        rows = await self._rows_of_entered_time(query.user_id, month, today)
        await self._add_rows_lined_up(rows, query.user_id, month)
        for key, row in rows.items():
            row.total_consumed_days = await self._row_consumption(key, today)

        month_status = await self._months.get(query.user_id, month)

        return MonthGrid(
            user_id=query.user_id,
            month=month,
            days=calendar_days,
            # Grouped by mission, then by activity: the grid reads as the
            # list of missions somebody works on, each cut into its trades.
            rows=sorted(rows.values(), key=lambda r: (r.project_label, r.label)),
            day_totals=self._day_totals(calendar_days, rows),
            working_days=working_days_count(month.year, month.month),
            is_writable=month_status.is_writable if month_status else True,
        )

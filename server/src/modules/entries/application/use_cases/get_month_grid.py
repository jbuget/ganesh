"""Builds a month's entry grid: missions as rows, days as columns."""

from dataclasses import dataclass, field
from datetime import date

from src.modules.calendar.domain.services.working_days import (
    CalendarDay,
    days_of_month,
    working_days_count,
)
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.domain.services.day_total import day_total, exceeds_one_day
from src.modules.months.domain.repositories.month_repository import MonthRepository
from src.modules.projects.domain.entities.project import ProjectKind
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.exceptions.domain_exceptions import EntityNotFoundError


@dataclass(frozen=True)
class GetMonthGridQuery:
    """Asks for a user's grid for one month."""

    user_id: int
    month: date
    today: date | None = None


@dataclass
class GridRow:
    """One grid row: a mission and its entries for the month."""

    project_id: int
    label: str
    kind: ProjectKind
    estimated_days: float | None
    values: dict[date, float] = field(default_factory=dict)
    actual_total: float = 0.0
    forecast_total: float = 0.0
    #: Consumed across the whole project, every month and every developer.
    #: The only figure comparable to `estimated_days`, which covers the project.
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
        entries: EntryRepository,
        months: MonthRepository,
    ) -> None:
        self._users = users
        self._projects = projects
        self._entries = entries
        self._months = months

    async def _project_consumption(self, project_id: int, today: date) -> float:
        """Time already consumed on a project, forecast excluded."""
        entries = await self._entries.list_for_project(project_id)
        return round(
            sum(float(e.value) for e in entries if not e.is_forecast(today)), 2
        )

    async def execute(self, query: GetMonthGridQuery) -> MonthGrid:
        if await self._users.get_by_id(query.user_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        month = query.month.replace(day=1)
        today = query.today or date.today()

        calendar_days = days_of_month(month.year, month.month)
        month_entries = await self._entries.list_for_month(query.user_id, month)

        rows: dict[int, GridRow] = {}
        for entry in month_entries:
            row = rows.get(entry.project_id)
            if row is None:
                project = await self._projects.get_by_id(entry.project_id)
                if project is None:
                    continue
                row = GridRow(
                    project_id=entry.project_id,
                    label=project.label,
                    kind=project.kind,
                    estimated_days=project.estimated_days,
                )
                rows[entry.project_id] = row

            row.values[entry.day] = float(entry.value)
            if entry.is_forecast(today):
                row.forecast_total = round(row.forecast_total + float(entry.value), 2)
            else:
                row.actual_total = round(row.actual_total + float(entry.value), 2)

        for row in rows.values():
            row.total_consumed_days = await self._project_consumption(
                row.project_id, today
            )

        day_totals = [
            DayTotal(
                day=calendar_day.day,
                total=(
                    total := day_total(
                        row.values[calendar_day.day]
                        for row in rows.values()
                        if calendar_day.day in row.values
                    )
                ),
                exceeds_capacity=exceeds_one_day([total]),
            )
            for calendar_day in calendar_days
        ]

        month_status = await self._months.get(query.user_id, month)

        return MonthGrid(
            user_id=query.user_id,
            month=month,
            days=calendar_days,
            rows=sorted(rows.values(), key=lambda r: r.label),
            day_totals=day_totals,
            working_days=working_days_count(month.year, month.month),
            is_writable=month_status.is_writable if month_status else True,
        )

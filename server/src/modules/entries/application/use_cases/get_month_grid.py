"""Construit la matrice de saisie d'un mois : missions en lignes, jours en colonnes."""

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
    """Demande la matrice d'un utilisateur pour un mois."""

    user_id: int
    mois: date
    today: date | None = None


@dataclass
class GridRow:
    """Une ligne de la matrice : une mission et ses saisies du mois."""

    project_id: int
    label: str
    kind: ProjectKind
    estime_j: float | None
    values: dict[date, float] = field(default_factory=dict)
    total_realise: float = 0.0
    total_prevu: float = 0.0

    @property
    def total(self) -> float:
        """Total du mois, realise et previsionnel confondus."""
        return round(self.total_realise + self.total_prevu, 2)


@dataclass
class DayTotal:
    """Total saisi sur une journee, tous projets confondus."""

    jour: date
    total: float
    exceeds_capacity: bool


@dataclass
class MonthGrid:
    """La matrice complete d'un mois."""

    user_id: int
    mois: date
    days: list[CalendarDay]
    rows: list[GridRow]
    day_totals: list[DayTotal]
    working_days: int
    is_writable: bool

    @property
    def total_realise(self) -> float:
        return round(sum(row.total_realise for row in self.rows), 2)

    @property
    def total_prevu(self) -> float:
        return round(sum(row.total_prevu for row in self.rows), 2)


class GetMonthGridUseCase:
    """Assemble la matrice affichee par l'ecran de saisie."""

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

    async def execute(self, query: GetMonthGridQuery) -> MonthGrid:
        if await self._users.get_by_id(query.user_id) is None:
            raise EntityNotFoundError("Utilisateur inconnu.")

        mois = query.mois.replace(day=1)
        today = query.today or date.today()

        calendar_days = days_of_month(mois.year, mois.month)
        month_entries = await self._entries.list_for_month(query.user_id, mois)

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
                    estime_j=project.estime_j,
                )
                rows[entry.project_id] = row

            row.values[entry.jour] = float(entry.valeur)
            if entry.is_forecast(today):
                row.total_prevu = round(row.total_prevu + float(entry.valeur), 2)
            else:
                row.total_realise = round(row.total_realise + float(entry.valeur), 2)

        day_totals = [
            DayTotal(
                jour=day.jour,
                total=(
                    total := day_total(
                        row.values[day.jour]
                        for row in rows.values()
                        if day.jour in row.values
                    )
                ),
                exceeds_capacity=exceeds_one_day([total]),
            )
            for day in calendar_days
        ]

        month = await self._months.get(query.user_id, mois)

        return MonthGrid(
            user_id=query.user_id,
            mois=mois,
            days=calendar_days,
            rows=sorted(rows.values(), key=lambda r: r.label),
            day_totals=day_totals,
            working_days=working_days_count(mois.year, mois.month),
            is_writable=month.is_writable if month else True,
        )

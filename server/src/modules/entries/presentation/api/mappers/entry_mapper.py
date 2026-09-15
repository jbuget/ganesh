"""Traduction des objets applicatifs en schemas d'API."""

from src.modules.entries.application.use_cases.get_month_grid import MonthGrid
from src.modules.entries.domain.entities.entry import Entry
from src.modules.entries.presentation.api.schemas.entry_schemas import (
    CalendarDayResponse,
    DayTotalResponse,
    EntryResponse,
    GridRowResponse,
    MonthGridResponse,
)


def to_entry_response(entry: Entry) -> EntryResponse:
    return EntryResponse(
        project_id=entry.project_id, jour=entry.jour, valeur=float(entry.valeur)
    )


def to_month_grid_response(grid: MonthGrid) -> MonthGridResponse:
    return MonthGridResponse(
        user_id=grid.user_id,
        mois=grid.mois,
        days=[
            CalendarDayResponse(
                jour=day.jour,
                kind=day.kind.value,
                label=day.label,
                is_off_day=day.is_off_day,
            )
            for day in grid.days
        ],
        rows=[
            GridRowResponse(
                project_id=row.project_id,
                label=row.label,
                kind=row.kind,
                estime_j=row.estime_j,
                values=row.values,
                total_realise=row.total_realise,
                total_prevu=row.total_prevu,
                total=row.total,
            )
            for row in grid.rows
        ],
        day_totals=[
            DayTotalResponse(
                jour=total.jour,
                total=total.total,
                exceeds_capacity=total.exceeds_capacity,
            )
            for total in grid.day_totals
        ],
        working_days=grid.working_days,
        is_writable=grid.is_writable,
        total_realise=grid.total_realise,
        total_prevu=grid.total_prevu,
    )

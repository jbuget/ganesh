"""Translating application objects into API schemas."""

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
        project_id=entry.project_id, day=entry.day, value=float(entry.value)
    )


def to_month_grid_response(grid: MonthGrid) -> MonthGridResponse:
    return MonthGridResponse(
        user_id=grid.user_id,
        month=grid.month,
        days=[
            CalendarDayResponse(
                day=day.day,
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
                estimated_days=row.estimated_days,
                values=row.values,
                actual_total=row.actual_total,
                forecast_total=row.forecast_total,
                total=row.total,
                total_consumed_days=row.total_consumed_days,
            )
            for row in grid.rows
        ],
        day_totals=[
            DayTotalResponse(
                day=total.day,
                total=total.total,
                exceeds_capacity=total.exceeds_capacity,
            )
            for total in grid.day_totals
        ],
        working_days=grid.working_days,
        is_writable=grid.is_writable,
        actual_total=grid.actual_total,
        forecast_total=grid.forecast_total,
    )

"""Schemas du calendrier."""

from datetime import date

from pydantic import BaseModel


class CalendarDaySchema(BaseModel):
    """Un jour et sa nature."""

    day: date
    kind: str
    label: str | None = None
    is_off_day: bool


class MonthCalendarResponse(BaseModel):
    """Le calendrier d'un mois."""

    year: int
    month: int
    working_days: int
    days: list[CalendarDaySchema]

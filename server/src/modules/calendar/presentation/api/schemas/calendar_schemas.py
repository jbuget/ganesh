"""Calendar schemas."""

from datetime import date

from pydantic import BaseModel


class CalendarDaySchema(BaseModel):
    """A day and its kind."""

    day: date
    kind: str
    label: str | None = None
    is_off_day: bool


class MonthCalendarResponse(BaseModel):
    """A month's calendar."""

    year: int
    month: int
    working_days: int
    days: list[CalendarDaySchema]

"""Month state schemas."""

from datetime import date, datetime

from pydantic import BaseModel

from src.modules.months.domain.entities.month import MonthState


class MonthResponse(BaseModel):
    """Entry state of a month."""

    user_id: int
    month: date
    state: MonthState
    is_writable: bool
    validated_at: datetime | None
    validated_by: int | None
    reopened_at: datetime | None
    reopened_by: int | None

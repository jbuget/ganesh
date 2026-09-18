"""Business rules that govern writing an entry."""

from datetime import date

from src.modules.calendar.domain.services.working_days import DayKind, classify_day
from src.shared.exceptions.domain_exceptions import ValidationError

LABELS: dict[DayKind, str] = {
    DayKind.WEEKEND: "a weekend",
    DayKind.FERIE: "a public holiday",
}


def ensure_day_is_workable(day: date) -> None:
    """Refuses any entry set on a non-working day.

    The rule lives in the domain, not in the interface: locking the cell on the
    client is a comfort, not a guarantee. The API must refuse the entry
    whoever the caller is.
    """
    kind = classify_day(day)
    if kind is DayKind.OUVRE:
        return
    raise ValidationError(
        f"{day.isoformat()} is {LABELS[kind]}: no entry is possible there."
    )

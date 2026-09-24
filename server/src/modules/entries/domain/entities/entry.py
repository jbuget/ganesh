"""Entry of a quarter of a day, or a multiple of it, on a mission."""

from dataclasses import dataclass
from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.shared.exceptions.domain_exceptions import ValidationError

#: Values that can be entered. An empty cell is not an entry: it does not exist.
#:
#: The quarter — two hours on an eight-hour day — is the grain the grid holds.
#: Halves alone cannot be made to come out right by somebody carrying half a
#: dozen projects, which is the whole reason this list grew.
#:
#: All four are exactly representable in binary, so sums of them stay exact:
#: no drift creeps into a month's total, however many cells it adds up.
ALLOWED_VALUES: tuple[float, ...] = (0.25, 0.5, 0.75, 1.0)


class DayValue(float):
    """The value of an entry: a quarter of a day, or a multiple of it."""

    def __new__(cls, value: float) -> "DayValue":
        if float(value) not in ALLOWED_VALUES:
            raise ValidationError(
                f"An entry is 0.25, 0.5, 0.75 or 1.0, not {value}.",
            )
        return super().__new__(cls, value)


@dataclass
class Entry:
    """The time a user declared, on a mission, on a given day.

    An entry remembers the project status at the moment it is written, which
    makes it possible to measure time consumed per phase.
    """

    id: int | None
    user_id: int
    project_id: int
    day: date
    value: DayValue
    status_at_entry: ProjectStatus | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.value, DayValue):
            self.value = DayValue(self.value)

    def is_forecast(self, today: date) -> bool:
        """An entry set on a future day is a forecast.

        Forecasts must never be pushed to Monday as time spent. Today itself
        counts as delivered.
        """
        return self.day > today

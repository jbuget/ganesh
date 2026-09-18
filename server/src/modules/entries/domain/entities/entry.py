"""Entry of a half day or a full day on a mission."""

from dataclasses import dataclass
from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.shared.exceptions.domain_exceptions import ValidationError

#: Values that can be entered. An empty cell is not an entry: it does not exist.
ALLOWED_VALUES: tuple[float, ...] = (0.5, 1.0)


class DayValue(float):
    """The value of an entry: a half day or a full day."""

    def __new__(cls, value: float) -> "DayValue":
        if float(value) not in ALLOWED_VALUES:
            raise ValidationError(
                f"An entry is 0.5 or 1.0, not {value}.",
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

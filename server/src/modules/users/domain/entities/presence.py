"""The week somebody works, and from where.

Read by the team rather than computed on: nothing here feeds a coverage, a
capacity or a number of days expected. It answers one question — « is Léa in
on Tuesday, and is she at the office? » — and answering it is all it does.

That is what keeps it simple. Nothing reads it back over a past window, so
there is nothing to freeze: no date of effect, no succession, no history to
correct. One says how their ordinary week goes, and says otherwise the day it
changes.
"""

from dataclasses import dataclass, fields
from datetime import date
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import ValidationError

#: Days of the week one declares, in order, from Monday. The week stops on
#: Friday: that nobody works at the weekend is an invariant of the domain.
WEEKDAYS: tuple[str, ...] = ("monday", "tuesday", "wednesday", "thursday", "friday")

SATURDAY = 5


class DayPresence(StrEnum):
    """Where somebody is on one day of an ordinary week."""

    ON_SITE = "ON_SITE"
    REMOTE = "REMOTE"
    AWAY = "AWAY"


@dataclass(frozen=True)
class WeekPresence:
    """An ordinary week: five days, each one somewhere.

    On site every day unless said otherwise. That default is not a stand-in
    for an answer nobody gave: it is the arrangement the team runs on, so it
    is what is true of whoever has said nothing. Declaring a Wednesday at home
    therefore takes one field rather than five.
    """

    monday: DayPresence = DayPresence.ON_SITE
    tuesday: DayPresence = DayPresence.ON_SITE
    wednesday: DayPresence = DayPresence.ON_SITE
    thursday: DayPresence = DayPresence.ON_SITE
    friday: DayPresence = DayPresence.ON_SITE

    def __post_init__(self) -> None:
        for field in fields(self):
            if not isinstance(getattr(self, field.name), DayPresence):
                raise ValidationError(
                    f"A day is spent on site, remotely or away, "
                    f"not {getattr(self, field.name)!r} ({field.name})."
                )

    @property
    def days(self) -> tuple[DayPresence, ...]:
        """The week, Monday first — the order `date.weekday()` counts in."""
        return tuple(getattr(self, name) for name in WEEKDAYS)

    @property
    def days_on_site(self) -> int:
        """Days spent at the office, which is what the team view counts."""
        return sum(1 for day in self.days if day is DayPresence.ON_SITE)

    @property
    def days_present(self) -> int:
        """Days worked at all, wherever from."""
        return sum(1 for day in self.days if day is not DayPresence.AWAY)

    def on(self, day: date) -> DayPresence:
        """Where this person ordinarily is that day. Nowhere at the weekend."""
        return (
            self.days[day.weekday()] if day.weekday() < SATURDAY else DayPresence.AWAY
        )

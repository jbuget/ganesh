"""What an ordinary week expects of one person.

A rhythm is a motif, not a number. « Four days a week » says nothing about
which four, and a public holiday does not fall on a number: whoever never
works on a Monday loses nothing to Whit Monday, whoever never works on a
Friday loses the first of May. Only the motif can tell the two apart.

The week stops on Friday. That nobody works at the weekend is an invariant of
the domain rather than a rhythm, and a pattern that could say otherwise would
let a rhythm contradict it.
"""

from dataclasses import dataclass
from datetime import date

from src.shared.exceptions.domain_exceptions import ValidationError

#: What a day of the motif may be worth. The same values an entry holds: a
#: rhythm expects what the grid is able to receive, and nothing else.
ALLOWED_VALUES: tuple[float, ...] = (0.0, 0.5, 1.0)

#: Days of the week a motif speaks about, in order, from Monday.
WEEKDAYS: tuple[str, ...] = ("monday", "tuesday", "wednesday", "thursday", "friday")


@dataclass(frozen=True)
class WeekPattern:
    """The days of an ordinary week, and what each one is worth.

    Full time unless said otherwise: a motif is read as the exception to the
    ordinary week, so declaring a Wednesday off takes one field, not five.

    A week worth nothing at all is one of them. A parental leave, a
    sabbatical, a week of school: the teammate is still of the team — their
    account stays open, their past months stay readable — and nothing is
    expected of them meanwhile. Counting them at five days is the very lie
    rhythms exist to stop telling, and deactivating their account would say
    something else entirely: that they are gone.

    Nothing here says « until ». A rhythm holds until the next one opens, so
    the end of an absence is declared like any other change.
    """

    monday: float = 1.0
    tuesday: float = 1.0
    wednesday: float = 1.0
    thursday: float = 1.0
    friday: float = 1.0

    def __post_init__(self) -> None:
        for name, value in zip(WEEKDAYS, self.days, strict=True):
            if value not in ALLOWED_VALUES:
                raise ValidationError(
                    f"A day of a rhythm is 0, 0.5 or 1, not {value} ({name}).",
                )

    @property
    def days(self) -> tuple[float, ...]:
        """The motif, Monday first — the order `date.weekday()` counts in."""
        return (self.monday, self.tuesday, self.wednesday, self.thursday, self.friday)

    @property
    def days_per_week(self) -> float:
        """Days an ordinary week expects, holidays aside."""
        return round(sum(self.days), 2)

    def on(self, day: date) -> float:
        """What this rhythm expects on this day. Nothing at the weekend.

        It says what is *expected*, never what is allowed: somebody who does
        not ordinarily work on Wednesdays may swap one for a Thursday, and
        what they declare that week is theirs to declare. The rhythm holds
        the week's total, which a swap leaves untouched.
        """
        motif = self.days
        weekday = day.weekday()
        return motif[weekday] if weekday < len(motif) else 0.0


#: What the application assumes of anyone who has declared nothing — which is
#: what it assumed of everybody before rhythms existed. A default that changes
#: no figure is the only honest one.
FULL_TIME = WeekPattern()

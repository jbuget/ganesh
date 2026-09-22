"""What a window expects of someone, before anything is declared."""

from datetime import date
from typing import Protocol

from src.modules.calendar.domain.entities.period import Period
from src.modules.calendar.domain.entities.week_pattern import FULL_TIME
from src.modules.calendar.domain.services.working_days import working_days_between


class DailyExpectation(Protocol):
    """Anything able to say what one day expects of one person.

    A motif answers it, and so does a history of motifs: a window is counted
    the same way whether it reads somebody who declared a rhythm or somebody
    who never did. Structural on purpose — the calendar names no teammate.
    """

    def on(self, day: date) -> float: ...


def expected_days(period: Period, rhythm: DailyExpectation = FULL_TIME) -> float:
    """Days the window calls for from one person, their rhythm honoured.

    Full time unless a rhythm says otherwise, which is what the application
    assumed of everybody before rhythms existed.

    Counted day by day rather than from a number of days a week: whoever
    never works on a Monday loses nothing to Whit Monday, whoever never works
    on a Friday loses the first of May, and only the motif tells the two
    apart. A week somebody swapped a Wednesday for a Thursday still expects
    the same of them — the swap moves a day, not the total.
    """
    return round(
        sum(rhythm.on(day) for day in working_days_between(period.start, period.end)),
        2,
    )

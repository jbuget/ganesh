"""The milestone: a date a mission is answerable for.

« Livraison du lot 1 », « COPIL de lancement », « bascule RDS ». What it is
called is proper to its mission, which is why it carries a free label and no
type: a closed list would either be too short to name what people actually
post, or it would overlap the phases — and those are dated on their own, at
the moment a card crosses a column. Two answers to one question is exactly
what this entity refuses to create.

It holds two dates, and they are read as a pair. `expected_on` is what the
team announces and is required: a milestone is first of all a day. `reached_on`
is the fact, and is what marks it crossed.

The two are **independent**: early, on the day, and late are all facts worth
recording, and late is the one a sheet exists to show. Binding them would mean
a milestone reached after the day announced could only be recorded by rewriting
the announcement, which loses the very thing steering came to read.
"""

from dataclasses import dataclass
from datetime import date, datetime

from src.shared.exceptions.domain_exceptions import ValidationError
from src.shared.utils import clock


@dataclass
class Milestone:
    """A day a mission is expected at, and the day it got there."""

    id: int | None
    #: The mission it hangs under — a project or one of its work packages.
    #: Never off-project work, which steers nothing and is dated by nobody.
    project_id: int
    label: str
    #: The day announced. Required: a milestone with no date decides nothing
    #: and would only be a line nothing can sort.
    expected_on: date
    #: The day it actually happened. Null until it does.
    reached_on: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.label = self.label.strip()
        if not self.label:
            raise ValidationError("A milestone label cannot be empty.")

        # Nobody crosses a milestone tomorrow. A day still to come is what
        # `expected_on` is for, and recording it as reached would make the
        # sheet announce as done what is merely planned.
        if self.reached_on is not None and self.reached_on > clock.today():
            raise ValidationError(
                f"« {self.label} » cannot have been reached on "
                f"{self.reached_on:%d/%m/%Y}: that day has not come."
            )

    @property
    def is_reached(self) -> bool:
        """Whether the milestone has actually happened."""
        return self.reached_on is not None

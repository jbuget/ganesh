"""Rhythm schemas: what a week expects of one teammate, and since when."""

from datetime import date

from pydantic import BaseModel, Field

from src.modules.calendar.domain.entities.week_pattern import WeekPattern
from src.modules.users.domain.entities.rhythm import Rhythm

#: A day of the motif holds what an entry holds, or nothing at all. The domain
#: refuses anything else; the schema says so in the OpenAPI too, so a client
#: knows before it calls.
_DAY = Field(default=1.0, ge=0.0, le=1.0, multiple_of=0.5)


class DeclareRhythmRequest(BaseModel):
    """Declaring one's own rhythm, from a given day.

    The five days travel together: a rhythm is a motif, and a field left out
    is a field set back to a full day.
    """

    effective_from: date
    monday: float = _DAY
    tuesday: float = _DAY
    wednesday: float = _DAY
    thursday: float = _DAY
    friday: float = _DAY

    def to_pattern(self) -> WeekPattern:
        return WeekPattern(
            monday=self.monday,
            tuesday=self.tuesday,
            wednesday=self.wednesday,
            thursday=self.thursday,
            friday=self.friday,
        )


class WorkRhythmResponse(BaseModel):
    """A rhythm in force, and what it adds up to over a week."""

    effective_from: date
    monday: float
    tuesday: float
    wednesday: float
    thursday: float
    friday: float
    #: Computed rather than left to the client: two screens counting it
    #: themselves would eventually count it differently.
    days_per_week: float


def to_rhythm_response(rhythm: Rhythm) -> WorkRhythmResponse:
    return WorkRhythmResponse(
        effective_from=rhythm.effective_from,
        monday=rhythm.pattern.monday,
        tuesday=rhythm.pattern.tuesday,
        wednesday=rhythm.pattern.wednesday,
        thursday=rhythm.pattern.thursday,
        friday=rhythm.pattern.friday,
        days_per_week=rhythm.pattern.days_per_week,
    )

"""Input and output schemas for moods."""

from datetime import date

from pydantic import BaseModel

from src.modules.moods.domain.entities.mood import MoodLevel


class SetMoodRequest(BaseModel):
    """Request to post a mood, or to change the one already posted."""

    day: date
    level: MoodLevel


class MoodResponse(BaseModel):
    """A posted mood."""

    day: date
    level: MoodLevel


class OpenDayResponse(BaseModel):
    """A day one may still answer for, and what one has already said of it."""

    day: date
    level: MoodLevel | None


class MyMoodsResponse(BaseModel):
    """What the home screen offers: the open days, the most recent first."""

    days: list[OpenDayResponse]


class MoodAuthorResponse(BaseModel):
    """Who posted a mood."""

    id: int
    display_name: str
    initials: str


class SignedMoodResponse(BaseModel):
    """A mood and its author."""

    author: MoodAuthorResponse
    level: MoodLevel


class DayMoodsResponse(BaseModel):
    """One day of the window, and what the team said of it."""

    day: date
    #: Best first: the shape of a day reads at a glance.
    moods: list[SignedMoodResponse]
    #: How many of each level, every level named even at zero.
    counts: dict[MoodLevel, int]
    #: The mean of the answers, or null when nobody answered.
    average: float | None
    participation: int


class TeamMoodsResponse(BaseModel):
    """The team's morale over the window."""

    days: list[DayMoodsResponse]
    #: Active teammates, against which participation is read.
    headcount: int

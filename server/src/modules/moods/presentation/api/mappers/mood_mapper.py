"""Turns the mood readings into what the screens receive."""

from src.modules.moods.application.dtos.mood_dtos import OpenDay, TeamMoods
from src.modules.moods.domain.entities.mood import Mood
from src.modules.moods.presentation.api.schemas.mood_schemas import (
    DayMoodsResponse,
    MoodAuthorResponse,
    MoodResponse,
    MyMoodsResponse,
    OpenDayResponse,
    SignedMoodResponse,
    TeamMoodsResponse,
)
from src.modules.users.domain.entities.user import User
from src.shared.utils.initials import initials

#: A mood whose author has been deleted keeps its place on the day it was
#: posted: dropping it would quietly change what that day looked like.
UNKNOWN = MoodAuthorResponse(id=0, display_name="Compte supprimé", initials="?")


def to_mood_response(mood: Mood) -> MoodResponse:
    return MoodResponse(day=mood.day, level=mood.level)


def to_my_moods_response(days: list[OpenDay]) -> MyMoodsResponse:
    return MyMoodsResponse(
        days=[OpenDayResponse(day=day.day, level=day.level) for day in days]
    )


def to_author(user: User) -> MoodAuthorResponse:
    return MoodAuthorResponse(
        id=user.id or 0,
        display_name=user.label,
        initials=initials(user.label),
    )


def to_team_moods_response(view: TeamMoods) -> TeamMoodsResponse:
    authors = {person.id: to_author(person) for person in view.people}
    return TeamMoodsResponse(
        days=[
            DayMoodsResponse(
                day=day.day,
                moods=[
                    SignedMoodResponse(
                        author=authors.get(signed.user_id, UNKNOWN),
                        level=signed.level,
                    )
                    for signed in day.moods
                ],
                counts=day.counts,
                average=day.average,
                participation=day.participation,
            )
            for day in view.report.days
        ],
        headcount=view.report.headcount,
    )

"""The month arranged as a chronicle: one chapter per project.

A flat list of everything that happened reads as a log, which is what it came
from. Gathered under the project it is about, the same facts read as a story
of that project's month — a work package's facts among them, because a lot's
month is part of its project's month, not a chronicle of its own.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from src.modules.gazette.domain.entities.movement import Movement


class ChapterOf(StrEnum):
    """What a chapter gathers.

    A project's month is one chapter; what the company asked for is another,
    and who joined or left the team a third. Said here rather than read off a
    missing label: two chapters about no project would otherwise be one.
    """

    PROJECT = "project"
    #: The needs the month was asked, from the day they were handed over to
    #: the day they became a mission. A chapter of their own because a need
    #: is not a mission, and the whole feature rests on not confusing them.
    REQUESTS = "requests"
    TEAM = "team"


@dataclass(frozen=True)
class Chapter:
    """One project's month, its work packages' facts told among its own."""

    of: ChapterOf
    #: The project the chapter is about, or nothing when it gathers what was
    #: about no project at all — a need expressed, somebody joining the team.
    project_id: int | None
    #: The project's name, as the register spelt it the day it was read.
    #: Nothing alongside a chapter about no project: what such a chapter is
    #: called is for the reading side to say, in French.
    label: str | None
    #: Everything that happened to the project and to its packages, in the
    #: order it happened. Each movement still says what it was about, so a
    #: line about a package can name it where a line about the project needs
    #: no naming.
    movements: list[Movement] = field(default_factory=list)

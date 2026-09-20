"""The month arranged as a chronicle: one chapter per mission.

A flat list of everything that happened reads as a log, which is what it came
from. Gathered under the mission it is about, the same facts read as a story
of that mission's month — and a work package is told inside its project,
because that is where its month belongs.
"""

from dataclasses import dataclass, field

from src.modules.gazette.domain.entities.movement import Movement


@dataclass(frozen=True)
class Chapter:
    """One mission's month, its packages told inside it."""

    #: The mission the chapter is about, or nothing when it gathers what was
    #: about no mission at all — somebody joining the team, or leaving it.
    project_id: int | None
    #: The mission's name, as the register spelt it the day it was read.
    #: Nothing alongside a chapter about no mission: what such a chapter is
    #: called is for the reading side to say, in French.
    label: str | None
    movements: list[Movement] = field(default_factory=list)
    #: The work packages of the project, each its own chapter. A project may
    #: carry none of its own movements and still open, to hold its packages.
    packages: list["Chapter"] = field(default_factory=list)

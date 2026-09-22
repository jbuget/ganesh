"""What the teammate panel reads, and what it asks for."""

from dataclasses import dataclass
from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.users.domain.entities.rhythm import Rhythm
from src.modules.users.domain.services.user_record import MonthFilling


@dataclass(frozen=True)
class GetUserRecordQuery:
    """Asks what the register holds on one teammate."""

    user_id: int
    #: Injected by the tests; today's date otherwise.
    today: date | None = None


@dataclass(frozen=True)
class RecordedMission:
    """A mission somebody is attached to, as the panel names it."""

    project_id: int
    label: str
    status: ProjectStatus | None
    #: Whether they answer for the mission, beyond working on it.
    is_lead: bool


@dataclass(frozen=True)
class DeclaredMission:
    """A mission somebody put time on over the window."""

    project_id: int
    label: str
    days: float
    #: Named as such rather than dropped: five days of which three on leave is
    #: not a week spent the way the total alone suggests.
    is_off_project: bool


@dataclass(frozen=True)
class DeclaredWindow:
    """What one person declared lately, and over which stretch."""

    since: date
    until: date
    days: float
    missions: list[DeclaredMission]


@dataclass(frozen=True)
class UserRecord:
    """What the register holds on one teammate."""

    user_id: int
    missions: list[RecordedMission]
    declared: DeclaredWindow
    months: list[MonthFilling]
    #: The rhythm in force today. None while nothing was ever declared, which
    #: reads as full time everywhere a figure is computed.
    rhythm: Rhythm | None = None

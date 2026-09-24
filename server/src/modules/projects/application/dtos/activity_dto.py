"""Commands that change the activities a mission is cut into."""

from dataclasses import dataclass

from src.shared.enums.work_nature import WorkNature


@dataclass(frozen=True)
class CreateActivityCommand:
    """Request to cut a new trade into a mission."""

    actor_id: int
    project_id: int
    label: str
    nature: WorkNature | None = None
    estimated_days: float | None = None


@dataclass(frozen=True)
class UpdateActivityCommand:
    """Request to change what an activity says.

    Every field is optional and only what is named is written: a screen
    editing the estimate alone must not blank the trade beside it. `nature`
    and `estimated_days` are therefore not told apart from « leave as is » by
    their value but by whether they were named at all.
    """

    actor_id: int
    activity_id: int
    label: str | None = None
    nature: WorkNature | None = None
    estimated_days: float | None = None
    sets_nature: bool = False
    sets_estimated_days: bool = False


@dataclass(frozen=True)
class ArchiveActivityCommand:
    """Request to take an activity out of what can be declared on."""

    actor_id: int
    activity_id: int

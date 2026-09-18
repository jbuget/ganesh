"""Commands acting on the mission reference list."""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)


@dataclass(frozen=True)
class CreateProjectCommand:
    """Creating a project, a work package or off-project work."""

    actor_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None = None
    parent_id: int | None = None
    estimated_days: float | None = None


@dataclass(frozen=True)
class ChangeProjectStatusCommand:
    """Phase change. Open to the whole team, but traced."""

    actor_id: int
    project_id: int
    status: ProjectStatus


#: Marks a field absent from the command, to tell it from a deliberate null:
#: `estimated_days=None` clears the estimate, an omitted `estimated_days`
#: leaves it alone.
ABSENT: Any = object()


@dataclass(frozen=True)
class UpdateProjectCommand:
    """Changing a mission. Only the fields provided are applied."""

    actor_id: int
    project_id: int
    label: str | Any = ABSENT
    status: ProjectStatus | None | Any = ABSENT
    estimated_days: float | None | Any = ABSENT
    category: ProjectCategory | None | Any = ABSENT
    priority: ProjectPriority | None | Any = ABSENT
    go_live_date: date | None | Any = ABSENT
    is_active: bool | Any = ABSENT
    parent_id: int | None | Any = ABSENT
    monday_item_id: str | None | Any = ABSENT
    monday_subitem_id: str | None | Any = ABSENT


@dataclass(frozen=True)
class ProjectImportLine:
    """One line of an import, as it comes out of a spreadsheet.

    The parent is named by its label: a Monday export knows nothing of our ids.
    """

    label: str
    kind: ProjectKind = ProjectKind.PROJECT
    status: ProjectStatus | None = ProjectStatus.EXPLORATION
    parent_label: str | None = None
    estimated_days: float | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


@dataclass(frozen=True)
class ImportProjectsCommand:
    """Bulk import of the reference list. Managers only."""

    actor_id: int
    rows: list[ProjectImportLine]


@dataclass
class ImportReport:
    """What the import did, line by line."""

    created: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeleteProjectCommand:
    """Deleting a mission that was never used."""

    actor_id: int
    project_id: int


@dataclass(frozen=True)
class MoveProjectCommand:
    """Moving a card on the board."""

    actor_id: int
    project_id: int
    status: ProjectStatus
    position: int

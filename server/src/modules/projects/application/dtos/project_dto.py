"""Commandes portant sur le referentiel des missions."""

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
    """Creation d'un projet, d'un lot ou d'une activite hors projet."""

    actor_id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None = None
    parent_id: int | None = None
    estimated_days: float | None = None


@dataclass(frozen=True)
class ChangeProjectStatusCommand:
    """Changement de phase. Ouvert a toute l'equipe, mais trace."""

    actor_id: int
    project_id: int
    status: ProjectStatus


#: Marque un champ absent de la commande, pour le distinguer d'une valeur nulle
#: volontaire : `estime_j=None` efface l'estime, `estime_j` omis ne le touche pas.
ABSENT: Any = object()


@dataclass(frozen=True)
class UpdateProjectCommand:
    """Modification d'une mission. Seuls les champs fournis sont appliques."""

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
    """Une ligne d'un import, telle qu'elle sort d'un tableur.

    Le parent est designe par son libelle : un export Monday ne connait pas nos
    identifiants.
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
    """Import en masse du referentiel. Reserve aux managers."""

    actor_id: int
    rows: list[ProjectImportLine]


@dataclass
class ImportReport:
    """Ce que l'import a fait, ligne par ligne."""

    created: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeleteProjectCommand:
    """Suppression d'une mission jamais utilisee."""

    actor_id: int
    project_id: int


@dataclass(frozen=True)
class MoveProjectCommand:
    """Deplacement d'une carte sur le tableau de bord."""

    actor_id: int
    project_id: int
    status: ProjectStatus
    position: int

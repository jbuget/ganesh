"""Commandes portant sur le referentiel des missions."""

from dataclasses import dataclass, field
from typing import Any

from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus


@dataclass(frozen=True)
class CreateProjectCommand:
    """Creation d'un projet, d'un lot ou d'une activite hors projet."""

    actor_id: int
    label: str
    kind: ProjectKind
    statut: ProjectStatus | None = None
    parent_id: int | None = None
    estime_j: float | None = None


@dataclass(frozen=True)
class ChangeProjectStatusCommand:
    """Changement de phase. Ouvert a toute l'equipe, mais trace."""

    actor_id: int
    project_id: int
    statut: ProjectStatus


#: Marque un champ absent de la commande, pour le distinguer d'une valeur nulle
#: volontaire : `estime_j=None` efface l'estime, `estime_j` omis ne le touche pas.
ABSENT: Any = object()


@dataclass(frozen=True)
class UpdateProjectCommand:
    """Modification d'une mission. Seuls les champs fournis sont appliques."""

    actor_id: int
    project_id: int
    label: str | Any = ABSENT
    statut: ProjectStatus | None | Any = ABSENT
    estime_j: float | None | Any = ABSENT
    actif: bool | Any = ABSENT
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
    kind: ProjectKind = ProjectKind.PROJET
    statut: ProjectStatus | None = ProjectStatus.EXPLORATION
    parent_label: str | None = None
    estime_j: float | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


@dataclass(frozen=True)
class ImportProjectsCommand:
    """Import en masse du referentiel. Reserve aux managers."""

    actor_id: int
    lignes: list[ProjectImportLine]


@dataclass
class ImportReport:
    """Ce que l'import a fait, ligne par ligne."""

    crees: int = 0
    ignores: int = 0
    erreurs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeleteProjectCommand:
    """Suppression d'une mission jamais utilisee."""

    actor_id: int
    project_id: int

"""Commandes portant sur le referentiel des missions."""

from dataclasses import dataclass

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

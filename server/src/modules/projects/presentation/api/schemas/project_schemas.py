"""Schemas du referentiel des missions."""

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities.project import ProjectKind, ProjectStatus


class CreateProjectRequest(BaseModel):
    """Creation d'une mission."""

    label: str = Field(min_length=1, max_length=255)
    kind: ProjectKind
    statut: ProjectStatus | None = None
    parent_id: int | None = None
    estime_j: float | None = None


class ChangeStatusRequest(BaseModel):
    """Changement de phase d'une mission."""

    statut: ProjectStatus


class ProjectResponse(BaseModel):
    """Une mission du referentiel."""

    id: int
    label: str
    kind: ProjectKind
    statut: ProjectStatus | None
    parent_id: int | None
    actif: bool
    estime_j: float | None
    is_syncable_to_monday: bool

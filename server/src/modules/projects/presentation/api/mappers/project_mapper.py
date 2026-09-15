"""Traduction des projets en schemas d'API."""

from src.modules.projects.domain.entities.project import Project
from src.modules.projects.presentation.api.schemas.project_schemas import (
    ProjectResponse,
)


def to_project_response(project: Project) -> ProjectResponse:
    assert project.id is not None
    return ProjectResponse(
        id=project.id,
        label=project.label,
        kind=project.kind,
        statut=project.statut,
        parent_id=project.parent_id,
        actif=project.actif,
        estime_j=project.estime_j,
        is_syncable_to_monday=project.is_syncable_to_monday,
    )

"""Traduction des projets en schemas d'API."""

from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.presentation.api.schemas.project_schemas import (
    ProjectResponse,
)


def to_project_response(
    project: Project, is_deletable: bool = False
) -> ProjectResponse:
    assert project.id is not None
    return ProjectResponse(
        id=project.id,
        label=project.label,
        kind=project.kind,
        statut=project.statut,
        parent_id=project.parent_id,
        actif=project.actif,
        estime_j=project.estime_j,
        monday_item_id=project.monday_item_id,
        monday_subitem_id=project.monday_subitem_id,
        is_syncable_to_monday=project.is_syncable_to_monday,
        is_deletable=is_deletable,
    )


def to_listed_project_response(listed: ListedProject) -> ProjectResponse:
    return to_project_response(listed.project, is_deletable=listed.is_deletable)
